# 엔진별 출력 구조 (실제 실행 확인)

GUI/AI 레이어를 만들기 전에 `diskcleaner/core/*` 각 엔진을 직접 실행해서 실제 반환값을 확인한 결과입니다.
테스트는 중복 파일 1쌍(`a.txt` / `sub/a_copy.txt`), 로그 파일(`app.log`), 캐시 파일(`cache1.cache`)로 구성된
샘플 디렉터리에 대해 진행했습니다 (Python 3.14, Windows, 2026-07-24 재검증).

## 전체 파이프라인 개요

5개 엔진은 아래 순서로 서로를 호출하며, `SmartCleanupEngine`이 나머지 4개를 감싸는 최상위 오케스트레이터입니다.

```
DirectoryScanner.scan()          — 디스크를 뒤져서 파일 목록을 만든다
        ↓ List[FileInfo]
FileClassifier.classify()        — 파일 하나하나에 "이게 뭔지" 3개 축으로 꼬리표를 붙인다
        ↓ by_type / by_risk / by_age
DuplicateFinder.find_duplicates() — 내용이 같은 파일끼리 그룹으로 묶는다
        ↓ List[DuplicateGroup]
SafetyChecker.verify_all()       — "지금 지워도 안전한가"를 파일별로 재검증한다
        ↓ 안전하지 않은 파일 제외
SmartCleanupEngine.analyze()     — 위 4단계를 순서대로 실행하고 하나의 CleanupReport로 묶어서 반환
```

GUI는 원칙적으로 `SmartCleanupEngine.analyze()` 하나만 호출하면 되고, 나머지 4개 엔진은 그 안에서
내부적으로 조립되는 부품입니다. (단, 중복파일 상세 모달처럼 `DuplicateFinder`의 결과만 별도로
다시 보여줘야 하는 화면에서는 `report.duplicates`를 그대로 재사용하면 됨 — 다시 스캔할 필요 없음.)

## 1. `DirectoryScanner.scan()` (`diskcleaner/core/scanner.py`)

**무슨 일을 하나**: 지정한 경로(`target_path`) 아래를 재귀적으로 순회하면서 존재하는 모든
파일·폴더의 메타데이터(경로, 크기, 수정시각 등)를 긁어모으는 "1단계 원시 스캐너"입니다.
이 시점에는 어떤 파일이 삭제해도 되는지, 어떤 파일이 중복인지 같은 판단은 전혀 하지 않고
순수하게 "디스크에 뭐가 있는지 목록화"만 담당합니다. 내부적으로 `os.scandir()`을 써서
`Path.glob()`보다 빠르게 순회하고, `cache_enabled=True`면 이전 스캔 결과(`~/.disk-cleaner/cache`)와
비교해 변경된 파일만 다시 읽는 증분 스캔을 지원합니다. `max_files`/`max_seconds`로 대용량 디스크에서
스캔이 무한정 오래 걸리는 것을 막는 조기 종료 장치도 갖고 있습니다.

```python
scanner = DirectoryScanner(path, cache_enabled=False)
files = scanner.scan()  # -> List[FileInfo]
```

`FileInfo`는 `@dataclass`:

| field   | type            | 비고                              |
|---------|-----------------|-----------------------------------|
| path    | str             | 절대 경로                          |
| name    | str             | 파일명만                           |
| size    | int             | bytes. 디렉터리는 0                |
| mtime   | float           | UNIX timestamp                     |
| is_dir  | bool            |                                    |
| is_link | bool            |                                    |
| inode   | Optional[int]   | Windows에서는 항상 0 (inode 없음)   |
| depth   | int             | target_path 기준 상대 깊이          |

- 디렉터리 자체도 `FileInfo(is_dir=True)`로 포함되어 반환됨 → 아래 단계로 넘기기 전에 `is_dir` 필터링 필요
  (`smart_cleanup.py`는 `[f for f in files if not f.is_dir]`로 걸러냄).
- `include_windows: bool = False` 옵션 있음 (이번 포크 정리 중 top-level로 이식). Windows 시스템 폴더까지
  스캔할지 여부. GUI에서 노출할 필요는 없고 기본값(False) 유지 권장.

## 2. `FileClassifier.classify(files)` (`diskcleaner/core/classifier.py`)

**무슨 일을 하나**: `DirectoryScanner`가 만든 파일 목록을 받아서, 파일 하나하나에 "이 파일이
무엇인가"를 3가지 서로 다른 기준(축)으로 동시에 분류하는 "꼬리표 붙이기" 엔진입니다.
같은 파일 하나가 `by_type`(무슨 종류: 로그냐 캐시냐 문서냐), `by_risk`(지워도 되는 위험도),
`by_age`(만들어진 지 얼마나 됐는지) 세 그룹 모두에 동시에 들어갑니다. 판단 기준은 파일 내용을
읽는 게 아니라 **파일명 패턴(확장자·와일드카드)과 경로 문자열만 보고** 정해집니다 — 즉 지금
단계에서는 아직 AI/LLM이 개입하지 않고, 순수 규칙 기반(rule-based) 매칭만 합니다.

```python
classification = classifier.classify(file_list)
# -> {"by_type": {...}, "by_risk": {...}, "by_age": {...}}
```

반환 타입은 3개 키를 가진 `Dict[str, Dict[str, List[FileInfo]]]`.

### by_type — ⚠️ 카테고리 라벨이 두 군데서 옴 (한국어 매핑 작업 시 둘 다 확인 필요)

1. **`config/defaults.py`의 `rules` 리스트가 먼저 적용됨** (영어 카테고리):
   - `*.log` → `"Logs"`
   - `node_modules/` → `"Build"`
   - `__pycache__/`, `*.pyc` → `"Cache"`
   - `*.tmp` → `"Temp"`
2. **위 규칙에 안 걸리면 `classifier.py`의 `type_categories` 하드코딩 (중국어)**:
   - `临时/构建产物` (임시/빌드 산출물): `*.tmp`, `*.temp`, `*.cache`, `__pycache__`, `node_modules`, `.pytest_cache`, `.mypy_cache`, `*.pyc`, `*.pyo`
   - `日志文件` (로그 파일): `*.log`
   - `缓存文件` (캐시 파일): `*.cache`, `.cache`, `Thumbs.db`, `.DS_Store`
   - `备份文件` (백업 파일): `*.bak`, `*.backup`, `*~`, `*.old`
   - `下载文件` (다운로드 파일): 패턴 없음, 경로에 "downloads" 포함 시 특별 처리
   - `媒体文件` (미디어 파일): mp4/mkv/avi/mov/mp3/flac/jpg/jpeg/png/gif/bmp
   - `文档文件` (문서 파일): pdf/doc/docx/xls/xlsx/ppt/pptx/odt
   - `压缩文件` (압축 파일): zip/tar/gz/rar/7z
3. 위 어디에도 안 걸리면 `"其他文件"` (기타 파일)

→ 실제 실행 결과 `by_type` 키: `['其他文件', 'Logs', '临时/构建产物']`
(`*.log`가 config rule에 의해 중국어 `日志文件`이 아니라 영어 `Logs`로 분류됨 — rule이 먼저 체크되기 때문)

**한국어 라벨 매핑표는 rules(영어 5개) + type_categories(중국어 8개) + "其他文件" fallback, 총 14개 문자열을 모두 커버해야 함.**

### by_risk — 고정 3키 (영어 enum, 매핑 불필요)

`RiskLevel` enum 값: `"safe"`, `"confirm_needed"`, `"protected"`

- `safe`: 위 type 카테고리가 임시/로그/캐시/build/cache/temp류
- `confirm_needed`: 다운로드/미디어/문서류 + 그 외 기본값
- `protected`: 보호 경로/확장자/패턴에 매칭된 파일

### by_age — 고정 4키 (중국어 하드코딩, 매핑 필요)

- `最近创建 (7天内)` — 최근 생성 (7일 이내)
- `近期文件 (30天内)` — 최근 파일 (30일 이내)
- `陈旧文件 (90天内)` — 오래된 파일 (90일 이내)
- `很旧 (90天以上)` — 매우 오래됨 (90일 이상)

## 3. `DuplicateFinder.find_duplicates(files)` (`diskcleaner/core/duplicate_finder.py`)

**무슨 일을 하나**: 파일명이 달라도 **내용이 완전히 같은 파일**들을 찾아서 그룹으로 묶어주는
엔진입니다. `FileClassifier`와 달리 이건 파일명을 안 보고 실제 내용(크기, 수정시각, 필요하면
SHA-256 해시)을 비교합니다. 파일 개수가 1000개 미만이면 모든 후보를 SHA-256으로 정확히
비교(`accurate`)하고, 1000개 이상이면 먼저 크기+수정시각이 비슷한 것끼리만 추려낸 뒤 필요한
경우에만 해시를 계산(`fast`)해서 대용량 디렉터리에서도 속도가 급격히 느려지지 않게 합니다
(`adaptive` = 파일 개수 보고 위 두 전략 중 자동 선택). 결과는 "이만큼 지우면 이만큼 공간이
빈다"는 계산까지 미리 해서 반환하지만, **어떤 사본을 남기고 어떤 걸 지울지는 결정하지 않습니다**
— 그건 그룹 안 파일 목록(`files`)만 넘겨주고 최종 선택은 사용자(GUI 상세 모달)의 몫으로 남겨둡니다.

```python
dups = duplicate_finder.find_duplicates(file_list)  # -> List[DuplicateGroup]
```

`DuplicateGroup` (`@dataclass`):

| field/property     | type              | 비고                                  |
|--------------------|-------------------|----------------------------------------|
| files              | List[FileInfo]    | 그룹 내 중복 파일들 (전부)               |
| size               | int               | 파일 1개당 크기                         |
| hash_value         | Optional[str]     | SHA-256 (accurate 전략일 때만 채워짐)    |
| count (property)   | int               | `len(files)`                            |
| reclaimable_space (property) | int      | `size * (count - 1)` — 1개만 남기고 삭제 시 회수 용량 |

- 파일 개수 1000개 기준으로 `fast`(size+mtime) / `accurate`(SHA-256) 전략을 자동 전환 (`adaptive`).
- 결과는 `reclaimable_space` 내림차순 정렬됨.
- 그룹 안에서 "어느 파일을 남길지"는 엔진이 정하지 않음 — GUI 상세 모달에서 사용자가 직접 선택해야 함.

## 4. `SafetyChecker.verify_all(files)` (`diskcleaner/core/safety.py`)

**무슨 일을 하나**: `FileClassifier`가 "위험도"를 파일명 패턴만 보고 정하는 것과 달리, 이 엔진은
**지금 이 순간 실제로 지워도 안전한지**를 파일 시스템 레벨에서 재확인하는 마지막 방어선입니다.
확인 항목은 4가지: (1) 보호 대상 경로/확장자/패턴에 걸리는가(`.exe`, `.dll`, `config.*` 등),
(2) 다른 프로세스가 그 파일을 사용 중이라 잠겨 있는가(`_is_locked`, 크로스 플랫폼 구현),
(3) 실제 쓰기 권한이 있는가, (4) 위 확인 과정 자체에서 에러가 났는가. 즉 `FileClassifier`가
"이건 로그 파일이니 지워도 될 것 같다"고 정적으로 판단한 것을, `SafetyChecker`가 "근데 지금 보니
그 로그 파일을 어떤 프로세스가 쓰고 있다"처럼 동적으로 뒤집을 수 있습니다. 실제 삭제 실행 직전에
반드시 거쳐야 하는 단계입니다.

```python
results = safety.verify_all(file_list)  # -> List[Tuple[FileInfo, FileStatus]]
```

`FileStatus` enum 값: `"safe"`, `"locked"`, `"no_permission"`, `"protected"`, `"error"`

⚠️ **버그성 낌새 발견 (재확인됨)**: `smart_cleanup.py`의 `analyze()`가
`status.value in ("safe", "confirm_needed")`로 필터링하는데, `FileStatus`에는 `"confirm_needed"`라는 값이
아예 없음(그건 `RiskLevel`의 값). 실질적으로는 `status.value == "safe"`인 파일만 통과하는 것과 동일하게 동작함
(대부분의 파일은 잠금/권한문제/보호 대상이 아니면 SAFE로 나오므로 지금 당장 심각한 문제는 아니지만,
추후 safety_check 로직을 건드릴 때 이 부분 주의).

## 5. `SmartCleanupEngine.analyze()` (`diskcleaner/core/smart_cleanup.py`) — GUI가 실제로 소비할 최종 출력

**무슨 일을 하나**: 위 4개 엔진(스캔 → 분류 → 중복탐지 → 안전검사)을 이 순서 그대로 호출하고,
그 결과를 하나의 `CleanupReport`로 합쳐주는 "총괄 지휘자"입니다. GUI는 이 엔진 하나만 알면 되고
나머지 4개를 직접 조립할 필요가 없습니다. 내부적으로 `safety_check=True`(기본값)면
안전검사에서 걸러진 파일들을 분류 결과·중복 그룹에서 다시 한번 제외하는 후처리까지 수행하므로,
GUI가 최종적으로 받는 `report`는 "이미 위험한 파일이 빠진, 바로 화면에 그려도 되는" 상태입니다.
용량 통계(총 용량/회수 가능 용량 등)도 이 단계에서 한 번에 계산됩니다.

```python
engine = SmartCleanupEngine(path, cache_enabled=True)
report = engine.analyze(include_duplicates=True, safety_check=True)  # -> CleanupReport
```

`CleanupReport` (`@dataclass`):

| field/property            | type                          |
|----------------------------|-------------------------------|
| by_type                    | Dict[str, List[FileInfo]]     |
| by_risk                    | Dict[str, List[FileInfo]]     |
| by_age                     | Dict[str, List[FileInfo]]     |
| duplicates                 | List[DuplicateGroup]          |
| total_files                | int                           |
| total_size                 | int (bytes)                   |
| reclaimable_space          | int (bytes)                   |
| scan_time                  | float (초)                     |
| timestamp                  | float (UNIX timestamp)        |
| safe_reclaimable (property)      | int |
| confirm_reclaimable (property)   | int |
| duplicate_reclaimable (property) | int |
| total_reclaimable (property)     | int |

- `safety_check=True`(기본값)일 때 `by_type`/`by_risk`/`by_age`/`duplicates`가 "안전한 파일만" 걸러진 뒤의 결과로 대체됨.
  즉 GUI가 받는 `report.by_type`은 이미 안전 필터링이 끝난 목록.
- **`get_summary(report)` 메서드는 중국어 하드코딩 문자열이라 GUI에서 그대로 쓰면 안 됨** — GUI는
  `by_type`/`by_risk`/`by_age` 원본 dict를 받아 한국어 라벨 매핑표로 직접 렌더링해야 함.
- `cache_enabled=True`(기본값)면 `~/.disk-cleaner/cache`에 증분 스캔 캐시가 쌓임 — 반복 스캔 시 결과가
  "새 파일/변경 파일"만 갱신될 수 있으니, GUI에서 매번 전체 스캔을 기대한다면 `cache_enabled=False` 고려.

### 실제 실행 예시 (샘플 디렉터리: 파일 4개, 중복 1쌍, 2026-07-24 재검증)

```
total_files: 4
total_size: 39
reclaimable_space: 45
by_type keys: ['其他文件', 'Logs', '临时/构建产物']
by_risk: {'safe': 1, 'confirm_needed': 3, 'protected': 0}
by_age: {'最近创建 (7天内)': 4, '近期文件 (30天内)': 0, '陈旧文件 (90天内)': 0, '很旧 (90天以上)': 0}
duplicates: 1 그룹 (a.txt / sub/a_copy.txt, 6 bytes)
safe_reclaimable: 18   (cache1.cache)
confirm_reclaimable: 21 (app.log 9B + a.txt 6B + a_copy.txt 6B)
duplicate_reclaimable: 6 (중복 그룹 1개, 1개 남기고 삭제 시)
total_reclaimable: 45
```

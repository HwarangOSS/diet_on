# LLM 삭제 권장 프롬프트 — 요청/응답 스키마 (이슈 #9)

API 연결은 하지 않음. 프롬프트 템플릿과 요청/응답 JSON 스키마만 확정하는 문서.
엔진 출력 구조는 [ENGINE_OUTPUTS.md](./ENGINE_OUTPUTS.md) 참고.

## 적용 대상

- `SafetyChecker` 통과 후 `by_risk == "confirm_needed"` 파일만 LLM에 보냄.
  - `safe`는 이미 삭제 안전 판정이 끝난 파일이라 LLM 호출 불필요.
  - `protected`/`locked`/`no_permission`은 애초에 삭제 후보가 아니므로 제외.
- 중복 파일 그룹(`DuplicateGroup`)은 "어느 사본을 남길지"를 사용자가 GUI 모달에서 직접 고르는
  별도 플로우이므로 이 프롬프트 범위 밖 (ENGINE_OUTPUTS.md 3번).

## 배치 단위

파일 50개 / 요청 — 즉 LLM에 요청을 1번 보낼 때 `files` 배열에 함께 담아 전송하는 파일 개수를
뜻함. 파일당 필드가 3~4개뿐이라 프롬프트가 가볍고, 응답 파싱 실패 시 재시도 비용도 작게 유지하기
위한 값 — 필요시 조정.

## 요청 스키마

```json
{
  "batch_id": "uuid4 문자열",
  "files": [
    {
      "path": "절대경로 (응답 매칭용 고유 key)",
      "name": "파일명만",
      "size": 12345,
      "mtime": 1753344000.0
    }
  ]
}
```

- `mtime`은 **초 단위 UNIX epoch timestamp**(float). `FileInfo.mtime`(ENGINE_OUTPUTS.md 필드 표)
  원본 그대로라 밀리초 변환 없이 그대로 전달. optional — "오래 방치된 파일" 판단 근거로 쓰되
  없어도 파일명+크기만으로 최소 판단은 동작해야 함.
- `category`(by_type)는 보내지 않음: 규칙 기반 분류가 놓치는 출처 불명 파일을 LLM이 파일명/경로
  패턴만으로 독자 판단하게 하는 것이 이 기능의 목적이라서 (CLAUDE.md 참고).

## 응답 스키마

```json
{
  "batch_id": "요청과 동일 값 echo",
  "results": [
    {
      "path": "요청 files[].path와 동일 (매칭 key)",
      "recommend_delete": true,
      "reason": "한 줄 근거 (한국어)",
      "confidence": 0.8
    }
  ]
}
```

- `results`는 `files`와 길이·순서 무관하게 `path`로 매칭. 응답에서 빠진 `path`는 GUI 쪽에서
  `confirm_needed` 그대로 폴백 처리 (TODO: 방어 로직 구현).
- `recommend_delete: true`는 권장 표시일 뿐 최종 삭제 트리거 아님 — 실제 삭제는 항상 사용자 확인 후.
- `confidence`는 optional, 0.0~1.0.

### `batch_id` vs `path` — 매칭 단위가 다름

둘 다 "매칭 key"지만 granularity가 다르다. 먼저 `batch_id`로 배치를 식별하고, 그 배치 안에서
`path`로 파일 하나하나를 식별하는 2단계 구조.

|            | 범위              | 요청당 개수             | 목적                               |
|------------|-------------------|------------------------|-----------------------------------|
| `batch_id` | 요청/응답 전체 1건 | 1개                    | 어느 배치에 대한 응답인지 식별       |
|   `path`   | 배치 안 파일 1개   | 최대 50개(배치 크기만큼) | 배치 안에서 어느 파일 결과인지 식별  |

지금은 배치를 순차 처리한다고 가정해 `batch_id` 매칭이 사실상 없어도 무방하지만, 나중에 여러
배치를 병렬로 요청하게 되면 응답이 뒤섞여 도착할 수 있어 그때부터 의미가 생김.

## 프롬프트 템플릿

**system**
```
당신은 PC 디스크 정리 보조 AI입니다. 사용자가 제공한 파일 목록(파일명, 경로, 용량, 수정시각)만
보고 각 파일이 "삭제해도 안전할 가능성이 높은 파일"인지 판단합니다. 파일 내용은 읽을 수 없고
파일명/경로 문자열 패턴과 크기만으로 판단합니다. 설치 잔여 파일, 임시/캐시성 파일, 출처를 알 수
없는 실행파일 등은 삭제 후보 신호로 보되, 확신이 낮으면 반드시 recommend_delete=false로
응답하세요 (오삭제 방지가 최우선). 반드시 지정된 JSON 스키마로만 응답하고 다른 텍스트는 출력하지
마세요.
```

**user**
```
batch_id: {batch_id}
files:
{files_json}

아래 스키마의 JSON으로만 응답하세요:
{response_schema}
```

플레이스홀더 3개는 단순 문자열 치환(`.format()`/f-string)으로 조립하고, 별도 템플릿 엔진이나
조건 분기는 두지 않음.

- `{batch_id}`: 요청 스키마의 `batch_id` 값을 그대로 삽입. 응답에 이 값을 echo하라는 지시 역할.
- `{files_json}`: 요청 스키마의 `files` 배열을 `json.dumps`로 직렬화한 문자열을 그대로 삽입 —
  LLM이 파싱 없이 눈으로 보는 실제 파일 목록 원문.
- `{response_schema}`: 응답 스키마의 예시(빈 값이 채워진 JSON 형태)를 문자열로 삽입하는 few-shot
  힌트. system 프롬프트의 "지정된 JSON 스키마로만 응답" 지시를 구체적인 모양으로 재확인시켜
  포맷 이탈을 줄이는 목적.

## TODO

- `confidence` 임계값: 지금은 실제 모델 응답이 없어 분포를 모르므로 미확정. API 연결 후 아래 순서로 실측 결정.
  1. `confirm_needed` 샘플에 실제 LLM 호출 → confidence 분포 수집
  2. 소량(수십~백 개)을 사람이 직접 "지워도 됨/아님"으로 라벨링
  3. 임계값을 올리며 오삭제(false positive) 비율이 "오삭제 방지 최우선" 원칙에 맞는 수준까지
     낮아지는 지점을 채택 (recall보다 precision 우선)
- 응답 개수가 요청과 다를 때 재시도할지 폴백만 할지

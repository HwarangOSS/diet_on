# DietOn

AI 기반 파일명 탐색 + 원클릭 일괄 최적화 PC 클리너.

기존 PC 최적화 프로그램은 기능이 많은 대신 뭘 눌러야 할지 판단하기 어려웠습니다. DietOn은 OS 자체 설정과 겹치는 기능은 빼고, 판단이 필요한 항목(중복 파일, 보안 프로그램 등)만 상세 화면에서 개별 확인하도록 구성했습니다. 나머지는 원클릭으로 끝냅니다.

[gccszs/disk-cleaner](https://github.com/gccszs/disk-cleaner)를 포크해 제작했습니다. 원본 프로젝트 고지는 [README.md](README.md), 라이선스 전문은 [LICENSE](LICENSE) 참고.

## 원본과 차이점

원본은 CLI 스크립트(`skills/disk-cleaner/scripts/*.py`) 기반이었습니다. DietOn은 같은 분석 엔진(`diskcleaner/` 패키지)을 그대로 쓰면서 스크립트를 PySide6 GUI로 바꿨고, Anthropic Claude API로 AI 삭제 권장을 붙였습니다(원본은 규칙 기반만 제공). 라벨/문구는 한국어로 매핑하였고, 원클릭 일괄 삭제 흐름과 중복 파일·AI 분석 대상 상세 화면을 새로 추가했습니다.

## 설치 및 실행

Windows 빌드본은 `DietOn_v1.0/DietOn.exe`를 바로 실행하면 됩니다.

소스에서 실행하려면:

```bash
git clone https://github.com/HwarangOSS/diet_on.git
cd diet_on
pip install -e ".[llm]"
python -m diskcleaner.gui.main
```

AI 삭제 권장을 쓰려면 실행 전 `ANTHROPIC_API_KEY` 환경변수를 설정해야 합니다.

macOS 빌드/실기 검증은 아직 진행 중이라 현재는 Windows 기준으로만 확인된 상태입니다.

## 도움말

### 실행 방법

1. 스캔할 경로 선택 (기본값: 사용자 홈 디렉토리) — 전체 드라이브를 그대로 스캔하면 시간이 오래 걸리므로 원하는 폴더로 바꿔서 검사하는 걸 권장
2. 스캔 시작 → 파일 분석 완료까지 대기
3. 결과 화면에서 안전 삭제 대상 / 중복 파일 / AI 분석 대상 확인
4. 원클릭 일괄 삭제 또는 상세 화면에서 개별 선택 후 삭제

### AI 삭제 권장 기능

`ANTHROPIC_API_KEY`가 설정돼 있으면 파일명 기반 AI 삭제 권장을 쓸 수 있습니다. 설정 안 해도 실행은 되고, 이 경우 기본 규칙 기반 권장만 나옵니다. Claude API는 사용한 토큰만큼 과금되는 유료 API라 [console.anthropic.com](https://console.anthropic.com)에서 키를 따로 발급받아야 합니다. API로는 파일명, 크기, 수정시각만 넘어가고 전체 경로나 파일 내용은 로컬에만 남습니다.

규칙 기반 권장은 임시/빌드 산출물, 로그, 캐시 파일을 안전 삭제 대상으로 자동 분류하고 다운로드/미디어/문서 파일은 확인 필요로 분류합니다. 시스템 파일 등 보호 대상 경로·확장자는 항상 삭제 후보에서 빠집니다.

앱 내 더보기 메뉴 → 도움말/라이센스에서도 같은 내용을 볼 수 있습니다.

## 삭제 안전성

삭제 대상 판단은 위 규칙 기반 분류를 기본으로 하고, AI가 켜져 있으면 Claude가 붙인 권장 사유가 같이 표시됩니다. 다만 현재 GUI 삭제는 휴지통을 거치지 않는 영구 삭제이고 별도 복구 기능도 없습니다. 삭제 실행 전 상세 화면에서 대상 목록을 꼭 확인하고, 중요 파일이 섞여 있을 수 있는 폴더는 미리 백업해두는 걸 권장합니다.

## 라이센스

DietOn은 [gccszs/disk-cleaner](https://github.com/gccszs/disk-cleaner)를 포크한 프로젝트이고, 원본과 마찬가지로 MIT License를 따릅니다. 아래 저작권 표기 중 2025년 줄은 원본 프로젝트, 2026년 HwarangOSS 줄은 이 저장소에서 추가한 부분에 대한 것입니다.

```
MIT License

Copyright (c) 2025 Disk Cleaner Contributors
Copyright (c) 2026 HwarangOSS (DietOn)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

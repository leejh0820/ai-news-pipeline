# 🤖 Daily Tech Radar (Make.com + Gemini API + Obsidian)

> **Make.com**과 **Google Gemini API**를 활용하여 지정한 RSS 피드 및 Gmail 뉴스레터를 자동 수집·분석하고, **Obsidian(옵시디언) 전용 마크다운 요약 리포트**를 생성하는 무인 자동화 파이프라인입니다.

---

## 📡 Data Sources (수집 출처)

본 파이프라인은 아래 출처로부터 최근 24~48시간 이내에 발행된 기술 소식을 수집합니다.

- **RSS Feeds:**
  - Daily Prompt (`[https://blog.secondbrush.co.kr/](https://blog.secondbrush.co.kr/)`)
  - Interconnects (`[https://www.interconnects.ai/](https://www.interconnects.ai/)`)
- **Gmail Newsletter:**
  - 지메일 라벨: `Newsletter`
  - 메일 수신 검색 조건: `label:Newsletter newer_than:2d` (`수신거부` 또는 `unsubscribe` 키워드 기반 필터링)

---

## 📌 Workflow Architecture (실행 순서)

Make.com 흐름 특성상 분기(Router) 후 합류가 불가능하므로, 안정적인 처리를 위해 **순차적(Sequential) 파이프라인**으로 설계되었습니다.

```text
[Tools 4: Set Variable] ──> 수집할 RSS URL 배열 정의
       │
       ▼
[Iterator 5] ────────────> URL 배열 요소 순회
       │
       ▼
[RSS 6] ─────────────────> 각 RSS 피드에서 신규 기사 추출
       │
       ▼
[Tools 7: Text Aggregator] ─> RSS 기사 텍스트 하나로 병합
       │
       ▼
[Gmail 14] ──────────────> 최근 2일 이내 수신된 뉴스레터 검색
       │
       ▼
[Tools 17: Text Aggregator] ─> 뉴스레터 Snippet(요약) 텍스트 하나로 병합
       │
       ▼
[Google Gemini AI 10] ────> 5개 카테고리 분류 및 인사이트 요약 생성
       │
       ▼
[Google Drive 11] ────────> 생성된 마크다운(.md) 리포트 파일 저장
```

---

## 🛠️ Key Technical Solutions (핵심 기술 특징)

1. **순차적 페이로드 통합 (Sequential Ingestion):**
   - RSS와 Gmail 데이터를 단계별 집계(Text Aggregator)하여 하나의 Gemini 프롬프트로 전달하도록 구조화.
2. **토큰 한도 최적화 (Rate Limit 429 Error 방지):**
   - 이메일 전체 본문(`Text Content`) 전달 시 발생하는 Gemini Free Tier 분당 토큰 제한(250,000 Tokens) 초과를 방지하기 위해, 핵심 요약본(`Snippet`) 매핑으로 용량 95% 절감.
3. **옵시디언 맞춤 시각화:**
   - 5개 규격 카테고리(`로보틱스/VLA`, `RL·포스트트레이닝`, `AI 엔지니어링 실무`, `채용·업계 동향`, `생성형 툴`) 자동 분류 및 접고 펼칠 수 있는 Callout(`> [!note]+`) 서식 적용.

---

## 🚀 Quick Start (사용 방법)

### 1. 사전 준비 (Prerequisites)
- [Make.com](https://www.make.com/) 계정
- [Google AI Studio](https://aistudio.google.com/)에서 발급받은 **Gemini API Key**
- 뉴스레터 수신용 Gmail 계정 및 구글 드라이브 계정

---

### 2. Gmail 라벨 필터 설정
뉴스레터 메일이 수신될 때 자동으로 라벨이 붙도록 지메일에서 설정합니다.
1. Gmail 검색창 우측 옵션 버튼 클릭 ➔ `포함하는 단어` 칸에 `수신거부 OR unsubscribe` 입력
2. **`필터 만들기`** 클릭
3. **`라벨 적용`** 선택 ➔ 새 라벨 이름: **`Newsletter`** 지정 후 필터 생성

---

### 3. Make.com 시나리오 가져오기 (Import)
1. Make.com 로그인 후 좌측 메뉴의 **`Scenarios`** ➔ 우측 상단 **`Create a new scenario`** 클릭
2. 화면 하단 컨트롤 바의 **`...` (More)** 버튼 클릭 ➔ **`Import Blueprint`** 선택
3. 본 레포지토리의 **`blueprint.json`** 파일 업로드

---

### 4. 모듈별 계정 및 변수 재설정 (필수 ⚠️)

가져온 시나리오는 계정연동이 해제되어 있으므로 아래 모듈을 순서대로 클릭하여 설정해야 합니다.

1. **`Tools 4 (Set Variable)`**
   - `Value` 항목에 수집하고자 하는 RSS 피드 URL 배열 등록/수정
2. **`Gmail 14 (Search emails)`**
   - `Connection` ➔ `Add` 클릭 후 지메일 계정 연동 (**연동 시 전체 권한 허용 필수**)
   - `Filter type`: `Complex filter`
   - `Query`: `label:Newsletter newer_than:2d`
3. **`Tools 17 (Text Aggregator)`**
   - `Text` 입력칸에 `Gmail 14` 모듈의 **`Snippet`** 변수가 정상 매핑되어 있는지 확인
4. **`Google Gemini AI 10 (Generate a response)`**
   - `Connection` ➔ Gemini API Key 연결
   - `AI Model`: `gemini-1.5-flash` 또는 `gemini-2.0-flash` 선택
   - `Text` 프롬프트 하단 입력 데이터 위치에 `Tools 7`과 `Tools 17`의 `text` 변수가 **보라색 알약(Chip)** 형태로 정상 매핑되었는지 확인
5. **`Google Drive 11 (Upload a file)`**
   - 구글 드라이브 계정 연동 ➔ 마크다운 리포트를 저장할 폴더 선택

---

## 🔍 Troubleshooting Log (트러블슈팅)

| 이슈 현상 | 발생 원인 | 해결 방법 |
| :--- | :--- | :--- |
| **`Not a feed` 에러** | Cloudflare Bot Protection에 의해 특정 RSS 보안 차단 | 차단되는 피드를 제거하고 정상 접근 가능한 RSS URL로 교체 |
| **`403 Scope` 에러** | OAuth 연동 시 Gmail 읽기/조회 권한 미부여 | Google OAuth 재연동 시 지메일 접근 체크박스 전체 허용 |
| **`429 Rate Limit` 에러** | 이메일 전체 본문 전송으로 인한 분당 토큰(250k) 초과 | `Text Content` 대신 `Snippet` 매핑으로 데이터 용량 최적화 |
| **변수 미인식 에러** | 키보드로 작성한 `{{7.text}}` 문자열을 단순 텍스트로 인식 | Make.com GUI 보라색 매핑 팝업창에서 직접 클릭하여 칩(Chip) 형태로 삽입 |

---

## 🛣️ Future Roadmap & Known Issues

현재 파이프라인의 한계점을 보완하기 위한 향후 개발 계획입니다.

- [ ] **Data Deduplication:** Make.com Data Store를 활용해 중복 수집된 뉴스/기사 자동 필터링 로직 구축
- [ ] **Error Handling & Alerting:** API 한도 초과 및 수집 실패 시 Slack/Telegram 에러 알림 연동
- [ ] **Full-Text Web Scraping:** RSS 요약본이 짧은 경우 웹 페이지 HTML 파싱을 통한 본문 정보 보완
- [ ] **Obsidian Git Sync:** GitHub API 연동을 통해 옵시디언 Vault 레포지토리로 직접 커밋(Commit) 자동화

---

## 📄 License

MIT License
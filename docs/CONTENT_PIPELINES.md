# 콘텐츠 파이프라인 가이드 (YouTube · Gmail · 시각자료)

## 개요
이 문서는 YouTube 키워드 수집, Gmail 라벨 기반 뉴스레터 인입, 이미지/다이어그램/차트/영상 임베드를 포함하는 자동화 파이프라인을 설명합니다.

## 환경 변수 설정
`.env` 파일에 아래 키를 필요에 맞게 설정합니다. (자세한 주석은 `env.example` 참고)

- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`
- YouTube: `YOUTUBE_API_KEY`, `YOUTUBE_KEYWORDS`, `YOUTUBE_MAX_RESULTS`, `YOUTUBE_REGION_CODE`, `YOUTUBE_PUBLISHED_AFTER_DAYS`, `YOUTUBE_CHANNELS_ENABLED`, `YOUTUBE_WATCHLIST_ENABLED`, `YOUTUBE_KEYWORD_GROUPS_ENABLED`
- Gmail: `GOOGLE_CLIENT_SECRET_FILE`, `GOOGLE_TOKEN_FILE`, `GMAIL_LABEL`
- 미디어: `GENERATE_CHARTS`, `GENERATE_DIAGRAMS`, `GENERATE_VIDEO`

## 의존성 설치 (Windows PowerShell)
```powershell
python -m venv venv
venv\Scripts\pip.exe install -r requirements.txt
```

## 실행 방법
- 1회 실행:
```powershell
venv\Scripts\python.exe -m automation.geeknews_pipeline --max-posts 5
```
- 주기 실행(스케줄러):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_windows_task.ps1 -PythonPath "venv\Scripts\python.exe" -IntervalMinutes 60 -TaskName "MyBlogPipeline"
```

## 구성요소
- 수집기: `automation/sources/youtube_collector.py`, `automation/sources/gmail_collector.py`
- 미디어: `automation/media/charts.py`, `automation/media/video.py`
- 파이프라인: `automation/geeknews_pipeline.py`
- 스케줄러: `scripts/run_scheduler.py`

## 동작 흐름
1) 소스 수집: RSS + (YouTube: 채널/워치리스트/키워드 그룹) + (Gmail 선택적)
2) 중복 제거 (`data/geeknews_state.json` 기준)
3) 필터링/우선순위 결정 (`ContentFilter`) + **카테고리 자동 태깅** + **시리즈 메타데이터**
4) 웹 연구(선택) → AI 요약/인사이트 생성 (`QAContentGenerator`)
5) 포스트 생성: front matter에 `thumbnail`, `video_url`, `images`, `charts`, `category`, `series`, `series_order` 지원
6) Git 자동 푸시(환경변수 `AUTO_GIT_PUSH=true` 시)

## YouTube 콘텐츠 수집
파이프라인은 세 가지 방식으로 YouTube 콘텐츠를 수집합니다:

### 1. 채널 기반 수집 (우선순위 높음)
특정 채널의 최신 동영상을 안정적으로 수집합니다.

**채널 설정 파일**: `data/youtube_channels.json`
```json
{
  "channels": [
    {
      "id": "UCxX9wt5FWQUAAz4UrysqK9A",
      "name": "Playwright",
      "handle": "@Playwright",
      "category": "qa-engineer",
      "priority": "high",
      "enabled": true,
      "description": "공식 Playwright 채널"
    }
  ]
}
```

**채널 관리**:
- `enabled: true`: 활성 채널만 수집
- `priority`: 우선순위 표시 (실제 수집 순서는 파일 순서대로)
- `category`: 블로그 포스트 카테고리 자동 분류 (향후 지원)
- `series`, `series_order`: 시리즈 관리 (선택사항, 워치리스트와 동일하게 사용 가능)

**채널 ID 찾기**:
- 채널 페이지 → 소스 보기 → `"channelId":"UC..."`
- 또는 YouTube Data API의 `channels.list` 사용

### 2. 워치리스트 기반 수집 (중간 우선순위)
특정 비디오 ID를 직접 지정하여 중요한 콘텐츠를 수집합니다.

**워치리스트 설정 파일**: `data/youtube_watchlist.json`
```json
{
  "watchlist": [
    {
      "video_id": "mCy4ZJZvRMc",
      "title": "Get started with end-to-end testing: Playwright",
      "category": "qa-engineer",
      "priority": "high",
      "enabled": true,
      "description": "Playwright 입문 튜토리얼",
      "tags": ["playwright", "beginner", "tutorial"]
    }
  ]
}
```

**워치리스트 관리**:
- `video_id`: YouTube URL의 `watch?v=` 뒤에 오는 11자리 문자열
  - 예: `https://www.youtube.com/watch?v=mCy4ZJZvRMc` → `mCy4ZJZvRMc`
- `enabled: true`: 활성 비디오만 수집
- `priority`, `tags`: 분류 및 우선순위 표시용
- 날짜 필터 없음: 워치리스트는 발행일과 관계없이 수집

**시리즈 관리**:
워치리스트에서 시리즈 콘텐츠를 체계적으로 관리할 수 있습니다:
```json
{
  "video_id": "mCy4ZJZvRMc",
  "title": "Get started with end-to-end testing: Playwright (Ep.1)",
  "series": "Playwright 입문",
  "series_order": 1,
  "enabled": true
}
```
- `series`: 시리즈 이름 (포스트 front matter에 추가됨)
- `series_order`: 시리즈 내 순서 (1부터 시작)
- 시리즈 정보는 블로그에서 연속 콘텐츠 탐색에 활용

**사용 사례**:
- 중요한 튜토리얼 시리즈 (예: Playwright 입문편)
- 특정 컨퍼런스 발표
- 추천받은 핵심 콘텐츠
- "스타트 워치리스트"로 입문자 가이드 제공

### 3. 키워드 그룹 기반 수집 (카테고리 자동 태깅)
카테고리별로 그룹화된 키워드로 검색하여 자동으로 카테고리를 태깅합니다.

**키워드 그룹 설정 파일**: `data/youtube_keyword_groups.json`
```json
{
  "keyword_groups": [
    {
      "name": "playwright",
      "category": "qa-engineer",
      "priority": "high",
      "enabled": true,
      "keywords": [
        "Playwright trace viewer",
        "pytest fixtures parametrize best practices",
        "Playwright test parallel sharding GitHub Actions",
        "Allure report Playwright Python"
      ],
      "description": "Playwright 테스트 자동화 관련 콘텐츠"
    },
    {
      "name": "cicd",
      "category": "learning",
      "priority": "high",
      "enabled": true,
      "keywords": [
        "GitHub Actions reusable workflows matrix",
        "Argo CD progressive delivery",
        "Terraform in CI security scanning"
      ],
      "description": "CI/CD 및 GitOps 관련 콘텐츠"
    }
  ]
}
```

**키워드 그룹 관리**:
- `name`: 그룹 식별자
- `category`: 블로그 포스트 카테고리 (`qa-engineer`, `learning`, `daily-life`)
- `keywords`: 해당 그룹의 검색 키워드 리스트 (OR 조건)
- `enabled: true`: 활성 그룹만 수집
- **자동 카테고리 태깅**: 수집된 비디오에 자동으로 `category` 메타데이터 추가

**키워드 그룹 vs 단일 키워드**:
- 키워드 그룹 활성 (`YOUTUBE_KEYWORD_GROUPS_ENABLED=true`): 그룹별로 수집 + 카테고리 태깅
- 키워드 그룹 비활성 (`YOUTUBE_KEYWORD_GROUPS_ENABLED=false`): 기존 방식 (`YOUTUBE_KEYWORDS` 문자열 사용)

### 수집 테스트
파이프라인 실행 전 수집 기능을 테스트할 수 있습니다:

```powershell
# 특정 채널 정보 조회
python scripts/test_youtube_channel.py --channel-id UCxX9wt5FWQUAAz4UrysqK9A --info-only

# 특정 채널 수집 테스트 (최대 3개)
python scripts/test_youtube_channel.py --channel-id UCxX9wt5FWQUAAz4UrysqK9A --max-results 3

# 설정 파일의 모든 채널 테스트
python scripts/test_youtube_channel.py --test-config --max-results 3

# 워치리스트 수집 테스트
python scripts/test_youtube_channel.py --test-watchlist
```

### 수집 순서 및 중복 제거
1. **채널** 수집 (우선순위 높음)
2. **워치리스트** 수집 (중간 우선순위)
3. **키워드 그룹** 수집 (카테고리 자동 태깅)
   - 그룹별로 순차 수집
   - 각 비디오에 `category`, `keyword_group` 메타데이터 추가
4. **중복 제거**: `guid` 기준으로 자동 제거 (먼저 수집된 것 유지)

**카테고리 결정 우선순위**:
1. 채널 설정의 `category` (향후 지원 예정)
2. 키워드 그룹의 `category` ← 현재 사용
3. 기본값: `learning`

## 다이어그램 / 차트 / 영상
- Mermaid: `_includes/head.html`에서 자동 초기화. Markdown에 ```mermaid 코드블록 사용.
- 차트: `automation/media/charts.py`의 `generate_trend_chart`로 PNG 생성 → `assets/img/auto/` 저장 후 본문에 `![...]()` 삽입.
- 영상: `automation/media/video.py`의 `generate_narration_video`로 mp4 생성 후 Front matter `video_url` 또는 파일 경로 임베드.

## Gmail 최초 인증
- `GOOGLE_CLIENT_SECRET_FILE` 경로의 JSON(로컬 전용, git 커밋 금지) 준비
- 최초 실행 시 브라우저 인증 완료 → `GOOGLE_TOKEN_FILE`에 토큰 생성

## 트러블슈팅
- YouTube 쿼터 초과: 
  - 키워드 범위 축소, `YOUTUBE_MAX_RESULTS` 감소
  - 일부 채널 비활성화 (`enabled: false`)
  - 워치리스트 항목 축소
- 채널 수집 실패: 채널 ID 확인, API 키 권한 확인
- 워치리스트 수집 실패: 
  - `video_id` 형식 확인 (11자리 문자열)
  - 비공개/삭제된 비디오 확인
  - PLACEHOLDER로 시작하는 ID는 실제 ID로 교체 필요
- 수집 비활성화: 
  - 채널: `.env`에서 `YOUTUBE_CHANNELS_ENABLED=false`
  - 워치리스트: `.env`에서 `YOUTUBE_WATCHLIST_ENABLED=false`
  - 키워드 그룹: `.env`에서 `YOUTUBE_KEYWORD_GROUPS_ENABLED=false` (기존 단일 키워드 방식으로 전환)
- 키워드 그룹 수집 실패:
  - 그룹별 `keywords` 리스트 확인
  - 특정 그룹만 비활성화: `enabled: false` 설정
  - 카테고리 값 확인 (`qa-engineer`, `learning`, `daily-life` 중 하나)
- Gmail 인증 실패: 토큰 파일 삭제 후 재인증
- Windows 작업 스케줄러 동작 확인: `Get-ScheduledTask -TaskName MyBlogPipeline | Get-ScheduledTaskInfo`



# 콘텐츠 파이프라인 가이드 (YouTube · Gmail · 시각자료)

## 개요
이 문서는 YouTube 키워드 수집, Gmail 라벨 기반 뉴스레터 인입, 이미지/다이어그램/차트/영상 임베드를 포함하는 자동화 파이프라인을 설명합니다.

## 환경 변수 설정
`.env` 파일에 아래 키를 필요에 맞게 설정합니다. (자세한 주석은 `env.example` 참고)

- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`
- YouTube: `YOUTUBE_API_KEY`, `YOUTUBE_KEYWORDS`, `YOUTUBE_MAX_RESULTS`, `YOUTUBE_REGION_CODE`, `YOUTUBE_PUBLISHED_AFTER_DAYS`
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
1) 소스 수집: RSS + (YouTube/Gmail 선택적)
2) 중복 제거 (`data/geeknews_state.json` 기준)
3) 필터링/우선순위 결정 (`ContentFilter`)
4) 웹 연구(선택) → AI 요약/인사이트 생성 (`QAContentGenerator`)
5) 포스트 생성: front matter에 `thumbnail`, `video_url`, `images`, `charts` 지원
6) Git 자동 푸시(환경변수 `AUTO_GIT_PUSH=true` 시)

## 다이어그램 / 차트 / 영상
- Mermaid: `_includes/head.html`에서 자동 초기화. Markdown에 ```mermaid 코드블록 사용.
- 차트: `automation/media/charts.py`의 `generate_trend_chart`로 PNG 생성 → `assets/img/auto/` 저장 후 본문에 `![...]()` 삽입.
- 영상: `automation/media/video.py`의 `generate_narration_video`로 mp4 생성 후 Front matter `video_url` 또는 파일 경로 임베드.

## Gmail 최초 인증
- `GOOGLE_CLIENT_SECRET_FILE` 경로의 JSON(로컬 전용, git 커밋 금지) 준비
- 최초 실행 시 브라우저 인증 완료 → `GOOGLE_TOKEN_FILE`에 토큰 생성

## 트러블슈팅
- YouTube 쿼터 초과: 키워드 범위 축소, `YOUTUBE_MAX_RESULTS` 감소
- Gmail 인증 실패: 토큰 파일 삭제 후 재인증
- Windows 작업 스케줄러 동작 확인: `Get-ScheduledTask -TaskName MyBlogPipeline | Get-ScheduledTaskInfo`



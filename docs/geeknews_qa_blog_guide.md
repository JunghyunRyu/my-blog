# GeekNews QA-Driven Blog Automation Guide

이 문서는 GeekNews RSS 피드를 기반으로 QA 전략이 가미된 블로그 콘텐츠를 주기적으로 생성하고 게시하는 자동화 파이프라인 구축 방법을 정리합니다. 파이프라인은 크게 **데이터 취합 → AI 분석 및 QA 강화 → 게시 및 반복 운영** 단계로 구성됩니다.

## 1. 데이터 취합

### 1.1 소스 선택
- **RSS 피드:** <https://feeds.feedburner.com/geeknews-feed>
- **웹 페이지:** <https://news.hada.io/> (필요시 보충 정보 크롤링)
- (선택) GeekNews에서 공식 API를 제공한다면 API 엔드포인트 활용. 없을 경우 RSS/HTML 파싱으로 대체합니다.

### 1.2 수집 아키텍처
1. **수집 스케줄러**
   - `cron`, GitHub Actions, 또는 기존 `scheduler.py`와 같은 파이썬 스케줄러로 주기 실행합니다.
   - 반복 주기는 GeekNews 업데이트 빈도(예: 30분~1시간)에 맞춰 조정합니다.
2. **피드 파서**
   - `feedparser` 라이브러리로 RSS 항목을 파싱합니다.
   - 항목 필드: 제목, 링크, 게시 시간, 요약, 태그 등을 추출합니다.
3. **중복 필터링**
   - 게시한 항목의 GUID/링크를 로컬 DB(SQLite)나 파일(JSON)로 저장.
   - 새 항목만 후속 단계로 전달합니다.
4. **(선택) 상세 수집**
   - 필요시 각 기사 링크를 HTTP 요청으로 가져와 본문을 정제합니다.
   - BeautifulSoup 등으로 본문을 HTML→텍스트 변환 후 요약에 활용합니다.

### 1.3 데이터 모델 예시
```json
{
  "guid": "https://news.hada.io/topic?id=12345",
  "title": "오픈AI, 새로운 GPT 모델 공개",
  "summary": "기사 요약 텍스트",
  "content": "풀 본문 텍스트",
  "published_at": "2024-05-20T05:30:00Z",
  "tags": ["AI", "모델"],
  "collected_at": "2024-05-20T06:00:00Z"
}
```

## 2. AI 분석 및 QA 강화

### 2.1 목표 정의
- 단순 기사 요약이 아니라 **질문·답변(QA) 관점에서 유용한 통찰** 제공.
- 예상 독자 질문을 발굴하고, 기사와 관련된 배경 지식/추가 리소스까지 연결합니다.

### 2.2 전처리
- 기사 본문과 메타데이터를 AI 입력에 적합하게 정리합니다.
- 언어 모델 토큰 제한을 고려해 최대 길이 조절 및 Bullet 구조화.

### 2.3 프롬프트 전략
1. **정보 추출**: 핵심 사실, 수치, 인용을 정리.
2. **QA 쿼리 생성**: 독자가 궁금해할 질문 3~5개 작성.
3. **답변 생성**: 각 질문에 대해 기사 내용과 보조 정보로 근거 있는 답변 작성.
4. **추가 가이드**: 영향, 전망, 실무 적용 팁 등 Value-Add 제공.

예시 프롬프트 구조:
```
당신은 GeekNews 분석가입니다. 다음 기사 내용을 바탕으로
1) 핵심 요약 (3문장 이내)
2) 독자가 궁금해할 질문 3~5개
3) 각 질문에 대한 근거 있는 답변
4) 추가로 파고들면 좋을 Follow-up 주제 2개
를 한국어로 작성하세요.
```

### 2.4 품질 보증(QA) 체크리스트
- **사실 검증**: 기사 원문 내용과 상충 여부 확인.
- **출처 표기**: 링크, 참고 문헌 명시.
- **톤 & 스타일**: 블로그 톤에 맞는 어조(전문적이지만 친근하게).
- **중복 방지**: 비슷한 주제의 이전 포스트와 비교하여 내용 차별화.
- **자동화 로깅**: 생성 과정에서 사용된 모델, 파라미터, 토큰 수 기록.

### 2.5 기술 선택
- OpenAI GPT-4o/4.1, Anthropic Claude, 혹은 사내 LLM 등.
- 프롬프트/출력을 버전 관리하여 재현 가능성 확보.
- 대량 요청 시 큐 시스템과 재시도 로직 구현.

## 3. 블로그 게시 및 운영

### 3.1 Jekyll 기반 게시 (현재 레포 구조 기준)
- `_posts/YYYY-MM-DD-title.md` 형식으로 마크다운 포스트 생성.
- Front Matter 예시:
  ```yaml
  ---
  layout: post
  title: "오픈AI 신규 모델 발표 – QA 분석"
  date: 2024-05-20 09:00:00 +0900
  categories: [GeekNews, AI]
  tags: [QA, Trend]
  summary: "핵심 요약과 주요 질의응답 정리"
  original_url: "https://news.hada.io/topic?id=12345"
  ---
  ```
- 본문에는 `요약`, `주요 Q&A`, `Follow-up` 섹션 등을 Markdown으로 구성합니다.

### 3.2 자동 생성 스크립트 흐름
1. 신규 항목 리스트 반복
2. AI 분석 결과를 Markdown 템플릿에 주입
3. 파일 저장 후 `git add/commit/push`
4. 필요시 Netlify/GitHub Pages 빌드 트리거

`automation/geeknews_pipeline.py` 스크립트가 위 흐름을 구현하고 있으며, `_posts/`에 QA 중심 마크다운 파일을 생성합니다.【F:automation/geeknews_pipeline.py†L1-L205】

실행 예시:

```bash
python -m automation.geeknews_pipeline --max-posts 3
```

`scheduler.py`를 사용하면 위 파이프라인을 주기적으로 실행하도록 예약할 수 있습니다.【F:scheduler.py†L1-L41】

로컬 환경에서 네트워크 없이 동작을 검증하려면 `automation/sample_feed.xml`을 `--feed-url`로 지정해 샘플 RSS를 사용할 수 있습니다.【F:automation/sample_feed.xml†L1-L14】

```bash
# macOS/Linux
python -m automation.geeknews_pipeline \
  --feed-url "$(python - <<'PY'
from pathlib import Path
print(Path('automation/sample_feed.xml').resolve().as_uri())
PY
)" --max-posts 1 --timezone UTC
```

PowerShell을 사용할 경우에는 아래와 같이 파일 경로를 미리 변수로 변환한 뒤 실행하면 됩니다.

```powershell
$feedUrl = python -c "from pathlib import Path; print(Path('automation/sample_feed.xml').resolve().as_uri())"
python -m automation.geeknews_pipeline --feed-url $feedUrl --max-posts 1 --timezone UTC
```

### 3.3 게시 전 QA
- 로컬에서 `bundle exec jekyll build` 혹은 `jekyll serve`로 렌더링 확인.
- 링크 체크, 이미지 미리보기, 마크다운 렌더링 확인.
- 자동 테스트(예: 링크 유효성 검사 스크립트) 추가 가능.

### 3.4 배포 & 모니터링
- GitHub Pages 혹은 별도 호스팅에 푸시 후 자동 배포.
- 실패 시 Slack/Webhook 알림.
- 페이지 뷰, 체류 시간 등 분석 도구(GA, Plausible)로 콘텐츠 성과 측정.

## 4. 반복 운영 전략

1. **스케줄 관리**: 시간대/주기에 따라 RSS fetch → AI 생성 → 게시.
2. **피드백 루프**: 독자 반응, FAQ 업데이트, 토픽 선정 기준 보정.
3. **모델 업데이트**: 모델 성능 변화에 따라 프롬프트/파라미터 조정.
4. **토픽 큐 관리**: `topics.json`과 같은 대기 토픽 목록을 유지하고, 소진 시 자동 갱신 로직 구현.【F:topics.json†L1-L31】
5. **에러 핸들링**: 수집 실패, API 제한, 빌드 실패 등을 로깅/알림으로 즉시 대응.

## 5. 향후 확장 아이디어
- 다국어 번역 버전 자동 생성.
- 독자 질문 수집(댓글/폼) → 다음 포스트에 반영.
- 음성/요약 팟캐스트 버전 자동 생성.
- 주간/월간 요약 뉴스레터와 연동.

---
이 가이드에 따라 수집·분석·게시 자동화를 구성하면 GeekNews 기반 QA 콘텐츠를 안정적으로 운영할 수 있습니다.

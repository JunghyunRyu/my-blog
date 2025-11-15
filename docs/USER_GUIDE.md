# QA 블로그 자동화 시스템 사용자 가이드

이 문서는 QA 블로그 자동화 시스템의 설치, 설정, 사용 방법을 안내합니다.

## 목차

1. [시스템 개요](#시스템-개요)
2. [설치 및 설정](#설치-및-설정)
3. [기본 사용법](#기본-사용법)
4. [고급 기능](#고급-기능)
5. [트러블슈팅](#트러블슈팅)

---

## 시스템 개요

QA 블로그 자동화 시스템은 다음과 같은 기능을 제공합니다:

- **다양한 데이터 소스 수집**: GeekNews, Reddit, Dev.to, Stack Overflow 등
- **멀티 AI 분석**: OpenAI, Claude, Perplexity, Gemini를 활용한 콘텐츠 강화
- **자동 블로그 포스트 생성**: Jekyll 호환 마크다운 파일 생성
- **소셜 미디어 자동 배포**: Instagram, LinkedIn, Twitter 자동 게시
- **품질 검증 및 개선**: 자동 품질 점수 계산 및 개선 제안

---

## 설치 및 설정

### 1. 사전 요구사항

- Python 3.8 이상
- Windows 10/11 (PowerShell)
- Git (자동 Push 기능 사용 시)

### 2. 저장소 클론

```powershell
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli
```

### 3. 가상 환경 생성 및 활성화

```powershell
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
.\venv\Scripts\Activate.ps1
```

### 4. 의존성 설치

```powershell
pip install -r requirements.txt
```

### 5. 환경 변수 설정

```powershell
# env.example을 .env로 복사
Copy-Item env.example .env

# .env 파일 편집 (실제 API 키 입력)
notepad .env
```

**최소 필수 설정**:
- `OPENAI_API_KEY`: OpenAI API 키 (필수)

**권장 설정**:
- `CLAUDE_API_KEY`: Claude API 키 (기술 분석 강화)
- `PERPLEXITY_API_KEY`: Perplexity API 키 (최신 정보 수집)

자세한 API 키 발급 방법은 [API_KEYS_GUIDE.md](./API_KEYS_GUIDE.md)를 참조하세요.

---

## 기본 사용법

### 1. 기본 파이프라인 실행

```powershell
# 기본 실행 (최대 10개 포스트)
python -m automation.geeknews_pipeline

# 포스트 수 지정
python -m automation.geeknews_pipeline --max-posts 5
```

### 2. 향상된 파이프라인 실행

```powershell
# 모든 개선사항 포함 파이프라인
python -m automation.enhanced_pipeline_example
```

### 3. 특정 소스만 수집

```powershell
# Reddit만 수집
python -c "from automation.enhanced_sources import RedditCollector; import asyncio; collector = RedditCollector('client_id', 'secret'); asyncio.run(collector.collect())"
```

---

## 고급 기능

### 1. 향상된 프롬프트 시스템 사용

`.env` 파일에 다음 설정 추가:
```ini
USE_ENHANCED_PROMPTS=true
PROMPT_PERSONA=senior_qa_architect
PROMPT_ANALYSIS_TYPE=deep_technical
PROMPT_FORMAT_TYPE=case_study
PROMPT_LEVEL=intermediate
```

### 2. 멀티 AI 분석 활성화

여러 AI API 키를 설정하면 자동으로 멀티 AI 분석이 활성화됩니다:
- OpenAI: 실무 적용 가이드
- Claude: 기술적 심층 분석
- Perplexity: 최신 트렌드 수집
- Gemini: 멀티모달 분석

### 3. 소셜 미디어 자동 배포

```python
from automation.social_media_publisher import SocialMediaOrchestrator
from pathlib import Path

orchestrator = SocialMediaOrchestrator()

# 모든 플랫폼에 게시
post_path = Path("_posts/2025-01-27-example.md")
results = await orchestrator.publish_to_all_platforms(post_path)

# 예약 게시
from datetime import datetime, timedelta
tomorrow = datetime.now() + timedelta(days=1)
tomorrow = tomorrow.replace(hour=9, minute=0)

schedule_id = orchestrator.schedule_post(
    post_path,
    ["instagram", "linkedin", "twitter"],
    tomorrow
)
```

### 4. 품질 검증 및 개선

품질 점수가 80점 미만인 포스트는 자동으로 개선됩니다:
- 추가 섹션 자동 생성
- 링크 및 리소스 추가
- 구조 개선

---

## 트러블슈팅

### 문제: API 키 오류

**증상**: `RuntimeError: API 호출 실패`

**해결 방법**:
1. `.env` 파일에 키가 올바르게 설정되었는지 확인
2. API 키 형식 확인 (공백, 따옴표 제거)
3. API 키가 만료되지 않았는지 확인
4. Rate limit 초과 여부 확인

### 문제: Reddit 수집 실패

**증상**: `Reddit 인증 실패`

**해결 방법**:
1. Reddit API 앱이 올바르게 생성되었는지 확인
2. `REDDIT_CLIENT_ID`와 `REDDIT_CLIENT_SECRET` 확인
3. `REDDIT_USER_AGENT` 설정 확인
4. Reddit API rate limit 확인

### 문제: 소셜 미디어 게시 실패

**증상**: `Instagram/LinkedIn/Twitter 게시 실패`

**해결 방법**:
1. OAuth 토큰이 만료되지 않았는지 확인
2. 필요한 권한이 모두 부여되었는지 확인
3. 앱 검수 상태 확인 (프로덕션 사용 시)
4. Rate limit 확인

### 문제: 이미지 생성 실패

**증상**: `Pillow 이미지 생성 실패`

**해결 방법**:
1. Pillow 패키지 설치 확인: `pip install Pillow`
2. 한글 폰트 파일 경로 확인 (선택사항)
3. 이미지 저장 경로 권한 확인

### 문제: 비동기 오류

**증상**: `RuntimeError: Event loop is closed`

**해결 방법**:
Windows 환경에서는 다음 코드 추가:
```python
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

### 문제: Git Push 실패

**증상**: `Git push 실패`

**해결 방법**:
1. Git 사용자 정보 설정 확인:
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your-email@example.com"
   ```
2. 원격 저장소 설정 확인
3. SSH 키 또는 Personal Access Token 설정

---

## 성능 최적화

### 1. 병렬 처리

시스템은 기본적으로 병렬 처리를 사용합니다:
- 여러 소스 동시 수집
- 여러 AI 동시 분석
- 여러 플랫폼 동시 게시

### 2. 캐싱

중복 콘텐츠는 자동으로 필터링됩니다:
- URL 기반 중복 제거
- 제목 기반 유사도 검사

### 3. Rate Limit 관리

각 API의 rate limit을 자동으로 관리합니다:
- 요청 간격 자동 조정
- 재시도 메커니즘

---

## 로그 확인

로그는 다음 위치에 저장됩니다:
- 콘솔 출력 (기본)
- 파일 로그 (설정 시)

로그 레벨 설정:
```python
import logging
logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR
```

---

## 다음 단계

1. [API_KEYS_GUIDE.md](./API_KEYS_GUIDE.md)에서 필요한 API 키 발급
2. `.env` 파일에 API 키 설정
3. 기본 파이프라인 실행 테스트
4. 소셜 미디어 API 설정 (선택사항)
5. 정기 실행 스케줄 설정 (선택사항)

---

**마지막 업데이트**: 2025-01-27


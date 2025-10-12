# My Blog CLI - 블로그 자동화 도구

Windows PowerShell 환경에서 작동하는 블로그 콘텐츠 자동화 시스템입니다.

## 주요 기능

### 1. GeekNews QA 전문가급 자동화 시스템 ⭐ NEW!
GeekNews에서 IT 신규 뉴스를 수집하여 QA Engineer 관점의 전문적인 블로그 포스트를 자동 생성합니다.

### 2. 코드깎는노인 트랜스크립트 스크래퍼
코드깎는노인 사이트의 강의 트랜스크립트를 자동으로 추출합니다.

---

# 📰 GeekNews QA 전문가급 자동화 시스템

## ✨ 주요 특징

- **AI/트렌드 자동 필터링**: AI 관련 항목 필수 포함 + 인기도 기반 선별
- **웹 연구 통합**: DuckDuckGo 검색 + HackerNews 전문가 의견 수집
- **QA Engineer 관점 강화**: 실무 가이드, 학습 로드맵, 전문가 의견 제공
- **심층 분석**: OpenAI GPT 기반 전문적인 콘텐츠 생성
- **완전 자동화**: RSS 수집부터 블로그 포스트 생성까지 원클릭

## 🚀 빠른 시작

### 1. 환경 설정

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
Copy-Item env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 설정
```

### 2. 실행

```powershell
# 기본 실행 (최대 10개 포스트)
python -m automation.geeknews_pipeline

# 포스트 개수 지정
python -m automation.geeknews_pipeline --max-posts 5

# 웹 연구 비활성화 (속도 개선)
python -m automation.geeknews_pipeline --no-web-research

# 최소 투표수 설정
python -m automation.geeknews_pipeline --min-votes 20
```

### 3. 스케줄러로 주기 실행

```powershell
# .env 파일에서 설정 조정 후
python scheduler.py
```

## 📋 시스템 아키텍처

### 파이프라인 흐름

```
1. RSS 피드 수집
   ↓
2. 중복 필터링
   ↓
3. AI/트렌드 필터링 + 우선순위 결정
   ↓
4. 웹 연구 (DuckDuckGo, HackerNews)
   ↓
5. OpenAI 기반 전문가급 QA 콘텐츠 생성
   ↓
6. Jekyll 블로그 포스트 작성 (_posts/)
   ↓
7. 상태 저장
```

### 필터링 기준

- **AI 관련 항목**: 무조건 포함 (최우선)
- **인기도**: 투표수 10개 이상 (설정 가능)
- **트렌드**: 최신 기술 관련 키워드
- **우선순위 점수**: AI(40점) + 투표수(30점) + 댓글(10점) + 트렌드(10점) + QA(10점)

## 📝 생성되는 콘텐츠 구조

```markdown
---
layout: post
title: "기사 제목"
categories: [GeekNews, QA, AI]
tags: [GeekNews, QA, AI]
---

## 요약
[3-4문장 핵심 요약]

## QA Engineer가 알아야 할 핵심 내용
- 이 기술이 QA 업무에 미치는 영향
- 테스트 전략 고려사항

## 실무 적용 가이드
### 1. 테스트 자동화 개선
실행 단계와 구체적인 방법

### 2. 품질 검증 프로세스
실무 적용 가이드

## 학습 로드맵
### 즉시 학습 (1-2주)
- 배워야 할 기술
- 추천 학습 자료

### 단기 학습 (1-3개월)
...

## 전문가 의견
### 시니어 QA 엔지니어 관점
> 전문가의 조언

### 테스트 자동화 전문가 관점
...

## 주요 Q&A
**Q:** 질문
**A:** 상세한 답변

## Follow-up 제안
- 추가 조사 항목

## 참고 자료
- [공식 문서](url)
- [튜토리얼](url)
```

## ⚙️ 설정 옵션

### 환경 변수 (.env 파일)

```bash
# 필수: OpenAI API 키
OPENAI_API_KEY=your_api_key_here

# 선택사항
OPENAI_MODEL=gpt-4o-mini              # 모델 선택
MIN_VOTE_COUNT=10                      # 최소 투표수
MAX_POSTS_PER_RUN=10                   # 최대 포스트 수
ENABLE_WEB_RESEARCH=true               # 웹 연구 활성화
PIPELINE_INTERVAL_SECONDS=3600         # 스케줄러 주기 (초)
```

### 명령줄 옵션

```powershell
--max-posts N          # 최대 포스트 수 (기본값: 10)
--min-votes N          # 최소 투표수 (기본값: 10)
--no-web-research      # 웹 연구 비활성화
--enable-scraping      # GeekNews 웹 스크래핑 활성화
--feed-url URL         # RSS 피드 URL
--timezone TZ          # 시간대 (기본값: Asia/Seoul)
```

## 📊 성공 지표

- ✅ AI 관련 항목 100% 포함
- ✅ 하루 5-10개 고품질 포스트 생성
- ✅ 전문가 의견 평균 2-3개 포함
- ✅ 웹 검색 기반 참고 자료 5개 이상
- ✅ QA Engineer 실무 가이드 포함
- ✅ 학습 로드맵 제공

## 🔧 문제 해결

### OpenAI API 오류
```powershell
# API 키 확인
echo $env:OPENAI_API_KEY

# .env 파일 확인
cat .env
```

### 웹 검색 실패
```powershell
# 웹 연구 비활성화하고 실행
python -m automation.geeknews_pipeline --no-web-research
```

### 느린 실행 속도
```powershell
# 포스트 개수 줄이기
python -m automation.geeknews_pipeline --max-posts 3

# 웹 연구 비활성화
python -m automation.geeknews_pipeline --no-web-research
```

---

# 🎓 코드깎는노인 트랜스크립트 스크래퍼

## 🚀 빠른 시작

### 1단계: 설치
```powershell
# 의존성 자동 설치
./install.bat
```

### 2단계: 로그인 설정 (최초 1회만)
```powershell
# 구글 계정 로그인 (브라우저가 열림)
./setup_auth.bat
```

### 3단계: 트랜스크립트 스크래핑
```powershell
# 강의 URL로 트랜스크립트 추출
./scrape.bat "https://cokac.com/list/lec019/146"
```

## 📖 상세 사용법

### PowerShell 직접 실행
```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 초기 로그인 설정
python main.py --setup-auth

# 트랜스크립트 스크래핑
python main.py --scrape --url "https://cokac.com/list/lec019/146"

# 세션 유효성 확인
python main.py --verify-session

# 현재 설정 확인
python main.py --config
```

### 배치 파일 실행
```cmd
install.bat           # 설치
setup_auth.bat        # 로그인 설정
scrape.bat <URL>      # 스크래핑
verify_session.bat    # 세션 확인
```

## 📁 프로젝트 구조
```
my-blog-cli/
├── scraper/
│   ├── __init__.py
│   ├── config.py           # 설정 관리
│   ├── auth_manager.py     # 구글 OAuth 로그인
│   └── page_scraper.py     # 페이지 스크래핑
├── data/
│   ├── cokac_storage.json  # 로그인 세션 저장
│   └── transcripts/        # 추출된 트랜스크립트
├── main.py                 # 메인 실행 스크립트
├── requirements.txt        # Python 의존성
├── install.bat            # 설치 스크립트
├── setup_auth.bat         # 로그인 설정
├── scrape.bat            # 스크래핑 실행
└── verify_session.bat    # 세션 확인
```

## 🔧 주요 기능

### ✅ 자동화된 로그인
- 구글 OAuth 인증 지원
- 세션 상태 저장 및 재사용
- 로그인 유효성 자동 검증

### 🎯 스마트 스크래핑
- 네트워크 API 응답 후킹
- DOM 기반 백업 추출
- 스마트 스크롤로 전체 로드
- 중복 제거 및 데이터 정제

### 💾 다양한 출력 형식
- JSON: 구조화된 메타데이터 포함
- TXT: 읽기 쉬운 텍스트 형식
- 타임스탬프 및 통계 정보 포함

### 🖥️ Windows 최적화
- PowerShell 환경 최적화
- 한글 인코딩 지원
- 배치 파일로 간편 실행

## ⚙️ 설정 옵션

환경변수로 동작을 커스터마이즈할 수 있습니다:

```powershell
# 헤드리스 모드 설정
$env:HEADLESS = "false"  # 브라우저 표시

# 출력 디렉토리 변경
$env:OUTPUT_PATH = "custom/output"

# 타임아웃 설정
$env:TIMEOUT = "60000"   # 60초

# 스크롤 속도 조절
$env:SCROLL_DELAY = "1000"  # 1초
```

## 🚨 문제 해결

### 로그인 관련
```powershell
# 세션 만료 시
./setup_auth.bat

# 세션 상태 확인
./verify_session.bat
```

### 스크래핑 관련
```powershell
# 브라우저 표시 모드로 디버깅
$env:HEADLESS = "false"
python main.py --scrape --url "<URL>"
```

### 권한 관련
```powershell
# PowerShell 실행 정책 설정
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 출력 예시

### JSON 형식
```json
{
  "lecture_url": "https://cokac.com/list/lec019/146",
  "scraped_at": "2025-10-03T14:30:00",
  "transcript_count": 245,
  "transcripts": [
    {
      "index": 0,
      "text": "안녕하세요 코드깎는노인입니다",
      "timestamp": "00:15",
      "source": "dom"
    }
  ]
}
```

### TXT 형식
```
강의 URL: https://cokac.com/list/lec019/146
스크래핑 시간: 2025년 10월 03일 14시 30분
총 트랜스크립트: 245개
================================================================================

  1. [00:15] 안녕하세요 코드깎는노인입니다
  2. [00:23] 오늘은 MCP 서버 만들기에 대해서 알아보겠습니다
  3. [00:31] 먼저 프로젝트 구조부터 살펴보겠습니다
```

## 🔒 보안 및 주의사항

- 로그인 세션은 로컬에만 저장됩니다
- 테스트 전용 계정 사용을 권장합니다
- 이용약관을 준수하여 사용해주세요
- 과도한 요청으로 서버에 부하를 주지 마세요

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. Python 3.8+ 설치 여부
2. 네트워크 연결 상태
3. 코드깎는노인 사이트 접속 가능 여부
4. 브라우저 호환성 (Chromium 기반)

---

**코드깎는노인 트랜스크립트 스크래퍼 v1.0.0**  
Windows PowerShell 환경 최적화 버전




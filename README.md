# 코드깎는노인 트랜스크립트 스크래퍼

Windows PowerShell 환경에서 작동하는 코드깎는노인 사이트의 강의 트랜스크립트 자동 스크래핑 도구입니다.

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




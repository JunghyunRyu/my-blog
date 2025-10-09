@echo off
REM 코드깎는노인 트랜스크립트 스크래퍼 - 설치 스크립트
REM 작성자: Windows PowerShell 환경 최적화

echo ====================================================
echo 🎓 코드깎는노인 트랜스크립트 스크래퍼 설치
echo ====================================================
echo.

REM 현재 디렉토리 확인
echo 📁 현재 작업 디렉토리: %CD%
echo.

REM Python 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo 💡 https://python.org에서 Python 3.8+ 버전을 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Python 버전 확인:
python --version

REM 가상환경 활성화
echo.
echo 🔧 가상환경 활성화 중...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ 가상환경이 활성화되었습니다.
) else (
    echo ⚠️  가상환경을 찾을 수 없습니다. 생성 중...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ 가상환경이 생성되고 활성화되었습니다.
)

REM 의존성 설치
echo.
echo 📦 필수 패키지 설치 중...
pip install --upgrade pip
pip install -r requirements.txt

REM Playwright 브라우저 설치
echo.
echo 🌐 Playwright 브라우저 설치 중...
playwright install chromium

echo.
echo ✅ 설치가 완료되었습니다!
echo.
echo 🚀 다음 단계:
echo    1. setup_auth.bat - 구글 계정 로그인 설정
echo    2. scrape.bat <URL> - 트랜스크립트 스크래핑
echo.
pause


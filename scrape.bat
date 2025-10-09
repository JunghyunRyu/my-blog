@echo off
REM 코드깎는노인 - 트랜스크립트 스크래핑 스크립트
REM 사용법: scrape.bat "https://cokac.com/list/lec019/146"

if "%1"=="" (
    echo ====================================================
    echo 🎯 코드깎는노인 트랜스크립트 스크래핑
    echo ====================================================
    echo.
    echo ❌ 강의 URL을 입력해주세요.
    echo.
    echo 📖 사용법:
    echo    scrape.bat "https://cokac.com/list/lec019/146"
    echo.
    echo 📋 예시 URL:
    echo    - https://cokac.com/list/lec019/146
    echo    - https://cokac.com/list/lec020/200
    echo.
    pause
    exit /b 1
)

echo ====================================================
echo 🎓 코드깎는노인 트랜스크립트 스크래핑
echo ====================================================
echo.
echo 📍 대상 URL: %1
echo.

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 💡 먼저 install.bat을 실행해주세요.
    pause
    exit /b 1
)

REM 스크래핑 실행
python main.py --scrape --url %1

echo.
echo 완료되었습니다. 아무 키나 눌러 종료하세요.
pause


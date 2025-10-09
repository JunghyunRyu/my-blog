@echo off
REM 코드깎는노인 - 초기 로그인 설정 스크립트

echo ====================================================
echo 🔐 코드깎는노인 로그인 설정
echo ====================================================
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

echo 🚀 구글 계정 로그인 설정을 시작합니다...
echo ⚠️  잠시 후 브라우저가 열리면 수동으로 로그인을 완료해주세요.
echo.

REM 로그인 설정 실행
python main.py --setup-auth

echo.
echo 완료되었습니다. 아무 키나 눌러 종료하세요.
pause


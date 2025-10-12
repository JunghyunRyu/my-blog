@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ================================================================================
echo GeekNews QA 전문가급 자동화 시스템
echo ================================================================================
echo.

REM 가상환경 확인 및 활성화
if not exist "venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 설정되지 않았습니다.
    echo.
    echo 해결 방법:
    echo   1. python -m venv venv
    echo   2. .\venv\Scripts\Activate.ps1
    echo   3. pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM OpenAI API 키 확인
if "%OPENAI_API_KEY%"=="" (
    echo [경고] OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.
    echo.
    echo 해결 방법:
    echo   1. .env 파일을 생성하고 OPENAI_API_KEY를 설정하세요.
    echo   2. 또는 PowerShell에서: $env:OPENAI_API_KEY = "your_key"
    echo.
    set /p continue="그래도 계속하시겠습니까? (y/N): "
    if /i not "!continue!"=="y" (
        exit /b 1
    )
)

REM 인자가 있으면 그대로 전달, 없으면 기본 실행
if "%~1"=="" (
    echo [실행] 기본 설정으로 실행 중...
    python -m automation.geeknews_pipeline
) else (
    echo [실행] 사용자 설정으로 실행 중...
    python -m automation.geeknews_pipeline %*
)

echo.
echo ================================================================================
echo 실행 완료
echo ================================================================================
pause


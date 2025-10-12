# GeekNews QA 전문가급 자동화 시스템 실행 스크립트
# Windows PowerShell 최적화

param(
    [int]$MaxPosts = 10,
    [int]$MinVotes = 10,
    [switch]$NoWebResearch,
    [switch]$EnableScraping,
    [string]$FeedUrl = "",
    [switch]$Help
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Show-Header {
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "GeekNews QA 전문가급 자동화 시스템" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Help {
    Write-Host "사용법:" -ForegroundColor Yellow
    Write-Host "  .\run_geeknews.ps1 [-MaxPosts N] [-MinVotes N] [-NoWebResearch] [-EnableScraping]"
    Write-Host ""
    Write-Host "옵션:" -ForegroundColor Yellow
    Write-Host "  -MaxPosts N         최대 포스트 수 (기본값: 10)"
    Write-Host "  -MinVotes N         최소 투표수 (기본값: 10)"
    Write-Host "  -NoWebResearch      웹 연구 비활성화 (속도 개선)"
    Write-Host "  -EnableScraping     GeekNews 웹 스크래핑 활성화"
    Write-Host "  -FeedUrl URL        RSS 피드 URL 지정"
    Write-Host "  -Help               도움말 표시"
    Write-Host ""
    Write-Host "예시:" -ForegroundColor Yellow
    Write-Host "  .\run_geeknews.ps1"
    Write-Host "  .\run_geeknews.ps1 -MaxPosts 5"
    Write-Host "  .\run_geeknews.ps1 -MaxPosts 3 -NoWebResearch"
    Write-Host ""
}

# 도움말 표시
if ($Help) {
    Show-Header
    Show-Help
    exit 0
}

Show-Header

# 가상환경 확인
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[오류] 가상환경이 설정되지 않았습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "  1. python -m venv venv"
    Write-Host "  2. .\venv\Scripts\Activate.ps1"
    Write-Host "  3. pip install -r requirements.txt"
    Write-Host ""
    exit 1
}

# 가상환경 활성화
Write-Host "[1/3] 가상환경 활성화 중..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# OpenAI API 키 확인
if (-not $env:OPENAI_API_KEY) {
    Write-Host "[경고] OPENAI_API_KEY 환경 변수가 설정되지 않았습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "  1. .env 파일을 생성하고 OPENAI_API_KEY를 설정하세요."
    Write-Host "  2. 또는 PowerShell에서: `$env:OPENAI_API_KEY = 'your_key'"
    Write-Host ""
    
    $continue = Read-Host "그래도 계속하시겠습니까? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
}

# 명령줄 구성
Write-Host "[2/3] 파이프라인 설정 중..." -ForegroundColor Cyan
$args = @()
$args += "--max-posts", $MaxPosts
$args += "--min-votes", $MinVotes

if ($NoWebResearch) {
    $args += "--no-web-research"
    Write-Host "  - 웹 연구: 비활성화" -ForegroundColor Yellow
} else {
    Write-Host "  - 웹 연구: 활성화" -ForegroundColor Green
}

if ($EnableScraping) {
    $args += "--enable-scraping"
    Write-Host "  - 웹 스크래핑: 활성화" -ForegroundColor Green
}

if ($FeedUrl) {
    $args += "--feed-url", $FeedUrl
}

Write-Host "  - 최대 포스트: $MaxPosts" -ForegroundColor Cyan
Write-Host "  - 최소 투표수: $MinVotes" -ForegroundColor Cyan
Write-Host ""

# 파이프라인 실행
Write-Host "[3/3] 파이프라인 실행 중..." -ForegroundColor Cyan
Write-Host ""
python -m automation.geeknews_pipeline @args

# 결과 확인
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "✓ 실행 완료" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "✗ 실행 실패 (종료 코드: $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Cyan
}


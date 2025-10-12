# GeekNews QA 전문가급 자동화 시스템 테스트 가이드

## 빠른 테스트

### 1. 샘플 RSS 피드로 테스트

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# OpenAI API 키 설정 (임시)
$env:OPENAI_API_KEY = "your-api-key-here"

# 샘플 피드로 테스트 (1개 포스트만)
python -m automation.geeknews_pipeline --max-posts 1 --feed-url "file://automation/sample_feed.xml"
```

### 2. 실제 GeekNews 피드로 소규모 테스트

```powershell
# 웹 연구 없이 빠른 테스트 (1개만)
python -m automation.geeknews_pipeline --max-posts 1 --no-web-research

# 웹 연구 포함 전체 테스트 (3개)
python -m automation.geeknews_pipeline --max-posts 3
```

### 3. 배치 파일로 테스트

```cmd
REM Windows CMD
run_geeknews.bat --max-posts 1 --no-web-research
```

```powershell
# PowerShell
.\run_geeknews.ps1 -MaxPosts 1 -NoWebResearch
```

## 단계별 검증

### 1단계: RSS 수집 검증

```powershell
python -c "from automation.geeknews_pipeline import fetch_feed; items = fetch_feed('https://feeds.feedburner.com/geeknews-feed'); print(f'수집된 항목: {len(items)}개')"
```

**예상 결과**: `수집된 항목: 20개` (또는 유사한 숫자)

### 2단계: 콘텐츠 필터링 검증

```python
# Python 인터프리터에서 실행
from automation.content_filter import ContentFilter

filter_engine = ContentFilter(min_votes=10)
sample_items = [
    {"title": "OpenAI GPT-5 출시", "summary": "AI 뉴스", "link": "https://example.com/1"},
    {"title": "일반 기술 뉴스", "summary": "일반 뉴스", "link": "https://example.com/2"}
]

results = filter_engine.filter_and_sort(sample_items, max_items=5)
for item, metrics in results:
    print(f"{item['title']} - 우선순위: {metrics.priority_score:.1f}, AI: {metrics.is_ai_related}")
```

**예상 결과**: 
```
OpenAI GPT-5 출시 - 우선순위: 40.0, AI: True
```

### 3단계: 웹 연구 검증

```python
from automation.web_researcher import WebResearcher

researcher = WebResearcher()
result = researcher.research(
    "OpenAI GPT-4 Turbo",
    "OpenAI가 새로운 GPT-4 Turbo 모델을 발표했습니다.",
    "https://example.com"
)

print(f"웹 검색 결과: {len(result.web_results)}개")
print(f"전문가 의견: {len(result.expert_opinions)}개")
```

**예상 결과**:
```
웹 검색 결과: 3개
전문가 의견: 1개
```

### 4단계: QA 콘텐츠 생성 검증

```python
import os
from automation.qa_generator import QAContentGenerator

# API 키 설정 필요
os.environ["OPENAI_API_KEY"] = "your-key"

generator = QAContentGenerator()
sample_item = {
    "title": "Playwright 1.40 출시",
    "summary": "새로운 테스트 기능 추가",
    "link": "https://example.com"
}

result = generator.generate(sample_item)
print(f"요약: {result.summary[:100]}...")
print(f"QA 인사이트: {len(result.qa_engineer_insights)}개")
print(f"실무 가이드: {len(result.practical_guide)}개")
print(f"학습 로드맵: {len(result.learning_roadmap)}개")
```

**예상 결과**:
```
요약: Playwright 1.40이 출시되었습니다...
QA 인사이트: 3개
실무 가이드: 2개
학습 로드맵: 3개
```

## 통합 테스트

### 전체 파이프라인 테스트

```powershell
# 1. 환경 설정 확인
if (-not $env:OPENAI_API_KEY) {
    Write-Host "OpenAI API 키를 설정하세요"
    exit 1
}

# 2. 의존성 확인
pip list | Select-String -Pattern "feedparser|duckduckgo|beautifulsoup"

# 3. 소규모 실행 (1개 포스트)
python -m automation.geeknews_pipeline --max-posts 1

# 4. 생성된 포스트 확인
Get-ChildItem _posts | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### 생성된 포스트 검증

```powershell
# 최근 생성된 포스트 확인
$latest = Get-ChildItem _posts | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName

# 포스트 구조 검증
$content = Get-Content $latest.FullName -Raw
$checks = @(
    "## 요약",
    "## QA Engineer가 알아야 할 핵심 내용",
    "## 실무 적용 가이드",
    "## 학습 로드맵",
    "## 전문가 의견",
    "## 주요 Q&A",
    "## 참고 자료"
)

foreach ($check in $checks) {
    if ($content -match [regex]::Escape($check)) {
        Write-Host "✓ $check" -ForegroundColor Green
    } else {
        Write-Host "✗ $check (누락)" -ForegroundColor Red
    }
}
```

**예상 결과**: 모든 섹션에 ✓ 표시

## 성능 테스트

### 실행 시간 측정

```powershell
# 웹 연구 없이
Measure-Command {
    python -m automation.geeknews_pipeline --max-posts 3 --no-web-research
}

# 웹 연구 포함
Measure-Command {
    python -m automation.geeknews_pipeline --max-posts 3
}
```

**예상 결과**:
- 웹 연구 없이: 약 30-60초 (포스트 3개)
- 웹 연구 포함: 약 60-120초 (포스트 3개)

## 에러 시나리오 테스트

### 1. API 키 없음

```powershell
$env:OPENAI_API_KEY = ""
python -m automation.geeknews_pipeline --max-posts 1
```

**예상 결과**: 규칙 기반 백업 로직 사용

### 2. 네트워크 오류

```powershell
# 잘못된 피드 URL
python -m automation.geeknews_pipeline --feed-url "https://invalid.url"
```

**예상 결과**: 에러 메시지 출력 후 종료

### 3. 중복 항목

```powershell
# 같은 명령 두 번 실행
python -m automation.geeknews_pipeline --max-posts 1
python -m automation.geeknews_pipeline --max-posts 1
```

**예상 결과**: 두 번째 실행에서 "새로운 항목이 없습니다" 메시지

## 결과 검증 체크리스트

- [ ] RSS 피드가 정상적으로 수집되는가?
- [ ] AI 관련 항목이 우선적으로 선별되는가?
- [ ] 웹 검색 결과가 포함되는가?
- [ ] 전문가 의견이 생성되는가?
- [ ] 모든 섹션이 포스트에 포함되는가?
- [ ] 생성된 마크다운이 유효한가?
- [ ] Front Matter가 올바른가?
- [ ] 중복 항목이 필터링되는가?
- [ ] 에러 핸들링이 적절한가?
- [ ] 실행 속도가 합리적인가?

## 문제 해결

### OpenAI API 할당량 초과

```powershell
# 포스트 수 줄이기
python -m automation.geeknews_pipeline --max-posts 1

# 더 저렴한 모델 사용
$env:OPENAI_MODEL = "gpt-4o-mini"
```

### 웹 검색 타임아웃

```powershell
# 웹 연구 비활성화
python -m automation.geeknews_pipeline --no-web-research
```

### 메모리 부족

```powershell
# 한 번에 하나씩 처리
for ($i = 1; $i -le 5; $i++) {
    python -m automation.geeknews_pipeline --max-posts 1
    Start-Sleep -Seconds 5
}
```

## 자동화된 테스트 스크립트

저장: `test_pipeline.ps1`

```powershell
#!/usr/bin/env pwsh

Write-Host "GeekNews 파이프라인 자동 테스트 시작" -ForegroundColor Cyan

# 1. 환경 검증
Write-Host "`n[1/4] 환경 검증..." -ForegroundColor Yellow
if (-not $env:OPENAI_API_KEY) {
    Write-Host "  ✗ OpenAI API 키 없음" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ OpenAI API 키 설정됨" -ForegroundColor Green

# 2. 의존성 검증
Write-Host "`n[2/4] 의존성 검증..." -ForegroundColor Yellow
$required = @("feedparser", "beautifulsoup4", "requests")
foreach ($pkg in $required) {
    if (pip list | Select-String -Pattern $pkg -Quiet) {
        Write-Host "  ✓ $pkg 설치됨" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $pkg 미설치" -ForegroundColor Red
    }
}

# 3. 소규모 테스트 실행
Write-Host "`n[3/4] 소규모 테스트 (1개 포스트)..." -ForegroundColor Yellow
$output = python -m automation.geeknews_pipeline --max-posts 1 --no-web-research 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 파이프라인 실행 성공" -ForegroundColor Green
} else {
    Write-Host "  ✗ 파이프라인 실행 실패" -ForegroundColor Red
    Write-Host $output
    exit 1
}

# 4. 결과 검증
Write-Host "`n[4/4] 결과 검증..." -ForegroundColor Yellow
$latest = Get-ChildItem _posts | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    Write-Host "  ✓ 포스트 생성됨: $($latest.Name)" -ForegroundColor Green
    
    $content = Get-Content $latest.FullName -Raw
    $sections = @("요약", "QA Engineer", "참고 자료")
    foreach ($section in $sections) {
        if ($content -match $section) {
            Write-Host "  ✓ $section 섹션 존재" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $section 섹션 누락" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ✗ 포스트가 생성되지 않음" -ForegroundColor Red
}

Write-Host "`n✓ 모든 테스트 완료" -ForegroundColor Cyan
```

실행:
```powershell
.\test_pipeline.ps1
```


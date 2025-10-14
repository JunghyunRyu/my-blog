# GeekNews 자동화 Makefile
# 
# 사용법:
#   make install    - 가상환경 생성 및 의존성 설치
#   make run        - 파이프라인 1회 실행
#   make schedule   - 스케줄러 시작
#   make health     - 헬스체크 실행
#   make test       - 테스트 실행
#   make clean      - 캐시 및 로그 정리
#   make deploy     - EC2 배포

.PHONY: help install run schedule health test clean deploy lint

# Python 실행 파일 (가상환경 또는 시스템)
PYTHON := python3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# 기본 타겟
help:
	@echo "GeekNews 자동화 Makefile"
	@echo ""
	@echo "사용 가능한 명령어:"
	@echo "  make install    - 가상환경 생성 및 의존성 설치"
	@echo "  make run        - 파이프라인 1회 실행"
	@echo "  make schedule   - 스케줄러 시작 (Ctrl+C로 중단)"
	@echo "  make health     - 헬스체크 실행"
	@echo "  make test       - 테스트 실행"
	@echo "  make lint       - 코드 린트 실행"
	@echo "  make clean      - 캐시 및 임시 파일 정리"
	@echo "  make deploy     - EC2 배포 (서버에서만)"
	@echo ""

# 가상환경 생성 및 의존성 설치
install:
	@echo "📦 가상환경 생성 중..."
	$(PYTHON) -m venv $(VENV)
	@echo "📚 의존성 설치 중..."
	$(VENV_PIP) install --upgrade pip setuptools wheel
	$(VENV_PIP) install -r requirements.txt
	@echo "✅ 설치 완료!"
	@echo ""
	@echo "다음 단계:"
	@echo "  1. .env 파일 생성: cp env.example .env"
	@echo "  2. OPENAI_API_KEY 설정: nano .env"
	@echo "  3. 헬스체크 실행: make health"
	@echo ""

# 파이프라인 1회 실행
run:
	@echo "🚀 GeekNews 파이프라인 실행 중..."
	$(VENV_PYTHON) scripts/run_once.py

# 스케줄러 시작
schedule:
	@echo "⏰ GeekNews 스케줄러 시작..."
	@echo "Ctrl+C를 눌러 중단할 수 있습니다."
	@echo ""
	$(VENV_PYTHON) scripts/run_scheduler.py

# 헬스체크 실행
health:
	@echo "🏥 헬스체크 실행 중..."
	$(VENV_PYTHON) scripts/health_check.py

# 테스트 실행
test:
	@echo "🧪 테스트 실행 중..."
	@if [ -d "tests" ] && [ -n "$$(ls -A tests/*.py 2>/dev/null)" ]; then \
		$(VENV_PYTHON) -m pytest tests/ -v; \
	else \
		echo "⚠️  테스트 파일이 없습니다."; \
	fi

# 코드 린트
lint:
	@echo "🔍 코드 린트 실행 중..."
	@if command -v flake8 >/dev/null 2>&1; then \
		$(VENV_PYTHON) -m flake8 geeknews/ scripts/; \
	else \
		echo "⚠️  flake8이 설치되지 않았습니다."; \
	fi

# 캐시 및 임시 파일 정리
clean:
	@echo "🧹 정리 중..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 정리 완료!"

# 로그 정리 (7일 이상 된 로그)
clean-logs:
	@echo "🗑️  오래된 로그 파일 정리 중..."
	find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "✅ 로그 정리 완료!"

# EC2 배포
deploy:
	@echo "🚀 배포 실행 중..."
	@if [ -f "deploy/deploy.sh" ]; then \
		bash deploy/deploy.sh; \
	else \
		echo "❌ deploy/deploy.sh를 찾을 수 없습니다."; \
		exit 1; \
	fi

# 의존성 업데이트
update-deps:
	@echo "📦 의존성 업데이트 중..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install --upgrade -r requirements.txt
	@echo "✅ 의존성 업데이트 완료!"

# 개발 환경 설정
dev-setup: install
	@echo "🛠️  개발 환경 추가 도구 설치 중..."
	$(VENV_PIP) install pytest flake8 black isort
	@echo "✅ 개발 환경 설정 완료!"



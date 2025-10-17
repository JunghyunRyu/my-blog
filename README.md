# GeekNews 자동화 블로그 시스템

**MCP Sequential Thinking 통합** | **AI 기반 QA 콘텐츠 생성** | **EC2 무인 배포**

GeekNews RSS 피드를 자동으로 수집하고, MCP Sequential Thinking과 OpenAI를 활용하여 전문가급 QA 콘텐츠를 생성하는 Jekyll 블로그 자동화 시스템입니다.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18_LTS-green.svg)](https://nodejs.org/)
[![Jekyll](https://img.shields.io/badge/Jekyll-4.x-red.svg)](https://jekyllrb.com/)

---

## 📋 목차

- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [빠른 시작](#빠른-시작)
- [설치 가이드](#설치-가이드)
- [사용법](#사용법)
- [EC2 배포](#ec2-배포)
- [환경 변수](#환경-변수)
- [프로젝트 구조](#프로젝트-구조)
- [개발 가이드](#개발-가이드)
- [트러블슈팅](#트러블슈팅)
- [라이선스](#라이선스)

---

## 🚀 주요 기능

### 1. **MCP Sequential Thinking 통합**
- AI가 단계적으로 사고하며 기사 분석
- 명시적인 추론 과정 제공
- 더 깊이 있고 구조화된 콘텐츠 생성

### 2. **AI 기반 QA 콘텐츠 생성**
- OpenAI GPT-4o-mini 활용
- QA Engineer, DevOps, 자동화 전문가 관점 분석
- 실무 적용 가이드, 학습 로드맵, Q&A 자동 생성

### 3. **웹 연구 통합**
- DuckDuckGo 검색으로 추가 정보 수집
- HackerNews 댓글 분석
- 다양한 출처의 전문가 의견 통합

### 4. **GitHub 자동화**
- 생성된 포스트 자동 커밋
- GitHub에 자동 푸시
- GitHub Pages 자동 빌드 트리거

### 5. **EC2 무인 운영**
- systemd timer로 매시간 자동 실행
- MCP 서버 백그라운드 운영
- 장애 시 자동 복구

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    EC2 Instance (t2.micro)               │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         MCP Sequential Thinking Server           │  │
│  │               (Node.js, Port 3000)               │  │
│  │          systemd: mcp-sequentialthinking         │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↕                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │        GeekNews Automation (Python 3.11)        │  │
│  │                                                  │  │
│  │  RSS → Filter → MCP → OpenAI → Jekyll → Git     │  │
│  │                                                  │  │
│  │          systemd timer: geeknews.timer           │  │
│  │              (매시간 자동 실행)                  │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↓                               │
│                   GitHub → GitHub Pages                  │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ 빠른 시작

### 로컬 테스트 (5분)

```bash
# Windows PowerShell
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli

# Python 가상환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp env.example .env
# .env 파일 편집: OPENAI_API_KEY 설정

# 실행
python scripts/run_once.py
```

### EC2 배포 (15분)

```bash
# EC2 인스턴스 접속
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# 프로젝트 클론
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli

# 자동 설정 (Node.js + Python + MCP + systemd)
bash deploy/setup_ec2.sh

# 환경 변수 및 GitHub 인증 설정
nano .env
# 상세 가이드: docs/EC2_DEPLOYMENT_GUIDE.md
```

---

## 📦 설치 가이드

### 사전 요구사항

#### 로컬 개발 (Windows)
- Python 3.11+
- Git
- OpenAI API Key

#### EC2 배포 (Ubuntu 22.04)
- Python 3.11+
- Node.js 18 LTS
- Git
- OpenAI API Key
- GitHub 인증 (SSH 키 또는 PAT)

### 의존성 설치

```bash
# Python 패키지
pip install -r requirements.txt

# 주요 패키지:
# - httpx: MCP HTTP 통신
# - anyio: 비동기 지원
# - beautifulsoup4: HTML 파싱
# - feedparser: RSS 파싱
# - duckduckgo-search: 웹 검색
```

---

## 💻 사용법

### 1회 실행

```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# 스크립트 실행
python scripts/run_once.py
```

### 스케줄러 실행 (백그라운드)

```bash
# Windows (PowerShell)
python scripts/run_scheduler.py

# Linux (systemd - 권장)
sudo systemctl start geeknews.timer
```

### 헬스체크

```bash
python scripts/health_check.py

# 확인 항목:
# ✅ 설정 파일
# ✅ OpenAI API 연결
# ✅ 네트워크
# ✅ Node.js 설치
# ✅ MCP 서버 상태
# ✅ Git 설정
# ✅ 디스크 용량
```

---

## 🌩️ EC2 배포

### 완전 자동 설정

```bash
# EC2 인스턴스에서 실행
cd ~/my-blog-cli
bash deploy/setup_ec2.sh
```

**이 스크립트가 수행하는 작업:**
1. ✅ 시스템 패키지 업데이트
2. ✅ Python 3.11 설치
3. ✅ Node.js 18 LTS 설치 (nvm)
4. ✅ MCP Sequential Thinking 서버 설치
5. ✅ Python 가상환경 및 의존성 설치
6. ✅ 필수 디렉토리 생성
7. ✅ MCP systemd 서비스 등록
8. ✅ Git 기본 설정
9. ✅ GeekNews systemd 타이머 설정

### 업데이트 배포

```bash
cd ~/my-blog-cli
bash deploy/deploy.sh

# 자동으로 수행:
# - Git pull
# - 백업
# - 의존성 업데이트
# - 헬스체크
# - 서비스 재시작
```

### 서비스 관리

```bash
# MCP 서버
sudo systemctl status mcp-sequentialthinking
sudo systemctl restart mcp-sequentialthinking
sudo journalctl -u mcp-sequentialthinking -f

# GeekNews 타이머
systemctl status geeknews.timer
systemctl list-timers geeknews.timer
sudo journalctl -u geeknews-oneshot -f
```

---

## 🔐 환경 변수

`.env` 파일에서 설정합니다 (`.env.example` 참고):

```bash
# ========== OpenAI (필수) ==========
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# ========== MCP Sequential Thinking ==========
ENABLE_MCP=true
MCP_SERVER_URL=http://localhost:3000
MCP_THINKING_DEPTH=3

# ========== GitHub 자동 Push ==========
AUTO_GIT_PUSH=true
GIT_USER_NAME="GeekNews Bot"
GIT_USER_EMAIL="your-email@example.com"

# ========== 파이프라인 설정 ==========
PIPELINE_MAX_POSTS=10
MIN_VOTE_COUNT=10
ENABLE_WEB_RESEARCH=true
ENABLE_SCRAPING=false
```

---

## 📁 프로젝트 구조

```
my-blog-cli/
├── automation/              # 자동화 스크립트
│   ├── mcp_client.py       # MCP 클라이언트
│   ├── qa_generator.py     # QA 콘텐츠 생성기
│   ├── geeknews_pipeline.py # 메인 파이프라인
│   ├── content_filter.py   # 콘텐츠 필터링
│   └── web_researcher.py   # 웹 연구
│
├── scripts/                 # 실행 스크립트
│   ├── run_once.py         # 1회 실행
│   ├── run_scheduler.py    # 스케줄러
│   ├── health_check.py     # 헬스체크
│   └── git_push.py         # Git 자동 푸시
│
├── deploy/                  # 배포 스크립트
│   ├── setup_ec2.sh        # EC2 초기 설정
│   ├── deploy.sh           # 업데이트 배포
│   ├── systemd/            # systemd 서비스 파일
│   │   ├── mcp-sequentialthinking.service
│   │   ├── geeknews-oneshot.service
│   │   └── geeknews.timer
│   └── cron/               # cron 설정
│
├── docs/                    # 문서
│   └── EC2_DEPLOYMENT_GUIDE.md
│
├── _posts/                  # Jekyll 블로그 포스트
│   ├── learning/           # 학습 카테고리
│   ├── qa-engineer/        # QA Engineer 카테고리
│   └── daily-life/         # 일상 카테고리
│
├── data/                    # 실행 데이터 (gitignore)
│   └── geeknews_state.json # 처리 상태
│
├── logs/                    # 로그 (gitignore)
│
├── .env                     # 환경 변수 (gitignore)
├── env.example              # 환경 변수 예시
├── requirements.txt         # Python 의존성
└── README.md               # 이 파일
```

---

## 🛠️ 개발 가이드

### 로컬 개발 환경 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# 3. 개발 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp env.example .env
# OPENAI_API_KEY 설정
# ENABLE_MCP=false (로컬에서는 MCP 없이 개발 가능)
```

### 코드 스타일

- **포맷터**: Black (자동 포맷팅)
- **린터**: Pylint, Flake8
- **타입 힌팅**: Python 3.11+ 타입 어노테이션 사용

### 테스트

```bash
# 단위 테스트
pytest tests/

# 통합 테스트
python scripts/run_once.py --max-posts 1
```

### 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🐛 트러블슈팅

### MCP 서버가 시작되지 않음

```bash
# 상태 확인
sudo systemctl status mcp-sequentialthinking

# 로그 확인
sudo journalctl -u mcp-sequentialthinking -n 50

# Node.js 경로 확인
which node
which npx

# 재시작
sudo systemctl restart mcp-sequentialthinking
```

### GitHub Push 실패

```bash
# SSH 연결 테스트
ssh -T git@github.com

# Git 설정 확인
git config user.name
git config user.email
git remote -v

# SSH 키 재설정
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
# GitHub에 등록
```

### OpenAI API 오류

```bash
# API 키 확인
cat .env | grep OPENAI_API_KEY

# 헬스체크
python scripts/health_check.py

# 직접 테스트
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### 메모리 부족 (t2.micro)

```bash
# 스왑 메모리 추가
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

---

## 📊 리소스 사용량

| 구성 요소 | 메모리 | CPU | 디스크 |
|-----------|--------|-----|--------|
| Python 환경 | ~200MB | 5-10% | ~300MB |
| Node.js MCP | ~150MB | 2-5% | ~100MB |
| 실행 시 피크 | ~600MB | 최대 50% | ~50MB/일 |
| **총합** | **~400-600MB** | **평균 10%** | **~500MB** |

**✅ t2.micro (1GB RAM) 무료 티어에서 충분히 운영 가능!**

---

## 📚 추가 문서

- [EC2 배포 가이드](docs/EC2_DEPLOYMENT_GUIDE.md) - 상세한 배포 가이드
- [MCP 통합 여정](\_posts/learning/2025-10-17-mcp-integration-ec2-automation-journey.md) - 프로젝트 개발 과정

---

## 🎯 로드맵

### 단기 (1-3개월)
- [ ] 멀티 MCP 서버 통합 (Memory, RAG)
- [ ] A/B 테스트 프레임워크
- [ ] 콘텐츠 품질 모니터링

### 중기 (3-6개월)
- [ ] 멀티 모델 전략 (GPT-4, Claude, Gemini)
- [ ] 자동 SEO 최적화
- [ ] 독자 참여 분석

### 장기 (6-12개월)
- [ ] 인터랙티브 블로그 (실시간 Q&A)
- [ ] 커스터마이징 가능한 콘텐츠
- [ ] 자동 번역 및 다국어 지원

---

## 🤝 기여자

- [@your-username](https://github.com/your-username) - 메인 개발자

---

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 감사의 말

- [Anthropic](https://www.anthropic.com/) - MCP 프로토콜 개발
- [OpenAI](https://openai.com/) - GPT API 제공
- [Jekyll](https://jekyllrb.com/) - 정적 사이트 생성기
- [GeekNews](https://news.hada.io/) - 기술 뉴스 큐레이션

---

## 📞 연락처

- **이슈**: [GitHub Issues](https://github.com/your-username/my-blog-cli/issues)
- **토론**: [GitHub Discussions](https://github.com/your-username/my-blog-cli/discussions)
- **이메일**: your-email@example.com

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**


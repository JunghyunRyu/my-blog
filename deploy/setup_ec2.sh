#!/bin/bash
# EC2 인스턴스 초기 설정 스크립트
# Ubuntu 22.04 LTS 기준

set -e  # 오류 발생 시 중단

echo "================================"
echo "GeekNews 자동화 EC2 설정 시작"
echo "================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 사용자 확인
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ root 사용자로 실행하지 마세요!${NC}"
    echo "일반 사용자(ubuntu)로 실행해주세요."
    exit 1
fi

PROJECT_DIR="$HOME/my-blog-cli"

echo "📦 시스템 패키지 업데이트 중..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

echo ""
echo "🐍 Python 3.11 설치 중..."
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl

# Python 3.11이 기본이 되도록 설정
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

echo ""
echo "🟢 Node.js 18 LTS 설치 중..."
# nvm 설치
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    echo "nvm이 이미 설치되어 있습니다."
fi

# Node.js 18 LTS 설치
nvm install 18
nvm use 18
nvm alias default 18

# Node.js 버전 확인
node --version
npm --version

echo ""
echo "🧠 MCP Sequential Thinking 서버 설치 중..."
# MCP 서버는 npx로 실행하므로 별도 설치 불필요
# 하지만 캐시를 위해 한 번 다운로드
npx -y @modelcontextprotocol/server-sequentialthinking --version || echo "MCP 서버 준비 완료"

echo ""
echo "📂 프로젝트 디렉토리로 이동..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_DIR${NC}"
    echo "먼저 프로젝트를 클론하세요:"
    echo "  git clone <repository-url> $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo ""
echo "🔧 가상환경 생성 중..."
if [ -d "venv" ]; then
    echo "가상환경이 이미 존재합니다. 재생성합니다..."
    rm -rf venv
fi

python3.11 -m venv venv
source venv/bin/activate

echo ""
echo "📚 Python 패키지 설치 중..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "📁 필수 디렉토리 생성 중..."
mkdir -p logs data _posts/learning _posts/qa-engineer

echo ""
echo "🔐 환경 변수 설정 확인..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다.${NC}"
    echo "env.example을 복사하여 .env를 생성합니다..."
    cp env.example .env
    echo -e "${YELLOW}⚠️  .env 파일을 편집하여 OPENAI_API_KEY를 설정하세요!${NC}"
    echo "   nano .env"
else
    echo "✅ .env 파일이 존재합니다."
fi

echo ""
echo "🏥 헬스체크 실행..."
python scripts/health_check.py || true

echo ""
echo "🧠 MCP Sequential Thinking 서비스 설정 중..."
# Node.js 경로 동적 감지
NODE_VERSION=$(node --version | sed 's/v//')
NODE_PATH="$HOME/.nvm/versions/node/v$NODE_VERSION/bin"

# systemd 서비스 파일 생성 (동적 경로 적용)
cat > /tmp/mcp-sequentialthinking.service << EOF
[Unit]
Description=MCP Sequential Thinking Server
Documentation=https://github.com/modelcontextprotocol/servers
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$HOME
Environment="PATH=$NODE_PATH:/usr/local/bin:/usr/bin:/bin"
Environment="NODE_ENV=production"
ExecStart=$NODE_PATH/npx -y @modelcontextprotocol/server-sequentialthinking
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
MemoryMax=256M
CPUQuota=25%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mcp-sequentialthinking

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/mcp-sequentialthinking.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcp-sequentialthinking.service
sudo systemctl start mcp-sequentialthinking.service

echo "✅ MCP 서버 systemd 서비스가 시작되었습니다."
echo ""
echo "MCP 서버 상태 확인:"
echo "  sudo systemctl status mcp-sequentialthinking"

echo ""
echo "🔧 Git 설정 확인..."
# Git 사용자 설정 (없는 경우에만)
git config user.name > /dev/null 2>&1 || git config --global user.name "GeekNews Bot"
git config user.email > /dev/null 2>&1 || git config --global user.email "bot@geeknews.local"
echo "✅ Git 사용자 설정 완료"
echo "   사용자명: $(git config user.name)"
echo "   이메일: $(git config user.email)"

echo ""
echo "================================"
echo "설정 방식 선택"
echo "================================"
echo "1) systemd 서비스 (추천) - 백그라운드 지속 실행"
echo "2) systemd 타이머 - 정해진 시간마다 실행 (권장)"
echo "3) cron - 전통적인 방식"
echo "4) 설정하지 않음"
echo ""
read -p "선택 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔧 systemd 서비스 설정 중..."
        sudo cp deploy/systemd/geeknews.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable geeknews.service
        sudo systemctl start geeknews.service
        echo "✅ systemd 서비스가 시작되었습니다."
        echo ""
        echo "서비스 상태 확인:"
        echo "  sudo systemctl status geeknews"
        echo "로그 확인:"
        echo "  sudo journalctl -u geeknews -f"
        ;;
    2)
        echo ""
        echo "🔧 systemd 타이머 설정 중..."
        sudo cp deploy/systemd/geeknews-oneshot.service /etc/systemd/system/
        sudo cp deploy/systemd/geeknews.timer /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable geeknews.timer
        sudo systemctl start geeknews.timer
        echo "✅ systemd 타이머가 활성화되었습니다."
        echo ""
        echo "타이머 상태 확인:"
        echo "  sudo systemctl status geeknews.timer"
        echo "다음 실행 시간 확인:"
        echo "  systemctl list-timers geeknews.timer"
        ;;
    3)
        echo ""
        echo "🔧 cron 설정 중..."
        echo "현재 crontab에 추가합니다..."
        (crontab -l 2>/dev/null; cat deploy/cron/geeknews.cron) | crontab -
        echo "✅ cron 작업이 추가되었습니다."
        echo ""
        echo "cron 작업 확인:"
        echo "  crontab -l"
        ;;
    4)
        echo "설정을 건너뜁니다."
        ;;
    *)
        echo -e "${RED}잘못된 선택입니다.${NC}"
        ;;
esac

echo ""
echo "================================"
echo "✅ EC2 설정 완료!"
echo "================================"
echo ""
echo "다음 단계:"
echo "  1. .env 파일 편집: nano .env"
echo "  2. OPENAI_API_KEY 설정"
echo "  3. MCP 설정 (ENABLE_MCP, MCP_SERVER_URL)"
echo "  4. Git 사용자 정보 설정 (GIT_USER_NAME, GIT_USER_EMAIL)"
echo "  5. GitHub SSH 키 또는 Personal Access Token 설정"
echo "  6. 수동 테스트: python scripts/run_once.py"
echo ""
echo "유용한 명령어:"
echo "  - 헬스체크: python scripts/health_check.py"
echo "  - 1회 실행: python scripts/run_once.py"
echo "  - MCP 서버 상태: sudo systemctl status mcp-sequentialthinking"
echo "  - GeekNews 타이머 상태: systemctl list-timers geeknews.timer"
echo "  - 로그 확인: tail -f logs/*.log"
echo "  - MCP 로그: sudo journalctl -u mcp-sequentialthinking -f"
echo ""
echo "GitHub 인증 설정 (자동 Push를 위해 필수):"
echo "  SSH 키 방식:"
echo "    1. ssh-keygen -t ed25519 -C 'your-email@example.com'"
echo "    2. cat ~/.ssh/id_ed25519.pub 출력 후 GitHub에 등록"
echo "    3. ssh -T git@github.com 으로 연결 테스트"
echo "  또는 Personal Access Token 방식:"
echo "    1. GitHub에서 PAT 생성 (repo 권한 필요)"
echo "    2. git config --global credential.helper store"
echo "    3. git push 시 토큰 입력"
echo ""



#!/bin/bash
# 배포 스크립트 - 기존 EC2에 업데이트 배포

set -e  # 오류 발생 시 중단

echo "================================"
echo "GeekNews 자동화 배포 시작"
echo "================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$HOME/my-blog-cli"
BACKUP_DIR="$HOME/backups/my-blog-cli-$(date +%Y%m%d-%H%M%S)"

cd "$PROJECT_DIR"

echo "📦 Git 저장소 상태 확인..."
git fetch

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "✅ 이미 최신 버전입니다."
else
    echo "📥 새로운 변경사항이 있습니다. 업데이트 중..."
    
    echo ""
    echo "💾 현재 상태 백업 중..."
    mkdir -p "$(dirname $BACKUP_DIR)"
    
    # 중요 파일 백업
    mkdir -p "$BACKUP_DIR"
    cp -r data logs .env "$BACKUP_DIR/" 2>/dev/null || true
    echo "백업 위치: $BACKUP_DIR"
    
    echo ""
    echo "🔄 Git pull 실행..."
    git pull
    
    echo ""
    echo "📚 의존성 업데이트..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "🏥 헬스체크 실행..."
    python scripts/health_check.py || {
        echo -e "${RED}❌ 헬스체크 실패!${NC}"
        echo "배포를 계속하시겠습니까? (y/N)"
        read -p "" continue
        if [ "$continue" != "y" ]; then
            echo "배포를 중단합니다."
            exit 1
        fi
    }
    
    echo ""
    echo "🧠 MCP 서버 상태 확인..."
    if systemctl is-active --quiet mcp-sequentialthinking.service 2>/dev/null; then
        echo "✅ MCP 서버 실행 중"
        sudo systemctl status mcp-sequentialthinking.service --no-pager --lines=3
    else
        echo -e "${YELLOW}⚠️  MCP 서버가 실행되지 않고 있습니다. 시작 중...${NC}"
        sudo systemctl start mcp-sequentialthinking.service
        sleep 2
        if systemctl is-active --quiet mcp-sequentialthinking.service; then
            echo "✅ MCP 서버 시작 완료"
        else
            echo -e "${RED}❌ MCP 서버 시작 실패${NC}"
            echo "로그 확인: sudo journalctl -u mcp-sequentialthinking -n 20"
        fi
    fi
    
    echo ""
    echo "🔧 서비스 재시작..."
    
    # systemd 서비스가 실행 중인지 확인
    if systemctl is-active --quiet geeknews.service 2>/dev/null; then
        echo "systemd 서비스 재시작 중..."
        sudo systemctl restart geeknews.service
        sleep 2
        sudo systemctl status geeknews.service --no-pager
    elif systemctl is-active --quiet geeknews.timer 2>/dev/null; then
        echo "systemd 타이머 활성화 상태 확인..."
        sudo systemctl status geeknews.timer --no-pager
    else
        echo -e "${YELLOW}⚠️  실행 중인 서비스가 없습니다.${NC}"
        echo "cron 또는 수동 실행 방식을 사용 중입니다."
    fi
    
    echo ""
    echo "================================"
    echo "✅ 배포 완료!"
    echo "================================"
    echo ""
    echo "변경사항:"
    git log --oneline -5
    echo ""
fi

echo "현재 버전: $(git describe --always --tags 2>/dev/null || git rev-parse --short HEAD)"
echo ""



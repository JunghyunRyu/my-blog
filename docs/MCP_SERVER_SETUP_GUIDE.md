# MCP Sequential Thinking 서버 설치 가이드

## 개요

MCP (Model Context Protocol) Sequential Thinking 서버는 복잡한 문제에 대한 단계별 사고 분석을 제공하는 서버입니다. 이 서버는 Anthropic의 Claude API를 사용하여 GeekNews 기사를 QA Engineer 관점에서 심층 분석합니다.

## 사전 요구사항

- Node.js v18 이상 (현재 시스템: v20.17.0 ✅)
- Anthropic API 키 (https://console.anthropic.com/에서 발급)
- Git

## 설치 방법

### 1. MCP 서버 저장소 클론

```bash
# MCP servers 저장소 클론
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/sequentialthinking

# 의존성 설치
npm install

# TypeScript 빌드
npm run build
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가합니다:

```env
# Anthropic API 키 (필수)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# 서버 포트 (선택, 기본값: 3000)
PORT=3000

# 로그 레벨 (선택)
LOG_LEVEL=info
```

### 3. 서버 실행

#### 개발 모드 (테스트용)

```bash
npm run dev
```

#### 프로덕션 모드

```bash
npm start
```

서버가 정상적으로 시작되면 다음과 같은 메시지가 표시됩니다:

```
MCP Sequential Thinking Server listening on port 3000
```

### 4. 서버 연결 테스트

Python에서 MCP 클라이언트로 연결을 테스트합니다:

```bash
cd C:\jhryu\my-blog-cli
.\venv\Scripts\Activate.ps1
python
```

Python 인터프리터에서:

```python
from automation.mcp_client import create_mcp_client

# MCP 클라이언트 생성
client = create_mcp_client()

if client:
    print("✓ MCP 서버 연결 성공!")
    
    # 간단한 테스트
    result = client.think("QA 테스트 자동화의 장점은?", depth=2)
    print(result)
    
    client.close()
else:
    print("✗ MCP 서버 연결 실패")
```

## Windows 환경에서의 설치

### 옵션 1: WSL (Windows Subsystem for Linux) 사용 (권장)

WSL에서 MCP 서버를 실행하면 더 안정적입니다:

```bash
# WSL에서 실행
wsl

# 위의 설치 단계를 WSL 내에서 수행
# ...

# 서버 실행
npm start
```

### 옵션 2: Windows PowerShell에서 직접 실행

Windows PowerShell에서도 실행 가능하지만, 일부 제약이 있을 수 있습니다:

```powershell
# PowerShell에서 실행
cd servers\src\sequentialthinking
npm install
npm run build
npm start
```

### 옵션 3: EC2 서버에서 실행 (프로덕션 권장)

EC2에서 실행하면 안정성과 가용성이 향상됩니다:

```bash
# EC2 인스턴스에 SSH 접속
ssh -i your-key.pem ec2-user@your-ec2-ip

# MCP 서버 설치 (위의 설치 단계 동일)
# ...

# Systemd 서비스로 등록 (자동 시작)
sudo cp ~/my-blog-cli/deploy/systemd/mcp-sequentialthinking.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcp-sequentialthinking
sudo systemctl start mcp-sequentialthinking

# 로그 확인
sudo journalctl -u mcp-sequentialthinking -f
```

## Systemd 서비스 설정 (Linux/EC2)

기존 서비스 파일을 사용합니다:

```bash
# 서비스 파일 확인
cat ~/my-blog-cli/deploy/systemd/mcp-sequentialthinking.service

# 서비스 등록
sudo cp ~/my-blog-cli/deploy/systemd/mcp-sequentialthinking.service /etc/systemd/system/
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start mcp-sequentialthinking

# 자동 시작 설정
sudo systemctl enable mcp-sequentialthinking

# 상태 확인
sudo systemctl status mcp-sequentialthinking

# 로그 확인
sudo journalctl -u mcp-sequentialthinking -f
```

## 문제 해결

### 1. "ANTHROPIC_API_KEY is not set" 에러

`.env` 파일에 Anthropic API 키가 올바르게 설정되어 있는지 확인하세요.

```bash
# .env 파일 확인
cat .env

# 환경 변수 직접 설정 (임시)
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
npm start
```

### 2. "Port 3000 is already in use" 에러

다른 프로세스가 3000 포트를 사용 중입니다:

```bash
# Windows PowerShell
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/WSL
lsof -ti:3000 | xargs kill -9
```

또는 `.env` 파일에서 다른 포트를 사용하도록 설정:

```env
PORT=3001
```

### 3. Python 클라이언트 연결 실패

MCP 서버 URL이 올바른지 확인:

```python
# 환경 변수로 서버 URL 설정
import os
os.environ["MCP_SERVER_URL"] = "http://localhost:3000"

# 또는 직접 지정
from automation.mcp_client import SyncSequentialThinkingClient
client = SyncSequentialThinkingClient(server_url="http://localhost:3001")
```

### 4. httpx 라이브러리 없음

```bash
pip install httpx
```

## MCP 활성화/비활성화

### 환경 변수로 제어

`.env` 파일에서:

```env
# MCP 비활성화
ENABLE_MCP=false

# MCP 활성화 (기본값)
ENABLE_MCP=true
```

### 일시적으로 비활성화

파이프라인 실행 시:

```bash
# MCP 없이 실행
ENABLE_MCP=false python automation/geeknews_pipeline.py --max-posts 5
```

## 성능 튜닝

### 사고 깊이 조절

`.env` 파일에서:

```env
# 사고 깊이 (1-5, 기본값: 3)
# 낮을수록 빠르지만 분석이 얕음
# 높을수록 느리지만 분석이 깊음
MCP_THINKING_DEPTH=3
```

### 타임아웃 설정

Python 코드에서:

```python
from automation.mcp_client import SyncSequentialThinkingClient

client = SyncSequentialThinkingClient(
    server_url="http://localhost:3000",
    timeout=60.0  # 60초 타임아웃
)
```

## 비용 고려사항

MCP Sequential Thinking 서버는 Anthropic Claude API를 사용하므로 사용량에 따라 비용이 발생합니다:

- Claude 3.5 Sonnet: 입력 $3/MTok, 출력 $15/MTok
- Claude 3 Haiku: 입력 $0.25/MTok, 출력 $1.25/MTok

기사 1개당 약 2,000-5,000 토큰을 사용하므로, 비용을 절약하려면:

1. `MCP_THINKING_DEPTH`를 낮게 설정 (예: 2)
2. 필요한 경우에만 MCP 활성화
3. Haiku 모델 사용 고려

## 대안

Anthropic API를 사용하고 싶지 않다면:

1. **MCP 비활성화**: `.env`에서 `ENABLE_MCP=false` 설정
2. **OpenAI만 사용**: OpenAI GPT-4만으로도 충분히 좋은 결과를 얻을 수 있습니다

## 추가 정보

- MCP 공식 문서: https://modelcontextprotocol.io/
- Anthropic API 문서: https://docs.anthropic.com/
- Sequential Thinking 서버 소스: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking


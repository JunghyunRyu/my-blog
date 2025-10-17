# EC2 배포 가이드

GeekNews 자동화 시스템을 AWS EC2 인스턴스에 배포하는 완전한 가이드입니다.

**MCP Sequential Thinking 통합 버전**

---

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [EC2 인스턴스 생성](#ec2-인스턴스-생성)
3. [초기 설정](#초기-설정)
4. [GitHub 인증 설정](#github-인증-설정)
5. [환경 변수 설정](#환경-변수-설정)
6. [서비스 시작 및 확인](#서비스-시작-및-확인)
7. [모니터링 및 관리](#모니터링-및-관리)
8. [트러블슈팅](#트러블슈팅)
9. [비용 최적화](#비용-최적화)

---

## 시스템 요구사항

### 하드웨어

- **최소 사양:** t2.micro (1 vCPU, 1GB RAM)
- **권장 사양:** t3.small (2 vCPU, 2GB RAM)
- **디스크:** 8GB 이상 (권장 16GB)

### 소프트웨어

- **OS:** Ubuntu 22.04 LTS (권장)
- **Python:** 3.11+
- **Node.js:** 18 LTS
- **Git:** 2.x+

### 예상 리소스 사용량

| 구성 요소 | 메모리 | CPU | 디스크 |
|-----------|--------|-----|--------|
| Python 환경 | ~200MB | 5-10% | ~300MB |
| Node.js MCP 서버 | ~150MB | 2-5% | ~100MB |
| 실행 시 피크 | ~600MB | 최대 50% | ~50MB/일 |
| **총합** | **~400-600MB** | **평균 10%** | **~500MB** |

**결론:** t2.micro (무료 티어)에서 충분히 실행 가능합니다.

---

## EC2 인스턴스 생성

### 1. AWS 콘솔에서 EC2 인스턴스 생성

1. **AMI 선택:** Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
2. **인스턴스 유형:** t2.micro 또는 t3.micro
3. **키 페어:** 새로운 키 페어 생성 또는 기존 키 사용
4. **네트워크 설정:**
   - VPC: 기본 VPC 사용
   - 퍼블릭 IP 자동 할당: **활성화**
   - 보안 그룹: SSH (22번 포트) 허용

5. **스토리지:** 16GB gp3 (권장)

### 2. 보안 그룹 설정

최소한 다음 인바운드 규칙 필요:

| 유형 | 프로토콜 | 포트 | 소스 |
|------|----------|------|------|
| SSH | TCP | 22 | 내 IP |

**참고:** MCP 서버는 localhost에서만 실행되므로 외부 포트 개방 불필요

### 3. SSH 접속

```bash
# Windows PowerShell에서
ssh -i "your-key.pem" ubuntu@your-ec2-public-ip

# 또는 EC2 Instance Connect 사용
```

---

## 초기 설정

### 1. 프로젝트 클론

```bash
# GitHub에서 프로젝트 클론
cd ~
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli
```

### 2. 자동 설치 스크립트 실행

```bash
bash deploy/setup_ec2.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
- ✅ 시스템 패키지 업데이트
- ✅ Python 3.11 설치
- ✅ Node.js 18 LTS 설치 (nvm 사용)
- ✅ MCP Sequential Thinking 서버 설치
- ✅ Python 가상환경 생성
- ✅ 의존성 패키지 설치
- ✅ 필수 디렉토리 생성
- ✅ MCP 서버 systemd 서비스 등록
- ✅ Git 기본 설정
- ✅ GeekNews 자동화 서비스 설정 (타이머 권장)

**설정 방식 선택 시:**
- **옵션 2 (systemd 타이머) 권장** - 매시간 자동 실행

---

## GitHub 인증 설정

자동 푸시 기능을 사용하려면 GitHub 인증이 필요합니다.

### 방법 1: SSH 키 (권장)

```bash
# 1. SSH 키 생성
ssh-keygen -t ed25519 -C "your-email@example.com"
# Enter 3번 (기본 경로, 비밀번호 없음)

# 2. 공개 키 복사
cat ~/.ssh/id_ed25519.pub

# 3. GitHub에 등록
# GitHub.com → Settings → SSH and GPG keys → New SSH key
# 위에서 복사한 내용 붙여넣기

# 4. 연결 테스트
ssh -T git@github.com
# "Hi username! You've successfully authenticated..." 메시지 확인

# 5. Git 원격 저장소를 SSH로 변경
cd ~/my-blog-cli
git remote set-url origin git@github.com:your-username/my-blog-cli.git
```

### 방법 2: Personal Access Token (PAT)

```bash
# 1. GitHub에서 PAT 생성
# GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 권한: repo (전체)

# 2. Git credential helper 설정
git config --global credential.helper store

# 3. 한 번 푸시하면서 토큰 입력
cd ~/my-blog-cli
git push
# Username: your-username
# Password: ghp_your_personal_access_token

# 이후 자동으로 저장되어 재입력 불필요
```

---

## 환경 변수 설정

### 1. .env 파일 편집

```bash
cd ~/my-blog-cli
nano .env
```

### 2. 필수 설정

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# OpenAI 모델 선택 (선택)
OPENAI_MODEL=gpt-4o-mini

# MCP 설정 (MCP 사용 시)
ENABLE_MCP=true
MCP_SERVER_URL=http://localhost:3000
MCP_THINKING_DEPTH=3

# GitHub 자동 Push 설정
AUTO_GIT_PUSH=true
GIT_USER_NAME="GeekNews Bot"
GIT_USER_EMAIL="your-email@example.com"

# 기타 설정
PIPELINE_MAX_POSTS=10
MIN_VOTE_COUNT=10
ENABLE_WEB_RESEARCH=true
```

**Ctrl+O** (저장), **Enter**, **Ctrl+X** (종료)

---

## 서비스 시작 및 확인

### 1. 헬스체크 실행

```bash
cd ~/my-blog-cli
source venv/bin/activate
python scripts/health_check.py
```

**모든 항목이 ✅ 상태인지 확인:**
- ✅ 설정
- ✅ OpenAI API
- ✅ 네트워크
- ✅ Node.js
- ✅ MCP 서버
- ✅ Git 설정
- ✅ 디스크
- ✅ 디렉토리

### 2. 수동 테스트

```bash
python scripts/run_once.py
```

**확인 사항:**
- RSS 피드 수집 성공
- MCP 분석 완료 (활성화된 경우)
- QA 콘텐츠 생성 성공
- 블로그 포스트 생성 성공
- GitHub 푸시 성공 (AUTO_GIT_PUSH=true인 경우)

### 3. 서비스 상태 확인

```bash
# MCP 서버 상태
sudo systemctl status mcp-sequentialthinking

# GeekNews 타이머 상태
sudo systemctl status geeknews.timer

# 다음 실행 시간 확인
systemctl list-timers geeknews.timer
```

---

## 모니터링 및 관리

### 실시간 로그 확인

```bash
# MCP 서버 로그
sudo journalctl -u mcp-sequentialthinking -f

# GeekNews 실행 로그
sudo journalctl -u geeknews-oneshot -f

# 또는 프로젝트 로그 파일
tail -f ~/my-blog-cli/logs/*.log
```

### 서비스 제어

```bash
# MCP 서버 재시작
sudo systemctl restart mcp-sequentialthinking

# GeekNews 타이머 재시작
sudo systemctl restart geeknews.timer

# 서비스 중지
sudo systemctl stop mcp-sequentialthinking
sudo systemctl stop geeknews.timer

# 서비스 시작
sudo systemctl start mcp-sequentialthinking
sudo systemctl start geeknews.timer
```

### 수동 실행

```bash
cd ~/my-blog-cli
source venv/bin/activate
python scripts/run_once.py
```

### 업데이트 배포

```bash
cd ~/my-blog-cli
bash deploy/deploy.sh
```

이 스크립트는:
1. Git에서 최신 코드 pull
2. 현재 상태 백업
3. 의존성 업데이트
4. 헬스체크 실행
5. MCP 서버 상태 확인
6. 서비스 재시작

---

## 트러블슈팅

### 문제 1: MCP 서버가 시작되지 않음

**증상:**
```
❌ MCP 서버에 연결할 수 없습니다
```

**해결:**
```bash
# 서비스 상태 확인
sudo systemctl status mcp-sequentialthinking

# 로그 확인
sudo journalctl -u mcp-sequentialthinking -n 50

# Node.js 경로 확인
which node
which npx

# 서비스 파일 재생성 (setup_ec2.sh 재실행)
cd ~/my-blog-cli
bash deploy/setup_ec2.sh
```

### 문제 2: GitHub 푸시 실패

**증상:**
```
⚠️  Git 자동 푸시 실패
```

**해결:**
```bash
# SSH 연결 테스트
ssh -T git@github.com

# Git 설정 확인
git config user.name
git config user.email
git remote -v

# 수동 푸시 테스트
cd ~/my-blog-cli
git push

# 권한 문제인 경우 SSH 키 재설정 또는 PAT 재발급
```

### 문제 3: OpenAI API 오류

**증상:**
```
❌ API 키가 유효하지 않습니다
```

**해결:**
```bash
# .env 파일 확인
cat ~/my-blog-cli/.env | grep OPENAI_API_KEY

# API 키 재설정
nano ~/my-blog-cli/.env

# 헬스체크로 검증
python scripts/health_check.py
```

### 문제 4: 메모리 부족

**증상:**
```
Killed (메모리 부족으로 프로세스 종료)
```

**해결:**
```bash
# 스왑 파일 생성 (1GB)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 적용
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# MCP 비활성화 (메모리 절약)
nano ~/my-blog-cli/.env
# ENABLE_MCP=false로 변경
```

### 문제 5: 포스트가 생성되지 않음

**증상:**
```
✓ 새로운 GeekNews 항목이 없습니다.
```

**해결:**
```bash
# RSS 피드 확인
curl -I https://feeds.feedburner.com/geeknews-feed

# 상태 파일 확인
cat ~/my-blog-cli/data/geeknews_state.json

# 필요 시 상태 파일 리셋 (모든 항목을 새로 처리)
rm ~/my-blog-cli/data/geeknews_state.json

# 재실행
python scripts/run_once.py
```

---

## 비용 최적화

### 무료 티어 활용

AWS 프리 티어는 다음을 제공합니다:
- **t2.micro:** 월 750시간 (24시간 × 31일 = 744시간)
- **EBS 스토리지:** 30GB
- **데이터 전송:** 월 15GB 아웃바운드

**결론:** 1개의 t2.micro 인스턴스를 24/7 실행해도 무료!

### 리소스 절약 팁

#### 1. MCP 서버 리소스 제한

MCP 서버는 이미 systemd에서 제한됨:
```ini
MemoryMax=256M
CPUQuota=25%
```

#### 2. Python 프로세스 제한

`geeknews-oneshot.service`에 설정됨:
```ini
MemoryMax=512M
CPUQuota=50%
```

#### 3. 로그 로테이션

```bash
# /etc/logrotate.d/geeknews 생성
sudo nano /etc/logrotate.d/geeknews
```

내용:
```
/home/ubuntu/my-blog-cli/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

#### 4. 실행 주기 조정

더 긴 간격으로 실행하려면:
```bash
sudo nano /etc/systemd/system/geeknews.timer

# OnCalendar 수정
# hourly → 매시간
# *-*-* 09,18:00:00 → 하루 2회 (9시, 18시)
# daily → 하루 1회
```

#### 5. 웹 연구 비활성화

메모리와 API 호출 절약:
```bash
nano ~/my-blog-cli/.env
# ENABLE_WEB_RESEARCH=false
```

### 비용 모니터링

```bash
# 현재 리소스 사용량 확인
htop  # 또는 top

# 디스크 사용량
df -h

# 메모리 사용량
free -h

# 프로세스별 메모리
ps aux --sort=-%mem | head -10
```

---

## 추가 리소스

- **MCP 공식 문서:** https://github.com/modelcontextprotocol/servers
- **AWS EC2 가이드:** https://docs.aws.amazon.com/ec2/
- **Jekyll GitHub Pages:** https://docs.github.com/en/pages
- **OpenAI API 문서:** https://platform.openai.com/docs

---

## 문의 및 지원

문제가 발생하거나 도움이 필요한 경우:

1. **로그 확인:** `sudo journalctl -u mcp-sequentialthinking -n 100`
2. **헬스체크 실행:** `python scripts/health_check.py`
3. **GitHub Issues:** 프로젝트 저장소에 이슈 등록

---

**배포를 완료하셨습니다! 🎉**

이제 GeekNews 자동화 시스템이 1시간마다 자동으로 실행되어 새로운 포스트를 생성하고 GitHub에 푸시합니다.


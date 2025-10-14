# EC2 배포 가이드

GeekNews 블로그 자동화를 EC2 인스턴스에 배포하는 상세 가이드입니다.

## 📋 목차

- [EC2 인스턴스 생성](#ec2-인스턴스-생성)
- [초기 설정](#초기-설정)
- [배포 방법](#배포-방법)
- [실행 방식 선택](#실행-방식-선택)
- [보안 설정](#보안-설정)
- [백업 및 복구](#백업-및-복구)

## 🖥️ EC2 인스턴스 생성

### 권장 사양

**인스턴스 타입**: `t3.micro` 또는 `t3.small`

**사양**:
- **CPU**: 1-2 vCPU
- **메모리**: 1-2GB
- **스토리지**: 10-20GB (gp3)
- **OS**: Ubuntu 22.04 LTS

### 생성 단계

1. **AWS 콘솔**에 로그인
2. **EC2 > Instances > Launch Instance**
3. 다음 설정 선택:
   - Name: `geeknews-automation`
   - AMI: `Ubuntu Server 22.04 LTS`
   - Instance type: `t3.micro`
   - Key pair: 기존 키 또는 새로 생성
   - Security group: SSH(22) 허용
   - Storage: 20GB gp3

4. **Launch** 클릭

### 보안 그룹 설정

```
Inbound Rules:
- Type: SSH
  Protocol: TCP
  Port: 22
  Source: My IP (또는 특정 IP 범위)

Outbound Rules:
- Type: All traffic
  Protocol: All
  Port: All
  Destination: 0.0.0.0/0
```

## 🔧 초기 설정

### 1. SSH 접속

```bash
# 키 파일 권한 설정
chmod 400 your-key.pem

# EC2 접속
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. 시스템 업데이트

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 3. Git 설치 및 저장소 클론

```bash
# Git 설치
sudo apt-get install -y git

# 저장소 클론
cd ~
git clone <repository-url> my-blog-cli
cd my-blog-cli
```

### 4. 자동 설정 스크립트 실행

```bash
bash deploy/setup_ec2.sh
```

스크립트는 다음을 수행합니다:
1. Python 3.11 설치
2. 가상환경 생성
3. 의존성 설치
4. 디렉토리 구조 생성
5. .env 파일 생성
6. 실행 방식 선택 (systemd/cron)

### 5. 환경 변수 설정

```bash
nano .env
```

필수 설정:
```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
MAX_POSTS_PER_RUN=10
PIPELINE_INTERVAL_SECONDS=3600
```

### 6. 설정 검증

```bash
# 가상환경 활성화
source venv/bin/activate

# 헬스체크
python scripts/health_check.py

# 테스트 실행
python scripts/run_once.py
```

## 🚀 배포 방법

### 자동 배포 스크립트

```bash
cd ~/my-blog-cli
bash deploy/deploy.sh
```

### 수동 배포

```bash
cd ~/my-blog-cli

# 최신 코드 가져오기
git pull

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트
pip install -r requirements.txt

# 서비스 재시작 (systemd 사용 시)
sudo systemctl restart geeknews
```

## ⚙️ 실행 방식 선택

### 방식 1: systemd 서비스 (권장)

**장점**:
- 백그라운드 지속 실행
- 자동 재시작
- 로그 관리 용이
- systemctl로 제어

**설정**:

```bash
# 서비스 파일 복사
sudo cp deploy/systemd/geeknews.service /etc/systemd/system/

# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable geeknews
sudo systemctl start geeknews

# 상태 확인
sudo systemctl status geeknews

# 로그 확인
sudo journalctl -u geeknews -f
```

**제어 명령어**:

```bash
# 시작
sudo systemctl start geeknews

# 중지
sudo systemctl stop geeknews

# 재시작
sudo systemctl restart geeknews

# 상태 확인
sudo systemctl status geeknews

# 로그 보기
sudo journalctl -u geeknews -n 50
sudo journalctl -u geeknews -f  # 실시간
```

### 방식 2: systemd 타이머

**장점**:
- cron보다 강력한 스케줄링
- 시스템 로그 통합
- 실패 시 재시도
- 부팅 시 누락된 작업 실행

**설정**:

```bash
# 서비스 및 타이머 파일 복사
sudo cp deploy/systemd/geeknews-oneshot.service /etc/systemd/system/
sudo cp deploy/systemd/geeknews.timer /etc/systemd/system/

# 타이머 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable geeknews.timer
sudo systemctl start geeknews.timer

# 타이머 상태 확인
sudo systemctl status geeknews.timer

# 다음 실행 시간 확인
systemctl list-timers geeknews.timer
```

**수동 실행**:

```bash
# 즉시 1회 실행
sudo systemctl start geeknews-oneshot

# 로그 확인
sudo journalctl -u geeknews-oneshot -n 50
```

### 방식 3: cron

**장점**:
- 전통적이고 친숙한 방식
- 설정이 간단
- 추가 패키지 불필요

**설정**:

```bash
# crontab 편집
crontab -e

# 다음 줄 추가 (매시간 실행)
0 * * * * cd /home/ubuntu/my-blog-cli && ./venv/bin/python scripts/run_once.py >> logs/cron.log 2>&1

# 또는 미리 작성된 cron 파일 사용
crontab deploy/cron/geeknews.cron
```

**cron 작업 확인**:

```bash
# 현재 cron 작업 목록
crontab -l

# cron 로그 확인
tail -f logs/cron.log
```

## 🔒 보안 설정

### SSH 키 관리

```bash
# 키 파일 권한 확인
ls -l ~/.ssh/authorized_keys

# 권한 설정 (필요시)
chmod 600 ~/.ssh/authorized_keys
```

### 방화벽 설정 (UFW)

```bash
# UFW 활성화
sudo ufw enable

# SSH 허용
sudo ufw allow 22/tcp

# 상태 확인
sudo ufw status
```

### .env 파일 보안

```bash
# .env 파일 권한 설정
chmod 600 .env

# 소유자 확인
ls -l .env
```

### API 키 보호

1. `.env` 파일은 Git에 절대 커밋하지 마세요
2. `.gitignore`에 `.env` 추가 확인
3. API 키는 환경 변수로만 관리
4. 주기적으로 API 키 교체

## 💾 백업 및 복구

### 백업 대상

1. **상태 파일**: `data/geeknews_state.json`
2. **환경 설정**: `.env`
3. **생성된 포스트**: `_posts/`
4. **로그**: `logs/` (선택사항)

### 자동 백업 설정

```bash
# 백업 디렉토리 생성
mkdir -p ~/backups

# 백업 스크립트 생성
cat > ~/backup_geeknews.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups/geeknews-$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
cd ~/my-blog-cli
cp -r data .env _posts $BACKUP_DIR/
tar -czf $BACKUP_DIR.tar.gz -C ~/backups $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR
# 30일 이상 된 백업 삭제
find ~/backups -name "geeknews-*.tar.gz" -mtime +30 -delete
EOF

chmod +x ~/backup_geeknews.sh

# cron에 백업 추가 (매일 오전 3시)
(crontab -l; echo "0 3 * * * ~/backup_geeknews.sh") | crontab -
```

### 복구 절차

```bash
# 백업 파일 목록 확인
ls -lh ~/backups/

# 최신 백업 복구
cd ~/backups
tar -xzf geeknews-YYYYMMDD-HHMMSS.tar.gz
cd ~/my-blog-cli

# 파일 복구
cp -r ~/backups/geeknews-YYYYMMDD-HHMMSS/data ./
cp ~/backups/geeknews-YYYYMMDD-HHMMSS/.env ./
cp -r ~/backups/geeknews-YYYYMMDD-HHMMSS/_posts ./

# 서비스 재시작
sudo systemctl restart geeknews
```

## 📊 모니터링

### CloudWatch 연동 (선택사항)

```bash
# CloudWatch Agent 설치
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# 설정 및 시작
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/path/to/config.json
```

### 로그 모니터링

```bash
# 실시간 로그
tail -f logs/geeknews.log

# 에러만 필터링
grep ERROR logs/geeknews.log

# 최근 100줄
tail -100 logs/geeknews.log
```

### 헬스체크 자동화

```bash
# 매일 헬스체크 실행 (cron)
(crontab -l; echo "0 9 * * * cd ~/my-blog-cli && ./venv/bin/python scripts/health_check.py >> logs/health.log 2>&1") | crontab -
```

## 🔄 업데이트 전략

### 무중단 업데이트

```bash
# 1. 백업
~/backup_geeknews.sh

# 2. 배포
cd ~/my-blog-cli
bash deploy/deploy.sh

# 3. 검증
python scripts/health_check.py

# 4. 완료 (서비스 자동 재시작됨)
```

### 롤백

```bash
# 이전 버전으로 롤백
cd ~/my-blog-cli
git log --oneline -10  # 이전 커밋 확인
git reset --hard <commit-hash>

# 의존성 재설치
source venv/bin/activate
pip install -r requirements.txt

# 서비스 재시작
sudo systemctl restart geeknews
```

## 📞 문제 해결

### 서비스가 시작되지 않음

```bash
# 상세 로그 확인
sudo journalctl -u geeknews -xe

# 수동 실행으로 디버깅
cd ~/my-blog-cli
source venv/bin/activate
python scripts/run_once.py
```

### API 키 오류

```bash
# 환경 변수 확인
source venv/bin/activate
python -c "from geeknews.config import Config; print(Config.OPENAI_API_KEY[:10])"

# .env 파일 확인
cat .env | grep OPENAI_API_KEY
```

### 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# 로그 정리
find ~/my-blog-cli/logs -name "*.log" -mtime +7 -delete

# 백업 정리
find ~/backups -name "*.tar.gz" -mtime +30 -delete
```

---

**다음**: [운영 매뉴얼](OPERATIONS.md)



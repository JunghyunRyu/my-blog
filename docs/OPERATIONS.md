# 운영 매뉴얼

GeekNews 블로그 자동화 시스템의 일상 운영을 위한 가이드입니다.

## 📋 목차

- [일일 체크리스트](#일일-체크리스트)
- [모니터링](#모니터링)
- [로그 관리](#로그-관리)
- [일반적인 작업](#일반적인-작업)
- [성능 최적화](#성능-최적화)
- [비용 관리](#비용-관리)

## ✅ 일일 체크리스트

### 아침 점검 (선택사항)

```bash
# SSH 접속
ssh ubuntu@your-ec2-ip

# 프로젝트 디렉토리로 이동
cd ~/my-blog-cli

# 헬스체크
make health

# 최근 로그 확인 (문제가 있는지 확인)
tail -20 logs/geeknews.log | grep ERROR

# 새로 생성된 포스트 확인
ls -lt _posts/learning/ | head -5
ls -lt _posts/qa-engineer/ | head -5
```

### 자동화 권장

헬스체크를 cron으로 자동화:

```bash
# crontab 편집
crontab -e

# 매일 오전 9시 헬스체크 (이메일 알림)
0 9 * * * cd ~/my-blog-cli && ./venv/bin/python scripts/health_check.py || echo "Health check failed" | mail -s "GeekNews Health Alert" your@email.com
```

## 📊 모니터링

### 서비스 상태 확인

#### systemd 서비스

```bash
# 상태 확인
sudo systemctl status geeknews

# 자세한 상태
sudo systemctl status geeknews --no-pager -l

# 재시작 횟수 확인
systemctl show geeknews | grep NRestarts
```

#### systemd 타이머

```bash
# 타이머 상태
sudo systemctl status geeknews.timer

# 다음 실행 시간
systemctl list-timers geeknews.timer

# 마지막 실행 결과
sudo systemctl status geeknews-oneshot
```

#### cron

```bash
# cron 작업 확인
crontab -l

# cron 로그 확인
tail -f logs/cron.log

# 시스템 cron 로그
grep CRON /var/log/syslog | tail -20
```

### 주요 지표

#### 생성된 포스트 수

```bash
# 오늘 생성된 포스트
find _posts -name "$(date +%Y-%m-%d)-*.md" | wc -l

# 최근 7일
find _posts -name "*.md" -mtime -7 | wc -l

# 전체 포스트 수
find _posts -name "*.md" | wc -l
```

#### 실행 성공률

```bash
# 최근 실행 로그에서 성공/실패 확인
grep -c "파이프라인 실행 완료" logs/geeknews.log
grep -c "ERROR" logs/geeknews.log
```

#### 시스템 리소스

```bash
# 메모리 사용량
free -h

# 디스크 사용량
df -h

# CPU 사용률 (프로세스별)
top -b -n 1 | head -20

# Python 프로세스 확인
ps aux | grep python
```

## 📝 로그 관리

### 로그 위치

```
logs/
├── geeknews.log          # 메인 로그
├── service.log           # systemd 서비스 stdout
├── service.error.log     # systemd 서비스 stderr
├── cron.log              # cron 실행 로그
├── health.log            # 헬스체크 로그
└── oneshot.log           # 타이머 실행 로그
```

### 로그 확인 명령어

```bash
# 실시간 로그
tail -f logs/geeknews.log

# 최근 100줄
tail -100 logs/geeknews.log

# 에러만 필터링
grep ERROR logs/geeknews.log

# 특정 날짜
grep "2025-10-12" logs/geeknews.log

# 에러 발생 횟수
grep -c ERROR logs/geeknews.log
```

### 로그 정리

#### 수동 정리

```bash
# 7일 이상 된 로그 삭제
find logs/ -name "*.log" -mtime +7 -delete

# 로그 압축
gzip logs/geeknews.log.1

# 특정 로그 삭제
rm logs/old_log_file.log
```

#### 자동 정리 (logrotate)

```bash
# logrotate 설정 파일 생성
sudo nano /etc/logrotate.d/geeknews

# 다음 내용 추가:
/home/ubuntu/my-blog-cli/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0644 ubuntu ubuntu
}

# 설정 테스트
sudo logrotate -d /etc/logrotate.d/geeknews

# 즉시 실행
sudo logrotate -f /etc/logrotate.d/geeknews
```

#### cron으로 정리

```bash
# crontab 편집
crontab -e

# 매주 일요일 자정에 정리
0 0 * * 0 find ~/my-blog-cli/logs -name "*.log" -mtime +7 -delete
```

## 🔧 일반적인 작업

### 설정 변경

```bash
# .env 파일 편집
nano .env

# 변경 사항 적용 (서비스 재시작)
sudo systemctl restart geeknews

# 또는 (타이머 사용 시) 다음 실행 시 자동 적용
```

### 수동 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# 1회 실행
python scripts/run_once.py

# 특정 옵션으로 실행
python -m geeknews.pipeline --max-posts 5 --no-web-research
```

### 코드 업데이트

```bash
# 배포 스크립트 사용 (권장)
bash deploy/deploy.sh

# 또는 수동으로
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart geeknews
```

### 상태 파일 관리

```bash
# 상태 파일 확인
cat data/geeknews_state.json | python -m json.tool

# 처리된 항목 수
cat data/geeknews_state.json | python -c "import sys, json; print(len(json.load(sys.stdin)['processed']))"

# 상태 파일 백업
cp data/geeknews_state.json data/geeknews_state.json.backup

# 상태 파일 초기화 (주의: 모든 기록 삭제)
echo '{"processed": []}' > data/geeknews_state.json
```

### 포스트 관리

```bash
# 최근 포스트 목록
ls -lt _posts/learning/ | head -10
ls -lt _posts/qa-engineer/ | head -10

# 특정 날짜 포스트
find _posts -name "2025-10-12-*.md"

# 포스트 수 통계
echo "Learning: $(find _posts/learning -name '*.md' | wc -l)"
echo "QA Engineer: $(find _posts/qa-engineer -name '*.md' | wc -l)"

# 포스트 내용 확인
less _posts/learning/2025-10-12-some-post.md
```

## ⚡ 성능 최적화

### API 비용 절감

```bash
# .env 파일에서 설정 변경
OPENAI_MODEL=gpt-4o-mini  # 가장 저렴한 모델
MAX_POSTS_PER_RUN=5       # 포스트 수 제한
ENABLE_WEB_RESEARCH=false # 웹 연구 비활성화로 속도 개선
```

### 실행 주기 조정

```bash
# .env 파일
PIPELINE_INTERVAL_SECONDS=7200  # 2시간마다 (기본 1시간)

# systemd 서비스 재시작
sudo systemctl restart geeknews

# cron 수정
crontab -e
# 0 */2 * * * ...  # 2시간마다
```

### 캐시 및 임시 파일 정리

```bash
# Python 캐시 정리
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 임시 파일 정리
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# 또는
make clean
```

## 💰 비용 관리

### OpenAI API 사용량 모니터링

```bash
# API 호출 로그 분석
grep "OpenAI API" logs/geeknews.log | wc -l

# 월간 예상 비용 계산
# 포스트당 $0.01-0.02 (gpt-4o-mini)
# 하루 10개 = $0.10-0.20
# 한달 300개 = $3-6
```

### EC2 비용 최적화

```bash
# 인스턴스 타입 다운그레이드 검토
# t3.micro (1GB) -> $0.0104/시간
# t3.small (2GB) -> $0.0208/시간

# Reserved Instance로 최대 72% 절감
# Savings Plan으로 최대 66% 절감
```

### 스토리지 관리

```bash
# 디스크 사용량 확인
du -sh ~/my-blog-cli/*

# 큰 파일 찾기
find ~/my-blog-cli -type f -size +10M

# 오래된 로그 정리
make clean-logs
```

## 🚨 알림 설정

### 이메일 알림 (선택사항)

```bash
# postfix 설치
sudo apt-get install -y postfix mailutils

# 설정 (Internet Site 선택)
sudo dpkg-reconfigure postfix

# 테스트
echo "Test" | mail -s "Test Subject" your@email.com
```

### Slack 알림 (선택사항)

Slack Incoming Webhook을 사용한 알림:

```bash
# .env에 Webhook URL 추가
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 알림 스크립트 생성
cat > ~/send_slack.sh << 'EOF'
#!/bin/bash
MESSAGE="$1"
WEBHOOK_URL="$SLACK_WEBHOOK_URL"
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$MESSAGE\"}" \
  $WEBHOOK_URL
EOF

chmod +x ~/send_slack.sh

# 사용 예
~/send_slack.sh "GeekNews: New posts created"
```

## 📈 대시보드 (선택사항)

### 간단한 상태 페이지

```bash
# 상태 HTML 생성 스크립트
cat > ~/my-blog-cli/generate_status.sh << 'EOF'
#!/bin/bash
cat > status.html << HTML
<html>
<head><title>GeekNews Status</title></head>
<body>
<h1>GeekNews Automation Status</h1>
<p>Last update: $(date)</p>
<p>Total posts: $(find _posts -name '*.md' | wc -l)</p>
<p>Today's posts: $(find _posts -name "$(date +%Y-%m-%d)-*.md" | wc -l)</p>
<pre>
$(tail -20 logs/geeknews.log)
</pre>
</body>
</html>
HTML
EOF

chmod +x ~/my-blog-cli/generate_status.sh

# cron으로 주기적 생성
# 0 * * * * cd ~/my-blog-cli && ./generate_status.sh
```

## 🔍 문제 감지

### 자동 헬스체크

```bash
# 스크립트 생성
cat > ~/check_and_alert.sh << 'EOF'
#!/bin/bash
cd ~/my-blog-cli
source venv/bin/activate

# 헬스체크 실행
python scripts/health_check.py > /tmp/health_check.log 2>&1

# 실패 시 알림
if [ $? -ne 0 ]; then
    cat /tmp/health_check.log | mail -s "GeekNews Health Check Failed" your@email.com
fi
EOF

chmod +x ~/check_and_alert.sh

# cron 추가
# 0 */6 * * * ~/check_and_alert.sh
```

### 에러 알림

```bash
# 에러 감지 및 알림
cat > ~/check_errors.sh << 'EOF'
#!/bin/bash
ERROR_COUNT=$(grep -c ERROR ~/my-blog-cli/logs/geeknews.log)

if [ $ERROR_COUNT -gt 10 ]; then
    echo "Too many errors: $ERROR_COUNT" | mail -s "GeekNews Error Alert" your@email.com
fi
EOF

chmod +x ~/check_errors.sh
```

---

**관련 문서**:
- [EC2 배포 가이드](EC2_DEPLOYMENT.md)
- [시스템 아키텍처](ARCHITECTURE.md)
- [문제 해결](TROUBLESHOOTING.md)



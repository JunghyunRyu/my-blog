---
layout: post
title: "EC2 서버에 Nginx와 Application Server(uvicorn/FastAPI) 연결 설정, 운영 팁까지"
date: 2025-10-12 13:05:00 +0900
categories: [Learning]
tags: [EC2, Nginx, FastAPI, Uvicorn, Ubuntu, systemd, ReverseProxy, SFTP, DevOps, AWS]
---

# EC2 서버에 Nginx와 Application Server 연결 설정, 운영 팁까지

**목표**: AWS EC2(Ubuntu)에서 **FastAPI(Uvicorn)** 애플리케이션을 구동하고, **Nginx**를 리버스 프록시로 앞단에 세워 80 포트로 서비스합니다.

추가로 재부팅 후 자동 기동(**systemd**), 정적 파일 서빙, VSCode **SFTP 배포**, **네트워크 이슈/Windows 경로 이스케이프** 등 운영 관점의 디테일까지 다룹니다.

---

## 📋 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [선행 준비](#2-선행-준비요약)
3. [애플리케이션 코드](#3-애플리케이션-코드)
4. [부팅 시 자동 실행](#4-부팅-시-자동-실행systemd)
5. [Nginx 리버스 프록시 설정](#5-nginx-리버스-프록시-설정)
6. [정적 파일 배치](#6-정적-파일-배치)
7. [VSCode SFTP 배포](#7-vscode-sftp로-배포-자동화)
8. [운영 체크리스트 & 트러블슈팅](#8-운영-체크리스트--트러블슈팅)
9. [HTTPS 설정](#9-https선택--곧바로-운영-반영-시-권장)
10. [최종 점검](#10-최종-점검-시나리오)

---

## 1) 아키텍처 개요

```
[Client] → (80/tcp) → [Nginx on EC2]
                         │
                         └──(127.0.0.1:8000)→ [Uvicorn(FastAPI)]
```

### 주요 특징

* **외부 접근**: 클라이언트는 **80 포트**로 접속 → Nginx가 수신
* **내부 라우팅**: Nginx가 내부 루프백(127.0.0.1:8000)으로 Uvicorn에 프록시
* **정적 파일**: `/images/` 경로는 Nginx가 **직접 서빙** (애플리케이션 서버 우회로 성능 향상)
* **자동 기동**: 애플리케이션은 **systemd**로 관리되어 서버 재부팅 시 자동 실행
* **보안**: 애플리케이션 서버(8000 포트)는 외부에 노출되지 않음

---

## 2) 선행 준비(요약)

### EC2 인스턴스 생성 및 접속

**인스턴스 설정**
- **AMI**: Ubuntu 24.04 LTS (또는 22.04 LTS)
- **인스턴스 타입**: t2.micro 이상 (프리티어: t2.micro)
- **키 페어**: 새로 생성하거나 기존 키 사용 (반드시 `.pem` 파일 안전하게 보관)

**보안 그룹 인바운드 규칙**

| 포트 | 프로토콜 | 소스 | 용도 |
|------|---------|------|------|
| 22 | TCP | 0.0.0.0/0 | SSH 접속 |
| 80 | TCP | 0.0.0.0/0 | HTTP 웹 서비스 |

> ⚠️ **주의**: 8000 포트는 외부에 열지 마세요. Nginx를 통해서만 접근하도록 합니다.

**SSH 접속**

```bash
# Linux/Mac
ssh -i /경로/키.pem ubuntu@<EC2_Public_IP>

# Windows (PowerShell)
ssh -i C:\경로\키.pem ubuntu@<EC2_Public_IP>
```

### Python 환경 구성

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 가상환경 도구 설치
sudo apt install -y python3 python3-venv python3-pip

# 프로젝트 디렉토리 생성
mkdir -p ~/reactbase && cd ~/reactbase

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 필수 패키지 설치
pip install --upgrade pip
pip install fastapi uvicorn[standard]
```

> 💡 **Tip**: `uvicorn[standard]`로 설치하면 websocket, HTTP/2 등 추가 기능을 사용할 수 있습니다.

---

## 3) 애플리케이션 코드

### FastAPI 애플리케이션 작성

`~/reactbase/server.py` 파일을 생성합니다:

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import pathlib

app = FastAPI(
    title="My API Server",
    description="EC2에서 구동되는 FastAPI 애플리케이션",
    version="1.0.0"
)

@app.get("/", response_class=PlainTextResponse)
def read_root():
    """루트 엔드포인트"""
    return "welcome"

@app.get("/hello", response_class=PlainTextResponse)
def read_hello():
    """Hello 엔드포인트"""
    return "hello"

@app.get("/world", response_class=PlainTextResponse)
def read_world():
    """World 엔드포인트"""
    return "world"

@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트 (모니터링용)"""
    return {"status": "healthy", "service": "fastapi"}

# 정적 파일: /home/ubuntu/reactbase/public → /images 경로로 노출
static_dir = pathlib.Path(__file__).resolve().parent
public_dir = static_dir / "public"

# public 디렉토리가 없으면 생성
public_dir.mkdir(exist_ok=True)

# 정적 파일 마운트
app.mount("/images", StaticFiles(directory=str(public_dir), html=False), name="images")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 로컬 테스트

```bash
# 가상환경 활성화 (아직 안 했다면)
source venv/bin/activate

# 방법 1: Python 직접 실행
python3 server.py

# 방법 2: uvicorn 명령어로 실행 (권장)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

> 💡 **Tip**: `--reload` 옵션은 코드 변경 시 자동 재시작합니다 (개발 환경에서만 사용).

### 동작 확인

**EC2 서버 내부에서 테스트:**

```bash
# 기본 엔드포인트 테스트
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/hello
curl http://127.0.0.1:8000/world

# 헬스 체크
curl http://127.0.0.1:8000/health

# API 문서 확인 (FastAPI 자동 생성)
curl http://127.0.0.1:8000/docs
```

**외부에서 테스트 (보안 그룹에 8000 포트가 열려있는 경우만):**

브라우저에서 `http://<EC2_Public_IP>:8000/` 접속 → `"welcome"` 확인

> ⚠️ **주의**: 보안 그룹 인바운드에서 8000 포트를 열지 않았다면 외부 접속은 안 됩니다. 
> 
> 이것이 정상입니다! Nginx 설정 후에는 80 포트로만 접근하게 됩니다.

---

## 4) 부팅 시 자동 실행(systemd)

서버가 재부팅되더라도 애플리케이션이 자동으로 시작되도록 systemd 서비스를 설정합니다.

### systemd 서비스 파일 생성

`/etc/systemd/system/fastapi.service` 파일을 생성합니다:

```bash
sudo nano /etc/systemd/system/fastapi.service
```

아래 내용을 입력:

```ini
[Unit]
Description=FastAPI Application Service
After=network.target
Documentation=https://fastapi.tiangolo.com/

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/reactbase
Environment="PATH=/home/ubuntu/reactbase/venv/bin"
ExecStart=/home/ubuntu/reactbase/venv/bin/uvicorn server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips="*"

# 재시작 정책
Restart=always
RestartSec=3

# 프로세스 종료 시간 제한
TimeoutStopSec=10

# 로그 설정 (journalctl로 확인 가능)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fastapi

[Install]
WantedBy=multi-user.target
```

### 설정 항목 설명

| 항목 | 설명 |
|------|------|
| `After=network.target` | 네트워크가 준비된 후에 시작 |
| `User=ubuntu` | ubuntu 사용자 권한으로 실행 |
| `WorkingDirectory` | 애플리케이션 실행 디렉토리 |
| `--proxy-headers` | Nginx 프록시 헤더 신뢰 (클라이언트 실제 IP 확인) |
| `--forwarded-allow-ips="*"` | 모든 프록시에서 forwarded 헤더 허용 |
| `Restart=always` | 실패 시 항상 재시작 |
| `RestartSec=3` | 재시작 전 3초 대기 |

### 서비스 활성화 및 시작

```bash
# systemd 데몬 리로드 (새 서비스 파일 인식)
sudo systemctl daemon-reload

# 부팅 시 자동 시작 활성화
sudo systemctl enable fastapi.service

# 서비스 시작
sudo systemctl start fastapi.service

# 상태 확인
sudo systemctl status fastapi.service
```

### 서비스 관리 명령어

```bash
# 서비스 중지
sudo systemctl stop fastapi.service

# 서비스 재시작
sudo systemctl restart fastapi.service

# 서비스 상태 확인
sudo systemctl status fastapi.service

# 로그 확인 (최근 100줄)
sudo journalctl -u fastapi.service -n 100

# 실시간 로그 모니터링
sudo journalctl -u fastapi.service -f

# 서비스 자동 시작 비활성화
sudo systemctl disable fastapi.service
```

> 💡 **Tip**: 코드를 수정한 후에는 `sudo systemctl restart fastapi.service`로 변경사항을 반영하세요.

---

## 5) Nginx 리버스 프록시 설정

Nginx를 설치하고 FastAPI 애플리케이션 앞단에 리버스 프록시로 설정합니다.

### Nginx 설치

```bash
# Nginx 설치
sudo apt update
sudo apt install -y nginx

# Nginx 상태 확인
sudo systemctl status nginx

# 기본 사이트 비활성화
sudo rm /etc/nginx/sites-enabled/default
```

### 사이트 구성 파일 생성

`/etc/nginx/sites-available/reactbase` 파일을 생성합니다:

```bash
sudo nano /etc/nginx/sites-available/reactbase
```

아래 내용을 입력:

```nginx
# HTTP/1.1 업그레이드 지원 (WebSocket용)
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    listen [::]:80;
    server_name <EC2_Public_IP_or_Domain>;

    # 보안 헤더
    server_tokens off;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # 업로드 파일 크기 제한
    client_max_body_size 10M;

    # 애플리케이션 서버로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;

        # 프록시 헤더 설정
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host  $host;
        proxy_set_header X-Forwarded-Port  $server_port;

        # WebSocket 지원
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        $connection_upgrade;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;

        # 버퍼링 설정
        proxy_buffering off;
        proxy_redirect off;
    }

    # 정적 파일 직접 서빙 (성능 향상)
    location /images/ {
        alias /home/ubuntu/reactbase/public/;
        
        # 보안 및 최적화
        autoindex off;
        access_log off;
        
        # 캐시 설정
        expires 1h;
        add_header Cache-Control "public, immutable";
        
        # MIME 타입 자동 설정
        include /etc/nginx/mime.types;
    }

    # 헬스 체크 엔드포인트 (선택)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Favicon 에러 로그 무시 (선택)
    location = /favicon.ico {
        access_log off;
        log_not_found off;
        return 204;
    }
}
```

> 💡 **Tip**: `<EC2_Public_IP_or_Domain>` 부분은 실제 EC2 Public IP 또는 도메인으로 변경하세요.
> 
> 예: `server_name 3.35.123.456;` 또는 `server_name example.com;`

### 설정 활성화 및 검증

```bash
# 심볼릭 링크 생성 (sites-enabled에 연결)
sudo ln -s /etc/nginx/sites-available/reactbase /etc/nginx/sites-enabled/

# Nginx 설정 문법 검증
sudo nginx -t

# 출력 예시:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Nginx 재시작

```bash
# Nginx 재시작
sudo systemctl restart nginx

# 상태 확인
sudo systemctl status nginx
```

### 동작 확인

**서버 내부에서 테스트:**

```bash
# HTTP 헤더 확인
curl -I http://localhost/

# 응답 본문 확인
curl http://localhost/

# 정적 파일 테스트 (파일이 있는 경우)
curl -I http://localhost/images/test.jpg
```

**외부 브라우저에서 테스트:**

브라우저에서 `http://<EC2_Public_IP>/` 접속 → `"welcome"` 확인

### Nginx 관리 명령어

```bash
# 설정 변경 후 문법 검증
sudo nginx -t

# 무중단 설정 리로드 (권장)
sudo systemctl reload nginx

# Nginx 재시작
sudo systemctl restart nginx

# Nginx 중지
sudo systemctl stop nginx

# Nginx 시작
sudo systemctl start nginx

# 로그 확인
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

> ⚠️ **주의**: 설정을 변경할 때는 항상 `sudo nginx -t`로 검증한 후 적용하세요.

---

## 6) 정적 파일 배치

### 정적 파일 디렉토리 구조

```
/home/ubuntu/reactbase/
├── server.py
├── venv/
└── public/              ← 정적 파일 저장 위치
    ├── logo.png
    ├── favicon.ico
    └── images/
        ├── banner.jpg
        └── profile.png
```

### 파일 업로드 방법

**방법 1: SCP로 파일 전송 (Linux/Mac)**

```bash
# 단일 파일 업로드
scp -i /경로/키.pem logo.png ubuntu@<EC2_Public_IP>:/home/ubuntu/reactbase/public/

# 폴더 전체 업로드
scp -i /경로/키.pem -r images/ ubuntu@<EC2_Public_IP>:/home/ubuntu/reactbase/public/
```

**방법 2: Windows PowerShell**

```powershell
# SCP 사용
scp -i C:\경로\키.pem logo.png ubuntu@<EC2_Public_IP>:/home/ubuntu/reactbase/public/
```

**방법 3: 서버에서 직접 생성**

```bash
# 테스트용 더미 파일 생성
cd ~/reactbase/public
echo "test" > test.txt
```

### 접근 경로 매핑

| 실제 파일 경로 | 웹 브라우저 URL |
|---------------|----------------|
| `/home/ubuntu/reactbase/public/logo.png` | `http://<EC2_IP>/images/logo.png` |
| `/home/ubuntu/reactbase/public/favicon.ico` | `http://<EC2_IP>/images/favicon.ico` |
| `/home/ubuntu/reactbase/public/images/banner.jpg` | `http://<EC2_IP>/images/images/banner.jpg` |

### 장점

* **성능 향상**: Nginx가 직접 서빙하므로 애플리케이션 서버를 거치지 않음
* **효율성**: Python 프로세스의 CPU/메모리 낭비 없음
* **캐싱**: Nginx 레벨에서 브라우저 캐시 헤더 설정 가능
* **대용량 파일**: 이미지, 비디오 등 대용량 파일도 효율적으로 서빙

> 💡 **Tip**: HTML/CSS/JS 파일을 빌드한 프론트엔드 자산도 여기에 배치할 수 있습니다.

---

## 7) VSCode SFTP로 배포 자동화

VSCode SFTP 확장을 사용하면 파일 저장 시 자동으로 EC2 서버에 업로드할 수 있습니다.

### SFTP 확장 설치

1. VSCode 확장 탭에서 **"SFTP"** 검색
2. **"SFTP/FTP sync"** (작성자: Natizyskunk) 설치

### 설정 파일 생성

로컬 프로젝트 루트에 `.vscode/sftp.json` 파일을 생성합니다:

**Linux/Mac 사용자:**

```json
{
  "name": "EC2 WebServer",
  "host": "<EC2_Public_IP>",
  "protocol": "sftp",
  "port": 22,
  "username": "ubuntu",
  "remotePath": "/home/ubuntu/reactbase",
  "uploadOnSave": true,
  "useTempFile": false,
  "openSsh": false,
  "privateKeyPath": "/Users/yourname/pem/my_key.pem",
  "ignore": [
    ".vscode",
    ".git",
    ".DS_Store",
    "venv",
    "__pycache__",
    "*.pyc"
  ]
}
```

**Windows 사용자:**

```json
{
  "name": "EC2 WebServer",
  "host": "<EC2_Public_IP>",
  "protocol": "sftp",
  "port": 22,
  "username": "ubuntu",
  "remotePath": "/home/ubuntu/reactbase",
  "uploadOnSave": true,
  "useTempFile": false,
  "openSsh": false,
  "privateKeyPath": "C:\\\\Users\\\\yourname\\\\pem\\\\my_key.pem",
  "ignore": [
    ".vscode",
    ".git",
    ".DS_Store",
    "venv",
    "__pycache__",
    "*.pyc"
  ]
}
```

> ⚠️ **Windows 중요**: 경로의 백슬래시(`\`)는 **4개(`\\\\`)** 로 이스케이프해야 합니다!
> 
> 예: `C:\Users\john\key.pem` → `"C:\\\\Users\\\\john\\\\key.pem"`

### 설정 항목 설명

| 항목 | 설명 |
|------|------|
| `name` | 연결 이름 (식별용) |
| `host` | EC2 Public IP |
| `remotePath` | 서버의 프로젝트 디렉토리 경로 |
| `uploadOnSave` | `true`로 설정 시 파일 저장 시 자동 업로드 |
| `privateKeyPath` | PEM 키 파일의 절대 경로 |
| `ignore` | 업로드 제외할 파일/폴더 패턴 |

### 사용 방법

1. **파일 수정 후 저장** (`Ctrl+S` 또는 `Cmd+S`)
2. 자동으로 EC2 서버에 업로드됨
3. 서비스 재시작으로 변경사항 반영:

```bash
sudo systemctl restart fastapi.service
```

### SFTP 수동 명령어

VSCode 명령 팔레트 (`Ctrl+Shift+P` 또는 `Cmd+Shift+P`)에서:

- **SFTP: Upload File** - 현재 파일 업로드
- **SFTP: Upload Folder** - 폴더 전체 업로드
- **SFTP: Download File** - 서버에서 파일 다운로드
- **SFTP: Sync Local → Remote** - 로컬을 서버로 동기화
- **SFTP: Sync Remote → Local** - 서버를 로컬로 동기화

### 트러블슈팅

**문제: "All configured authentication methods failed"**

- PEM 키 경로가 올바른지 확인
- Windows에서 백슬래시 이스케이프 확인 (`\\\\`)
- PEM 파일 권한 확인 (Linux/Mac: `chmod 400 키.pem`)

**문제: "Permission denied"**

- EC2 보안 그룹에서 22번 포트(SSH) 허용 확인
- `username`이 `ubuntu`인지 확인 (Ubuntu AMI의 기본 사용자)

**배포 후 변경사항이 반영되지 않음:**

```bash
# FastAPI 서비스 재시작 필요
sudo systemctl restart fastapi.service

# 로그 확인
sudo journalctl -u fastapi.service -n 50
```

> 💡 **Tip**: `uploadOnSave: true`로 설정하면 개발 속도가 크게 향상됩니다!

---

## 8) 운영 체크리스트 & 트러블슈팅

### A. 보안 그룹/네트워크

**필수 포트 설정**

| 포트 | 상태 | 용도 |
|------|------|------|
| 22 | 열림 | SSH 접속 |
| 80 | 열림 | HTTP 웹 서비스 |
| 8000 | **닫힘** | 외부 노출 불필요 (Nginx를 통해서만 접근) |

> ⚠️ **주의**: 8000 포트는 보안상 외부에 열지 마세요. 테스트가 필요한 경우에만 임시로 개방 후 즉시 닫으세요.

**보안 그룹 확인 방법:**
1. AWS 콘솔 → EC2 → 인스턴스 선택
2. **보안** 탭 → **보안 그룹** 클릭
3. **인바운드 규칙** 확인

### B. ISP/통신사 차단 이슈

**증상:**
- AWS 보안 그룹은 정상적으로 설정되어 있음
- 서버 내부에서는 정상 접속 (`curl localhost`)
- 외부에서 접속이 안 됨

**원인 및 해결:**

가정용 인터넷(KT, SKT, LG U+ 등)에서는 특정 포트가 **ISP 레벨에서 차단**될 수 있습니다.

**해결 방법:**
1. **휴대폰 핫스팟**으로 전환하여 테스트
2. 접속이 되면 → ISP 차단 문제
3. 해결:
   - ISP에 문의하여 포트 개방 요청
   - 또는 443 포트(HTTPS) 사용
   - VPN 사용

### C. SSH 접속 문제

**문제: `Permission denied (publickey)`**

**원인 체크리스트:**

```bash
# 1. PEM 키 파일이 올바른지 확인
# EC2 인스턴스 생성 시 선택한 키 페어와 일치해야 함

# 2. 파일 권한 확인 (Linux/Mac)
chmod 400 키.pem

# 3. 올바른 사용자명 사용
# Ubuntu AMI: ubuntu
# Amazon Linux: ec2-user
ssh -i 키.pem ubuntu@<IP>

# 4. 보안 그룹에서 22번 포트 확인
# 소스: 0.0.0.0/0 (또는 내 IP만)
```

**Windows 특수 문제:**

```powershell
# PEM 파일 권한 설정 (PowerShell 관리자 권한)
icacls "C:\경로\키.pem" /inheritance:r
icacls "C:\경로\키.pem" /grant:r "%username%:R"
```

### D. Nginx 문제 해결

**문제: 502 Bad Gateway**

**원인:**
- FastAPI 서비스가 실행 중이지 않음
- 포트 불일치 (Nginx는 8000으로 프록시하는데 Uvicorn은 다른 포트에서 실행)

**해결:**

```bash
# FastAPI 서비스 상태 확인
sudo systemctl status fastapi.service

# 서비스가 실패했다면 로그 확인
sudo journalctl -u fastapi.service -n 100

# 포트 확인 (8000 포트에서 리스닝 중인지)
sudo netstat -tulpn | grep :8000
# 또는
sudo ss -tulpn | grep :8000

# 서비스 재시작
sudo systemctl restart fastapi.service
```

**문제: Nginx 설정 오류**

```bash
# 설정 파일 문법 검증
sudo nginx -t

# 자주 발생하는 오류:
# 1. 세미콜론(;) 누락
# 2. 중괄호 불일치
# 3. 파일 경로 오타

# 로그 확인
sudo tail -f /var/log/nginx/error.log
```

**문제: 정적 파일(이미지) 404**

```bash
# 디렉토리 권한 확인
ls -ld /home/ubuntu/reactbase/public/
ls -l /home/ubuntu/reactbase/public/

# Nginx 사용자가 접근 가능해야 함
# 권한 문제라면:
chmod 755 /home/ubuntu/reactbase/public/
chmod 644 /home/ubuntu/reactbase/public/*

# Nginx 설정에서 alias 경로 확인
# 끝에 슬래시(/) 필수!
# location /images/ {
#     alias /home/ubuntu/reactbase/public/;
# }
```

### E. FastAPI/Uvicorn 문제 해결

**서비스 관리:**

```bash
# 상태 확인
sudo systemctl status fastapi.service

# 로그 확인 (최근 200줄)
sudo journalctl -u fastapi.service -n 200

# 실시간 로그 모니터링
sudo journalctl -u fastapi.service -f

# 서비스 재시작
sudo systemctl restart fastapi.service

# 서비스 파일 수정 후 리로드
sudo systemctl daemon-reload
```

**성능 최적화 - Worker 프로세스:**

CPU 코어 수에 따라 worker 수 조정:

```bash
# CPU 코어 수 확인
nproc
```

`/etc/systemd/system/fastapi.service` 수정:

```ini
# 코어가 2개라면 workers=2 또는 3
ExecStart=/home/ubuntu/reactbase/venv/bin/uvicorn server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --proxy-headers \
    --forwarded-allow-ips="*"
```

> 💡 **권장**: `workers = (2 × CPU 코어 수) + 1`

**Python 모듈 오류:**

```bash
# 가상환경 활성화 후 패키지 재설치
cd ~/reactbase
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn[standard]
```

### F. 재부팅 후 자동 시작 확인

```bash
# 자동 시작 활성화 상태 확인
sudo systemctl is-enabled fastapi.service
# 출력: enabled (활성화됨)
# 출력: disabled (비활성화됨)

# 비활성화되어 있다면:
sudo systemctl enable fastapi.service

# 재부팅 테스트
sudo reboot

# 재접속 후 확인
sudo systemctl status fastapi.service
sudo systemctl status nginx
```

### G. 모니터링 & 로그

**시스템 리소스 확인:**

```bash
# CPU, 메모리 사용량 실시간 모니터링
htop
# 또는
top

# 디스크 사용량
df -h

# 메모리 사용량
free -h
```

**로그 위치:**

| 서비스 | 로그 위치 |
|--------|----------|
| FastAPI | `sudo journalctl -u fastapi.service` |
| Nginx 액세스 | `/var/log/nginx/access.log` |
| Nginx 에러 | `/var/log/nginx/error.log` |
| 시스템 | `/var/log/syslog` |

**로그 모니터링 명령어:**

```bash
# FastAPI 실시간 로그
sudo journalctl -u fastapi.service -f

# Nginx 액세스 로그 실시간
sudo tail -f /var/log/nginx/access.log

# Nginx 에러 로그 실시간
sudo tail -f /var/log/nginx/error.log

# 여러 로그 동시 모니터링
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

---

## 9) HTTPS(선택) — 곧바로 운영 반영 시 권장

운영 환경에서는 보안을 위해 **HTTPS**를 사용해야 합니다.

도메인이 있다면 **Let's Encrypt(certbot)**으로 무료 SSL/TLS 인증서를 발급받을 수 있습니다.

### 사전 준비

1. **도메인 필요**: 도메인을 구매하고 EC2 Public IP를 가리키도록 DNS A 레코드 설정
2. **방화벽**: 보안 그룹에서 **443 포트(HTTPS)** 추가 개방

| 포트 | 프로토콜 | 소스 | 용도 |
|------|---------|------|------|
| 443 | TCP | 0.0.0.0/0 | HTTPS |

### Certbot 설치 및 인증서 발급

```bash
# Certbot 및 Nginx 플러그인 설치
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 자동 발급 및 Nginx 설정
sudo certbot --nginx -d your.domain.com

# 여러 도메인을 동시에 지원하는 경우
sudo certbot --nginx -d your.domain.com -d www.your.domain.com
```

**대화형 프롬프트:**
1. 이메일 입력 (인증서 만료 알림용)
2. 이용약관 동의
3. HTTP → HTTPS 리다이렉트 설정 여부 (권장: Yes)

### 설정 후 변경사항

Certbot이 자동으로 Nginx 설정을 수정합니다:

```nginx
server {
    listen 80;
    server_name your.domain.com;
    # HTTP → HTTPS 리다이렉트 자동 추가
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your.domain.com;

    # SSL 인증서 경로 (자동 설정됨)
    ssl_certificate /etc/letsencrypt/live/your.domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your.domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 기존 location 블록들...
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ...
    }
}
```

### 인증서 자동 갱신

Let's Encrypt 인증서는 **90일** 유효기간을 가집니다.

Certbot은 자동 갱신 타이머를 설정합니다:

```bash
# 자동 갱신 타이머 상태 확인
sudo systemctl status certbot.timer

# 갱신 테스트 (실제로 갱신하지 않고 테스트만)
sudo certbot renew --dry-run

# 수동 갱신 (필요한 경우)
sudo certbot renew
```

### HTTPS 동작 확인

```bash
# 로컬에서 테스트
curl -I https://your.domain.com

# SSL 인증서 정보 확인
openssl s_client -connect your.domain.com:443 -servername your.domain.com
```

**브라우저에서 확인:**
- `https://your.domain.com` 접속
- 주소창에 자물쇠 아이콘 확인
- 인증서 정보 확인

### 추가 보안 설정 (선택)

HTTPS 설정 후 추가 보안 헤더를 Nginx에 추가할 수 있습니다:

```nginx
server {
    listen 443 ssl http2;
    server_name your.domain.com;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 기존 보안 헤더들...
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # ...
}
```

설정 후 Nginx 리로드:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

> 💡 **Tip**: 도메인이 없어도 Self-Signed 인증서로 HTTPS를 사용할 수 있지만, 브라우저에서 경고가 표시됩니다.

---

## 10) 최종 점검 시나리오

전체 설정이 완료되었다면 아래 체크리스트로 동작을 확인하세요.

### 체크리스트

**1. 서비스 상태 확인**

```bash
# FastAPI 서비스 확인
sudo systemctl status fastapi.service
# 출력: active (running) 이어야 함

# Nginx 서비스 확인
sudo systemctl status nginx
# 출력: active (running) 이어야 함

# 포트 리스닝 확인
sudo netstat -tulpn | grep -E ':80|:8000'
# 80 포트: nginx
# 8000 포트: uvicorn
```

**2. 로컬 테스트 (EC2 서버 내부)**

```bash
# Uvicorn 직접 접근 테스트
curl -s http://127.0.0.1:8000/
# 출력: welcome

# Nginx를 통한 접근 테스트
curl -I http://localhost/
# 출력: HTTP/1.1 200 OK

curl http://localhost/
# 출력: welcome

# 헬스 체크 엔드포인트
curl http://localhost/health
# 출력: {"status":"healthy","service":"fastapi"}

# 추가 엔드포인트 테스트
curl http://localhost/hello  # 출력: hello
curl http://localhost/world  # 출력: world
```

**3. 외부 접근 테스트 (브라우저)**

로컬 PC 브라우저에서 다음 URL 접속:

- `http://<EC2_Public_IP>/` → `"welcome"` 출력 확인
- `http://<EC2_Public_IP>/hello` → `"hello"` 출력 확인
- `http://<EC2_Public_IP>/health` → JSON 응답 확인
- `http://<EC2_Public_IP>/docs` → FastAPI 자동 생성 API 문서 확인

**4. 정적 파일 테스트**

```bash
# 테스트 파일 생성
echo "Static file test" > ~/reactbase/public/test.txt

# 서버 내부에서 테스트
curl http://localhost/images/test.txt

# 외부 브라우저에서 테스트
# http://<EC2_Public_IP>/images/test.txt
```

**5. 개발 워크플로우 테스트**

```bash
# 1. 로컬에서 server.py 수정
# 예: 새 엔드포인트 추가

# 2. VSCode에서 저장 (자동 업로드)

# 3. 서비스 재시작
sudo systemctl restart fastapi.service

# 4. 변경사항 확인
curl http://localhost/새로운엔드포인트
```

**6. 재부팅 테스트**

```bash
# 서버 재부팅
sudo reboot

# 재접속 후 (약 1-2분 후)
ssh -i 키.pem ubuntu@<EC2_Public_IP>

# 자동 시작 확인
sudo systemctl status fastapi.service
sudo systemctl status nginx

# 외부 접근 확인
curl http://localhost/
```

### 성공 기준

✅ **모든 서비스가 `active (running)` 상태**

✅ **로컬에서 모든 엔드포인트 정상 응답**

✅ **외부 브라우저에서 접근 가능**

✅ **정적 파일 서빙 정상 동작**

✅ **재부팅 후 자동 시작 확인**

### 문제 발생 시

문제가 발생하면 [8) 운영 체크리스트 & 트러블슈팅](#8-운영-체크리스트--트러블슈팅) 섹션을 참고하세요.

---

## 📌 결론

### 구축한 아키텍처 요약

이 가이드를 통해 다음과 같은 **프로덕션 수준의 웹 서버 환경**을 구축했습니다:

```
┌─────────────────────────────────────────┐
│             Internet                     │
└──────────────┬──────────────────────────┘
               │ Port 80 (HTTP)
               │
┌──────────────▼──────────────────────────┐
│        AWS EC2 (Ubuntu)                  │
│  ┌────────────────────────────────────┐  │
│  │  Nginx (Reverse Proxy)             │  │
│  │  - Security Headers                │  │
│  │  - Static File Serving             │  │
│  │  - Load Balancing (확장 가능)      │  │
│  └──────────┬─────────────────────────┘  │
│             │ 127.0.0.1:8000              │
│  ┌──────────▼─────────────────────────┐  │
│  │  FastAPI (Uvicorn)                 │  │
│  │  - systemd Auto-start              │  │
│  │  - Multi-worker Support            │  │
│  │  - Application Logic               │  │
│  └────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 핵심 성과

**✅ 보안**
- 애플리케이션 서버(8000 포트)는 외부에 노출되지 않음
- Nginx를 통한 요청 필터링 및 보안 헤더 설정
- HTTPS 적용 가능 (Let's Encrypt)

**✅ 안정성**
- systemd로 재부팅 시 자동 시작
- 프로세스 실패 시 자동 재시작
- 헬스 체크 엔드포인트로 모니터링 가능

**✅ 성능**
- Nginx가 정적 파일을 직접 서빙 (애플리케이션 서버 부하 감소)
- Multi-worker 프로세스로 동시 처리 능력 향상
- 브라우저 캐싱 설정으로 네트워크 트래픽 감소

**✅ 개발 생산성**
- VSCode SFTP로 파일 저장 시 자동 배포
- FastAPI 자동 생성 API 문서 (`/docs`)
- journalctl로 실시간 로그 모니터링

### 실무 팁 요약

**보안 그룹 설정**
- 22 (SSH), 80 (HTTP), 443 (HTTPS)만 개방
- 8000 포트는 외부에 열지 말 것

**ISP 차단 문제**
- 접속이 안 되면 휴대폰 핫스팟으로 테스트
- ISP 레벨 차단일 가능성 확인

**Windows 사용자**
- SFTP 경로 백슬래시 4개 이스케이프 (`\\\\`)
- PEM 파일 권한 설정 (`icacls` 명령어)

**로그 모니터링**
```bash
# FastAPI 로그
sudo journalctl -u fastapi.service -f

# Nginx 로그
sudo tail -f /var/log/nginx/error.log
```

### 다음 단계 제안

현재 구축한 기본 환경을 바탕으로 다음 기능들을 추가할 수 있습니다:

**1. HTTPS 적용**
- Let's Encrypt로 무료 SSL 인증서
- HTTP → HTTPS 자동 리다이렉트

**2. 데이터베이스 연동**
- PostgreSQL, MySQL, MongoDB 등
- RDS(관리형 데이터베이스) 사용 권장

**3. 모니터링 & 알림**
- CloudWatch 로그 전송
- Prometheus + Grafana
- 에러 발생 시 이메일/Slack 알림

**4. CI/CD 파이프라인**
- GitHub Actions로 자동 배포
- 테스트 자동화

**5. 컨테이너화**
- Docker로 애플리케이션 패키징
- ECS/EKS로 오케스트레이션

**6. 부하 분산**
- Application Load Balancer (ALB)
- Auto Scaling Group

**7. 백업 & 재해 복구**
- 데이터베이스 정기 백업
- AMI 스냅샷
- 다중 AZ 배포

### 마무리

이제 **EC2에서 FastAPI + Nginx 리버스 프록시 구조**로 안전하고 효율적인 웹 서비스를 운영할 수 있는 기반이 마련되었습니다.

**systemd** 자동 기동, **SFTP** 배포 자동화, **트러블슈팅** 가이드까지 실무에서 바로 활용할 수 있는 내용을 담았습니다.

운영하면서 발생하는 이슈들은 이 가이드의 트러블슈팅 섹션을 참고하시고, 추가 질문이 있다면 AWS 공식 문서나 커뮤니티를 활용하세요!

**행복한 배포 되세요!** 🚀

---

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Uvicorn 공식 문서](https://www.uvicorn.org/)
- [Nginx 공식 문서](https://nginx.org/en/docs/)
- [systemd 서비스 관리](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Let's Encrypt (Certbot)](https://certbot.eff.org/)
- [AWS EC2 사용 설명서](https://docs.aws.amazon.com/ec2/)

---

**작성일**: 2025년 10월 12일  
**카테고리**: DevOps, AWS  
**태그**: EC2, Nginx, FastAPI, Uvicorn, Ubuntu, systemd, ReverseProxy, SFTP

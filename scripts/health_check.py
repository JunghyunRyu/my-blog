#!/usr/bin/env python3
"""시스템 상태를 점검하는 헬스체크 스크립트.

설정, API 키, 네트워크, 디스크 등을 확인합니다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests 라이브러리가 설치되지 않았습니다.")

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.config import Config


def check_config() -> tuple[bool, list[str]]:
    """설정 유효성을 확인합니다."""
    print("📋 설정 검사 중...")
    errors = Config.validate()
    
    if errors:
        print("  ❌ 설정 오류 발견:")
        for error in errors:
            print(f"     - {error}")
        return False, errors
    
    print("  ✅ 설정이 올바릅니다.")
    return True, []


def check_openai_api() -> tuple[bool, str]:
    """OpenAI API 키를 테스트합니다."""
    print("\n🔑 OpenAI API 테스트 중...")
    
    if not Config.OPENAI_API_KEY:
        print("  ❌ API 키가 설정되지 않았습니다.")
        return False, "API 키 미설정"
    
    if not REQUESTS_AVAILABLE:
        print("  ❌ requests 라이브러리가 필요합니다.")
        return False, "라이브러리 미설치"
    
    try:
        # 간단한 API 호출로 키 유효성 검증
        url = "https://api.openai.com/v1/models"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        model_count = len(data.get("data", []))
        print(f"  ✅ API 키가 유효합니다. (사용 가능한 모델: {model_count}개)")
        return True, "정상"
            
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            print("  ❌ API 키가 유효하지 않습니다.")
            return False, "인증 실패"
        else:
            print(f"  ⚠️  API 호출 오류: HTTP {e.response.status_code}")
            return False, f"HTTP {e.response.status_code}"
    except Exception as e:
        print(f"  ⚠️  API 테스트 실패: {e}")
        return False, str(e)


def check_network() -> tuple[bool, str]:
    """네트워크 연결을 확인합니다."""
    print("\n🌐 네트워크 연결 테스트 중...")
    
    if not REQUESTS_AVAILABLE:
        print("  ❌ requests 라이브러리가 필요합니다.")
        return False, "라이브러리 미설치"
    
    test_urls = [
        ("GeekNews RSS", Config.GEEKNEWS_FEED_URL),
        ("OpenAI API", "https://api.openai.com"),
    ]
    
    all_ok = True
    for name, url in test_urls:
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            print(f"  ✅ {name}: 연결 성공 (HTTP {response.status_code})")
        except Exception as e:
            print(f"  ❌ {name}: 연결 실패 ({e})")
            all_ok = False
    
    if all_ok:
        return True, "정상"
    else:
        return False, "일부 연결 실패"


def check_disk_space() -> tuple[bool, str]:
    """디스크 용량을 확인합니다."""
    print("\n💾 디스크 용량 확인 중...")
    
    try:
        usage = shutil.disk_usage(Config.PROJECT_ROOT)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_percent = (usage.used / usage.total) * 100
        
        print(f"  전체: {total_gb:.1f}GB")
        print(f"  사용: {used_percent:.1f}%")
        print(f"  여유: {free_gb:.1f}GB")
        
        if free_gb < 1.0:
            print("  ⚠️  디스크 용량이 부족합니다!")
            return False, f"여유 공간 {free_gb:.1f}GB"
        elif free_gb < 5.0:
            print("  ⚠️  디스크 용량이 부족해지고 있습니다.")
            return True, f"여유 공간 {free_gb:.1f}GB (주의)"
        else:
            print("  ✅ 디스크 용량이 충분합니다.")
            return True, "정상"
            
    except Exception as e:
        print(f"  ❌ 디스크 용량 확인 실패: {e}")
        return False, str(e)


def check_last_run() -> tuple[bool, str]:
    """마지막 실행 시간을 확인합니다."""
    print("\n⏰ 마지막 실행 시간 확인 중...")
    
    state_file = Config.STATE_FILE
    
    if not state_file.exists():
        print("  ℹ️  상태 파일이 없습니다 (아직 실행된 적 없음).")
        return True, "미실행"
    
    try:
        stat = state_file.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()
        delta = now - mtime
        
        hours_ago = delta.total_seconds() / 3600
        
        print(f"  마지막 업데이트: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  경과 시간: {hours_ago:.1f}시간")
        
        if hours_ago > 24:
            print("  ⚠️  24시간 이상 실행되지 않았습니다!")
            return False, f"{hours_ago:.1f}시간 전"
        else:
            print("  ✅ 정상적으로 실행되고 있습니다.")
            return True, f"{hours_ago:.1f}시간 전"
            
    except Exception as e:
        print(f"  ❌ 상태 파일 확인 실패: {e}")
        return False, str(e)


def check_directories() -> tuple[bool, str]:
    """필수 디렉토리 존재를 확인합니다."""
    print("\n📁 디렉토리 구조 확인 중...")
    
    required_dirs = [
        Config.POSTS_DIR,
        Config.DATA_DIR,
        Config.LOGS_DIR,
        Config.POSTS_DIR / "learning",
        Config.POSTS_DIR / "qa-engineer",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"  ✅ {dir_path.relative_to(Config.PROJECT_ROOT)}")
        else:
            print(f"  ❌ {dir_path.relative_to(Config.PROJECT_ROOT)} (없음)")
            all_ok = False
    
    if all_ok:
        return True, "정상"
    else:
        return False, "일부 디렉토리 없음"


def check_nodejs() -> tuple[bool, str]:
    """Node.js 설치를 확인합니다."""
    print("\n🟢 Node.js 확인 중...")
    
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ Node.js 설치됨: {version}")
            return True, version
        else:
            print("  ❌ Node.js가 설치되어 있지 않습니다.")
            return False, "미설치"
    except FileNotFoundError:
        print("  ❌ Node.js가 설치되어 있지 않습니다.")
        return False, "미설치"
    except Exception as e:
        print(f"  ⚠️  Node.js 확인 실패: {e}")
        return False, str(e)


def check_mcp_server() -> tuple[bool, str]:
    """MCP Sequential Thinking 서버 연결을 확인합니다."""
    print("\n🧠 MCP 서버 확인 중...")
    
    # MCP 비활성화 확인
    if os.getenv("ENABLE_MCP", "true").lower() not in ("true", "1", "yes"):
        print("  ℹ️  MCP가 비활성화되어 있습니다.")
        return True, "비활성화"
    
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    
    try:
        # HTTP 헬스체크 시도
        request = urllib.request.Request(
            f"{mcp_url}/health",
            headers={"User-Agent": "HealthCheck/1.0"}
        )
        
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status == 200:
                print(f"  ✅ MCP 서버 연결 성공: {mcp_url}")
                return True, "정상"
            else:
                print(f"  ⚠️  MCP 서버 응답 이상: HTTP {response.status}")
                return False, f"HTTP {response.status}"
                
    except urllib.error.URLError as e:
        print(f"  ❌ MCP 서버에 연결할 수 없습니다: {e}")
        print(f"     확인: sudo systemctl status mcp-sequentialthinking")
        return False, "연결 실패"
    except Exception as e:
        print(f"  ⚠️  MCP 서버 확인 실패: {e}")
        return False, str(e)


def check_git_config() -> tuple[bool, str]:
    """Git 설정을 확인합니다."""
    print("\n🔧 Git 설정 확인 중...")
    
    errors = []
    
    # Git 사용자 이름 확인
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            username = result.stdout.strip()
            print(f"  ✅ Git user.name: {username}")
        else:
            print("  ❌ Git user.name이 설정되지 않았습니다.")
            errors.append("user.name 미설정")
    except Exception as e:
        print(f"  ⚠️  Git user.name 확인 실패: {e}")
        errors.append(f"user.name 오류: {e}")
    
    # Git 사용자 이메일 확인
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            email = result.stdout.strip()
            print(f"  ✅ Git user.email: {email}")
        else:
            print("  ❌ Git user.email이 설정되지 않았습니다.")
            errors.append("user.email 미설정")
    except Exception as e:
        print(f"  ⚠️  Git user.email 확인 실패: {e}")
        errors.append(f"user.email 오류: {e}")
    
    # Git 원격 저장소 확인
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Config.PROJECT_ROOT
        )
        if result.returncode == 0 and result.stdout.strip():
            remotes = result.stdout.strip().split('\n')
            print(f"  ✅ Git 원격 저장소: {len(remotes)}개 등록됨")
        else:
            print("  ⚠️  Git 원격 저장소가 설정되지 않았습니다.")
            errors.append("원격 저장소 미설정")
    except Exception as e:
        print(f"  ⚠️  Git 원격 저장소 확인 실패: {e}")
        errors.append(f"원격 저장소 오류: {e}")
    
    if errors:
        return False, ", ".join(errors)
    else:
        return True, "정상"


def main() -> int:
    """헬스체크를 실행합니다."""
    print("=" * 80)
    print("GeekNews 자동화 헬스체크")
    print("=" * 80)
    print()
    
    checks = [
        ("설정", check_config),
        ("OpenAI API", check_openai_api),
        ("네트워크", check_network),
        ("Node.js", check_nodejs),
        ("MCP 서버", check_mcp_server),
        ("Git 설정", check_git_config),
        ("디스크", check_disk_space),
        ("디렉토리", check_directories),
        ("마지막 실행", check_last_run),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            success, message = check_func()
            results[name] = (success, message)
        except Exception as e:
            print(f"\n❌ {name} 검사 중 오류: {e}")
            results[name] = (False, f"오류: {e}")
    
    # 요약
    print("\n" + "=" * 80)
    print("헬스체크 요약")
    print("=" * 80)
    
    all_pass = True
    for name, (success, message) in results.items():
        status = "✅ 정상" if success else "❌ 문제"
        print(f"{status} - {name}: {message}")
        if not success:
            all_pass = False
    
    print("=" * 80)
    
    if all_pass:
        print("\n✅ 모든 검사를 통과했습니다!")
        return 0
    else:
        print("\n⚠️  일부 검사에서 문제가 발견되었습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())



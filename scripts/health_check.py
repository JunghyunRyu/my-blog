#!/usr/bin/env python3
"""시스템 상태를 점검하는 헬스체크 스크립트.

설정, API 키, 네트워크, 디스크 등을 확인합니다.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from geeknews.config import Config


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
    
    try:
        # 간단한 API 호출로 키 유효성 검증
        url = "https://api.openai.com/v1/models"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            }
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            model_count = len(data.get("data", []))
            print(f"  ✅ API 키가 유효합니다. (사용 가능한 모델: {model_count}개)")
            return True, "정상"
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("  ❌ API 키가 유효하지 않습니다.")
            return False, "인증 실패"
        else:
            print(f"  ⚠️  API 호출 오류: HTTP {e.code}")
            return False, f"HTTP {e.code}"
    except Exception as e:
        print(f"  ⚠️  API 테스트 실패: {e}")
        return False, str(e)


def check_network() -> tuple[bool, str]:
    """네트워크 연결을 확인합니다."""
    print("\n🌐 네트워크 연결 테스트 중...")
    
    test_urls = [
        ("GeekNews RSS", Config.GEEKNEWS_FEED_URL),
        ("OpenAI API", "https://api.openai.com"),
    ]
    
    all_ok = True
    for name, url in test_urls:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                print(f"  ✅ {name}: 연결 성공 (HTTP {response.status})")
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



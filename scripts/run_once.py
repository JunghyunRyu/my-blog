#!/usr/bin/env python3
"""GeekNews 파이프라인을 1회 실행하는 스크립트.

EC2 cron job이나 수동 실행에 사용됩니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.config import Config
from automation.geeknews_pipeline import main as pipeline_main


def main() -> int:
    """파이프라인을 1회 실행합니다."""
    print("=" * 80)
    print("GeekNews 자동화 - 1회 실행")
    print("=" * 80)
    
    # 설정 검증
    errors = Config.validate()
    if errors:
        print("\n❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    # 설정 출력
    if Config.LOG_LEVEL == "DEBUG":
        Config.print_config()
    
    try:
        # 파이프라인 실행
        return pipeline_main()
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
        return 130
    except Exception as exc:
        print(f"\n❌ 예상치 못한 오류: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())



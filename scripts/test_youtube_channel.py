"""YouTube 채널 수집 검증 스크립트.

채널 ID를 입력받아 API 연결 테스트 및 기본 정보를 조회합니다.
"""
import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.config import Config

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("❌ google-api-python-client가 설치되어 있지 않습니다.")
    print("   설치: pip install google-api-python-client")
    sys.exit(1)


def test_channel_info(api_key: str, channel_id: str):
    """채널 정보를 조회하여 API 연결을 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"YouTube 채널 정보 조회 테스트")
    print(f"{'='*60}\n")
    
    try:
        service = build("youtube", "v3", developerKey=api_key)
        
        # 채널 정보 조회
        print(f"📡 채널 ID: {channel_id}")
        print(f"   API 요청 중...")
        
        response = service.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()
        
        if not response.get("items"):
            print(f"❌ 채널을 찾을 수 없습니다. ID를 확인하세요.")
            return False
        
        channel = response["items"][0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        
        print(f"\n✅ 채널 정보 조회 성공!")
        print(f"\n채널명: {snippet.get('title', 'N/A')}")
        print(f"설명: {snippet.get('description', 'N/A')[:100]}...")
        print(f"구독자 수: {stats.get('subscriberCount', 'N/A')}")
        print(f"총 동영상 수: {stats.get('videoCount', 'N/A')}")
        print(f"총 조회수: {stats.get('viewCount', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def test_channels_from_config(api_key: str):
    """설정 파일의 모든 활성 채널을 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"설정 파일 채널 테스트")
    print(f"{'='*60}\n")
    
    channels = Config.load_channels()
    
    if not channels:
        print("⚠️ 활성화된 채널이 없습니다.")
        return
    
    print(f"활성 채널 {len(channels)}개를 테스트합니다.\n")
    
    success_count = 0
    for idx, ch in enumerate(channels, 1):
        channel_id = ch.get("id", "")
        channel_name = ch.get("name", "Unknown")
        priority = ch.get("priority", "N/A")
        
        print(f"\n[{idx}/{len(channels)}] {channel_name} (우선순위: {priority})")
        print(f"     채널 ID: {channel_id}")
        
        if test_channel_info(api_key, channel_id):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"테스트 완료: {success_count}/{len(channels)} 성공")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 채널 수집 검증 스크립트"
    )
    parser.add_argument(
        "--channel-id",
        help="테스트할 채널 ID (옵션)"
    )
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="설정 파일의 모든 채널 테스트"
    )
    
    args = parser.parse_args()
    
    # API 키 확인
    if not Config.YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 YOUTUBE_API_KEY를 설정하세요.")
        sys.exit(1)
    
    print(f"✅ API 키 확인 완료")
    
    # 테스트 실행
    if args.test_config:
        test_channels_from_config(Config.YOUTUBE_API_KEY)
    elif args.channel_id:
        test_channel_info(Config.YOUTUBE_API_KEY, args.channel_id)
    else:
        print("\n사용법:")
        print("  특정 채널 테스트:")
        print("    python scripts/test_youtube_channel.py --channel-id UCxX9wt5FWQUAAz4UrysqK9A")
        print("\n  설정 파일 전체 테스트:")
        print("    python scripts/test_youtube_channel.py --test-config")


if __name__ == "__main__":
    main()


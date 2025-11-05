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
from automation.sources import youtube_collector

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


def test_channel_collection(api_key: str, channel_id: str, max_results: int = 3):
    """채널에서 실제 동영상 수집을 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"YouTube 채널 수집 테스트")
    print(f"{'='*60}\n")
    
    try:
        print(f"📡 채널 ID: {channel_id}")
        print(f"   최대 결과: {max_results}개")
        print(f"   수집 중...\n")
        
        videos = youtube_collector.collect_from_channel(
            api_key=api_key,
            channel_id=channel_id,
            max_results=max_results,
            published_after_days=30  # 최근 30일
        )
        
        if not videos:
            print("⚠️ 수집된 동영상이 없습니다.")
            return False
        
        print(f"✅ {len(videos)}개 동영상 수집 성공!\n")
        
        for idx, video in enumerate(videos, 1):
            print(f"[{idx}] {video.get('title', 'N/A')}")
            print(f"    링크: {video.get('link', 'N/A')}")
            print(f"    발행일: {video.get('published_at', 'N/A')}")
            print(f"    채널: {video.get('channel_name', 'N/A')}")
            print(f"    요약 텍스트: {len(video.get('summary', ''))}자")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_watchlist_collection(api_key: str):
    """워치리스트에서 비디오 수집을 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"YouTube 워치리스트 수집 테스트")
    print(f"{'='*60}\n")
    
    try:
        watchlist = Config.load_watchlist()
        
        if not watchlist:
            print("⚠️ 활성화된 워치리스트 항목이 없습니다.")
            return False
        
        video_ids = [item.get("video_id", "") for item in watchlist if item.get("video_id")]
        
        print(f"📡 워치리스트 비디오 {len(video_ids)}개")
        print(f"   수집 중...\n")
        
        videos = youtube_collector.collect_from_watchlist(
            api_key=api_key,
            video_ids=video_ids
        )
        
        if not videos:
            print("⚠️ 수집된 동영상이 없습니다.")
            return False
        
        print(f"✅ {len(videos)}개 동영상 수집 성공!\n")
        
        for idx, video in enumerate(videos, 1):
            print(f"[{idx}] {video.get('title', 'N/A')}")
            print(f"    링크: {video.get('link', 'N/A')}")
            print(f"    발행일: {video.get('published_at', 'N/A')}")
            print(f"    채널: {video.get('channel_name', 'N/A')}")
            print(f"    요약 텍스트: {len(video.get('summary', ''))}자")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_channels_from_config(api_key: str, max_results: int = 3):
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
        
        if test_channel_collection(api_key, channel_id, max_results=max_results):
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
        "--max-results",
        type=int,
        default=3,
        help="수집할 최대 동영상 수 (기본값: 3)"
    )
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="설정 파일의 모든 채널 테스트"
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="채널 정보만 조회 (수집 테스트 제외)"
    )
    parser.add_argument(
        "--test-watchlist",
        action="store_true",
        help="워치리스트 수집 테스트"
    )
    
    args = parser.parse_args()
    
    # API 키 확인
    if not Config.YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 YOUTUBE_API_KEY를 설정하세요.")
        sys.exit(1)
    
    print(f"✅ API 키 확인 완료")
    
    # 테스트 실행
    if args.test_watchlist:
        test_watchlist_collection(Config.YOUTUBE_API_KEY)
    elif args.test_config:
        test_channels_from_config(Config.YOUTUBE_API_KEY, max_results=args.max_results)
    elif args.channel_id:
        if args.info_only:
            test_channel_info(Config.YOUTUBE_API_KEY, args.channel_id)
        else:
            test_channel_collection(Config.YOUTUBE_API_KEY, args.channel_id, max_results=args.max_results)
    else:
        print("\n사용법:")
        print("  특정 채널 정보 조회:")
        print("    python scripts/test_youtube_channel.py --channel-id UCxX9wt5FWQUAAz4UrysqK9A --info-only")
        print("\n  특정 채널 수집 테스트:")
        print("    python scripts/test_youtube_channel.py --channel-id UCxX9wt5FWQUAAz4UrysqK9A --max-results 3")
        print("\n  설정 파일 전체 테스트:")
        print("    python scripts/test_youtube_channel.py --test-config --max-results 3")
        print("\n  워치리스트 테스트:")
        print("    python scripts/test_youtube_channel.py --test-watchlist")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
코드깎는노인 트랜스크립트 스크래퍼
구글 OAuth 로그인을 통해 코드깎는노인 사이트의 강의 트랜스크립트를 자동으로 스크래핑합니다.

사용법:
    python main.py --setup-auth              # 최초 1회 로그인 설정
    python main.py --scrape --url <URL>      # 트랜스크립트 스크래핑
    python main.py --verify-session          # 저장된 세션 유효성 검사
    python main.py --config                  # 현재 설정 확인

예시:
    python main.py --setup-auth
    python main.py --scrape --url "https://cokac.com/list/lec019/146"
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.auth_manager import AuthManager
from scraper.page_scraper import CokacScraper
from scraper.config import Config

def print_banner():
    """프로그램 시작 시 배너 출력"""
    print("=" * 80)
    print("🎓 코드깎는노인 트랜스크립트 스크래퍼 v1.0.0")
    print("   구글 OAuth 로그인 → 강의 트랜스크립트 자동 추출")
    print("   개발: Windows PowerShell 환경 최적화")
    print("=" * 80)
    print()

def print_help_message():
    """도움말 메시지 출력"""
    print("🔧 사용 가능한 명령어:")
    print()
    print("📋 초기 설정:")
    print("   python main.py --setup-auth")
    print("   → 최초 1회 구글 계정 로그인 (브라우저가 열림)")
    print()
    print("🎯 트랜스크립트 스크래핑:")
    print("   python main.py --scrape --url <강의URL>")
    print("   → 지정된 강의의 트랜스크립트 추출")
    print()
    print("✅ 세션 확인:")
    print("   python main.py --verify-session")
    print("   → 저장된 로그인 세션의 유효성 검사")
    print()
    print("⚙️ 설정 확인:")
    print("   python main.py --config")
    print("   → 현재 스크래퍼 설정값 출력")
    print()
    print("📖 예시:")
    print('   python main.py --scrape --url "https://cokac.com/list/lec019/146"')
    print()

async def setup_authentication():
    """초기 인증 설정"""
    print("🔐 코드깎는노인 로그인 설정을 시작합니다...")
    print()
    
    auth_manager = AuthManager()
    
    try:
        success = await auth_manager.setup_initial_login()
        
        if success:
            print()
            print("✅ 로그인 설정이 완료되었습니다!")
            print("🎉 이제 다음 명령으로 트랜스크립트를 스크래핑할 수 있습니다:")
            print()
            print('   python main.py --scrape --url "https://cokac.com/list/lec019/146"')
            print()
            return True
        else:
            print()
            print("❌ 로그인 설정에 실패했습니다.")
            print("💡 문제 해결 방법:")
            print("   1. 브라우저에서 구글 로그인이 완료되었는지 확인")
            print("   2. 2단계 인증이 필요한 경우 완료 후 진행")
            print("   3. 네트워크 연결 상태 확인")
            print("   4. 다시 시도: python main.py --setup-auth")
            print()
            return False
            
    except Exception as e:
        print(f"❌ 인증 설정 중 오류 발생: {e}")
        print("💡 관리자에게 문의하거나 다시 시도해주세요.")
        return False

async def verify_session():
    """저장된 세션 유효성 검사"""
    print("🔍 저장된 세션의 유효성을 확인합니다...")
    print()
    
    auth_manager = AuthManager()
    
    try:
        is_valid = await auth_manager.verify_session_validity()
        
        if is_valid:
            print("✅ 저장된 세션이 유효합니다. 스크래핑을 진행할 수 있습니다!")
        else:
            print("❌ 저장된 세션이 만료되었거나 유효하지 않습니다.")
            print("🔧 해결 방법: python main.py --setup-auth")
        
        return is_valid
        
    except FileNotFoundError:
        print("❌ 저장된 세션 파일을 찾을 수 없습니다.")
        print("🔧 해결 방법: python main.py --setup-auth")
        return False
    except Exception as e:
        print(f"❌ 세션 확인 중 오류 발생: {e}")
        return False

async def scrape_transcript(lecture_url: str):
    """트랜스크립트 스크래핑 실행"""
    if not lecture_url:
        print("❌ 스크래핑할 강의 URL을 --url 옵션으로 지정해주세요.")
        print()
        print("📖 사용법:")
        print('   python main.py --scrape --url "https://cokac.com/list/lec019/146"')
        print()
        return False
    
    # URL 기본 검증
    if not lecture_url.startswith('https://cokac.com'):
        print(f"❌ 유효하지 않은 코드깎는노인 URL입니다: {lecture_url}")
        print("✅ 올바른 URL 형식: https://cokac.com/list/lec019/146")
        return False
    
    print(f"🚀 트랜스크립트 스크래핑을 시작합니다...")
    print(f"📍 대상 URL: {lecture_url}")
    print(f"🕐 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scraper = CokacScraper()
    
    try:
        result = await scraper.scrape_lecture(lecture_url)
        
        if result:
            print()
            print("🎉 스크래핑이 성공적으로 완료되었습니다!")
            print(f"📊 추출된 트랜스크립트: {len(result)}개")
            print(f"📝 총 글자 수: {sum(item.get('length', 0) for item in result):,}자")
            print(f"🔤 총 단어 수: {sum(item.get('word_count', 0) for item in result):,}개")
            print(f"💾 저장 위치: {scraper.config.OUTPUT_PATH}/")
            print()
            
            # 샘플 트랜스크립트 미리보기
            if result:
                print("📖 트랜스크립트 미리보기 (처음 3개):")
                for i, item in enumerate(result[:3], 1):
                    timestamp = f"[{item.get('timestamp', '00:00')}] " if item.get('timestamp') else ""
                    text = item['text'][:100] + ('...' if len(item['text']) > 100 else '')
                    print(f"   {i}. {timestamp}{text}")
            print()
            
            return True
        else:
            print()
            print("😞 스크래핑에 실패했거나 추출된 트랜스크립트가 없습니다.")
            print()
            print("💡 가능한 원인:")
            print("   1. 해당 강의에 트랜스크립트가 없음")
            print("   2. 로그인 세션이 만료됨 → python main.py --verify-session")
            print("   3. 강의 접근 권한이 없음")
            print("   4. 페이지 구조가 변경됨")
            print()
            return False
            
    except FileNotFoundError:
        print("❌ 저장된 로그인 세션을 찾을 수 없습니다.")
        print("🔧 해결 방법: python main.py --setup-auth")
        return False
    except Exception as e:
        print(f"❌ 스크래핑 중 오류 발생:")
        print(f"   오류 유형: {type(e).__name__}")
        print(f"   오류 메시지: {e}")
        print()
        print("💡 문제 해결:")
        print("   1. 네트워크 연결 확인")
        print("   2. URL이 올바른지 확인")
        print("   3. 세션 유효성 확인: python main.py --verify-session")
        print("   4. 관리자에게 문의")
        return False

def show_config():
    """현재 설정 출력"""
    print("⚙️ 현재 스크래퍼 설정:")
    print()
    
    try:
        config = Config()
        config.print_config()
        print()
        print("📁 파일 경로:")
        print(f"   세션 저장: {config.STORAGE_STATE_PATH}")
        print(f"   출력 디렉토리: {config.OUTPUT_PATH}")
        print()
        print("🎯 스크래핑 대상:")
        print(f"   트랜스크립트 선택자: {config.TRANSCRIPT_SELECTOR}")
        print(f"   컨테이너 선택자: {config.TRANSCRIPT_CONTAINER}")
        print()
        
        # 파일 존재 여부 확인
        if os.path.exists(config.STORAGE_STATE_PATH):
            stat = os.stat(config.STORAGE_STATE_PATH)
            print(f"✅ 저장된 세션: 있음 (크기: {stat.st_size} bytes)")
        else:
            print("❌ 저장된 세션: 없음")
        
        if os.path.exists(config.OUTPUT_PATH):
            files = [f for f in os.listdir(config.OUTPUT_PATH) if f.endswith(('.json', '.txt'))]
            print(f"📄 저장된 파일: {len(files)}개")
        else:
            print("📄 저장된 파일: 0개 (출력 디렉토리 없음)")
        
    except Exception as e:
        print(f"❌ 설정 확인 중 오류 발생: {e}")

def setup_windows_environment():
    """Windows 환경 설정"""
    # Windows에서 이벤트 루프 정책 설정
    if sys.platform.startswith('win'):
        # Python 3.8+ 에서 Windows ProactorEventLoop 사용
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            # 이전 버전 호환성
            pass
    
    # PowerShell 환경에서 UTF-8 출력 설정
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'

def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description='코드깎는노인 강의 트랜스크립트 스크래퍼',
        epilog='자세한 사용법은 --help 옵션을 확인하세요.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 메인 액션 그룹
    action_group = parser.add_mutually_exclusive_group(required=False)
    
    action_group.add_argument(
        '--setup-auth', 
        action='store_true', 
        help='최초 1회 구글 계정 로그인 설정'
    )
    
    action_group.add_argument(
        '--scrape', 
        action='store_true', 
        help='트랜스크립트 스크래핑 실행'
    )
    
    action_group.add_argument(
        '--verify-session', 
        action='store_true', 
        help='저장된 로그인 세션의 유효성 검사'
    )
    
    action_group.add_argument(
        '--config', 
        action='store_true', 
        help='현재 설정값 출력'
    )
    
    # 스크래핑 옵션
    parser.add_argument(
        '--url', 
        type=str, 
        help='스크래핑할 강의 URL (예: https://cokac.com/list/lec019/146)'
    )
    
    # 추가 옵션
    parser.add_argument(
        '--headless', 
        type=str, 
        choices=['true', 'false'],
        help='브라우저를 헤드리스 모드로 실행 (기본값: true)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        help='출력 디렉토리 경로 (기본값: data/transcripts)'
    )
    
    return parser.parse_args()

async def main():
    """메인 실행 함수"""
    # Windows 환경 설정
    setup_windows_environment()
    
    # 배너 출력
    print_banner()
    
    # 명령행 인수 파싱
    args = parse_arguments()
    
    # 환경 변수 오버라이드
    if args.headless:
        os.environ['HEADLESS'] = args.headless
    if args.output:
        os.environ['OUTPUT_PATH'] = args.output
    
    try:
        # 액션 실행
        if args.setup_auth:
            success = await setup_authentication()
            sys.exit(0 if success else 1)
            
        elif args.scrape:
            success = await scrape_transcript(args.url)
            sys.exit(0 if success else 1)
            
        elif args.verify_session:
            success = await verify_session()
            sys.exit(0 if success else 1)
            
        elif args.config:
            show_config()
            sys.exit(0)
            
        else:
            # 인수가 없으면 도움말 출력
            print_help_message()
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다:")
        print(f"   {type(e).__name__}: {e}")
        print("\n💡 문제가 지속되면 관리자에게 문의해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    # 메인 함수 실행
    asyncio.run(main())


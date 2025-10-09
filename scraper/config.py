import os
from dotenv import load_dotenv

# .env 파일이 있으면 로드, 없으면 기본값 사용
try:
    load_dotenv()
except:
    pass

class Config:
    """코드깎는노인 스크래퍼 설정 클래스"""
    
    # 사이트 URL 설정
    LOGIN_URL = os.getenv('COKAC_LOGIN_URL', 'https://cokac.com/member')
    BASE_URL = os.getenv('COKAC_BASE_URL', 'https://cokac.com')
    
    # 파일 경로 설정
    STORAGE_STATE_PATH = os.getenv('STORAGE_STATE_PATH', 'data/cokac_storage.json')
    OUTPUT_PATH = os.getenv('OUTPUT_PATH', 'data/transcripts')
    
    # 브라우저 설정
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
    SCROLL_DELAY = int(os.getenv('SCROLL_DELAY', '500'))
    USER_AGENT = os.getenv('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 트랜스크립트 스크래핑 관련 설정
    TRANSCRIPT_SELECTOR = 'span[class*="TranscriptCue_lazy_module_cueText"]'
    TRANSCRIPT_CONTAINER = 'div[class*="transcript"], div[class*="TranscriptCue"], [class*="transcript-container"]'
    TIMESTAMP_SELECTOR = 'span[class*="time"], span[class*="timestamp"], [class*="cue-time"]'
    
    # 스크롤 및 로딩 설정
    MAX_SCROLL_ATTEMPTS = 50
    SCROLL_STEP = 800
    IDLE_THRESHOLD = 5
    NETWORK_TIMEOUT = 5000
    
    # 로그 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """설정값 유효성 검사"""
        errors = []
        
        if not cls.LOGIN_URL.startswith('http'):
            errors.append("LOGIN_URL must start with http or https")
        
        if not cls.BASE_URL.startswith('http'):
            errors.append("BASE_URL must start with http or https")
        
        if cls.TIMEOUT < 1000:
            errors.append("TIMEOUT must be at least 1000ms")
        
        if cls.SCROLL_DELAY < 100:
            errors.append("SCROLL_DELAY must be at least 100ms")
        
        if errors:
            raise ValueError("Configuration errors: " + ", ".join(errors))
        
        return True
    
    @classmethod
    def print_config(cls):
        """현재 설정값 출력"""
        print("🔧 현재 설정:")
        print(f"   LOGIN_URL: {cls.LOGIN_URL}")
        print(f"   BASE_URL: {cls.BASE_URL}")
        print(f"   STORAGE_STATE_PATH: {cls.STORAGE_STATE_PATH}")
        print(f"   OUTPUT_PATH: {cls.OUTPUT_PATH}")
        print(f"   HEADLESS: {cls.HEADLESS}")
        print(f"   TIMEOUT: {cls.TIMEOUT}ms")
        print(f"   SCROLL_DELAY: {cls.SCROLL_DELAY}ms")

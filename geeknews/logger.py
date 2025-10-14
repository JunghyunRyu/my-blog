"""중앙 집중식 로깅 시스템.

파일 로깅, rotation, 구조화된 로깅을 지원합니다.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .config import Config


class JsonFormatter(logging.Formatter):
    """JSON 형식 로그 포매터."""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 변환합니다."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """텍스트 형식 로그 포매터."""
    
    FORMAT = "%(asctime)s [%(levelname)8s] %(name)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self):
        super().__init__(self.FORMAT, self.DATE_FORMAT)


def setup_logger(
    name: str = "geeknews",
    level: str | None = None,
    log_file: Path | None = None,
) -> logging.Logger:
    """로거를 설정합니다.
    
    Args:
        name: 로거 이름
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일에 저장하지 않음)
    
    Returns:
        설정된 로거
    """
    # 로거 생성
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 로그 레벨 설정
    if level is None:
        level = Config.LOG_LEVEL
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 포매터 선택
    if Config.LOG_FORMAT.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()
    
    # 콘솔 핸들러 (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (옵션)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "geeknews") -> logging.Logger:
    """기존 로거를 가져오거나 새로 생성합니다.
    
    Args:
        name: 로거 이름
    
    Returns:
        로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 로거가 아직 설정되지 않았으면 기본 설정 적용
    if not logger.handlers:
        log_file = Config.LOGS_DIR / "geeknews.log"
        logger = setup_logger(name, log_file=log_file)
    
    return logger


# 기본 로거 생성
default_logger = get_logger()


def log_execution(func):
    """함수 실행을 로깅하는 데코레이터.
    
    Usage:
        @log_execution
        def my_function():
            pass
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.info(f"실행 시작: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"실행 완료: {func.__name__}")
            return result
        except Exception as exc:
            logger.error(f"실행 실패: {func.__name__} - {exc}", exc_info=True)
            raise
    
    return wrapper


# 사용 예시
if __name__ == "__main__":
    # 기본 로깅 테스트
    logger = get_logger()
    
    logger.debug("디버그 메시지")
    logger.info("정보 메시지")
    logger.warning("경고 메시지")
    logger.error("에러 메시지")
    
    try:
        raise ValueError("테스트 예외")
    except ValueError:
        logger.exception("예외 발생!")



"""중앙 집중식 로깅 시스템 모듈.

모든 모듈에서 사용할 수 있는 표준화된 로깅 시스템을 제공합니다.
"""
from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from automation.config import Config


class JSONFormatter(logging.Formatter):
    """JSON 형식의 로그 포맷터."""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환합니다."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 예외 정보가 있으면 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드가 있으면 추가
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """텍스트 형식의 로그 포맷터."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
    format_type: Optional[str] = None
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.
    
    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
        log_file: 로그 파일 경로 (None이면 파일 로깅 비활성화)
        level: 로그 레벨 (None이면 Config.LOG_LEVEL 사용)
        format_type: 로그 포맷 타입 ("json" 또는 "text", None이면 Config.LOG_FORMAT 사용)
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 재설정하지 않음
    if logger.handlers:
        return logger
    
    # 로그 레벨 설정
    if level is None:
        level = Config.LOG_LEVEL
    level_name = level.upper()
    log_level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(log_level)
    
    # 포맷터 선택
    if format_type is None:
        format_type = Config.LOG_FORMAT
    
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (log_file이 제공된 경우)
    if log_file:
        try:
            # 로그 디렉토리 생성
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=Config.LOG_MAX_BYTES,
                backupCount=Config.LOG_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 파일 로깅 실패해도 콘솔 로깅은 계속
            logger.warning(f"파일 로깅 설정 실패: {e}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    기본 설정으로 로거를 가져옵니다.
    
    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 그대로 반환
    if logger.handlers:
        return logger
    
    # 기본 설정으로 로거 설정
    return setup_logger(name)


# 모듈 레벨 로거 (자동 설정)
_module_logger = get_logger(__name__)


"""MCP Sequential Thinking 클라이언트


이 모듈은 MCP Sequential Thinking 서버와 통신하여
복잡한 문제에 대한 단계별 사고 분석을 제공합니다.

환경 변수:
-----------
ENABLE_MCP : bool
    MCP 클라이언트 활성화 여부 (기본값: true)
MCP_SERVER_URL : str
    MCP 서버 URL (기본값: http://localhost:3000)
MCP_THINKING_DEPTH : int
    사고 깊이 수준 1-5 (기본값: 3)
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional
import json

try:
    import httpx
except ImportError:
    httpx = None


class SequentialThinkingClient:
    """Sequential Thinking MCP 서버와 통신하는 비동기 클라이언트"""
    
    def __init__(
        self, 
        server_url: str | None = None,
        timeout: float = 30.0
    ):
        """
        MCP 클라이언트 초기화
        
        Args:
            server_url: MCP 서버 URL (None이면 환경 변수 사용)
            timeout: 요청 타임아웃 (초)
        """
        if httpx is None:
            raise ImportError(
                "httpx 패키지가 필요합니다. "
                "'pip install httpx'를 실행하세요."
            )
        
        self.server_url = (
            server_url 
            or os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        ).rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def think(
        self,
        problem: str,
        depth: int | None = None,
        context: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Sequential Thinking 도구를 호출하여 문제를 분석
        
        Args:
            problem: 분석할 문제 또는 질문
            depth: 사고 깊이 (1-5, None이면 환경 변수 사용)
            context: 추가 컨텍스트 정보
        
        Returns:
            분석 결과 딕셔너리
            {
                "thoughts": ["단계1", "단계2", ...],
                "insights": ["통찰1", "통찰2", ...],
                "conclusion": "최종 결론",
                "error": "오류 메시지" (실패 시)
            }
        
        Raises:
            httpx.HTTPError: 서버 통신 실패
        """
        if depth is None:
            depth = int(os.getenv("MCP_THINKING_DEPTH", "3"))
        
        # depth 범위 제한
        depth = max(1, min(5, depth))
        
        payload = {
            "problem": problem,
            "depth": depth,
            "context": context or {}
        }
        
        try:
            response = await self.client.post(
                f"{self.server_url}/think",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # 폴백: 오류 정보 반환
            return {
                "error": str(e),
                "fallback": True,
                "thoughts": [],
                "insights": [],
                "conclusion": "MCP 서버 연결 실패"
            }
    
    async def health_check(self) -> bool:
        """
        MCP 서버 상태 확인
        
        Returns:
            서버가 정상 작동 중이면 True
        """
        try:
            response = await self.client.get(
                f"{self.server_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """클라이언트 연결 종료"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class SyncSequentialThinkingClient:
    """동기 방식 MCP 클라이언트 (기존 동기 코드와의 호환성)"""
    
    def __init__(
        self,
        server_url: str | None = None,
        timeout: float = 30.0
    ):
        """
        동기 MCP 클라이언트 초기화
        
        Args:
            server_url: MCP 서버 URL
            timeout: 요청 타임아웃 (초)
        """
        self.async_client = SequentialThinkingClient(server_url, timeout)
        self._loop = None
    
    def think(
        self,
        problem: str,
        depth: int | None = None,
        context: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        동기 방식으로 Sequential Thinking 호출
        
        Args:
            problem: 분석할 문제
            depth: 사고 깊이 (1-5)
            context: 추가 컨텍스트
        
        Returns:
            분석 결과 딕셔너리
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 새 루프 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.async_client.think(problem, depth, context)
        )
    
    def health_check(self) -> bool:
        """
        동기 방식으로 서버 상태 확인
        
        Returns:
            서버가 정상이면 True
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.async_client.health_check())
    
    def close(self):
        """클라이언트 연결 종료"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.async_client.close())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.close()
        except:
            pass


def is_mcp_enabled() -> bool:
    """
    MCP가 활성화되어 있는지 확인
    
    Returns:
        ENABLE_MCP 환경 변수가 true이면 True
    """
    return os.getenv("ENABLE_MCP", "true").lower() in ("true", "1", "yes")


def create_mcp_client() -> SyncSequentialThinkingClient | None:
    """
    MCP 클라이언트 생성 (활성화 상태 확인)
    
    Returns:
        MCP가 활성화되어 있으면 클라이언트, 아니면 None
    """
    if not is_mcp_enabled():
        return None
    
    if httpx is None:
        print("⚠️ MCP 활성화되었지만 httpx가 설치되지 않았습니다.")
        return None
    
    try:
        client = SyncSequentialThinkingClient()
        # 간단한 연결 테스트
        if client.health_check():
            return client
        else:
            print("⚠️ MCP 서버에 연결할 수 없습니다.")
            return None
    except Exception as e:
        print(f"⚠️ MCP 클라이언트 생성 실패: {e}")
        return None


# 사용 예시
if __name__ == "__main__":
    # 비동기 사용
    async def async_example():
        async with SequentialThinkingClient() as client:
            result = await client.think(
                "GeekNews 기사를 QA Engineer 관점에서 분석하는 방법",
                depth=3
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 동기 사용
    def sync_example():
        with SyncSequentialThinkingClient() as client:
            result = client.think(
                "테스트 자동화 전략 수립 방법",
                depth=2
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 실행
    print("=== 동기 예시 ===")
    sync_example()


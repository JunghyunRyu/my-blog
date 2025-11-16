"""웹 검색 및 외부 자료 수집 모듈.

GeekNews 기사와 관련된 추가 정보를 웹에서 수집합니다.
- 웹 검색 (DuckDuckGo)
- 기사 본문 스크래핑
- 전문가 의견 수집 (HackerNews, Reddit)
"""
from __future__ import annotations

import json
import re
import time
import typing as t
from dataclasses import dataclass, field

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    # ddgs (구 duckduckgo_search) 라이브러리 사용
    try:
        from ddgs import DDGS
    except ImportError:
        # 하위 호환성을 위해 구버전도 지원
        from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from automation.logger import get_logger

logger = get_logger(__name__)

if not REQUESTS_AVAILABLE:
    logger.warning("requests 라이브러리가 설치되지 않았습니다. 'pip install requests'로 설치하세요.")

if not DDGS_AVAILABLE:
    logger.warning("ddgs 라이브러리가 설치되지 않았습니다. 'pip install ddgs'로 설치하세요.")


@dataclass
class WebResource:
    """웹 검색 결과 또는 외부 자료."""
    
    title: str
    url: str
    snippet: str = ""
    source: str = ""  # 'duckduckgo', 'hackernews', 'reddit' 등


@dataclass
class ResearchResult:
    """웹 연구 결과."""
    
    web_results: list[WebResource] = field(default_factory=list)
    expert_opinions: list[dict[str, str]] = field(default_factory=list)
    related_articles: list[WebResource] = field(default_factory=list)


class WebResearcher:
    """웹 검색 및 외부 자료 수집."""
    
    def __init__(self, max_search_results: int = 5, enable_expert_search: bool = True):
        self.max_search_results = max_search_results
        self.enable_expert_search = enable_expert_search
    
    def research(self, title: str, summary: str, url: str) -> ResearchResult:
        """주어진 기사에 대한 웹 연구를 수행한다."""
        result = ResearchResult()
        
        # 1. 웹 검색 수행
        search_query = self._build_search_query(title, summary)
        result.web_results = self._search_web(search_query)
        
        # 2. 전문가 의견 수집 (선택적)
        if self.enable_expert_search:
            result.expert_opinions = self._search_expert_opinions(title)
        
        # 3. 관련 기사 검색
        result.related_articles = self._search_related_articles(title)
        
        return result
    
    def _build_search_query(self, title: str, summary: str) -> str:
        """검색 쿼리를 생성한다."""
        # 제목에서 핵심 키워드 추출
        query_parts = [title]
        
        # AI/기술 관련 키워드 추가
        tech_keywords = ["QA", "testing", "tutorial", "guide", "best practices"]
        for keyword in tech_keywords:
            if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
                query_parts.append(keyword)
                break
        
        return " ".join(query_parts[:3])  # 최대 3개 단어
    
    def _search_web(self, query: str) -> list[WebResource]:
        """DuckDuckGo를 사용하여 웹 검색을 수행한다."""
        if not DDGS_AVAILABLE:
            logger.warning("DuckDuckGo 검색 라이브러리를 사용할 수 없습니다. 빈 결과 반환.")
            return []
        
        try:
            results: list[WebResource] = []
            
            # duckduckgo-search 라이브러리 사용
            # DDGS 초기화 시 proxies 파라미터 제거 (버전 호환성 문제)
            try:
                # 최신 버전 ddgs 사용 시도
                with DDGS() as ddgs:
                    search_results = ddgs.text(
                        query, 
                        max_results=self.max_search_results,
                        region='kr-kr',  # 한국 지역 우선
                        safesearch='moderate'
                    )
                    
                    for result in search_results:
                        if isinstance(result, dict):
                            results.append(WebResource(
                                title=result.get("title", "")[:100],
                                url=result.get("href", "") or result.get("link", ""),
                                snippet=result.get("body", "") or result.get("snippet", ""),
                                source="duckduckgo"
                            ))
            except TypeError as te:
                # proxies 파라미터 오류 시 다른 방식 시도
                if "proxies" in str(te):
                    logger.warning(f"ddgs 라이브러리 버전 호환성 문제. 웹 검색을 건너뜁니다: {te}")
                    return []
                raise
            
            return results[:self.max_search_results]
            
        except Exception as exc:
            logger.warning(f"웹 검색 중 오류: {exc}", exc_info=True)
            # 에러 발생 시 빈 리스트 반환 (크래시 방지)
            return []
    
    def _search_expert_opinions(self, title: str) -> list[dict[str, str]]:
        """HackerNews API를 통해 전문가 의견을 검색한다."""
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            # HackerNews Algolia API 사용
            url = f"https://hn.algolia.com/api/v1/search"
            params = {
                "query": title[:100],
                "tags": "story",
                "hitsPerPage": 3
            }
            
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            opinions: list[dict[str, str]] = []
            
            for hit in data.get("hits", [])[:2]:
                if hit.get("num_comments", 0) > 5:  # 댓글이 5개 이상인 것만
                    opinions.append({
                        "source": "HackerNews",
                        "title": hit.get("title", ""),
                        "url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                        "comments": str(hit.get("num_comments", 0)),
                        "points": str(hit.get("points", 0))
                    })
            
            return opinions
            
        except requests.RequestException as exc:
            logger.warning(f"HackerNews API 연결 실패: {exc}", exc_info=True)
            return []
        except json.JSONDecodeError as exc:
            logger.warning(f"HackerNews API 응답 파싱 실패: {exc}", exc_info=True)
            return []
        except Exception as exc:
            logger.warning(f"전문가 의견 검색 중 오류: {exc}", exc_info=True)
            return []
    
    def _search_related_articles(self, title: str) -> list[WebResource]:
        """관련 기술 문서 및 튜토리얼을 검색한다."""
        try:
            # 특정 사이트에서 검색 (Medium, Dev.to 등)
            sites = ["site:medium.com", "site:dev.to", "site:stackoverflow.com"]
            results: list[WebResource] = []
            
            for site in sites[:2]:  # 최대 2개 사이트
                query = f"{title[:50]} {site}"
                try:
                    site_results = self._search_web(query)
                    results.extend(site_results[:1])  # 각 사이트에서 1개씩
                except Exception as site_exc:
                    logger.warning(f"{site} 검색 실패: {site_exc}", exc_info=True)
                    continue
            
            return results
            
        except Exception as exc:
            logger.warning(f"관련 기사 검색 중 오류: {exc}", exc_info=True)
            return []


def extract_article_content(url: str) -> str:
    """주어진 URL에서 기사 본문을 추출한다 (간단한 버전)."""
    if not REQUESTS_AVAILABLE:
        logger.warning("requests 라이브러리가 필요합니다.")
        return ""
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15
        )
        response.raise_for_status()
        
        # 인코딩 자동 감지
        html = response.text
        
        # 간단한 텍스트 추출 (HTML 태그 제거)
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        return text[:5000]  # 최대 5000자
        
    except requests.RequestException as exc:
        logger.warning(f"기사 URL 접근 실패: {exc}", exc_info=True)
        return ""
    except UnicodeDecodeError as exc:
        logger.warning(f"기사 본문 인코딩 오류: {exc}", exc_info=True)
        return ""
    except Exception as exc:
        logger.warning(f"기사 본문 추출 중 오류: {exc}", exc_info=True)
        return ""


# 사용 예시
if __name__ == "__main__":
    researcher = WebResearcher(max_search_results=5)
    result = researcher.research(
        title="OpenAI GPT-4 Turbo 출시",
        summary="OpenAI가 새로운 GPT-4 Turbo 모델을 발표했습니다.",
        url="https://news.hada.io/topic?id=12345"
    )
    
    logger.info("웹 검색 결과:")
    for res in result.web_results:
        logger.info(f"  - {res.title[:80]} ({res.url})")
    
    logger.info("\n전문가 의견:")
    for op in result.expert_opinions:
        logger.info(f"  - {op['title']} (댓글: {op['comments']}, 포인트: {op['points']})")


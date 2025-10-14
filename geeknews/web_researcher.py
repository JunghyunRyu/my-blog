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
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


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
        try:
            # DuckDuckGo Instant Answer API 사용
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            results: list[WebResource] = []
            
            # RelatedTopics에서 결과 추출
            related_topics = data.get("RelatedTopics", [])
            for topic in related_topics[:self.max_search_results]:
                if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                    results.append(WebResource(
                        title=topic.get("Text", "")[:100],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", ""),
                        source="duckduckgo"
                    ))
            
            # Abstract가 있으면 추가
            if data.get("Abstract") and data.get("AbstractURL"):
                results.insert(0, WebResource(
                    title=data.get("Heading", "Related Article"),
                    url=data.get("AbstractURL", ""),
                    snippet=data.get("Abstract", ""),
                    source="duckduckgo"
                ))
            
            return results[:self.max_search_results]
            
        except Exception as exc:
            print(f"웹 검색 중 오류: {exc}")
            return []
    
    def _search_expert_opinions(self, title: str) -> list[dict[str, str]]:
        """HackerNews API를 통해 전문가 의견을 검색한다."""
        try:
            # HackerNews Algolia API 사용
            encoded_query = urllib.parse.quote(title[:100])
            url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&tags=story&hitsPerPage=3"
            
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
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
            
        except Exception as exc:
            print(f"전문가 의견 검색 중 오류: {exc}")
            return []
    
    def _search_related_articles(self, title: str) -> list[WebResource]:
        """관련 기술 문서 및 튜토리얼을 검색한다."""
        try:
            # 특정 사이트에서 검색 (Medium, Dev.to 등)
            sites = ["site:medium.com", "site:dev.to", "site:stackoverflow.com"]
            results: list[WebResource] = []
            
            for site in sites[:2]:  # 최대 2개 사이트
                query = f"{title[:50]} {site}"
                site_results = self._search_web(query)
                results.extend(site_results[:1])  # 각 사이트에서 1개씩
            
            return results
            
        except Exception as exc:
            print(f"관련 기사 검색 중 오류: {exc}")
            return []


def extract_article_content(url: str) -> str:
    """주어진 URL에서 기사 본문을 추출한다 (간단한 버전)."""
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        
        with urllib.request.urlopen(request, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
        
        # 간단한 텍스트 추출 (HTML 태그 제거)
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        return text[:5000]  # 최대 5000자
        
    except Exception as exc:
        print(f"기사 본문 추출 중 오류: {exc}")
        return ""


# 사용 예시
if __name__ == "__main__":
    researcher = WebResearcher(max_search_results=5)
    result = researcher.research(
        title="OpenAI GPT-4 Turbo 출시",
        summary="OpenAI가 새로운 GPT-4 Turbo 모델을 발표했습니다.",
        url="https://news.hada.io/topic?id=12345"
    )
    
    print("웹 검색 결과:")
    for res in result.web_results:
        print(f"  - {res.title[:80]} ({res.url})")
    
    print("\n전문가 의견:")
    for op in result.expert_opinions:
        print(f"  - {op['title']} (댓글: {op['comments']}, 포인트: {op['points']})")


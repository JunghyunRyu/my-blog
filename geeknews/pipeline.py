"""GeekNews QA 블로그 자동화를 위한 메인 파이프라인 스크립트.

이 스크립트는 다음 단계를 수행합니다.
1. GeekNews RSS 피드에서 최신 항목을 수집한다.
2. 중복 여부를 판단하여 아직 게시하지 않은 항목만 선별한다.
3. QA 지향 AI 분석(또는 규칙 기반 백업 로직)을 수행한다.
4. 블로그(Jekyll) 포스트 마크다운을 생성하여 `_posts` 디렉터리에 저장한다.

환경 변수
----------
OPENAI_API_KEY
    설정되어 있으면 OpenAI Chat Completions API를 호출하여 QA 콘텐츠를 생성합니다.
OPENAI_MODEL (선택)
    기본값은 ``gpt-4o-mini`` 입니다. 다른 모델을 사용하려면 환경 변수를 지정하세요.

사용 예시
--------
```
python automation/geeknews_pipeline.py --max-posts 3
```
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import textwrap
import typing as t
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

try:  # pragma: no cover - 런타임에서만 필요
    from .qa_generator import QAContentGenerator, QAResult
    from .content_filter import ContentFilter, ContentMetrics
    from .web_researcher import WebResearcher, ResearchResult
except ImportError:  # pragma: no cover - 스크립트 직접 실행 대비
    from geeknews.qa_generator import QAContentGenerator, QAResult
    from geeknews.content_filter import ContentFilter, ContentMetrics
    from geeknews.web_researcher import WebResearcher, ResearchResult


DEFAULT_FEED_URL = "https://feeds.feedburner.com/geeknews-feed"
STATE_DIR = Path("data")
STATE_FILE = STATE_DIR / "geeknews_state.json"
POSTS_DIR = Path("_posts")
DEFAULT_MAX_POSTS = 10
DEFAULT_MIN_VOTES = 10
DEFAULT_ENABLE_WEB_RESEARCH = True
DEFAULT_ENABLE_SCRAPING = False  # GeekNews 스크래핑 비활성화 (키워드 기반 필터링 사용)


class FeedItem(t.TypedDict):
    guid: str
    title: str
    link: str
    summary: str
    published_at: str


def fetch_feed(url: str = DEFAULT_FEED_URL) -> list[FeedItem]:
    """RSS 또는 Atom 피드를 가져와서 FeedItem 목록을 반환한다."""
    try:
        with urllib.request.urlopen(url) as response:
            raw = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"RSS 피드에 접근할 수 없습니다: {exc}") from exc

    root = ET.fromstring(raw)
    
    # Atom 피드인지 RSS 피드인지 확인
    if root.tag.endswith("}feed") or root.tag == "feed":
        # Atom 피드 처리
        return _parse_atom_feed(root)
    else:
        # RSS 피드 처리
        return _parse_rss_feed(root)


def _parse_rss_feed(root: ET.Element) -> list[FeedItem]:
    """RSS 2.0 피드를 파싱한다."""
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS 피드에 channel 요소가 없습니다.")

    items: list[FeedItem] = []
    for item in channel.findall("item"):
        guid = _get_first_text(item, "guid") or _get_first_text(item, "link")
        title = _get_first_text(item, "title")
        link = _get_first_text(item, "link")
        summary = _get_first_text(item, "description")
        published = _get_first_text(item, "pubDate")

        if not guid or not title or not link:
            # 필수 필드가 없으면 스킵
            continue

        items.append(
            FeedItem(
                guid=guid.strip(),
                title=_normalize_whitespace(title),
                link=link.strip(),
                summary=_normalize_whitespace(summary or ""),
                published_at=published.strip() if published else "",
            )
        )
    return items


def _parse_atom_feed(root: ET.Element) -> list[FeedItem]:
    """Atom 피드를 파싱한다."""
    # Atom 네임스페이스
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    items: list[FeedItem] = []
    for entry in root.findall("atom:entry", ns):
        # id (guid 역할)
        guid = _get_first_text_ns(entry, "atom:id", ns)
        
        # title
        title = _get_first_text_ns(entry, "atom:title", ns)
        
        # link (alternate 타입 우선)
        link = _get_atom_link(entry, ns)
        
        # summary 또는 content
        summary = _get_first_text_ns(entry, "atom:summary", ns) or _get_first_text_ns(entry, "atom:content", ns)
        
        # published 또는 updated
        published = _get_first_text_ns(entry, "atom:published", ns) or _get_first_text_ns(entry, "atom:updated", ns)
        
        if not guid or not title or not link:
            # 필수 필드가 없으면 스킵
            continue
        
        items.append(
            FeedItem(
                guid=guid.strip(),
                title=_normalize_whitespace(title),
                link=link.strip(),
                summary=_normalize_whitespace(summary or ""),
                published_at=published.strip() if published else "",
            )
        )
    return items


def _get_atom_link(entry: ET.Element, ns: dict[str, str]) -> str | None:
    """Atom entry에서 link를 추출한다. alternate 타입을 우선으로 찾는다."""
    # alternate 타입 링크 찾기
    for link_elem in entry.findall("atom:link", ns):
        if link_elem.get("rel") == "alternate" or link_elem.get("rel") is None:
            href = link_elem.get("href")
            if href:
                return href
    
    # 첫 번째 링크 반환
    link_elem = entry.find("atom:link", ns)
    if link_elem is not None:
        return link_elem.get("href")
    
    return None


def _get_first_text_ns(parent: ET.Element, tag: str, ns: dict[str, str]) -> str | None:
    """네임스페이스를 고려하여 첫 번째 텍스트를 가져온다."""
    element = parent.find(tag, ns)
    if element is None or element.text is None:
        return None
    return element.text


def _get_first_text(parent: ET.Element, tag: str) -> str | None:
    element = parent.find(tag)
    if element is None or element.text is None:
        return None
    return element.text


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def load_state(path: Path = STATE_FILE) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return set(data.get("processed", []))


def save_state(processed: set[str], path: Path = STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"processed": sorted(processed)}
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def select_new_items(items: list[FeedItem], processed: set[str]) -> list[FeedItem]:
    return [item for item in items if item["guid"] not in processed]


def ensure_posts_dir(path: Path = POSTS_DIR) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_post(
    item: FeedItem, 
    qa_result: QAResult, 
    metrics: ContentMetrics | None = None,
    *, 
    timezone: dt.tzinfo | None = None
) -> Path:
    ensure_posts_dir()
    published_dt = parse_pubdate(item.get("published_at"))
    if published_dt is None:
        published_dt = dt.datetime.now(timezone or dt.timezone.utc)
    elif timezone is not None:
        published_dt = published_dt.astimezone(timezone)

    # 별점 계산
    stars = metrics.get_star_rating() if metrics else "⭐⭐⭐"
    
    # 제목에 별점 추가
    title_with_priority = f"{item['title']} {stars}"
    
    # 타겟 카테고리 결정 (AI 분석 우선, 그 다음 metrics 기반)
    if qa_result and qa_result.technical_level == "practical":
        target_category = "qa-engineer"
    elif metrics and metrics.target_category:
        target_category = metrics.target_category
    else:
        target_category = "learning"
    
    # 카테고리 이름 변환
    category_name = "QA Engineer" if target_category == "qa-engineer" else "Learning"
    
    slug = slugify(item["title"])
    filename = f"{published_dt:%Y-%m-%d}-{slug}.md"
    
    # 타겟 카테고리별 디렉토리에 저장
    target_dir = POSTS_DIR / target_category
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename

    # 카테고리 및 태그 결정 (GeekNews 제거, 메인 카테고리만 사용)
    categories = [category_name]
    tags = []
    
    if metrics and metrics.categories:
        # AI, QA, DevOps 등의 세부 태그만 추가
        tags.extend([cat for cat in metrics.categories if cat not in ["GeekNews", "Technology"]])
    
    # 중복 제거
    tags = list(dict.fromkeys(tags))

    # priority 필드 값
    priority_score = int(metrics.priority_score) if metrics else 50
    
    front_matter = textwrap.dedent(
        f"""\
        ---
        layout: post
        title: "{title_with_priority}"
        date: {published_dt:%Y-%m-%d %H:%M:%S %z}
        categories: {categories}
        tags: {tags}
        priority: {priority_score}
        summary: "{qa_result.summary.strip()}"
        original_url: "{item['link']}"
        ---
        """
    ).strip()

    content_lines = [front_matter, "", "## 요약", "", qa_result.summary.strip() or "(요약 준비 중)", ""]

    # QA Engineer 인사이트
    if qa_result.qa_engineer_insights:
        content_lines.extend(["## QA Engineer가 알아야 할 핵심 내용", ""])
        for insight in qa_result.qa_engineer_insights:
            content_lines.append(f"- {insight}")
        content_lines.append("")

    # 실무 적용 가이드
    if qa_result.practical_guide:
        content_lines.extend(["## 실무 적용 가이드", ""])
        for i, guide in enumerate(qa_result.practical_guide, 1):
            title = guide.get("title", f"가이드 {i}")
            description = guide.get("description", "")
            content_lines.append(f"### {i}. {title}")
            content_lines.append("")
            content_lines.append(description)
            if guide.get("steps"):
                content_lines.append("")
                content_lines.append("**실행 단계:**")
                steps = guide.get("steps", "")
                if isinstance(steps, str):
                    for step in steps.split(","):
                        content_lines.append(f"- {step.strip()}")
                else:
                    for step in steps:
                        content_lines.append(f"- {step}")
            content_lines.append("")

    # 학습 로드맵
    if qa_result.learning_roadmap:
        content_lines.extend(["## 학습 로드맵", ""])
        for roadmap in qa_result.learning_roadmap:
            phase = roadmap.get("phase", "학습 단계")
            skills = roadmap.get("skills", [])
            resources = roadmap.get("resources", [])
            
            content_lines.append(f"### {phase}")
            content_lines.append("")
            
            if skills:
                content_lines.append("**배워야 할 기술:**")
                for skill in skills:
                    content_lines.append(f"- {skill}")
                content_lines.append("")
            
            if resources:
                content_lines.append("**추천 학습 자료:**")
                for resource in resources:
                    content_lines.append(f"- {resource}")
                content_lines.append("")

    # 전문가 의견
    if qa_result.expert_opinions:
        content_lines.extend(["## 전문가 의견", ""])
        for expert in qa_result.expert_opinions:
            perspective = expert.get("perspective", "전문가")
            opinion = expert.get("opinion", "")
            content_lines.append(f"### {perspective} 관점")
            content_lines.append("")
            content_lines.append(f"> {opinion}")
            content_lines.append("")

    # 주요 Q&A
    if qa_result.qa_pairs:
        content_lines.extend(["## 주요 Q&A", ""])
        for pair in qa_result.qa_pairs:
            question = pair.get("question", "질문")
            answer = pair.get("answer", "답변 준비 중입니다.")
            content_lines.append(f"**Q:** {question}")
            content_lines.append("")
            content_lines.append(f"**A:** {answer}")
            content_lines.append("")
    else:
        content_lines.extend(["## 주요 Q&A", "", "(추가 분석 대기 중)", ""])

    # Follow-up 제안
    if qa_result.follow_ups:
        content_lines.extend(["## Follow-up 제안", ""])
        for idea in qa_result.follow_ups:
            content_lines.append(f"- {idea}")
        content_lines.append("")

    # 참고 자료
    if qa_result.resources:
        content_lines.extend(["## 참고 자료", ""])
        for resource in qa_result.resources:
            label = resource.get("label") or resource.get("url") or "관련 링크"
            url = resource.get("url")
            resource_type = resource.get("type", "")
            
            if url:
                if resource_type:
                    content_lines.append(f"- [{label}]({url}) ({resource_type})")
                else:
                    content_lines.append(f"- [{label}]({url})")
            else:
                content_lines.append(f"- {label}")
        content_lines.append("")

    content = "\n".join(line.rstrip() for line in content_lines).strip() + "\n"

    with filepath.open("w", encoding="utf-8") as fp:
        fp.write(content)

    return filepath


def parse_pubdate(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        except ValueError:
            return None


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = []
    for char in ascii_str.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "geeknews"


def run_pipeline(
    max_posts: int, 
    feed_url: str, 
    timezone: dt.tzinfo | None,
    enable_web_research: bool = DEFAULT_ENABLE_WEB_RESEARCH,
    enable_scraping: bool = DEFAULT_ENABLE_SCRAPING,
    min_votes: int = DEFAULT_MIN_VOTES
) -> list[Path]:
    print("=" * 80)
    print("GeekNews QA 전문가급 자동화 파이프라인 시작")
    print("=" * 80)
    
    # 1. RSS 피드 수집
    print("\n[1단계] RSS 피드 수집 중...")
    items = fetch_feed(feed_url)
    print(f"  → 총 {len(items)}개 항목 수집 완료")
    
    # 2. 중복 필터링
    print("\n[2단계] 중복 항목 필터링 중...")
    processed = load_state()
    new_items = select_new_items(items, processed)
    print(f"  → {len(new_items)}개의 신규 항목 발견")
    
    if not new_items:
        print("\n[OK] 새로운 GeekNews 항목이 없습니다.")
        return []
    
    # 3. 콘텐츠 필터링 및 우선순위 결정
    print("\n[3단계] AI/트렌드 필터링 및 우선순위 결정 중...")
    content_filter = ContentFilter(
        min_votes=min_votes, 
        enable_scraping=enable_scraping
    )
    
    # 디버깅: 모든 항목의 점수 확인
    print(f"\n  [분석] 전체 {len(new_items)}개 항목 분석 결과:")
    all_analyzed = []
    for item in new_items:
        metrics = content_filter.analyze(item)
        all_analyzed.append((item, metrics))
        title_preview = item['title'][:50] + ("..." if len(item['title']) > 50 else "")
        print(f"\n    제목: {title_preview}")
        print(f"    점수: {metrics.priority_score:.1f}점 (통과 기준: 20점)")
        print(f"    - AI 관련: {metrics.is_ai_related} (+30점)")
        print(f"    - 트렌드: {metrics.is_trending} (+20점)")
        print(f"    - QA 관련: {'QA' in metrics.categories} (+20점)")
        print(f"    - 카테고리: {', '.join(metrics.categories)}")
        status = "[통과]" if content_filter.should_process(metrics) else "[제외]"
        print(f"    -> {status}")
    
    filtered_items = content_filter.filter_and_sort(new_items, max_items=max_posts)
    print(f"\n  -> {len(filtered_items)}개 항목 선별 완료")
    
    if filtered_items:
        print("\n  [선별 완료] 우선순위 순:")
        for i, (item, metrics) in enumerate(filtered_items[:5], 1):  # 상위 5개만 출력
            print(f"    {i}. {item['title'][:60]}... (우선순위: {metrics.priority_score:.1f})")
            print(f"       AI: {metrics.is_ai_related}, 트렌드: {metrics.is_trending}, 카테고리: {', '.join(metrics.categories)}")
    else:
        print("\n  [주의] 필터링 조건을 만족하는 항목이 없습니다.")
        print("     -> AI, 트렌드, QA 관련 키워드가 없는 항목들입니다.")
        return []
    
    # 4. 웹 연구 및 QA 콘텐츠 생성
    print("\n[4단계] 웹 연구 및 전문가급 QA 콘텐츠 생성 중...")
    
    web_researcher = WebResearcher(
        max_search_results=5,
        enable_expert_search=enable_web_research
    ) if enable_web_research else None
    
    generator = QAContentGenerator()
    created_files: list[Path] = []
    
    for i, (item, metrics) in enumerate(filtered_items, 1):
        print(f"\n  [{i}/{len(filtered_items)}] 처리 중: {item['title']}")
        
        # 웹 연구 수행
        research_data = None
        if web_researcher:
            print(f"    → 웹 연구 수행 중...")
            try:
                research_data = web_researcher.research(
                    item["title"], 
                    item.get("summary", ""), 
                    item["link"]
                )
                print(f"       웹 검색 결과: {len(research_data.web_results)}개")
                print(f"       전문가 의견: {len(research_data.expert_opinions)}개")
            except Exception as exc:
                print(f"       웹 연구 실패: {exc}")
        
        # QA 콘텐츠 생성
        print(f"    → AI 기반 QA 콘텐츠 생성 중...")
        try:
            qa_result = generator.generate(item, research_data=research_data)
            print(f"       생성 완료 (인사이트: {len(qa_result.qa_engineer_insights)}개)")
        except Exception as exc:
            print(f"       생성 실패: {exc}")
            continue
        
        # 포스트 작성
        print(f"    → 블로그 포스트 작성 중...")
        try:
            filepath = write_post(item, qa_result, metrics=metrics, timezone=timezone)
            print(f"       [OK] 생성 완료: {filepath.name}")
            created_files.append(filepath)
            processed.add(item["guid"])
        except Exception as exc:
            print(f"       포스트 작성 실패: {exc}")
            continue
    
    # 5. 상태 저장
    print("\n[5단계] 처리 상태 저장 중...")
    save_state(processed)
    print(f"  → 상태 저장 완료")
    
    # 요약 출력
    print("\n" + "=" * 80)
    print("파이프라인 실행 완료")
    print("=" * 80)
    print(f"총 생성된 포스트: {len(created_files)}개")
    
    if created_files:
        print("\n생성된 포스트 목록:")
        for path in created_files:
            print(f"  [OK] {path}")
    
    print("=" * 80)
    
    return created_files


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GeekNews QA 전문가급 자동화 포스트 생성",
        epilog="예시: python -m automation.geeknews_pipeline --max-posts 10"
    )
    parser.add_argument(
        "--max-posts", 
        type=int, 
        default=DEFAULT_MAX_POSTS, 
        help=f"한 번에 생성할 최대 포스트 수 (기본값: {DEFAULT_MAX_POSTS})"
    )
    parser.add_argument(
        "--feed-url", 
        type=str, 
        default=DEFAULT_FEED_URL, 
        help="대상 RSS 피드 URL"
    )
    parser.add_argument(
        "--timezone", 
        type=str, 
        default="Asia/Seoul", 
        help="게시 시간대 (IANA Olson 형식)"
    )
    parser.add_argument(
        "--min-votes", 
        type=int, 
        default=DEFAULT_MIN_VOTES, 
        help=f"최소 투표수 필터링 (기본값: {DEFAULT_MIN_VOTES})"
    )
    parser.add_argument(
        "--no-web-research", 
        action="store_true", 
        help="웹 연구 비활성화 (속도 개선)"
    )
    parser.add_argument(
        "--disable-scraping", 
        action="store_true", 
        help="GeekNews 웹 스크래핑 비활성화 (속도 개선, 투표수 0으로 처리)"
    )
    return parser.parse_args(argv)


def resolve_timezone(name: str | None) -> dt.tzinfo | None:
    if not name:
        return None
    try:
        from zoneinfo import ZoneInfo
    except ImportError:  # pragma: no cover - Python <3.9
        return None

    try:
        return ZoneInfo(name)
    except Exception:
        print(f"경고: 알 수 없는 타임존 '{name}'. UTC를 사용합니다.")
        return dt.timezone.utc


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timezone = resolve_timezone(args.timezone)
    
    try:
        created = run_pipeline(
            max_posts=args.max_posts,
            feed_url=args.feed_url,
            timezone=timezone,
            enable_web_research=not args.no_web_research,
            enable_scraping=not args.disable_scraping,
            min_votes=args.min_votes
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n[오류] 파이프라인 실행 중 오류: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

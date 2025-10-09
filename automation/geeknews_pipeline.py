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
except ImportError:  # pragma: no cover - 스크립트 직접 실행 대비
    from qa_generator import QAContentGenerator, QAResult


DEFAULT_FEED_URL = "https://feeds.feedburner.com/geeknews-feed"
STATE_DIR = Path("data")
STATE_FILE = STATE_DIR / "geeknews_state.json"
POSTS_DIR = Path("_posts")
DEFAULT_MAX_POSTS = 3


class FeedItem(t.TypedDict):
    guid: str
    title: str
    link: str
    summary: str
    published_at: str


def fetch_feed(url: str = DEFAULT_FEED_URL) -> list[FeedItem]:
    """RSS/Atom 피드를 가져와서 FeedItem 목록을 반환한다."""
    try:
        with urllib.request.urlopen(url) as response:
            raw = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"RSS 피드에 접근할 수 없습니다: {exc}") from exc

    root = ET.fromstring(raw)
    root_tag = _strip_namespace(root.tag).lower()

    if root_tag == "rss":
        return _parse_rss_items(root)
    if root_tag == "feed":
        return _parse_atom_entries(root)

    raise RuntimeError("지원하지 않는 피드 형식입니다. RSS/Atom 피드를 사용하세요.")


def _parse_rss_items(root: ET.Element) -> list[FeedItem]:
    channel: ET.Element | None = None
    for child in root:
        if _strip_namespace(child.tag).lower() == "channel":
            channel = child
            break
    if channel is None:
        raise RuntimeError("RSS 피드에서 channel 요소를 찾을 수 없습니다.")

    items: list[FeedItem] = []
    for item in channel:
        if _strip_namespace(item.tag).lower() != "item":
            continue
        guid = _find_text(item, "guid") or _find_text(item, "link")
        title = _find_text(item, "title")
        link = _find_text(item, "link")
        summary = _find_text(item, "description") or _find_text(item, "content")
        published = _find_text(item, "pubdate") or _find_text(item, "published")

        if not guid or not title or not link:
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


def _parse_atom_entries(root: ET.Element) -> list[FeedItem]:
    items: list[FeedItem] = []
    for entry in root:
        if _strip_namespace(entry.tag).lower() != "entry":
            continue

        guid = _find_text(entry, "id")
        title = _find_text(entry, "title")
        link = _find_link(entry)
        summary = _find_text(entry, "summary") or _find_text(entry, "content")
        published = _find_text(entry, "published") or _find_text(entry, "updated")

        if not title:
            continue
        if not guid:
            guid = link or title
        if not link:
            link = guid

        items.append(
            FeedItem(
                guid=guid.strip(),
                title=_normalize_whitespace(title),
                link=link.strip(),
                summary=_normalize_whitespace(summary or ""),
                published_at=published.strip() if published else "",
            )
        )
    if not items:
        raise RuntimeError("Atom 피드에서 entry 요소를 찾을 수 없습니다.")
    return items


def _find_text(parent: ET.Element, tag: str) -> str | None:
    for child in parent:
        if _strip_namespace(child.tag).lower() != tag.lower():
            continue
        text = child.text or ""
        return text
    return None


def _find_link(parent: ET.Element) -> str | None:
    for child in parent:
        if _strip_namespace(child.tag).lower() != "link":
            continue
        href = child.attrib.get("href")
        if href and child.attrib.get("rel", "alternate") in {"alternate", ""}:
            return href
        if child.text:
            return child.text
    return None


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


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


def write_post(item: FeedItem, qa_result: QAResult, *, timezone: dt.tzinfo | None = None) -> Path:
    ensure_posts_dir()
    published_dt = parse_pubdate(item.get("published_at"))
    if published_dt is None:
        published_dt = dt.datetime.now(timezone or dt.timezone.utc)
    elif timezone is not None:
        published_dt = published_dt.astimezone(timezone)

    slug = slugify(item["title"])
    filename = f"{published_dt:%Y-%m-%d}-{slug}.md"
    filepath = POSTS_DIR / filename

    front_matter = textwrap.dedent(
        f"""\
        ---
        layout: post
        title: "{item['title']}"
        date: {published_dt:%Y-%m-%d %H:%M:%S %z}
        categories: [GeekNews, QA]
        tags: [GeekNews, QA]
        summary: "{qa_result.summary.strip()}"
        original_url: "{item['link']}"
        ---
        """
    ).strip()

    content_lines = [front_matter, "", "## 요약", "", qa_result.summary.strip() or "(요약 준비 중)", ""]

    if qa_result.qa_pairs:
        content_lines.extend(["## 주요 Q&A", ""])
        for pair in qa_result.qa_pairs:
            question = pair.get("question", "질문")
            answer = pair.get("answer", "답변 준비 중입니다.")
            content_lines.append(f"- **Q:** {question}")
            content_lines.append(f"  **A:** {answer}")
            content_lines.append("")
    else:
        content_lines.extend(["## 주요 Q&A", "", "(추가 분석 대기 중)", ""])

    if qa_result.follow_ups:
        content_lines.extend(["## Follow-up 제안", ""])
        for idea in qa_result.follow_ups:
            content_lines.append(f"- {idea}")
        content_lines.append("")

    if qa_result.resources:
        content_lines.extend(["## 참고 자료", ""])
        for resource in qa_result.resources:
            label = resource.get("label") or resource.get("url") or "관련 링크"
            url = resource.get("url")
            if url:
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


def run_pipeline(max_posts: int, feed_url: str, timezone: dt.tzinfo | None) -> list[Path]:
    items = fetch_feed(feed_url)
    processed = load_state()
    new_items = select_new_items(items, processed)

    if not new_items:
        print("새로운 GeekNews 항목이 없습니다.")
        return []

    generator = QAContentGenerator()
    created_files: list[Path] = []

    for item in new_items[:max_posts]:
        print(f"처리 중: {item['title']}")
        qa_result = generator.generate(item)
        filepath = write_post(item, qa_result, timezone=timezone)
        print(f"생성된 포스트: {filepath}")
        created_files.append(filepath)
        processed.add(item["guid"])

    save_state(processed)
    return created_files


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GeekNews QA 포스트 자동 생성")
    parser.add_argument("--max-posts", type=int, default=DEFAULT_MAX_POSTS, help="한 번에 생성할 최대 포스트 수")
    parser.add_argument("--feed-url", type=str, default=DEFAULT_FEED_URL, help="대상 RSS 피드 URL")
    parser.add_argument("--timezone", type=str, default="Asia/Seoul", help="게시 시간대 (IANA Olson 형식)")
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
        created = run_pipeline(args.max_posts, args.feed_url, timezone)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"파이프라인 실행 중 오류: {exc}")
        return 1

    if created:
        print("생성 완료:")
        for path in created:
            print(f"- {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

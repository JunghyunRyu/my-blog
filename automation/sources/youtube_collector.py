"""YouTube 키워드 기반 수집기.

YouTube Data API v3를 사용해 최신 동영상을 키워드로 검색하고,
자막을 가져와 요약 대상으로 사용할 텍스트를 구성한다.
"""
from __future__ import annotations

import datetime as dt
import time
import typing as t
from dataclasses import dataclass

try:
    from googleapiclient.discovery import build  # type: ignore
    GOOGLE_API_AVAILABLE = True
except Exception:
    GOOGLE_API_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    TRANSCRIPT_AVAILABLE = True
except Exception:
    TRANSCRIPT_AVAILABLE = False


@dataclass
class YouTubeItem:
    video_id: str
    title: str
    description: str
    published_at: str
    channel_title: str
    thumbnail_url: str


def _now_utc_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _days_ago_iso(days: int) -> str:
    return (dt.datetime.utcnow() - dt.timedelta(days=days)).replace(microsecond=0).isoformat() + "Z"


def _safe_get_transcript(video_id: str, languages: list[str] | None = None) -> str:
    if not TRANSCRIPT_AVAILABLE:
        return ""
    languages = languages or ["ko", "en"]
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # 우선 한국어, 다음 영어
        for lang in languages:
            if transcript_list.find_transcript([lang]):
                tr = transcript_list.find_transcript([lang])
                chunks = tr.fetch()
                return " ".join(chunk.get("text", "") for chunk in chunks)
        # 자동 생성 자막도 시도
        tr = transcript_list.find_generated_transcript(languages)
        chunks = tr.fetch()
        return " ".join(chunk.get("text", "") for chunk in chunks)
    except Exception:
        return ""


def _build_service(api_key: str):
    return build("youtube", "v3", developerKey=api_key)


def collect(
    *,
    api_key: str,
    keywords: str,
    max_results: int = 10,
    region_code: str = "KR",
    published_after_days: int = 7,
) -> list[dict[str, t.Any]]:
    """YouTube에서 키워드 기반으로 최신 영상을 수집해 표준 FeedItem 형태로 반환.

    Returns list of dicts with keys compatible to FeedItem: guid, title, link, summary, published_at
    and extras: thumbnail, video_url, source.
    """
    if not GOOGLE_API_AVAILABLE:
        raise RuntimeError("google-api-python-client이 필요합니다. 'pip install google-api-python-client'를 설치하세요.")

    service = _build_service(api_key)

    published_after = _days_ago_iso(published_after_days)

    # 검색어: 쉼표 구분 문자열을 공백으로 합쳐 검색 정확도 개선
    query = " ".join([k.strip() for k in keywords.split(",") if k.strip()])

    search_resp = service.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results,
        regionCode=region_code,
        publishedAfter=published_after,
        order="date",
        safeSearch="none",
    ).execute()

    video_ids: list[str] = [item["id"]["videoId"] for item in search_resp.get("items", []) if item.get("id", {}).get("videoId")]
    if not video_ids:
        return []

    details_resp = service.videos().list(
        part="snippet,contentDetails,statistics",
        id=",".join(video_ids),
        maxResults=max_results,
    ).execute()

    results: list[dict[str, t.Any]] = []
    for v in details_resp.get("items", []):
        vid = v.get("id", "")
        sn = v.get("snippet", {})
        title = sn.get("title", "(제목 없음)")
        description = sn.get("description", "")
        published_at = sn.get("publishedAt", _now_utc_iso())
        thumbnails = (sn.get("thumbnails", {}) or {})
        thumb = thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}
        thumb_url = thumb.get("url", "")

        transcript_text = _safe_get_transcript(vid)
        base_text = transcript_text if transcript_text.strip() else description
        summary_seed = base_text[:6000]  # 요약 입력을 위한 원문 시드 텍스트(길이 제한)

        link = f"https://www.youtube.com/watch?v={vid}"
        guid = f"youtube:{vid}"

        item = {
            "guid": guid,
            "title": title,
            "link": link,
            "summary": summary_seed,
            "published_at": published_at,
            # extras
            "thumbnail": thumb_url,
            "video_url": link,
            "source": "youtube",
        }
        results.append(item)

        # 간단한 쿼터 보호: 요청 사이 짧은 대기
        time.sleep(0.05)

    return results


def collect_from_channel(
    *,
    api_key: str,
    channel_id: str,
    max_results: int = 10,
    published_after_days: int = 7,
) -> list[dict[str, t.Any]]:
    """특정 YouTube 채널에서 최신 영상을 수집해 표준 FeedItem 형태로 반환.
    
    Args:
        api_key: YouTube Data API v3 키
        channel_id: YouTube 채널 ID (UC로 시작)
        max_results: 최대 결과 수
        published_after_days: 최근 N일 이내 동영상만 수집
    
    Returns:
        list of dicts with keys compatible to FeedItem: guid, title, link, summary, published_at
        and extras: thumbnail, video_url, source, channel_name.
    """
    if not GOOGLE_API_AVAILABLE:
        raise RuntimeError("google-api-python-client이 필요합니다. 'pip install google-api-python-client'를 설치하세요.")
    
    service = _build_service(api_key)
    
    published_after = _days_ago_iso(published_after_days)
    
    # 채널의 최신 동영상 검색
    search_resp = service.search().list(
        part="snippet",
        channelId=channel_id,
        type="video",
        maxResults=max_results,
        publishedAfter=published_after,
        order="date",
    ).execute()
    
    video_ids: list[str] = [item["id"]["videoId"] for item in search_resp.get("items", []) if item.get("id", {}).get("videoId")]
    if not video_ids:
        return []
    
    # 동영상 상세 정보 조회
    details_resp = service.videos().list(
        part="snippet,contentDetails,statistics",
        id=",".join(video_ids),
        maxResults=max_results,
    ).execute()
    
    results: list[dict[str, t.Any]] = []
    for v in details_resp.get("items", []):
        vid = v.get("id", "")
        sn = v.get("snippet", {})
        title = sn.get("title", "(제목 없음)")
        description = sn.get("description", "")
        published_at = sn.get("publishedAt", _now_utc_iso())
        channel_title = sn.get("channelTitle", "")
        thumbnails = (sn.get("thumbnails", {}) or {})
        thumb = thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}
        thumb_url = thumb.get("url", "")
        
        # 자막 추출 시도
        transcript_text = _safe_get_transcript(vid)
        base_text = transcript_text if transcript_text.strip() else description
        summary_seed = base_text[:6000]  # 요약 입력을 위한 원문 시드 텍스트
        
        link = f"https://www.youtube.com/watch?v={vid}"
        guid = f"youtube:{vid}"
        
        item = {
            "guid": guid,
            "title": title,
            "link": link,
            "summary": summary_seed,
            "published_at": published_at,
            # extras
            "thumbnail": thumb_url,
            "video_url": link,
            "source": "youtube",
            "channel_name": channel_title,
        }
        results.append(item)
        
        # API 쿼터 보호
        time.sleep(0.05)
    
    return results


def collect_from_watchlist(
    *,
    api_key: str,
    video_ids: list[str],
) -> list[dict[str, t.Any]]:
    """워치리스트의 특정 비디오 ID들을 수집해 표준 FeedItem 형태로 반환.
    
    Args:
        api_key: YouTube Data API v3 키
        video_ids: YouTube 비디오 ID 리스트 (11자리 문자열)
    
    Returns:
        list of dicts with keys compatible to FeedItem: guid, title, link, summary, published_at
        and extras: thumbnail, video_url, source, channel_name.
    """
    if not GOOGLE_API_AVAILABLE:
        raise RuntimeError("google-api-python-client이 필요합니다. 'pip install google-api-python-client'를 설치하세요.")
    
    if not video_ids:
        return []
    
    service = _build_service(api_key)
    
    # 비디오 상세 정보 조회 (최대 50개씩 요청 가능)
    # 워치리스트는 보통 소수이므로 한 번에 요청
    results: list[dict[str, t.Any]] = []
    
    # API 제한을 고려하여 50개씩 분할
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        
        try:
            details_resp = service.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(batch_ids),
            ).execute()
            
            for v in details_resp.get("items", []):
                vid = v.get("id", "")
                sn = v.get("snippet", {})
                title = sn.get("title", "(제목 없음)")
                description = sn.get("description", "")
                published_at = sn.get("publishedAt", _now_utc_iso())
                channel_title = sn.get("channelTitle", "")
                thumbnails = (sn.get("thumbnails", {}) or {})
                thumb = thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}
                thumb_url = thumb.get("url", "")
                
                # 자막 추출 시도
                transcript_text = _safe_get_transcript(vid)
                base_text = transcript_text if transcript_text.strip() else description
                summary_seed = base_text[:6000]  # 요약 입력을 위한 원문 시드 텍스트
                
                link = f"https://www.youtube.com/watch?v={vid}"
                guid = f"youtube:{vid}"
                
                item = {
                    "guid": guid,
                    "title": title,
                    "link": link,
                    "summary": summary_seed,
                    "published_at": published_at,
                    # extras
                    "thumbnail": thumb_url,
                    "video_url": link,
                    "source": "youtube_watchlist",
                    "channel_name": channel_title,
                }
                results.append(item)
                
                # API 쿼터 보호
                time.sleep(0.05)
        
        except Exception as e:
            print(f"⚠️ 워치리스트 배치 수집 실패 ({i}-{i+len(batch_ids)}): {e}")
            continue
    
    return results



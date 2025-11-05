"""Gmail 뉴스레터 수집기 (label 기반).

Gmail API를 통해 특정 라벨(기본: newsletter)의 최근 메일을 조회하고,
본문 텍스트와 포함된 링크를 추출하여 표준 FeedItem 형태로 반환한다.
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import re
import typing as t

from bs4 import BeautifulSoup  # type: ignore

try:
    from google.auth.transport.requests import Request  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    GOOGLE_GMAIL_AVAILABLE = True
except Exception:
    GOOGLE_GMAIL_AVAILABLE = False


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_credentials(client_secret_file: str, token_file: str) -> "Credentials":
    creds = None
    if GOOGLE_GMAIL_AVAILABLE is False:
        raise RuntimeError("Gmail API 라이브러리가 필요합니다. requirements.txt를 설치하세요.")
    try:
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    except Exception:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            # 로컬 서버 방식 인증 (최초 1회 필요)
            creds = flow.run_local_server(port=0)
        # 토큰 저장
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def _decode_body(message: dict) -> str:
    """메시지에서 본문 추출(Base64url decoding + HTML -> text)."""
    payload = message.get("payload", {})
    data = None

    def _walk_parts(parts: list[dict]) -> str:
        for part in parts:
            mime = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")
            if data and ("html" in mime or "plain" in mime):
                try:
                    raw = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
                    return raw
                except Exception:
                    continue
            if part.get("parts"):
                inner = _walk_parts(part["parts"])
                if inner:
                    return inner
        return ""

    parts = payload.get("parts") or []
    if parts:
        data = _walk_parts(parts)
    else:
        body = payload.get("body", {})
        if body.get("data"):
            try:
                data = base64.urlsafe_b64decode(body["data"].encode("utf-8")).decode("utf-8", errors="replace")
            except Exception:
                data = None

    if not data:
        return ""

    # HTML -> 텍스트
    soup = BeautifulSoup(data, "html.parser")
    text = soup.get_text(" ")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _extract_first_link(message: dict) -> str:
    payload = message.get("payload", {})
    # HTML 파트에서 첫 a[href] 추출
    def _walk(parts: list[dict]) -> str:
        for part in parts:
            mime = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")
            if data and "html" in mime:
                try:
                    raw = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
                    soup = BeautifulSoup(raw, "html.parser")
                    a = soup.find("a", href=True)
                    if a and a.get("href"):
                        return a.get("href")
                except Exception:
                    pass
            if part.get("parts"):
                inner = _walk(part["parts"])
                if inner:
                    return inner
        return ""

    parts = payload.get("parts") or []
    if parts:
        link = _walk(parts)
        if link:
            return link
    return ""


def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def collect(
    *,
    client_secret_file: str,
    token_file: str,
    label: str = "newsletter",
    max_results: int = 20,
) -> list[dict[str, t.Any]]:
    """Gmail 라벨 기반으로 최근 메일을 수집해 FeedItem 형태로 반환."""
    creds = _get_credentials(client_secret_file, token_file)
    service = build("gmail", "v1", credentials=creds)

    # 라벨명으로 필터링
    resp = service.users().messages().list(userId="me", labelIds=[label], maxResults=max_results).execute()
    messages = resp.get("messages", [])
    if not messages:
        return []

    results: list[dict[str, t.Any]] = []
    for m in messages:
        mid = m.get("id")
        if not mid:
            continue
        msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        subject = _get_header(headers, "Subject") or "(제목 없음)"
        date_str = _get_header(headers, "Date")
        try:
            # RFC2822 → ISO
            dt_obj = dt.datetime.strptime(date_str[:31], "%a, %d %b %Y %H:%M:%S %z") if date_str else dt.datetime.now(dt.timezone.utc)
            published_at = dt_obj.astimezone(dt.timezone.utc).isoformat()
        except Exception:
            published_at = dt.datetime.now(dt.timezone.utc).isoformat()

        body_text = _decode_body(msg)
        first_link = _extract_first_link(msg)
        link = first_link or f"mailto:{mid}"

        item = {
            "guid": f"gmail:{mid}",
            "title": subject,
            "link": link,
            "summary": body_text[:6000],
            "published_at": published_at,
            "source": "gmail",
        }
        results.append(item)

    return results



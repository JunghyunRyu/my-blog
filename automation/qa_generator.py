"""GeekNews 기사를 QA 관점의 블로그 포스트로 변환하는 모듈."""
from __future__ import annotations

import json
import os
import textwrap
import typing as t
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class QAResult:
    """QA 분석 결과를 표현하는 데이터 구조."""

    summary: str = ""
    qa_pairs: list[dict[str, str]] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    resources: list[dict[str, str]] = field(default_factory=list)


class QAProvider(t.Protocol):
    """QAResult를 생성하는 프로바이더 인터페이스."""

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        ...


class QAContentGenerator:
    """AI 기반 또는 규칙 기반으로 QA 결과를 생성한다."""

    def __init__(self, provider: QAProvider | None = None):
        self._provider = provider or self._build_provider()

    def _build_provider(self) -> QAProvider:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return OpenAIProvider(api_key=api_key, model=model)
        return RuleBasedProvider()

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        try:
            return self._provider.generate(item)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"AI 생성 중 오류 발생: {exc}. 규칙 기반 백업을 사용합니다.")
            return RuleBasedProvider().generate(item)


class OpenAIProvider:
    """OpenAI Chat Completions API를 호출하여 QAResult를 생성한다."""

    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        prompt = self._build_prompt(item)
        payload = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 GeekNews 기사를 분석하여 QA 엔지니어가 활용할 수 있는 질문과 답변을 정리하는 보조자입니다. "
                        "가능하면 사실 기반으로 답변하고, 추측은 명시하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - 네트워크 의존
            raise RuntimeError(f"OpenAI API 요청 실패: {exc.read().decode('utf-8', 'ignore')}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - 네트워크 의존
            raise RuntimeError(f"OpenAI API에 연결할 수 없습니다: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - 외부 응답 의존
            raise RuntimeError(f"예상치 못한 응답 형식: {data}") from exc

        return self._parse_response(content, item)

    def _build_prompt(self, item: t.Mapping[str, t.Any]) -> str:
        description = item.get("summary") or ""
        return textwrap.dedent(
            f"""
            아래는 GeekNews 기사 정보입니다. QA 관점에서 분석한 결과를 JSON으로 반환하세요.

            기사 정보:
            - 제목: {item.get('title')}
            - 링크: {item.get('link')}
            - 요약: {description}
            - 발행일: {item.get('published_at', '')}

            JSON 스키마:
            {{
              "summary": "3-4문장 요약",
              "qa_pairs": [
                {{"question": "질문", "answer": "답변"}}
              ],
              "follow_ups": ["추가 조사 아이디어"],
              "resources": [{{"label": "출처명", "url": "https://..."}}]
            }}

            반드시 JSON만 반환하세요.
            """
        ).strip()

    def _parse_response(self, content: str, item: t.Mapping[str, t.Any]) -> QAResult:
        json_text = _extract_json(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - 외부 응답 의존
            raise RuntimeError(f"JSON 파싱 실패: {exc}\n본문:\n{content}") from exc

        summary = t.cast(str, payload.get("summary") or (item.get("summary") or ""))
        qa_pairs = _ensure_qa_pairs(payload.get("qa_pairs"))
        follow_ups = _ensure_str_list(payload.get("follow_ups"))
        resources = _ensure_resource_list(payload.get("resources"))
        if not resources and item.get("link"):
            resources = [{"label": "GeekNews 원문", "url": t.cast(str, item.get("link"))}]

        return QAResult(summary=summary, qa_pairs=qa_pairs, follow_ups=follow_ups, resources=resources)


class RuleBasedProvider:
    """외부 API가 없을 때 사용되는 간단한 규칙 기반 생성기."""

    DEFAULT_QUESTIONS = (
        "이 소식이 다루는 핵심 변화는 무엇인가요?",
        "QA 담당자가 확인해야 할 위험 요소는 무엇인가요?",
        "팀에 바로 적용할 수 있는 행동 항목은 무엇인가요?",
    )

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        description = (item.get("summary") or "").strip()
        title = item.get("title") or "GeekNews 소식"
        link = item.get("link")

        summary = self._build_summary(title, description)
        qa_pairs = self._build_qa_pairs(title, summary)
        follow_ups = self._build_follow_ups(title)
        resources: list[dict[str, str]] = []
        if link:
            resources.append({"label": "GeekNews 원문", "url": t.cast(str, link)})

        return QAResult(summary=summary, qa_pairs=qa_pairs, follow_ups=follow_ups, resources=resources)

    def _build_summary(self, title: str, description: str) -> str:
        if description:
            return description[:400]
        return f"'{title}' 기사에서 소개한 내용을 추후 업데이트할 예정입니다."

    def _build_qa_pairs(self, title: str, summary: str) -> list[dict[str, str]]:
        qa_pairs: list[dict[str, str]] = []
        for question in self.DEFAULT_QUESTIONS:
            answer = self._generate_answer(question, title, summary)
            qa_pairs.append({"question": question, "answer": answer})
        return qa_pairs

    def _generate_answer(self, question: str, title: str, summary: str) -> str:
        base = summary or f"'{title}' 관련 정보가 추가 수집 중입니다."
        if "핵심" in question:
            return f"기사 '{title}'는 다음을 강조합니다: {base}"
        if "위험" in question:
            return (
                f"QA 관점에서 '{title}'는 새 기능/변화를 검증할 때 잠재적인 결함 영역을 면밀히 확인해야 합니다. "
                f"기사에서 언급된 내용({base})을 기준으로 테스트 시나리오를 준비하세요."
            )
        if "행동" in question:
            return (
                f"팀은 기사 '{title}'에서 소개된 내용을 바탕으로 회고를 진행하고, QA 체크리스트를 업데이트하세요. "
                "테스트 데이터, 모니터링 지표, 사용자 피드백 경로를 정비하면 도움이 됩니다."
            )
        return base

    def _build_follow_ups(self, title: str) -> list[str]:
        return [
            f"'{title}' 관련 추가 공식 발표나 블로그를 모니터링하세요.",
            "도입 시 필요한 테스트 자동화 시나리오를 정의하세요.",
        ]


def _extract_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        lines = [line for line in content.splitlines() if not line.startswith("```")]
        return "\n".join(lines)
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise RuntimeError("응답에서 JSON을 찾을 수 없습니다.")
    return content[start : end + 1]


def _ensure_qa_pairs(value: t.Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if question or answer:
                result.append({"question": question, "answer": answer})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            question, answer = item
            result.append({"question": str(question), "answer": str(answer)})
    return result


def _ensure_resource_list(value: t.Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            label = str(item.get("label", "")).strip() or "관련 자료"
            url = str(item.get("url", "")).strip()
            entry: dict[str, str] = {"label": label}
            if url:
                entry["url"] = url
            result.append(entry)
        elif isinstance(item, (list, tuple)) and item:
            label = str(item[0])
            url = str(item[1]) if len(item) > 1 else ""
            entry: dict[str, str] = {"label": label}
            if url:
                entry["url"] = url
            result.append(entry)
    return result


def _ensure_str_list(value: t.Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, bytes):
            result.append(item.decode("utf-8", "ignore"))
    return result

"""GeekNews 기사를 QA 관점의 블로그 포스트로 변환하는 모듈."""
from __future__ import annotations

import json
import os
import re
import textwrap
import typing as t
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html import unescape

from automation.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QAResult:
    """QA 분석 결과를 표현하는 데이터 구조."""

    summary: str = ""
    qa_pairs: list[dict[str, str]] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    resources: list[dict[str, str]] = field(default_factory=list)
    # 추가 필드
    qa_engineer_insights: list[str] = field(default_factory=list)
    practical_guide: list[dict[str, str]] = field(default_factory=list)
    learning_roadmap: list[dict[str, t.Any]] = field(default_factory=list)
    expert_opinions: list[dict[str, str]] = field(default_factory=list)
    technical_level: str = "advanced"  # "advanced" 또는 "practical"
    blog_category: str = "Learning"  # "Learning", "QA Engineer", "Daily Life"


class QAProvider(t.Protocol):
    """QAResult를 생성하는 프로바이더 인터페이스."""

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        ...


class QAContentGenerator:
    """AI 기반 또는 규칙 기반으로 QA 결과를 생성한다."""

    def __init__(self, provider: QAProvider | None = None, research_data: t.Any = None, enable_mcp: bool | None = None):
        self._provider = provider or self._build_provider()
        self.research_data = research_data
        
        # MCP 클라이언트 초기화
        self.mcp_client = None
        if enable_mcp is None:
            enable_mcp = os.getenv("ENABLE_MCP", "true").lower() in ("true", "1", "yes")
        
        if enable_mcp:
            try:
                from .mcp_client import create_mcp_client
                self.mcp_client = create_mcp_client()
                if self.mcp_client:
                    logger.info("MCP Sequential Thinking 활성화됨")
            except ImportError:
                logger.warning("MCP 클라이언트 모듈을 찾을 수 없습니다.")
            except Exception as exc:
                logger.warning(f"MCP 클라이언트 초기화 실패: {exc}")

    def _build_provider(self) -> QAProvider:
        # Claude API 키가 있으면 Claude 사용 (기술 분석에 강점)
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
            return ClaudeProvider(api_key=claude_key, model=model)
        
        # OpenAI API 키가 있으면 OpenAI 사용
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return OpenAIProvider(api_key=api_key, model=model)
        
        return RuleBasedProvider()

    def generate(self, item: t.Mapping[str, t.Any], research_data: t.Any = None) -> QAResult:
        try:
            # MCP 사전 분석 수행
            mcp_insights = None
            if self.mcp_client:
                mcp_insights = self._run_mcp_analysis(item)
            
            # research_data와 MCP 인사이트를 provider에 전달
            if hasattr(self._provider, 'set_research_data'):
                if research_data:
                    self._provider.set_research_data(research_data)
                if mcp_insights and hasattr(self._provider, 'set_mcp_insights'):
                    self._provider.set_mcp_insights(mcp_insights)
            
            return self._provider.generate(item)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"AI 생성 중 오류 발생: {exc}. 규칙 기반 백업을 사용합니다.", exc_info=True)
            return RuleBasedProvider().generate(item)
    
    def _run_mcp_analysis(self, item: t.Mapping[str, t.Any]) -> dict[str, t.Any] | None:
        """MCP Sequential Thinking으로 기사를 사전 분석한다."""
        if not self.mcp_client:
            return None
        
        try:
            title = item.get("title", "")
            summary = item.get("summary", "")
            
            problem = f"""
            다음 기술 기사를 QA Engineer 관점에서 분석하세요:
            
            제목: {title}
            요약: {summary}
            
            다음 관점에서 단계적으로 분석해주세요:
            1. 이 기술이 QA 업무에 미치는 영향
            2. 실무 적용 시 고려사항
            3. 학습이 필요한 핵심 기술
            4. 잠재적 위험 요소
            """
            
            depth = int(os.getenv("MCP_THINKING_DEPTH", "3"))
            result = self.mcp_client.think(problem.strip(), depth=depth)
            
            if result.get("error"):
                logger.warning(f"MCP 분석 실패: {result.get('error')}")
                return None
            
            logger.info(f"MCP 분석 완료 (사고 단계: {len(result.get('thoughts', []))})")
            return result
            
        except Exception as exc:
            logger.warning(f"MCP 분석 중 오류: {exc}", exc_info=True)
            return None


class OpenAIProvider:
    """OpenAI Chat Completions API를 호출하여 QAResult를 생성한다."""

    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.research_data: t.Any = None
        self.mcp_insights: dict[str, t.Any] | None = None
    
    def set_research_data(self, research_data: t.Any) -> None:
        """웹 연구 데이터를 설정한다."""
        self.research_data = research_data
    
    def set_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> None:
        """MCP Sequential Thinking 분석 결과를 설정한다."""
        self.mcp_insights = mcp_insights

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        prompt = self._build_prompt(item)
        
        # 일부 모델은 temperature를 지원하지 않음 (예: gpt-5-mini)
        # 모델 이름에 따라 temperature 파라미터 조건부 추가
        payload: dict[str, t.Any] = {
            "model": self.model,
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
        
        # temperature를 지원하는 모델에만 추가
        # gpt-5-mini 같은 일부 모델은 temperature를 지원하지 않음
        if not self.model.startswith("gpt-5"):
            payload["temperature"] = 0.3

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        max_retries = 3
        retry_delay = 2  # 초
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_response(content, item)
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8") if exc.fp else ""
                if exc.code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        import time
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"OpenAI API rate limit. {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                elif exc.code >= 500:  # Server error
                    if attempt < max_retries - 1:
                        import time
                        logger.warning(f"OpenAI API 서버 오류 (HTTP {exc.code}). 재시도 중... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise RuntimeError(f"OpenAI API 호출 실패 (HTTP {exc.code}): {exc.reason}\n{error_body}") from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"OpenAI API 연결 실패. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"OpenAI API 연결 실패: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"OpenAI API 응답 JSON 파싱 실패: {exc}") from exc
            except KeyError as exc:
                raise RuntimeError(f"OpenAI API 응답 형식 오류: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"OpenAI API 호출 중 예상치 못한 오류: {exc}") from exc
        
        # 모든 재시도 실패
        raise RuntimeError(f"OpenAI API 호출이 {max_retries}번 모두 실패했습니다.")

    def _build_prompt(self, item: t.Mapping[str, t.Any]) -> str:
        description = item.get("summary") or ""
        title = item.get("title", "")
        
        # 웹 연구 데이터 포함
        research_context = ""
        if self.research_data:
            research_context = self._format_research_data(self.research_data)
        
        # MCP 인사이트 포함
        mcp_context = ""
        if self.mcp_insights:
            mcp_context = self._format_mcp_insights(self.mcp_insights)
        
        # 향상된 프롬프트 시스템 사용 여부 확인
        use_enhanced_prompts = os.getenv("USE_ENHANCED_PROMPTS", "false").lower() in ("true", "1", "yes")
        
        if use_enhanced_prompts:
            try:
                from automation.enhanced_prompts import EnhancedPromptTemplates
                
                # 컨텍스트 준비
                context = {
                    "title": title,
                    "summary": description,
                    "link": item.get("link", ""),
                    "published_at": item.get("published_at", ""),
                    "additional_data": {
                        "research_context": research_context,
                        "mcp_context": mcp_context
                    }
                }
                
                # 페르소나 및 분석 유형 결정
                persona = os.getenv("PROMPT_PERSONA", "senior_qa_architect")
                analysis_type = os.getenv("PROMPT_ANALYSIS_TYPE", "deep_technical")
                format_type = os.getenv("PROMPT_FORMAT_TYPE", "case_study")
                level = os.getenv("PROMPT_LEVEL", "intermediate")
                
                # 향상된 프롬프트 생성
                enhanced_prompt = EnhancedPromptTemplates.combine_prompts(
                    persona=persona,
                    analysis_type=analysis_type,
                    format_type=format_type,
                    level=level,
                    context=context
                )
                
                # 기존 JSON 스키마 추가
                return enhanced_prompt + "\n\n" + self._get_base_json_schema()
            except ImportError:
                logger.warning("향상된 프롬프트 시스템을 사용할 수 없습니다. 기본 프롬프트를 사용합니다.")
        
        # 기본 프롬프트 사용
        return textwrap.dedent(
            f"""
            당신은 15년 경력의 시니어 QA 아키텍트입니다. 아래 GeekNews 기사를 분석하여 
            QA Engineer들이 실무에 즉시 활용할 수 있는 심층적이고 전문적인 콘텐츠를 생성하세요.

            **중요: 반드시 QA 엔지니어 관점에서 작성하세요.**
            - 기술의 내부 구현보다는 테스트 전략, 품질 검증 방법, 실무 적용에 집중하세요
            - 모든 기술/도구를 QA 관점에서 어떻게 활용할 수 있는지 구체적으로 설명하세요
            - 2025년 최신 AI 트렌드를 반드시 포함하세요 (LLM 기반 테스트, Agentic AI, AI QA 도구 등)

            기사 정보:
            - 제목: {title}
            - 링크: {item.get('link')}
            - 요약: {description}
            - 발행일: {item.get('published_at', '')}

            {research_context}

            {mcp_context}

            다음 JSON 스키마에 맞춰 응답하세요:
            {{
              "blog_category": "이 기사가 속할 블로그 카테고리를 정확히 하나만 선택하세요. 반드시 다음 3개 중 하나만 선택해야 합니다: 'Learning' (기술 트렌드, 새로운 도구/프레임워크, 개발 방법론, AI/ML 기술, 프로그래밍 언어 등), 'QA Engineer' (테스트 자동화, QA 도구, 품질 보증 프로세스, 테스팅 전략, QA 업무 관련), 'Daily Life' (일상적인 주제, 여행, 요리, 라이프스타일, 취미, 쇼핑 등). 절대로 복수의 카테고리나 다른 값을 입력하지 마세요.",
              
              "technical_level": "이 기사의 기술적 난이도를 판단합니다. 'advanced' (신기술 발표, 연구 논문, 복잡한 아키텍처, 고급 엔지니어 대상) 또는 'practical' (QA 도구 사용법, 테스팅 베스트 프랙티스, 실무 가이드)",
              
              "summary": "3-5문장의 긴 문단으로 기사의 핵심 내용을 요약합니다. 주요 기술 트렌드, 혁신적 변화, 비즈니스 및 기술적 영향을 중심으로 작성하되, 가능한 경우 관련 출처나 통계를 자연스럽게 인용하세요(예: 'tricentis.com에 따르면...'). 이 기술이 왜 중요한지, 어떤 기업들이 도입하고 있는지, 그리고 결과적으로 업계에 어떤 변화를 가져오는지를 포함하여 서술하세요.",
              
              "qa_engineer_insights": [
                "첫 번째 인사이트: QA 관점에서 이 기술/뉴스가 왜 중요한지를 3-5문장의 긴 문단으로 설명합니다. 현대 소프트웨어 개발 환경의 복잡도와 속도 증가 배경을 언급하고, 이 기술이 QA 엔지니어에게 필수적인 도구가 되는 이유를 구체적으로 서술하세요. **반드시 이 기술을 테스트할 때 필요한 전략, 성능/품질 측정 방법, CI/CD 파이프라인 통합 방법을 포함하세요.** 업계 통계나 설문 결과(예: '2025년 80%의 팀이 도입 예정')를 인용하여 신뢰도를 높이고, 경쟁력 관점에서의 중요성도 강조하세요.",
                "두 번째 인사이트: 테스트 전략과 품질 보증 방식에 미치는 영향을 3-5문장의 긴 문단으로 상세히 분석합니다. 기존 QA 프로세스의 어떤 부분(테스트 계획, 실행, 분석 등)이 어떻게 변화하는지 구체적으로 설명하세요. **2025년 최신 AI 트렌드를 반드시 포함하세요: LLM 기반 테스트 자동화(예: GitHub Copilot, Cursor, Codeium), Agentic AI 기술의 QA 분야 적용, AI 모델 품질 검증 방법(LLM 평가, 벤치마크) 등.** 새로운 접근법이나 개념(예: QAOps, shift-left, 데이터 중심 접근 등)을 포함하고, AI가 리스크 식별과 우선순위 재조정에 어떻게 활용되는지 기술하세요.",
                "세 번째 인사이트: QA 업무 수행 시 주의해야 할 사항과 고려 사항을 3-5문장의 긴 문단으로 기술합니다. **실제 테스트 시나리오 예시와 코드 스니펫을 포함하세요.** AI 결과물을 맹신하지 말고 반드시 검증해야 하는 이유, 학습 데이터의 한계로 인한 오작동 가능성, 인간 전문가의 검토와 승인 절차의 중요성을 언급하세요. 보안 및 개인정보 보호 측면의 위험(예: 테스트 데이터의 클라우드 유출 위험)도 구체적으로 다루고, 'AI는 도구일 뿐'이라는 메시지를 전달하세요."
              ],
              
              "practical_guide": [
                {{
                  "title": "테스트 자동화 개선",
                  "description": "이 기술을 활용하여 테스트 자동화를 고도화하는 구체적인 방안을 2-3문장으로 제시합니다. **반드시 2025년 최신 AI 도구를 언급하세요: GitHub Copilot, Cursor, Codeium, Test.ai, Applitools 등.** 예를 들어 생성형 AI나 신기술을 활용한 테스트 케이스 자동 생성, 자연어 요구사항 입력을 통한 테스트 생성, 자가 치유 기능을 활용한 UI 변경 대응, 유지보수 부담 경감 등을 언급하세요.",
                  "steps": [
                    "1. AI 테스트 도구 파일럿 도입: 팀의 작은 모듈에 **2025년 최신 AI 기반 테스트 케이스 생성 도구(예: GitHub Copilot, Cursor, Codeium, Test.ai)**를 시범 적용하여 효과를 검증합니다.",
                    "2. AI 생성 테스트 검토: AI가 생성한 테스트 케이스를 QA 엔지니어가 검토하여 누락된 시나리오나 오류가 있는 케이스를 걸러냅니다. **LLM 기반 테스트 생성의 한계와 검증 방법을 문서화하세요.**",
                    "3. CI/CD 통합: 검증된 AI 생성 테스트 케이스를 CI/CD 파이프라인에 포함시켜 코드 변경 시 자동 실행되도록 구성합니다. **GitHub Actions, GitLab CI, Jenkins 등 구체적인 플랫폼 예시를 포함하세요.**",
                    "4. 결과 모니터링 및 피드백: AI가 제안한 테스트의 실행 결과를 모니터링하고, 오탐/미탐 사례를 수집하여 모델 개선이나 추가 테스트 케이스 작성에 반영합니다. **Agentic AI 기술을 활용한 자동 개선 프로세스를 고려하세요.**",
                    "5. 팀 가이드 마련: AI 도구 활용에 대한 모범 사례와 한계를 문서화하여 팀원들과 공유하고, AI 결과에 대한 리뷰 절차를 공식화합니다. **2025년 AI QA 트렌드를 반영한 가이드를 작성하세요.**"
                  ]
                }},
                {{
                  "title": "품질 검증 프로세스",
                  "description": "AI를 품질 검증 프로세스 전반에 통합하기 위한 종합적인 가이드를 5-7문장의 긴 문단으로 작성합니다. 테스트 기획 단계에서 AI 분석을 통해 위험도가 높은 기능을 선별하고 자원을 집중하는 전략, 테스트 실행 단계에서 AI가 로그와 결과를 분석하여 결함의 근본 원인을 파악하거나 방대한 테스트 결과를 시각화하는 방법, 배포 후 운영 단계에서 AIOps와 연계된 AI 모니터링을 통해 실제 사용자 환경의 이상 징후를 조기 탐지하는 방안을 포함하세요. 요구사항 분석부터 운영 모니터링까지 QA 프로세스 각 단계에 AI를 내재화하여 전체 테스트 사이클의 효율성과 선제적 품질 관리 능력을 향상시키는 방법을 제시하세요. 이 항목에는 steps 필드를 포함하지 마세요."
                }}
              ],
              
              "learning_roadmap": [
                {{
                  "phase": "즉시 학습 (1-2주)",
                  "skills": [
                    "기사에서 언급된 구체적인 기술/도구/플랫폼의 기본 개념과 작동 원리 학습",
                    "기사에서 다루는 기술과 직접 관련된 간단한 도구나 플랫폼 사용 경험"
                  ]
                }},
                {{
                  "phase": "단기 학습 (1-3개월)",
                  "skills": [
                    "기사에서 다루는 기술과 관련된 프로그래밍 언어나 기술 스택 학습",
                    "기사에서 언급된 기술을 QA 관점에서 활용하기 위한 테스트 자동화 프레임워크 및 도구 심화 학습"
                  ]
                }},
                {{
                  "phase": "장기 학습 (3-6개월)",
                  "skills": [
                    "기사에서 다루는 기술을 실제 QA 업무에 고급 수준으로 적용하고 커스터마이징하는 능력 개발",
                    "기사에서 다루는 기술과 관련된 품질 거버넌스, 윤리, 보안, 규정 준수 측면 학습"
                  ]
                }}
              ],
              
              "expert_opinions": [
                {{
                  "perspective": "시니어 QA 엔지니어",
                  "opinion": "시니어 QA 엔지니어 관점에서 이 기술의 실무 적용 경험과 조언을 4-6문장의 긴 문단으로 제공합니다. 기술 도입으로 품질 보증의 기본 원리는 변하지 않으며, 이 기술을 '똑똑한 보조자'로 보는 시각을 제시하세요. 반복적인 테스트 처리를 기술이 담당함으로써 초기 설계 단계의 품질 이슈 검토나 창의적인 테스트 시나리오 구상에 시간을 투입할 수 있게 된 점을 강조하고, 기술 결과물에 대한 최종 책임은 여전히 QA 팀에 있으므로 놓친 부분을 찾아내고 판단을 보완하는 역할의 중요성을 언급하세요."
                }},
                {{
                  "perspective": "테스트 자동화 전문가",
                  "opinion": "테스트 자동화 전문가 입장에서 이 기술이 자동화 분야에 가져온 변화를 4-6문장의 긴 문단으로 설명합니다. 과거 스크립트 작성과 유지보수에 많은 수작업 시간이 들었으나, 이제 기술이 코드 생성부터 자가 치유까지 도와주어 자동화 범위가 크게 넓어진 점을 강조하세요. 특히 시각적 테스트나 동적 요소 식별 기술이 그동안 자동화가 어려웠던 영역을 크게 개선했음을 언급하고, 이러한 도구들을 기존 프레임워크와 프로세스에 잘 통합하여 신뢰성 높은 자동화 파이프라인을 구축하는 것의 중요성을 제시하세요."
                }},
                {{
                  "perspective": "DevOps/SRE",
                  "opinion": "운영 및 안정성 관점에서 이 기술의 장단점을 4-6문장의 긴 문단으로 논의합니다. 기술 도입으로 개발, 테스트, 운영 간 경계가 더욱 모호해지는 추세를 설명하고, 테스트 단계에서 결함을 잘 잡아내면 운영 환경 장애를 줄일 수 있으며 운영 중 로그 분석으로 이상 징후를 실시간 감지할 수 있게 된 장점을 언급하세요. 동시에 파이프라인에 새로운 복잡성이 생기는 점도 다루고, 기술로부터 나오는 알림과 지표를 기존 모니터링 시스템과 통합하며 오탐지나 경미한 이슈가 과도한 알람으로 이어지지 않도록 튜닝하는 노력의 필요성을 강조하세요."
                }}
              ],
              
              "qa_pairs": [
                {{
                  "question": "이 기술의 핵심 변화는 무엇인가요?",
                  "answer": "핵심 변화를 5-7문장의 긴 문단으로 명확히 정의하고, 과거와 현재를 비교하여 설명합니다. QA 업무에 이 기술이 깊숙이 도입되면서 테스트 케이스 설계, 유지보수, 결함 탐지와 같은 작업들을 지능적으로 자동화할 수 있게 된 점을 강조하세요. 과거 수작업으로 작성하던 시나리오를 이제 요구사항 분석을 통해 대량으로 생성하고, 실행 중 오류를 자가 치유로 자동 수정할 수 있음을 언급하고, 그 결과 훨씬 짧은 시간에 더 폭넓은 테스트를 수행하여 품질을 확보할 수 있으며 QA 인력은 전략 수립과 창의적 품질 향상에 집중할 수 있게 되었다는 점을 서술하세요. 가능하면 업계 사례나 통계(예: 출처 URL 인용)를 포함하여 설득력을 높이세요."
                }},
                {{
                  "question": "QA 담당자가 확인해야 할 위험 요소는?",
                  "answer": "여러 위험 요소를 5-7문장의 긴 문단으로 구체적으로 나열하고 설명합니다. 첫째, 기술의 한계로 인해 잘못된 결과가 나올 수 있으며, 학습된 데이터에만 기반하므로 특정 도메인 지식이 필요한 경우 부정확한 테스트 케이스를 제안하거나 중요한 시나리오를 놓칠 수 있습니다. 둘째, 기술에 대한 과도한 의존은 위험하므로 제공된 답이 맥락에 맞는지 판단하고 교차 검증해야 하며, 이를 소홀히 하면 잘못된 결론을 얻을 수 있습니다. 셋째, 기술 도구 사용 시 데이터 보안과 프라이버시 문제도 고려해야 하며, 외부 클라우드 서비스에 제품의 민감한 테스트 데이터를 업로드하면 정보 유출 위험이 있습니다. 넷째, 기술의 결정은 이유가 불투명할 때가 많으므로(설명 가능성 낮음) 결과를 맹신하기보다 왜 그런 결과가 나왔는지 추가 확인하는 태도가 필요합니다. 가능하면 각 위험에 대한 출처를 인용하세요."
                }},
                {{
                  "question": "팀에 바로 적용할 수 있는 행동 항목은?",
                  "answer": "즉시 실행 가능한 구체적인 액션 아이템을 4-6문장의 긴 문단으로 제공합니다. 우선 작은 범위에서라도 기술 활용을 시작해보는 것이 좋으며, 현재 프로젝트의 일부 모듈에 관련 도구를 도입해 파일럿으로 운영하고 그 결과를 팀과 공유하세요. 또한 팀원들의 이해도를 높이기 위해 짧은 워크숍이나 스터디를 개최하여 간단한 실습(예: 도구로 테스트 시나리오 만들어보기)을 해볼 수 있습니다. 즉각 실행할 수 있는 조치로, 기술이 제안한 결과에 대해 항상 2인 이상의 리뷰를 거치는 절차를 추가하여 실수를 걸러내고 팀의 신뢰도를 유지할 수 있도록 하세요."
                }}
              ],
              
              "follow_ups": [
                "이 기술과 관련하여 추가로 조사하면 좋을 구체적인 주제나 키워드를 제시합니다 (예: '생성형 AI를 활용한 테스트 데이터 및 시나리오 생성 기법 연구')",
                "관련 기술 동향이나 신기술 모니터링 항목을 구체적으로 제안합니다 (예: 'Agentic AI (자율 에이전트) 기술의 QA 분야 적용 가능성 모니터링')"
              ]
            }}

            작성 지침 및 예시:
            
            **중요: QA 엔지니어 관점 강화**
            - 기술의 내부 구현이나 이론보다는 **테스트 전략, 품질 검증 방법, 실무 적용**에 집중하세요
            - 모든 기술/도구를 **QA 엔지니어가 어떻게 활용할 수 있는지** 구체적으로 설명하세요
            - **2025년 최신 AI 트렌드를 반드시 포함하세요**: LLM 기반 테스트 자동화, Agentic AI, AI QA 도구(GitHub Copilot, Cursor, Codeium 등)
            
            1. **출처 인용 스타일**: 가능한 경우 관련 출처나 URL을 텍스트 내에 자연스럽게 괄호 형식으로 인용하세요.
               - 좋은 예: "한 설문에 따르면 2025년에 80%의 소프트웨어 팀이 AI를 활용할 것이라고 전망됩니다(tricentis.com)."
               - 좋은 예: "AI가 제공한 답이라도 맥락에 맞는지 판단하고 교차 검증해야 합니다(practitest.com)."
               - 여러 출처 인용 예: "tricentis.com", "qodo.ai", "practitest.com", "slexn.com" 등
            
            2. **구체성과 예시**: 추상적인 설명보다는 구체적인 수치, 예시, 시나리오를 포함하세요.
               - 좋은 예: "AI가 수초 내에 수백 개의 시나리오를 만들어내어 테스트 커버리지를 넓혀줍니다."
               - 좋은 예: "자연어로 작성된 요구사항을 입력하면 AI 기반 도구(GitHub Copilot, Cursor)가 수 초 안에 관련 테스트 케이스를 대거 생성해줍니다."
               - 좋은 예: "Playwright를 사용하여 K8s Pod 자동 정리 도구를 테스트할 때는 Pod 상태 변화를 모니터링하고, 정리 전후 리소스 사용량을 측정하는 테스트 케이스를 작성해야 합니다."
            
            3. **긴 문단 작성**: 각 섹션의 설명은 짧은 한 줄이 아니라 3-7문장의 풍부한 문단으로 작성하세요.
               - qa_engineer_insights: 각 항목당 3-5문장
               - expert_opinions: 각 항목당 4-6문장
               - qa_pairs 답변: 각 답변당 4-7문장
               - practical_guide description: 2-7문장 (항목에 따라 다름)
            
            4. **실무 적용성**: QA 엔지니어가 바로 활용할 수 있는 실용적이고 구체적인 조언을 우선시하세요.
               - 도구명 언급 (예: ChatGPT, Selenium, Playwright 등)
               - 프로세스명 언급 (예: CI/CD 통합, QAOps, shift-left 등)
               - 구체적인 단계별 액션 제시
            
            5. **균형잡힌 시각**: 장점뿐 아니라 한계와 위험 요소, 주의사항도 반드시 함께 다루세요.
               - 과도한 의존의 위험
               - 보안 및 프라이버시 문제
               - AI 결과의 검증 필요성
               - 인간 전문가의 최종 판단 중요성
            
            6. **단계별 구조**: 학습 로드맵과 실무 가이드는 명확한 단계별 구조를 유지하세요.
               - 학습 로드맵: 즉시(1-2주) → 단기(1-3개월) → 장기(3-6개월)
               - practical_guide: "테스트 자동화 개선"에는 steps 포함, "품질 검증 프로세스"에는 steps 없음
            
            7. **학습 로드맵 구체성**: 학습 로드맵은 반드시 기사 제목, 요약, 기술명을 분석하여 각 기사에 맞는 구체적인 학습 항목을 생성해야 합니다. JSON 스키마 예시는 일반적인 형식만 보여주지만, 실제 생성 시에는 기사 내용에 맞춰 구체적으로 작성해야 합니다.
               - 절대로 일반적인 내용(예: "기술의 기본 개념 이해", "머신러닝 기초 지식", "간단한 도구나 플랫폼 사용 경험")을 그대로 사용하지 마세요.
               - 기사에서 언급된 구체적인 기술명, 도구명, 서비스명, 플랫폼명을 반드시 포함하세요.
               - 각 skills 배열의 항목은 기사에서 다루는 기술/도구/플랫폼의 실제 이름을 포함한 구체적인 학습 항목이어야 합니다.
               - 예시:
                 * OpenAI 기사: "OpenAI API 기본 사용법 및 모델 이해", "ChatGPT API를 사용한 테스트 케이스 생성"
                 * Playwright 기사: "Playwright 설치 및 기본 사용법", "Playwright를 활용한 E2E 테스트 자동화"
                 * AWS 기사: "AWS EC2 인스턴스 생성 및 기본 설정", "Terraform을 사용한 인프라 코드화"
               - 각 단계별로 기사 내용에 맞는 실제 학습 가능한 구체적인 기술이나 도구를 제시하세요.
            
            8. **신뢰성과 정확성**: 추측이 필요한 경우 명시하고, 사실 기반 정보를 우선하세요.
               - 업계 통계나 설문 결과 인용
               - 실제 사례나 도구 언급
               - 불확실한 정보는 "추정됩니다", "예상됩니다" 등으로 명시
            
            9. **JSON 형식 준수**: 반드시 유효한 JSON만 반환하세요.
               - 마크다운 코드 블록(```) 사용 금지
               - 순수 JSON 객체만 출력
               - 모든 문자열은 큰따옴표로 감싸기
               - 특수문자는 적절히 이스케이프
            
            반드시 위 지침을 따라 유효한 JSON만 반환하세요.
            """
        ).strip()
    
    def _format_research_data(self, research_data: t.Any) -> str:
        """웹 연구 데이터를 프롬프트에 포함할 수 있는 형식으로 변환한다."""
        if not research_data:
            return ""
        
        context_parts = ["추가 참고 정보:"]
        
        # 웹 검색 결과
        if hasattr(research_data, 'web_results') and research_data.web_results:
            context_parts.append("\n웹 검색 결과:")
            for i, result in enumerate(research_data.web_results[:3], 1):
                context_parts.append(f"  {i}. {result.title}")
                if result.snippet:
                    context_parts.append(f"     {result.snippet[:200]}")
        
        # 전문가 의견
        if hasattr(research_data, 'expert_opinions') and research_data.expert_opinions:
            context_parts.append("\n외부 전문가 의견:")
            for opinion in research_data.expert_opinions[:2]:
                context_parts.append(f"  - {opinion.get('title', '')} (댓글: {opinion.get('comments', 0)})")
        
        return "\n".join(context_parts) if len(context_parts) > 1 else ""
    
    def _format_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> str:
        """MCP Sequential Thinking 분석 결과를 프롬프트에 포함할 수 있는 형식으로 변환한다."""
        if not mcp_insights or mcp_insights.get("error"):
            return ""
        
        context_parts = ["MCP Sequential Thinking 분석 결과:"]
        
        # 사고 과정
        thoughts = mcp_insights.get("thoughts", [])
        if thoughts:
            context_parts.append("\n분석 사고 과정:")
            for i, thought in enumerate(thoughts[:5], 1):
                context_parts.append(f"  {i}. {thought}")
        
        # 인사이트
        insights = mcp_insights.get("insights", [])
        if insights:
            context_parts.append("\n핵심 인사이트:")
            for insight in insights[:3]:
                context_parts.append(f"  - {insight}")
        
        # 결론
        conclusion = mcp_insights.get("conclusion", "")
        if conclusion:
            context_parts.append(f"\n종합 결론: {conclusion}")
        
        if len(context_parts) > 1:
            context_parts.append("\n위 MCP 분석 결과를 참고하여 더 깊이 있고 구조화된 콘텐츠를 생성하세요.")
            return "\n".join(context_parts)
        
        return ""
    
    def _get_base_json_schema(self) -> str:
        """기본 JSON 스키마 반환 (향상된 프롬프트와 함께 사용)."""
        return textwrap.dedent(
            """
            다음 JSON 스키마에 맞춰 응답하세요:
            {
              "blog_category": "Learning | QA Engineer | Daily Life",
              "technical_level": "advanced | practical",
              "summary": "3-5문장 요약",
              "qa_engineer_insights": ["인사이트 1", "인사이트 2", "인사이트 3"],
              "practical_guide": [{"title": "...", "description": "...", "steps": [...]}],
              "learning_roadmap": [{"phase": "...", "skills": [...]}],
              "expert_opinions": [{"perspective": "...", "opinion": "..."}],
              "qa_pairs": [{"question": "...", "answer": "..."}],
              "follow_ups": ["...", "..."]
            }
            
            반드시 유효한 JSON만 반환하세요.
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
        
        # 새로운 필드 파싱
        qa_engineer_insights = _ensure_str_list(payload.get("qa_engineer_insights"))
        practical_guide = _ensure_practical_guide_list(payload.get("practical_guide"))
        learning_roadmap = _ensure_learning_roadmap_list(payload.get("learning_roadmap"))
        expert_opinions = _ensure_expert_opinions_list(payload.get("expert_opinions"))
        technical_level = str(payload.get("technical_level", "advanced")).lower()
        blog_category = str(payload.get("blog_category", "Learning")).strip()
        
        # technical_level 유효성 검증
        if technical_level not in ["advanced", "practical"]:
            technical_level = "advanced"
        
        # blog_category 유효성 검증 (정확히 3개 중 하나만 허용)
        if blog_category not in ["Learning", "QA Engineer", "Daily Life"]:
            blog_category = "Learning"

        return QAResult(
            summary=summary, 
            qa_pairs=qa_pairs, 
            follow_ups=follow_ups, 
            resources=resources,
            qa_engineer_insights=qa_engineer_insights,
            practical_guide=practical_guide,
            learning_roadmap=learning_roadmap,
            expert_opinions=expert_opinions,
            technical_level=technical_level,
            blog_category=blog_category
        )


class ClaudeProvider:
    """Anthropic Claude API를 호출하여 QAResult를 생성한다."""

    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        self.api_key = api_key
        self.model = model
        self.research_data: t.Any = None
        self.mcp_insights: dict[str, t.Any] | None = None
    
    def set_research_data(self, research_data: t.Any) -> None:
        """웹 연구 데이터를 설정한다."""
        self.research_data = research_data
    
    def set_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> None:
        """MCP Sequential Thinking 분석 결과를 설정한다."""
        self.mcp_insights = mcp_insights

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        prompt = self._build_prompt(item)
        payload = {
            "model": self.model,
            "max_tokens": 8192,
            "temperature": 0.3,
            "system": (
                "당신은 15년 경력의 시니어 QA 아키텍트입니다. "
                "대규모 분산 시스템의 품질 보증 전략을 설계하고, "
                "수백 명의 엔지니어가 사용하는 테스트 인프라를 구축한 경험이 있습니다. "
                "**반드시 QA 엔지니어 관점에서 작성하세요.** "
                "기술의 내부 구현보다는 테스트 전략, 품질 검증 방법, 실무 적용에 집중하고, "
                "2025년 최신 AI 트렌드(LLM 기반 테스트, Agentic AI, AI QA 도구)를 반드시 포함하세요."
            ),
            "messages": [
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
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        max_retries = 3
        retry_delay = 2  # 초
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    content = data["content"][0]["text"]
                    return self._parse_response(content, item)
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8") if exc.fp else ""
                if exc.code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        import time
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Claude API rate limit. {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                elif exc.code >= 500:  # Server error
                    if attempt < max_retries - 1:
                        import time
                        logger.warning(f"Claude API 서버 오류 (HTTP {exc.code}). 재시도 중... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise RuntimeError(f"Claude API 호출 실패 (HTTP {exc.code}): {exc.reason}\n{error_body}") from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"Claude API 연결 실패. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Claude API 연결 실패: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Claude API 응답 JSON 파싱 실패: {exc}") from exc
            except KeyError as exc:
                raise RuntimeError(f"Claude API 응답 형식 오류: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"Claude API 호출 중 예상치 못한 오류: {exc}") from exc
        
        # 모든 재시도 실패
        raise RuntimeError(f"Claude API 호출이 {max_retries}번 모두 실패했습니다.")

    def _build_prompt(self, item: t.Mapping[str, t.Any]) -> str:
        """Claude용 프롬프트 생성 (기술적 심층 분석 중심)."""
        description = item.get("summary") or ""
        title = item.get("title", "")
        
        # 웹 연구 데이터 포함
        research_context = ""
        if self.research_data:
            research_context = self._format_research_data(self.research_data)
        
        # MCP 인사이트 포함
        mcp_context = ""
        if self.mcp_insights:
            mcp_context = self._format_mcp_insights(self.mcp_insights)
        
        return textwrap.dedent(
            f"""
            다음 기술 기사를 시니어 QA 아키텍트 관점에서 심층 분석하세요:
            
            제목: {title}
            요약: {description}
            링크: {item.get('link', '')}
            
            {research_context}
            
            {mcp_context}
            
            다음 관점에서 분석하세요:
            
            1. **아키텍처 수준 영향 분석**
               - 기존 QA 아키텍처와의 통합 방안
               - 성능 및 확장성 고려사항
               - 기술 스택 호환성 매트릭스
            
            2. **실제 구현 사례**
               - 엔터프라이즈 환경 적용 예시
               - 단계별 마이그레이션 전략
               - 실제 코드 예시와 설정 파일
            
            3. **비교 분석**
               - 경쟁 도구/기술 대비 장단점
               - 정량적 성능 비교
               - TCO(Total Cost of Ownership) 분석
            
            4. **미래 전망 (3-5년)**
               - 기술 로드맵과 발전 방향
               - 예상되는 패러다임 변화
               - 투자 가치와 위험 요소
            
            OpenAIProvider와 동일한 JSON 스키마로 응답하세요.
            """
        ).strip()
    
    def _format_research_data(self, research_data: t.Any) -> str:
        """웹 연구 데이터를 프롬프트에 포함할 수 있는 형식으로 변환한다."""
        if not research_data:
            return ""
        
        context_parts = ["추가 참고 정보:"]
        
        # 웹 검색 결과
        if hasattr(research_data, 'web_results') and research_data.web_results:
            context_parts.append("\n웹 검색 결과:")
            for i, result in enumerate(research_data.web_results[:3], 1):
                context_parts.append(f"  {i}. {result.title}")
                if result.snippet:
                    context_parts.append(f"     {result.snippet[:200]}")
        
        return "\n".join(context_parts) if len(context_parts) > 1 else ""
    
    def _format_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> str:
        """MCP Sequential Thinking 분석 결과를 프롬프트에 포함할 수 있는 형식으로 변환한다."""
        if not mcp_insights or mcp_insights.get("error"):
            return ""
        
        context_parts = ["MCP Sequential Thinking 분석 결과:"]
        
        # 사고 과정
        thoughts = mcp_insights.get("thoughts", [])
        if thoughts:
            context_parts.append("\n분석 사고 과정:")
            for i, thought in enumerate(thoughts[:5], 1):
                context_parts.append(f"  {i}. {thought}")
        
        # 인사이트
        insights = mcp_insights.get("insights", [])
        if insights:
            context_parts.append("\n핵심 인사이트:")
            for insight in insights[:3]:
                context_parts.append(f"  - {insight}")
        
        # 결론
        conclusion = mcp_insights.get("conclusion", "")
        if conclusion:
            context_parts.append(f"\n종합 결론: {conclusion}")
        
        if len(context_parts) > 1:
            context_parts.append("\n위 MCP 분석 결과를 참고하여 더 깊이 있고 구조화된 콘텐츠를 생성하세요.")
            return "\n".join(context_parts)
        
        return ""

    def _parse_response(self, content: str, item: t.Mapping[str, t.Any]) -> QAResult:
        """Claude 응답을 파싱하여 QAResult로 변환."""
        # OpenAIProvider와 동일한 파싱 로직 사용
        json_text = _extract_json(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON 파싱 실패: {exc}\n본문:\n{content}") from exc

        summary = t.cast(str, payload.get("summary") or (item.get("summary") or ""))
        qa_pairs = _ensure_qa_pairs(payload.get("qa_pairs"))
        follow_ups = _ensure_str_list(payload.get("follow_ups"))
        resources = _ensure_resource_list(payload.get("resources"))
        if not resources and item.get("link"):
            resources = [{"label": "원문", "url": t.cast(str, item.get("link"))}]
        
        # 새로운 필드 파싱
        qa_engineer_insights = _ensure_str_list(payload.get("qa_engineer_insights"))
        practical_guide = _ensure_practical_guide_list(payload.get("practical_guide"))
        learning_roadmap = _ensure_learning_roadmap_list(payload.get("learning_roadmap"))
        expert_opinions = _ensure_expert_opinions_list(payload.get("expert_opinions"))
        technical_level = str(payload.get("technical_level", "advanced")).lower()
        blog_category = str(payload.get("blog_category", "Learning")).strip()
        
        # technical_level 유효성 검증
        if technical_level not in ["advanced", "practical"]:
            technical_level = "advanced"
        
        # blog_category 유효성 검증
        if blog_category not in ["Learning", "QA Engineer", "Daily Life"]:
            blog_category = "Learning"

        return QAResult(
            summary=summary, 
            qa_pairs=qa_pairs, 
            follow_ups=follow_ups, 
            resources=resources,
            qa_engineer_insights=qa_engineer_insights,
            practical_guide=practical_guide,
            learning_roadmap=learning_roadmap,
            expert_opinions=expert_opinions,
            technical_level=technical_level,
            blog_category=blog_category
        )


class PerplexityProvider:
    """Perplexity API를 호출하여 실시간 웹 검색 기반 QAResult를 생성한다."""

    endpoint = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str, model: str = "sonar"):
        self.api_key = api_key
        self.model = model
        self.research_data: t.Any = None
        self.mcp_insights: dict[str, t.Any] | None = None
    
    def set_research_data(self, research_data: t.Any) -> None:
        """웹 연구 데이터를 설정한다."""
        self.research_data = research_data
    
    def set_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> None:
        """MCP Sequential Thinking 분석 결과를 설정한다."""
        self.mcp_insights = mcp_insights

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        prompt = self._build_prompt(item)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 최신 기술 트렌드를 분석하는 QA 전문가입니다. "
                        "실시간 웹 검색을 통해 최신 정보를 수집하고, "
                        "QA 엔지니어가 활용할 수 있는 실용적인 인사이트를 제공하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_response(content, item)
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8") if exc.fp else ""
                if exc.code == 429:
                    if attempt < max_retries - 1:
                        import time
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Perplexity API rate limit. {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                elif exc.code >= 500:
                    if attempt < max_retries - 1:
                        import time
                        logger.warning(f"Perplexity API 서버 오류 (HTTP {exc.code}). 재시도 중... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise RuntimeError(f"Perplexity API 호출 실패 (HTTP {exc.code}): {exc.reason}\n{error_body}") from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"Perplexity API 연결 실패. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Perplexity API 연결 실패: {exc}") from exc
            except (json.JSONDecodeError, KeyError) as exc:
                raise RuntimeError(f"Perplexity API 응답 파싱 실패: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"Perplexity API 호출 중 예상치 못한 오류: {exc}") from exc
        
        raise RuntimeError(f"Perplexity API 호출이 {max_retries}번 모두 실패했습니다.")

    def _build_prompt(self, item: t.Mapping[str, t.Any]) -> str:
        """Perplexity용 프롬프트 생성 (실시간 웹 검색 중심)."""
        description = item.get("summary") or ""
        title = item.get("title", "")
        
        return textwrap.dedent(
            f"""
            다음 주제에 대한 최신 정보를 실시간 웹 검색을 통해 수집하고 분석하세요:
            
            제목: {title}
            요약: {description}
            링크: {item.get('link', '')}
            
            다음 내용을 포함하여 분석하세요:
            
            1. **최근 3개월 내 관련 뉴스 및 발표**
               - 주요 기업의 도입 사례
               - 최신 버전 및 업데이트
            
            2. **실제 기업 도입 사례**
               - 성공 사례와 실패 사례
               - ROI 및 효과 측정 결과
            
            3. **경쟁 기술/도구 비교**
               - 유사 기술과의 차이점
               - 장단점 비교
            
            4. **커뮤니티 반응과 평가**
               - 개발자 커뮤니티의 평가
               - GitHub 프로젝트 트렌드
            
            5. **QA 엔지니어 관점의 실무 적용**
               - 즉시 적용 가능한 방법
               - 주의사항 및 베스트 프랙티스
            
            OpenAIProvider와 동일한 JSON 스키마로 응답하세요.
            """
        ).strip()

    def _parse_response(self, content: str, item: t.Mapping[str, t.Any]) -> QAResult:
        """Perplexity 응답을 파싱하여 QAResult로 변환."""
        json_text = _extract_json(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON 파싱 실패: {exc}\n본문:\n{content}") from exc

        summary = t.cast(str, payload.get("summary") or (item.get("summary") or ""))
        qa_pairs = _ensure_qa_pairs(payload.get("qa_pairs"))
        follow_ups = _ensure_str_list(payload.get("follow_ups"))
        resources = _ensure_resource_list(payload.get("resources"))
        if not resources and item.get("link"):
            resources = [{"label": "원문", "url": t.cast(str, item.get("link"))}]
        
        qa_engineer_insights = _ensure_str_list(payload.get("qa_engineer_insights"))
        practical_guide = _ensure_practical_guide_list(payload.get("practical_guide"))
        learning_roadmap = _ensure_learning_roadmap_list(payload.get("learning_roadmap"))
        expert_opinions = _ensure_expert_opinions_list(payload.get("expert_opinions"))
        technical_level = str(payload.get("technical_level", "advanced")).lower()
        blog_category = str(payload.get("blog_category", "Learning")).strip()
        
        if technical_level not in ["advanced", "practical"]:
            technical_level = "advanced"
        if blog_category not in ["Learning", "QA Engineer", "Daily Life"]:
            blog_category = "Learning"

        return QAResult(
            summary=summary, 
            qa_pairs=qa_pairs, 
            follow_ups=follow_ups, 
            resources=resources,
            qa_engineer_insights=qa_engineer_insights,
            practical_guide=practical_guide,
            learning_roadmap=learning_roadmap,
            expert_opinions=expert_opinions,
            technical_level=technical_level,
            blog_category=blog_category
        )


class GeminiProvider:
    """Google Gemini API를 호출하여 멀티모달 QAResult를 생성한다."""

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.research_data: t.Any = None
        self.mcp_insights: dict[str, t.Any] | None = None
    
    def set_research_data(self, research_data: t.Any) -> None:
        """웹 연구 데이터를 설정한다."""
        self.research_data = research_data
    
    def set_mcp_insights(self, mcp_insights: dict[str, t.Any]) -> None:
        """MCP Sequential Thinking 분석 결과를 설정한다."""
        self.mcp_insights = mcp_insights

    def generate(self, item: t.Mapping[str, t.Any]) -> QAResult:
        prompt = self._build_prompt(item)
        url = self.endpoint.format(model=self.model)
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
            }
        }

        full_url = f"{url}?key={self.api_key}"
        request = urllib.request.Request(
            full_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
        )

        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._parse_response(content, item)
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8") if exc.fp else ""
                if exc.code == 429:
                    if attempt < max_retries - 1:
                        import time
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Gemini API rate limit. {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                elif exc.code >= 500:
                    if attempt < max_retries - 1:
                        import time
                        logger.warning(f"Gemini API 서버 오류 (HTTP {exc.code}). 재시도 중... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise RuntimeError(f"Gemini API 호출 실패 (HTTP {exc.code}): {exc.reason}\n{error_body}") from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"Gemini API 연결 실패. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Gemini API 연결 실패: {exc}") from exc
            except (json.JSONDecodeError, KeyError) as exc:
                raise RuntimeError(f"Gemini API 응답 파싱 실패: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"Gemini API 호출 중 예상치 못한 오류: {exc}") from exc
        
        raise RuntimeError(f"Gemini API 호출이 {max_retries}번 모두 실패했습니다.")

    def _build_prompt(self, item: t.Mapping[str, t.Any]) -> str:
        """Gemini용 프롬프트 생성 (멀티모달 분석 중심)."""
        description = item.get("summary") or ""
        title = item.get("title", "")
        
        return textwrap.dedent(
            f"""
            다음 기술 기사를 멀티모달 관점에서 분석하세요:
            
            제목: {title}
            요약: {description}
            링크: {item.get('link', '')}
            
            다음을 포함하여 분석하세요:
            
            1. **시각적 자료 분석** (이미지, 차트, 다이어그램이 있다면)
               - 시각 자료에서 추출한 핵심 정보
               - 데이터 시각화 해석
            
            2. **기술적 심층 분석**
               - 코드 예시와 아키텍처 다이어그램 설명
               - 성능 메트릭 및 벤치마크
            
            3. **실무 적용 가이드**
               - 단계별 구현 방법
               - 실제 코드 스니펫
            
            4. **QA 엔지니어 관점의 인사이트**
               - 테스트 전략 수립
               - 품질 보증 방법
            
            OpenAIProvider와 동일한 JSON 스키마로 응답하세요.
            """
        ).strip()

    def _parse_response(self, content: str, item: t.Mapping[str, t.Any]) -> QAResult:
        """Gemini 응답을 파싱하여 QAResult로 변환."""
        json_text = _extract_json(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON 파싱 실패: {exc}\n본문:\n{content}") from exc

        summary = t.cast(str, payload.get("summary") or (item.get("summary") or ""))
        qa_pairs = _ensure_qa_pairs(payload.get("qa_pairs"))
        follow_ups = _ensure_str_list(payload.get("follow_ups"))
        resources = _ensure_resource_list(payload.get("resources"))
        if not resources and item.get("link"):
            resources = [{"label": "원문", "url": t.cast(str, item.get("link"))}]
        
        qa_engineer_insights = _ensure_str_list(payload.get("qa_engineer_insights"))
        practical_guide = _ensure_practical_guide_list(payload.get("practical_guide"))
        learning_roadmap = _ensure_learning_roadmap_list(payload.get("learning_roadmap"))
        expert_opinions = _ensure_expert_opinions_list(payload.get("expert_opinions"))
        technical_level = str(payload.get("technical_level", "advanced")).lower()
        blog_category = str(payload.get("blog_category", "Learning")).strip()
        
        if technical_level not in ["advanced", "practical"]:
            technical_level = "advanced"
        if blog_category not in ["Learning", "QA Engineer", "Daily Life"]:
            blog_category = "Learning"

        return QAResult(
            summary=summary, 
            qa_pairs=qa_pairs, 
            follow_ups=follow_ups, 
            resources=resources,
            qa_engineer_insights=qa_engineer_insights,
            practical_guide=practical_guide,
            learning_roadmap=learning_roadmap,
            expert_opinions=expert_opinions,
            technical_level=technical_level,
            blog_category=blog_category
        )


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
            # HTML 제거 및 마크다운 변환
            cleaned = _strip_html(description)
            return cleaned[:400]
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
    
    # 마크다운 코드 블록 제거
    if "```json" in content:
        # ```json ... ``` 형식
        start_marker = content.find("```json")
        end_marker = content.find("```", start_marker + 7)
        if end_marker != -1:
            content = content[start_marker + 7:end_marker].strip()
    elif content.startswith("```") and content.endswith("```"):
        # ``` ... ``` 형식
        lines = [line for line in content.splitlines() if not line.startswith("```")]
        content = "\n".join(lines)
    
    # JSON 객체 찾기
    start = content.find("{")
    end = content.rfind("}")
    
    if start == -1 or end == -1:
        # JSON 배열도 시도
        start = content.find("[")
        end = content.rfind("]")
        if start == -1 or end == -1:
            raise RuntimeError("응답에서 JSON을 찾을 수 없습니다.")
    
    json_text = content[start : end + 1]
    
    # trailing comma 제거 (배열/객체 마지막 쉼표)
    import re
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # 불완전한 JSON 처리 (마지막 부분이 잘린 경우)
    # 중괄호 균형 확인
    open_braces = json_text.count("{")
    close_braces = json_text.count("}")
    if open_braces > close_braces:
        json_text += "}" * (open_braces - close_braces)
    
    return json_text


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


def _ensure_practical_guide_list(value: t.Any) -> list[dict[str, str]]:
    """실무 가이드 리스트를 검증하고 반환한다."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            guide = {
                "title": str(item.get("title", "")),
                "description": str(item.get("description", "")),
            }
            if item.get("steps"):
                guide["steps"] = ", ".join([str(s) for s in item.get("steps", [])])
            result.append(guide)
    return result


def _ensure_learning_roadmap_list(value: t.Any) -> list[dict[str, t.Any]]:
    """학습 로드맵 리스트를 검증하고 반환한다."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, t.Any]] = []
    for item in value:
        if isinstance(item, dict):
            roadmap = {
                "phase": str(item.get("phase", "")),
                "skills": _ensure_str_list(item.get("skills")),
                "resources": _ensure_str_list(item.get("resources"))
            }
            result.append(roadmap)
    return result


def _ensure_expert_opinions_list(value: t.Any) -> list[dict[str, str]]:
    """전문가 의견 리스트를 검증하고 반환한다."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            opinion = {
                "perspective": str(item.get("perspective", "")),
                "opinion": str(item.get("opinion", ""))
            }
            result.append(opinion)
    return result


def _strip_html(html: str) -> str:
    """HTML 태그를 제거하고 마크다운으로 변환한다."""
    if not html:
        return ""
    
    # HTML 엔티티 디코딩
    text = unescape(html)
    
    # <strong> -> **
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    
    # <em> -> *
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
    
    # <ul><li> -> - 
    text = re.sub(r'<ul>\s*', '', text)
    text = re.sub(r'</ul>', '', text)
    text = re.sub(r'<li>(.*?)</li>', r'- \1\n', text)
    
    # <p> -> \n\n
    text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text)
    
    # 나머지 HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 연속된 공백 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

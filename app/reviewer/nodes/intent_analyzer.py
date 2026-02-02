"""
PR Intent Analyzer Node
"""
import json
from datetime import datetime

from loguru import logger

from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_intent_analysis_prompt
from app.reviewer.llm import get_llm
from app.reviewer.utils import parse_llm_json_response


async def analyze_pr_intent(state: ReviewState) -> dict:
    """
    PR의 의도를 분석하는 노드

    Args:
        state: 현재 리뷰 상태

    Returns:
        업데이트된 상태 (pr_intent, messages 추가)
    """
    logger.info("🎯 PR 의도 분석 시작...")

    pr_data = state["pr_data"]

    try:
        # LLM 초기화 (Provider에 따라 자동 선택)
        llm = get_llm(temperature=0.0)

        # 프롬프트 생성
        prompt = create_intent_analysis_prompt(pr_data)

        # LLM 호출
        response = await llm.ainvoke(prompt)
        response_text = response.content

        logger.debug(f"Intent 분석 응답: {response_text[:200]}...")

        # JSON 파싱
        try:
            pr_intent = parse_llm_json_response(response_text)

            logger.info(
                f"✅ PR 의도 분석 완료: {pr_intent.get('type', 'unknown')} - "
                f"{pr_intent.get('summary', 'N/A')[:50]}..."
            )

        except json.JSONDecodeError as e:
            # 파싱 실패 시 기본값
            pr_intent = {
                "type": "unknown",
                "summary": response_text[:200],
                "key_objectives": [],
                "complexity": "medium",
                "reasoning": "JSON 파싱 실패로 원본 텍스트 사용"
            }

        return {
            "pr_intent": pr_intent,
            "messages": [{
                "role": "intent_analyzer",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }]
        }

    except Exception as e:
        logger.error(f"❌ PR 의도 분석 중 오류 발생: {e}")
        return {
            "pr_intent": {
                "type": "error",
                "summary": "분석 실패",
                "key_objectives": [],
                "complexity": "unknown",
                "reasoning": str(e)
            },
            "errors": [f"Intent analysis failed: {str(e)}"]
        }

"""
Risk Classifier Node
"""
import json
from datetime import datetime

from loguru import logger

from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_risk_assessment_prompt
from app.reviewer.llm import get_llm


async def classify_risk(state: ReviewState) -> dict:
    """
    PR의 위험도를 분류하는 노드

    Args:
        state: 현재 리뷰 상태

    Returns:
        업데이트된 상태 (risk_assessment, messages 추가)
    """
    logger.info("⚠️  위험도 분류 시작...")

    pr_data = state["pr_data"]
    pr_intent = state.get("pr_intent", {})

    try:
        # LLM 초기화 (Provider에 따라 자동 선택)
        llm = get_llm(temperature=0.0)

        # 프롬프트 생성
        prompt = create_risk_assessment_prompt(pr_data, pr_intent)

        # LLM 호출
        response = await llm.ainvoke(prompt)
        response_text = response.content

        logger.debug(f"Risk 평가 응답: {response_text[:200]}...")

        # JSON 파싱
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            risk_assessment = json.loads(json_text)

            logger.info(
                f"✅ 위험도 분류 완료: {risk_assessment.get('level', 'UNKNOWN')} "
                f"(점수: {risk_assessment.get('score', 0)}/10)"
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            risk_assessment = {
                "level": "MEDIUM",
                "score": 5,
                "factors": ["json_parse_error"],
                "reasoning": response_text[:300],
                "needs_careful_review": True,
                "review_focus_areas": []
            }

        return {
            "risk_assessment": risk_assessment,
            "messages": [{
                "role": "risk_classifier",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }]
        }

    except Exception as e:
        logger.error(f"❌ 위험도 분류 중 오류 발생: {e}")
        return {
            "risk_assessment": {
                "level": "UNKNOWN",
                "score": 5,
                "factors": ["analysis_error"],
                "reasoning": str(e),
                "needs_careful_review": True,
                "review_focus_areas": []
            },
            "errors": [f"Risk classification failed: {str(e)}"]
        }

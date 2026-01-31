"""
File Reviewer Node (with Loop)
"""
import json
from datetime import datetime

from loguru import logger

from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_file_review_prompt
from app.reviewer.llm import get_llm


async def review_next_file(state: ReviewState) -> dict:
    """
    다음 파일을 리뷰하는 노드 (Loop)

    Args:
        state: 현재 리뷰 상태

    Returns:
        업데이트된 상태 (file_reviews 추가, current_file_index 증가)
    """
    pr_data = state["pr_data"]
    current_index = state.get("current_file_index", 0)
    pr_intent = state.get("pr_intent", {})
    risk_assessment = state.get("risk_assessment", {})

    # 모든 파일을 리뷰했는지 확인
    if current_index >= len(pr_data.files):
        logger.info("✅ 모든 파일 리뷰 완료")
        return {"current_file_index": current_index}

    file = pr_data.files[current_index]

    logger.info(f"📄 파일 리뷰 중 ({current_index + 1}/{len(pr_data.files)}): {file.filename}")

    try:
        # LLM 초기화 (Provider에 따라 자동 선택)
        llm = get_llm(temperature=0.0)

        # 프롬프트 생성
        prompt = create_file_review_prompt(file, pr_intent, risk_assessment)

        # LLM 호출
        response = await llm.ainvoke(prompt)
        response_text = response.content

        logger.debug(f"File review 응답: {response_text[:200]}...")

        # JSON 파싱
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            file_review = json.loads(json_text)

            # 기본 필드 보장
            file_review.setdefault("filename", file.filename)
            file_review.setdefault("status", "UNKNOWN")
            file_review.setdefault("issues", [])
            file_review.setdefault("suggestions", [])
            file_review.setdefault("summary", "리뷰 완료")

            issues_count = len(file_review.get("issues", []))
            logger.info(
                f"  ✅ {file.filename} 리뷰 완료: "
                f"{file_review.get('status', 'UNKNOWN')} ({issues_count}개 이슈)"
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            file_review = {
                "filename": file.filename,
                "status": "ERROR",
                "issues": [],
                "suggestions": [],
                "summary": f"JSON 파싱 실패: {response_text[:200]}",
                "raw_review": response_text
            }

        return {
            "file_reviews": [file_review],
            "current_file_index": current_index + 1,
            "messages": [{
                "role": "file_reviewer",
                "file": file.filename,
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }]
        }

    except Exception as e:
        logger.error(f"❌ 파일 리뷰 중 오류 발생: {e}")
        return {
            "file_reviews": [{
                "filename": file.filename,
                "status": "ERROR",
                "issues": [],
                "suggestions": [],
                "summary": f"리뷰 실패: {str(e)}"
            }],
            "current_file_index": current_index + 1,
            "errors": [f"File review failed for {file.filename}: {str(e)}"]
        }


def should_continue_review(state: ReviewState) -> str:
    """
    더 리뷰할 파일이 있는지 확인하는 조건부 엣지

    Args:
        state: 현재 리뷰 상태

    Returns:
        "continue" 또는 "done"
    """
    pr_data = state["pr_data"]
    current_index = state.get("current_file_index", 0)

    if current_index < len(pr_data.files):
        logger.debug(f"계속 리뷰: {current_index}/{len(pr_data.files)}")
        return "continue"
    else:
        logger.info(f"리뷰 완료: {len(pr_data.files)}개 파일 모두 리뷰됨")
        return "done"

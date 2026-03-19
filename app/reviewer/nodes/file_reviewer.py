"""
File Reviewer Node (Parallel Processing)
"""
import asyncio
import json
from datetime import datetime

from loguru import logger

from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_file_review_prompt
from app.reviewer.llm import get_llm
from app.reviewer.utils import parse_llm_json_response
from app.models import FileChange


async def review_single_file(
    file: FileChange,
    file_index: int,
    total_files: int,
    pr_intent: dict,
    risk_assessment: dict
) -> dict:
    """단일 파일을 리뷰하는 헬퍼 함수.

    Args:
        file: 리뷰할 파일.
        file_index: 파일 인덱스 (로깅용).
        total_files: 전체 파일 수 (로깅용).
        pr_intent: PR 의도 분석 결과.
        risk_assessment: 위험도 평가 결과.

    Returns:
        ``review``, ``message``, ``error`` 키를 포함하는 딕셔너리.
    """
    logger.info(f"📄 파일 리뷰 중 ({file_index + 1}/{total_files}): {file.filename}")

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
            file_review = parse_llm_json_response(response_text)

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
            file_review = {
                "filename": file.filename,
                "status": "ERROR",
                "issues": [],
                "suggestions": [],
                "summary": f"JSON 파싱 실패: {response_text[:200]}",
                "raw_review": response_text
            }

        return {
            "review": file_review,
            "message": {
                "role": "file_reviewer",
                "file": file.filename,
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"❌ 파일 리뷰 중 오류 발생 ({file.filename}): {e}")
        return {
            "review": {
                "filename": file.filename,
                "status": "ERROR",
                "issues": [],
                "suggestions": [],
                "summary": f"리뷰 실패: {str(e)}"
            },
            "message": {
                "role": "file_reviewer",
                "file": file.filename,
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            },
            "error": f"File review failed for {file.filename}: {str(e)}"
        }


async def review_all_files(state: ReviewState) -> dict:
    """모든 파일을 병렬로 리뷰하는 노드.

    Args:
        state: 현재 리뷰 상태.

    Returns:
        ``file_reviews``, ``messages``, ``errors``, ``retry_count``가 포함된 상태 업데이트 딕셔너리.
    """
    pr_data = state["pr_data"]
    pr_intent = state.get("pr_intent", {})
    risk_assessment = state.get("risk_assessment", {})

    files = pr_data.files
    total_files = len(files)

    if total_files == 0:
        logger.warning("⚠️  리뷰할 파일이 없습니다")
        return {
            "file_reviews": [],
            "messages": [],
            "errors": []
        }

    retry_count = state.get("retry_count", 0) + 1
    logger.info(f"🚀 {total_files}개 파일 병렬 리뷰 시작... (실행 횟수: {retry_count})")

    # 모든 파일 리뷰를 병렬로 실행
    review_tasks = [
        review_single_file(file, idx, total_files, pr_intent, risk_assessment)
        for idx, file in enumerate(files)
    ]

    # 병렬 실행
    results = await asyncio.gather(*review_tasks, return_exceptions=True)

    # 결과 집계
    file_reviews = []
    messages = []
    errors = []

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"예외 발생: {result}")
            errors.append(f"Unexpected exception: {str(result)}")
        else:
            file_reviews.append(result["review"])
            messages.append(result["message"])
            if result["error"]:
                errors.append(result["error"])

    logger.info(f"✅ 병렬 리뷰 완료: {len(file_reviews)}개 파일 처리됨")

    return {
        "file_reviews": file_reviews,
        "messages": messages,
        "errors": errors,
        "retry_count": retry_count,
        "needs_retry": False,  # summarize 노드가 다시 판단
    }

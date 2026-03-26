"""
File Reviewer Node (Parallel Processing)
"""
import asyncio
import json
from datetime import datetime

from loguru import logger

from app.github import github_client
from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_file_review_prompt
from app.reviewer.llm import get_llm
from app.reviewer.utils import parse_llm_json_response
from app.models import FileChange

# 라우터/뷰/API 파일이 포함된 경로 패턴 → 앱 진입점을 컨텍스트로 제공
_ROUTE_PATH_PATTERNS = ("routers/", "routes/", "views/", "endpoints/", "api/")
# 앱 진입점 후보 (순서대로 시도)
_ENTRY_CANDIDATES = ("main.py", "app.py", "application.py", "server.py", "asgi.py")


async def _fetch_context_files(
    changed_files: list[FileChange],
    installation_id: str,
    repo_owner: str,
    repo_name: str,
    head_sha: str,
) -> dict[str, str]:
    """변경된 파일 목록을 분석해 리뷰에 필요한 컨텍스트 파일을 GitHub에서 가져옵니다.

    현재 규칙:
    - 라우터/엔드포인트 파일이 포함된 경우 앱 진입점(main.py 등)을 함께 제공합니다.

    Args:
        changed_files: PR에서 변경된 파일 목록.
        installation_id: GitHub App Installation ID.
        repo_owner: 리포지토리 소유자.
        repo_name: 리포지토리 이름.
        head_sha: HEAD 커밋 SHA (파일 내용 조회 기준).

    Returns:
        {파일경로: 파일내용} 딕셔너리. 가져오지 못한 파일은 포함되지 않습니다.
    """
    needs_entry_file = any(
        pattern in f.filename for f in changed_files for pattern in _ROUTE_PATH_PATTERNS
    )
    if not needs_entry_file:
        return {}

    context: dict[str, str] = {}
    for candidate in _ENTRY_CANDIDATES:
        try:
            content = await github_client.get_file_content(
                installation_id=installation_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                file_path=candidate,
                ref=head_sha,
            )
            context[candidate] = content
            logger.info(f"📎 컨텍스트 파일 로드: {candidate}")
            break  # 첫 번째로 찾은 진입점만 사용
        except Exception:
            continue

    return context


async def review_single_file(
    file: FileChange,
    file_index: int,
    total_files: int,
    pr_intent: dict,
    risk_assessment: dict,
    context_files: dict[str, str] | None = None,
    pr_files: list | None = None,
    repo_skills: list[dict] | None = None,
    previous_review: dict | None = None,
) -> dict:
    """단일 파일을 리뷰하는 헬퍼 함수.

    Args:
        file: 리뷰할 파일.
        file_index: 파일 인덱스 (로깅용).
        total_files: 전체 파일 수 (로깅용).
        pr_intent: PR 의도 분석 결과.
        risk_assessment: 위험도 평가 결과.
        context_files: 리뷰에 필요한 관련 파일 내용. {파일경로: 내용} 형식.
        pr_files: 이 PR에서 변경된 전체 파일 목록.
        repo_skills: 저장소별 커스텀 리뷰 기준 목록.
        previous_review: 이전 리뷰 컨텍스트 (미해결 코멘트 포함).

    Returns:
        ``review``, ``message``, ``error`` 키를 포함하는 딕셔너리.
    """
    logger.info(f"📄 파일 리뷰 중 ({file_index + 1}/{total_files}): {file.filename}")

    try:
        # LLM 초기화 (Provider에 따라 자동 선택)
        llm = get_llm(temperature=0.0)

        # 프롬프트 생성
        prompt = create_file_review_prompt(
            file, pr_intent, risk_assessment, context_files, pr_files, repo_skills, previous_review
        )

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
    repo_skills = state.get("repo_skills", [])
    previous_review = state.get("previous_review")

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

    # 컨텍스트 파일 사전 수집 (라우터 등 관련 파일이 있을 때만)
    context_files = await _fetch_context_files(
        changed_files=files,
        installation_id=state["installation_id"],
        repo_owner=state["repo_owner"],
        repo_name=state["repo_name"],
        head_sha=pr_data.head_sha,
    )

    # 모든 파일 리뷰를 병렬로 실행
    review_tasks = [
        review_single_file(
            file, idx, total_files, pr_intent, risk_assessment,
            context_files, files, repo_skills, previous_review
        )
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

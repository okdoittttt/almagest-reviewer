"""
File Reviewer Node (Parallel Processing with Skill Sub-agents)
"""
import asyncio
import json
from datetime import datetime

from loguru import logger

from app.github import github_client
from app.reviewer.state import ReviewState
from app.reviewer.prompts import create_file_review_prompt
from app.reviewer.prompts.skill_agent_prompt import create_skill_agent_prompt
from app.reviewer.skill_router import get_applicable_skills
from app.reviewer.llm import get_llm, get_current_provider
from app.reviewer.utils import parse_llm_json_response
from app.reviewer.file_filter import should_skip_file
from app.reviewer.diff_limit import get_diff_limit
from app.models import FileChange

# 라우터/뷰/API 파일이 포함된 경로 패턴 → 앱 진입점을 컨텍스트로 제공
_ROUTE_PATH_PATTERNS = ("routers/", "routes/", "views/", "endpoints/", "api/")
# 앱 진입점 후보 (순서대로 시도)
_ENTRY_CANDIDATES = ("main.py", "app.py", "application.py", "server.py", "asgi.py")

_VERDICT_TO_STATUS = {
    "fail": "BLOCKING",
    "warn": "MINOR_ISSUES",
    "pass": "LGTM",
}


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
            break
        except Exception:
            continue

    return context


async def _run_skill_agent(
    file: FileChange,
    skill: dict,
    diff_max_chars: int,
) -> dict:
    """단일 스킬 서브 에이전트를 실행합니다.

    Args:
        file: 리뷰 대상 파일.
        skill: 적용할 스킬 정보.
        diff_max_chars: diff 최대 표시 길이.

    Returns:
        ``skill``, ``verdict``, ``issues`` 키를 포함하는 딕셔너리.
    """
    try:
        llm = get_llm(temperature=0.0)
        prompt = create_skill_agent_prompt(file, skill, diff_max_chars)
        response = await llm.ainvoke(prompt)
        result = parse_llm_json_response(response.content)
        result.setdefault("skill", skill.get("name", "unknown"))
        result.setdefault("verdict", "pass")
        result.setdefault("issues", [])
        return result
    except Exception as e:
        logger.warning(f"  ⚠️ 스킬 에이전트 실패 ({skill.get('name')}): {e}")
        return {"skill": skill.get("name", "unknown"), "verdict": "pass", "issues": []}


def _aggregate_skill_results(filename: str, skill_results: list) -> dict:
    """스킬별 결과를 파일 단위 리뷰로 집계합니다.

    Args:
        filename: 파일 경로.
        skill_results: 스킬 서브 에이전트 결과 목록.

    Returns:
        파일 리뷰 결과 딕셔너리.
    """
    all_issues = []
    verdicts = []

    for result in skill_results:
        if isinstance(result, Exception):
            continue
        verdicts.append(result.get("verdict", "pass"))
        for issue in result.get("issues", []):
            issue["skill"] = result.get("skill", "unknown")
            all_issues.append(issue)

    # 가장 심각한 verdict를 파일 status로
    if "fail" in verdicts:
        status = "BLOCKING"
    elif "warn" in verdicts:
        status = "MINOR_ISSUES"
    else:
        status = "LGTM"

    high_issues = [i for i in all_issues if i.get("severity") == "high"]
    if high_issues:
        status = "BLOCKING"
    elif any(i.get("severity") == "medium" for i in all_issues):
        if status == "LGTM":
            status = "MINOR_ISSUES"

    return {
        "filename": filename,
        "status": status,
        "issues": all_issues,
        "suggestions": [],
        "resolved_comment_ids": [],
        "summary": f"{len(skill_results)}개 스킬 검토 완료 — 이슈 {len(all_issues)}개",
        "skill_results": skill_results,
    }


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
    diff_max_chars: int = 10000,
    system_prompt: str | None = None,
) -> dict:
    """단일 파일을 리뷰하는 헬퍼 함수.

    스킬이 있으면 스킬별 서브 에이전트를 병렬 실행하고,
    없으면 system_prompt 기반 단일 LLM 호출로 fallback합니다.

    Args:
        file: 리뷰할 파일.
        file_index: 파일 인덱스 (로깅용).
        total_files: 전체 파일 수 (로깅용).
        pr_intent: PR 의도 분석 결과.
        risk_assessment: 위험도 평가 결과.
        context_files: 리뷰에 필요한 관련 파일 내용.
        pr_files: 이 PR에서 변경된 전체 파일 목록.
        repo_skills: 저장소별 커스텀 리뷰 기준 목록.
        previous_review: 이전 리뷰 컨텍스트.
        diff_max_chars: diff 최대 표시 길이.
        system_prompt: 저장소별 리뷰 지침.

    Returns:
        ``review``, ``message``, ``error`` 키를 포함하는 딕셔너리.
    """
    logger.info(f"📄 파일 리뷰 중 ({file_index + 1}/{total_files}): {file.filename}")

    try:
        # 이 파일에 적용할 스킬 결정 (패턴 매칭, LLM 호출 없음)
        applicable_skills = get_applicable_skills(file.filename, repo_skills or [])

        if applicable_skills:
            logger.info(
                f"  🎯 적용 스킬 {len(applicable_skills)}개: "
                f"{[s['name'] for s in applicable_skills]}"
            )
            # 스킬별 서브 에이전트 병렬 실행
            skill_tasks = [
                _run_skill_agent(file, skill, diff_max_chars)
                for skill in applicable_skills
            ]
            skill_results = await asyncio.gather(*skill_tasks, return_exceptions=True)
            file_review = _aggregate_skill_results(file.filename, list(skill_results))

        else:
            # 스킬 없음 → system_prompt 기반 단일 LLM 호출 (fallback)
            logger.info(f"  💬 스킬 없음 — system_prompt 기반 리뷰")
            llm = get_llm(temperature=0.0)
            prompt = create_file_review_prompt(
                file, pr_intent, risk_assessment, context_files,
                pr_files, None, previous_review, diff_max_chars,
                system_prompt=system_prompt,
            )
            response = await llm.ainvoke(prompt)
            response_text = response.content

            try:
                file_review = parse_llm_json_response(response_text)
                file_review.setdefault("filename", file.filename)
                file_review.setdefault("status", "UNKNOWN")
                file_review.setdefault("issues", [])
                file_review.setdefault("suggestions", [])
                file_review.setdefault("resolved_comment_ids", [])
                file_review.setdefault("summary", "리뷰 완료")
            except json.JSONDecodeError:
                file_review = {
                    "filename": file.filename,
                    "status": "ERROR",
                    "issues": [],
                    "suggestions": [],
                    "summary": f"JSON 파싱 실패: {response_text[:200]}",
                    "raw_review": response_text,
                }

        issues_count = len(file_review.get("issues", []))
        logger.info(
            f"  ✅ {file.filename} 리뷰 완료: "
            f"{file_review.get('status', 'UNKNOWN')} ({issues_count}개 이슈)"
        )

        return {
            "review": file_review,
            "message": {
                "role": "file_reviewer",
                "file": file.filename,
                "content": file_review.get("summary", ""),
                "timestamp": datetime.now().isoformat(),
            },
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ 파일 리뷰 중 오류 발생 ({file.filename}): {e}")
        return {
            "review": {
                "filename": file.filename,
                "status": "ERROR",
                "issues": [],
                "suggestions": [],
                "summary": f"리뷰 실패: {str(e)}",
            },
            "message": {
                "role": "file_reviewer",
                "file": file.filename,
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            },
            "error": f"File review failed for {file.filename}: {str(e)}",
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
    system_prompt = state.get("repo_system_prompt")

    all_files = pr_data.files

    # 저가치 파일 필터링
    files = []
    for f in all_files:
        skip, reason = should_skip_file(f.filename)
        if skip:
            logger.info(f"⏭️  스킵: {f.filename} ({reason})")
        else:
            files.append(f)

    skipped_count = len(all_files) - len(files)
    if skipped_count:
        logger.info(f"⏭️  총 {skipped_count}개 파일 스킵 (lock/generated/build)")

    total_files = len(files)

    if total_files == 0:
        logger.warning("⚠️  리뷰할 파일이 없습니다")
        return {"file_reviews": [], "messages": [], "errors": []}

    risk_level = risk_assessment.get("level")
    diff_max_chars = get_diff_limit(risk_level)
    logger.info(f"📏 diff 한도: {diff_max_chars:,}자 (위험도={risk_level}, provider={get_current_provider()})")

    retry_count = state.get("retry_count", 0) + 1
    logger.info(f"🚀 {total_files}개 파일 병렬 리뷰 시작... (실행 횟수: {retry_count})")

    context_files = await _fetch_context_files(
        changed_files=files,
        installation_id=state["installation_id"],
        repo_owner=state["repo_owner"],
        repo_name=state["repo_name"],
        head_sha=pr_data.head_sha,
    )

    review_tasks = [
        review_single_file(
            file, idx, total_files, pr_intent, risk_assessment,
            context_files, files, repo_skills, previous_review, diff_max_chars,
            system_prompt=system_prompt,
        )
        for idx, file in enumerate(files)
    ]

    results = await asyncio.gather(*review_tasks, return_exceptions=True)

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
        "needs_retry": False,
    }

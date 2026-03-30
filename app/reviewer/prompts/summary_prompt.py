"""
Review Summary Prompt
"""
from app.models import PRData
from app.reviewer.prompts._sanitize import sanitize_skills


def create_summary_prompt(
    pr_data: PRData,
    pr_intent: dict,
    risk_assessment: dict,
    file_reviews: list[dict],
    repo_skills: list[dict] | None = None,
    previous_review: dict | None = None,
    system_prompt: str | None = None,
) -> str:
    """최종 리뷰 요약을 생성하는 프롬프트를 생성합니다.

    Args:
        pr_data: PR 데이터.
        pr_intent: PR 의도 분석 결과.
        risk_assessment: 위험도 평가 결과.
        file_reviews: 파일별 리뷰 결과 목록.
        repo_skills: 저장소별 커스텀 리뷰 기준 목록.
        previous_review: 이전 리뷰 컨텍스트 (미해결 코멘트, 이전 판정 등).
        system_prompt: 저장소별 리뷰 지침. 없으면 스킬만으로 판단합니다.

    Returns:
        LLM에 전달할 프롬프트 문자열.
    """
    # 이슈 집계
    all_issues = []
    blocking_count = 0
    needs_changes_count = 0
    minor_issues_count = 0
    lgtm_count = 0

    for review in file_reviews:
        status = review.get('status', 'UNKNOWN')
        if status == 'BLOCKING':
            blocking_count += 1
        elif status == 'NEEDS_CHANGES':
            needs_changes_count += 1
        elif status == 'MINOR_ISSUES':
            minor_issues_count += 1
        elif status == 'LGTM':
            lgtm_count += 1

        for issue in review.get('issues', []):
            all_issues.append({
                'file': review['filename'],
                'severity': issue.get('severity', 'unknown'),
                'type': issue.get('type', 'unknown'),
                'message': issue.get('message', ''),
                'suggestion': issue.get('suggestion', '')
            })

    # 심각도별 이슈 분류
    high_issues = [i for i in all_issues if i['severity'] == 'high']
    medium_issues = [i for i in all_issues if i['severity'] == 'medium']
    low_issues = [i for i in all_issues if i['severity'] == 'low']

    # 파일별 리뷰 요약
    file_summaries = []
    for review in file_reviews[:10]:  # 최대 10개만
        file_summaries.append(f"""
**{review['filename']}** ({review.get('status', 'UNKNOWN')})
- 이슈: {len(review.get('issues', []))}개
- 요약: {review.get('summary', 'N/A')}
""")

    prev_review_section = ""
    if previous_review:
        unresolved_count = previous_review.get("unresolved_count", 0)
        prev_decision = previous_review.get("decision", "N/A")
        prev_risk = previous_review.get("risk_level", "N/A")

        unresolved_lines = []
        for filename, comments in previous_review.get("unresolved_by_file", {}).items():
            for c in comments:
                unresolved_lines.append(f"- **{filename}** [{c['type']}]: {c['body']}")

        unresolved_text = "\n".join(unresolved_lines[:10]) if unresolved_lines else "(없음)"
        if len(unresolved_lines) > 10:
            unresolved_text += f"\n... 외 {len(unresolved_lines) - 10}개"

        prev_review_section = f"""
## 이전 리뷰 현황 (델타 분석 참고)
- 이전 판정: **{prev_decision}** (위험도: {prev_risk})
- 미해결 코멘트: **{unresolved_count}개**

### 미해결 이슈 목록
{unresolved_text}

종합 평가 시 위 미해결 이슈들이 이번 PR에서 해결됐는지 판단하고,
개선된 항목과 여전히 남은 항목을 코멘트에 명시해주세요.
"""

    system_prompt_section = ""
    if system_prompt and system_prompt.strip():
        system_prompt_section = f"\n## 리뷰 지침\n{system_prompt.strip()}\n"

    skills_section = ""
    if repo_skills:
        safe_skills = sanitize_skills(repo_skills)
        if safe_skills:
            skill_lines = []
            for s in safe_skills:
                line = f"- **{s['name']}**: {s['description']}"
                if s.get("criteria"):
                    line += f"\n  기준: {s['criteria']}"
                skill_lines.append(line)
            skills_section = (
                "\n## 반드시 적용할 리뷰 기준\n"
                + "\n".join(skill_lines)
                + "\n"
            )

    return f"""코드 리뷰어입니다. 모든 파일 리뷰를 종합하여 최종 의견을 작성하고 JSON으로만 응답하세요.
{system_prompt_section}{skills_section}{prev_review_section}
## PR 개요
**제목:** {pr_data.title}
**작성자:** @{pr_data.author.login}
**의도:** {pr_intent.get('summary', 'N/A')} ({pr_intent.get('type', 'unknown')})
**위험도:** {risk_assessment.get('level', 'UNKNOWN')} ({risk_assessment.get('score', 0)}/10)

## 변경 통계
- 파일: {pr_data.changed_files_count}개
- 변경량: +{pr_data.total_additions}/-{pr_data.total_deletions} 줄
- 커밋: {pr_data.commits_count}개

## 리뷰 결과 집계
- ✅ LGTM: {lgtm_count}개 파일
- ⚠️ MINOR_ISSUES: {minor_issues_count}개 파일
- 🔧 NEEDS_CHANGES: {needs_changes_count}개 파일
- 🚫 BLOCKING: {blocking_count}개 파일

## 심각도별 이슈
- 🔴 HIGH: {len(high_issues)}개
- 🟡 MEDIUM: {len(medium_issues)}개
- 🟢 LOW: {len(low_issues)}개

## 주요 이슈 목록
{chr(10).join([
    f"- [{i['severity'].upper()}] {i['file']}: {i['message']}"
    for i in (high_issues + medium_issues)[:5]
]) if (high_issues + medium_issues) else "(심각한 이슈 없음)"}

## 파일별 리뷰 요약
{chr(10).join(file_summaries) if file_summaries else "(리뷰 없음)"}

---

위 정보를 바탕으로 **GitHub PR에 게시할 최종 리뷰 코멘트**를 작성해주세요.

다음 JSON 형식으로 응답해주세요:

```json
{{
  "decision": "APPROVE | REQUEST_CHANGES | COMMENT",
  "summary": "전체 평가를 2-3문장으로 요약",
  "comment": "실제 GitHub에 게시될 마크다운 코멘트",
  "action_items": [
    "수정이 필요한 항목 1"
  ],
  "needs_deeper_review": false
}}
```

**needs_deeper_review 기준:**
- `true`: 특정 파일의 리뷰 내용이 불충분하거나, high severity 이슈가 있는데 근거가 부족하여 더 깊은 분석이 필요한 경우
- `false`: 리뷰 내용이 충분하거나, 파일 리뷰 자체가 없는 경우 (LOW 위험도 PR 등)

JSON만 응답해주세요."""

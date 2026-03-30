"""Skill 서브 에이전트 프롬프트 — 단일 스킬 기준으로 파일을 검토합니다."""
from app.models import FileChange
from app.reviewer.prompts._sanitize import sanitize_skill_text, _MAX_NAME_LEN, _MAX_DESC_LEN, _MAX_CRITERIA_LEN


def create_skill_agent_prompt(
    file: FileChange,
    skill: dict,
    diff_max_chars: int = 10000,
    context_files: dict[str, str] | None = None,
    pr_files: list | None = None,
    previous_review: dict | None = None,
) -> str:
    """단일 스킬 서브 에이전트용 프롬프트를 생성합니다.

    Args:
        file: 리뷰 대상 파일.
        skill: 적용할 스킬 정보 (name, description, criteria).
        diff_max_chars: diff 최대 표시 길이.
        context_files: 리뷰에 필요한 관련 파일 내용. {파일경로: 내용} 형식.
        pr_files: 이 PR에서 변경된 전체 파일 목록 (FileChange 리스트).
        previous_review: 이전 리뷰 컨텍스트. ``unresolved_by_file`` 등을 포함합니다.

    Returns:
        LLM에 전달할 프롬프트 문자열.
    """
    name = sanitize_skill_text(skill.get("name"), _MAX_NAME_LEN)
    description = sanitize_skill_text(skill.get("description"), _MAX_DESC_LEN)
    criteria = sanitize_skill_text(skill.get("criteria"), _MAX_CRITERIA_LEN)

    patch_preview = file.patch[:diff_max_chars] if file.patch and len(file.patch) > diff_max_chars else (file.patch or "")
    is_truncated = file.patch and len(file.patch) > diff_max_chars

    criteria_section = f"\n{criteria}" if criteria else ""

    pr_files_section = ""
    if pr_files:
        file_lines = [
            f"- {f.filename} ({f.status}, +{f.additions}/-{f.deletions})"
            for f in pr_files
            if f.filename != file.filename
        ]
        if file_lines:
            pr_files_section = "\n## 이 PR에서 함께 변경된 파일들\n" + "\n".join(file_lines) + "\n"

    context_section = ""
    if context_files:
        parts = []
        for path, content in context_files.items():
            preview = content[:2000] if len(content) > 2000 else content
            truncated = " (처음 2000자)" if len(content) > 2000 else ""
            parts.append(f"### `{path}`{truncated}\n```\n{preview}\n```")
        context_section = "\n## 관련 파일 (변경되지 않은 컨텍스트)\n" + "\n\n".join(parts) + "\n"

    prev_issues_section = ""
    if previous_review:
        unresolved = previous_review.get("unresolved_by_file", {}).get(file.filename, [])
        if unresolved:
            lines = [f"- [#{c['id']}][{c['type']}] {c['body']}" for c in unresolved]
            prev_issues_section = (
                "\n## 이전 리뷰에서 미해결된 이슈 (이 파일)\n"
                + "\n".join(lines)
                + "\n이 이슈들이 이번 변경에서 해결됐는지 확인하세요. "
                + "해결된 이슈의 ID를 resolved_comment_ids에 포함해주세요.\n"
            )

    return f"""코드 리뷰어입니다. 아래 단일 기준으로만 이 파일을 검토하고 JSON으로만 응답하세요.

## 검토 기준: {name}
{description}{criteria_section}
{pr_files_section}{context_section}{prev_issues_section}
## 파일: `{file.filename}`
**변경:** +{file.additions}/-{file.deletions}
{'(처음 ' + str(diff_max_chars) + '자만 표시)' if is_truncated else ''}

```diff
{patch_preview}
```

이 기준에 해당하는 이슈만 찾아 JSON으로 응답하세요:

```json
{{
  "skill": "{name}",
  "verdict": "pass | warn | fail",
  "issues": [
    {{
      "severity": "high | medium | low",
      "type": "bug | security | performance | style | logic",
      "message": "구체적인 문제 설명",
      "suggestion": "해결 방법 제안"
    }}
  ],
  "resolved_comment_ids": [이전 리뷰에서 이번 변경으로 해결된 코멘트 ID 목록. 없으면 빈 배열]
}}
```

**verdict 기준:**
- `pass`: 이 기준에서 문제 없음
- `warn`: 권장사항 위반 (low/medium 이슈)
- `fail`: 반드시 수정 필요 (high 이슈 존재)

JSON만 응답하세요."""

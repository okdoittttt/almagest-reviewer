"""
File Review Prompt
"""
from app.models import FileChange
from app.reviewer.prompts._sanitize import sanitize_skills


def create_file_review_prompt(
    file: FileChange,
    pr_intent: dict,
    risk_assessment: dict,
    context_files: dict[str, str] | None = None,
    pr_files: list | None = None,
    repo_skills: list[dict] | None = None,
    previous_review: dict | None = None,
    diff_max_chars: int = 10000,
    system_prompt: str | None = None,
) -> str:
    """개별 파일을 리뷰하는 프롬프트를 생성합니다.

    Args:
        file: 파일 변경 정보.
        pr_intent: PR 의도 분석 결과.
        risk_assessment: 위험도 평가 결과.
        context_files: 리뷰에 필요한 관련 파일 내용. {파일경로: 내용} 형식.
        pr_files: 이 PR에서 변경된 전체 파일 목록 (FileChange 리스트).
        repo_skills: 저장소별 커스텀 리뷰 기준 목록.
        previous_review: 이전 리뷰 컨텍스트. ``unresolved_by_file`` 등을 포함합니다.
        diff_max_chars: diff 최대 표시 길이 (문자 수).
        system_prompt: 저장소별 리뷰 지침. 없으면 스킬만으로 판단합니다.

    Returns:
        LLM에 전달할 프롬프트 문자열.
    """
    # Diff가 없는 경우 (바이너리 파일, 이름 변경 등)
    if not file.patch:
        return f"""코드 리뷰어입니다. 다음 파일의 변경사항을 검토해주세요.

**파일:** `{file.filename}`
**상태:** {file.status}
**변경:** +{file.additions}/-{file.deletions}

Diff가 제공되지 않았습니다. (바이너리 파일이거나 이름만 변경됨)

```json
{{
  "filename": "{file.filename}",
  "status": "LGTM",
  "issues": [],
  "suggestions": [],
  "summary": "Diff 없음 - {file.status} 파일"
}}
```

JSON만 응답해주세요."""

    # Diff 길이 제한
    patch_preview = file.patch[:diff_max_chars] if len(file.patch) > diff_max_chars else file.patch
    is_truncated = len(file.patch) > diff_max_chars

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

    pr_files_section = ""
    if pr_files:
        file_lines = [
            f"- {f.filename} ({f.status}, +{f.additions}/-{f.deletions})"
            for f in pr_files
            if f.filename != file.filename
        ]
        if file_lines:
            pr_files_section = "\n## 이 PR에서 함께 변경된 파일들\n" + "\n".join(file_lines) + "\n"

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

    context_section = ""
    if context_files:
        parts = []
        for path, content in context_files.items():
            preview = content[:2000] if len(content) > 2000 else content
            truncated = " (처음 2000자)" if len(content) > 2000 else ""
            parts.append(f"### `{path}`{truncated}\n```\n{preview}\n```")
        context_section = "\n## 관련 파일 (변경되지 않은 컨텍스트)\n" + "\n\n".join(parts) + "\n"

    return f"""코드 리뷰어입니다. 아래 기준에 따라 파일을 리뷰하고 JSON으로만 응답하세요.
{system_prompt_section}{skills_section}
## 컨텍스트
**PR 의도:** {pr_intent.get('summary', 'N/A')} ({pr_intent.get('type', 'unknown')})
**위험도:** {risk_assessment.get('level', 'UNKNOWN')} (점수: {risk_assessment.get('score', 0)}/10)
**주요 검토 영역:** {', '.join(risk_assessment.get('review_focus_areas', [])[:3])}
{pr_files_section}{prev_issues_section}{context_section}
## 파일 정보
**경로:** `{file.filename}`
**상태:** {file.status}
**변경:** +{file.additions} 줄 추가, -{file.deletions} 줄 삭제

## Diff
{'(처음 ' + str(diff_max_chars) + '자만 표시, 전체 길이: ' + str(len(file.patch)) + '자)' if is_truncated else ''}

```diff
{patch_preview}
```

---

다음 JSON 형식으로 응답해주세요:

```json
{{
  "filename": "{file.filename}",
  "status": "LGTM | MINOR_ISSUES | NEEDS_CHANGES | BLOCKING",
  "issues": [
    {{
      "severity": "high | medium | low",
      "type": "bug | security | performance | style | logic",
      "message": "구체적인 문제 설명",
      "suggestion": "해결 방법 제안"
    }}
  ],
  "suggestions": [
    "개선 제안 1"
  ],
  "positive_notes": [
    "잘된 부분 1"
  ],
  "resolved_comment_ids": [이전 리뷰에서 이번 변경으로 해결된 코멘트 ID 목록. 없으면 빈 배열],
  "summary": "이 파일 변경에 대한 전체 평가 (2-3문장)"
}}
```

JSON만 응답해주세요. 실제 코드를 작성하지 말고 검토만 해주세요."""

"""Skill 서브 에이전트 프롬프트 — 단일 스킬 기준으로 파일을 검토합니다."""
from app.models import FileChange
from app.reviewer.prompts._sanitize import sanitize_skill_text, _MAX_NAME_LEN, _MAX_DESC_LEN, _MAX_CRITERIA_LEN


def create_skill_agent_prompt(
    file: FileChange,
    skill: dict,
    diff_max_chars: int = 10000,
) -> str:
    """단일 스킬 서브 에이전트용 프롬프트를 생성합니다.

    Args:
        file: 리뷰 대상 파일.
        skill: 적용할 스킬 정보 (name, description, criteria).
        diff_max_chars: diff 최대 표시 길이.

    Returns:
        LLM에 전달할 프롬프트 문자열.
    """
    name = sanitize_skill_text(skill.get("name"), _MAX_NAME_LEN)
    description = sanitize_skill_text(skill.get("description"), _MAX_DESC_LEN)
    criteria = sanitize_skill_text(skill.get("criteria"), _MAX_CRITERIA_LEN)

    patch_preview = file.patch[:diff_max_chars] if file.patch and len(file.patch) > diff_max_chars else (file.patch or "")
    is_truncated = file.patch and len(file.patch) > diff_max_chars

    criteria_section = f"\n{criteria}" if criteria else ""

    return f"""코드 리뷰어입니다. 아래 단일 기준으로만 이 파일을 검토하고 JSON으로만 응답하세요.

## 검토 기준: {name}
{description}{criteria_section}

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
      "message": "구체적인 문제 설명",
      "suggestion": "해결 방법 제안"
    }}
  ]
}}
```

**verdict 기준:**
- `pass`: 이 기준에서 문제 없음
- `warn`: 권장사항 위반 (low/medium 이슈)
- `fail`: 반드시 수정 필요 (high 이슈 존재)

JSON만 응답하세요."""

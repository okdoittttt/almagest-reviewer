"""
PR Intent Analysis Prompt
"""
from app.models import PRData


def create_intent_analysis_prompt(pr_data: PRData) -> str:
    """
    PR의 의도를 분석하는 프롬프트 생성

    Args:
        pr_data: PR 데이터

    Returns:
        프롬프트 문자열
    """
    commits_summary = "\n".join([
        f"- {commit.sha[:7]}: {commit.message.split(chr(10))[0]}"
        for commit in pr_data.commits[:5]
    ]) if pr_data.commits else "커밋 정보 없음"

    if len(pr_data.commits) > 5:
        commits_summary += f"\n- ... 외 {len(pr_data.commits) - 5}개 커밋"

    return f"""당신은 숙련된 코드 리뷰어입니다. 다음 Pull Request의 의도를 분석해주세요.

## PR 정보

**제목:** {pr_data.title}

**본문:**
{pr_data.body or '(본문 없음)'}

**브랜치:** `{pr_data.head_branch}` → `{pr_data.base_branch}`

**작성자:** @{pr_data.author.login}

**변경 통계:**
- 파일: {pr_data.changed_files_count}개
- 추가: +{pr_data.total_additions} 줄
- 삭제: -{pr_data.total_deletions} 줄
- 커밋: {pr_data.commits_count}개

**커밋 목록:**
{commits_summary}

**변경된 파일 (처음 10개):**
{chr(10).join([f"- {file.filename} ({file.status})" for file in pr_data.files[:10]])}

---

다음 형식으로 JSON 응답을 제공해주세요:

```json
{{
  "type": "feature | bugfix | refactor | docs | test | chore",
  "summary": "이 PR의 핵심 목적을 한 문장으로 요약",
  "key_objectives": ["목표1", "목표2", "목표3"],
  "complexity": "low | medium | high",
  "reasoning": "이 분석의 근거"
}}
```

**판단 기준:**
1. **type**: 커밋 메시지, 변경된 파일, PR 제목/본문을 종합하여 가장 적합한 유형 선택
2. **summary**: PR의 핵심 가치를 명확하게 표현
3. **key_objectives**: 구체적이고 측정 가능한 목표들
4. **complexity**: 코드 변경의 범위와 영향도를 고려

JSON만 응답해주세요."""

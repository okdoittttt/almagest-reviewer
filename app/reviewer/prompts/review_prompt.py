"""
File Review Prompt
"""
from app.models import FileChange


def create_file_review_prompt(
    file: FileChange,
    pr_intent: dict,
    risk_assessment: dict
) -> str:
    """
    개별 파일을 리뷰하는 프롬프트 생성

    Args:
        file: 파일 변경 정보
        pr_intent: PR 의도 분석 결과
        risk_assessment: 위험도 평가 결과

    Returns:
        프롬프트 문자열
    """
    # Diff가 없는 경우 (바이너리 파일, 이름 변경 등)
    if not file.patch:
        return f"""다음 파일의 변경사항을 검토해주세요.

**파일:** `{file.filename}`
**상태:** {file.status}
**변경:** +{file.additions}/-{file.deletions}

Diff가 제공되지 않았습니다. (바이너리 파일이거나 이름만 변경됨)

간단히 다음 형식으로 응답해주세요:

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

    # Diff 길이 제한 (너무 긴 경우 요약)
    patch_preview = file.patch[:3000] if len(file.patch) > 3000 else file.patch
    is_truncated = len(file.patch) > 3000

    return f"""당신은 코드 품질과 보안을 중시하는 시니어 개발자입니다. 다음 파일의 변경사항을 상세히 리뷰해주세요.

## 컨텍스트
**PR 의도:** {pr_intent.get('summary', 'N/A')} ({pr_intent.get('type', 'unknown')})
**위험도:** {risk_assessment.get('level', 'UNKNOWN')} (점수: {risk_assessment.get('score', 0)}/10)
**주요 검토 영역:** {', '.join(risk_assessment.get('review_focus_areas', [])[:3])}

## 파일 정보
**경로:** `{file.filename}`
**상태:** {file.status}
**변경:** +{file.additions} 줄 추가, -{file.deletions} 줄 삭제

## Diff
{'(처음 3000자만 표시, 전체 길이: ' + str(len(file.patch)) + '자)' if is_truncated else ''}

```diff
{patch_preview}
```

---

다음 관점에서 코드를 검토하고, JSON 형식으로 응답해주세요:

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
    "개선 제안 1",
    "개선 제안 2"
  ],
  "positive_notes": [
    "잘된 부분 1",
    "잘된 부분 2"
  ],
  "summary": "이 파일 변경에 대한 전체 평가 (2-3문장)"
}}
```

**검토 체크리스트:**
1. ✅ **로직 정확성**: 버그 가능성, 엣지 케이스 처리
2. 🔒 **보안**: SQL Injection, XSS, 인증/인가 우회, 민감정보 노출
3. ⚡ **성능**: N+1 쿼리, 불필요한 반복, 메모리 누수
4. 🎨 **코드 품질**: 가독성, 중복 코드, 네이밍, 복잡도
5. 🧪 **테스트 필요성**: 이 변경에 테스트가 필요한가?
6. 📚 **문서화**: 복잡한 로직에 주석이 필요한가?

**severity 판단 기준:**
- **high**: 보안 취약점, 치명적 버그, 데이터 손실 가능성
- **medium**: 일반적인 버그, 성능 문제, 잘못된 로직
- **low**: 코드 스타일, 네이밍, 가독성 개선

**status 판단 기준:**
- **LGTM**: 이슈 없음, 승인 가능
- **MINOR_ISSUES**: 사소한 개선사항만 있음, 승인 가능
- **NEEDS_CHANGES**: 수정이 필요하지만 치명적이지 않음
- **BLOCKING**: 반드시 수정해야 함 (보안, 치명적 버그)

JSON만 응답해주세요. 실제 코드를 작성하지 말고 검토만 해주세요."""

# almagest-reviewer 🌌

**An experimental GitHub code reviewer exploring agent workflows with LangGraph**

`almagest-reviewer`는 Pull Request 코드 리뷰를 자동화하기 위해 설계된  
**Agentic workflow 기반 GitHub App**입니다.  
LangGraph를 활용해 리뷰 단계를 명시적인 그래프 구조로 정의하고,  
자동 판단과 사람의 개입(human-in-the-loop)을 자연스럽게 결합하는 것을 목표로 합니다.

---

## Motivation

대부분의 AI 코드 리뷰 도구는 다음 중 하나에 머무릅니다.

- 단순 LLM 호출 기반의 일회성 리뷰
- 규칙 기반 정적 분석
- 사람이 최종 판단을 하기 어려운 블랙박스형 자동화

`almagest-reviewer`는 다음 질문에서 출발했습니다.

> 코드 리뷰를 **에이전트의 사고 흐름(process)**로 모델링할 수는 없을까?

이 프로젝트는 **LangGraph**를 사용해  
리뷰 과정을 **명시적인 상태 전이(State Transition)**,  
**루프(loop)**, 그리고 **인간 개입 지점(human-in-the-loop)**으로 구성합니다.

---

## Key Features

- **Agentic Code Review**  
  코드 분석 → 이슈 분류 → 리뷰 생성 과정을 그래프로 모델링

- **Human-in-the-loop**  
  특정 조건에서 자동 리뷰를 중단하고 사람의 판단을 요청

- **LangGraph-based Workflow**  
  단순 체인이 아닌 상태 기반 에이전트 플로우

- **GitHub App Integration**  
  Pull Request 이벤트 기반 자동 실행

- **Extensible Review Nodes**  
  Lint / Architecture / Readability / Risk Analysis 등 노드 확장 가능

---

## High-level Architecture

```text
GitHub Pull Request Event
          ↓
   Webhook Receiver
          ↓
   LangGraph Workflow
     ├─ Code Context Builder
     ├─ Review Agent
     ├─ Issue Classifier
     ├─ Human-in-the-loop Gate
     └─ Comment Generator
          ↓
 GitHub Review Comment
```
---

## Why "Almagest"?

**Almagest**는 고대 천문학에서  
복잡한 천체의 움직임을 체계적으로 설명한 이론 체계입니다.

이 프로젝트는 코드 리뷰 역시  
단순한 결과(output)가 아니라  
**구조화된 사고 과정(system)**으로 다뤄야 한다는 관점에서 출발했습니다.

`almagest-reviewer`는  
AI의 판단을 보이지 않는 마법이 아닌,  
**설명 가능한 흐름으로 드러내는 것**을 목표로 합니다.

---

## GitHub App Permissions (Planned)

최소 권한 원칙을 따릅니다.

- **Pull Requests**: Read & Write  
- **Contents**: Read  
- **Metadata**: Read  

---

## Data & Privacy

- Pull Request 코드 및 메타데이터는 **리뷰 목적에 한해 처리**
- 장기 저장을 기본으로 하지 않음
- 외부 전송 여부 및 범위는 명시적으로 관리

(세부 정책은 추후 문서화 예정)

---

## Project Status

**MVP Complete** ✅

- [x] 프로젝트 컨셉 및 구조 설계
- [x] LangGraph 학습 및 PoC
- [x] GitHub App 생성 및 설치
- [x] JWT 토큰 기반 GitHub App 인증 구현
- [x] Webhook 서명 검증 구현
- [x] PR 데이터 수집 시스템 (파일 변경, 커밋, diff 포함)
- [x] LangGraph 기반 4단계 코드 리뷰 워크플로우
- [x] Multi-LLM Provider 지원 (Anthropic Claude, Google Gemini)
- [x] Webhook → Workflow 연결
- [x] PR 리뷰 자동 코멘트 MVP

---

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Webhook 서버
- **LangGraph** - Agentic workflow orchestration
- **LangChain** - LLM abstraction layer
- **Pydantic** - Data validation and settings
- **PyGithub** - GitHub API wrapper
- **PyJWT** - JWT token generation
- **Loguru** - Structured logging
- **Anthropic Claude API** - Primary LLM provider
- **Google Gemini API** - Alternative LLM provider

---

## Architecture Deep Dive

### LangGraph Workflow

```text
PR Webhook Event
      ↓
  PR Data Collection
  (파일, 커밋, diff 수집)
      ↓
┌─────────────────────────┐
│  LangGraph Workflow     │
├─────────────────────────┤
│                         │
│  1. Intent Analysis     │  ← PR 의도 파악 (feature/bugfix/refactor)
│         ↓               │
│  2. Risk Classification │  ← 위험도 평가 (LOW/MEDIUM/HIGH)
│         ↓               │
│  3. File Review (Loop)  │  ← 각 파일별 상세 리뷰
│    ├─ review_file       │
│    ├─ should_continue?  │
│    └─ [loop until done] │
│         ↓               │
│  4. Review Summary      │  ← 최종 리뷰 통합 및 의사결정
│                         │
└─────────────────────────┘
      ↓
GitHub PR Comment
(APPROVE/REQUEST_CHANGES/COMMENT)
```

### State Management

LangGraph의 상태 기반 워크플로우는 다음 데이터를 관리합니다:

```python
ReviewState = {
    "pr_data": PRData,              # PR 메타데이터 + 파일 변경사항
    "pr_intent": dict,              # PR 의도 분석 결과
    "risk_assessment": dict,        # 위험도 평가 결과
    "file_reviews": List[dict],     # 각 파일별 리뷰 (누적)
    "current_file_index": int,      # 현재 리뷰 중인 파일 인덱스
    "final_review": str,            # 최종 마크다운 리뷰
    "review_decision": str,         # APPROVE/REQUEST_CHANGES/COMMENT
    "messages": List[dict],         # 각 노드의 LLM 응답 기록
    "errors": List[str]             # 에러 로그
}
```

---

## Project Structure

```text
almagest-reviewer/
├── app/
│   ├── auth/
│   │   └── jwt_generator.py        # GitHub App JWT 토큰 생성
│   ├── github/
│   │   ├── client.py               # GitHub API 클라이언트
│   │   └── pr_collector.py         # PR 데이터 수집기
│   ├── models/
│   │   └── pr_data.py              # Pydantic 데이터 모델
│   ├── reviewer/
│   │   ├── graph.py                # LangGraph 워크플로우 정의
│   │   ├── state.py                # ReviewState TypedDict
│   │   ├── llm.py                  # LLM Provider Factory
│   │   ├── nodes/
│   │   │   ├── intent_analyzer.py  # Node 1: PR 의도 분석
│   │   │   ├── risk_classifier.py  # Node 2: 위험도 평가
│   │   │   ├── file_reviewer.py    # Node 3: 파일별 리뷰 (Loop)
│   │   │   └── summarizer.py       # Node 4: 최종 요약
│   │   └── prompts/
│   │       ├── intent_prompt.py    # Intent 분석 프롬프트
│   │       ├── risk_prompt.py      # Risk 평가 프롬프트
│   │       ├── review_prompt.py    # 파일 리뷰 프롬프트
│   │       └── summary_prompt.py   # 최종 요약 프롬프트
│   ├── webhook/
│   │   └── validator.py            # Webhook 서명 검증
│   └── config.py                   # 설정 관리 (Pydantic Settings)
├── tests/                          # 단위 테스트
├── main.py                         # FastAPI 서버 & Webhook 엔드포인트
├── requirements.txt
├── .env.example
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites

- Python 3.11 이상
- GitHub App 생성 및 설치 완료
- Anthropic API Key 또는 Google API Key

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/almagest-reviewer.git
cd almagest-reviewer
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. GitHub App Configuration

#### GitHub App 생성

1. GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
2. 필수 권한 설정:
   - **Repository permissions:**
     - Pull requests: Read & Write
     - Contents: Read
     - Metadata: Read
3. Subscribe to events:
   - Pull request
4. Webhook URL: `https://your-domain.com/webhook`
5. Webhook secret 생성 (랜덤 문자열 권장)

#### Private Key 다운로드

1. GitHub App 설정 페이지에서 "Generate a private key" 클릭
2. 다운로드된 `.pem` 파일을 프로젝트 루트에 저장
3. 경로를 `.env` 파일에 기록

#### Installation ID 확인

1. GitHub App을 Repository에 설치
2. 설치 후 URL에서 Installation ID 확인:
   ```
   https://github.com/settings/installations/{installation_id}
   ```

### 5. Environment Variables Setup

`.env.example`을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 내용:

```bash
# GitHub App Credentials
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=./your-app-name.private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_INSTALLATION_ID=your_installation_id

# LLM Provider Selection (anthropic or google)
LLM_PROVIDER=anthropic

# Anthropic API (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Google API (Gemini)
GOOGLE_API_KEY=AIzaxxxxx

# Server Settings
HOST=0.0.0.0
PORT=8000
```

### 6. LLM Provider Configuration

#### Option A: Anthropic Claude (Default)

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

기본 모델: `claude-3-5-sonnet-20241022`

#### Option B: Google Gemini

```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=AIzaxxxxx
```

기본 모델: `gemini-2.5-flash`

모델 변경은 [app/reviewer/llm.py](app/reviewer/llm.py)에서 가능:

```python
# Anthropic
model = kwargs.pop("model", "claude-3-5-sonnet-20241022")

# Google
model = kwargs.pop("model", "gemini-2.5-flash")
```

---

## Running the Server

### Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

서버가 시작되면 다음 엔드포인트가 활성화됩니다:

- `GET /` - Health check
- `POST /webhook` - GitHub Webhook receiver

---

## Testing

### 1. Unit Tests

```bash
# JWT 토큰 생성 테스트
python tests/test_jwt_generation.py

# Installation Token 획득 테스트
python tests/test_installation_token.py

# Webhook 서명 검증 테스트
python tests/test_webhook_signature.py

# Webhook 엔드포인트 테스트
python tests/test_webhook_endpoint.py

# PR 데이터 수집 테스트
python tests/test_pr_data_collection.py
```

### 2. End-to-End Test with Real PR

#### 로컬 테스트 (ngrok 사용)

```bash
# 1. ngrok로 로컬 서버 노출
ngrok http 8000

# 2. ngrok URL을 GitHub App Webhook URL에 설정
# https://xxxx.ngrok.io/webhook

# 3. 테스트 레포지토리에 PR 생성
# GitHub App이 설치된 레포지토리에서 새 PR 생성

# 4. 서버 로그 확인
# LangGraph 워크플로우 실행 과정이 출력됨
```

#### 로그 출력 예시

```text
INFO - 🎯 PR 의도 분석 시작...
INFO - ✅ PR 의도 분석 완료: feature - JWT 토큰 발급 로직 추가...
INFO - ⚠️ 위험도 평가 시작...
INFO - ✅ 위험도 평가 완료: MEDIUM (Score: 5/10)
INFO - 📄 파일 리뷰 중 (1/3): app/auth/jwt_generator.py
INFO - ✅ app/auth/jwt_generator.py 리뷰 완료: APPROVED (0개 이슈)
INFO - 📝 최종 리뷰 요약 시작...
INFO - ✅ 최종 리뷰 완료: COMMENT
INFO - 💬 리뷰 코멘트 작성 완료
```

### 3. Example Review Output

LangGraph 워크플로우가 생성하는 최종 리뷰 예시:

```markdown
## 🤖 AI 코드 리뷰

### 📋 PR 요약
**타입**: Feature
**복잡도**: Medium
**위험도**: MEDIUM (5/10)

이 PR은 GitHub App의 JWT 토큰 생성 로직을 추가합니다.

### 🎯 주요 목표
- GitHub App 인증을 위한 JWT 토큰 생성 함수 구현
- RS256 알고리즘을 사용한 안전한 서명
- 토큰 만료 시간 설정 (기본 10분)

### ⚠️ 발견된 이슈

#### 🔴 Critical Issues
없음

#### 🟡 Warnings
- **app/auth/jwt_generator.py:45** - 에러 핸들링 개선 권장
  - 파일 읽기 실패 시 구체적인 예외 처리 추가

### ✅ 파일별 리뷰

#### app/auth/jwt_generator.py
**상태**: APPROVED

- JWT 토큰 생성 로직이 올바르게 구현됨
- RS256 알고리즘 사용으로 보안 요구사항 충족
- 타입 힌트가 잘 적용되어 있음

**개선 제안**:
- Private key 파일 읽기 실패 시 더 명확한 에러 메시지 제공
- 토큰 만료 시간을 환경 변수로 설정 가능하도록 개선

### 🎬 최종 결정
**COMMENT** - 추가 리뷰 필요

전반적으로 잘 구현되었으나, 에러 핸들링 개선 후 머지를 권장합니다.

---
*🤖 Generated by Almagest Reviewer*
```

---

## Configuration Options

### LLM Temperature Settings

각 노드별로 temperature 조정 가능:

- **Intent Analyzer**: `temperature=0.0` (결정적)
- **Risk Classifier**: `temperature=0.0` (결정적)
- **File Reviewer**: `temperature=0.0` (결정적)
- **Summarizer**: `temperature=0.1` (약간의 창의성)

### Review Workflow Customization

[app/reviewer/graph.py](app/reviewer/graph.py)에서 워크플로우 수정:

```python
# 노드 추가
workflow.add_node("custom_node", custom_function)

# 엣지 추가
workflow.add_edge("intent_analysis", "custom_node")
workflow.add_edge("custom_node", "risk_classification")
```

### Prompt Customization

[app/reviewer/prompts/](app/reviewer/prompts/) 디렉토리에서 각 노드의 프롬프트 수정 가능:

- `intent_prompt.py` - PR 의도 분석 지침
- `risk_prompt.py` - 위험도 평가 기준
- `review_prompt.py` - 코드 리뷰 가이드라인
- `summary_prompt.py` - 최종 요약 형식

---

## Development Guide

### Adding a New Review Node

1. **노드 함수 작성** (`app/reviewer/nodes/your_node.py`)

```python
async def your_custom_node(state: ReviewState) -> dict:
    llm = get_llm(temperature=0.0)
    prompt = create_your_prompt(state["pr_data"])
    response = await llm.ainvoke(prompt)

    return {
        "your_result": response.content,
        "messages": [{
            "role": "your_node",
            "content": response.content,
            "timestamp": datetime.now().isoformat()
        }]
    }
```

2. **State 업데이트** (`app/reviewer/state.py`)

```python
class ReviewState(TypedDict):
    # ... existing fields ...
    your_result: str  # 새 필드 추가
```

3. **Graph에 노드 추가** (`app/reviewer/graph.py`)

```python
from app.reviewer.nodes.your_node import your_custom_node

workflow.add_node("your_node", your_custom_node)
workflow.add_edge("intent_analysis", "your_node")
workflow.add_edge("your_node", "risk_classification")
```

### Debugging

#### LLM 응답 로깅

모든 노드는 `messages` 필드에 LLM 응답을 기록합니다:

```python
for msg in review_result.get("messages", []):
    logger.debug(f"{msg['role']}: {msg['content'][:200]}...")
```

#### State 추적

LangGraph의 상태 변화를 추적하려면:

```python
# app/reviewer/graph.py
async def run_review(pr_data: PRData, ...):
    result = await workflow.ainvoke(initial_state)

    # 각 단계별 상태 출력
    logger.debug(f"PR Intent: {result.get('pr_intent')}")
    logger.debug(f"Risk: {result.get('risk_assessment')}")
    logger.debug(f"File Reviews: {len(result.get('file_reviews', []))}")

    return result
```

---

## Troubleshooting

### 1. JWT 토큰 생성 실패

**증상**: `401 Unauthorized` 에러

**해결**:
- `GITHUB_APP_ID`가 올바른지 확인
- Private key 파일 경로 확인
- Private key 파일이 손상되지 않았는지 확인

```bash
# Private key 검증
openssl rsa -in your-app.private-key.pem -check
```

### 2. Webhook 서명 검증 실패

**증상**: `Invalid webhook signature` 에러

**해결**:
- `GITHUB_WEBHOOK_SECRET`이 GitHub App 설정과 일치하는지 확인
- Webhook 요청의 `X-Hub-Signature-256` 헤더 확인

### 3. LLM API 호출 실패

**증상**: `API key not found` 또는 `Rate limit exceeded`

**해결**:

```bash
# Anthropic API Key 확인
echo $ANTHROPIC_API_KEY

# Google API Key 확인
echo $GOOGLE_API_KEY

# API Key 테스트
python -c "from app.reviewer.llm import get_llm; llm = get_llm(); print('OK')"
```

### 4. JSON 파싱 실패

**증상**: `JSON decode error` in logs

**원인**: LLM이 JSON 형식이 아닌 응답 반환

**해결**: 각 노드는 파싱 실패 시 폴백 처리가 구현되어 있음. 프롬프트를 더 명확하게 수정하거나 temperature를 낮추세요.

### 5. File Review Loop가 멈춤

**증상**: 일부 파일만 리뷰되고 멈춤

**해결**:
- `current_file_index` 상태 확인
- `should_continue_review()` 로직 검증
- 특정 파일에서 예외 발생 여부 확인 (로그 확인)

---

## Roadmap

### Planned Features

- [ ] **Human-in-the-loop Gate**: 고위험 PR은 자동 승인하지 않고 사람에게 알림
- [ ] **Review Quality Metrics**: 리뷰 품질 측정 및 개선
- [ ] **Multi-model Ensemble**: 여러 LLM 결과를 앙상블하여 신뢰도 향상
- [ ] **Incremental Review**: 이전 리뷰와 비교하여 변경사항만 리뷰
- [ ] **Custom Rule Integration**: 팀별 코딩 컨벤션 적용
- [ ] **Performance Optimization**: 대형 PR(100+ files) 처리 최적화
- [ ] **Docker Deployment**: 컨테이너 기반 배포 가이드
- [ ] **Dashboard**: 리뷰 통계 및 인사이트 대시보드

### Known Limitations

- 매우 큰 파일(1000+ lines)은 LLM context limit에 걸릴 수 있음
- Binary 파일은 리뷰하지 않음
- 현재는 단일 레포지토리 설치만 지원 (Organization-wide 미지원)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# 개발 의존성 설치
pip install -r requirements.txt
pip install pytest pytest-asyncio

# 테스트 실행
pytest tests/

# 코드 포맷팅 (선택사항)
pip install black isort
black .
isort .
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is experimental and provided as-is for learning and research purposes.

---

## Acknowledgments

- **LangGraph** by LangChain - Agentic workflow orchestration
- **Anthropic Claude** - Advanced reasoning capabilities
- **Google Gemini** - Fast and efficient LLM alternative
- GitHub Apps API documentation

---

## Contact & Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Built with ❤️ using LangGraph and LLMs**
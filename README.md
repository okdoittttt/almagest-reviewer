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

**Work in Progress**

- [x] 프로젝트 컨셉 및 구조 설계
- [x] LangGraph 학습 및 PoC
- [ ] GitHub App 생성
- [ ] Webhook → Workflow 연결
- [ ] PR 리뷰 자동 코멘트 MVP

---

## Tech Stack

- **Python**
- **LangGraph**
- **GitHub App / Webhooks**
- (Planned) FastAPI, Docker
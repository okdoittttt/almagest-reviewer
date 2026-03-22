# Almagest Reviewer — Frontend

GitHub PR AI 리뷰 시스템의 웹 대시보드입니다.
LangGraph 기반 AI 리뷰 결과를 시각화하고, 레포지토리·스킬을 관리합니다.

---

## 기술 스택

| 구분 | 라이브러리 | 버전 |
|------|-----------|------|
| UI 프레임워크 | React | 19.2.4 |
| 라우터 | React Router DOM | 7.13.1 |
| HTTP 클라이언트 | Axios | 1.13.6 |
| 스타일링 | Tailwind CSS | 4.2.2 |
| 마크다운 렌더링 | react-markdown | 10.1.0 |
| 빌드 도구 | Vite | 8.0.1 |
| 언어 | TypeScript | 5.9.3 |

---

## 디렉토리 구조

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios 인스턴스 및 인터셉터
│   │   └── types.ts           # API 응답 TypeScript 타입 정의
│   ├── components/
│   │   ├── Badge.tsx          # 재사용 배지 (RiskBadge, DecisionBadge 포함)
│   │   ├── Layout.tsx         # 공통 레이아웃 (헤더 + 네비게이션)
│   │   ├── ProtectedRoute.tsx # 인증 가드 (미로그인 시 /login 리다이렉트)
│   │   └── StatCard.tsx       # 대시보드 통계 카드
│   ├── context/
│   │   └── AuthContext.tsx    # 전역 인증 상태 관리 (React Context)
│   ├── pages/
│   │   ├── Dashboard.tsx          # 홈 — 통계 및 최근 PR 목록
│   │   ├── Login.tsx              # GitHub OAuth 로그인
│   │   ├── Repositories.tsx       # 레포지토리 목록 및 활성화 관리
│   │   ├── PullRequests.tsx       # PR 목록 (필터링 지원)
│   │   ├── PullRequestDetail.tsx  # PR 상세 — 리뷰 이력
│   │   ├── ReviewDetail.tsx       # 리뷰 상세 — AI 분석 결과 전체
│   │   └── Skills.tsx             # 레포지토리별 스킬 CRUD
│   ├── App.tsx                # React Router 라우팅 설정
│   ├── main.tsx               # 앱 진입점
│   └── index.css              # Tailwind 전역 스타일
├── public/                    # 정적 파일
├── vite.config.ts             # Vite 설정 (API 프록시 포함)
├── Dockerfile.dev             # 개발용 Docker 이미지
└── package.json
```

---

## 페이지 구성

### `/` — 대시보드
- 전체 통계 요약: 연동 레포지토리 수, PR 수, 리뷰 수(승인률), 평균 위험 점수
- 리뷰 결정 분포: APPROVE / REQUEST_CHANGES / COMMENT 건수
- 최근 10개 PR 테이블

### `/login` — GitHub OAuth 로그인
- GitHub App이 설치된 계정만 접근 가능
- httpOnly 쿠키 기반 세션 인증

### `/repositories` — 레포지토리 관리
- 연동된 레포지토리 카드 그리드 (반응형)
- 레포지토리별 PR 수, 스킬 수, 활성화 상태 표시
- 활성화 / 비활성화 토글

### `/pull-requests` — PR 목록
- 필터: 위험 레벨(LOW/MEDIUM/HIGH), 상태(open/closed/merged), 리뷰 결정
- 레포지토리별 필터 (`/repositories/:repoId/pull-requests`)

### `/pull-requests/:prId` — PR 상세
- PR 메타데이터: 제목, 브랜치, 작성자, 커밋 SHA
- 해당 PR의 리뷰 이력 목록

### `/reviews/:reviewId` — 리뷰 상세
- **PR 인텐트**: PR 유형, 복잡도, 요약, 주요 목적
- **위험 평가**: 위험 요소 목록 및 판단 근거
- **파일별 분석 아코디언**: 파일 상태(LGTM/NEEDS_IMPROVEMENT), 이슈 및 제안
- **최종 리뷰**: 마크다운 렌더링
- **코멘트**: 이슈/제안 항목별 처리 완료 체크

### `/repositories/:repoId/skills` — 스킬 관리
- 레포지토리별 리뷰 기준(스킬) 생성 / 수정 / 삭제
- 스킬 항목: 이름, 설명, 점검 항목(Focus Areas), 제외 패턴(Ignore Patterns)
- 활성화 / 비활성화 토글

---

## API 연동

Axios 인스턴스(`src/api/client.ts`)가 `/api` prefix로 백엔드와 통신합니다.

```
GET  /api/auth/me
POST /api/auth/logout
GET  /api/stats
GET  /api/repositories
PATCH /api/repositories/:id/toggle
GET  /api/pull-requests
GET  /api/pull-requests/:prId
GET  /api/pull-requests/:prId/reviews
GET  /api/reviews/:reviewId
GET  /api/reviews/:reviewId/comments
PATCH /api/reviews/:reviewId/comments/:commentId
GET  /api/repositories/:repoId/pull-requests
GET  /api/repositories/:repoId/skills
POST /api/repositories/:repoId/skills
PATCH /api/skills/:skillId
DELETE /api/skills/:skillId
```

---

## 개발 환경 실행

### 필요 조건

- Node.js 18+
- 백엔드 서버 실행 중 (기본 `http://localhost:8000`)

### 환경변수

```bash
# .env (선택 — 기본값: http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

### 실행

```bash
cd frontend
npm install
npm run dev        # 개발 서버 (HMR 포함, 기본 포트 5173)
npm run build      # 프로덕션 빌드 (타입 체크 포함)
npm run lint       # ESLint 검사
npm run preview    # 빌드 결과 로컬 미리보기
```

### Docker (개발)

```bash
docker compose up frontend
```

> Vite 개발 서버는 `host: 0.0.0.0`으로 설정되어 컨테이너 환경에서도 접근 가능합니다.

---

## 인증 흐름

1. 미인증 상태에서 보호된 라우트 접근 → `/login` 리다이렉트
2. GitHub OAuth 로그인 → 백엔드에서 httpOnly 쿠키 발급
3. Axios 인터셉터가 401 응답 감지 시 자동으로 `/login` 리다이렉트
4. `AuthContext`가 전역 사용자 상태를 관리하며 `useAuth()` 훅으로 접근

---

## 상태 관리

Redux나 Zustand 없이 **React 내장 기능**만 사용합니다.

- **전역**: `AuthContext` (인증 상태)
- **페이지별**: `useState` / `useEffect` (로딩, 필터, 모달 상태)

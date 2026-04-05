import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Docs — Almagest Reviewer',
  description: 'How to install, configure, and use Almagest Reviewer',
}

function SectionHeading({
  id,
  children,
}: {
  id: string
  children: React.ReactNode
}) {
  return (
    <h2
      id={id}
      data-section
      className="text-xl font-semibold text-primary mt-14 mb-4 scroll-mt-20 pb-2 border-b border-white/[0.07]"
    >
      {children}
    </h2>
  )
}

function SubHeading({
  id,
  children,
}: {
  id: string
  children: React.ReactNode
}) {
  return (
    <h3
      id={id}
      data-section
      className="text-base font-semibold text-primary mt-8 mb-3 scroll-mt-20"
    >
      {children}
    </h3>
  )
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-secondary text-sm leading-relaxed mb-3">{children}</p>
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="bg-surface2 text-accent px-1.5 py-0.5 rounded text-xs font-mono">
      {children}
    </code>
  )
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre className="bg-surface text-primary text-xs font-mono p-4 rounded-xl border border-white/[0.07] overflow-x-auto mb-4 leading-relaxed">
      {children}
    </pre>
  )
}

function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3 bg-accent/5 border border-accent/20 rounded-xl px-4 py-3 mb-4">
      <span className="text-accent text-sm mt-0.5 shrink-0">ℹ</span>
      <p className="text-secondary text-sm leading-relaxed">{children}</p>
    </div>
  )
}

function EnvRow({ name, description }: { name: string; description: string }) {
  return (
    <tr className="border-b border-white/[0.05]">
      <td className="py-2.5 pr-4 align-top">
        <code className="text-accent text-xs font-mono">{name}</code>
      </td>
      <td className="py-2.5 text-secondary text-sm">{description}</td>
    </tr>
  )
}

function TableRow({ cells }: { cells: string[] }) {
  return (
    <tr className="border-b border-white/[0.05]">
      {cells.map((cell, i) => (
        <td key={i} className={`py-2.5 pr-6 text-sm ${i === 0 ? 'font-mono text-xs text-primary' : 'text-secondary'}`}>
          {cell}
        </td>
      ))}
    </tr>
  )
}

export default function DocsPage() {
  return (
    <article className="max-w-3xl">

      {/* ── Introduction ────────────────────────────── */}
      <div id="introduction" data-section className="scroll-mt-20">
        <p className="text-xs font-semibold text-accent tracking-widest uppercase mb-3">
          Documentation
        </p>
        <h1
          className="text-3xl font-bold text-primary mb-4 leading-tight"
          style={{ fontFamily: 'var(--font-brand)' }}
        >
          Almagest Reviewer
        </h1>
        <P>
          <strong className="text-primary">Almagest Reviewer</strong>는 Pull Request 코드 리뷰를 자동화하기 위해 설계된
          GitHub App입니다. LangGraph를 사용해 리뷰 과정을 명시적인 상태 전이(State Transition), 루프(loop),
          그리고 인간 개입 지점(human-in-the-loop)으로 구성합니다.
        </P>
        <P>
          단순한 LLM 호출이나 규칙 기반 분석을 넘어, 코드 리뷰를 <em className="text-primary not-italic">에이전트의 사고 흐름(process)</em>으로
          모델링하는 것을 목표로 합니다.
        </P>

        <div className="grid grid-cols-3 gap-3 mt-6">
          {[
            { label: 'LangGraph', desc: 'Agentic workflow' },
            { label: 'Multi-LLM', desc: 'Anthropic · Gemini · Ollama' },
            { label: 'GitHub App', desc: 'Webhook 기반 실시간 리뷰' },
          ].map(item => (
            <div
              key={item.label}
              className="rounded-xl border border-white/[0.07] bg-surface p-4"
            >
              <p className="text-sm font-semibold text-primary mb-1">{item.label}</p>
              <p className="text-xs text-muted">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Getting Started ─────────────────────────── */}
      <SectionHeading id="getting-started">Getting Started</SectionHeading>

      <SubHeading id="prerequisites">Prerequisites</SubHeading>
      <ul className="list-disc pl-5 space-y-1.5 mb-4">
        {[
          'Python 3.11 이상',
          'Docker & Docker Compose',
          'GitHub App 생성 권한',
          'Anthropic API Key 또는 Google API Key (Ollama 사용 시 불필요)',
        ].map(item => (
          <li key={item} className="text-secondary text-sm">
            {item}
          </li>
        ))}
      </ul>

      <SubHeading id="installation">Installation</SubHeading>
      <P>레포지토리를 클론하고 환경변수 파일을 생성합니다.</P>
      <CodeBlock>{`git clone https://github.com/okdoittttt/almagest-reviewer.git
cd almagest-reviewer

cp .env.example .env`}</CodeBlock>

      <P>
        <Code>.env</Code> 파일을 열어 아래 항목들을 채웁니다.
      </P>

      <div className="overflow-x-auto mb-4">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/[0.07]">
              <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide pr-4">변수</th>
              <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide">설명</th>
            </tr>
          </thead>
          <tbody>
            <EnvRow name="GITHUB_APP_ID" description="생성한 GitHub App의 ID" />
            <EnvRow name="GITHUB_PRIVATE_KEY_PATH" description="다운로드한 .pem 키 파일 경로" />
            <EnvRow name="GITHUB_WEBHOOK_SECRET" description="GitHub App에 설정한 Webhook Secret" />
            <EnvRow name="LLM_PROVIDER" description="anthropic / google / ollama 중 하나" />
            <EnvRow name="ANTHROPIC_API_KEY" description="Anthropic 사용 시 필요" />
            <EnvRow name="GOOGLE_API_KEY" description="Google Gemini 사용 시 필요" />
            <EnvRow name="OLLAMA_BASE_URL" description="Ollama 서버 주소 (기본값: http://localhost:11434)" />
            <EnvRow name="GITHUB_CLIENT_ID" description="GitHub App OAuth 클라이언트 ID" />
            <EnvRow name="GITHUB_CLIENT_SECRET" description="GitHub App OAuth 클라이언트 Secret" />
            <EnvRow name="ALLOWED_GITHUB_USERS" description="대시보드 접근을 허용할 GitHub 로그인명 (콤마 구분)" />
            <EnvRow name="JWT_SECRET" description="세션 토큰 서명에 사용할 임의의 랜덤 문자열" />
          </tbody>
        </table>
      </div>

      <Note>
        <Code>DATABASE_URL</Code>은 Docker Compose 환경에서 자동으로 설정됩니다. 로컬 실행 시에는 <Code>.env</Code>에서 직접 지정하세요.
      </Note>

      <SubHeading id="running">Running the Server</SubHeading>
      <P>
        <Code>deploy.sh</Code>를 사용하면 이미지 빌드, 마이그레이션, 컨테이너 기동을 한 번에 처리합니다.
      </P>
      <CodeBlock>{`chmod +x deploy.sh
./deploy.sh deploy   # 빌드 → 마이그레이션 → 기동`}</CodeBlock>

      <div className="overflow-x-auto mb-4">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/[0.07]">
              <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide pr-6">명령어</th>
              <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide">설명</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['./deploy.sh deploy', '이미지 빌드 → 마이그레이션 → 전체 기동'],
              ['./deploy.sh up', '컨테이너 기동 (빌드 없음)'],
              ['./deploy.sh down', '컨테이너 종료'],
              ['./deploy.sh migrate', '마이그레이션만 실행 (alembic upgrade head)'],
              ['./deploy.sh status', '마이그레이션 버전 및 미적용 항목 확인'],
              ['./deploy.sh logs', '앱 로그 확인 (예: ./deploy.sh logs db)'],
            ].map(row => (
              <TableRow key={row[0]} cells={row} />
            ))}
          </tbody>
        </table>
      </div>

      <P>기동 후 접근 가능한 주소:</P>
      <ul className="list-disc pl-5 space-y-1 mb-4">
        <li className="text-secondary text-sm">
          <Code>http://localhost:8000</Code> — API 서버 + 웹 대시보드
        </li>
        <li className="text-secondary text-sm">
          <Code>http://localhost:5173</Code> — 프론트엔드 개발 서버 (hot-reload)
        </li>
      </ul>

      <Note>
        GitHub App 설정의 <strong className="text-primary">Callback URL</strong>에{' '}
        <Code>http://localhost:8000/api/auth/callback</Code>이 등록되어 있어야 웹 대시보드 로그인이 동작합니다.
      </Note>

      {/* ── Key Features ────────────────────────────── */}
      <SectionHeading id="features">Key Features</SectionHeading>

      <div className="grid gap-3">
        {[
          {
            title: 'Agentic Code Review',
            desc: '코드 분석 → 이슈 분류 → 리뷰 생성 과정을 LangGraph 그래프로 모델링합니다. 단순 체인이 아닌 상태 기반 에이전트 플로우로 체계적인 리뷰를 제공합니다.',
          },
          {
            title: 'Multi-LLM Provider',
            desc: 'Anthropic Claude, Google Gemini, Ollama(로컬)를 지원합니다. LLM_PROVIDER 환경변수 하나로 전환할 수 있습니다.',
          },
          {
            title: 'Intelligent Risk Assessment',
            desc: 'PR의 의도와 변경 규모를 분석해 위험도(LOW / MEDIUM / HIGH)를 자동으로 분류합니다. LOW로 판단된 PR은 상세 파일 리뷰를 건너뛰어 빠르게 처리합니다.',
          },
          {
            title: 'GitHub App Integration',
            desc: 'Pull Request 이벤트 기반으로 실시간 리뷰 코멘트를 작성합니다. 앱이 설치된 모든 레포지토리에서 자동으로 동작합니다.',
          },
          {
            title: 'Web Dashboard',
            desc: 'GitHub OAuth 로그인 기반 관리 UI를 제공합니다. 연동된 저장소, PR 리뷰 결과, 스킬 설정을 브라우저에서 확인하고 관리할 수 있습니다.',
          },
          {
            title: 'Multi-repo Support',
            desc: '여러 레포지토리에 앱을 설치하고 레포별 설정을 독립적으로 관리합니다. 웹훅 payload에서 installation_id를 동적으로 추출하므로 서버 수정 없이 연동이 완료됩니다.',
          },
        ].map(item => (
          <div
            key={item.title}
            className="rounded-xl border border-white/[0.07] bg-surface p-4"
          >
            <p className="text-sm font-semibold text-primary mb-1">{item.title}</p>
            <p className="text-sm text-secondary leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* ── Architecture ────────────────────────────── */}
      <SectionHeading id="architecture">Architecture</SectionHeading>
      <P>
        리뷰 프로세스는 4단계 그래프 노드로 구성됩니다. 위험도에 따라 일부 단계는 건너뜁니다.
      </P>

      <div className="space-y-3 mb-6">
        {[
          {
            step: '01',
            title: 'Intent Analysis',
            desc: 'PR 제목과 설명을 분석해 기능 추가 · 버그 수정 · 리팩토링 등의 의도를 파악합니다.',
          },
          {
            step: '02',
            title: 'Risk Classification',
            desc: '변경 규모와 중요도를 바탕으로 위험도(LOW / MEDIUM / HIGH)를 평가합니다. LOW이면 파일 리뷰를 건너뜁니다.',
          },
          {
            step: '03',
            title: 'File Review (병렬)',
            desc: 'MEDIUM / HIGH PR의 변경 파일을 병렬로 동시 리뷰합니다. 코드 품질, 보안, 성능, 가독성을 검토합니다.',
          },
          {
            step: '04',
            title: 'Review Summary',
            desc: '모든 분석을 종합해 최종 의견(APPROVE / REQUEST_CHANGES / COMMENT)과 요약문을 작성합니다. 리뷰가 불충분하면 파일 리뷰를 최대 2회 재실행합니다.',
          },
        ].map(item => (
          <div key={item.step} className="flex gap-4 rounded-xl border border-white/[0.07] bg-surface p-4">
            <span className="text-xs font-mono font-bold text-accent mt-0.5 shrink-0">{item.step}</span>
            <div>
              <p className="text-sm font-semibold text-primary mb-1">{item.title}</p>
              <p className="text-sm text-secondary leading-relaxed">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Multi-repo ───────────────────────────────── */}
      <SectionHeading id="multi-repo">Multi-repo Integration</SectionHeading>
      <P>
        웹훅 payload에서 <Code>installation_id</Code>를 동적으로 추출하므로, 서버 코드 수정 없이
        GitHub App 설치만으로 모든 레포지토리 연동이 완료됩니다.
      </P>

      <h4 className="text-sm font-semibold text-primary mt-6 mb-3">Step 1. GitHub App 추가 설치</h4>
      <P>
        GitHub → Settings → Applications → <Code>almagest-reviewer</Code> 옆 Configure 클릭 후
        Repository access에서 연동할 레포지토리를 추가합니다.
      </P>

      <h4 className="text-sm font-semibold text-primary mt-6 mb-3">Step 2. 자동 등록 확인</h4>
      <P>설치된 레포지토리에서 PR을 하나 열면 <Code>repositories</Code> 테이블에 자동 등록됩니다. 직접 확인하려면:</P>
      <CodeBlock>{`docker exec -it almagest-reviewer-db-1 psql -U almagest -d almagest_reviewer \\
  -c "SELECT id, owner, name, installation_id, is_active FROM repositories ORDER BY created_at DESC;"`}</CodeBlock>

      <h4 className="text-sm font-semibold text-primary mt-6 mb-3">리뷰 일시 중단</h4>
      <P>연동은 유지하되 리뷰를 멈추려면 <Code>is_active</Code>를 <Code>false</Code>로 변경합니다.</P>
      <CodeBlock>{`UPDATE repositories
SET is_active = false
WHERE owner = 'my-org' AND name = 'my-repo';`}</CodeBlock>

      {/* ── Self-hosted ──────────────────────────────── */}
      <SectionHeading id="self-hosted">Self-hosted Deployment</SectionHeading>
      <P>
        레포지토리를 fork해 자신만의 서버를 운영하는 절차입니다.
      </P>

      <div className="space-y-4">
        {[
          {
            step: 'Step 1',
            title: '레포지토리 Fork',
            content: 'GitHub에서 이 레포지토리를 fork합니다.',
          },
          {
            step: 'Step 2',
            title: 'GitHub App 신규 등록',
            content: (
              <>
                <P>GitHub → Settings → Developer settings → GitHub Apps → New GitHub App에서 앱을 생성합니다.</P>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-white/[0.07]">
                        <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide pr-6">항목</th>
                        <th className="pb-2 text-xs font-semibold text-muted uppercase tracking-wide">값</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ['Webhook URL', 'https://your-domain.com/webhook'],
                        ['Webhook secret', '임의의 비밀 문자열'],
                        ['Repository permissions', 'Pull requests: Read & write'],
                        ['Subscribe to events', 'Pull request'],
                      ].map(row => (
                        <TableRow key={row[0]} cells={row} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ),
          },
          {
            step: 'Step 3',
            title: '환경변수 설정 및 서버 배포',
            content: (
              <CodeBlock>{`cp .env.example .env
# .env 편집 후

docker compose up -d --build`}</CodeBlock>
            ),
          },
          {
            step: 'Step 4',
            title: 'GitHub App 설치',
            content: '생성한 GitHub App 페이지 → Install App → 리뷰를 받을 레포지토리 선택.',
          },
        ].map(item => (
          <div key={item.step} className="rounded-xl border border-white/[0.07] bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono font-bold text-accent">{item.step}</span>
              <p className="text-sm font-semibold text-primary">{item.title}</p>
            </div>
            {typeof item.content === 'string' ? (
              <P>{item.content}</P>
            ) : (
              item.content
            )}
          </div>
        ))}
      </div>

      {/* ── Troubleshooting ──────────────────────────── */}
      <SectionHeading id="troubleshooting">Troubleshooting</SectionHeading>

      <div className="space-y-3">
        {[
          {
            problem: '401 Unauthorized (Webhook)',
            solution: 'GITHUB_APP_ID 또는 Private Key 경로가 올바른지 확인하세요.',
          },
          {
            problem: 'Invalid Webhook Signature',
            solution: 'GITHUB_WEBHOOK_SECRET이 GitHub App 설정의 값과 일치하는지 확인하세요.',
          },
          {
            problem: 'LLM API Errors',
            solution: 'API Key가 유효한지, 할당량이 남아있는지 확인하세요.',
          },
          {
            problem: '로그인 후 403',
            solution: 'ALLOWED_GITHUB_USERS에 본인의 GitHub 로그인명이 포함되어 있는지 확인하세요.',
          },
          {
            problem: '로그인 콜백 오류',
            solution: 'GitHub App Settings의 Callback URL에 http://localhost:8000/api/auth/callback이 등록되어 있는지 확인하세요.',
          },
        ].map(item => (
          <div key={item.problem} className="rounded-xl border border-white/[0.07] bg-surface p-4">
            <p className="text-sm font-semibold text-danger mb-1">{item.problem}</p>
            <p className="text-sm text-secondary">{item.solution}</p>
          </div>
        ))}
      </div>

      {/* ── Roadmap ──────────────────────────────────── */}
      <SectionHeading id="roadmap">Roadmap</SectionHeading>
      <P>현재 기본 초석을 다진 단계이며, 실무 수준의 서비스로 고도화를 목표로 합니다.</P>

      <div className="space-y-2 mb-8">
        {[
          { done: true, label: 'Multi-repo Support', desc: 'PostgreSQL 기반 멀티테넌시 구조' },
          { done: true, label: 'Web Dashboard', desc: 'GitHub OAuth 로그인 기반 관리 UI' },
          { done: false, label: 'Skills', desc: '레포지토리별 리뷰 기준 커스터마이징' },
          { done: false, label: 'PR Triage', desc: '여러 PR 동시 접수 시 우선순위 자동 판단' },
          { done: false, label: 'Follow-up', desc: '리뷰 코멘트 반영 여부 추적 및 재검토' },
          { done: false, label: 'Human-in-the-loop Gate', desc: '고위험 PR은 사람 승인 후 코멘트 게시' },
          { done: false, label: 'Incremental Review', desc: '변경 라인(diff) 중심의 최적화 리뷰' },
          { done: false, label: 'Multi-model Ensemble', desc: '복수 LLM 의견 종합으로 정확도 향상' },
        ].map(item => (
          <div key={item.label} className="flex items-start gap-3 py-2.5 border-b border-white/[0.05]">
            <span className={`mt-0.5 text-sm shrink-0 ${item.done ? 'text-success' : 'text-muted'}`}>
              {item.done ? '✓' : '○'}
            </span>
            <div>
              <span className={`text-sm font-medium ${item.done ? 'text-primary' : 'text-secondary'}`}>
                {item.label}
              </span>
              <span className="text-sm text-muted ml-2">{item.desc}</span>
            </div>
          </div>
        ))}
      </div>

    </article>
  )
}

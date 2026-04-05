import Link from 'next/link'

const features = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
      </svg>
    ),
    title: 'Agentic Workflow',
    description: 'LangGraph 기반 상태 머신으로 코드 분석 → 이슈 분류 → 리뷰 생성을 명시적인 그래프로 모델링합니다.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
    title: 'Multi-LLM Support',
    description: 'Anthropic Claude, Google Gemini, Ollama(로컬) 등 다양한 LLM 프로바이더를 지원합니다.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
    title: 'Risk Assessment',
    description: 'PR 의도를 분석하고 위험도(LOW/MEDIUM/HIGH)를 자동 분류하여 중요한 변경사항을 놓치지 않습니다.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
      </svg>
    ),
    title: 'Human-in-the-Loop',
    description: '자동 판단과 사람의 개입을 자연스럽게 결합합니다. 리뷰 결과를 검토하고 false positive를 직접 dismiss할 수 있습니다.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z" />
      </svg>
    ),
    title: 'Custom Skills',
    description: '저장소별 리뷰 기준을 직접 정의하세요. 보안 점검, 성능 최적화, 코딩 컨벤션 등 다양한 스킬을 추가할 수 있습니다.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
      </svg>
    ),
    title: 'Web Dashboard',
    description: 'GitHub OAuth 로그인 기반 관리 UI. 연동 저장소, PR 리뷰 결과, 스킬 설정을 브라우저에서 한 눈에 확인하세요.',
  },
]

const steps = [
  {
    number: '01',
    title: 'GitHub App 설치',
    description: '리뷰가 필요한 저장소에 Almagest Reviewer GitHub App을 설치합니다.',
  },
  {
    number: '02',
    title: 'PR 오픈',
    description: 'Pull Request를 열거나 ready_for_review로 전환하면 자동으로 리뷰가 시작됩니다.',
  },
  {
    number: '03',
    title: '리뷰 확인',
    description: '대시보드에서 AI 리뷰 결과, 위험도 평가, 파일별 코멘트를 확인하고 관리합니다.',
  },
]

export default function LandingPage() {
  return (
    <div
      className="min-h-screen"
      style={{ background: '#09090b', color: '#fafafa' }}
    >
      {/* Nav */}
      <header
        className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 border-b border-white/[0.06]"
        style={{
          background: 'rgba(9, 9, 11, 0.8)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}
      >
        <span
          className="text-lg font-semibold text-white tracking-tight"
          style={{ fontFamily: 'var(--font-brand)' }}
        >
          Almagest Reviewer
        </span>
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/okdoittttt/almagest-reviewer"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-secondary hover:text-primary transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub
          </a>
          <Link
            href="/login"
            className="text-sm font-medium px-4 py-1.5 rounded-lg transition-all duration-150 text-white"
            style={{ background: '#2997ff' }}
          >
            대시보드 →
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section
        className="relative flex flex-col items-center text-center px-6 pt-28 pb-24"
        style={{
          background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(41, 151, 255, 0.12) 0%, transparent 70%)',
        }}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/30 bg-accent/5 text-xs text-accent mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
          LangGraph · Agentic Workflow · GitHub App
        </div>

        <h1
          className="text-5xl md:text-6xl font-bold text-white leading-tight max-w-3xl"
          style={{ fontFamily: 'var(--font-brand)', letterSpacing: '-0.02em' }}
        >
          AI가 코드 리뷰를
          <br />
          <span style={{ color: '#2997ff' }}>에이전트처럼</span> 생각합니다
        </h1>

        <p className="mt-6 text-lg text-secondary max-w-xl leading-relaxed">
          단순한 LLM 호출이 아닙니다. LangGraph 기반 상태 전이 그래프로
          코드 분석부터 리뷰 생성까지 전 과정을 명시적으로 모델링합니다.
        </p>

        <div className="flex items-center gap-4 mt-10">
          <Link
            href="/login"
            className="px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-150 hover:opacity-90"
            style={{ background: '#2997ff' }}
          >
            무료로 시작하기
          </Link>
          <a
            href="https://github.com/okdoittttt/almagest-reviewer"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-xl text-sm font-medium border border-white/[0.12] text-secondary hover:text-primary hover:border-white/20 transition-all duration-150 flex items-center gap-2"
            style={{ background: 'rgba(255,255,255,0.04)' }}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub에서 보기
          </a>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <h2
            className="text-3xl font-bold text-white"
            style={{ fontFamily: 'var(--font-brand)', letterSpacing: '-0.01em' }}
          >
            기능
          </h2>
          <p className="mt-3 text-secondary">코드 리뷰의 모든 단계를 자동화합니다</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(f => (
            <div
              key={f.title}
              className="rounded-2xl border border-white/[0.07] p-6 space-y-3 hover:border-white/[0.14] transition-all duration-200"
              style={{ background: 'rgba(24, 24, 27, 0.6)' }}
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-accent" style={{ background: 'rgba(41, 151, 255, 0.1)' }}>
                {f.icon}
              </div>
              <h3 className="font-semibold text-white">{f.title}</h3>
              <p className="text-sm text-secondary leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2
              className="text-3xl font-bold text-white"
              style={{ fontFamily: 'var(--font-brand)', letterSpacing: '-0.01em' }}
            >
              시작하는 방법
            </h2>
            <p className="mt-3 text-secondary">3단계로 AI 코드 리뷰를 시작하세요</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map(step => (
              <div key={step.number} className="text-center space-y-3">
                <div
                  className="w-12 h-12 rounded-2xl flex items-center justify-center text-accent font-bold text-lg mx-auto"
                  style={{ background: 'rgba(41, 151, 255, 0.1)', border: '1px solid rgba(41, 151, 255, 0.2)' }}
                >
                  {step.number}
                </div>
                <h3 className="font-semibold text-white">{step.title}</h3>
                <p className="text-sm text-secondary leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 text-center">
        <div
          className="max-w-2xl mx-auto rounded-3xl border border-white/[0.08] p-12 space-y-6"
          style={{
            background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(41, 151, 255, 0.08) 0%, rgba(24, 24, 27, 0.8) 70%)',
          }}
        >
          <h2
            className="text-3xl font-bold text-white"
            style={{ fontFamily: 'var(--font-brand)', letterSpacing: '-0.01em' }}
          >
            지금 바로 시작하세요
          </h2>
          <p className="text-secondary">
            GitHub 계정으로 로그인하고 저장소를 연결하면 바로 사용할 수 있습니다.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-150 hover:opacity-90"
            style={{ background: '#2997ff' }}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub으로 시작하기
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-white/[0.06] text-center">
        <p className="text-xs text-muted">
          © 2025 Almagest Reviewer · Open Source ·{' '}
          <a
            href="https://github.com/okdoittttt/almagest-reviewer"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-secondary transition-colors"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  )
}

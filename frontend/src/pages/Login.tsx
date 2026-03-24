import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  const handleLogin = () => {
    window.location.href = '/api/auth/login'
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{
        background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(41, 151, 255, 0.08) 0%, #09090b 60%)',
      }}
    >
      <div
        className="rounded-2xl border border-white/[0.08] p-10 flex flex-col items-center gap-7 w-full max-w-sm"
        style={{
          background: 'rgba(24, 24, 27, 0.8)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
        }}
      >
        <div className="text-center space-y-2">
          <h1
            className="text-2xl text-primary tracking-tight"
            style={{ fontFamily: 'var(--font-brand)' }}
          >
            Almagest Reviewer
          </h1>
          <p className="text-sm text-secondary">
            GitHub 계정으로 로그인하여 리뷰 대시보드에 접근하세요.
          </p>
        </div>

        <button
          onClick={handleLogin}
          className="w-full flex items-center justify-center gap-3 font-medium py-3 px-5 rounded-xl transition-all duration-150 border border-white/[0.12] text-primary hover:bg-white/10 hover:border-white/20"
          style={{ background: 'rgba(255,255,255,0.06)' }}
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          GitHub으로 로그인
        </button>

        <p className="text-xs text-muted text-center">
          GitHub App 설치 계정만 접근 가능합니다.
        </p>
      </div>
    </div>
  )
}

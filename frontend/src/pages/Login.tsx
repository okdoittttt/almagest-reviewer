import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const { token } = useAuth()
  const navigate = useNavigate()

  // 이미 로그인된 경우 대시보드로 이동
  useEffect(() => {
    if (token) navigate('/', { replace: true })
  }, [token, navigate])

  const handleLogin = () => {
    window.location.href = '/api/auth/login'
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 flex flex-col items-center gap-6 w-full max-w-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Almagest Reviewer</h1>
          <p className="text-sm text-gray-500 mt-2">GitHub 계정으로 로그인하여 리뷰 대시보드에 접근하세요.</p>
        </div>

        <button
          onClick={handleLogin}
          className="w-full flex items-center justify-center gap-3 bg-gray-900 hover:bg-gray-700 text-white font-medium py-3 px-5 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          GitHub으로 로그인
        </button>

        <p className="text-xs text-gray-400 text-center">
          GitHub App 설치 계정만 접근 가능합니다.
        </p>
      </div>
    </div>
  )
}

import { createContext, useContext, useEffect, useState } from 'react'
import { getMe } from '../api/client'

const TOKEN_KEY = 'almagest_token'

interface AuthState {
  token: string | null
  user: { login: string } | null
  loading: boolean
  logout: () => void
}

const AuthContext = createContext<AuthState>({
  token: null,
  user: null,
  loading: true,
  logout: () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<{ login: string } | null>(null)
  const [loading, setLoading] = useState(true)

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(u => setUser(u))
      .catch(() => {
        // 토큰이 만료되었거나 유효하지 않으면 로그아웃
        logout()
      })
      .finally(() => setLoading(false))
  }, [token])

  // URL에서 ?token= 파라미터를 읽어 저장 (OAuth 콜백 후)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const t = params.get('token')
    if (t) {
      localStorage.setItem(TOKEN_KEY, t)
      setToken(t)
      // URL에서 token 파라미터 제거
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

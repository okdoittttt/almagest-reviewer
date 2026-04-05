'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

interface AuthState {
  user: { login: string } | null
  loading: boolean
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  logout: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ login: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get<{ login: string }>('/api/auth/me', { withCredentials: true })
      .then(r => setUser(r.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const logout = async () => {
    await axios.post('/api/auth/logout', null, { withCredentials: true })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

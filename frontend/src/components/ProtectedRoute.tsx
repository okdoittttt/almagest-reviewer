import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        인증 확인 중...
      </div>
    )
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />
}

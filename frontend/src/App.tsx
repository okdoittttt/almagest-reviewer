import { Outlet, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { PullRequestDetail } from './pages/PullRequestDetail'
import { PullRequests } from './pages/PullRequests'
import { Repositories } from './pages/Repositories'
import { ReviewDetail } from './pages/ReviewDetail'
import { Skills } from './pages/Skills'

function AppLayout() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* 공개 라우트 */}
          <Route path="/login" element={<Login />} />

          {/* 보호된 라우트 — 미인증 시 /login 으로 리다이렉트 */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="repositories" element={<Repositories />} />
              <Route path="repositories/:repoId/pull-requests" element={<PullRequests />} />
              <Route path="repositories/:repoId/skills" element={<Skills />} />
              <Route path="pull-requests" element={<PullRequests />} />
              <Route path="pull-requests/:prId" element={<PullRequestDetail />} />
              <Route path="reviews/:reviewId" element={<ReviewDetail />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  )
}

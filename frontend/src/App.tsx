import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { PullRequestDetail } from './pages/PullRequestDetail'
import { PullRequests } from './pages/PullRequests'
import { Repositories } from './pages/Repositories'
import { ReviewDetail } from './pages/ReviewDetail'
import { Skills } from './pages/Skills'

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/repositories" element={<Repositories />} />
          <Route path="/repositories/:repoId/pull-requests" element={<PullRequests />} />
          <Route path="/repositories/:repoId/skills" element={<Skills />} />
          <Route path="/pull-requests" element={<PullRequests />} />
          <Route path="/pull-requests/:prId" element={<PullRequestDetail />} />
          <Route path="/reviews/:reviewId" element={<ReviewDetail />} />
        </Routes>
      </Layout>
    </Router>
  )
}

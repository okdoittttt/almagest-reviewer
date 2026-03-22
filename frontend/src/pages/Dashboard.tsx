import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPullRequests, getStats } from '../api/client'
import type { PullRequest, Stats } from '../api/types'
import { RiskBadge } from '../components/Badge'
import { StatCard } from '../components/StatCard'

function fmt(dt: string) {
  return new Date(dt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [prs, setPrs] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStats(), getPullRequests({ limit: 10 })])
      .then(([s, p]) => {
        setStats(s)
        setPrs(p)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-400 mt-10 text-center">불러오는 중...</div>

  const approvalRate =
    stats && stats.total_reviews > 0
      ? Math.round((stats.approve_count / stats.total_reviews) * 100)
      : 0

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="연동 저장소" value={stats?.total_repositories ?? 0} sub={`활성 ${stats?.active_repositories ?? 0}개`} />
        <StatCard label="총 Pull Request" value={stats?.total_pull_requests ?? 0} />
        <StatCard label="총 리뷰" value={stats?.total_reviews ?? 0} sub={`승인률 ${approvalRate}%`} />
        <StatCard
          label="평균 위험 점수"
          value={stats?.avg_risk_score != null ? stats.avg_risk_score.toFixed(2) : 'N/A'}
          sub="0.0 ~ 1.0"
        />
      </div>

      {/* Review Decision Breakdown */}
      {stats && stats.total_reviews > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">리뷰 결정 현황</h2>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-green-400 inline-block" />
              <span className="text-sm text-gray-600">APPROVE {stats.approve_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400 inline-block" />
              <span className="text-sm text-gray-600">REQUEST_CHANGES {stats.request_changes_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-400 inline-block" />
              <span className="text-sm text-gray-600">COMMENT {stats.comment_count}</span>
            </div>
          </div>
        </div>
      )}

      {/* Recent PRs */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">최근 Pull Request</h2>
          <Link to="/pull-requests" className="text-xs text-indigo-600 hover:underline">전체 보기</Link>
        </div>
        {prs.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">아직 리뷰된 PR이 없습니다.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                <th className="px-5 py-2 font-medium">저장소</th>
                <th className="px-5 py-2 font-medium">PR</th>
                <th className="px-5 py-2 font-medium">위험도</th>
                <th className="px-5 py-2 font-medium">리뷰 수</th>
                <th className="px-5 py-2 font-medium">날짜</th>
              </tr>
            </thead>
            <tbody>
              {prs.map(pr => (
                <tr key={pr.id} className="hover:bg-gray-50 border-b border-gray-50 last:border-0">
                  <td className="px-5 py-3 text-gray-500 text-xs">{pr.repo_owner}/{pr.repo_name}</td>
                  <td className="px-5 py-3">
                    <Link
                      to={`/pull-requests/${pr.id}`}
                      className="text-indigo-600 hover:underline font-medium"
                    >
                      #{pr.pr_number} {pr.title}
                    </Link>
                  </td>
                  <td className="px-5 py-3"><RiskBadge level={pr.risk_level} /></td>
                  <td className="px-5 py-3 text-gray-600">{pr.review_count}</td>
                  <td className="px-5 py-3 text-gray-400 text-xs">{fmt(pr.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

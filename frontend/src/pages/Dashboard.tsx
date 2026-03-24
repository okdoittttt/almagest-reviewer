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

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>

  const approvalRate =
    stats && stats.total_reviews > 0
      ? Math.round((stats.approve_count / stats.total_reviews) * 100)
      : 0

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-primary">Dashboard</h1>

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
        <div className="bg-surface rounded-xl border border-white/[0.07] p-5">
          <h2 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-4">리뷰 결정 현황</h2>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-success inline-block" />
              <span className="text-sm text-secondary">APPROVE <span className="text-primary font-medium">{stats.approve_count}</span></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-danger inline-block" />
              <span className="text-sm text-secondary">REQUEST_CHANGES <span className="text-primary font-medium">{stats.request_changes_count}</span></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block" />
              <span className="text-sm text-secondary">COMMENT <span className="text-primary font-medium">{stats.comment_count}</span></span>
            </div>
          </div>
        </div>
      )}

      {/* Recent PRs */}
      <div className="bg-surface rounded-xl border border-white/[0.07]">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.07]">
          <h2 className="text-xs font-semibold text-secondary uppercase tracking-wider">최근 Pull Request</h2>
          <Link to="/pull-requests" className="text-xs text-accent hover:text-accent/80 transition-colors">전체 보기</Link>
        </div>
        {prs.length === 0 ? (
          <p className="text-sm text-muted text-center py-10">아직 리뷰된 PR이 없습니다.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-white/[0.05]">
                <th className="px-5 py-3 font-medium">저장소</th>
                <th className="px-5 py-3 font-medium">PR</th>
                <th className="px-5 py-3 font-medium">위험도</th>
                <th className="px-5 py-3 font-medium">리뷰 수</th>
                <th className="px-5 py-3 font-medium">날짜</th>
              </tr>
            </thead>
            <tbody>
              {prs.map(pr => (
                <tr key={pr.id} className="hover:bg-white/[0.02] border-b border-white/[0.04] last:border-0 transition-colors">
                  <td className="px-5 py-3 text-muted text-xs">{pr.repo_owner}/{pr.repo_name}</td>
                  <td className="px-5 py-3">
                    <Link
                      to={`/pull-requests/${pr.id}`}
                      className="text-accent hover:text-accent/80 font-medium transition-colors"
                    >
                      #{pr.pr_number} {pr.title}
                    </Link>
                  </td>
                  <td className="px-5 py-3"><RiskBadge level={pr.risk_level} /></td>
                  <td className="px-5 py-3 text-secondary">{pr.review_count}</td>
                  <td className="px-5 py-3 text-muted text-xs">{fmt(pr.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

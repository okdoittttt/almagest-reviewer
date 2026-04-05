'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { getRepoPullRequests } from '@/api/client'
import type { PullRequest } from '@/api/types'
import { Badge, RiskBadge } from '@/components/Badge'

function fmt(dt: string) {
  return new Date(dt).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const RISK_OPTIONS = ['', 'LOW', 'MEDIUM', 'HIGH']
const STATE_OPTIONS = ['', 'open', 'closed', 'merged']

const selectClass = [
  'text-sm rounded-lg px-3 py-1.5 transition-colors duration-150',
  'bg-surface2 text-secondary border border-white/[0.07]',
  'hover:border-white/20 focus:outline-none focus:border-accent/50',
].join(' ')

export default function RepoPullRequestsPage() {
  const { repoId } = useParams<{ repoId: string }>()
  const [prs, setPrs] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [riskFilter, setRiskFilter] = useState('')
  const [stateFilter, setStateFilter] = useState('')

  useEffect(() => {
    if (!repoId) return
    setLoading(true)
    getRepoPullRequests(Number(repoId), {
      risk_level: riskFilter || undefined,
      state: stateFilter || undefined,
    })
      .then(data => setPrs(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [riskFilter, stateFilter, repoId])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-primary">Pull Requests</h1>

      <div className="flex flex-wrap gap-3">
        <select className={selectClass} value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          {RISK_OPTIONS.map(v => <option key={v} value={v}>{v || '위험도 전체'}</option>)}
        </select>
        <select className={selectClass} value={stateFilter} onChange={e => setStateFilter(e.target.value)}>
          {STATE_OPTIONS.map(v => <option key={v} value={v}>{v || '상태 전체'}</option>)}
        </select>
      </div>

      <div className="bg-surface rounded-xl border border-white/[0.07] overflow-hidden">
        {loading ? (
          <p className="text-secondary text-center py-10">불러오는 중...</p>
        ) : prs.length === 0 ? (
          <p className="text-muted text-center py-10">해당하는 PR이 없습니다.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-white/[0.07] bg-surface2/50">
                <th className="px-5 py-3 font-medium">PR</th>
                <th className="px-5 py-3 font-medium">작성자</th>
                <th className="px-5 py-3 font-medium">상태</th>
                <th className="px-5 py-3 font-medium">위험도</th>
                <th className="px-5 py-3 font-medium">리뷰</th>
                <th className="px-5 py-3 font-medium">업데이트</th>
              </tr>
            </thead>
            <tbody>
              {prs.map(pr => (
                <tr key={pr.id} className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3 max-w-xs">
                    <Link href={`/pull-requests/${pr.id}`} className="text-accent hover:text-accent/80 font-medium transition-colors">
                      #{pr.pr_number}
                    </Link>{' '}
                    <span className="text-secondary truncate">{pr.title}</span>
                  </td>
                  <td className="px-5 py-3 text-secondary">{pr.author_login ?? '-'}</td>
                  <td className="px-5 py-3">
                    <Badge label={pr.state} variant={pr.state === 'open' ? 'green' : pr.state === 'merged' ? 'purple' : 'gray'} />
                  </td>
                  <td className="px-5 py-3"><RiskBadge level={pr.risk_level} /></td>
                  <td className="px-5 py-3 text-secondary">{pr.review_count}개</td>
                  <td className="px-5 py-3 text-muted text-xs whitespace-nowrap">{fmt(pr.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getPullRequests, getRepoPullRequests } from '../api/client'
import type { PullRequest } from '../api/types'
import { Badge, RiskBadge } from '../components/Badge'

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
const DECISION_OPTIONS = ['', 'APPROVE', 'REQUEST_CHANGES', 'COMMENT']

export function PullRequests() {
  const { repoId } = useParams()
  const [prs, setPrs] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [riskFilter, setRiskFilter] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('')

  const fetchPrs = async () => {
    setLoading(true)
    const params = {
      risk_level: riskFilter || undefined,
      state: stateFilter || undefined,
      review_decision: decisionFilter || undefined,
    }
    try {
      const data = repoId
        ? await getRepoPullRequests(Number(repoId), params)
        : await getPullRequests({ ...params, limit: 100 })
      setPrs(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPrs() }, [riskFilter, stateFilter, decisionFilter, repoId])

  const select = 'text-sm border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700'

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Pull Requests</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select className={select} value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          {RISK_OPTIONS.map(v => <option key={v} value={v}>{v || '위험도 전체'}</option>)}
        </select>
        <select className={select} value={stateFilter} onChange={e => setStateFilter(e.target.value)}>
          {STATE_OPTIONS.map(v => <option key={v} value={v}>{v || '상태 전체'}</option>)}
        </select>
        {!repoId && (
          <select className={select} value={decisionFilter} onChange={e => setDecisionFilter(e.target.value)}>
            {DECISION_OPTIONS.map(v => <option key={v} value={v}>{v || '리뷰 결정 전체'}</option>)}
          </select>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <p className="text-gray-400 text-center py-10">불러오는 중...</p>
        ) : prs.length === 0 ? (
          <p className="text-gray-400 text-center py-10">해당하는 PR이 없습니다.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100 bg-gray-50">
                <th className="px-5 py-3 font-medium">저장소</th>
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
                <tr key={pr.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                  <td className="px-5 py-3 text-gray-400 text-xs whitespace-nowrap">
                    {pr.repo_owner}/{pr.repo_name}
                  </td>
                  <td className="px-5 py-3 max-w-xs">
                    <Link
                      to={`/pull-requests/${pr.id}`}
                      className="text-indigo-600 hover:underline font-medium"
                    >
                      #{pr.pr_number}
                    </Link>{' '}
                    <span className="text-gray-700 truncate">{pr.title}</span>
                  </td>
                  <td className="px-5 py-3 text-gray-500">{pr.author_login ?? '-'}</td>
                  <td className="px-5 py-3">
                    <Badge
                      label={pr.state}
                      variant={pr.state === 'open' ? 'green' : pr.state === 'merged' ? 'purple' : 'gray'}
                    />
                  </td>
                  <td className="px-5 py-3"><RiskBadge level={pr.risk_level} /></td>
                  <td className="px-5 py-3 text-gray-500">{pr.review_count}개</td>
                  <td className="px-5 py-3 text-gray-400 text-xs whitespace-nowrap">{fmt(pr.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

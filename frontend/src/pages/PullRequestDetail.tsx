import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getPullRequest, getPullRequestReviews } from '../api/client'
import type { PullRequest, Review } from '../api/types'
import { DecisionBadge, RiskBadge } from '../components/Badge'

function fmt(dt: string) {
  return new Date(dt).toLocaleString('ko-KR')
}

export function PullRequestDetail() {
  const { prId } = useParams()
  const [pr, setPr] = useState<PullRequest | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!prId) return
    Promise.all([getPullRequest(Number(prId)), getPullRequestReviews(Number(prId))])
      .then(([p, r]) => {
        setPr(p)
        setReviews(r)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [prId])

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>
  if (!pr) return <div className="text-danger mt-10 text-center">PR을 찾을 수 없습니다.</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Link to="/pull-requests" className="hover:text-accent transition-colors">Pull Requests</Link>
        <span>/</span>
        <span className="text-secondary">{pr.repo_owner}/{pr.repo_name} #{pr.pr_number}</span>
      </div>

      {/* PR 정보 */}
      <div className="bg-surface rounded-xl border border-white/[0.07] p-6 space-y-5">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-xl font-bold text-primary">{pr.title ?? `PR #${pr.pr_number}`}</h1>
          <RiskBadge level={pr.risk_level} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-muted text-xs uppercase tracking-wider mb-1">작성자</p>
            <p className="font-medium text-secondary">{pr.author_login ?? '-'}</p>
          </div>
          <div>
            <p className="text-muted text-xs uppercase tracking-wider mb-1">브랜치</p>
            <p className="font-medium text-secondary text-xs">{pr.head_branch} → {pr.base_branch}</p>
          </div>
          <div>
            <p className="text-muted text-xs uppercase tracking-wider mb-1">커밋 SHA</p>
            <p className="font-mono text-xs text-secondary">{pr.head_sha.slice(0, 8)}</p>
          </div>
          <div>
            <p className="text-muted text-xs uppercase tracking-wider mb-1">상태</p>
            <p className="font-medium text-secondary">{pr.state}</p>
          </div>
        </div>
      </div>

      {/* 리뷰 목록 */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-primary">리뷰 이력</h2>
        <span className="text-xs text-muted">{reviews.length}개</span>
      </div>
      {reviews.length === 0 ? (
        <p className="text-muted">아직 리뷰가 없습니다.</p>
      ) : (
        <div className="space-y-3">
          {reviews.map(review => (
            <Link
              key={review.id}
              to={`/reviews/${review.id}`}
              className="block bg-surface rounded-xl border border-white/[0.07] p-5 hover:border-white/[0.2] hover:bg-white/[0.02] transition-all duration-150"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <DecisionBadge decision={review.review_decision} />
                  <RiskBadge level={review.risk_level} />
                  {review.risk_score != null && (
                    <span className="text-xs text-muted">score: {review.risk_score.toFixed(2)}</span>
                  )}
                </div>
                <span className="text-xs text-muted">{fmt(review.created_at)}</span>
              </div>
              <p className="text-xs text-muted mt-2 font-mono">{review.head_sha.slice(0, 12)}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getReview, getReviewComments, updateCommentAddressed } from '../api/client'
import type { Review, ReviewComment } from '../api/types'
import { Badge, DecisionBadge, RiskBadge } from '../components/Badge'

type FileReview = {
  filename?: string
  status?: string
  summary?: string
  issues?: { description?: string; severity?: string }[]
  suggestions?: { description?: string }[]
}

export function ReviewDetail() {
  const { reviewId } = useParams()
  const [review, setReview] = useState<Review | null>(null)
  const [comments, setComments] = useState<ReviewComment[]>([])
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!reviewId) return
    Promise.all([getReview(Number(reviewId)), getReviewComments(Number(reviewId))])
      .then(([r, c]) => {
        setReview(r)
        setComments(c)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [reviewId])

  const toggleExpand = (idx: number) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  const handleAddressed = async (comment: ReviewComment) => {
    if (!review) return
    const updated = await updateCommentAddressed(review.id, comment.id, !comment.is_addressed)
    setComments(prev => prev.map(c => (c.id === updated.id ? updated : c)))
  }

  if (loading) return <div className="text-gray-400 mt-10 text-center">불러오는 중...</div>
  if (!review) return <div className="text-red-400 mt-10 text-center">리뷰를 찾을 수 없습니다.</div>

  const fileReviews: FileReview[] = Array.isArray(review.file_reviews) ? (review.file_reviews as FileReview[]) : []
  const intent = review.pr_intent as Record<string, unknown> | null | undefined
  const risk = review.risk_assessment as Record<string, unknown> | null | undefined

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/pull-requests" className="hover:text-indigo-600">Pull Requests</Link>
        <span>/</span>
        <Link to={`/pull-requests/${review.pull_request_id}`} className="hover:text-indigo-600">
          PR #{review.pull_request_id}
        </Link>
        <span>/</span>
        <span>Review #{review.id}</span>
      </div>

      {/* 리뷰 헤더 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <DecisionBadge decision={review.review_decision} />
          <RiskBadge level={review.risk_level} />
          {review.risk_score != null && (
            <span className="text-sm text-gray-500">Risk Score: <strong>{review.risk_score.toFixed(2)}</strong></span>
          )}
          {review.retry_count > 0 && (
            <Badge label={`재시도 ${review.retry_count}회`} variant="yellow" />
          )}
        </div>
        <p className="text-xs text-gray-400 font-mono">커밋: {review.head_sha}</p>
      </div>

      {/* PR Intent + Risk Assessment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {intent && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">PR Intent</h3>
            <div className="space-y-2 text-sm">
              {intent.type != null && <div><span className="text-gray-400">타입: </span><Badge label={String(intent.type)} variant="blue" /></div>}
              {intent.complexity != null && <div><span className="text-gray-400">복잡도: </span><strong>{String(intent.complexity)}</strong></div>}
              {intent.summary != null && <p className="text-gray-700">{String(intent.summary)}</p>}
              {Array.isArray(intent.key_objectives) && intent.key_objectives.length > 0 && (
                <ul className="list-disc pl-4 text-gray-600 space-y-0.5">
                  {intent.key_objectives.map((o, i) => <li key={i}>{String(o)}</li>)}
                </ul>
              )}
            </div>
          </div>
        )}
        {risk && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Risk Assessment</h3>
            <div className="space-y-2 text-sm">
              {risk.reasoning != null && <p className="text-gray-700">{String(risk.reasoning)}</p>}
              {Array.isArray(risk.factors) && risk.factors.length > 0 && (
                <div>
                  <p className="text-gray-400 mb-1">위험 요소</p>
                  <ul className="list-disc pl-4 text-gray-600 space-y-0.5">
                    {risk.factors.map((f, i) => <li key={i}>{String(f)}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Final Review Markdown */}
      {review.final_review && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Final Review</h3>
          <div className="prose text-sm text-gray-700 max-w-none">
            <ReactMarkdown>{review.final_review}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* File Reviews 아코디언 */}
      {fileReviews.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">파일별 리뷰 ({fileReviews.length}개 파일)</h3>
          {fileReviews.map((fr, idx) => {
            const isOpen = expanded.has(idx)
            const statusColor = fr.status === 'LGTM' ? 'green' : fr.status === 'NEEDS_IMPROVEMENT' ? 'yellow' : 'gray'
            return (
              <div key={idx} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <button
                  onClick={() => toggleExpand(idx)}
                  className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <Badge label={fr.status ?? 'UNKNOWN'} variant={statusColor as 'green' | 'yellow' | 'gray'} />
                    <span className="text-sm font-mono text-gray-700">{fr.filename}</span>
                  </div>
                  <span className="text-gray-400 text-xs">{isOpen ? '▲' : '▼'}</span>
                </button>
                {isOpen && (
                  <div className="border-t border-gray-100 px-5 py-4 space-y-3">
                    {fr.summary && <p className="text-sm text-gray-600">{fr.summary}</p>}
                    {fr.issues && fr.issues.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-red-600 mb-1">이슈</p>
                        <ul className="space-y-1">
                          {fr.issues.map((issue, i) => (
                            <li key={i} className="text-sm text-gray-700 flex gap-2">
                              {issue.severity && <Badge label={issue.severity} variant="red" />}
                              <span>{issue.description}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {fr.suggestions && fr.suggestions.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-blue-600 mb-1">제안</p>
                        <ul className="space-y-1">
                          {fr.suggestions.map((s, i) => (
                            <li key={i} className="text-sm text-gray-700">{s.description}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Review Comments */}
      {comments.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">코멘트 ({comments.length}개)</h3>
          {comments.map(comment => (
            <div
              key={comment.id}
              className={`bg-white rounded-xl border p-4 flex items-start gap-3 ${
                comment.is_addressed ? 'border-green-200 opacity-60' : 'border-gray-200'
              }`}
            >
              <input
                type="checkbox"
                checked={comment.is_addressed}
                onChange={() => handleAddressed(comment)}
                className="mt-0.5 cursor-pointer"
              />
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <Badge
                    label={comment.comment_type}
                    variant={comment.comment_type === 'issue' ? 'red' : 'blue'}
                  />
                  {comment.filename && (
                    <span className="text-xs font-mono text-gray-400">{comment.filename}</span>
                  )}
                </div>
                <p className="text-sm text-gray-700">{comment.body}</p>
                {comment.is_addressed && comment.addressed_at && (
                  <p className="text-xs text-green-500">
                    처리됨: {new Date(comment.addressed_at).toLocaleString('ko-KR')}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {review.errors && (review.errors as unknown[]).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-red-700 mb-2">오류</h3>
          <ul className="space-y-1">
            {(review.errors as unknown[]).map((e, i) => (
              <li key={i} className="text-sm text-red-600">{String(e)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

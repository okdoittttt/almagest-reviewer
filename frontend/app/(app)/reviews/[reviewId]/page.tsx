'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import { getReview, getReviewComments, updateCommentAddressed, createCommentReply, dismissComment, undismissComment } from '@/api/client'
import type { Review, ReviewComment } from '@/api/types'
import { Badge, DecisionBadge, RiskBadge, TriggerSourceBadge } from '@/components/Badge'

type FileReview = {
  filename?: string
  status?: string
  summary?: string
  issues?: { description?: string; severity?: string }[]
  suggestions?: { description?: string }[]
}

export default function ReviewDetailPage() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const [review, setReview] = useState<Review | null>(null)
  const [comments, setComments] = useState<ReviewComment[]>([])
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyText, setReplyText] = useState('')
  const [submittingReply, setSubmittingReply] = useState(false)
  const [dismissingComment, setDismissingComment] = useState<number | null>(null)
  const [dismissReason, setDismissReason] = useState('')
  const [submittingDismiss, setSubmittingDismiss] = useState(false)

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

  const handleDismissSubmit = async (comment: ReviewComment) => {
    if (!review) return
    setSubmittingDismiss(true)
    try {
      const updated = await dismissComment(review.id, comment.id, dismissReason.trim() || null)
      setComments(prev => prev.map(c => (c.id === updated.id ? updated : c)))
      const refreshed = await getReview(review.id)
      setReview(refreshed)
      setDismissingComment(null)
      setDismissReason('')
    } catch (e) {
      console.error(e)
    } finally {
      setSubmittingDismiss(false)
    }
  }

  const handleUndismiss = async (comment: ReviewComment) => {
    if (!review) return
    try {
      const updated = await undismissComment(review.id, comment.id)
      setComments(prev => prev.map(c => (c.id === updated.id ? updated : c)))
      const refreshed = await getReview(review.id)
      setReview(refreshed)
    } catch (e) {
      console.error(e)
    }
  }

  const handleReplySubmit = async (commentId: number) => {
    if (!review || !replyText.trim()) return
    setSubmittingReply(true)
    try {
      const reply = await createCommentReply(review.id, commentId, replyText.trim())
      setComments(prev => [...prev, reply])
      setReplyingTo(null)
      setReplyText('')
    } catch (e) {
      console.error(e)
    } finally {
      setSubmittingReply(false)
    }
  }

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>
  if (!review) return <div className="text-danger mt-10 text-center">리뷰를 찾을 수 없습니다.</div>

  const fileReviews: FileReview[] = Array.isArray(review.file_reviews) ? (review.file_reviews as FileReview[]) : []
  const intent = review.pr_intent as Record<string, unknown> | null | undefined
  const risk = review.risk_assessment as Record<string, unknown> | null | undefined

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Link href="/pull-requests" className="hover:text-accent transition-colors">Pull Requests</Link>
        <span>/</span>
        <Link href={`/pull-requests/${review.pull_request_id}`} className="hover:text-accent transition-colors">
          PR #{review.pull_request_id}
        </Link>
        <span>/</span>
        <span className="text-secondary">Review #{review.id}</span>
      </div>

      <div className="bg-surface rounded-xl border border-white/[0.07] p-6 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <DecisionBadge decision={review.review_decision} />
          <RiskBadge level={review.display_risk_level ?? review.risk_level} />
          <TriggerSourceBadge source={review.trigger_source} />
          {review.display_risk_score != null && (
            <span className="text-sm text-secondary">
              Risk Score: <strong className="text-primary">{review.display_risk_score.toFixed(2)}</strong>
              {review.effective_risk_score != null && review.effective_risk_score !== review.risk_score && (
                <span className="ml-1.5 text-xs text-muted line-through">{review.risk_score?.toFixed(2)}</span>
              )}
            </span>
          )}
          {review.effective_risk_level != null && review.effective_risk_level !== review.risk_level && (
            <Badge label="오탐 기각 반영됨" variant="yellow" />
          )}
          {review.retry_count > 0 && (
            <Badge label={`재시도 ${review.retry_count}회`} variant="yellow" />
          )}
        </div>
        <p className="text-xs text-muted font-mono">커밋: {review.head_sha}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {intent && (
          <div className="bg-surface rounded-xl border border-white/[0.07] p-5">
            <h3 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-3">PR Intent</h3>
            <div className="space-y-2 text-sm">
              {intent.type != null && <div><span className="text-muted">타입: </span><Badge label={String(intent.type)} variant="blue" /></div>}
              {intent.complexity != null && <div><span className="text-muted">복잡도: </span><strong className="text-primary">{String(intent.complexity)}</strong></div>}
              {intent.summary != null && <p className="text-secondary">{String(intent.summary)}</p>}
              {Array.isArray(intent.key_objectives) && intent.key_objectives.length > 0 && (
                <ul className="list-disc pl-4 text-secondary space-y-0.5">
                  {intent.key_objectives.map((o, i) => <li key={i}>{String(o)}</li>)}
                </ul>
              )}
            </div>
          </div>
        )}
        {risk && (
          <div className="bg-surface rounded-xl border border-white/[0.07] p-5">
            <h3 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-3">Risk Assessment</h3>
            <div className="space-y-2 text-sm">
              {risk.reasoning != null && <p className="text-secondary">{String(risk.reasoning)}</p>}
              {Array.isArray(risk.factors) && risk.factors.length > 0 && (
                <div>
                  <p className="text-muted text-xs mb-1">위험 요소</p>
                  <ul className="list-disc pl-4 text-secondary space-y-0.5">
                    {risk.factors.map((f, i) => <li key={i}>{String(f)}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {review.final_review && (
        <div className="bg-surface rounded-xl border border-white/[0.07] p-6">
          <h3 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-4">Final Review</h3>
          <div className="prose text-sm max-w-none">
            <ReactMarkdown>{review.final_review}</ReactMarkdown>
          </div>
        </div>
      )}

      {fileReviews.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-primary">파일별 리뷰</h3>
            <span className="text-xs text-muted">{fileReviews.length}개 파일</span>
          </div>
          {fileReviews.map((fr, idx) => {
            const isOpen = expanded.has(idx)
            const statusColor = fr.status === 'LGTM' ? 'green' : fr.status === 'NEEDS_IMPROVEMENT' ? 'yellow' : 'gray'
            return (
              <div key={idx} className="bg-surface rounded-xl border border-white/[0.07] overflow-hidden">
                <button
                  onClick={() => toggleExpand(idx)}
                  className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Badge label={fr.status ?? 'UNKNOWN'} variant={statusColor as 'green' | 'yellow' | 'gray'} />
                    <span className="text-sm font-mono text-secondary">{fr.filename}</span>
                  </div>
                  <span className="text-muted text-xs">{isOpen ? '▲' : '▼'}</span>
                </button>
                {isOpen && (
                  <div className="border-t border-white/[0.06] px-5 py-4 space-y-3 bg-surface2/30">
                    {fr.summary && <p className="text-sm text-secondary">{fr.summary}</p>}
                    {fr.issues && fr.issues.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-danger mb-2">이슈</p>
                        <ul className="space-y-2">
                          {fr.issues.map((issue, i) => (
                            <li key={i} className="text-sm text-secondary flex gap-2 items-start">
                              {issue.severity && <Badge label={issue.severity} variant="red" />}
                              <span>{issue.description}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {fr.suggestions && fr.suggestions.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-accent mb-2">제안</p>
                        <ul className="space-y-1">
                          {fr.suggestions.map((s, i) => (
                            <li key={i} className="text-sm text-secondary">{s.description}</li>
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

      {comments.filter(c => c.parent_id === null).length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-primary">코멘트</h3>
            <span className="text-xs text-muted">{comments.filter(c => c.parent_id === null).length}개</span>
          </div>
          {comments.filter(c => c.parent_id === null).map(comment => {
            const replies = comments.filter(c => c.parent_id === comment.id)
            const isReplying = replyingTo === comment.id
            const isDismissing = dismissingComment === comment.id
            return (
              <div key={comment.id} className="space-y-1">
                <div
                  className={`bg-surface rounded-xl border p-4 flex items-start gap-3 transition-all duration-150 ${
                    comment.is_dismissed
                      ? 'border-yellow-500/20 opacity-50'
                      : comment.is_addressed
                      ? 'border-success/20 opacity-50'
                      : 'border-white/[0.07]'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={comment.is_addressed}
                    onChange={() => handleAddressed(comment)}
                    disabled={comment.is_dismissed}
                    className="mt-0.5 cursor-pointer accent-accent disabled:cursor-not-allowed"
                  />
                  <div className="flex-1 space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge label={comment.comment_type} variant={comment.comment_type === 'issue' ? 'red' : 'blue'} />
                        {comment.severity && (
                          <Badge
                            label={comment.severity}
                            variant={comment.severity === 'high' ? 'red' : comment.severity === 'medium' ? 'yellow' : 'gray'}
                          />
                        )}
                        {comment.filename && <span className="text-xs font-mono text-muted">{comment.filename}</span>}
                      </div>
                      <div className="flex items-center gap-3">
                        {comment.comment_type === 'issue' && (
                          comment.is_dismissed ? (
                            <button onClick={() => handleUndismiss(comment)} className="text-xs text-yellow-400/70 hover:text-yellow-400 transition-colors">
                              기각 취소
                            </button>
                          ) : (
                            <button
                              onClick={() => { setDismissingComment(isDismissing ? null : comment.id); setDismissReason('') }}
                              className="text-xs text-muted hover:text-yellow-400 transition-colors"
                            >
                              오탐 기각
                            </button>
                          )
                        )}
                        <button
                          onClick={() => { setReplyingTo(isReplying ? null : comment.id); setReplyText('') }}
                          className="text-xs text-muted hover:text-accent transition-colors"
                        >
                          답글
                        </button>
                      </div>
                    </div>
                    <p className={`text-sm text-secondary ${comment.is_dismissed ? 'line-through' : ''}`}>{comment.body}</p>
                    {comment.is_dismissed && (
                      <p className="text-xs text-yellow-400/70">
                        오탐으로 기각됨{comment.dismissed_reason ? `: ${comment.dismissed_reason}` : ''}
                        {comment.dismissed_at && ` · ${new Date(comment.dismissed_at).toLocaleString('ko-KR')}`}
                      </p>
                    )}
                    {!comment.is_dismissed && comment.is_addressed && comment.addressed_at && (
                      <p className="text-xs text-success">처리됨: {new Date(comment.addressed_at).toLocaleString('ko-KR')}</p>
                    )}
                  </div>
                </div>

                {isDismissing && (
                  <div className="ml-8 bg-surface/60 rounded-xl border border-yellow-500/20 p-3 space-y-2">
                    <p className="text-xs text-yellow-400/70">오탐으로 기각합니다. 사유를 입력하면 다음 리뷰에서 LLM이 재지적하지 않습니다.</p>
                    <textarea
                      value={dismissReason}
                      onChange={e => setDismissReason(e.target.value)}
                      placeholder="기각 사유 (선택)"
                      rows={2}
                      className="w-full bg-transparent text-sm text-secondary placeholder-muted resize-none outline-none"
                    />
                    <div className="flex justify-end gap-2">
                      <button onClick={() => { setDismissingComment(null); setDismissReason('') }} className="text-xs text-muted hover:text-secondary transition-colors" disabled={submittingDismiss}>취소</button>
                      <button
                        onClick={() => handleDismissSubmit(comment)}
                        disabled={submittingDismiss}
                        className="px-3 py-1 text-xs font-semibold bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 rounded-lg hover:bg-yellow-500/20 transition-colors disabled:opacity-50"
                      >
                        {submittingDismiss ? '처리 중...' : '기각 확인'}
                      </button>
                    </div>
                  </div>
                )}

                {replies.length > 0 && (
                  <div className="ml-8 space-y-1">
                    {replies.map(reply => (
                      <div key={reply.id} className="bg-surface/60 rounded-xl border border-white/[0.05] p-3 flex items-start gap-3">
                        <div className="w-4 flex-shrink-0 flex items-center justify-center text-muted text-xs">↳</div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge label="reply" variant="gray" />
                            <span className="text-xs text-muted">{new Date(reply.created_at).toLocaleString('ko-KR')}</span>
                          </div>
                          <p className="text-sm text-secondary">{reply.body}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {isReplying && (
                  <div className="ml-8 bg-surface/60 rounded-xl border border-accent/20 p-3 space-y-2">
                    <textarea
                      value={replyText}
                      onChange={e => setReplyText(e.target.value)}
                      placeholder="답글을 입력하세요..."
                      rows={2}
                      className="w-full bg-transparent text-sm text-secondary placeholder-muted resize-none outline-none"
                    />
                    <div className="flex justify-end gap-2">
                      <button onClick={() => { setReplyingTo(null); setReplyText('') }} className="text-xs text-muted hover:text-secondary transition-colors" disabled={submittingReply}>취소</button>
                      <button
                        onClick={() => handleReplySubmit(comment.id)}
                        disabled={submittingReply || !replyText.trim()}
                        className="px-3 py-1 text-xs font-semibold bg-accent/20 text-accent border border-accent/30 rounded-lg hover:bg-accent/30 transition-colors disabled:opacity-50"
                      >
                        {submittingReply ? '전송 중...' : '답글 등록'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {review.errors && (review.errors as unknown[]).length > 0 && (
        <div className="bg-danger/5 border border-danger/20 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-danger mb-2">오류</h3>
          <ul className="space-y-1">
            {(review.errors as unknown[]).map((e, i) => (
              <li key={i} className="text-sm text-danger/80">{String(e)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

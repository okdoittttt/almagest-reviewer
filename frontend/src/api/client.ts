import axios from 'axios'
import type {
  PullRequest,
  Repository,
  Review,
  ReviewComment,
  Skill,
  SkillCreate,
  SkillUpdate,
  Stats,
} from './types'

// httpOnly 쿠키를 자동 전송하기 위해 withCredentials: true 설정
// Authorization 헤더 불필요 — 쿠키가 모든 요청에 자동 포함됨
const api = axios.create({ baseURL: '/api', withCredentials: true })

// 401 응답 시 로그인 페이지로 이동
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const getMe = () => api.get<{ login: string }>('/auth/me').then(r => r.data)

// Stats
export const getStats = () => api.get<Stats>('/stats').then(r => r.data)

// Repositories
export const getRepositories = () => api.get<Repository[]>('/repositories').then(r => r.data)
export const toggleRepository = (id: number) =>
  api.patch<Repository>(`/repositories/${id}/toggle`).then(r => r.data)

// Pull Requests
export const getPullRequests = (params?: {
  state?: string
  risk_level?: string
  review_decision?: string
  limit?: number
  offset?: number
}) => api.get<PullRequest[]>('/pull-requests', { params }).then(r => r.data)

export const getRepoPullRequests = (
  repoId: number,
  params?: { state?: string; risk_level?: string }
) => api.get<PullRequest[]>(`/repositories/${repoId}/pull-requests`, { params }).then(r => r.data)

export const getPullRequest = (prId: number) =>
  api.get<PullRequest>(`/pull-requests/${prId}`).then(r => r.data)

export const getPullRequestReviews = (prId: number) =>
  api.get<Review[]>(`/pull-requests/${prId}/reviews`).then(r => r.data)

// Reviews
export const getReview = (reviewId: number) =>
  api.get<Review>(`/reviews/${reviewId}`).then(r => r.data)

export const getReviewComments = (reviewId: number) =>
  api.get<ReviewComment[]>(`/reviews/${reviewId}/comments`).then(r => r.data)

export const updateCommentAddressed = (reviewId: number, commentId: number, isAddressed: boolean) =>
  api
    .patch<ReviewComment>(`/reviews/${reviewId}/comments/${commentId}`, { is_addressed: isAddressed })
    .then(r => r.data)

export const createCommentReply = (reviewId: number, commentId: number, body: string) =>
  api
    .post<ReviewComment>(`/reviews/${reviewId}/comments/${commentId}/replies`, { body })
    .then(r => r.data)

export const mergePullRequest = (prId: number, mergeMethod: string) =>
  api.post<import('./types').PullRequest>(`/pull-requests/${prId}/merge`, { merge_method: mergeMethod }).then(r => r.data)

// Skills
export const getSkills = (repoId: number) =>
  api.get<Skill[]>(`/repositories/${repoId}/skills`).then(r => r.data)

export const createSkill = (repoId: number, data: SkillCreate) =>
  api.post<Skill>(`/repositories/${repoId}/skills`, data).then(r => r.data)

export const updateSkill = (skillId: number, data: SkillUpdate) =>
  api.patch<Skill>(`/skills/${skillId}`, data).then(r => r.data)

export const deleteSkill = (skillId: number) =>
  api.delete(`/skills/${skillId}`)

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

const TOKEN_KEY = 'almagest_token'

const api = axios.create({ baseURL: '/api' })

// 요청 인터셉터 — JWT를 Authorization 헤더에 자동 주입
api.interceptors.request.use(config => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 응답 인터셉터 — 401 시 토큰 삭제 후 로그인 페이지로 이동
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem(TOKEN_KEY)
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

// Skills
export const getSkills = (repoId: number) =>
  api.get<Skill[]>(`/repositories/${repoId}/skills`).then(r => r.data)

export const createSkill = (repoId: number, data: SkillCreate) =>
  api.post<Skill>(`/repositories/${repoId}/skills`, data).then(r => r.data)

export const updateSkill = (skillId: number, data: SkillUpdate) =>
  api.patch<Skill>(`/skills/${skillId}`, data).then(r => r.data)

export const deleteSkill = (skillId: number) =>
  api.delete(`/skills/${skillId}`)

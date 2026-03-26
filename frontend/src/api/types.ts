export interface Repository {
  id: number
  github_repo_id: number
  owner: string
  name: string
  installation_id: string
  is_active: boolean
  pull_request_count: number
  skill_count: number
  created_at: string
  updated_at: string
}

export interface PullRequest {
  id: number
  repository_id: number
  github_pr_id: number
  pr_number: number
  title: string | null
  author_login: string | null
  head_sha: string
  base_branch: string | null
  head_branch: string | null
  state: string
  risk_level: string | null
  triage_priority: number | null
  review_count: number
  repo_owner: string
  repo_name: string
  created_at: string
  updated_at: string
}

export interface Review {
  id: number
  pull_request_id: number
  head_sha: string
  risk_level: string | null
  risk_score: number | null
  review_decision: string | null
  retry_count: number
  pr_intent?: Record<string, unknown>
  risk_assessment?: Record<string, unknown>
  file_reviews?: unknown[]
  final_review?: string | null
  errors?: unknown[]
  created_at: string
  updated_at: string
}

export interface ReviewComment {
  id: number
  review_id: number
  parent_id: number | null
  filename: string | null
  comment_type: string
  body: string | null
  is_addressed: boolean
  addressed_at: string | null
  created_at: string
  updated_at: string
}

export interface Skill {
  id: number
  repository_id: number
  name: string
  description: string | null
  criteria: Record<string, unknown>
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface Stats {
  total_repositories: number
  active_repositories: number
  total_pull_requests: number
  total_reviews: number
  approve_count: number
  request_changes_count: number
  comment_count: number
  avg_risk_score: number | null
}

export interface SkillCreate {
  name: string
  description?: string
  criteria?: Record<string, unknown>
  is_enabled?: boolean
}

export interface SkillUpdate {
  name?: string
  description?: string
  criteria?: Record<string, unknown>
  is_enabled?: boolean
}

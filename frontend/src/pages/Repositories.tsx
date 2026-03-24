import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRepositories, toggleRepository } from '../api/client'
import type { Repository } from '../api/types'
import { Badge } from '../components/Badge'

export function Repositories() {
  const [repos, setRepos] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRepositories()
      .then(data => setRepos(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleToggle = async (repo: Repository) => {
    const updated = await toggleRepository(repo.id)
    setRepos(prev => prev.map(r => (r.id === updated.id ? updated : r)))
  }

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-primary">Repositories</h1>
      {repos.length === 0 ? (
        <div className="bg-surface rounded-xl border border-white/[0.07] p-10 text-center">
          <p className="text-secondary">연동된 저장소가 없습니다.</p>
          <p className="text-sm text-muted mt-2">GitHub App을 설치한 저장소에서 PR을 열면 자동으로 등록됩니다.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {repos.map(repo => (
            <div
              key={repo.id}
              className="bg-surface rounded-xl border border-white/[0.07] p-5 space-y-4 hover:border-white/[0.15] transition-all duration-150"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-semibold text-primary">
                    {repo.owner}/{repo.name}
                  </h2>
                  <p className="text-xs text-muted mt-0.5">Installation: {repo.installation_id}</p>
                </div>
                <Badge label={repo.is_active ? '활성' : '비활성'} variant={repo.is_active ? 'green' : 'gray'} />
              </div>

              <div className="flex gap-4 text-sm text-secondary">
                <span>PR <strong className="text-primary">{repo.pull_request_count}</strong>개</span>
                <span>스킬 <strong className="text-primary">{repo.skill_count}</strong>개</span>
              </div>

              <div className="flex gap-2 pt-3 border-t border-white/[0.06]">
                <Link
                  to={`/repositories/${repo.id}/pull-requests`}
                  className="flex-1 text-center text-xs font-medium text-accent hover:bg-accent/10 py-1.5 rounded-lg border border-accent/30 hover:border-accent/50 transition-all duration-150"
                >
                  PR 목록
                </Link>
                <Link
                  to={`/repositories/${repo.id}/skills`}
                  className="flex-1 text-center text-xs font-medium text-secondary hover:text-primary hover:bg-white/5 py-1.5 rounded-lg border border-white/[0.07] hover:border-white/20 transition-all duration-150"
                >
                  스킬 관리
                </Link>
                <button
                  onClick={() => handleToggle(repo)}
                  className="flex-1 text-xs font-medium text-secondary hover:text-primary hover:bg-white/5 py-1.5 rounded-lg border border-white/[0.07] hover:border-white/20 transition-all duration-150"
                >
                  {repo.is_active ? '비활성화' : '활성화'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

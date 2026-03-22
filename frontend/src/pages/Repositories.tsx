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

  if (loading) return <div className="text-gray-400 mt-10 text-center">불러오는 중...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
      {repos.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400">
          <p>연동된 저장소가 없습니다.</p>
          <p className="text-sm mt-2">GitHub App을 설치한 저장소에서 PR을 열면 자동으로 등록됩니다.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {repos.map(repo => (
            <div key={repo.id} className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-semibold text-gray-900">
                    {repo.owner}/{repo.name}
                  </h2>
                  <p className="text-xs text-gray-400 mt-0.5">Installation: {repo.installation_id}</p>
                </div>
                <Badge label={repo.is_active ? '활성' : '비활성'} variant={repo.is_active ? 'green' : 'gray'} />
              </div>

              <div className="flex gap-4 text-sm text-gray-600">
                <span>PR <strong>{repo.pull_request_count}</strong>개</span>
                <span>스킬 <strong>{repo.skill_count}</strong>개</span>
              </div>

              <div className="flex gap-2 pt-2 border-t border-gray-100">
                <Link
                  to={`/repositories/${repo.id}/pull-requests`}
                  className="flex-1 text-center text-xs font-medium text-indigo-600 hover:bg-indigo-50 py-1.5 rounded-md border border-indigo-200 transition-colors"
                >
                  PR 목록
                </Link>
                <Link
                  to={`/repositories/${repo.id}/skills`}
                  className="flex-1 text-center text-xs font-medium text-gray-600 hover:bg-gray-50 py-1.5 rounded-md border border-gray-200 transition-colors"
                >
                  스킬 관리
                </Link>
                <button
                  onClick={() => handleToggle(repo)}
                  className="flex-1 text-xs font-medium text-gray-600 hover:bg-gray-50 py-1.5 rounded-md border border-gray-200 transition-colors"
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

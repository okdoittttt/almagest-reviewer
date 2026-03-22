import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { createSkill, deleteSkill, getSkills, updateSkill } from '../api/client'
import type { Skill, SkillCreate } from '../api/types'

const EMPTY_FORM: SkillCreate = {
  name: '',
  description: '',
  criteria: { focus_areas: [], ignore_patterns: [] },
  is_enabled: true,
}

export function Skills() {
  const { repoId } = useParams()
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<SkillCreate>(EMPTY_FORM)
  const [focusArea, setFocusArea] = useState('')
  const [ignorePattern, setIgnorePattern] = useState('')

  useEffect(() => {
    if (!repoId) return
    getSkills(Number(repoId)).then(data => {
      setSkills(data)
      setLoading(false)
    })
  }, [repoId])

  const openCreate = () => {
    setForm(EMPTY_FORM)
    setFocusArea('')
    setIgnorePattern('')
    setEditingId(null)
    setShowModal(true)
  }

  const openEdit = (skill: Skill) => {
    setForm({
      name: skill.name,
      description: skill.description ?? '',
      criteria: skill.criteria,
      is_enabled: skill.is_enabled,
    })
    setFocusArea('')
    setIgnorePattern('')
    setEditingId(skill.id)
    setShowModal(true)
  }

  const handleSubmit = async () => {
    if (!repoId || !form.name.trim()) return
    if (editingId) {
      const updated = await updateSkill(editingId, form)
      setSkills(prev => prev.map(s => (s.id === updated.id ? updated : s)))
    } else {
      const created = await createSkill(Number(repoId), form)
      setSkills(prev => [...prev, created])
    }
    setShowModal(false)
  }

  const handleDelete = async (skill: Skill) => {
    if (!confirm(`"${skill.name}" 스킬을 삭제할까요?`)) return
    await deleteSkill(skill.id)
    setSkills(prev => prev.filter(s => s.id !== skill.id))
  }

  const handleToggle = async (skill: Skill) => {
    const updated = await updateSkill(skill.id, { is_enabled: !skill.is_enabled })
    setSkills(prev => prev.map(s => (s.id === updated.id ? updated : s)))
  }

  const addFocusArea = () => {
    if (!focusArea.trim()) return
    const areas = ((form.criteria?.focus_areas as string[]) ?? [])
    setForm(f => ({ ...f, criteria: { ...f.criteria, focus_areas: [...areas, focusArea.trim()] } }))
    setFocusArea('')
  }

  const removeFocusArea = (i: number) => {
    const areas = ((form.criteria?.focus_areas as string[]) ?? []).filter((_, idx) => idx !== i)
    setForm(f => ({ ...f, criteria: { ...f.criteria, focus_areas: areas } }))
  }

  const addIgnorePattern = () => {
    if (!ignorePattern.trim()) return
    const patterns = ((form.criteria?.ignore_patterns as string[]) ?? [])
    setForm(f => ({ ...f, criteria: { ...f.criteria, ignore_patterns: [...patterns, ignorePattern.trim()] } }))
    setIgnorePattern('')
  }

  const removeIgnorePattern = (i: number) => {
    const patterns = ((form.criteria?.ignore_patterns as string[]) ?? []).filter((_, idx) => idx !== i)
    setForm(f => ({ ...f, criteria: { ...f.criteria, ignore_patterns: patterns } }))
  }

  if (loading) return <div className="text-gray-400 mt-10 text-center">불러오는 중...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/repositories" className="hover:text-indigo-600">Repositories</Link>
        <span>/</span>
        <span>Skills</span>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">스킬 관리</h1>
        <button
          onClick={openCreate}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
        >
          + 새 스킬 추가
        </button>
      </div>

      {skills.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400">
          <p>등록된 스킬이 없습니다.</p>
          <p className="text-sm mt-2">스킬을 추가하면 AI 리뷰 시 해당 기준이 적용됩니다.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {skills.map(skill => {
            const focusAreas = (skill.criteria?.focus_areas as string[]) ?? []
            const ignorePatterns = (skill.criteria?.ignore_patterns as string[]) ?? []
            return (
              <div key={skill.id} className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900">{skill.name}</h2>
                    {skill.description && <p className="text-sm text-gray-500 mt-0.5">{skill.description}</p>}
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <span className="text-xs text-gray-500">{skill.is_enabled ? '활성' : '비활성'}</span>
                    <div
                      onClick={() => handleToggle(skill)}
                      className={`w-10 h-5 rounded-full transition-colors cursor-pointer ${
                        skill.is_enabled ? 'bg-indigo-500' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 bg-white rounded-full shadow transition-transform mt-0.5 ${
                          skill.is_enabled ? 'translate-x-5' : 'translate-x-0.5'
                        }`}
                      />
                    </div>
                  </label>
                </div>

                {focusAreas.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Focus Areas</p>
                    <div className="flex flex-wrap gap-1">
                      {focusAreas.map((a, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
                {ignorePatterns.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Ignore Patterns</p>
                    <div className="flex flex-wrap gap-1">
                      {ignorePatterns.map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-mono">{p}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-2 border-t border-gray-100">
                  <button
                    onClick={() => openEdit(skill)}
                    className="flex-1 text-xs text-indigo-600 hover:bg-indigo-50 py-1.5 rounded border border-indigo-200 transition-colors"
                  >
                    편집
                  </button>
                  <button
                    onClick={() => handleDelete(skill)}
                    className="flex-1 text-xs text-red-500 hover:bg-red-50 py-1.5 rounded border border-red-200 transition-colors"
                  >
                    삭제
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 스킬 추가/편집 모달 */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 p-6 space-y-4">
            <h2 className="text-lg font-bold text-gray-900">{editingId ? '스킬 편집' : '새 스킬 추가'}</h2>

            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700">스킬 이름 *</label>
                <input
                  className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="예: Security Review"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">설명</label>
                <textarea
                  className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
                  rows={2}
                  value={form.description ?? ''}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="스킬에 대한 설명"
                />
              </div>

              {/* Focus Areas */}
              <div>
                <label className="text-sm font-medium text-gray-700">Focus Areas</label>
                <div className="flex gap-2 mt-1">
                  <input
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    value={focusArea}
                    onChange={e => setFocusArea(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addFocusArea()}
                    placeholder="예: security vulnerabilities"
                  />
                  <button onClick={addFocusArea} className="px-3 py-1.5 bg-indigo-100 text-indigo-700 text-sm rounded-lg hover:bg-indigo-200">추가</button>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {((form.criteria?.focus_areas as string[]) ?? []).map((a, i) => (
                    <span key={i} className="flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                      {a}
                      <button onClick={() => removeFocusArea(i)} className="text-blue-400 hover:text-blue-700">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Ignore Patterns */}
              <div>
                <label className="text-sm font-medium text-gray-700">Ignore Patterns</label>
                <div className="flex gap-2 mt-1">
                  <input
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    value={ignorePattern}
                    onChange={e => setIgnorePattern(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addIgnorePattern()}
                    placeholder="예: *.test.ts"
                  />
                  <button onClick={addIgnorePattern} className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200">추가</button>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {((form.criteria?.ignore_patterns as string[]) ?? []).map((p, i) => (
                    <span key={i} className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-mono">
                      {p}
                      <button onClick={() => removeIgnorePattern(i)} className="text-gray-400 hover:text-gray-700">×</button>
                    </span>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_enabled}
                  onChange={e => setForm(f => ({ ...f, is_enabled: e.target.checked }))}
                />
                <span className="text-sm text-gray-700">활성화</span>
              </label>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
              >
                {editingId ? '저장' : '추가'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

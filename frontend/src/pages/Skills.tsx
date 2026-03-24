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

const inputClass = [
  'w-full rounded-lg px-3 py-2 text-sm text-primary',
  'bg-surface2 border border-white/[0.07]',
  'placeholder:text-muted',
  'focus:outline-none focus:border-accent/50 focus:ring-0',
  'transition-colors duration-150',
].join(' ')

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

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Link to="/repositories" className="hover:text-accent transition-colors">Repositories</Link>
        <span>/</span>
        <span className="text-secondary">Skills</span>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary">스킬 관리</h1>
        <button
          onClick={openCreate}
          className="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-150 text-white"
          style={{ background: '#2997ff' }}
          onMouseOver={e => (e.currentTarget.style.background = '#1a7fd4')}
          onMouseOut={e => (e.currentTarget.style.background = '#2997ff')}
        >
          + 새 스킬 추가
        </button>
      </div>

      {skills.length === 0 ? (
        <div className="bg-surface rounded-xl border border-white/[0.07] p-10 text-center">
          <p className="text-secondary">등록된 스킬이 없습니다.</p>
          <p className="text-sm text-muted mt-2">스킬을 추가하면 AI 리뷰 시 해당 기준이 적용됩니다.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {skills.map(skill => {
            const focusAreas = (skill.criteria?.focus_areas as string[]) ?? []
            const ignorePatterns = (skill.criteria?.ignore_patterns as string[]) ?? []
            return (
              <div key={skill.id} className="bg-surface rounded-xl border border-white/[0.07] p-5 space-y-3 hover:border-white/[0.15] transition-all duration-150">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-primary">{skill.name}</h2>
                    {skill.description && <p className="text-sm text-secondary mt-0.5">{skill.description}</p>}
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <span className="text-xs text-muted">{skill.is_enabled ? '활성' : '비활성'}</span>
                    <div
                      onClick={() => handleToggle(skill)}
                      className={`w-10 h-5 rounded-full transition-colors cursor-pointer ${
                        skill.is_enabled ? 'bg-accent' : 'bg-surface2'
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
                    <p className="text-xs text-muted mb-1.5">Focus Areas</p>
                    <div className="flex flex-wrap gap-1">
                      {focusAreas.map((a, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-950/60 text-accent text-xs rounded ring-1 ring-blue-900/80">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
                {ignorePatterns.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-1.5">Ignore Patterns</p>
                    <div className="flex flex-wrap gap-1">
                      {ignorePatterns.map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-surface2 text-secondary text-xs rounded font-mono">{p}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-3 border-t border-white/[0.06]">
                  <button
                    onClick={() => openEdit(skill)}
                    className="flex-1 text-xs text-accent hover:bg-accent/10 py-1.5 rounded-lg border border-accent/30 hover:border-accent/50 transition-all duration-150"
                  >
                    편집
                  </button>
                  <button
                    onClick={() => handleDelete(skill)}
                    className="flex-1 text-xs text-danger/80 hover:bg-danger/10 py-1.5 rounded-lg border border-danger/20 hover:border-danger/40 transition-all duration-150"
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
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div
            className="rounded-2xl border border-white/[0.08] w-full max-w-lg mx-4 p-6 space-y-4"
            style={{ background: 'rgba(24, 24, 27, 0.95)' }}
          >
            <h2 className="text-lg font-bold text-primary">{editingId ? '스킬 편집' : '새 스킬 추가'}</h2>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">스킬 이름 *</label>
                <input
                  className={`mt-1.5 ${inputClass}`}
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="예: Security Review"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">설명</label>
                <textarea
                  className={`mt-1.5 ${inputClass} resize-none`}
                  rows={2}
                  value={form.description ?? ''}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="스킬에 대한 설명"
                />
              </div>

              {/* Focus Areas */}
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">Focus Areas</label>
                <div className="flex gap-2 mt-1.5">
                  <input
                    className={`flex-1 ${inputClass}`}
                    value={focusArea}
                    onChange={e => setFocusArea(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addFocusArea()}
                    placeholder="예: security vulnerabilities"
                  />
                  <button
                    onClick={addFocusArea}
                    className="px-3 py-1.5 bg-accent/10 text-accent text-sm rounded-lg border border-accent/30 hover:bg-accent/20 transition-colors"
                  >
                    추가
                  </button>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {((form.criteria?.focus_areas as string[]) ?? []).map((a, i) => (
                    <span key={i} className="flex items-center gap-1 px-2 py-0.5 bg-blue-950/60 text-accent text-xs rounded ring-1 ring-blue-900/80">
                      {a}
                      <button onClick={() => removeFocusArea(i)} className="text-accent/60 hover:text-accent">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Ignore Patterns */}
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">Ignore Patterns</label>
                <div className="flex gap-2 mt-1.5">
                  <input
                    className={`flex-1 ${inputClass} font-mono`}
                    value={ignorePattern}
                    onChange={e => setIgnorePattern(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addIgnorePattern()}
                    placeholder="예: *.test.ts"
                  />
                  <button
                    onClick={addIgnorePattern}
                    className="px-3 py-1.5 bg-surface2 text-secondary text-sm rounded-lg border border-white/[0.07] hover:border-white/20 hover:text-primary transition-all"
                  >
                    추가
                  </button>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {((form.criteria?.ignore_patterns as string[]) ?? []).map((p, i) => (
                    <span key={i} className="flex items-center gap-1 px-2 py-0.5 bg-surface2 text-secondary text-xs rounded font-mono">
                      {p}
                      <button onClick={() => removeIgnorePattern(i)} className="text-muted hover:text-secondary">×</button>
                    </span>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_enabled}
                  onChange={e => setForm(f => ({ ...f, is_enabled: e.target.checked }))}
                  className="accent-accent"
                />
                <span className="text-sm text-secondary">활성화</span>
              </label>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 border border-white/[0.07] rounded-lg text-sm text-secondary hover:text-primary hover:border-white/20 transition-all"
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 py-2 rounded-lg text-sm font-medium text-white transition-all"
                style={{ background: '#2997ff' }}
                onMouseOver={e => (e.currentTarget.style.background = '#1a7fd4')}
                onMouseOut={e => (e.currentTarget.style.background = '#2997ff')}
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

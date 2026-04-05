'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { createSkill, deleteSkill, getSkills, updateSkill } from '@/api/client'
import type { Skill } from '@/api/types'

function serializeCriteria(focusAreas: string[], ignorePatterns: string[]): string | null {
  const parts: string[] = []
  if (focusAreas.length > 0)
    parts.push('집중 영역:\n' + focusAreas.map(a => `- ${a}`).join('\n'))
  if (ignorePatterns.length > 0)
    parts.push('무시 항목:\n' + ignorePatterns.map(p => `- ${p}`).join('\n'))
  return parts.length > 0 ? parts.join('\n\n') : null
}

function parseCriteriaText(text: string | null): { focusAreas: string[]; ignorePatterns: string[] } {
  if (!text) return { focusAreas: [], ignorePatterns: [] }
  const parseSection = (label: string): string[] => {
    const match = text.match(new RegExp(`${label}:\\n([\\s\\S]*?)(?:\\n\\n|$)`))
    if (!match) return []
    return match[1].split('\n').map(l => l.replace(/^- /, '').trim()).filter(Boolean)
  }
  return { focusAreas: parseSection('집중 영역'), ignorePatterns: parseSection('무시 항목') }
}

const inputClass = [
  'w-full rounded-lg px-3 py-2 text-sm text-primary',
  'bg-surface2 border border-white/[0.07]',
  'placeholder:text-muted',
  'focus:outline-none focus:border-accent/50 focus:ring-0',
  'transition-colors duration-150',
].join(' ')

interface TagInputProps {
  label: string
  placeholder: string
  tags: string[]
  inputValue: string
  onInputChange: (v: string) => void
  onAdd: () => void
  onRemove: (i: number) => void
  mono?: boolean
  tagStyle?: string
}

function TagInput({ label, placeholder, tags, inputValue, onInputChange, onAdd, onRemove, mono, tagStyle }: TagInputProps) {
  return (
    <div>
      <label className="text-xs font-medium text-secondary uppercase tracking-wider">{label}</label>
      <div className="flex gap-2 mt-1.5">
        <input
          className={`flex-1 ${inputClass}${mono ? ' font-mono' : ''}`}
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && onAdd()}
          placeholder={placeholder}
        />
        <button
          onClick={onAdd}
          className="px-3 py-1.5 bg-surface2 text-secondary text-sm rounded-lg border border-white/[0.07] hover:border-white/20 hover:text-primary transition-all"
        >
          추가
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {tags.map((tag, i) => (
            <span key={i} className={`flex items-center gap-1 px-2 py-0.5 text-xs rounded ${tagStyle ?? 'bg-surface2 text-secondary'}${mono ? ' font-mono' : ''}`}>
              {tag}
              <button onClick={() => onRemove(i)} className="text-muted hover:text-secondary leading-none">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SkillsPage() {
  const { repoId } = useParams<{ repoId: string }>()
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isEnabled, setIsEnabled] = useState(true)
  const [focusAreas, setFocusAreas] = useState<string[]>([])
  const [ignorePatterns, setIgnorePatterns] = useState<string[]>([])
  const [filePatterns, setFilePatterns] = useState<string[]>([])
  const [focusInput, setFocusInput] = useState('')
  const [ignoreInput, setIgnoreInput] = useState('')
  const [filePatternInput, setFilePatternInput] = useState('')

  useEffect(() => {
    if (!repoId) return
    getSkills(Number(repoId)).then(data => { setSkills(data); setLoading(false) })
  }, [repoId])

  const resetForm = () => {
    setName(''); setDescription(''); setIsEnabled(true)
    setFocusAreas([]); setIgnorePatterns([]); setFilePatterns([])
    setFocusInput(''); setIgnoreInput(''); setFilePatternInput('')
    setEditingId(null)
  }

  const openCreate = () => { resetForm(); setShowModal(true) }

  const openEdit = (skill: Skill) => {
    const { focusAreas: fa, ignorePatterns: ip } = parseCriteriaText(skill.criteria)
    setName(skill.name); setDescription(skill.description ?? ''); setIsEnabled(skill.is_enabled)
    setFocusAreas(fa); setIgnorePatterns(ip); setFilePatterns(skill.file_patterns ?? [])
    setFocusInput(''); setIgnoreInput(''); setFilePatternInput('')
    setEditingId(skill.id); setShowModal(true)
  }

  const handleSubmit = async () => {
    if (!repoId || !name.trim()) return
    const payload = {
      name: name.trim(),
      description: description.trim() || undefined,
      criteria: serializeCriteria(focusAreas, ignorePatterns),
      file_patterns: filePatterns,
      is_enabled: isEnabled,
    }
    if (editingId) {
      const updated = await updateSkill(editingId, payload)
      setSkills(prev => prev.map(s => (s.id === updated.id ? updated : s)))
    } else {
      const created = await createSkill(Number(repoId), payload)
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

  if (loading) return <div className="text-secondary mt-10 text-center">불러오는 중...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Link href="/repositories" className="hover:text-accent transition-colors">Repositories</Link>
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
            const { focusAreas: fa, ignorePatterns: ip } = parseCriteriaText(skill.criteria)
            const fp = skill.file_patterns ?? []
            return (
              <div key={skill.id} className="bg-surface rounded-xl border border-white/[0.07] p-5 space-y-3 hover:border-white/[0.15] transition-all duration-150">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-primary">{skill.name}</h2>
                    {skill.description && <p className="text-sm text-secondary mt-0.5">{skill.description}</p>}
                  </div>
                  <div onClick={() => handleToggle(skill)} className="flex items-center gap-2 cursor-pointer">
                    <span className="text-xs text-muted">{skill.is_enabled ? '활성' : '비활성'}</span>
                    <div className={`w-10 h-5 rounded-full transition-colors ${skill.is_enabled ? 'bg-accent' : 'bg-surface2'}`}>
                      <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform mt-0.5 ${skill.is_enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
                    </div>
                  </div>
                </div>

                {fa.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-1.5">Focus Areas</p>
                    <div className="flex flex-wrap gap-1">
                      {fa.map((a, i) => <span key={i} className="px-2 py-0.5 bg-blue-950/60 text-accent text-xs rounded ring-1 ring-blue-900/80">{a}</span>)}
                    </div>
                  </div>
                )}
                {ip.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-1.5">Ignore Patterns</p>
                    <div className="flex flex-wrap gap-1">
                      {ip.map((p, i) => <span key={i} className="px-2 py-0.5 bg-surface2 text-secondary text-xs rounded font-mono">{p}</span>)}
                    </div>
                  </div>
                )}
                {fp.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-1.5">적용 파일 패턴</p>
                    <div className="flex flex-wrap gap-1">
                      {fp.map((p, i) => <span key={i} className="px-2 py-0.5 bg-surface2 text-muted text-xs rounded font-mono">{p}</span>)}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-3 border-t border-white/[0.06]">
                  <button onClick={() => openEdit(skill)} className="flex-1 text-xs text-accent hover:bg-accent/10 py-1.5 rounded-lg border border-accent/30 hover:border-accent/50 transition-all duration-150">편집</button>
                  <button onClick={() => handleDelete(skill)} className="flex-1 text-xs text-danger/80 hover:bg-danger/10 py-1.5 rounded-lg border border-danger/20 hover:border-danger/40 transition-all duration-150">삭제</button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div
            className="rounded-2xl border border-white/[0.08] w-full max-w-lg mx-4 p-6 space-y-4 overflow-y-auto max-h-[90vh]"
            style={{ background: 'rgba(24, 24, 27, 0.95)' }}
          >
            <h2 className="text-lg font-bold text-primary">{editingId ? '스킬 편집' : '새 스킬 추가'}</h2>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">스킬 이름 *</label>
                <input className={`mt-1.5 ${inputClass}`} value={name} onChange={e => setName(e.target.value)} placeholder="예: 보안 점검" />
              </div>
              <div>
                <label className="text-xs font-medium text-secondary uppercase tracking-wider">설명</label>
                <textarea className={`mt-1.5 ${inputClass} resize-none`} rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="예: SQL Injection, XSS, 인증 우회 취약점을 검토합니다" />
              </div>
              <TagInput
                label="Focus Areas" placeholder="예: 파라미터화된 쿼리 사용 여부"
                tags={focusAreas} inputValue={focusInput} onInputChange={setFocusInput}
                onAdd={() => { if (focusInput.trim()) { setFocusAreas(p => [...p, focusInput.trim()]); setFocusInput('') } }}
                onRemove={i => setFocusAreas(p => p.filter((_, idx) => idx !== i))}
                tagStyle="bg-blue-950/60 text-accent ring-1 ring-blue-900/80"
              />
              <TagInput
                label="Ignore Patterns" placeholder="예: *.test.ts"
                tags={ignorePatterns} inputValue={ignoreInput} onInputChange={setIgnoreInput}
                onAdd={() => { if (ignoreInput.trim()) { setIgnorePatterns(p => [...p, ignoreInput.trim()]); setIgnoreInput('') } }}
                onRemove={i => setIgnorePatterns(p => p.filter((_, idx) => idx !== i))} mono
              />
              <TagInput
                label="적용 파일 패턴" placeholder="예: **/migrations/** (비워두면 전체 적용)"
                tags={filePatterns} inputValue={filePatternInput} onInputChange={setFilePatternInput}
                onAdd={() => { if (filePatternInput.trim()) { setFilePatterns(p => [...p, filePatternInput.trim()]); setFilePatternInput('') } }}
                onRemove={i => setFilePatterns(p => p.filter((_, idx) => idx !== i))} mono
              />
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" checked={isEnabled} onChange={e => setIsEnabled(e.target.checked)} className="accent-accent" />
                <span className="text-sm text-secondary">활성화</span>
              </label>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2 border border-white/[0.07] rounded-lg text-sm text-secondary hover:text-primary hover:border-white/20 transition-all">취소</button>
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

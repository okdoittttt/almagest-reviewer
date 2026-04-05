'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

const sections = [
  { id: 'introduction', label: 'Introduction' },
  {
    id: 'getting-started',
    label: 'Getting Started',
    children: [
      { id: 'prerequisites', label: 'Prerequisites' },
      { id: 'installation', label: 'Installation' },
      { id: 'running', label: 'Running the Server' },
    ],
  },
  { id: 'features', label: 'Key Features' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'multi-repo', label: 'Multi-repo Integration' },
  { id: 'self-hosted', label: 'Self-hosted Deployment' },
  { id: 'troubleshooting', label: 'Troubleshooting' },
  { id: 'roadmap', label: 'Roadmap' },
]

function DocsSidebar() {
  const [activeId, setActiveId] = useState('introduction')

  useEffect(() => {
    const headings = document.querySelectorAll('[data-section]')
    const observer = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        }
      },
      { rootMargin: '-10% 0px -80% 0px' }
    )
    headings.forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <aside className="w-60 shrink-0">
      <nav className="sticky top-20 flex flex-col gap-0.5">
        {sections.map(section => (
          <div key={section.id}>
            <a
              href={`#${section.id}`}
              className={`block text-sm px-3 py-1.5 rounded-lg transition-all duration-150 ${
                activeId === section.id
                  ? 'text-accent bg-accent/10 font-medium'
                  : 'text-secondary hover:text-primary hover:bg-white/5'
              }`}
            >
              {section.label}
            </a>
            {section.children && (
              <div className="ml-3 flex flex-col gap-0.5 mt-0.5">
                {section.children.map(child => (
                  <a
                    key={child.id}
                    href={`#${child.id}`}
                    className={`block text-sm px-3 py-1 rounded-lg transition-all duration-150 ${
                      activeId === child.id
                        ? 'text-accent bg-accent/10 font-medium'
                        : 'text-muted hover:text-secondary hover:bg-white/5'
                    }`}
                  >
                    {child.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  )
}

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header
        className="sticky top-0 z-50 flex items-center gap-6 px-6 py-3 border-b border-white/[0.07]"
        style={{
          background: 'rgba(9, 9, 11, 0.85)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}
      >
        <Link
          href="/"
          className="text-lg shrink-0 text-primary tracking-tight"
          style={{ fontFamily: 'var(--font-brand)' }}
        >
          Almagest Reviewer
        </Link>
        <nav className="flex gap-1 flex-1">
          <Link
            href="/docs"
            className="text-sm font-medium px-3 py-1.5 rounded-lg transition-all duration-150 bg-white/10 text-primary"
          >
            Docs
          </Link>
        </nav>
        <Link
          href="/login"
          className="text-sm text-secondary hover:text-primary px-3 py-1.5 rounded-lg border border-white/[0.07] hover:border-white/20 transition-all duration-150"
        >
          Dashboard →
        </Link>
      </header>

      {/* Body */}
      <div className="max-w-6xl mx-auto px-6 py-10 flex gap-12">
        <DocsSidebar />
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  )
}

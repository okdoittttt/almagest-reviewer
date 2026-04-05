import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Almagest Reviewer',
  description: 'AI-powered GitHub code reviewer using LangGraph agentic workflows',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}

import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Repositories', to: '/repositories' },
  { label: 'Pull Requests', to: '/pull-requests' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation()
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
        <Link to="/" className="text-lg font-bold text-indigo-600 shrink-0">
          Almagest Reviewer
        </Link>
        <nav className="flex gap-4 flex-1">
          {navItems.map(item => (
            <Link
              key={item.to}
              to={item.to}
              className={`text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
                pathname === item.to
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        {user && (
          <div className="flex items-center gap-3">
            <a
              href={`https://github.com/${user.login}`}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
              </svg>
              {user.login}
            </a>
            <button
              onClick={logout}
              className="text-xs text-gray-400 hover:text-gray-700 px-2 py-1 rounded border border-gray-200 hover:border-gray-400 transition-colors"
            >
              로그아웃
            </button>
          </div>
        )}
      </header>
      <main className="flex-1 px-6 py-6 max-w-7xl w-full mx-auto">{children}</main>
    </div>
  )
}

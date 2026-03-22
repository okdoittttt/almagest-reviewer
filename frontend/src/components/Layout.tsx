import { Link, useLocation } from 'react-router-dom'

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Repositories', to: '/repositories' },
  { label: 'Pull Requests', to: '/pull-requests' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
        <Link to="/" className="text-lg font-bold text-indigo-600 shrink-0">
          Almagest Reviewer
        </Link>
        <nav className="flex gap-4">
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
      </header>
      <main className="flex-1 px-6 py-6 max-w-7xl w-full mx-auto">{children}</main>
    </div>
  )
}

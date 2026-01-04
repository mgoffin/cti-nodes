import { Outlet, Link, useNavigate } from 'react-router'
import SearchBar from './SearchBar'
import { useTheme } from '../hooks/useTheme'

export default function Layout() {
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()

  const handleSearch = (query: string) => {
    navigate(`/?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="min-h-screen transition-colors duration-200">
      {/* Header */}
      <header className="header border-b sticky top-0 z-50 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <svg className="w-8 h-8" viewBox="0 0 100 100">
                <circle cx="50" cy="30" r="12" fill="#0ea5e9"/>
                <circle cx="25" cy="70" r="12" fill="#0ea5e9"/>
                <circle cx="75" cy="70" r="12" fill="#0ea5e9"/>
                <line x1="50" y1="42" x2="25" y2="58" stroke="#64748b" strokeWidth="3"/>
                <line x1="50" y1="42" x2="75" y2="58" stroke="#64748b" strokeWidth="3"/>
                <line x1="37" y1="70" x2="63" y2="70" stroke="#64748b" strokeWidth="3"/>
              </svg>
              <span className="text-xl font-bold theme-text-heading">Nodes</span>
            </Link>

            {/* Search */}
            <div className="flex-1 max-w-2xl mx-8">
              <SearchBar onSearch={handleSearch} />
            </div>

            {/* Right side buttons */}
            <div className="flex items-center space-x-3">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg theme-toggle transition-colors"
                aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              >
                {theme === 'light' ? (
                  // Sun icon - shown in light mode (indicates current state)
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  // Moon icon - shown in dark mode (indicates current state)
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>

              {/* New Node Button */}
              <Link
                to="/new"
                className="btn btn-primary flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>New Node</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}

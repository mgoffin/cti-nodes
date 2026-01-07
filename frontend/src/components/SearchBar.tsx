import { useState, useCallback, useRef, useEffect } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
  placeholder?: string
}

export default function SearchBar({ onSearch, placeholder = 'Search nodes...' }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [showHelp, setShowHelp] = useState(false)
  const helpRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }, [query, onSearch])

  // Close help popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        showHelp &&
        helpRef.current &&
        buttonRef.current &&
        !helpRef.current.contains(e.target as Node) &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setShowHelp(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showHelp])

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input block w-full pl-10 pr-3 py-2 text-sm"
            placeholder={placeholder}
          />
        </div>

        {/* Help button */}
        <div className="relative">
          <button
            ref={buttonRef}
            type="button"
            onClick={() => setShowHelp(!showHelp)}
            className="p-2 rounded-lg theme-toggle transition-colors"
            aria-label="Search help"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          {/* Help popover */}
          {showHelp && (
            <div
              ref={helpRef}
              className="absolute right-0 top-full mt-2 w-80 card shadow-lg z-50"
            >
              <h3 className="text-sm font-semibold theme-text-heading mb-3">Search Syntax</h3>

              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-medium theme-text-primary">Keyword Search</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">APT29</code>
                  <p className="text-xs theme-text-muted mt-1">Search everywhere (content, tags, extracted entities)</p>
                </div>

                <div>
                  <p className="font-medium theme-text-primary">Content Only</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">content="malware analysis"</code>
                  <p className="text-xs theme-text-muted mt-1">Search only in node content</p>
                </div>

                <div>
                  <p className="font-medium theme-text-primary">Tag Search</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">tag:threat_actor="APT36"</code>
                  <p className="text-xs theme-text-muted mt-1">Find nodes with specific tag name and value</p>
                </div>

                <div>
                  <p className="font-medium theme-text-primary">Tag Existence</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">tag:campaign=*</code>
                  <p className="text-xs theme-text-muted mt-1">Find all nodes that have a specific tag</p>
                </div>

                <div>
                  <p className="font-medium theme-text-primary">Tag Value Search</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">tag-value="*cobalt*"</code>
                  <p className="text-xs theme-text-muted mt-1">Search all tag values (supports wildcards)</p>
                </div>

                <div>
                  <p className="font-medium theme-text-primary">Author Search</p>
                  <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">author="john@example.com"</code>
                  <p className="text-xs theme-text-muted mt-1">Find nodes created by a specific author</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowHelp(false)}
                className="mt-4 w-full btn btn-secondary text-sm"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </form>
  )
}

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

function getInitialTheme(): Theme {
  // Only run on client
  if (typeof window === 'undefined') {
    return 'light'
  }

  // Check what class is already on the HTML element (set by inline script)
  if (document.documentElement.classList.contains('dark')) {
    return 'dark'
  }
  if (document.documentElement.classList.contains('light')) {
    return 'light'
  }

  // Fallback: Check localStorage
  const stored = localStorage.getItem('nodes-theme')
  if (stored === 'dark' || stored === 'light') {
    return stored
  }

  // Check system preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }

  return 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')
  const [mounted, setMounted] = useState(false)

  // Set initial theme after mount
  useEffect(() => {
    setTheme(getInitialTheme())
    setMounted(true)
  }, [])

  // Apply theme class to document
  useEffect(() => {
    if (!mounted) return

    const root = document.documentElement

    // Remove both classes first to ensure clean state
    root.classList.remove('light', 'dark')

    // Add the current theme class
    root.classList.add(theme)

    // Save to localStorage
    localStorage.setItem('nodes-theme', theme)

    console.log('Theme changed to:', theme, 'Classes:', root.classList.toString())
  }, [theme, mounted])

  const toggleTheme = () => {
    setTheme(prev => {
      const newTheme = prev === 'light' ? 'dark' : 'light'
      console.log('Toggling theme from', prev, 'to', newTheme)
      return newTheme
    })
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, AuthState, AuthConfig } from '../types'

interface AuthContextType extends AuthState {
  login: () => void
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  authConfig: AuthConfig | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null)

  // Fetch auth config on mount
  useEffect(() => {
    fetchAuthConfig()
  }, [])

  // Fetch current user on mount (if auth is enabled)
  useEffect(() => {
    if (authConfig?.auth_enabled) {
      fetchCurrentUser()
    } else if (authConfig?.auth_enabled === false) {
      // Auth is disabled - no user needed
      setIsLoading(false)
    }
  }, [authConfig])

  const fetchAuthConfig = async () => {
    try {
      const response = await fetch('/api/auth/config', {
        credentials: 'include',
      })
      if (response.ok) {
        const config = await response.json()
        setAuthConfig(config)
      } else {
        // If auth config endpoint fails, assume auth is disabled
        setAuthConfig({ auth_enabled: false, sso_provider: null, sso_display_name: null })
      }
    } catch (error) {
      console.error('Failed to fetch auth config:', error)
      // Assume auth is disabled on error
      setAuthConfig({ auth_enabled: false, sso_provider: null, sso_display_name: null })
    }
  }

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        setUser(null)
      }
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const refreshUser = async () => {
    if (!authConfig?.auth_enabled) return
    await fetchCurrentUser()
  }

  const login = () => {
    // Redirect to SSO login endpoint
    // The backend will handle the OAuth flow and redirect back with cookies set
    window.location.href = '/api/auth/login'
  }

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
      setUser(null)
      // Redirect to home or login page
      window.location.href = '/'
    } catch (error) {
      console.error('Failed to logout:', error)
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    authConfig,
    login,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

export function SSOStatusBanner() {
  const { authConfig } = useAuth()
  const [ssoStatus, setSsoStatus] = useState<'healthy' | 'degraded' | 'offline' | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (!authConfig?.auth_enabled) return

    // Check SSO health periodically
    checkSSOHealth()
    const interval = setInterval(checkSSOHealth, 60000) // Check every minute

    return () => clearInterval(interval)
  }, [authConfig])

  const checkSSOHealth = async () => {
    try {
      // The backend SSO health check is handled by middleware
      // We can infer status from API responses or add a dedicated endpoint
      // For now, we'll check if we can reach the auth config endpoint
      const response = await fetch('/api/auth/config', {
        credentials: 'include',
      })

      if (response.ok) {
        const data = await response.json()
        // Check if there's a health indicator in the response
        if (data.sso_health === 'offline') {
          setSsoStatus('offline')
          setIsVisible(true)
        } else if (data.sso_health === 'degraded') {
          setSsoStatus('degraded')
          setIsVisible(true)
        } else {
          setSsoStatus('healthy')
          setIsVisible(false)
        }
      }
    } catch (error) {
      console.error('Failed to check SSO health:', error)
      // Don't show banner on network errors - could be client-side issue
    }
  }

  if (!isVisible || !authConfig?.auth_enabled) return null

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-40 ${
        ssoStatus === 'offline'
          ? 'bg-red-600'
          : ssoStatus === 'degraded'
          ? 'bg-yellow-500'
          : 'bg-blue-600'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {ssoStatus === 'offline' ? (
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
            <div className="text-white">
              {ssoStatus === 'offline' ? (
                <div>
                  <span className="font-semibold">SSO Provider Unavailable</span>
                  <span className="ml-2 text-sm opacity-90">
                    - New logins are temporarily disabled. Existing sessions remain active.
                  </span>
                </div>
              ) : ssoStatus === 'degraded' ? (
                <div>
                  <span className="font-semibold">SSO Performance Degraded</span>
                  <span className="ml-2 text-sm opacity-90">
                    - Login may be slower than usual. Your session is safe.
                  </span>
                </div>
              ) : null}
            </div>
          </div>
          <button
            onClick={() => setIsVisible(false)}
            className="text-white hover:opacity-75 transition-opacity"
            aria-label="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

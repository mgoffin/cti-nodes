import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import type { Session } from '../types'

interface SessionManagerProps {
  onClose: () => void
}

export function SessionManager({ onClose }: SessionManagerProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [revokingId, setRevokingId] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await apiClient.auth.getSessions()
      setSessions(data)
    } catch (err) {
      setError('Failed to load sessions')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRevoke = async (sessionId: string) => {
    if (!confirm('Are you sure you want to revoke this session?')) {
      return
    }

    setRevokingId(sessionId)
    try {
      await apiClient.auth.revokeSession(sessionId)
      setSessions(sessions.filter((s) => s.id !== sessionId))
    } catch (err) {
      alert('Failed to revoke session')
      console.error(err)
    } finally {
      setRevokingId(null)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const getRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Active Sessions</h2>
            <p className="text-sm text-gray-600 mt-1">Manage your login sessions across devices</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="text-center text-gray-600 py-8">Loading sessions...</div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-800">
              {error}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center text-gray-600 py-8">No active sessions</div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {session.user_agent ? parseUserAgent(session.user_agent) : 'Unknown Device'}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {session.ip_address || 'Unknown IP'}
                          </p>
                        </div>
                      </div>

                      <div className="ml-13 space-y-1 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">Created:</span>
                          <span>{formatDate(session.created_at)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">Last active:</span>
                          <span>{getRelativeTime(session.last_accessed)}</span>
                          <span className="text-gray-400">({formatDate(session.last_accessed)})</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleRevoke(session.id)}
                      disabled={revokingId === session.id}
                      className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {revokingId === session.id ? 'Revoking...' : 'Revoke'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full py-2 px-4 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function parseUserAgent(ua: string): string {
  // Simple user agent parsing for display
  if (ua.includes('Chrome')) return 'Chrome Browser'
  if (ua.includes('Firefox')) return 'Firefox Browser'
  if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari Browser'
  if (ua.includes('Edge')) return 'Edge Browser'
  if (ua.includes('Mobile')) return 'Mobile Device'
  return 'Web Browser'
}

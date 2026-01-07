import { useAuth } from '../contexts/AuthContext'

export function Login() {
  const { authConfig, login, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  if (!authConfig?.auth_enabled) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Authentication Disabled</h1>
          <p className="text-gray-600 mb-6">
            Authentication is not enabled for this instance. You can access the application without logging in.
          </p>
          <a
            href="/"
            className="block w-full py-2 px-4 bg-blue-600 text-white text-center rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Nodes Platform</h1>
          <p className="text-gray-600">Threat Intelligence Notebook</p>
        </div>

        <div className="mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h2 className="text-sm font-semibold text-blue-900 mb-1">Single Sign-On</h2>
            <p className="text-sm text-blue-700">
              Authenticate with {authConfig.sso_display_name || authConfig.sso_provider || 'SSO Provider'}
            </p>
          </div>
        </div>

        <button
          onClick={login}
          className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Sign in with {authConfig.sso_display_name || 'SSO'}
        </button>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            By signing in, you agree to the organization's security policies and terms of use.
          </p>
        </div>
      </div>
    </div>
  )
}

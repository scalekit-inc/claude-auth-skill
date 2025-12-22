import Link from 'next/link';
import { getCurrentUser, isAuthenticated, requireAuth } from '@/lib/auth';

export default async function Home() {
  const user = await getCurrentUser();
  const authenticated = await isAuthenticated();

  // Get token claims if authenticated
  let claims = null;
  if (authenticated) {
    try {
      claims = await requireAuth();
    } catch {
      // If requireAuth fails, user will be redirected
    }
  }

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Scalekit Authentication Demo</h1>

      {authenticated && user ? (
        <div className="space-y-6">
          <div className="bg-green-100 border border-green-400 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4 text-green-800">✅ Authenticated</h2>
            <p className="text-green-700">Welcome, {user.email}!</p>
          </div>

          <div className="bg-gray-100 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">User Information</h2>
            <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto text-sm">
              {JSON.stringify(user, null, 2)}
            </pre>
          </div>

          {claims && (
            <div className="bg-gray-100 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Token Claims (validateToken Result)</h2>
              <div className="bg-yellow-100 border border-yellow-400 p-4 rounded mb-4">
                <p className="text-sm text-yellow-800">
                  <strong>Critical Test:</strong> This should be an object with JWT claims (sub, email, iat, exp, etc.),
                  NOT a boolean true/false. If you see "true" or "false" below, the validateToken fix didn't work!
                </p>
              </div>
              <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto text-sm">
                {JSON.stringify(claims, null, 2)}
              </pre>
            </div>
          )}

          <div className="flex gap-4">
            <Link
              href="/dashboard"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Go to Dashboard
            </Link>
            <Link
              href="/auth/logout"
              className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700"
            >
              Logout
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-red-100 border border-red-400 p-6 rounded-lg">
            <p className="text-lg text-red-800">❌ You are not logged in.</p>
          </div>
          <Link
            href="/auth/login"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Sign In with Scalekit
          </Link>
        </div>
      )}
    </main>
  );
}

import { requireAuth, getCurrentUser } from '@/lib/auth';
import Link from 'next/link';

export default async function Dashboard() {
  const claims = await requireAuth();
  const user = await getCurrentUser();

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Dashboard (Protected Route)</h1>

      <div className="space-y-6">
        <div className="bg-green-100 border border-green-400 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4 text-green-800">✅ Authenticated</h2>
          <p className="text-green-700">Welcome, {user?.email}!</p>
          <p className="text-sm text-green-600 mt-2">
            This page is protected by requireAuth() - unauthenticated users are redirected to login.
          </p>
        </div>

        <div className="bg-gray-100 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">User Information</h2>
          <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto text-sm">
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>

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

        <div className="flex gap-4">
          <Link
            href="/"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Home
          </Link>
          <Link
            href="/auth/logout"
            className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700"
          >
            Logout
          </Link>
        </div>
      </div>
    </main>
  );
}

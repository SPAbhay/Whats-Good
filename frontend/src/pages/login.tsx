import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { auth } from '../services/api';
import { AuthLayout } from '../components/layout/AuthLayout';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const result = await auth.login({ email, password });

      // Redirect based on whether user has completed onboarding
      if (result.hasBrand) {
        router.push('/');
      } else {
        router.push('/onboarding/questions');
      }
    } catch (error) {
      // Set a generic error message
      setError('Invalid credentials');
      // If you want to log the error, you can do so here
      console.error(error); // Optional: Log the error for debugging
    }
  };

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-surface-800 mb-2">Welcome Back</h2>
          <p className="text-surface-400">Sign in to continue to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1">
            <label htmlFor="email" className="block text-sm font-medium text-surface-800">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 bg-white border border-surface-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              placeholder="name@company.com"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="block text-sm font-medium text-surface-800">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-white border border-surface-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-primary-600 to-primary-500 text-white py-2.5 px-4 rounded-xl hover:from-primary-700 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all font-medium"
          >
            Sign In
          </button>

          <p className="text-center text-surface-400">
  Don&apos;t have an account?{' '}
  <Link href="/signup" className="text-primary-600 hover:text-primary-700 font-medium">
    Create account
  </Link>
</p>
        </form>
      </div>
    </AuthLayout>
  );
}

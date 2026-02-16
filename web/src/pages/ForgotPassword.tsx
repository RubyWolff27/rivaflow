import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { authApi } from '../api/auth';

export default function ForgotPassword() {
  usePageTitle('Forgot Password');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setIsLoading(true);

    try {
      await authApi.forgotPassword(email);
      setSuccess(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to send reset email');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg)' }}>
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold" style={{ color: 'var(--text)' }}>
              Check Your Email
            </h2>
            <div className="mt-6 p-6 rounded-lg" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
              <p className="text-center text-sm" style={{ color: 'var(--text)' }}>
                If an account exists with <strong>{email}</strong>, you will receive a password reset link shortly.
              </p>
              <p className="mt-4 text-center text-xs" style={{ color: 'var(--muted)' }}>
                Check your spam folder if you don't see it within a few minutes.
              </p>
            </div>
            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="text-sm font-medium hover:opacity-80"
                style={{ color: 'var(--accent)' }}
              >
                ← Back to login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold" style={{ color: 'var(--text)' }}>
            Reset Your Password
          </h2>
          <p className="mt-2 text-center text-sm" style={{ color: 'var(--muted)' }}>
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md p-4" style={{ backgroundColor: 'var(--error-bg)' }}>
              <p className="text-sm" style={{ color: 'var(--error)' }}>{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--surface)',
                color: 'var(--text)',
              }}
              placeholder="your@email.com"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#FFFFFF',
              }}
            >
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </div>

          <div className="text-center space-y-2">
            <Link
              to="/login"
              className="block text-sm font-medium hover:opacity-80"
              style={{ color: 'var(--accent)' }}
            >
              ← Back to login
            </Link>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Don't have an account?{' '}
              <Link
                to="/register"
                className="font-medium hover:opacity-80"
                style={{ color: 'var(--accent)' }}
              >
                Sign up
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

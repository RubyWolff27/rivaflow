import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="max-w-md w-full space-y-6">
        {/* Beta Welcome Banner */}
        <div
          className="p-4 rounded-lg border-2"
          style={{
            backgroundColor: 'var(--surface)',
            borderColor: 'var(--accent)',
          }}
        >
          <p className="text-sm text-center leading-relaxed" style={{ color: 'var(--text)' }}>
            <span className="font-semibold" style={{ color: 'var(--accent)' }}>Welcome to RivaFlow Beta!</span>
            <br />
            You're joining early — things might break, features are still cooking, and your feedback shapes what we build next. Log your rolls, track your progress, and let us know what's working (and what's not).
            <br />
            <span className="font-medium">OSS! 🤙</span>
          </p>
        </div>

        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold" style={{ color: 'var(--text)' }}>
            Login to RivaFlow
          </h2>
          <p className="mt-2 text-center text-sm" style={{ color: 'var(--muted)' }}>
            Track your training journey
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md p-4" style={{ backgroundColor: 'var(--error-bg)' }}>
              <p className="text-sm" style={{ color: 'var(--error)' }}>{error}</p>
            </div>
          )}

          <div className="space-y-4">
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
              <label htmlFor="password" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--text)',
                }}
                placeholder="Password"
              />
            </div>
          </div>

          <div className="flex items-center justify-end">
            <div className="text-sm">
              <Link
                to="/forgot-password"
                className="font-medium hover:opacity-80"
                style={{ color: 'var(--accent)' }}
              >
                Forgot your password?
              </Link>
            </div>
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
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </div>

          <div className="text-center">
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

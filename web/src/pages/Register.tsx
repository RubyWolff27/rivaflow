import { useState, FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { BELT_GRADES } from '../constants/belts';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const inviteToken = searchParams.get('invite') || undefined;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [defaultGym, setDefaultGym] = useState('');
  const [beltGrade, setBeltGrade] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, firstName, lastName, inviteToken, defaultGym || undefined, beltGrade || undefined);
      navigate('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="max-w-md w-full space-y-6">
        {/* Invite banner or Beta banner */}
        {inviteToken ? (
          <div
            className="p-4 rounded-lg border-2"
            style={{
              backgroundColor: 'var(--surface)',
              borderColor: 'var(--accent)',
            }}
          >
            <p className="text-sm text-center leading-relaxed" style={{ color: 'var(--text)' }}>
              <span className="font-semibold" style={{ color: 'var(--accent)' }}>You've been invited!</span>
              <br />
              Create your account to get started with RivaFlow. Log your rolls, track your progress, and connect with your gym crew.
            </p>
          </div>
        ) : (
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
        )}

        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold" style={{ color: 'var(--text)' }}>
            Create your RivaFlow account
          </h2>
          <p className="mt-2 text-center text-sm" style={{ color: 'var(--muted)' }}>
            Start tracking your training journey
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md p-4" style={{ backgroundColor: 'var(--error-bg)' }}>
              <p className="text-sm" style={{ color: 'var(--error)' }}>{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  First Name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  autoComplete="given-name"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                  style={{
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--surface)',
                    color: 'var(--text)',
                  }}
                  placeholder="John"
                />
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Last Name
                </label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  autoComplete="family-name"
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                  style={{
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--surface)',
                    color: 'var(--text)',
                  }}
                  placeholder="Doe"
                />
              </div>
            </div>

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
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--text)',
                }}
                placeholder="Minimum 8 characters"
              />
              <p className="mt-1 text-xs" style={{ color: 'var(--muted)' }}>Must be at least 8 characters</p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--text)',
                }}
                placeholder="Re-enter password"
              />
            </div>

            <div>
              <label htmlFor="defaultGym" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Gym <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
              </label>
              <input
                id="defaultGym"
                name="defaultGym"
                type="text"
                autoComplete="organization"
                value={defaultGym}
                onChange={(e) => setDefaultGym(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--text)',
                }}
                placeholder="Your gym or academy"
              />
            </div>

            <div>
              <label htmlFor="beltGrade" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Belt <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
              </label>
              <select
                id="beltGrade"
                name="beltGrade"
                value={beltGrade}
                onChange={(e) => setBeltGrade(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: beltGrade ? 'var(--text)' : 'var(--muted)',
                }}
              >
                <option value="">Select your belt</option>
                {BELT_GRADES.map((grade) => (
                  <option key={grade} value={grade}>{grade}</option>
                ))}
              </select>
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
              {isLoading ? 'Creating account...' : 'Create account'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium hover:opacity-80"
                style={{ color: 'var(--accent)' }}
              >
                Login
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

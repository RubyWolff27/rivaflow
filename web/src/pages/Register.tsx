import { useState, FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { BELT_GRADES } from '../constants/belts';
import { usePageTitle } from '../hooks/usePageTitle';

type StrengthLevel = 'weak' | 'fair' | 'strong';

function getPasswordStrength(password: string): { level: StrengthLevel; score: number; label: string } {
  let score = 0;
  if (password.length >= 10) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/~`]/.test(password)) score++;

  if (score >= 4) return { level: 'strong', score, label: 'Strong' };
  if (score >= 3) return { level: 'fair', score, label: 'Fair' };
  return { level: 'weak', score, label: 'Weak' };
}

const strengthColors: Record<StrengthLevel, string> = {
  weak: 'var(--error)',
  fair: 'var(--warning)',
  strong: 'var(--success)',
};

export default function Register() {
  usePageTitle('Register');
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

  const passwordStrength = getPasswordStrength(password);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (password.length < 10) {
      setError('Password must be at least 10 characters long');
      return;
    }

    if (!/[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/~`]/.test(password)) {
      setError('Password must contain at least one special character');
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
                  className="input"
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
                  className="input"
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
                className="input"
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
                className="input"
                placeholder="Minimum 10 characters"
                aria-describedby="password-strength"
              />
              {password.length > 0 && (
                <div id="password-strength" className="mt-2">
                  <div
                    className="h-1 rounded-full transition-all duration-300"
                    style={{
                      width: passwordStrength.level === 'weak' ? '33%' : passwordStrength.level === 'fair' ? '66%' : '100%',
                      backgroundColor: strengthColors[passwordStrength.level],
                    }}
                  />
                  <p className="mt-1 text-xs font-medium" style={{ color: strengthColors[passwordStrength.level] }}>
                    {passwordStrength.label}
                  </p>
                </div>
              )}
              <p className="mt-1 text-xs" style={{ color: 'var(--muted)' }}>Must be at least 10 characters with a special character</p>
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
                className="input"
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
                className="input"
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
                className="input"
                style={{ color: beltGrade ? undefined : 'var(--muted)' }}
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

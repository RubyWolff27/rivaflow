import { useState, useEffect, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { waitlistApi } from '../api/client';

const BELT_RANKS = ['White', 'Blue', 'Purple', 'Brown', 'Black'];

export default function Waitlist() {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [gymName, setGymName] = useState('');
  const [beltRank, setBeltRank] = useState('');
  const [referralSource, setReferralSource] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState<{ position: number; message: string } | null>(null);
  const [waitlistCount, setWaitlistCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    waitlistApi.getCount().then(res => {
      if (!cancelled) setWaitlistCount(res.data.count);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const res = await waitlistApi.join({
        email,
        first_name: firstName || undefined,
        gym_name: gymName || undefined,
        belt_rank: beltRank || undefined,
        referral_source: referralSource || undefined,
      });
      setSuccess(res.data);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to join waitlist. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg)' }}>
        <div className="max-w-md w-full text-center space-y-6">
          <div
            className="p-8 rounded-lg border-2"
            style={{
              backgroundColor: 'var(--surface)',
              borderColor: 'var(--accent)',
            }}
          >
            <div className="text-5xl mb-4">🥋</div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text)' }}>
              You're on the list!
            </h2>
            <p className="text-lg mb-4" style={{ color: 'var(--muted)' }}>
              {success.message}
            </p>
            <div
              className="inline-block px-4 py-2 rounded-full text-sm font-semibold"
              style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
            >
              Position #{success.position}
            </div>
            <p className="mt-6 text-sm" style={{ color: 'var(--muted)' }}>
              We'll send you an invite when it's your turn.
              <br />
              Keep an eye on your inbox.
            </p>
          </div>

          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Already have an account?{' '}
            <Link to="/login" className="font-medium hover:opacity-80" style={{ color: 'var(--accent)' }}>
              Login
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="max-w-md w-full space-y-6">
        {/* Hero */}
        <div className="text-center">
          <h1 className="text-4xl font-extrabold mb-2" style={{ color: 'var(--text)' }}>
            RivaFlow
          </h1>
          <p className="text-lg" style={{ color: 'var(--accent)' }}>
            Train with intent. Flow to mastery.
          </p>
          <p className="mt-3 text-sm" style={{ color: 'var(--muted)' }}>
            The training OS for BJJ athletes. Log sessions, track progress, earn milestones, and connect with your gym crew.
          </p>
          {waitlistCount !== null && waitlistCount > 0 && (
            <p className="mt-2 text-xs font-medium" style={{ color: 'var(--muted)' }}>
              {waitlistCount} {waitlistCount === 1 ? 'person' : 'people'} already waiting
            </p>
          )}
        </div>

        {/* Signup form */}
        <div className="p-6 rounded-lg" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text)' }}>
            Join the Waitlist
          </h2>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md p-3" style={{ backgroundColor: '#FEE2E2' }}>
                <p className="text-sm" style={{ color: '#991B1B' }}>{error}</p>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Email address *
              </label>
              <input
                id="email"
                type="email"
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
              <label htmlFor="firstName" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                First name
              </label>
              <input
                id="firstName"
                type="text"
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="gymName" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Gym
                </label>
                <input
                  id="gymName"
                  type="text"
                  value={gymName}
                  onChange={(e) => setGymName(e.target.value)}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                  style={{
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--surface)',
                    color: 'var(--text)',
                  }}
                  placeholder="e.g. Atos HQ"
                />
              </div>

              <div>
                <label htmlFor="beltRank" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Belt
                </label>
                <select
                  id="beltRank"
                  value={beltRank}
                  onChange={(e) => setBeltRank(e.target.value)}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                  style={{
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--surface)',
                    color: beltRank ? 'var(--text)' : 'var(--muted)',
                  }}
                >
                  <option value="">Select belt</option>
                  {BELT_RANKS.map(belt => (
                    <option key={belt} value={belt.toLowerCase()}>{belt}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="referralSource" className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                How did you hear about us?
              </label>
              <input
                id="referralSource"
                type="text"
                value={referralSource}
                onChange={(e) => setReferralSource(e.target.value)}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border focus:outline-none focus:ring-2 sm:text-sm"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surface)',
                  color: 'var(--text)',
                }}
                placeholder="Instagram, friend, Reddit..."
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#FFFFFF',
              }}
            >
              {isLoading ? 'Joining...' : 'Join Waitlist'}
            </button>
          </form>
        </div>

        {/* Features preview */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { icon: '📊', label: 'Session Tracking' },
            { icon: '🔥', label: 'Streaks & Milestones' },
            { icon: '🤝', label: 'Training Partners' },
            { icon: '📈', label: 'Analytics & Reports' },
          ].map(feature => (
            <div
              key={feature.label}
              className="p-3 rounded-lg text-center text-sm"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <div className="text-xl mb-1">{feature.icon}</div>
              <span style={{ color: 'var(--muted)' }}>{feature.label}</span>
            </div>
          ))}
        </div>

        <p className="text-center text-sm" style={{ color: 'var(--muted)' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-medium hover:opacity-80" style={{ color: 'var(--accent)' }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

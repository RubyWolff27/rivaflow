import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi } from '../api/client';
import { logger } from '../utils/logger';
import { ArrowLeft, Users, Swords, TrendingUp, Calendar, Target, BarChart3 } from 'lucide-react';
import { CardSkeleton } from '../components/ui';

interface PartnerRelationship {
  partner_id: number;
  partner_name: string;
  total_rolls: number;
  total_sessions_together: number;
  first_roll_date: string;
  last_roll_date: string;
  submissions_for: number;
  submissions_against: number;
  days_known: number;
  avg_rolls_per_session: number;
  favorite_techniques_against: string[];
  most_common_positions: string[];
  [key: string]: unknown;
}

export default function PartnerStats() {
  usePageTitle('Training Partner');
  const { partnerId } = useParams<{ partnerId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<PartnerRelationship | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!partnerId) return;
    let cancelled = false;
    const load = async () => {
      try {
        setLoading(true);
        const res = await analyticsApi.partnerRelationship(parseInt(partnerId));
        if (!cancelled) setData(res.data);
      } catch (err) {
        if (!cancelled) {
          setError('Could not load partner stats');
          logger.error('Failed to load partner relationship', err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [partnerId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={6} />
        <CardSkeleton lines={4} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12">
        <Users className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
        <p style={{ color: 'var(--muted)' }}>{error || 'Partner not found'}</p>
        <button onClick={() => navigate(-1)} className="text-sm mt-2 underline" style={{ color: 'var(--accent)' }}>
          Go back
        </button>
      </div>
    );
  }

  const subRate = data.total_rolls > 0
    ? Math.round((data.submissions_for / data.total_rolls) * 100)
    : 0;
  const subAgainstRate = data.total_rolls > 0
    ? Math.round((data.submissions_against / data.total_rolls) * 100)
    : 0;

  const monthsKnown = Math.max(1, Math.round(data.days_known / 30));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:opacity-80 transition-opacity"
          style={{ backgroundColor: 'var(--surfaceElev)' }}
          aria-label="Go back"
        >
          <ArrowLeft className="w-5 h-5" style={{ color: 'var(--text)' }} />
        </button>
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            {data.partner_name}
          </h1>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Training Partner
          </p>
        </div>
      </div>

      {/* Hero stat: Rolls together */}
      <div
        className="rounded-[14px] p-6 text-center"
        style={{
          background: 'linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 70%, #000))',
          color: '#FFFFFF',
        }}
      >
        <Users className="w-8 h-8 mx-auto mb-2 opacity-80" />
        <p className="text-4xl font-black tabular-nums">{data.total_rolls}</p>
        <p className="text-sm opacity-80 mt-1">Rolls Together</p>
        <p className="text-xs opacity-60 mt-2">
          Across {data.total_sessions_together} sessions over {monthsKnown} month{monthsKnown !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<Swords className="w-4 h-4" />}
          label="Subs Caught"
          value={data.submissions_for}
          sub={`${subRate}% rate`}
          color="#10B981"
        />
        <StatCard
          icon={<Target className="w-4 h-4" />}
          label="Subs Conceded"
          value={data.submissions_against}
          sub={`${subAgainstRate}% rate`}
          color="#EF4444"
        />
        <StatCard
          icon={<Calendar className="w-4 h-4" />}
          label="First Roll"
          value={new Date(data.first_roll_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
          sub={`${data.days_known} days ago`}
        />
        <StatCard
          icon={<TrendingUp className="w-4 h-4" />}
          label="Avg Rolls/Session"
          value={data.avg_rolls_per_session?.toFixed(1) || '—'}
          sub="when training together"
        />
      </div>

      {/* Techniques */}
      {data.favorite_techniques_against && data.favorite_techniques_against.length > 0 && (
        <div className="rounded-[14px] p-5" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
            <BarChart3 className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            Top Techniques Against {data.partner_name.split(' ')[0]}
          </h3>
          <div className="flex flex-wrap gap-2">
            {data.favorite_techniques_against.map((tech, i) => (
              <span
                key={i}
                className="px-3 py-1.5 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: 'var(--surfaceElev)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                }}
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="rounded-[14px] p-5" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
          Training Timeline
        </h3>
        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--muted)' }}>
          <div>
            <p className="font-medium" style={{ color: 'var(--text)' }}>First trained</p>
            <p>{new Date(data.first_roll_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
          </div>
          <div className="flex-1 mx-4 h-px" style={{ backgroundColor: 'var(--border)' }} />
          <div className="text-right">
            <p className="font-medium" style={{ color: 'var(--text)' }}>Last trained</p>
            <p>{new Date(data.last_roll_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
          </div>
        </div>
      </div>

      {/* Back to friends */}
      <div className="text-center">
        <Link
          to="/friends"
          className="text-sm underline"
          style={{ color: 'var(--accent)' }}
        >
          View all training partners
        </Link>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub: string;
  color?: string;
}) {
  return (
    <div className="rounded-[14px] p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-1.5 mb-2">
        <span style={{ color: color || 'var(--accent)' }}>{icon}</span>
        <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>{label}</span>
      </div>
      <p className="text-xl font-bold tabular-nums" style={{ color: 'var(--text)' }}>{value}</p>
      <p className="text-[10px] mt-0.5" style={{ color: 'var(--muted)' }}>{sub}</p>
    </div>
  );
}

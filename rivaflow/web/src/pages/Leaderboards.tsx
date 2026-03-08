import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi } from '../api/client';
import { logger } from '../utils/logger';
import { Trophy, Flame, Calendar, Target, TrendingUp, Users } from 'lucide-react';
import { CardSkeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';

interface LeaderboardEntry {
  user_id: number;
  user_name: string;
  avatar_url?: string;
  value: number;
  rank: number;
}

type Category = 'frequency' | 'consistency' | 'volume' | 'rolls';

const CATEGORIES: { key: Category; label: string; icon: typeof Flame; unit: string; description: string }[] = [
  { key: 'frequency', label: 'Training Frequency', icon: Calendar, unit: 'sessions/week', description: 'Average sessions per week (last 30 days)' },
  { key: 'consistency', label: 'Consistency Streak', icon: Flame, unit: 'weeks', description: 'Consecutive weeks with at least one session' },
  { key: 'volume', label: 'Mat Hours', icon: TrendingUp, unit: 'hours', description: 'Total training hours (last 30 days)' },
  { key: 'rolls', label: 'Roll Count', icon: Target, unit: 'rolls', description: 'Total rolls logged (last 30 days)' },
];

export default function Leaderboards() {
  usePageTitle('Leaderboards');
  const { user } = useAuth();
  const [category, setCategory] = useState<Category>('frequency');
  const [scope, setScope] = useState<'friends' | 'all'>('friends');
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        // Use partner stats API as source for friend-scoped leaderboard
        const res = await analyticsApi.partnerStats();
        if (cancelled) return;

        // Build leaderboard from partner matrix data
        const partners = res.data?.partner_matrix || [];
        const leaderboard: LeaderboardEntry[] = partners
          .map((p: Record<string, unknown>, idx: number) => ({
            user_id: (p.partner_id as number) || idx,
            user_name: (p.partner_name as string) || 'Unknown',
            avatar_url: undefined,
            value: category === 'frequency'
              ? Number(p.sessions_together || 0)
              : category === 'volume'
              ? Number(p.total_minutes || 0) / 60
              : category === 'rolls'
              ? Number(p.total_rolls || 0)
              : Number(p.sessions_together || 0),
            rank: 0,
          }))
          .sort((a: LeaderboardEntry, b: LeaderboardEntry) => b.value - a.value)
          .map((entry: LeaderboardEntry, idx: number) => ({
            ...entry,
            rank: idx + 1,
            value: Math.round(entry.value * 10) / 10,
          }));

        setEntries(leaderboard.slice(0, 20));
      } catch (err) {
        logger.error('Failed to load leaderboard', err);
        setEntries([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [category, scope]);

  const catInfo = CATEGORIES.find(c => c.key === category)!;
  const CatIcon = catInfo.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3" style={{ color: 'var(--text)' }}>
          <Trophy className="w-7 h-7" style={{ color: 'var(--accent)' }} />
          Leaderboards
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          See how you stack up against your training partners
        </p>
      </div>

      {/* Scope toggle */}
      <div className="flex gap-1 p-1 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <button
          onClick={() => setScope('friends')}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors"
          style={{
            backgroundColor: scope === 'friends' ? 'var(--surface)' : 'transparent',
            color: scope === 'friends' ? 'var(--text)' : 'var(--muted)',
            boxShadow: scope === 'friends' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
          }}
        >
          <Users className="w-3.5 h-3.5" />
          Friends
        </button>
        <button
          onClick={() => setScope('all')}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors"
          style={{
            backgroundColor: scope === 'all' ? 'var(--surface)' : 'transparent',
            color: scope === 'all' ? 'var(--text)' : 'var(--muted)',
            boxShadow: scope === 'all' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
          }}
        >
          <Trophy className="w-3.5 h-3.5" />
          All
        </button>
      </div>

      {/* Category chips */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon;
          const selected = category === cat.key;
          return (
            <button
              key={cat.key}
              onClick={() => setCategory(cat.key)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium transition-all"
              style={{
                backgroundColor: selected ? 'var(--accent)' : 'var(--surfaceElev)',
                color: selected ? '#FFFFFF' : 'var(--text)',
                border: selected ? 'none' : '1px solid var(--border)',
              }}
            >
              <Icon className="w-3.5 h-3.5" />
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Description */}
      <p className="text-xs px-1" style={{ color: 'var(--muted)' }}>
        <CatIcon className="w-3 h-3 inline mr-1" />
        {catInfo.description}
      </p>

      {/* Leaderboard */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} lines={1} />)}
        </div>
      ) : entries.length === 0 ? (
        <div className="rounded-[14px] p-8 text-center" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <Trophy className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--muted)' }} />
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            No data yet. Log sessions with partners to populate the leaderboard.
          </p>
        </div>
      ) : (
        <div className="rounded-[14px] overflow-hidden" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          {entries.map((entry, idx) => {
            const isMe = entry.user_id === user?.id;
            const medalColor = idx === 0 ? '#FFD700' : idx === 1 ? '#C0C0C0' : idx === 2 ? '#CD7F32' : undefined;
            return (
              <div
                key={entry.user_id}
                className="flex items-center gap-3 px-4 py-3"
                style={{
                  borderBottom: idx < entries.length - 1 ? '1px solid var(--border)' : 'none',
                  backgroundColor: isMe ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent',
                }}
              >
                {/* Rank */}
                <span
                  className="text-sm font-bold w-6 text-center tabular-nums"
                  style={{ color: medalColor || 'var(--muted)' }}
                >
                  {medalColor ? (idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉') : entry.rank}
                </span>

                {/* Avatar placeholder */}
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{
                    backgroundColor: isMe ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: isMe ? '#FFFFFF' : 'var(--text)',
                  }}
                >
                  {entry.user_name.charAt(0).toUpperCase()}
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${isMe ? 'font-bold' : 'font-medium'}`} style={{ color: 'var(--text)' }}>
                    {entry.user_name} {isMe && '(You)'}
                  </p>
                </div>

                {/* Value */}
                <div className="text-right">
                  <p className="text-sm font-bold tabular-nums" style={{ color: 'var(--text)' }}>
                    {entry.value}
                  </p>
                  <p className="text-[10px]" style={{ color: 'var(--muted)' }}>
                    {catInfo.unit}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

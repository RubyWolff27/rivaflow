import { useState } from 'react';
import { Trophy, Plus, Calendar, Users, Target, Flame, Clock, ChevronDown, ChevronUp } from 'lucide-react';

export interface Challenge {
  id: number;
  name: string;
  challenge_type: 'mat_hours' | 'session_count' | 'roll_count' | 'streak_days';
  target_value: number;
  start_date: string;
  end_date: string;
  participants: ChallengeParticipant[];
  created_by: string;
}

export interface ChallengeParticipant {
  user_id: number;
  user_name: string;
  current_value: number;
  progress_pct: number;
  rank: number;
}

const CHALLENGE_TYPES = [
  { value: 'mat_hours', label: 'Mat Hours', icon: Clock, unit: 'hours' },
  { value: 'session_count', label: 'Sessions', icon: Target, unit: 'sessions' },
  { value: 'roll_count', label: 'Rolls', icon: Flame, unit: 'rolls' },
  { value: 'streak_days', label: 'Streak', icon: Calendar, unit: 'days' },
];

interface GroupChallengesProps {
  challenges: Challenge[];
  onCreateChallenge?: (data: {
    name: string;
    challenge_type: string;
    target_value: number;
    duration_days: number;
  }) => void;
  isAdmin?: boolean;
}

export default function GroupChallenges({ challenges, onCreateChallenge, isAdmin }: GroupChallengesProps) {
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '',
    challenge_type: 'session_count',
    target_value: 10,
    duration_days: 30,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    onCreateChallenge?.(form);
    setForm({ name: '', challenge_type: 'session_count', target_value: 10, duration_days: 30 });
    setShowForm(false);
  };

  const activeChallenges = challenges.filter(c => new Date(c.end_date) >= new Date());
  const pastChallenges = challenges.filter(c => new Date(c.end_date) < new Date());

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold flex items-center gap-2" style={{ color: 'var(--text)' }}>
          <Trophy className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          Challenges
        </h3>
        {isAdmin && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            <Plus className="w-3 h-3" />
            New
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="rounded-[14px] p-4 space-y-3" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <input
            type="text"
            placeholder="Challenge name (e.g., March Mat Marathon)"
            value={form.name}
            onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
          />
          <div className="grid grid-cols-2 gap-2">
            <select
              value={form.challenge_type}
              onChange={(e) => setForm(f => ({ ...f, challenge_type: e.target.value }))}
              className="px-3 py-2 rounded-lg text-sm"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
            >
              {CHALLENGE_TYPES.map(ct => (
                <option key={ct.value} value={ct.value}>{ct.label}</option>
              ))}
            </select>
            <input
              type="number"
              min={1}
              value={form.target_value}
              onChange={(e) => setForm(f => ({ ...f, target_value: parseInt(e.target.value) || 1 }))}
              className="px-3 py-2 rounded-lg text-sm"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
              placeholder="Target"
            />
          </div>
          <select
            value={form.duration_days}
            onChange={(e) => setForm(f => ({ ...f, duration_days: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
          >
            <option value={7}>1 Week</option>
            <option value={14}>2 Weeks</option>
            <option value={30}>1 Month</option>
            <option value={60}>2 Months</option>
            <option value={90}>3 Months</option>
          </select>
          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 px-3 py-2 rounded-lg text-sm font-medium"
              style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
            >
              Create Challenge
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-3 py-2 rounded-lg text-sm"
              style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Active challenges */}
      {activeChallenges.length === 0 && pastChallenges.length === 0 ? (
        <div className="rounded-[14px] p-6 text-center" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <Trophy className="w-10 h-10 mx-auto mb-2" style={{ color: 'var(--muted)' }} />
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            No challenges yet. {isAdmin ? 'Create one to get started!' : 'Ask a group admin to create one.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {activeChallenges.map(challenge => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              expanded={expanded === challenge.id}
              onToggle={() => setExpanded(expanded === challenge.id ? null : challenge.id)}
              isActive
            />
          ))}
          {pastChallenges.length > 0 && (
            <>
              <p className="text-xs font-medium pt-2" style={{ color: 'var(--muted)' }}>Past</p>
              {pastChallenges.slice(0, 3).map(challenge => (
                <ChallengeCard
                  key={challenge.id}
                  challenge={challenge}
                  expanded={expanded === challenge.id}
                  onToggle={() => setExpanded(expanded === challenge.id ? null : challenge.id)}
                  isActive={false}
                />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function ChallengeCard({ challenge, expanded, onToggle, isActive }: {
  challenge: Challenge;
  expanded: boolean;
  onToggle: () => void;
  isActive: boolean;
}) {
  const typeInfo = CHALLENGE_TYPES.find(ct => ct.value === challenge.challenge_type) || CHALLENGE_TYPES[1];
  const TypeIcon = typeInfo.icon;
  const daysLeft = Math.max(0, Math.ceil((new Date(challenge.end_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)));
  const leader = challenge.participants.length > 0
    ? challenge.participants.reduce((a, b) => a.progress_pct > b.progress_pct ? a : b)
    : null;

  return (
    <div
      className="rounded-[14px] overflow-hidden"
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        opacity: isActive ? 1 : 0.6,
      }}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <TypeIcon className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{challenge.name}</p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              {isActive ? `${daysLeft}d left` : 'Completed'} · {challenge.participants.length} participants · {challenge.target_value} {typeInfo.unit}
            </p>
          </div>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />
        }
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {/* Leader */}
          {leader && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
              <Users className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
              <span className="text-xs" style={{ color: 'var(--muted)' }}>Leader:</span>
              <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{leader.user_name}</span>
              <span className="text-xs ml-auto tabular-nums" style={{ color: 'var(--accent)' }}>
                {leader.current_value} / {challenge.target_value}
              </span>
            </div>
          )}

          {/* Leaderboard */}
          <div className="space-y-1">
            {challenge.participants
              .sort((a, b) => b.progress_pct - a.progress_pct)
              .map((p, i) => (
                <div key={p.user_id} className="flex items-center gap-2 px-3 py-1.5">
                  <span className="text-xs font-bold w-5 text-right tabular-nums" style={{ color: 'var(--muted)' }}>
                    {i + 1}.
                  </span>
                  <span className="text-xs flex-1" style={{ color: 'var(--text)' }}>{p.user_name}</span>
                  <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, p.progress_pct)}%`,
                        backgroundColor: p.progress_pct >= 100 ? '#10B981' : 'var(--accent)',
                      }}
                    />
                  </div>
                  <span className="text-xs tabular-nums w-12 text-right" style={{ color: 'var(--muted)' }}>
                    {Math.round(p.progress_pct)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

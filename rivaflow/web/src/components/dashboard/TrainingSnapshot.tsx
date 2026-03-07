import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flame, ChevronRight, ChevronDown, Activity, User, Dumbbell } from 'lucide-react';
import { useTrainingSnapshot } from '../../hooks/useTrainingSnapshot';
import type { WeekDay, ClassTypeVolume } from '../../hooks/useTrainingSnapshot';
import { ACTIVITY_COLORS, ACTIVITY_LABELS } from '../../constants/activity';

interface TrainingSnapshotProps {
  readinessScore: number | null;
  streakCount: number;
  whoopRecovery: number | null;
}

function getReadinessColor(score: number | null): string {
  if (score == null) return 'var(--muted)';
  if (score >= 16) return 'var(--success)';
  if (score >= 12) return 'var(--warning)';
  return 'var(--danger)';
}

function getReadinessLabel(score: number | null): string {
  if (score == null) return 'No check-in';
  if (score >= 16) return 'Train Hard';
  if (score >= 12) return 'Light Session';
  return 'Rest Day';
}

function formatRelativeDate(dateStr: string): string {
  const today = new Date();
  const date = new Date(dateStr + 'T00:00:00');
  const diffDays = Math.floor((today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short' });
}

/* ── Profile Card ── */
function ProfileCard({ profile, totalSessions, totalHours, totalRolls }: {
  profile: { first_name: string; last_name: string; avatar_url: string | null; current_grade: string | null };
  totalSessions: number;
  totalHours: number;
  totalRolls: number;
}) {
  const initials = `${profile.first_name.charAt(0)}${profile.last_name.charAt(0)}`.toUpperCase();

  return (
    <div className="flex flex-col items-center text-center">
      <Link to="/profile" className="group">
        {profile.avatar_url ? (
          <img
            src={profile.avatar_url}
            alt={`${profile.first_name} ${profile.last_name}`}
            className="w-16 h-16 rounded-full object-cover mb-2 group-hover:opacity-80 transition-opacity"
          />
        ) : (
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold mb-2 group-hover:opacity-80 transition-opacity"
            style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
          >
            {initials || <User className="w-6 h-6" />}
          </div>
        )}
      </Link>
      <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>
        {profile.first_name} {profile.last_name}
      </p>
      {profile.current_grade && (
        <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
          {profile.current_grade}
        </p>
      )}

      {/* Stats row — like Strava's Following / Followers / Activities */}
      <div className="flex items-center justify-center gap-6 mt-3 pt-3 w-full" style={{ borderTop: '1px solid var(--border)' }}>
        <div>
          <p className="text-base font-bold tabular-nums" style={{ color: 'var(--text)' }}>{totalSessions}</p>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Sessions</p>
        </div>
        <div>
          <p className="text-base font-bold tabular-nums" style={{ color: 'var(--text)' }}>{totalHours.toFixed(1)}</p>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Hours</p>
        </div>
        <div>
          <p className="text-base font-bold tabular-nums" style={{ color: 'var(--text)' }}>{totalRolls}</p>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Rolls</p>
        </div>
      </div>
    </div>
  );
}

/* ── Latest Activity ── */
function LatestActivity({ session }: { session: { class_type: string; gym_name: string; duration_mins: number; session_date: string; rolls: number } }) {
  return (
    <Link to="/sessions" className="block group">
      <p className="text-[10px] font-medium uppercase tracking-wider mb-1.5" style={{ color: 'var(--muted)' }}>
        Latest Activity
      </p>
      <div className="flex items-start gap-2.5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
          style={{ backgroundColor: `${ACTIVITY_COLORS[session.class_type] || '#6B7280'}20` }}
        >
          <Dumbbell className="w-4 h-4" style={{ color: ACTIVITY_COLORS[session.class_type] || '#6B7280' }} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold group-hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
            {ACTIVITY_LABELS[session.class_type] || session.class_type}
          </p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {formatRelativeDate(session.session_date)} &middot; {session.gym_name}
          </p>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs tabular-nums" style={{ color: 'var(--muted)' }}>
              {session.duration_mins}min
            </span>
            {session.rolls > 0 && (
              <span className="text-xs tabular-nums" style={{ color: 'var(--muted)' }}>
                {session.rolls} rolls
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

/* ── Streak Grid ── */
function WeekStreakGrid({ weekDays, streakCount }: { weekDays: WeekDay[]; streakCount: number }) {
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  return (
    <div>
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
          Your Streak
        </p>
        {streakCount > 0 && (
          <div className="flex items-center gap-1">
            <Flame className="w-3.5 h-3.5" style={{ color: '#F59E0B' }} />
            <span className="text-xs font-bold" style={{ color: '#F59E0B' }}>
              {streakCount} {streakCount === 1 ? 'day' : 'days'}
            </span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-7 gap-0.5">
        {/* Day labels */}
        {weekDays.map((day, i) => {
          const isToday = day.date === todayStr;
          return (
            <div key={`label-${i}`} className="text-center">
              <span
                className="text-[10px] font-semibold"
                style={{ color: isToday ? 'var(--accent)' : 'var(--muted)' }}
              >
                {day.label}
              </span>
            </div>
          );
        })}
        {/* Session dots */}
        {weekDays.map((day) => {
          const isToday = day.date === todayStr;
          const hasSessions = day.sessions.length > 0;
          return (
            <div key={day.date} className="flex flex-col items-center gap-0.5 py-1 min-h-[28px]">
              {hasSessions ? (
                day.sessions.map((s, i) => (
                  <div
                    key={i}
                    className="w-4 h-4 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: ACTIVITY_COLORS[s.class_type] || '#6B7280' }}
                    title={`${ACTIVITY_LABELS[s.class_type] || s.class_type} — ${s.duration_mins}min`}
                  >
                    <span className="text-[8px] font-bold text-white">
                      {Math.round(s.duration_mins / 60) || ''}
                    </span>
                  </div>
                ))
              ) : (
                <div
                  className="w-4 h-4 rounded-full"
                  style={{
                    border: `2px solid ${isToday ? 'var(--accent)' : 'var(--border)'}`,
                    opacity: isToday ? 1 : 0.5,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Training Log Link (Strava-style row) ── */
function TrainingLogLink() {
  return (
    <Link
      to="/sessions"
      className="flex items-center justify-between py-2.5 group"
    >
      <span className="text-sm font-medium group-hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
        Your Training Log
      </span>
      <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
    </Link>
  );
}

/* ── Activity Type Icons (filter row like Strava) ── */
function ActivityTypeIcons({ volumes }: { volumes: ClassTypeVolume[] }) {
  if (volumes.length === 0) return null;
  return (
    <div className="flex items-center gap-2 py-2">
      {volumes.map((v) => (
        <div
          key={v.type}
          className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium"
          style={{
            backgroundColor: `${ACTIVITY_COLORS[v.type] || '#6B7280'}15`,
            color: ACTIVITY_COLORS[v.type] || '#6B7280',
          }}
          title={`${ACTIVITY_LABELS[v.type] || v.type}: ${v.count} sessions, ${v.hours.toFixed(1)}h`}
        >
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: ACTIVITY_COLORS[v.type] || '#6B7280' }}
          />
          {ACTIVITY_LABELS[v.type] || v.type}
        </div>
      ))}
    </div>
  );
}

/* ── Readiness Insight (like Strava's Relative Effort) ── */
function ReadinessInsight({ score, whoopRecovery }: { score: number | null; whoopRecovery: number | null }) {
  const color = getReadinessColor(score);
  const label = getReadinessLabel(score);

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <Activity className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
        <p className="text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
          Readiness
        </p>
      </div>

      <div className="flex items-center gap-4">
        {/* Readiness score ring */}
        <div className="relative flex-shrink-0">
          <svg width="52" height="52" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="22" fill="none" stroke="var(--border)" strokeWidth="4" />
            <circle
              cx="26" cy="26" r="22"
              fill="none"
              stroke={color}
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={`${((score || 0) / 20) * 138.2} 138.2`}
              transform="rotate(-90 26 26)"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold" style={{ color: 'var(--text)' }}>
              {score != null ? score : '--'}
            </span>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold" style={{ color }}>{label}</p>
          {whoopRecovery != null && (
            <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
              WHOOP {whoopRecovery}% recovery
            </p>
          )}
          <p className="text-[11px] mt-1" style={{ color: 'var(--muted)' }}>
            {score != null && score >= 16
              ? 'Your body is ready for a hard training session.'
              : score != null && score >= 12
              ? 'Consider a lighter session or technique focus.'
              : score != null
              ? 'Rest or very light movement recommended.'
              : 'Check in to see your readiness score.'}
          </p>
        </div>
      </div>
    </div>
  );
}

/* ── Mobile Accordion ── */
function AccordionSection({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full py-3 px-1 min-h-[44px]"
        style={{ color: 'var(--text)' }}
      >
        <span className="text-sm font-medium">{title}</span>
        <ChevronDown
          className="w-4 h-4 transition-transform"
          style={{ color: 'var(--muted)', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </button>
      <div
        className="overflow-hidden transition-all duration-200"
        style={{ maxHeight: open ? '600px' : '0', opacity: open ? 1 : 0, paddingBottom: open ? '12px' : '0' }}
      >
        {children}
      </div>
    </div>
  );
}

/* ── Main Component ── */
export default function TrainingSnapshot({ readinessScore, streakCount, whoopRecovery }: TrainingSnapshotProps) {
  const { loading, weekDays, volumes, totalSessions, totalHours, totalRolls, lastSession, profile } = useTrainingSnapshot();

  if (loading) {
    return (
      <div className="rounded-[14px] p-5 space-y-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div className="animate-pulse space-y-4">
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-[var(--surfaceElev)]" />
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-1/2" />
            <div className="h-3 bg-[var(--surfaceElev)] rounded w-1/3" />
          </div>
          <div className="h-10 bg-[var(--surfaceElev)] rounded" />
          <div className="h-24 bg-[var(--surfaceElev)] rounded" />
        </div>
      </div>
    );
  }

  const sidebarContent = (
    <div className="space-y-0">
      {/* Profile card */}
      {profile && (
        <div className="pb-4">
          <ProfileCard
            profile={profile}
            totalSessions={totalSessions}
            totalHours={totalHours}
            totalRolls={totalRolls}
          />
        </div>
      )}

      {/* Latest activity */}
      {lastSession && (
        <div className="py-4" style={{ borderTop: '1px solid var(--border)' }}>
          <LatestActivity session={lastSession} />
        </div>
      )}

      {/* Streak grid */}
      <div className="py-4" style={{ borderTop: '1px solid var(--border)' }}>
        <WeekStreakGrid weekDays={weekDays} streakCount={streakCount} />
      </div>

      {/* Training Log link */}
      <div style={{ borderTop: '1px solid var(--border)' }}>
        <TrainingLogLink />
      </div>

      {/* Activity type filter icons */}
      {volumes.length > 0 && (
        <div style={{ borderTop: '1px solid var(--border)' }}>
          <ActivityTypeIcons volumes={volumes} />
        </div>
      )}

      {/* Readiness insight */}
      <div className="py-4" style={{ borderTop: '1px solid var(--border)' }}>
        <ReadinessInsight score={readinessScore} whoopRecovery={whoopRecovery} />
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <div
        className="hidden lg:block rounded-[14px] p-5 sticky top-4"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        {sidebarContent}
      </div>

      {/* Mobile accordion */}
      <div
        className="lg:hidden rounded-[14px] px-4 py-1"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        {profile && (
          <div className="py-3" style={{ borderBottom: '1px solid var(--border)' }}>
            <ProfileCard
              profile={profile}
              totalSessions={totalSessions}
              totalHours={totalHours}
              totalRolls={totalRolls}
            />
          </div>
        )}
        <AccordionSection title="This Week" defaultOpen>
          <div className="space-y-4">
            <WeekStreakGrid weekDays={weekDays} streakCount={streakCount} />
            {volumes.length > 0 && <ActivityTypeIcons volumes={volumes} />}
          </div>
        </AccordionSection>
        {lastSession && (
          <AccordionSection title="Latest Activity">
            <LatestActivity session={lastSession} />
          </AccordionSection>
        )}
        <AccordionSection title="Readiness">
          <ReadinessInsight score={readinessScore} whoopRecovery={whoopRecovery} />
        </AccordionSection>
        <div className="py-2">
          <TrainingLogLink />
        </div>
      </div>
    </>
  );
}

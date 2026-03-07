import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flame, ChevronDown, Activity, User } from 'lucide-react';
import { useTrainingSnapshot } from '../../hooks/useTrainingSnapshot';
import { ACTIVITY_COLORS, ACTIVITY_LABELS } from '../../constants/activity';

interface TrainingSnapshotProps {
  readinessScore: number | null;
  streakCount: number;
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

function ProfileCard({ profile }: { profile: { first_name: string; last_name: string; avatar_url: string | null; current_grade: string | null } }) {
  const initials = `${profile.first_name.charAt(0)}${profile.last_name.charAt(0)}`.toUpperCase();

  return (
    <Link to="/profile" className="flex items-center gap-3 group">
      {profile.avatar_url ? (
        <img
          src={profile.avatar_url}
          alt={`${profile.first_name} ${profile.last_name}`}
          className="w-12 h-12 rounded-full object-cover"
        />
      ) : (
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          {initials || <User className="w-5 h-5" />}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-sm font-semibold truncate group-hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
          {profile.first_name} {profile.last_name}
        </p>
        {profile.current_grade && (
          <p className="text-xs truncate" style={{ color: 'var(--muted)' }}>
            {profile.current_grade}
          </p>
        )}
      </div>
    </Link>
  );
}

function WeekStreakGrid({ weekDays }: { weekDays: { label: string; date: string; sessions: { class_type: string }[] }[] }) {
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wider mb-2" style={{ color: 'var(--muted)' }}>
        This Week
      </p>
      <div className="grid grid-cols-7 gap-1">
        {weekDays.map((day) => {
          const isToday = day.date === todayStr;
          return (
            <div key={day.date} className="flex flex-col items-center gap-1">
              <span
                className="text-[10px] font-medium"
                style={{ color: isToday ? 'var(--accent)' : 'var(--muted)' }}
              >
                {day.label}
              </span>
              <div className="flex flex-col items-center gap-0.5 min-h-[20px]">
                {day.sessions.length > 0 ? (
                  day.sessions.map((s, i) => (
                    <div
                      key={i}
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: ACTIVITY_COLORS[s.class_type] || '#6B7280' }}
                      title={ACTIVITY_LABELS[s.class_type] || s.class_type}
                    />
                  ))
                ) : (
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ border: '1.5px solid var(--border)' }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ActivityVolume({ volumes, totalSessions }: { volumes: { type: string; count: number }[]; totalSessions: number }) {
  if (volumes.length === 0) return null;
  const maxCount = Math.max(...volumes.map(v => v.count), 1);

  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wider mb-2" style={{ color: 'var(--muted)' }}>
        Activity Mix
      </p>
      <div className="space-y-2">
        {volumes.map((v) => (
          <div key={v.type} className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: ACTIVITY_COLORS[v.type] || '#6B7280' }}
            />
            <span className="text-xs w-16 truncate" style={{ color: 'var(--text)' }}>
              {ACTIVITY_LABELS[v.type] || v.type}
            </span>
            <div className="flex-1 h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
              <div
                className="h-2 rounded-full transition-all"
                style={{
                  width: `${(v.count / maxCount) * 100}%`,
                  backgroundColor: ACTIVITY_COLORS[v.type] || '#6B7280',
                }}
              />
            </div>
            <span className="text-xs tabular-nums w-4 text-right" style={{ color: 'var(--muted)' }}>
              {v.count}
            </span>
          </div>
        ))}
      </div>
      <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
        {totalSessions} session{totalSessions !== 1 ? 's' : ''} this week
      </p>
    </div>
  );
}

function ReadinessCompact({ score }: { score: number | null }) {
  const color = getReadinessColor(score);
  const label = getReadinessLabel(score);

  return (
    <Link to="/readiness" className="flex items-center gap-3 group">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ backgroundColor: `${color}18` }}
      >
        <Activity className="w-5 h-5" style={{ color }} />
      </div>
      <div>
        <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          {score != null ? `${score}/20` : '--'}
        </p>
        <p className="text-[11px]" style={{ color }}>{label}</p>
      </div>
    </Link>
  );
}

function StreakBadge({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ backgroundColor: 'rgba(245, 158, 11, 0.12)' }}
      >
        <Flame className="w-5 h-5" style={{ color: '#F59E0B' }} />
      </div>
      <div>
        <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          {count} day{count !== 1 ? 's' : ''}
        </p>
        <p className="text-[11px]" style={{ color: 'var(--muted)' }}>Current streak</p>
      </div>
    </div>
  );
}

/** Accordion section for mobile — uses details/summary for zero-JS progressive enhancement */
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
          style={{
            color: 'var(--muted)',
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        />
      </button>
      <div
        className="overflow-hidden transition-all duration-200"
        style={{
          maxHeight: open ? '500px' : '0',
          opacity: open ? 1 : 0,
          paddingBottom: open ? '12px' : '0',
        }}
      >
        {children}
      </div>
    </div>
  );
}

export default function TrainingSnapshot({ readinessScore, streakCount }: TrainingSnapshotProps) {
  const { loading, weekDays, volumes, totalSessions, profile } = useTrainingSnapshot();

  if (loading) {
    return (
      <div className="rounded-[14px] p-5 space-y-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div className="animate-pulse space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[var(--surfaceElev)]" />
            <div className="space-y-2 flex-1">
              <div className="h-4 bg-[var(--surfaceElev)] rounded w-2/3" />
              <div className="h-3 bg-[var(--surfaceElev)] rounded w-1/2" />
            </div>
          </div>
          <div className="h-8 bg-[var(--surfaceElev)] rounded" />
          <div className="h-20 bg-[var(--surfaceElev)] rounded" />
        </div>
      </div>
    );
  }

  // Desktop: full sidebar
  const sidebarContent = (
    <div className="space-y-5">
      {profile && <ProfileCard profile={profile} />}

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <WeekStreakGrid weekDays={weekDays} />
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <ActivityVolume volumes={volumes} totalSessions={totalSessions} />
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <div className="space-y-3">
          <ReadinessCompact score={readinessScore} />
          <StreakBadge count={streakCount} />
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
        <Link
          to="/sessions"
          className="text-xs font-medium hover:opacity-80 transition-opacity"
          style={{ color: 'var(--accent)' }}
        >
          Training Log →
        </Link>
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
            <ProfileCard profile={profile} />
          </div>
        )}
        <AccordionSection title="This Week" defaultOpen>
          <div className="space-y-4">
            <WeekStreakGrid weekDays={weekDays} />
            <ActivityVolume volumes={volumes} totalSessions={totalSessions} />
          </div>
        </AccordionSection>
        <AccordionSection title="Status">
          <div className="space-y-3">
            <ReadinessCompact score={readinessScore} />
            <StreakBadge count={streakCount} />
          </div>
        </AccordionSection>
        <div className="py-2">
          <Link
            to="/sessions"
            className="text-xs font-medium hover:opacity-80 transition-opacity"
            style={{ color: 'var(--accent)' }}
          >
            Training Log →
          </Link>
        </div>
      </div>
    </>
  );
}

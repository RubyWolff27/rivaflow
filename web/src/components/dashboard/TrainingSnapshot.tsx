import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, ChevronDown, User, Dumbbell } from 'lucide-react';
import { useTrainingSnapshot } from '../../hooks/useTrainingSnapshot';
import type { ClassTypeVolume } from '../../hooks/useTrainingSnapshot';
import { ACTIVITY_COLORS, ACTIVITY_LABELS } from '../../constants/activity';


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

      {/* Stats row — this week's training */}
      <p className="text-[10px] uppercase tracking-wide mt-3 pt-3" style={{ color: 'var(--muted)', borderTop: '1px solid var(--border)' }}>
        This Week
      </p>
      <div className="flex items-center justify-center gap-6 mt-1 w-full">
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
function LatestActivity({ session }: { session: { id: number; class_type: string; gym_name: string; duration_mins: number; session_date: string; rolls: number } }) {
  return (
    <Link to={`/session/${session.id}`} className="block group">
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
export default function TrainingSnapshot() {
  const { loading, volumes, totalSessions, totalHours, totalRolls, lastSession, profile } = useTrainingSnapshot();

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
          {volumes.length > 0 ? <ActivityTypeIcons volumes={volumes} /> : null}
        </AccordionSection>
        {lastSession && (
          <AccordionSection title="Latest Activity">
            <LatestActivity session={lastSession} />
          </AccordionSection>
        )}
        <div className="py-2">
          <TrainingLogLink />
        </div>
      </div>
    </>
  );
}

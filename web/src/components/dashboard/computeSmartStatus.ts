import type { Session, WeeklyGoalProgress, GymClass } from '../../types';

export function parseTimeToday(timeStr: string): Date {
  const parts = timeStr.split(':').map(Number);
  const d = new Date();
  d.setHours(parts[0], parts[1], parts[2] || 0, 0);
  return d;
}

export interface SmartStatus {
  type: string;
  headline: string;
  subtext?: string;
  icon: 'check' | 'clock' | 'alert' | 'calendar';
  iconColor: string;
  iconBg: string;
  showLogButton: boolean;
}

export function computeSmartStatus(
  intention: string | undefined,
  sessions: Session[],
  classes: GymClass[],
  goals: WeeklyGoalProgress | null,
): SmartStatus | null {
  const now = new Date();
  const hasSession = sessions.length > 0;

  // P1: Session logged + matches an ended gym class
  if (hasSession && classes.length > 0) {
    const matchedEnded = classes.some(c => {
      const endTime = parseTimeToday(c.end_time);
      if (now.getTime() < endTime.getTime() - 30 * 60 * 1000) return false;
      return sessions.some(s =>
        c.class_type === null || s.class_type === c.class_type
      );
    });
    if (matchedEnded) {
      return {
        type: 'trained-planned',
        headline: 'Nice work — trained as planned!',
        icon: 'check',
        iconColor: 'var(--success)',
        iconBg: 'var(--success-bg)',
        showLogButton: false,
      };
    }
  }

  // P2: Session logged, no gym match
  if (hasSession) {
    return {
      type: 'trained',
      headline: 'Session logged — nice work!',
      icon: 'check',
      iconColor: 'var(--success)',
      iconBg: 'var(--success-bg)',
      showLogButton: false,
    };
  }

  // P3: Upcoming class within 4 hrs
  if (classes.length > 0) {
    const upcoming = classes
      .filter(c => {
        const start = parseTimeToday(c.start_time);
        const diffMs = start.getTime() - now.getTime();
        return diffMs > 0 && diffMs <= 4 * 60 * 60 * 1000;
      })
      .sort((a, b) =>
        parseTimeToday(a.start_time).getTime() - parseTimeToday(b.start_time).getTime()
      );
    if (upcoming.length > 0) {
      const next = upcoming[0];
      const timeStr = parseTimeToday(next.start_time)
        .toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      const typeLabel = next.class_type
        ? ' ' + next.class_type.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('-')
        : '';
      return {
        type: 'upcoming',
        headline: `Next: ${timeStr}${typeLabel}`,
        subtext: next.class_name,
        icon: 'clock',
        iconColor: 'var(--accent)',
        iconBg: 'var(--surfaceElev)',
        showLogButton: false,
      };
    }
  }

  // P4: Behind on goals with <=4 days remaining
  if (goals && goals.days_remaining <= 4) {
    const { targets, actual } = goals;
    const gaps: { label: string; needed: number }[] = [];
    if (targets.sc_sessions && actual.sc_sessions != null
        && targets.sc_sessions > actual.sc_sessions) {
      gaps.push({ label: 'S&C', needed: targets.sc_sessions - actual.sc_sessions });
    }
    if (targets.mobility_sessions && actual.mobility_sessions != null
        && targets.mobility_sessions > actual.mobility_sessions) {
      gaps.push({ label: 'mobility', needed: targets.mobility_sessions - actual.mobility_sessions });
    }
    if (targets.bjj_sessions && actual.bjj_sessions != null
        && targets.bjj_sessions > actual.bjj_sessions) {
      gaps.push({ label: 'BJJ', needed: targets.bjj_sessions - actual.bjj_sessions });
    }
    if (gaps.length > 0) {
      const top = gaps[0];
      return {
        type: 'goal-nudge',
        headline: `You still need ${top.needed} ${top.label} session${top.needed > 1 ? 's' : ''} this week`,
        subtext: `${goals.days_remaining} day${goals.days_remaining > 1 ? 's' : ''} remaining`,
        icon: 'alert',
        iconColor: 'var(--warning)',
        iconBg: 'var(--warning-bg)',
        showLogButton: true,
      };
    }
  }

  // P5: All classes past, no upcoming
  if (classes.length > 0) {
    const allPast = classes.every(c =>
      now.getTime() > parseTimeToday(c.end_time).getTime()
    );
    if (allPast) {
      return {
        type: 'missed',
        headline: "Missed today's class? Plan for tomorrow",
        icon: 'calendar',
        iconColor: 'var(--muted)',
        iconBg: 'var(--surfaceElev)',
        showLogButton: false,
      };
    }
  }

  // P6: Intention from yesterday
  if (intention) {
    return {
      type: 'intention',
      headline: intention,
      subtext: 'Your plan today',
      icon: 'calendar',
      iconColor: 'var(--warning)',
      iconBg: 'var(--warning-bg)',
      showLogButton: true,
    };
  }

  // P7: Nothing to show
  return null;
}

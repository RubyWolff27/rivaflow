import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Trophy, Target, Flame } from 'lucide-react';
import { eventsApi, milestonesApi } from '../../api/client';
import { Card, CardSkeleton } from '../ui';
import type { MilestoneProgress, CompEvent } from '../../types';

const MILESTONE_ICONS: Record<string, string> = {
  hours: 'Hours on the mat',
  sessions: 'Training sessions',
  rolls: 'Rounds rolled',
  partners: 'Training partners',
  techniques: 'Techniques logged',
  streak: 'Day streak',
};

export default function NextGoal() {
  const [loading, setLoading] = useState(true);
  const [eventData, setEventData] = useState<{
    event: CompEvent | null;
    days_until: number | null;
    current_weight: number | null;
  }>({ event: null, days_until: null, current_weight: null });
  const [milestone, setMilestone] = useState<(MilestoneProgress & { has_milestone: boolean }) | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const results = await Promise.allSettled([
        eventsApi.getNext(),
        milestonesApi.getClosest(),
      ]);

      if (cancelled) return;

      if (results[0].status === 'fulfilled') setEventData(results[0].value.data);
      if (results[1].status === 'fulfilled' && results[1].value.data?.has_milestone) {
        setMilestone(results[1].value.data);
      }
      setLoading(false);
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <CardSkeleton lines={2} />;

  const hasMilestone = milestone?.has_milestone;

  // Show event if it exists (comp countdown)
  const event = eventData.event;
  if (event != null) {
    const { days_until, current_weight } = eventData;
    const isUrgent = days_until != null && days_until <= 7;

    return (
      <div className="space-y-3">
        <Link to="/events">
          <Card interactive>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                  style={{ backgroundColor: isUrgent ? 'var(--danger-bg)' : 'var(--warning-bg)' }}
                >
                  <Trophy className="w-5 h-5" style={{ color: isUrgent ? 'var(--danger)' : 'var(--warning)' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                    Next Competition
                  </p>
                  <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
                    {event.name}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    {new Date(event.event_date + 'T00:00:00').toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric',
                    })}
                    {event.location && ` \u00B7 ${event.location}`}
                  </p>
                </div>
              </div>
              <div className="text-right shrink-0 ml-3">
                <div
                  className="text-2xl font-bold tabular-nums"
                  style={{ color: isUrgent ? 'var(--danger)' : 'var(--accent)' }}
                >
                  {days_until}
                </div>
                <div className="text-[10px] uppercase font-medium" style={{ color: 'var(--muted)' }}>
                  {days_until === 1 ? 'day' : 'days'}
                </div>
                {event.target_weight && current_weight && (
                  <div className="text-[10px] mt-1" style={{ color: 'var(--muted)' }}>
                    {current_weight}kg / {event.target_weight}kg
                  </div>
                )}
              </div>
            </div>
          </Card>
        </Link>

        {/* Also show milestone if available alongside event */}
        {hasMilestone && <MilestoneCard milestone={milestone!} />}
      </div>
    );
  }

  // No event — show milestone as the primary goal
  if (hasMilestone) {
    return <MilestoneCard milestone={milestone!} />;
  }

  // Nothing — motivational empty state
  return (
    <Link to="/goals">
      <Card interactive>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
              style={{ backgroundColor: 'var(--surfaceElev)' }}
            >
              <Target className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>What are you training toward?</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Set goals to stay motivated and track your journey</p>
            </div>
          </div>
          <span className="text-xs font-medium shrink-0" style={{ color: 'var(--accent)' }}>Set up →</span>
        </div>
      </Card>
    </Link>
  );
}

function MilestoneCard({ milestone }: { milestone: MilestoneProgress }) {
  const pct = Math.min(100, milestone.percentage || 0);
  const description = MILESTONE_ICONS[milestone.type] || milestone.type;

  return (
    <Link to="/progress">
      <Card interactive>
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
            style={{ backgroundColor: 'var(--success-bg)' }}
          >
            <Flame className="w-5 h-5" style={{ color: 'var(--success)' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
              Next Milestone
            </p>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              {milestone.next_label}
            </p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>{description}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-lg font-bold tabular-nums" style={{ color: 'var(--accent)' }}>
              {pct.toFixed(0)}%
            </p>
            <p className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {milestone.current} / {milestone.next_value}
            </p>
          </div>
        </div>
        <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{ width: `${pct}%`, backgroundColor: 'var(--accent)' }}
          />
        </div>
      </Card>
    </Link>
  );
}

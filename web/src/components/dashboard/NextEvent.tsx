import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Trophy, Calendar } from 'lucide-react';
import { eventsApi } from '../../api/client';
import { Card, CardSkeleton } from '../ui';
import type { CompEvent } from '../../types';

export default function NextEvent() {
  const [loading, setLoading] = useState(true);
  const [eventData, setEventData] = useState<{
    event: CompEvent | null;
    days_until: number | null;
    current_weight: number | null;
  }>({ event: null, days_until: null, current_weight: null });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await eventsApi.getNext();
        if (!cancelled) setEventData(res.data);
      } catch {
        // No events
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <CardSkeleton lines={2} />;

  if (!eventData.event) {
    return (
      <Link to="/events">
        <Card interactive>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <Calendar className="w-5 h-5" style={{ color: 'var(--accent)' }} />
              </div>
              <div>
                <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Got a comp coming up?</p>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>Add it to track your prep and weight cut</p>
              </div>
            </div>
            <span className="text-xs font-medium shrink-0" style={{ color: 'var(--accent)' }}>Add →</span>
          </div>
        </Card>
      </Link>
    );
  }

  const { event, days_until, current_weight } = eventData;
  const isUrgent = days_until != null && days_until <= 7;

  return (
    <Link to="/events">
      <Card interactive>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
              style={{
                backgroundColor: isUrgent ? 'var(--danger-bg)' : 'var(--warning-bg)',
              }}
            >
              <Trophy className="w-5 h-5" style={{ color: isUrgent ? 'var(--danger)' : 'var(--warning)' }} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
                {event.name}
              </p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                {new Date(event.event_date + 'T00:00:00').toLocaleDateString('en-US', {
                  month: 'short', day: 'numeric',
                })}
                {event.location && ` - ${event.location}`}
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
  );
}

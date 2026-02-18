import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { sessionsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Calendar } from 'lucide-react';
import { ACTIVITY_COLORS, formatClassType } from '../../constants/activity';
import { Card } from '../ui';
import SessionScoreBadge from '../sessions/SessionScoreBadge';

interface Session {
  id: number;
  session_date: string;
  class_type: string;
  gym_name: string;
  duration_mins: number;
  intensity: number;
  rolls?: number;
  notes?: string;
  session_score?: number;
}

export function LastSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const response = await sessionsApi.list(1);
        if (!cancelled && response.data && response.data.length > 0) {
          setSession(response.data[0]);
        }
      } catch (error) {
        if (!cancelled) logger.error('Failed to load last session:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <Card variant="compact">
        <div className="animate-pulse flex items-center gap-3">
          <div className="h-4 bg-[var(--surfaceElev)] rounded w-24" />
          <div className="h-4 bg-[var(--surfaceElev)] rounded w-32" />
        </div>
      </Card>
    );
  }

  if (!session) {
    return (
      <Card variant="compact">
        <div className="text-center py-4">
          <Calendar className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--muted)' }} />
          <p className="text-sm mb-2" style={{ color: 'var(--muted)' }}>
            No sessions yet
          </p>
          <Link
            to="/log"
            className="inline-block px-3 py-1.5 rounded-lg text-sm font-medium"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            Log Session
          </Link>
        </div>
      </Card>
    );
  }

  const color = ACTIVITY_COLORS[session.class_type] || '#6B7280';
  const formattedDate = new Date(session.session_date).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });

  return (
    <Link to={`/session/${session.id}`}>
      <Card variant="compact" interactive>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="shrink-0">
              <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Last Session
              </span>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                {formattedDate}
              </p>
            </div>
            <div
              className="px-2 py-0.5 rounded-full text-xs font-semibold uppercase shrink-0"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {formatClassType(session.class_type)}
            </div>
            <span className="text-sm truncate" style={{ color: 'var(--text)' }}>
              {session.gym_name}
            </span>
            <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
              {session.duration_mins}min
            </span>
            <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
              {session.intensity}/5
            </span>
          </div>
          <SessionScoreBadge score={session.session_score} />
        </div>
      </Card>
    </Link>
  );
}

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { sessionsApi } from '../../api/client';
import { Calendar, Clock, TrendingUp, Award } from 'lucide-react';
import { Card } from '../ui';

interface Session {
  id: number;
  session_date: string;
  class_type: string;
  gym_name: string;
  duration_mins: number;
  intensity: number;
  rolls?: number;
  notes?: string;
}

const ACTIVITY_COLORS: Record<string, string> = {
  'gi': '#3B82F6',
  'no-gi': '#8B5CF6',
  's&c': '#EF4444',
  'drilling': '#F59E0B',
  'open-mat': '#10B981',
  'competition': '#EC4899',
};

export function LastSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLastSession();
  }, []);

  const loadLastSession = async () => {
    try {
      const response = await sessionsApi.list(1);
      if (response.data && response.data.length > 0) {
        setSession(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load last session:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full"></div>
            <div className="h-4 bg-gray-700 rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (!session) {
    return (
      <Card className="p-6">
        <div className="text-center py-8">
          <Calendar className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
          <h3 className="font-semibold mb-2" style={{ color: 'var(--text)' }}>
            No Sessions Yet
          </h3>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
            Log your first training session to start tracking
          </p>
          <Link
            to="/log"
            className="inline-block px-4 py-2 rounded-lg font-medium transition-colors"
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
      <Card className="p-6 hover:border-[var(--accent)] transition-colors cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--text)' }}>
              Last Session
            </h3>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>{formattedDate}</p>
          </div>
          <div
            className="px-3 py-1 rounded-full text-xs font-semibold uppercase"
            style={{
              backgroundColor: `${color}20`,
              color: color,
            }}
          >
            {session.class_type}
          </div>
        </div>

        <div className="space-y-3">
          {/* Gym */}
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4" style={{ color: 'var(--muted)' }} />
            <span className="text-sm" style={{ color: 'var(--text)' }}>
              {session.gym_name}
            </span>
          </div>

          {/* Duration and Intensity */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-sm" style={{ color: 'var(--text)' }}>
                {session.duration_mins}min
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-sm" style={{ color: 'var(--text)' }}>
                {session.intensity}/5 intensity
              </span>
            </div>
            {session.rolls && session.rolls > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium" style={{ color: color }}>
                  {session.rolls} rolls
                </span>
              </div>
            )}
          </div>

          {/* Notes Preview */}
          {session.notes && (
            <p className="text-sm line-clamp-2" style={{ color: 'var(--muted)' }}>
              {session.notes}
            </p>
          )}
        </div>
      </Card>
    </Link>
  );
}

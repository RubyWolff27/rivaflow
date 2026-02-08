import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi } from '../api/client';
import { Star, Trophy, Users, Flame, Target, Zap, UserPlus } from 'lucide-react';

interface Insight {
  type: string;
  title: string;
  description: string;
  icon: string;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  star: Star,
  trophy: Trophy,
  users: Users,
  flame: Flame,
  target: Target,
  zap: Zap,
};

const ICON_COLORS: Record<string, string> = {
  star: '#f59e0b',
  trophy: '#f59e0b',
  users: '#3b82f6',
  flame: '#ef4444',
  target: '#8b5cf6',
  zap: '#10b981',
};

export default function SessionInsights({ sessionId }: { sessionId: number }) {
  const navigate = useNavigate();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await sessionsApi.getInsights(sessionId);
        if (!cancelled) setInsights(res.data?.insights || []);
      } catch {
        // Silently fail — insights are non-critical
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [sessionId]);

  if (loading || insights.length === 0) return null;

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
      {insights.map((insight, i) => {
        const IconComponent = ICON_MAP[insight.icon] || Star;
        const iconColor = ICON_COLORS[insight.icon] || 'var(--accent)';

        return (
          <div
            key={i}
            className="flex-shrink-0 rounded-[14px] p-4 min-w-[200px] max-w-[260px]"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span style={{ color: iconColor }}><IconComponent className="w-5 h-5" /></span>
              <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>
                {insight.title}
              </span>
            </div>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              {insight.description}
            </p>
            {insight.type === 'partner_milestone' && (
              <button
                onClick={() => navigate('/friends')}
                className="flex items-center gap-1 mt-2 text-xs font-medium"
                style={{ color: 'var(--accent)' }}
              >
                <UserPlus className="w-3.5 h-3.5" />
                Add Friend
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

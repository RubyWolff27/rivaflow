import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Target, ChevronRight } from 'lucide-react';
import { gamePlansApi } from '../../api/client';
import { Card } from '../ui';
import type { GamePlan } from '../../types';

export default function MyGameWidget() {
  const [plan, setPlan] = useState<GamePlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await gamePlansApi.getCurrent();
        if (!cancelled) {
          const data = response.data;
          setPlan(data.plan !== undefined ? (data.plan === null ? null : data) : data.id ? data : null);
        }
      } catch {
        // No plan yet
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return null;

  if (!plan) {
    return (
      <Link to="/my-game">
        <Card variant="compact" interactive>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <div>
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Build Your Game</h3>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>Create a strategy mind map</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          </div>
        </Card>
      </Link>
    );
  }

  const focusNodes = plan.focus_nodes || [];

  return (
    <Link to="/my-game">
      <Card variant="compact" interactive>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              {plan.title || 'My Game'}
            </h3>
          </div>
          <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
        </div>
        {focusNodes.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {focusNodes.slice(0, 3).map((n) => (
              <span
                key={n.id}
                className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              >
                {n.name}
              </span>
            ))}
            {focusNodes.length > 3 && (
              <span className="text-xs" style={{ color: 'var(--muted)' }}>
                +{focusNodes.length - 3} more
              </span>
            )}
          </div>
        ) : (
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {plan.flat_nodes?.length || 0} techniques &middot; Set focus areas
          </p>
        )}
      </Card>
    </Link>
  );
}

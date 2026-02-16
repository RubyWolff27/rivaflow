import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, Target, ChevronRight } from 'lucide-react';
import { grappleApi, gamePlansApi } from '../../api/client';
import { Card } from '../ui';

interface InsightRow {
  title: string;
}

interface GamePlanRow {
  focus: string;
}

export default function QuickLinks() {
  const navigate = useNavigate();
  const [insight, setInsight] = useState<InsightRow | null>(null);
  const [gamePlan, setGamePlan] = useState<GamePlanRow | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const results = await Promise.allSettled([
        grappleApi.getInsights({ limit: 1 }),
        gamePlansApi.getCurrent(),
      ]);

      if (cancelled) return;

      if (results[0].status === 'fulfilled' && results[0].value.data) {
        const insights = results[0].value.data;
        const list = Array.isArray(insights) ? insights : insights.insights;
        if (list && list.length > 0) {
          setInsight({ title: list[0].title || list[0].insight_type || 'Training Insight' });
        }
      }

      if (results[1].status === 'fulfilled' && results[1].value.data) {
        const plan = results[1].value.data;
        const focus = plan.focus_areas
          ? (Array.isArray(plan.focus_areas) ? plan.focus_areas.join(', ') : plan.focus_areas)
          : plan.name || 'Game Plan';
        setGamePlan({ focus: String(focus) });
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (!insight && !gamePlan) return null;

  return (
    <Card variant="compact">
      <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
        {insight && (
          <button
            onClick={() => navigate('/grapple?panel=chat')}
            className="flex items-center gap-3 w-full py-2 first:pt-0 last:pb-0 text-left hover:opacity-80 transition-opacity"
          >
            <Brain className="w-4 h-4 shrink-0" style={{ color: 'var(--accent)' }} />
            <span className="text-sm truncate flex-1" style={{ color: 'var(--text)' }}>
              Insight: {insight.title}
            </span>
            <ChevronRight className="w-4 h-4 shrink-0" style={{ color: 'var(--muted)' }} />
          </button>
        )}
        {gamePlan && (
          <button
            onClick={() => navigate('/my-game')}
            className="flex items-center gap-3 w-full py-2 first:pt-0 last:pb-0 text-left hover:opacity-80 transition-opacity"
          >
            <Target className="w-4 h-4 shrink-0" style={{ color: 'var(--accent)' }} />
            <span className="text-sm truncate flex-1" style={{ color: 'var(--text)' }}>
              My Game: {gamePlan.focus}
            </span>
            <ChevronRight className="w-4 h-4 shrink-0" style={{ color: 'var(--muted)' }} />
          </button>
        )}
      </div>
    </Card>
  );
}

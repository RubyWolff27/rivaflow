import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ChevronRight, Loader2 } from 'lucide-react';
import { grappleApi } from '../../api/client';
import { Card } from '../ui';
import type { AIInsight } from '../../types';

export default function LatestInsightWidget() {
  const navigate = useNavigate();
  const [insight, setInsight] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await grappleApi.getInsights({ limit: 1 });
        if (!cancelled) {
          const insights = response.data.insights || [];
          setInsight(insights.length > 0 ? insights[0] : null);
        }
      } catch {
        // Insights not available
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return null;

  if (!insight) {
    return (
      <Card variant="compact">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>AI Insights</h3>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
          Log a few sessions and Grapple will start spotting patterns in your training.
        </p>
      </Card>
    );
  }

  const categoryColors: Record<string, string> = {
    observation: '#3B82F6',
    pattern: '#8B5CF6',
    focus: '#F59E0B',
    recovery: '#10B981',
  };
  const color = categoryColors[insight.category] || '#6B7280';

  const handleClick = async () => {
    setOpening(true);
    try {
      const res = await grappleApi.createInsightChat(insight.id);
      navigate(`/grapple?session=${res.data.chat_session_id}`);
    } catch {
      navigate('/grapple');
    }
  };

  return (
    <div onClick={handleClick} onKeyDown={e => e.key === 'Enter' && handleClick()} role="button" tabIndex={0} aria-label="View latest insight" className="cursor-pointer">
      <Card variant="compact" interactive>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Latest Insight</h3>
            <span
              className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded"
              style={{ backgroundColor: color + '20', color }}
            >
              {insight.category}
            </span>
          </div>
          {opening ? (
            <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--muted)' }} />
          ) : (
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          )}
        </div>
        <p className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>
          {insight.title}
        </p>
        <p className="text-xs line-clamp-2 leading-relaxed" style={{ color: 'var(--muted)' }}>
          {insight.content}
        </p>
      </Card>
    </div>
  );
}

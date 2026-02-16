import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Mic, Brain } from 'lucide-react';
import { grappleApi } from '../../api/client';
import { Card } from '../ui';

export default function QuickLinks() {
  const navigate = useNavigate();
  const [insightTitle, setInsightTitle] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await grappleApi.getInsights({ limit: 1 });
        if (cancelled) return;
        const insights = res.data;
        const list = Array.isArray(insights) ? insights : insights?.insights;
        if (list && list.length > 0) {
          setInsightTitle(list[0].title || list[0].insight_type || 'Training Insight');
        }
      } catch { /* best-effort */ }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <Card variant="compact">
      {/* Grapple AI quick actions */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-6 h-6 rounded-md flex items-center justify-center"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          <Brain className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          Grapple AI
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => navigate('/grapple?panel=chat')}
          className="flex flex-col items-center gap-1.5 py-2.5 rounded-lg text-xs font-medium transition-all hover:opacity-80"
          style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
        >
          <MessageCircle className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          Ask Coach
        </button>
        <button
          onClick={() => navigate('/grapple?panel=extract')}
          className="flex flex-col items-center gap-1.5 py-2.5 rounded-lg text-xs font-medium transition-all hover:opacity-80"
          style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
        >
          <Mic className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          Voice Log
        </button>
        <button
          onClick={() => navigate('/grapple?panel=chat')}
          className="flex flex-col items-center gap-1.5 py-2.5 rounded-lg text-xs font-medium transition-all hover:opacity-80"
          style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
        >
          <Brain className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          Insight
        </button>
      </div>

      {/* Latest insight one-liner */}
      {insightTitle && (
        <button
          onClick={() => navigate('/grapple?panel=chat')}
          className="flex items-center gap-2 w-full mt-3 pt-3 text-left hover:opacity-80 transition-opacity"
          style={{ borderTop: '1px solid var(--border)' }}
        >
          <span className="text-xs truncate flex-1" style={{ color: 'var(--muted)' }}>
            Latest: {insightTitle}
          </span>
          <span className="text-xs" style={{ color: 'var(--accent)' }}>View</span>
        </button>
      )}
    </Card>
  );
}

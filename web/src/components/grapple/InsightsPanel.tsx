import { useState, useEffect } from 'react';
import { useToast } from '../../contexts/ToastContext';
import { grappleApi, getErrorMessage } from '../../api/client';
import type { AIInsight } from '../../types';
import InsightCard from './InsightCard';

export default function InsightsPanel() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const toast = useToast();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await grappleApi.getInsights({ limit: 10 });
        if (!cancelled) setInsights(response.data.insights || []);
      } catch {
        // Insights not available
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const handleGenerateWeekly = async () => {
    setGenerating(true);
    try {
      const response = await grappleApi.generateInsight({ insight_type: 'weekly' });
      setInsights((prev) => [response.data, ...prev]);
      toast.success('Insight generated!');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div className="text-center py-4" style={{ color: 'var(--muted)' }}>Loading insights...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold" style={{ color: 'var(--text)' }}>AI Insights</h3>
        <button
          onClick={handleGenerateWeekly}
          disabled={generating}
          className="text-sm px-3 py-1.5 rounded-lg font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          {generating ? 'Generating...' : 'Generate Weekly'}
        </button>
      </div>
      {insights.length === 0 ? (
        <p className="text-sm text-center py-4" style={{ color: 'var(--muted)' }}>
          No insights yet. Train more and generate your first insight!
        </p>
      ) : (
        insights.map((insight) => <InsightCard key={insight.id} insight={insight} />)
      )}
    </div>
  );
}

import type { AIInsight } from '../../types';

const categoryColors: Record<string, string> = {
  observation: '#3B82F6',
  pattern: '#8B5CF6',
  focus: '#F59E0B',
  recovery: '#10B981',
};

export default function InsightCard({ insight }: { insight: AIInsight }) {
  const color = categoryColors[insight.category] || '#6B7280';

  return (
    <div
      className="p-4 rounded-[14px] space-y-2"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2">
        <span
          className="text-[10px] font-bold uppercase px-2 py-0.5 rounded"
          style={{ backgroundColor: color + '20', color }}
        >
          {insight.category}
        </span>
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          {insight.insight_type}
        </span>
      </div>
      <h4 className="font-semibold text-sm" style={{ color: 'var(--text)' }}>
        {insight.title}
      </h4>
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        {insight.content}
      </p>
    </div>
  );
}

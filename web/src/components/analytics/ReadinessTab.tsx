import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { analyticsApi } from '../../api/client';
import { Card, MetricTile, MetricTileSkeleton, CardSkeleton, EmptyState } from '../ui';
import ReadinessTrendChart from './ReadinessTrendChart';

interface ReadinessTabProps {
  dateRange: { start: string; end: string };
  selectedTypes: string[];
}

export default function ReadinessTab({ dateRange, selectedTypes }: ReadinessTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;
    if (!dateRange.start || !dateRange.end) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          start_date: dateRange.start,
          end_date: dateRange.end,
          types: selectedTypes.length > 0 ? selectedTypes : undefined,
        };
        const res = await analyticsApi.readinessTrends(params);
        if (!cancelled) setData(res.data ?? null);
      } catch (err) {
        if (!cancelled) {
          console.error('Error loading readiness trends:', err);
          setError('Failed to load readiness data. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [dateRange, selectedTypes]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
        </div>
        <CardSkeleton lines={4} />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <EmptyState
          icon={Activity}
          title="Error Loading Data"
          description={error}
        />
      </Card>
    );
  }

  const trends = data?.trends || [];
  const summary = data?.summary || {};
  const componentAverages = data?.component_averages || {};

  if (trends.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={Activity}
          title="No Readiness Data"
          description="Start logging your daily readiness checks to see trends, averages, and insights about your recovery."
          actionLabel="Check In Now"
          actionPath="/readiness"
        />
      </Card>
    );
  }

  // Transform trend data for chart
  const chartData = trends.map((t: any) => ({
    date: t.check_date || t.date,
    score: t.composite_score ?? 0,
  }));

  const avgScore = summary.avg_composite_score != null
    ? Number(summary.avg_composite_score).toFixed(1)
    : '0';
  const bestDay = summary.best_day ?? '-';
  const worstDay = summary.worst_day ?? '-';
  const daysLogged = summary.days_logged ?? trends.length;

  return (
    <div className="space-y-6">
      {/* Metric tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricTile label="Avg Score" value={avgScore} chipLabel="/20" />
        <MetricTile label="Days Logged" value={daysLogged} chipLabel="Total" />
        <MetricTile label="Best Day" value={bestDay} chipLabel="Score" />
        <MetricTile label="Worst Day" value={worstDay} chipLabel="Score" />
      </div>

      {/* Trend chart */}
      <Card>
        <div className="mb-4">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Readiness Trend</h3>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Green zone (16-20) = Ready to train hard, Yellow (12-15) = Light session, Red (&lt;12) = Rest
          </p>
        </div>
        <ReadinessTrendChart data={chartData} />
      </Card>

      {/* Component averages */}
      {(componentAverages.sleep != null || componentAverages.stress != null) && (
        <Card>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text)' }}>Component Breakdown</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Sleep', value: componentAverages.sleep, max: 5, good: 'higher' },
              { label: 'Stress', value: componentAverages.stress, max: 5, good: 'lower' },
              { label: 'Soreness', value: componentAverages.soreness, max: 5, good: 'lower' },
              { label: 'Energy', value: componentAverages.energy, max: 5, good: 'higher' },
            ].map((comp) => (
              <div key={comp.label} className="text-center">
                <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--muted)' }}>
                  {comp.label}
                </p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {comp.value != null ? Number(comp.value).toFixed(1) : '-'}
                </p>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>/ {comp.max}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

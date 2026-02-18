import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi } from '../api/client';
import { logger } from '../utils/logger';
import { Swords, Shield, BarChart3 } from 'lucide-react';
import DynamicsChart from '../components/dynamics/DynamicsChart';
import MatchupCard, { SummaryStats } from '../components/dynamics/MatchupCard';
import type { HeatmapPeriod, ViewMode } from '../components/dynamics/DynamicsChart';
import type { InsightsData } from '../components/dynamics/MatchupCard';

export default function FightDynamics() {
  usePageTitle('Fight Dynamics');
  const [view, setView] = useState<ViewMode>('weekly');
  const [heatmapData, setHeatmapData] = useState<HeatmapPeriod[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      setError(null);
      try {
        const [heatmapRes, insightsRes] = await Promise.all([
          analyticsApi.fightDynamicsHeatmap({ view }),
          analyticsApi.fightDynamicsInsights(),
        ]);
        if (!cancelled) {
          setHeatmapData(heatmapRes.data ?? []);
          setInsights(insightsRes.data ?? null);
        }
      } catch (err) {
        if (!cancelled) {
          logger.error('Error loading fight dynamics:', err);
          setError('Failed to load fight dynamics data.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [view]);

  const hasAnyData = heatmapData.some(p => p.attacks_attempted > 0 || p.defenses_attempted > 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'var(--accent)', opacity: 0.9 }}>
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: 'var(--text)' }}>Fight Dynamics</h1>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Attack vs Defence heatmap</p>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }}>
          {(['weekly', 'monthly'] as ViewMode[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className="px-4 py-1.5 text-xs font-medium transition-colors"
              style={{
                backgroundColor: view === v ? 'var(--accent)' : 'var(--surface)',
                color: view === v ? '#FFFFFF' : 'var(--muted)',
              }}
            >
              {v === 'weekly' ? '8 Weeks' : '6 Months'}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-xl p-4 text-sm text-red-400" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {/* Skeleton heatmap */}
          <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="h-5 w-32 rounded mb-6" style={{ backgroundColor: 'var(--border)' }} />
            <div className="space-y-4">
              {[0, 1].map(row => (
                <div key={row} className="flex gap-2">
                  <div className="w-20 h-16 rounded" style={{ backgroundColor: 'var(--border)' }} />
                  {Array.from({ length: view === 'weekly' ? 8 : 6 }).map((_, i) => (
                    <div key={i} className="flex-1 h-16 rounded" style={{ backgroundColor: 'var(--border)' }} />
                  ))}
                </div>
              ))}
            </div>
          </div>
          {/* Skeleton insights */}
          <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="h-5 w-24 rounded mb-4" style={{ backgroundColor: 'var(--border)' }} />
            <div className="grid grid-cols-2 gap-4">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="h-20 rounded" style={{ backgroundColor: 'var(--border)' }} />
              ))}
            </div>
          </div>
        </div>
      ) : !hasAnyData ? (
        /* Empty state */
        <div
          className="rounded-xl p-8 text-center"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex justify-center gap-3 mb-4">
            <Swords className="w-8 h-8" style={{ color: 'var(--accent)' }} />
            <Shield className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
            No Fight Dynamics Data Yet
          </h2>
          <p className="text-sm max-w-md mx-auto" style={{ color: 'var(--muted)' }}>
            Start tracking your attacks and defences during sparring sessions.
            Open the "Fight Dynamics" section when logging a session to record your attack and defence counts.
          </p>
        </div>
      ) : (
        <>
          {/* Heatmap Card */}
          <DynamicsChart heatmapData={heatmapData} view={view} />

          {/* Summary Stats */}
          {insights && <SummaryStats insights={insights} />}

          {/* Insights Panel */}
          {insights && <MatchupCard insights={insights} />}
        </>
      )}
    </div>
  );
}

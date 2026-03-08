import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, Swords, ShieldAlert, BookOpen, AlertTriangle, ChevronRight } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi, sessionsApi } from '../api/client';
import { logger } from '../utils/logger';
import { CardSkeleton, Chip, EmptyState } from '../components/ui';
import type { Session } from '../types';
import type { TechniquesData } from '../components/analytics/reportTypes';

const CATEGORY_COLORS: Record<string, string> = {
  submission: '#EF4444',
  position: '#3B82F6',
  sweep: '#F59E0B',
  pass: '#10B981',
  takedown: '#8B5CF6',
  escape: '#06B6D4',
  defense: '#6366F1',
  movement: '#EC4899',
  concept: '#64748B',
};

export default function MyGame() {
  usePageTitle('My Game');
  const navigate = useNavigate();
  const [techData, setTechData] = useState<TechniquesData | null>(null);
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [techRes, sessRes] = await Promise.all([
          analyticsApi.techniqueBreakdown(),
          sessionsApi.list(20),
        ]);
        if (!cancelled) {
          setTechData(techRes.data);
          // Filter to sessions that have techniques or notes
          const sessions = (sessRes.data || []).filter(
            (s: Session) => (s.techniques && s.techniques.length > 0) || s.notes
          );
          setRecentSessions(sessions.slice(0, 8));
        }
      } catch (err) {
        logger.debug('My Game data load error', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
        </div>
        <CardSkeleton lines={4} />
      </div>
    );
  }

  const hasData = techData && (techData.summary?.total_unique_techniques_used ?? 0) > 0;
  const subStats = techData?.submission_stats;

  if (!hasData && recentSessions.length === 0) {
    return (
      <div className="py-8">
        <EmptyState
          icon={Target}
          title="Build Your Game"
          description="Log sessions with techniques, submissions, and notes to see your training data come to life here. The more you log, the more your game reveals itself."
          actionLabel="Log a Session"
          actionPath="/log"
        />
      </div>
    );
  }

  const subRatio = subStats
    ? subStats.total_submissions_for + subStats.total_submissions_against > 0
      ? (subStats.total_submissions_for / (subStats.total_submissions_for + subStats.total_submissions_against) * 100).toFixed(0)
      : null
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Target className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>My Game</h1>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Built from your actual training data
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          icon={<BookOpen className="w-4 h-4" />}
          label="Techniques"
          value={techData?.summary?.total_unique_techniques_used ?? 0}
        />
        <StatCard
          icon={<Swords className="w-4 h-4" />}
          label="Subs For"
          value={subStats?.total_submissions_for ?? 0}
          color="var(--accent)"
        />
        <StatCard
          icon={<ShieldAlert className="w-4 h-4" />}
          label="Subs Against"
          value={subStats?.total_submissions_against ?? 0}
        />
        <StatCard
          icon={<AlertTriangle className="w-4 h-4" />}
          label="Stale (30d)"
          value={techData?.summary?.stale_count ?? 0}
          color={techData?.summary?.stale_count ? '#F59E0B' : undefined}
        />
      </div>

      {/* Sub Ratio Bar */}
      {subStats && (subStats.total_submissions_for + subStats.total_submissions_against) > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase" style={{ color: 'var(--muted)' }}>
              Submission Ratio
            </span>
            <span className="text-sm font-bold" style={{ color: 'var(--accent)' }}>
              {subRatio}% yours
            </span>
          </div>
          <div className="w-full h-3 rounded-full overflow-hidden flex" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-full rounded-l-full transition-all"
              style={{
                width: `${subRatio}%`,
                backgroundColor: 'var(--accent)',
              }}
            />
            <div
              className="h-full rounded-r-full"
              style={{
                width: `${100 - Number(subRatio)}%`,
                backgroundColor: 'var(--muted)',
                opacity: 0.3,
              }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {subStats.total_submissions_for} for
            </span>
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {subStats.total_submissions_against} against
            </span>
          </div>
        </div>
      )}

      {/* Top Submissions */}
      {techData?.top_submissions && techData.top_submissions.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Top Submissions
          </h3>
          <div className="space-y-2">
            {techData.top_submissions.slice(0, 6).map((sub, i) => {
              const maxCount = techData.top_submissions![0].count;
              const pct = maxCount > 0 ? (sub.count / maxCount) * 100 : 0;
              return (
                <div key={sub.name} className="flex items-center gap-3">
                  <span className="text-xs font-bold w-5 text-right" style={{ color: 'var(--muted)' }}>
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{sub.name}</span>
                      <span className="text-sm font-semibold" style={{ color: 'var(--accent)' }}>
                        {sub.count}
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${pct}%`, backgroundColor: 'var(--accent)' }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      {techData?.category_breakdown && techData.category_breakdown.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Technique Categories
          </h3>
          <div className="space-y-3">
            {[...techData.category_breakdown]
              .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
              .map((cat) => {
                const maxCount = Math.max(...techData.category_breakdown!.map(c => c.count ?? 0));
                const pct = maxCount > 0 ? ((cat.count ?? 0) / maxCount) * 100 : 0;
                const color = CATEGORY_COLORS[cat.category ?? ''] || 'var(--accent)';
                return (
                  <div key={cat.category}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-sm capitalize" style={{ color: 'var(--text)' }}>
                          {cat.category}
                        </span>
                      </div>
                      <span className="text-xs" style={{ color: 'var(--muted)' }}>{cat.count}</span>
                    </div>
                    <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Recent Training Notes */}
      {recentSessions.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Recent Training Notes
          </h3>
          <div className="space-y-3">
            {recentSessions.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/sessions/${s.id}`)}
                className="w-full text-left p-3 rounded-lg transition-colors hover:brightness-110"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                    {new Date(s.session_date).toLocaleDateString('en-AU', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                    {' '}&middot; {s.class_type}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                </div>
                {s.notes && (
                  <p className="text-sm line-clamp-2 mb-1.5" style={{ color: 'var(--text)' }}>
                    {s.notes}
                  </p>
                )}
                {s.techniques && s.techniques.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {s.techniques.slice(0, 4).map((t) => (
                      <span
                        key={t}
                        className="text-[10px] px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: 'var(--accent)' + '15',
                          color: 'var(--accent)',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                    {s.techniques.length > 4 && (
                      <span className="text-[10px] px-2 py-0.5" style={{ color: 'var(--muted)' }}>
                        +{s.techniques.length - 4} more
                      </span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stale Techniques */}
      {techData?.stale_techniques && techData.stale_techniques.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4" style={{ color: '#F59E0B' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Stale Techniques
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: '#F59E0B20', color: '#F59E0B' }}>
              Not trained in 30+ days
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {techData.stale_techniques.slice(0, 15).map((tech) => (
              <Chip key={tech.id ?? tech.name}>{tech.name ?? 'Unknown'}</Chip>
            ))}
            {techData.stale_techniques.length > 15 && (
              <Chip>+{techData.stale_techniques.length - 15} more</Chip>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div
      className="p-4 rounded-[14px]"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span style={{ color: 'var(--muted)' }}>{icon}</span>
        <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
          {label}
        </span>
      </div>
      <p className="text-2xl font-semibold" style={{ color: color || 'var(--text)' }}>
        {value}
      </p>
    </div>
  );
}

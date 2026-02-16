import { Activity, Book, Target } from 'lucide-react';
import { Card, Chip, CardSkeleton, EmptyState } from '../ui';
import TechniqueHeatmap from './TechniqueHeatmap';
import type { TechniquesData } from './reportTypes';

interface TechniquesTabProps {
  loading: boolean;
  error: string | null;
  techniquesData: TechniquesData | null;
  selectedTypes: string[];
}

export default function TechniquesTab({
  loading,
  error,
  techniquesData,
  selectedTypes,
}: TechniquesTabProps) {
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-3">
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
        </div>
        <CardSkeleton lines={4} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton lines={3} />
          <CardSkeleton lines={3} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <EmptyState
            icon={Activity}
            title="Error Loading Data"
            description={error}
          />
        </Card>
      </div>
    );
  }

  if (
    !techniquesData ||
    (techniquesData.summary?.total_unique_techniques_used ?? 0) === 0
  ) {
    return (
      <div className="space-y-6">
        <Card>
          <EmptyState
            icon={Target}
            title={
              selectedTypes.length > 0
                ? 'No Technique Data for Selected Activity Types'
                : 'No Technique Data'
            }
            description={
              selectedTypes.length > 0
                ? `No technique data found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                : 'Start logging submissions and techniques during your rolls to see analytics on your technique usage and proficiency.'
            }
            actionLabel={
              selectedTypes.length > 0 ? undefined : 'Log Session'
            }
            actionPath={selectedTypes.length > 0 ? undefined : '/log'}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div
          className="p-4 rounded-[14px]"
          style={{
            backgroundColor: 'var(--surfaceElev)',
            border: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Book
              className="w-4 h-4"
              style={{ color: 'var(--muted)' }}
            />
            <span
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: 'var(--muted)' }}
            >
              Unique Techniques
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {techniquesData.summary?.total_unique_techniques_used ?? 0}
          </p>
        </div>

        <div
          className="p-4 rounded-[14px]"
          style={{
            backgroundColor: 'var(--surfaceElev)',
            border: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Activity
              className="w-4 h-4"
              style={{ color: 'var(--muted)' }}
            />
            <span
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: 'var(--muted)' }}
            >
              Stale (30+ days)
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {techniquesData.summary?.stale_count ?? 0}
          </p>
        </div>
      </div>

      {/* Submissions Overview */}
      {techniquesData.submission_stats && (
        <Card>
          <div className="mb-4">
            <h3
              className="text-lg font-semibold"
              style={{ color: 'var(--text)' }}
            >
              Submissions Overview
            </h3>
            <p
              className="text-xs mt-1"
              style={{ color: 'var(--muted)' }}
            >
              Session-level submission totals
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            <div
              className="p-3 rounded-lg text-center"
              style={{ backgroundColor: 'var(--surfaceElev)' }}
            >
              <p
                className="text-xl font-semibold"
                style={{ color: 'var(--accent)' }}
              >
                {techniquesData.submission_stats.total_submissions_for ??
                  0}
              </p>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                Subs For
              </p>
            </div>
            <div
              className="p-3 rounded-lg text-center"
              style={{ backgroundColor: 'var(--surfaceElev)' }}
            >
              <p
                className="text-xl font-semibold"
                style={{ color: 'var(--text)' }}
              >
                {techniquesData.submission_stats
                  .total_submissions_against ?? 0}
              </p>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                Subs Against
              </p>
            </div>
            <div
              className="p-3 rounded-lg text-center"
              style={{ backgroundColor: 'var(--surfaceElev)' }}
            >
              <p
                className="text-xl font-semibold"
                style={{ color: 'var(--text)' }}
              >
                {techniquesData.submission_stats
                  .sessions_with_submissions ?? 0}
              </p>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                Sessions w/ Subs
              </p>
            </div>
          </div>

          {techniquesData.top_submissions &&
          Array.isArray(techniquesData.top_submissions) &&
          techniquesData.top_submissions.length > 0 ? (
            <div>
              <h4
                className="text-sm font-semibold mb-2"
                style={{ color: 'var(--text)' }}
              >
                Most Common Submissions
              </h4>
              <div className="space-y-2">
                {techniquesData.top_submissions
                  .slice(0, 8)
                  .map((tech) => (
                    <div
                      key={
                        tech.name ?? `sub-${Math.random()}`
                      }
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{
                        backgroundColor: 'var(--surfaceElev)',
                      }}
                    >
                      <span
                        className="text-sm"
                        style={{ color: 'var(--text)' }}
                      >
                        {tech.name ?? 'Unknown'}
                      </span>
                      <span
                        className="text-sm font-medium"
                        style={{ color: 'var(--accent)' }}
                      >
                        {tech.count ?? 0}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            <p
              className="text-sm text-center py-4"
              style={{ color: 'var(--muted)' }}
            >
              Log technique names during sessions to see your most common
              submissions here.
            </p>
          )}
        </Card>
      )}

      {/* Category Breakdown */}
      {techniquesData.category_breakdown &&
        Array.isArray(techniquesData.category_breakdown) &&
        techniquesData.category_breakdown.length > 0 && (
          <Card>
            <div className="mb-4">
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text)' }}
              >
                Submissions by Category
              </h3>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                Which categories you're using most
              </p>
            </div>

            <div className="space-y-3">
              {techniquesData
                .category_breakdown!.sort(
                  (a, b) => (b.count ?? 0) - (a.count ?? 0)
                )
                .map((cat) => {
                  const maxCount = Math.max(
                    ...techniquesData.category_breakdown!.map(
                      (c) => c.count ?? 0
                    )
                  );
                  const percentage =
                    ((cat.count ?? 0) / maxCount) * 100;

                  return (
                    <div key={cat.category ?? 'unknown'}>
                      <div className="flex items-center justify-between mb-2">
                        <span
                          className="text-sm font-medium"
                          style={{ color: 'var(--text)' }}
                        >
                          {cat.category ?? 'Unknown'}
                        </span>
                        <span
                          className="text-sm"
                          style={{
                            color: 'var(--muted)',
                          }}
                        >
                          {cat.count ?? 0}
                        </span>
                      </div>
                      <div
                        className="w-full rounded-full h-2"
                        style={{
                          backgroundColor: 'var(--border)',
                        }}
                      >
                        <div
                          className="h-2 rounded-full transition-all"
                          style={{
                            width: `${percentage}%`,
                            backgroundColor:
                              'var(--accent)',
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>
        )}

      {/* Gi vs No-Gi Split */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Gi Techniques */}
        <Card>
          <div className="mb-4">
            <h3
              className="text-lg font-semibold"
              style={{ color: 'var(--text)' }}
            >
              Top Gi Techniques
            </h3>
            <p
              className="text-xs mt-1"
              style={{ color: 'var(--muted)' }}
            >
              Most successful in gi sessions
            </p>
          </div>

          {techniquesData.gi_top_techniques &&
          Array.isArray(techniquesData.gi_top_techniques) &&
          techniquesData.gi_top_techniques.length > 0 ? (
            <div className="space-y-2">
              {techniquesData.gi_top_techniques
                .slice(0, 5)
                .map((tech) => (
                  <div
                    key={tech.name ?? tech.id}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{
                      backgroundColor: 'var(--surfaceElev)',
                    }}
                  >
                    <span
                      className="text-sm"
                      style={{ color: 'var(--text)' }}
                    >
                      {tech.name ?? 'Unknown'}
                    </span>
                    <span
                      className="text-sm font-medium"
                      style={{ color: 'var(--accent)' }}
                    >
                      {tech.count ?? 0}
                    </span>
                  </div>
                ))}
            </div>
          ) : (
            <p
              className="text-center py-8 text-sm"
              style={{ color: 'var(--muted)' }}
            >
              No gi techniques logged yet
            </p>
          )}
        </Card>

        {/* No-Gi Techniques */}
        <Card>
          <div className="mb-4">
            <h3
              className="text-lg font-semibold"
              style={{ color: 'var(--text)' }}
            >
              Top No-Gi Techniques
            </h3>
            <p
              className="text-xs mt-1"
              style={{ color: 'var(--muted)' }}
            >
              Most successful in no-gi sessions
            </p>
          </div>

          {techniquesData.nogi_top_techniques &&
          Array.isArray(techniquesData.nogi_top_techniques) &&
          techniquesData.nogi_top_techniques.length > 0 ? (
            <div className="space-y-2">
              {techniquesData.nogi_top_techniques
                .slice(0, 5)
                .map((tech) => (
                  <div
                    key={tech.name ?? tech.id}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{
                      backgroundColor: 'var(--surfaceElev)',
                    }}
                  >
                    <span
                      className="text-sm"
                      style={{ color: 'var(--text)' }}
                    >
                      {tech.name ?? 'Unknown'}
                    </span>
                    <span
                      className="text-sm font-medium"
                      style={{ color: 'var(--accent)' }}
                    >
                      {tech.count ?? 0}
                    </span>
                  </div>
                ))}
            </div>
          ) : (
            <p
              className="text-center py-8 text-sm"
              style={{ color: 'var(--muted)' }}
            >
              No no-gi techniques logged yet
            </p>
          )}
        </Card>
      </div>

      {/* Technique Heatmap */}
      {techniquesData.all_techniques &&
        Array.isArray(techniquesData.all_techniques) &&
        techniquesData.all_techniques.length > 0 && (
          <TechniqueHeatmap
            techniques={techniquesData.all_techniques}
          />
        )}

      {/* Stale Techniques */}
      {techniquesData.stale_techniques &&
        Array.isArray(techniquesData.stale_techniques) &&
        techniquesData.stale_techniques.length > 0 && (
          <Card>
            <div className="mb-4">
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text)' }}
              >
                Stale Techniques
              </h3>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                Not practiced in the last 30 days
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {techniquesData.stale_techniques
                .slice(0, 15)
                .map((tech) => (
                  <Chip
                    key={
                      tech.id ?? `stale-${Math.random()}`
                    }
                  >
                    {tech.name ?? 'Unknown'}
                  </Chip>
                ))}
              {techniquesData.stale_techniques.length > 15 && (
                <Chip>
                  +{techniquesData.stale_techniques.length - 15}{' '}
                  more
                </Chip>
              )}
            </div>
          </Card>
        )}
    </div>
  );
}

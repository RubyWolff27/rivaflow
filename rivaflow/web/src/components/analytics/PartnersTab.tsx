import { Activity, Users, Target } from 'lucide-react';
import { Card, CardSkeleton, EmptyState } from '../ui';
import type { PartnersData, BeltDistData } from './reportTypes';

interface PartnersTabProps {
  loading: boolean;
  error: string | null;
  partnersData: PartnersData | null;
  beltDistData: BeltDistData | null;
  selectedTypes: string[];
}

export default function PartnersTab({
  loading,
  error,
  partnersData,
  beltDistData,
  selectedTypes,
}: PartnersTabProps) {
  if (loading) {
    return (
      <div className="space-y-6">
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
    !partnersData ||
    (partnersData.top_partners &&
      Array.isArray(partnersData.top_partners) &&
      partnersData.top_partners.length === 0)
  ) {
    return (
      <div className="space-y-6">
        <Card>
          <EmptyState
            icon={Users}
            title={
              selectedTypes.length > 0
                ? 'No Partner Data for Selected Activity Types'
                : 'No Partner Data'
            }
            description={
              selectedTypes.length > 0
                ? `No partner data found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                : 'Start logging rolls with training partners to see analytics on your training relationships and performance with different partners.'
            }
            actionLabel={
              selectedTypes.length > 0
                ? undefined
                : 'Log Session with Partners'
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
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          className="p-4 rounded-[14px]"
          style={{
            backgroundColor: 'var(--surfaceElev)',
            border: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Users
              className="w-4 h-4"
              style={{ color: 'var(--muted)' }}
            />
            <span
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: 'var(--muted)' }}
            >
              Active Partners
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {partnersData.diversity_metrics?.active_partners ?? 0}
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
              Total Rolls
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {partnersData.summary?.total_rolls ?? 0}
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
            <Target
              className="w-4 h-4"
              style={{ color: 'var(--muted)' }}
            />
            <span
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: 'var(--muted)' }}
            >
              Subs For
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {partnersData.summary?.total_submissions_for ?? 0}
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
            <Target
              className="w-4 h-4"
              style={{ color: 'var(--muted)' }}
            />
            <span
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: 'var(--muted)' }}
            >
              Subs Against
            </span>
          </div>
          <p
            className="text-2xl font-semibold"
            style={{ color: 'var(--text)' }}
          >
            {partnersData.summary?.total_submissions_against ?? 0}
          </p>
        </div>
      </div>

      {/* Top Partners List */}
      <Card>
        <div className="mb-4">
          <h3
            className="text-lg font-semibold"
            style={{ color: 'var(--text)' }}
          >
            Top Training Partners
          </h3>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Most frequent partners this period
          </p>
        </div>

        {partnersData.top_partners &&
        Array.isArray(partnersData.top_partners) &&
        partnersData.top_partners.length > 0 ? (
          <div className="space-y-3">
            {partnersData.top_partners.map(
              (partner: any, index: number) => (
                <div
                  key={partner.id}
                  className="p-4 rounded-[14px]"
                  style={{
                    backgroundColor: 'var(--surfaceElev)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold"
                        style={{
                          backgroundColor: 'var(--accent)',
                          color: '#FFFFFF',
                        }}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <p
                          className="font-medium"
                          style={{ color: 'var(--text)' }}
                        >
                          {partner.name ?? 'Unknown'}
                        </p>
                        {partner.belt_rank && (
                          <p
                            className="text-xs"
                            style={{ color: 'var(--muted)' }}
                          >
                            {partner.belt_rank}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p
                        className="text-lg font-semibold"
                        style={{ color: 'var(--text)' }}
                      >
                        {partner.total_rolls ?? 0} rolls
                      </p>
                    </div>
                  </div>

                  <div
                    className="grid grid-cols-3 gap-3 pt-3"
                    style={{ borderTop: '1px solid var(--border)' }}
                  >
                    <div>
                      <p
                        className="text-xs"
                        style={{ color: 'var(--muted)' }}
                      >
                        Subs For
                      </p>
                      <p
                        className="text-sm font-medium"
                        style={{ color: 'var(--text)' }}
                      >
                        {partner.submissions_for ?? 0}
                      </p>
                    </div>
                    <div>
                      <p
                        className="text-xs"
                        style={{ color: 'var(--muted)' }}
                      >
                        Subs Against
                      </p>
                      <p
                        className="text-sm font-medium"
                        style={{ color: 'var(--text)' }}
                      >
                        {partner.submissions_against ?? 0}
                      </p>
                    </div>
                    <div>
                      <p
                        className="text-xs"
                        style={{ color: 'var(--muted)' }}
                      >
                        Ratio
                      </p>
                      <p
                        className="text-sm font-medium"
                        style={{
                          color:
                            (partner.sub_ratio ?? 0) >= 1
                              ? 'var(--accent)'
                              : 'var(--text)',
                        }}
                      >
                        {partner.sub_ratio != null
                          ? partner.sub_ratio.toFixed(2)
                          : '0.00'}
                      </p>
                    </div>
                  </div>
                </div>
              )
            )}
          </div>
        ) : (
          <p
            className="text-center py-8 text-sm"
            style={{ color: 'var(--muted)' }}
          >
            No partner data for this period. Start logging rolls with
            partners!
          </p>
        )}
      </Card>

      {/* Belt Distribution */}
      {beltDistData?.distribution &&
        beltDistData.distribution.length > 0 && (
          <Card>
            <div className="mb-4">
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text)' }}
              >
                Belt Distribution
              </h3>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                {beltDistData.total_partners} total partners
              </p>
            </div>
            <div className="space-y-2">
              {beltDistData.distribution!.map((b: any) => {
                const maxCount = Math.max(
                  ...beltDistData.distribution!.map(
                    (d: any) => d.count
                  )
                );
                const beltColors: Record<string, string> = {
                  white: '#FFFFFF',
                  blue: '#0066CC',
                  purple: '#8B3FC0',
                  brown: '#8B4513',
                  black: '#1a1a1a',
                  unranked: 'var(--muted)',
                };
                return (
                  <div key={b.belt}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full border"
                          style={{
                            backgroundColor:
                              beltColors[b.belt] || 'var(--muted)',
                            borderColor: 'var(--border)',
                          }}
                        />
                        <span
                          className="text-sm font-medium capitalize"
                          style={{ color: 'var(--text)' }}
                        >
                          {b.belt}
                        </span>
                      </div>
                      <span
                        className="text-sm"
                        style={{ color: 'var(--muted)' }}
                      >
                        {b.count}
                      </span>
                    </div>
                    <div
                      className="w-full rounded-full h-2"
                      style={{ backgroundColor: 'var(--border)' }}
                    >
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${(b.count / maxCount) * 100}%`,
                          backgroundColor:
                            beltColors[b.belt] || 'var(--accent)',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}
    </div>
  );
}

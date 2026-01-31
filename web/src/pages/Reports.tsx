import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/client';
import { TrendingUp, Users, Activity, Target, Lightbulb, Book } from 'lucide-react';
import { Card, Chip, MetricTile } from '../components/ui';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [loading, setLoading] = useState(false);
  const [hasUserChangedRange, setHasUserChangedRange] = useState(false);

  // Data states
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [partnersData, setPartnersData] = useState<any>(null);
  const [techniquesData, setTechniquesData] = useState<any>(null);

  useEffect(() => {
    // Set default date range (last 7 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 7);
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    });
  }, []);

  useEffect(() => {
    if (dateRange.start && dateRange.end) {
      loadData();
    }
  }, [dateRange, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = { start_date: dateRange.start, end_date: dateRange.end };

      if (activeTab === 'overview') {
        const perfRes = await analyticsApi.performanceOverview(params);
        setPerformanceData(perfRes.data);
      } else if (activeTab === 'partners') {
        const partnersRes = await analyticsApi.partnerStats(params);
        setPartnersData(partnersRes.data);
      } else if (activeTab === 'techniques') {
        const techRes = await analyticsApi.techniqueBreakdown(params);
        setTechniquesData(techRes.data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateRangeChange = (start: string, end: string) => {
    setDateRange({ start, end });
    setHasUserChangedRange(true);
  };

  const tabs = [
    { id: 'overview', name: 'Performance', icon: TrendingUp },
    { id: 'partners', name: 'Partners', icon: Users },
    { id: 'readiness', name: 'Readiness', icon: Activity },
    { id: 'techniques', name: 'Techniques', icon: Target },
  ];

  // Extract real data from API response
  const summary = performanceData?.summary || {};
  const timeseries = performanceData?.daily_timeseries || {};
  const deltas = performanceData?.deltas || {};

  const sessionsValue = summary.total_sessions || 0;
  const intensityValue = summary.avg_intensity?.toFixed(1) || '0.0';
  const rollsValue = summary.total_rolls || 0;
  const submissionsValue = summary.total_submissions_for || 0;

  // Use real time series data from API
  const sessionsSeries = timeseries.sessions || [];
  const intensitySeries = timeseries.intensity || [];
  const rollsSeries = timeseries.rolls || [];
  const submissionsSeries = timeseries.submissions || [];

  // Use real deltas from API
  const sessionsDelta = deltas.sessions || 0;
  const intensityDelta = deltas.intensity || 0;
  const rollsDelta = deltas.rolls || 0;
  const submissionsDelta = deltas.submissions || 0;

  // Quick Insights logic - generate 2 most valuable insights
  const getQuickInsights = () => {
    if (sessionsValue === 0) {
      return [
        'Log 1 session to unlock trend insights.',
        'Your tiles will show automatic 7-day trends.',
      ];
    }

    const allInsights: Array<{ text: string; priority: number }> = [];

    // Session frequency insights
    if (sessionsDelta > 0) {
      allInsights.push({
        text: `Training frequency up ${Math.abs(sessionsDelta)} sessions this period.`,
        priority: Math.abs(sessionsDelta) >= 2 ? 10 : 5,
      });
    } else if (sessionsDelta < 0) {
      allInsights.push({
        text: `Training frequency down ${Math.abs(sessionsDelta)} sessions this period.`,
        priority: Math.abs(sessionsDelta) >= 2 ? 10 : 5,
      });
    }

    // Intensity insights
    if (Math.abs(intensityDelta) >= 0.5) {
      if (intensityDelta > 0) {
        allInsights.push({
          text: `Intensity trending higher (+${intensityDelta.toFixed(1)}/5 avg).`,
          priority: 8,
        });
      } else {
        allInsights.push({
          text: `Intensity trending lower (${intensityDelta.toFixed(1)}/5 avg).`,
          priority: 8,
        });
      }
    }

    // Submissions insights
    if (Math.abs(submissionsDelta) >= 3) {
      if (submissionsDelta > 0) {
        allInsights.push({
          text: `Submission rate up +${submissionsDelta} this period.`,
          priority: 9,
        });
      } else {
        allInsights.push({
          text: `Submission rate down ${Math.abs(submissionsDelta)} this period.`,
          priority: 7,
        });
      }
    }

    // Rolls insights
    if (Math.abs(rollsDelta) >= 5) {
      if (rollsDelta > 0) {
        allInsights.push({
          text: `Rolling more (+${rollsDelta} rounds this period).`,
          priority: 6,
        });
      } else {
        allInsights.push({
          text: `Less live rolling (${Math.abs(rollsDelta)} fewer rounds).`,
          priority: 6,
        });
      }
    }

    // Default insights if no significant changes
    if (allInsights.length === 0) {
      allInsights.push({
        text: 'Training consistency maintained.',
        priority: 3,
      });
      allInsights.push({
        text: `Logged ${sessionsValue} sessions this period.`,
        priority: 2,
      });
    }

    // Sort by priority and take top 2
    allInsights.sort((a, b) => b.priority - a.priority);
    return allInsights.slice(0, 2).map(i => i.text);
  };

  const quickInsights = getQuickInsights();
  const chipLabel = hasUserChangedRange ? 'Range' : 'Last 7d';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-[var(--text)]">Analytics</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--border)] pb-0">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors"
              style={{
                color: isActive ? 'var(--accent)' : 'var(--muted)',
                fontWeight: isActive ? 600 : 500,
              }}
            >
              <Icon className="w-4 h-4" />
              {tab.name}
              {isActive && (
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t-full"
                  style={{ backgroundColor: 'var(--accent)' }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Date Range Control */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-[var(--text)]">Date Range</label>
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => handleDateRangeChange(e.target.value, dateRange.end)}
            className="input text-sm"
            style={{ maxWidth: '160px' }}
          />
          <span className="text-[var(--muted)]">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => handleDateRangeChange(dateRange.start, e.target.value)}
            className="input text-sm"
            style={{ maxWidth: '160px' }}
          />
        </div>
      </Card>

      {/* Overview Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 2x2 Metric Tiles Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MetricTile
              label="Sessions"
              chipLabel={chipLabel}
              value={sessionsValue}
              delta={sessionsDelta}
              sparklineData={sessionsSeries}
            />
            <MetricTile
              label="Avg Intensity"
              chipLabel={chipLabel}
              value={`${intensityValue}/5`}
              delta={intensityDelta}
              sparklineData={intensitySeries}
            />
            <MetricTile
              label="Total Rolls"
              chipLabel={chipLabel}
              value={rollsValue}
              delta={rollsDelta}
              sparklineData={rollsSeries}
            />
            <MetricTile
              label="Submissions"
              chipLabel={chipLabel}
              value={submissionsValue}
              delta={submissionsDelta}
              sparklineData={submissionsSeries}
            />
          </div>

          {/* Quick Insights */}
          <Card>
            <div className="flex items-start gap-3">
              <div
                className="flex items-center justify-center w-10 h-10 rounded-full"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <Lightbulb className="w-5 h-5 text-[var(--muted)]" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-[var(--text)]">Quick Insights</h3>
                  <Chip>{chipLabel}</Chip>
                </div>
                <ul className="space-y-2">
                  {quickInsights.map((insight, index) => (
                    <li key={index} className="text-sm text-[var(--muted)] flex items-start gap-2">
                      <span className="text-[var(--accent)] font-bold">•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Partners Tab Content */}
      {activeTab === 'partners' && partnersData && (
        <div className="space-y-6">
          {/* Summary Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Active Partners</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {partnersData.diversity_metrics?.active_partners || 0}
              </p>
            </div>

            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Total Rolls</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {partnersData.summary?.total_rolls || 0}
              </p>
            </div>

            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs For</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {partnersData.summary?.total_submissions_for || 0}
              </p>
            </div>

            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs Against</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {partnersData.summary?.total_submissions_against || 0}
              </p>
            </div>
          </div>

          {/* Top Partners List */}
          <Card>
            <div className="mb-4">
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Top Training Partners</h3>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Most frequent partners this period</p>
            </div>

            {partnersData.top_partners && partnersData.top_partners.length > 0 ? (
              <div className="space-y-3">
                {partnersData.top_partners.map((partner: any, index: number) => (
                  <div
                    key={partner.id}
                    className="p-4 rounded-[14px]"
                    style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
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
                          <p className="font-medium" style={{ color: 'var(--text)' }}>{partner.name}</p>
                          {partner.belt_rank && (
                            <p className="text-xs" style={{ color: 'var(--muted)' }}>{partner.belt_rank}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                          {partner.total_rolls} rolls
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs For</p>
                        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {partner.submissions_for || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs Against</p>
                        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {partner.submissions_against || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Ratio</p>
                        <p className="text-sm font-medium" style={{ color: partner.sub_ratio >= 1 ? 'var(--accent)' : 'var(--text)' }}>
                          {partner.sub_ratio ? partner.sub_ratio.toFixed(2) : '0.00'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center py-8 text-sm" style={{ color: 'var(--muted)' }}>
                No partner data for this period. Start logging rolls with partners!
              </p>
            )}
          </Card>
        </div>
      )}

      {/* Techniques Tab Content */}
      {activeTab === 'techniques' && techniquesData && (
        <div className="space-y-6">
          {/* Summary Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Book className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Unique Techniques</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {techniquesData.summary?.total_unique_techniques_used || 0}
              </p>
            </div>

            <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Stale (30+ days)</span>
              </div>
              <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                {techniquesData.summary?.stale_count || 0}
              </p>
            </div>
          </div>

          {/* Category Breakdown */}
          {techniquesData.category_breakdown && techniquesData.category_breakdown.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Submissions by Category</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Which categories you're using most</p>
              </div>

              <div className="space-y-3">
                {techniquesData.category_breakdown
                  .sort((a: any, b: any) => b.count - a.count)
                  .map((cat: any) => {
                    const maxCount = Math.max(...techniquesData.category_breakdown.map((c: any) => c.count));
                    const percentage = (cat.count / maxCount) * 100;

                    return (
                      <div key={cat.category}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                            {cat.category}
                          </span>
                          <span className="text-sm" style={{ color: 'var(--muted)' }}>
                            {cat.count}
                          </span>
                        </div>
                        <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                          <div
                            className="h-2 rounded-full transition-all"
                            style={{
                              width: `${percentage}%`,
                              backgroundColor: 'var(--accent)',
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
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Top Gi Techniques</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Most successful in gi sessions</p>
              </div>

              {techniquesData.gi_top_techniques && techniquesData.gi_top_techniques.length > 0 ? (
                <div className="space-y-2">
                  {techniquesData.gi_top_techniques.slice(0, 5).map((tech: any, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ backgroundColor: 'var(--surfaceElev)' }}
                    >
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{tech.name}</span>
                      <span className="text-sm font-medium" style={{ color: 'var(--accent)' }}>{tech.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-sm" style={{ color: 'var(--muted)' }}>
                  No gi techniques logged yet
                </p>
              )}
            </Card>

            {/* No-Gi Techniques */}
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Top No-Gi Techniques</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Most successful in no-gi sessions</p>
              </div>

              {techniquesData.nogi_top_techniques && techniquesData.nogi_top_techniques.length > 0 ? (
                <div className="space-y-2">
                  {techniquesData.nogi_top_techniques.slice(0, 5).map((tech: any, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ backgroundColor: 'var(--surfaceElev)' }}
                    >
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{tech.name}</span>
                      <span className="text-sm font-medium" style={{ color: 'var(--accent)' }}>{tech.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-sm" style={{ color: 'var(--muted)' }}>
                  No no-gi techniques logged yet
                </p>
              )}
            </Card>
          </div>

          {/* Stale Techniques */}
          {techniquesData.stale_techniques && techniquesData.stale_techniques.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Stale Techniques</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                  Not practiced in the last 30 days
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {techniquesData.stale_techniques.slice(0, 15).map((tech: any) => (
                  <Chip key={tech.id}>{tech.name}</Chip>
                ))}
                {techniquesData.stale_techniques.length > 15 && (
                  <Chip>+{techniquesData.stale_techniques.length - 15} more</Chip>
                )}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Placeholder for Readiness tab */}
      {activeTab === 'readiness' && (
        <Card>
          <div className="text-center py-12 text-[var(--muted)]">
            <p className="text-sm">
              Readiness analytics coming soon.
            </p>
          </div>
        </Card>
      )}

      {loading && (
        <div className="fixed inset-0 bg-[var(--bg)] bg-opacity-50 flex items-center justify-center">
          <div className="text-[var(--text)]">Loading...</div>
        </div>
      )}
    </div>
  );
}

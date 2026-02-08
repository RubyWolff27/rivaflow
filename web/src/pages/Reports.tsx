import { useState, useEffect } from 'react';
import { getLocalDateString } from '../utils/date';
import { useSearchParams, Link } from 'react-router-dom';
import { analyticsApi } from '../api/client';
import { TrendingUp, Users, Activity, Target, Lightbulb, Book, Calendar, Swords } from 'lucide-react';
import { Card, Chip, MetricTile, MetricTileSkeleton, CardSkeleton, EmptyState } from '../components/ui';
import { ActivityTypeFilter } from '../components/ActivityTypeFilter';
import { useFeatureAccess } from '../hooks/useTier';
import { PremiumBadge, UpgradePrompt } from '../components/UpgradePrompt';
import ReadinessTab from '../components/analytics/ReadinessTab';
import TechniqueHeatmap from '../components/analytics/TechniqueHeatmap';

export default function Reports() {
  const { hasAccess: hasAdvancedAnalytics } = useFeatureAccess('advanced_analytics');
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    searchParams.get('types')?.split(',').filter(Boolean) || []
  );
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);
  const [loading, setLoading] = useState(false);
  const [hasUserChangedRange, setHasUserChangedRange] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      start: getLocalDateString(start),
      end: getLocalDateString(end),
    });
  }, []);

  // Update URL params when filters change
  useEffect(() => {
    const params: any = { tab: activeTab };
    if (selectedTypes.length > 0) {
      params.types = selectedTypes.join(',');
    }
    setSearchParams(params, { replace: true });
  }, [activeTab, selectedTypes]);

  useEffect(() => {
    let cancelled = false;
    if (dateRange.start && dateRange.end) {
      const doLoad = async () => {
        setLoading(true);
        setError(null);
        try {
          const params = {
            start_date: dateRange.start,
            end_date: dateRange.end,
            types: selectedTypes.length > 0 ? selectedTypes : undefined,
          };

          if (activeTab === 'overview') {
            const perfRes = await analyticsApi.performanceOverview(params);
            if (!cancelled) setPerformanceData(perfRes.data ?? null);
          } else if (activeTab === 'partners') {
            const partnersRes = await analyticsApi.partnerStats(params);
            if (!cancelled) setPartnersData(partnersRes.data ?? null);
          } else if (activeTab === 'techniques') {
            const techRes = await analyticsApi.techniqueBreakdown(params);
            if (!cancelled) setTechniquesData(techRes.data ?? null);
          }
        } catch (error) {
          if (!cancelled) {
            console.error('Error loading analytics:', error);
            setError('Failed to load analytics data. Please try again.');
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      };
      doLoad();
    }
    return () => { cancelled = true; };
  }, [dateRange, activeTab, selectedTypes]);

  const handleDateRangeChange = (start: string, end: string) => {
    setDateRange({ start, end });
    setHasUserChangedRange(true);
  };

  const setQuickRange = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    setDateRange({
      start: getLocalDateString(start),
      end: getLocalDateString(end),
    });
    setHasUserChangedRange(false);
  };

  // Determine if we should show BJJ-specific tabs
  const isBJJActivity = selectedTypes.length === 0 || selectedTypes.some(t => ['gi', 'no-gi', 'drilling', 'open-mat', 'competition'].includes(t));
  const isOnlySC = selectedTypes.length > 0 && selectedTypes.every(t => t === 's&c');

  const allTabs = [
    { id: 'overview', name: 'Performance', icon: TrendingUp },
    { id: 'partners', name: 'Partners', icon: Users, bjjOnly: true },
    { id: 'readiness', name: 'Readiness', icon: Activity },
    { id: 'techniques', name: 'Techniques', icon: Target, bjjOnly: true },
  ];

  // Filter tabs based on activity selection
  const tabs = isOnlySC
    ? allTabs.filter(tab => !tab.bjjOnly)
    : allTabs;

  // Extract real data from API response with safe defaults
  const summary = performanceData?.summary || {};
  const timeseries = performanceData?.daily_timeseries || {};
  const deltas = performanceData?.deltas || {};

  const sessionsValue = summary.total_sessions ?? 0;
  const intensityValue = summary.avg_intensity != null ? summary.avg_intensity.toFixed(1) : '0.0';
  const rollsValue = summary.total_rolls ?? 0;
  const submissionsValue = summary.total_submissions_for ?? 0;

  // Use real time series data from API with safe defaults
  const sessionsSeries = timeseries.sessions || [];
  const intensitySeries = timeseries.intensity || [];
  const rollsSeries = timeseries.rolls || [];
  const submissionsSeries = timeseries.submissions || [];

  // Use real deltas from API with safe defaults
  const sessionsDelta = deltas.sessions ?? 0;
  const intensityDelta = deltas.intensity ?? 0;
  const rollsDelta = deltas.rolls ?? 0;
  const submissionsDelta = deltas.submissions ?? 0;

  // Check if we have any data
  const hasData = performanceData && (summary.total_sessions ?? 0) > 0;

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

    // Hours insight
    const totalHours = summary.total_hours ?? 0;
    if (totalHours > 0) {
      allInsights.push({
        text: `${Number(totalHours).toFixed(1)} hours on the mat this period.`,
        priority: 4,
      });
    }

    // Top class type insight
    if (summary.top_class_type) {
      allInsights.push({
        text: `Most trained class type: ${summary.top_class_type}.`,
        priority: 3,
      });
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
        <div className="flex items-center gap-3">
          <Link
            to="/fight-dynamics"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:opacity-80"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)', color: 'var(--accent)' }}
          >
            <Swords className="w-4 h-4" />
            Fight Dynamics
          </Link>
          {hasAdvancedAnalytics ? (
            <ActivityTypeFilter selectedTypes={selectedTypes} onChange={setSelectedTypes} />
          ) : (
            <button
              onClick={() => setShowUpgradePrompt(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)', color: 'var(--muted)' }}
            >
              <span>Activity Filter</span>
              <PremiumBadge className="ml-1" />
            </button>
          )}
        </div>
      </div>

      {/* Upgrade Prompt Modal */}
      {showUpgradePrompt && !hasAdvancedAnalytics && (
        <UpgradePrompt
          feature="advanced_analytics"
          onClose={() => setShowUpgradePrompt(false)}
        />
      )}

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
        <div className="space-y-3">
          <label className="text-sm font-medium text-[var(--text)]">Date Range</label>

          {/* Quick Range Buttons */}
          <div className="flex gap-2" role="group" aria-label="Quick date range">
            {[
              { label: 'Last 7 days', days: 7 },
              { label: 'Last 14 days', days: 14 },
              { label: 'Last 30 days', days: 30 },
            ].map((range) => {
              const end = new Date();
              const start = new Date();
              start.setDate(start.getDate() - range.days);
              const isActive = !hasUserChangedRange &&
                dateRange.start === getLocalDateString(start) &&
                dateRange.end === getLocalDateString(end);

              return (
                <button
                  key={range.days}
                  type="button"
                  onClick={() => setQuickRange(range.days)}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: isActive ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: isActive ? '#FFFFFF' : 'var(--text)',
                    border: isActive ? 'none' : '1px solid var(--border)',
                  }}
                  aria-pressed={isActive}
                >
                  {range.label}
                </button>
              );
            })}
          </div>

          {/* Custom Date Range */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-[var(--muted)]">Or select custom range:</span>
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
        </div>
      </Card>

      {/* Overview Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {loading ? (
            <>
              {/* Loading skeletons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MetricTileSkeleton />
                <MetricTileSkeleton />
                <MetricTileSkeleton />
                <MetricTileSkeleton />
              </div>
              <CardSkeleton lines={2} />
            </>
          ) : error ? (
            <Card>
              <EmptyState
                icon={Activity}
                title="Error Loading Data"
                description={error}
              />
            </Card>
          ) : !hasData ? (
            <Card>
              <EmptyState
                icon={Calendar}
                title={selectedTypes.length > 0 ? "No Data for Selected Activity Types" : "No Training Data Yet"}
                description={
                  selectedTypes.length > 0
                    ? `No sessions found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                    : "Start logging your training sessions to see performance analytics, trends, and insights."
                }
                actionLabel={selectedTypes.length > 0 ? undefined : "Log First Session"}
                actionPath={selectedTypes.length > 0 ? undefined : "/log-session"}
              />
            </Card>
          ) : (
            <>
              {/* Metric Tiles Grid - BJJ gets 2x2, S&C gets 1x2 */}
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
                {/* Only show Rolls and Submissions for BJJ activities */}
                {isBJJActivity && (
                  <>
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
                  </>
                )}
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
                      {quickInsights.map((insight) => (
                        <li key={insight} className="text-sm text-[var(--muted)] flex items-start gap-2">
                          <span className="text-[var(--accent)] font-bold">•</span>
                          <span>{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* Partners Tab Content */}
      {activeTab === 'partners' && (
        <div className="space-y-6">
          {loading ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <CardSkeleton lines={1} />
                <CardSkeleton lines={1} />
                <CardSkeleton lines={1} />
                <CardSkeleton lines={1} />
              </div>
              <CardSkeleton lines={4} />
            </>
          ) : error ? (
            <Card>
              <EmptyState
                icon={Activity}
                title="Error Loading Data"
                description={error}
              />
            </Card>
          ) : !partnersData || (partnersData.top_partners && Array.isArray(partnersData.top_partners) && partnersData.top_partners.length === 0) ? (
            <Card>
              <EmptyState
                icon={Users}
                title={selectedTypes.length > 0 ? "No Partner Data for Selected Activity Types" : "No Partner Data"}
                description={
                  selectedTypes.length > 0
                    ? `No partner data found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                    : "Start logging rolls with training partners to see analytics on your training relationships and performance with different partners."
                }
                actionLabel={selectedTypes.length > 0 ? undefined : "Log Session with Partners"}
                actionPath={selectedTypes.length > 0 ? undefined : "/log-session"}
              />
            </Card>
          ) : (
            <>
              {/* Summary Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Users className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Active Partners</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {partnersData.diversity_metrics?.active_partners ?? 0}
                </p>
              </div>

              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Total Rolls</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {partnersData.summary?.total_rolls ?? 0}
                </p>
              </div>

              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs For</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {partnersData.summary?.total_submissions_for ?? 0}
                </p>
              </div>

              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs Against</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {partnersData.summary?.total_submissions_against ?? 0}
                </p>
              </div>
          </div>

          {/* Top Partners List */}
          <Card>
            <div className="mb-4">
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Top Training Partners</h3>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Most frequent partners this period</p>
            </div>

            {partnersData.top_partners && Array.isArray(partnersData.top_partners) && partnersData.top_partners.length > 0 ? (
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
                          <p className="font-medium" style={{ color: 'var(--text)' }}>{partner.name ?? 'Unknown'}</p>
                          {partner.belt_rank && (
                            <p className="text-xs" style={{ color: 'var(--muted)' }}>{partner.belt_rank}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                          {partner.total_rolls ?? 0} rolls
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs For</p>
                        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {partner.submissions_for ?? 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs Against</p>
                        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {partner.submissions_against ?? 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>Ratio</p>
                        <p className="text-sm font-medium" style={{ color: (partner.sub_ratio ?? 0) >= 1 ? 'var(--accent)' : 'var(--text)' }}>
                          {partner.sub_ratio != null ? partner.sub_ratio.toFixed(2) : '0.00'}
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
            </>
          )}
        </div>
      )}

      {/* Techniques Tab Content */}
      {activeTab === 'techniques' && (
        <div className="space-y-6">
          {loading ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <CardSkeleton lines={1} />
                <CardSkeleton lines={1} />
              </div>
              <CardSkeleton lines={4} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <CardSkeleton lines={3} />
                <CardSkeleton lines={3} />
              </div>
            </>
          ) : error ? (
            <Card>
              <EmptyState
                icon={Activity}
                title="Error Loading Data"
                description={error}
              />
            </Card>
          ) : !techniquesData || (techniquesData.summary?.total_unique_techniques_used ?? 0) === 0 ? (
            <Card>
              <EmptyState
                icon={Target}
                title={selectedTypes.length > 0 ? "No Technique Data for Selected Activity Types" : "No Technique Data"}
                description={
                  selectedTypes.length > 0
                    ? `No technique data found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                    : "Start logging submissions and techniques during your rolls to see analytics on your technique usage and proficiency."
                }
                actionLabel={selectedTypes.length > 0 ? undefined : "Log Session"}
                actionPath={selectedTypes.length > 0 ? undefined : "/log-session"}
              />
            </Card>
          ) : (
            <>
              {/* Summary Metrics */}
              <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Book className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Unique Techniques</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {techniquesData.summary?.total_unique_techniques_used ?? 0}
                </p>
              </div>

              <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Stale (30+ days)</span>
                </div>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {techniquesData.summary?.stale_count ?? 0}
                </p>
              </div>
            </div>

          {/* Category Breakdown */}
          {techniquesData.category_breakdown && Array.isArray(techniquesData.category_breakdown) && techniquesData.category_breakdown.length > 0 && (
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
                      <div key={cat.category ?? 'unknown'}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                            {cat.category ?? 'Unknown'}
                          </span>
                          <span className="text-sm" style={{ color: 'var(--muted)' }}>
                            {cat.count ?? 0}
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

              {techniquesData.gi_top_techniques && Array.isArray(techniquesData.gi_top_techniques) && techniquesData.gi_top_techniques.length > 0 ? (
                <div className="space-y-2">
                  {techniquesData.gi_top_techniques.slice(0, 5).map((tech: any) => (
                    <div
                      key={tech.name ?? tech.id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ backgroundColor: 'var(--surfaceElev)' }}
                    >
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{tech.name ?? 'Unknown'}</span>
                      <span className="text-sm font-medium" style={{ color: 'var(--accent)' }}>{tech.count ?? 0}</span>
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

              {techniquesData.nogi_top_techniques && Array.isArray(techniquesData.nogi_top_techniques) && techniquesData.nogi_top_techniques.length > 0 ? (
                <div className="space-y-2">
                  {techniquesData.nogi_top_techniques.slice(0, 5).map((tech: any) => (
                    <div
                      key={tech.name ?? tech.id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ backgroundColor: 'var(--surfaceElev)' }}
                    >
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{tech.name ?? 'Unknown'}</span>
                      <span className="text-sm font-medium" style={{ color: 'var(--accent)' }}>{tech.count ?? 0}</span>
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

          {/* Technique Heatmap */}
          {techniquesData.all_techniques && Array.isArray(techniquesData.all_techniques) && techniquesData.all_techniques.length > 0 && (
            <TechniqueHeatmap techniques={techniquesData.all_techniques} />
          )}

          {/* Stale Techniques */}
          {techniquesData.stale_techniques && Array.isArray(techniquesData.stale_techniques) && techniquesData.stale_techniques.length > 0 && (
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Stale Techniques</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                  Not practiced in the last 30 days
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {techniquesData.stale_techniques.slice(0, 15).map((tech: any) => (
                  <Chip key={tech.id ?? `stale-${Math.random()}`}>{tech.name ?? 'Unknown'}</Chip>
                ))}
                {techniquesData.stale_techniques.length > 15 && (
                  <Chip>+{techniquesData.stale_techniques.length - 15} more</Chip>
                )}
              </div>
            </Card>
          )}
          </>
        )}
        </div>
      )}

      {/* Readiness Tab */}
      {activeTab === 'readiness' && (
        <ReadinessTab dateRange={dateRange} selectedTypes={selectedTypes} />
      )}
    </div>
  );
}

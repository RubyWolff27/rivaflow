import { useState, useEffect } from 'react';
import { getLocalDateString } from '../utils/date';
import { useSearchParams, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi, sessionsApi } from '../api/client';
import { logger } from '../utils/logger';
import { TrendingUp, Users, Activity, Target, Brain, ChevronRight } from 'lucide-react';
import { Card } from '../components/ui';
import { ActivityTypeFilter } from '../components/ActivityTypeFilter';
import { useFeatureAccess } from '../hooks/useTier';
import { PremiumBadge, UpgradePrompt } from '../components/UpgradePrompt';
import ReadinessTab from '../components/analytics/ReadinessTab';
import InsightsTab from '../components/analytics/InsightsTab';
import OverviewTab from '../components/analytics/OverviewTab';
import PartnersTab from '../components/analytics/PartnersTab';
import TechniquesTab from '../components/analytics/TechniquesTab';
import GameRadar from '../components/analytics/GameRadar';
import LifetimeJourneyBar from '../components/analytics/LifetimeJourneyBar';
import ErrorBoundary from '../components/ErrorBoundary';
import type {
  PerformanceOverview,
  PartnersData,
  TechniquesData,
  CalendarData,
  DurationData,
  TimeOfDayData,
  GymData,
  ClassTypeData,
  BeltDistData,
} from '../components/analytics/reportTypes';

export default function Reports() {
  usePageTitle('Progress');
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
  const [performanceData, setPerformanceData] = useState<PerformanceOverview | null>(null);
  const [partnersData, setPartnersData] = useState<PartnersData | null>(null);
  const [techniquesData, setTechniquesData] = useState<TechniquesData | null>(null);
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null);
  const [durationData, setDurationData] = useState<DurationData | null>(null);
  const [timeOfDayData, setTimeOfDayData] = useState<TimeOfDayData | null>(null);
  const [gymData, setGymData] = useState<GymData | null>(null);
  const [classTypeData, setClassTypeData] = useState<ClassTypeData | null>(null);
  const [beltDistData, setBeltDistData] = useState<BeltDistData | null>(null);
  const [zoneTrendsData, setZoneTrendsData] = useState<Array<{ session_id: number; date: string; zones: Record<string, number> }> | null>(null);

  useEffect(() => {
    // Set default date range (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setDateRange({
      start: getLocalDateString(start),
      end: getLocalDateString(end),
    });
  }, []);

  // Update URL params when filters change
  useEffect(() => {
    const params: Record<string, string> = { tab: activeTab };
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
            const [perfRes, calRes, durRes, todRes, gymRes, ctRes] = await Promise.all([
              analyticsApi.performanceOverview(params),
              analyticsApi.trainingCalendar({ start_date: params.start_date, end_date: params.end_date, types: params.types }),
              analyticsApi.durationTrends(params).catch(() => ({ data: null })),
              analyticsApi.timeOfDayPatterns(params).catch(() => ({ data: null })),
              analyticsApi.gymComparison(params).catch(() => ({ data: null })),
              analyticsApi.classTypeEffectiveness(params).catch(() => ({ data: null })),
            ]);
            if (!cancelled) {
              setPerformanceData(perfRes.data ?? null);
              setCalendarData(calRes.data ?? null);
              setDurationData(durRes.data ?? null);
              setTimeOfDayData(todRes.data ?? null);
              setGymData(gymRes.data ?? null);
              setClassTypeData(ctRes.data ?? null);
            }
            // Zone trends from the sessions' own Air zone data (no extra endpoint)
            try {
              const sessRes = await sessionsApi.list(50);
              const rangeSessions = (sessRes.data || []).filter((s) =>
                s.session_date >= params.start_date && s.session_date <= params.end_date
              );
              if (!cancelled) {
                const trends: Array<{ session_id: number; date: string; zones: Record<string, number> }> = [];
                for (const s of rangeSessions) {
                  const secs = [
                    s.garmin_hr_z1_sec, s.garmin_hr_z2_sec, s.garmin_hr_z3_sec,
                    s.garmin_hr_z4_sec, s.garmin_hr_z5_sec,
                  ];
                  const total = secs.reduce((sum: number, v) => sum + (v ?? 0), 0);
                  if (total > 0) {
                    trends.push({
                      session_id: s.id,
                      date: s.session_date,
                      zones: {
                        zone_one_milli: (secs[0] ?? 0) * 1000,
                        zone_two_milli: (secs[1] ?? 0) * 1000,
                        zone_three_milli: (secs[2] ?? 0) * 1000,
                        zone_four_milli: (secs[3] ?? 0) * 1000,
                        zone_five_milli: (secs[4] ?? 0) * 1000,
                      },
                    });
                  }
                }
                trends.sort((a, b) => a.date.localeCompare(b.date));
                setZoneTrendsData(trends.length > 0 ? trends : null);
              }
            } catch (err) { logger.debug('Zone trends derivation failed', err); }
          } else if (activeTab === 'partners') {
            const [partnersRes, beltRes] = await Promise.all([
              analyticsApi.partnerStats(params),
              analyticsApi.partnerBeltDistribution().catch(() => ({ data: null })),
            ]);
            if (!cancelled) {
              setPartnersData(partnersRes.data ?? null);
              setBeltDistData(beltRes.data ?? null);
            }
          } else if (activeTab === 'techniques') {
            const techRes = await analyticsApi.techniqueBreakdown(params);
            if (!cancelled) setTechniquesData(techRes.data ?? null);
          }
        } catch (error) {
          if (!cancelled) {
            logger.error('Error loading analytics:', error);
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
    { id: 'insights', name: 'Insights', icon: Brain, bjjOnly: true },
  ];

  // Filter tabs based on activity selection
  const tabs = isOnlySC
    ? allTabs.filter(tab => !tab.bjjOnly)
    : allTabs;

  // Compute derived values for OverviewTab
  const deltas = performanceData?.deltas || {};
  const sessionsDelta = deltas.sessions ?? 0;
  const intensityDelta = deltas.intensity ?? 0;
  const rollsDelta = deltas.rolls ?? 0;
  const submissionsDelta = deltas.submissions ?? 0;
  const chipLabel = hasUserChangedRange ? 'Range' : 'Last 7d';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-semibold text-[var(--text)]">Progress</h1>
        <div className="flex items-center gap-2 flex-wrap">
          {hasAdvancedAnalytics ? (
            <ActivityTypeFilter selectedTypes={selectedTypes} onChange={setSelectedTypes} />
          ) : (
            <button
              onClick={() => setShowUpgradePrompt(true)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
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
      <div className="flex gap-1 border-b border-[var(--border)] pb-0 overflow-x-auto scrollbar-hide" role="tablist" aria-label="Analytics tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              aria-selected={isActive}
              className="relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors flex-shrink-0"
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
          <div className="flex flex-wrap gap-2" role="group" aria-label="Quick date range">
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
          <div className="flex flex-wrap items-center gap-2 sm:gap-4">
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

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <ErrorBoundary compact>
              <GameRadar />
            </ErrorBoundary>
          </div>
          <div className="space-y-4">
            <ErrorBoundary compact>
              <LifetimeJourneyBar />
            </ErrorBoundary>
            <Card>
              <Link to="/friends" className="flex items-center justify-between gap-3 group">
                <div>
                  <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>
                    Training Partners
                  </h2>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    Open a partner to see your head-to-head record, roll count and
                    submission split with them.
                  </p>
                </div>
                <ChevronRight className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--accent)' }} />
              </Link>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'overview' && (
        <ErrorBoundary compact>
          <OverviewTab
            loading={loading}
            error={error}
            performanceData={performanceData}
            calendarData={calendarData}
            durationData={durationData}
            timeOfDayData={timeOfDayData}
            gymData={gymData}
            classTypeData={classTypeData}
            zoneTrendsData={zoneTrendsData}
            isBJJActivity={isBJJActivity}
            selectedTypes={selectedTypes}
            chipLabel={chipLabel}
            sessionsDelta={sessionsDelta}
            intensityDelta={intensityDelta}
            rollsDelta={rollsDelta}
            submissionsDelta={submissionsDelta}
          />
        </ErrorBoundary>
      )}

      {activeTab === 'partners' && (
        <ErrorBoundary compact>
          <PartnersTab
            loading={loading}
            error={error}
            partnersData={partnersData}
            beltDistData={beltDistData}
            selectedTypes={selectedTypes}
          />
        </ErrorBoundary>
      )}

      {activeTab === 'techniques' && (
        <ErrorBoundary compact>
          <TechniquesTab
            loading={loading}
            error={error}
            techniquesData={techniquesData}
            selectedTypes={selectedTypes}
          />
        </ErrorBoundary>
      )}

      {activeTab === 'readiness' && (
        <ReadinessTab dateRange={dateRange} selectedTypes={selectedTypes} />
      )}

      {activeTab === 'insights' && (
        <InsightsTab dateRange={dateRange} />
      )}
    </div>
  );
}

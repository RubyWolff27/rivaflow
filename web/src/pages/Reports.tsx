import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/client';
import { TrendingUp, Users, Activity, Target, Lightbulb } from 'lucide-react';
import { Card, Chip, MetricTile } from '../components/ui';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [loading, setLoading] = useState(false);
  const [hasUserChangedRange, setHasUserChangedRange] = useState(false);

  // Data states
  const [performanceData, setPerformanceData] = useState<any>(null);

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
      const perfRes = await analyticsApi.performanceOverview(params);
      setPerformanceData(perfRes.data);
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

  // Quick Insights logic
  const getQuickInsights = () => {
    if (sessionsValue === 0) {
      return [
        'Log 1 session to unlock trend insights.',
        'Your tiles will show automatic 7-day trends.',
      ];
    }

    // Determine trends
    const sessionTrend = sessionsDelta > 0 ? 'up' : sessionsDelta < 0 ? 'down' : 'flat';
    const intensityTrend = intensityDelta > 0 ? 'up' : intensityDelta < 0 ? 'down' : 'flat';

    const insights = [];

    if (sessionTrend === 'up') {
      insights.push(`Training frequency up ${Math.abs(sessionsDelta)} sessions this period.`);
    } else if (sessionTrend === 'down') {
      insights.push(`Training frequency down ${Math.abs(sessionsDelta)} sessions this period.`);
    } else {
      insights.push('Training frequency holding steady.');
    }

    if (intensityTrend === 'up') {
      insights.push(`Intensity trending higher (+${intensityDelta.toFixed(1)}/5 avg).`);
    } else if (intensityTrend === 'down') {
      insights.push(`Intensity trending lower (${intensityDelta.toFixed(1)}/5 avg).`);
    } else {
      insights.push('Intensity levels consistent across sessions.');
    }

    return insights.slice(0, 2); // Always exactly 2 bullets
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

      {/* Placeholder for other tabs */}
      {activeTab !== 'overview' && (
        <Card>
          <div className="text-center py-12 text-[var(--muted)]">
            <p className="text-sm">
              {tabs.find((t) => t.id === activeTab)?.name} analytics coming soon.
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

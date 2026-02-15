import { useState } from 'react';
import {
  Activity,
  Calendar,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Heart,
} from 'lucide-react';
import {
  Card,
  Chip,
  MetricTile,
  MetricTileSkeleton,
  CardSkeleton,
  EmptyState,
} from '../ui';
import TrainingCalendar from './TrainingCalendar';
import MiniZoneBar from '../MiniZoneBar';
import type {
  PerformanceOverview,
  CalendarData,
  DurationData,
  TimeOfDayData,
  GymData,
  ClassTypeData,
} from './reportTypes';

interface OverviewTabProps {
  loading: boolean;
  error: string | null;
  performanceData: PerformanceOverview | null;
  calendarData: CalendarData | null;
  durationData: DurationData | null;
  timeOfDayData: TimeOfDayData | null;
  gymData: GymData | null;
  classTypeData: ClassTypeData | null;
  zoneTrendsData: Array<{
    session_id: number;
    date: string;
    zones: Record<string, number>;
  }> | null;
  isBJJActivity: boolean;
  selectedTypes: string[];
  chipLabel: string;
  sessionsDelta: number;
  intensityDelta: number;
  rollsDelta: number;
  submissionsDelta: number;
}

function getQuickInsights(
  performanceData: PerformanceOverview | null,
  sessionsDelta: number,
  intensityDelta: number,
  rollsDelta: number,
  submissionsDelta: number
): string[] {
  const summary = performanceData?.summary || {};
  const sessionsValue = summary.total_sessions ?? 0;

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
  return allInsights.slice(0, 2).map((i) => i.text);
}

export default function OverviewTab({
  loading,
  error,
  performanceData,
  calendarData,
  durationData,
  timeOfDayData,
  gymData,
  classTypeData,
  zoneTrendsData,
  isBJJActivity,
  selectedTypes,
  chipLabel,
  sessionsDelta,
  intensityDelta,
  rollsDelta,
  submissionsDelta,
}: OverviewTabProps) {
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>(
    {}
  );
  const toggleCard = (key: string) =>
    setExpandedCards((prev) => ({ ...prev, [key]: !prev[key] }));

  const summary = performanceData?.summary || {};
  const timeseries = performanceData?.daily_timeseries || {};

  const sessionsValue = summary.total_sessions ?? 0;
  const intensityValue =
    summary.avg_intensity != null
      ? summary.avg_intensity.toFixed(1)
      : '0.0';
  const rollsValue = summary.total_rolls ?? 0;
  const submissionsValue = summary.total_submissions_for ?? 0;

  const sessionsSeries = timeseries.sessions || [];
  const intensitySeries = timeseries.intensity || [];
  const rollsSeries = timeseries.rolls || [];
  const submissionsSeries = timeseries.submissions || [];

  const hasData = performanceData && (summary.total_sessions ?? 0) > 0;

  const quickInsights = getQuickInsights(
    performanceData,
    sessionsDelta,
    intensityDelta,
    rollsDelta,
    submissionsDelta
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
          <MetricTileSkeleton />
        </div>
        <CardSkeleton lines={2} />
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

  if (!hasData) {
    return (
      <div className="space-y-6">
        <Card>
          <EmptyState
            icon={Calendar}
            title={
              selectedTypes.length > 0
                ? 'No Data for Selected Activity Types'
                : 'No Training Data Yet'
            }
            description={
              selectedTypes.length > 0
                ? `No sessions found for ${selectedTypes.join(', ')} in this time period. Try adjusting your filters or date range.`
                : 'Start logging your training sessions to see performance analytics, trends, and insights.'
            }
            actionLabel={
              selectedTypes.length > 0 ? undefined : 'Log First Session'
            }
            actionPath={selectedTypes.length > 0 ? undefined : '/log'}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Metric Tiles Grid */}
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
              <h3 className="text-sm font-semibold text-[var(--text)]">
                Quick Insights
              </h3>
              <Chip>{chipLabel}</Chip>
            </div>
            <ul className="space-y-2">
              {quickInsights.map((insight) => (
                <li
                  key={insight}
                  className="text-sm text-[var(--muted)] flex items-start gap-2"
                >
                  <span className="text-[var(--accent)] font-bold">
                    •
                  </span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Training Calendar */}
      {calendarData && calendarData.calendar && (
        <TrainingCalendar
          calendar={calendarData.calendar}
          totalActiveDays={calendarData.total_active_days ?? 0}
          activityRate={calendarData.activity_rate ?? 0}
        />
      )}

      {/* Duration Analytics */}
      {durationData && (durationData.overall_avg ?? 0) > 0 && (
        <Card>
          <button
            className="w-full flex items-center justify-between"
            onClick={() => toggleCard('duration')}
          >
            <div>
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text)' }}
              >
                Duration Analytics
              </h3>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                Avg: {durationData.overall_avg} min
              </p>
            </div>
            {expandedCards.duration ? (
              <ChevronUp
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            ) : (
              <ChevronDown
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            )}
          </button>
          {expandedCards.duration && (
            <div className="mt-4 space-y-3">
              {durationData.by_class_type?.map((ct: any) => (
                <div
                  key={ct.class_type}
                  className="flex justify-between items-center p-3 rounded-lg"
                  style={{ backgroundColor: 'var(--surfaceElev)' }}
                >
                  <span
                    className="text-sm font-medium"
                    style={{ color: 'var(--text)' }}
                  >
                    {ct.class_type}
                  </span>
                  <span
                    className="text-sm"
                    style={{ color: 'var(--muted)' }}
                  >
                    {ct.avg_duration} min avg ({ct.sessions} sessions)
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Time of Day */}
      {timeOfDayData?.patterns &&
        timeOfDayData.patterns.some((p: any) => p.sessions > 0) && (
          <Card>
            <button
              className="w-full flex items-center justify-between"
              onClick={() => toggleCard('timeOfDay')}
            >
              <div>
                <h3
                  className="text-lg font-semibold"
                  style={{ color: 'var(--text)' }}
                >
                  Time of Day
                </h3>
                <p
                  className="text-xs mt-1"
                  style={{ color: 'var(--muted)' }}
                >
                  Performance by training time
                </p>
              </div>
              {expandedCards.timeOfDay ? (
                <ChevronUp
                  className="w-5 h-5"
                  style={{ color: 'var(--muted)' }}
                />
              ) : (
                <ChevronDown
                  className="w-5 h-5"
                  style={{ color: 'var(--muted)' }}
                />
              )}
            </button>
            {expandedCards.timeOfDay && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {timeOfDayData.patterns.map((p: any) => (
                  <div
                    key={p.time_slot}
                    className="p-3 rounded-[14px] text-center"
                    style={{
                      backgroundColor: 'var(--surfaceElev)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <p
                      className="text-xs font-medium uppercase tracking-wide mb-2"
                      style={{ color: 'var(--muted)' }}
                    >
                      {p.time_slot}
                    </p>
                    <p
                      className="text-xl font-semibold"
                      style={{ color: 'var(--text)' }}
                    >
                      {p.sessions}
                    </p>
                    <p
                      className="text-xs mt-1"
                      style={{ color: 'var(--muted)' }}
                    >
                      sessions
                    </p>
                    {p.sessions > 0 && (
                      <p
                        className="text-xs mt-1"
                        style={{ color: 'var(--accent)' }}
                      >
                        Intensity: {p.avg_intensity}/5
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

      {/* Gym Comparison */}
      {gymData?.gyms && gymData.gyms.length > 1 && (
        <Card>
          <button
            className="w-full flex items-center justify-between"
            onClick={() => toggleCard('gym')}
          >
            <div>
              <h3
                className="text-lg font-semibold"
                style={{ color: 'var(--text)' }}
              >
                Gym Comparison
              </h3>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                {gymData.gyms.length} gyms trained at
              </p>
            </div>
            {expandedCards.gym ? (
              <ChevronUp
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            ) : (
              <ChevronDown
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            )}
          </button>
          {expandedCards.gym && (
            <div className="mt-4 space-y-3">
              {gymData.gyms.map((g: any) => (
                <div
                  key={g.gym}
                  className="p-3 rounded-lg flex items-center justify-between"
                  style={{ backgroundColor: 'var(--surfaceElev)' }}
                >
                  <div>
                    <p
                      className="text-sm font-medium"
                      style={{ color: 'var(--text)' }}
                    >
                      {g.gym}
                    </p>
                    <p
                      className="text-xs"
                      style={{ color: 'var(--muted)' }}
                    >
                      {g.sessions} sessions, {g.avg_duration} min avg
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className="text-sm font-semibold"
                      style={{ color: 'var(--accent)' }}
                    >
                      {g.avg_intensity}/5
                    </p>
                    <p
                      className="text-xs"
                      style={{ color: 'var(--muted)' }}
                    >
                      intensity
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Class Type Effectiveness */}
      {classTypeData?.class_types &&
        classTypeData.class_types.length > 1 && (
          <Card>
            <button
              className="w-full flex items-center justify-between"
              onClick={() => toggleCard('classType')}
            >
              <div>
                <h3
                  className="text-lg font-semibold"
                  style={{ color: 'var(--text)' }}
                >
                  Class Type Effectiveness
                </h3>
                <p
                  className="text-xs mt-1"
                  style={{ color: 'var(--muted)' }}
                >
                  Sub rate by class type
                </p>
              </div>
              {expandedCards.classType ? (
                <ChevronUp
                  className="w-5 h-5"
                  style={{ color: 'var(--muted)' }}
                />
              ) : (
                <ChevronDown
                  className="w-5 h-5"
                  style={{ color: 'var(--muted)' }}
                />
              )}
            </button>
            {expandedCards.classType && (
              <div className="mt-4 space-y-3">
                {classTypeData.class_types.map((ct: any) => (
                  <div
                    key={ct.class_type}
                    className="p-3 rounded-lg flex items-center justify-between"
                    style={{ backgroundColor: 'var(--surfaceElev)' }}
                  >
                    <div>
                      <p
                        className="text-sm font-medium"
                        style={{ color: 'var(--text)' }}
                      >
                        {ct.class_type}
                      </p>
                      <p
                        className="text-xs"
                        style={{ color: 'var(--muted)' }}
                      >
                        {ct.sessions} sessions, {ct.avg_rolls} avg rolls
                      </p>
                    </div>
                    <div className="text-right">
                      <p
                        className="text-sm font-semibold"
                        style={{
                          color:
                            ct.sub_rate >= 1
                              ? 'var(--accent)'
                              : 'var(--text)',
                        }}
                      >
                        {ct.sub_rate.toFixed(2)} ratio
                      </p>
                      <p
                        className="text-xs"
                        style={{ color: 'var(--muted)' }}
                      >
                        {ct.total_subs_for}:{ct.total_subs_against} subs
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

      {/* HR Zone Trends */}
      {zoneTrendsData && zoneTrendsData.length > 0 && (
        <Card>
          <button
            className="w-full flex items-center justify-between"
            onClick={() => toggleCard('zonesTrend')}
          >
            <div>
              <div className="flex items-center gap-2">
                <Heart
                  className="w-5 h-5"
                  style={{ color: '#EF4444' }}
                />
                <h3
                  className="text-lg font-semibold"
                  style={{ color: 'var(--text)' }}
                >
                  HR Zone Trends
                </h3>
              </div>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--muted)' }}
              >
                {zoneTrendsData.length} sessions with WHOOP data
              </p>
            </div>
            {expandedCards.zonesTrend ? (
              <ChevronUp
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            ) : (
              <ChevronDown
                className="w-5 h-5"
                style={{ color: 'var(--muted)' }}
              />
            )}
          </button>
          {expandedCards.zonesTrend && (
            <div className="mt-4 space-y-3">
              {/* Aggregate summary */}
              {(() => {
                const zoneKeys = [
                  'zone_one_milli',
                  'zone_two_milli',
                  'zone_three_milli',
                  'zone_four_milli',
                  'zone_five_milli',
                ];
                const zoneLabels = [
                  'Recovery',
                  'Light',
                  'Moderate',
                  'Hard',
                  'Max',
                ];
                const zoneColors = [
                  '#93C5FD',
                  '#34D399',
                  '#FBBF24',
                  '#F97316',
                  '#EF4444',
                ];
                const agg: Record<string, number> = {};
                zoneKeys.forEach((k) => {
                  agg[k] = 0;
                });
                zoneTrendsData.forEach((s) => {
                  zoneKeys.forEach((k) => {
                    agg[k] += s.zones[k] || 0;
                  });
                });
                const totalMs = zoneKeys.reduce(
                  (sum, k) => sum + agg[k],
                  0
                );
                if (totalMs <= 0) return null;
                return (
                  <div
                    className="p-4 rounded-lg"
                    style={{ backgroundColor: 'var(--surfaceElev)' }}
                  >
                    <p
                      className="text-sm font-medium mb-3"
                      style={{ color: 'var(--text)' }}
                    >
                      Period Totals
                    </p>
                    <MiniZoneBar zones={agg} height="h-4" />
                    <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mt-3">
                      {zoneKeys.map((k, i) => {
                        const mins = Math.round(agg[k] / 60000);
                        const pct = (
                          (agg[k] / totalMs) *
                          100
                        ).toFixed(0);
                        return (
                          <div key={k} className="text-center">
                            <div
                              className="w-3 h-3 rounded-sm mx-auto mb-1"
                              style={{
                                backgroundColor: zoneColors[i],
                              }}
                            />
                            <p
                              className="text-xs font-medium"
                              style={{ color: 'var(--text)' }}
                            >
                              {mins}m
                            </p>
                            <p
                              className="text-xs"
                              style={{ color: 'var(--muted)' }}
                            >
                              {pct}%
                            </p>
                            <p
                              className="text-xs"
                              style={{ color: 'var(--muted)' }}
                            >
                              {zoneLabels[i]}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
              {/* Per-session bars */}
              <p
                className="text-sm font-medium"
                style={{ color: 'var(--text)' }}
              >
                Per Session
              </p>
              {zoneTrendsData.map((s) => (
                <div key={s.session_id}>
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="text-xs"
                      style={{ color: 'var(--muted)' }}
                    >
                      {new Date(s.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                    <span
                      className="text-xs"
                      style={{ color: 'var(--muted)' }}
                    >
                      {Math.round(
                        Object.values(s.zones).reduce(
                          (a, b) => a + b,
                          0
                        ) / 60000
                      )}{' '}
                      min
                    </span>
                  </div>
                  <MiniZoneBar zones={s.zones} height="h-2.5" />
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

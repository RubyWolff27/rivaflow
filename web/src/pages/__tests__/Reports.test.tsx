import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  analyticsApi: {
    performanceOverview: vi.fn(() =>
      Promise.resolve({
        data: {
          summary: {
            total_sessions: 12,
            avg_intensity: 3.5,
            total_rolls: 45,
            total_submissions_for: 8,
            total_hours: 18,
          },
          daily_timeseries: { sessions: [], intensity: [], rolls: [], submissions: [] },
          deltas: { sessions: 2, intensity: 0.3, rolls: 5, submissions: 1 },
        },
      })
    ),
    trainingCalendar: vi.fn(() =>
      Promise.resolve({ data: { calendar: [], total_active_days: 12, activity_rate: 0.4 } })
    ),
    partnerStats: vi.fn(() =>
      Promise.resolve({
        data: {
          top_partners: [],
          diversity_metrics: { active_partners: 5 },
          summary: { total_rolls: 45, total_submissions_for: 8, total_submissions_against: 3 },
        },
      })
    ),
    partnerBeltDistribution: vi.fn(() => Promise.resolve({ data: [] })),
    techniqueBreakdown: vi.fn(() =>
      Promise.resolve({
        data: {
          summary: { total_unique_techniques_used: 10, stale_count: 2 },
          category_breakdown: [],
          gi_top_techniques: [],
          nogi_top_techniques: [],
          stale_techniques: [],
        },
      })
    ),
    durationTrends: vi.fn(() => Promise.resolve({ data: {} })),
    timeOfDayPatterns: vi.fn(() => Promise.resolve({ data: {} })),
    gymComparison: vi.fn(() => Promise.resolve({ data: {} })),
    classTypeEffectiveness: vi.fn(() => Promise.resolve({ data: {} })),
  },
  sessionsApi: {
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  whoopApi: {
    getZonesBatch: vi.fn(() => Promise.resolve({ data: { zones: {} } })),
  },
}))

vi.mock('../../hooks/useTier', () => ({
  useFeatureAccess: () => ({
    hasAccess: true,
    tier: 'beta',
  }),
}))

vi.mock('../../components/ActivityTypeFilter', () => ({
  ActivityTypeFilter: () => <div data-testid="activity-filter" />,
}))

vi.mock('../../components/UpgradePrompt', () => ({
  PremiumBadge: () => null,
  UpgradePrompt: () => null,
}))

vi.mock('../../components/analytics/ReadinessTab', () => ({
  default: () => <div data-testid="readiness-tab" />,
}))

vi.mock('../../components/analytics/TechniqueHeatmap', () => ({
  default: () => <div data-testid="technique-heatmap" />,
}))

vi.mock('../../components/analytics/TrainingCalendar', () => ({
  default: () => <div data-testid="training-calendar" />,
}))

vi.mock('../../components/analytics/InsightsTab', () => ({
  default: () => <div data-testid="insights-tab" />,
}))

vi.mock('../../components/analytics/WhoopAnalyticsTab', () => ({
  default: () => <div data-testid="whoop-tab" />,
}))

vi.mock('../../components/MiniZoneBar', () => ({
  default: () => <div data-testid="mini-zone-bar" />,
}))

vi.mock('../../components/ui', () => ({
  Card: ({ children, ...props }: { children: React.ReactNode }) => <div {...props}>{children}</div>,
  Chip: ({ children, ...props }: { children: React.ReactNode }) => (
    <button {...props}>{children}</button>
  ),
  MetricTile: ({
    label,
    value,
  }: {
    label: string;
    value: string | number;
  }) => (
    <div data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
      {label}: {value}
    </div>
  ),
  MetricTileSkeleton: () => <div data-testid="metric-skeleton" />,
  CardSkeleton: () => <div data-testid="card-skeleton" />,
  EmptyState: ({ message }: { message: string }) => <div>{message}</div>,
}))

import Reports from '../Reports'

function renderReports() {
  return render(
    <BrowserRouter>
      <Reports />
    </BrowserRouter>
  )
}

describe('Reports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    renderReports()
    await waitFor(() => {
      expect(screen.getByText(/progress/i)).toBeInTheDocument()
    })
  })

  it('renders tab navigation', async () => {
    renderReports()
    await waitFor(() => {
      expect(screen.getByText(/performance/i)).toBeInTheDocument()
      expect(screen.getByText(/partners/i)).toBeInTheDocument()
      expect(screen.getByText(/techniques/i)).toBeInTheDocument()
    })
  })

  it('fetches performance overview on mount', async () => {
    const { analyticsApi } = await import('../../api/client')
    renderReports()
    await waitFor(() => {
      expect(analyticsApi.performanceOverview).toHaveBeenCalled()
    })
  })

  it('renders date range quick buttons', async () => {
    renderReports()
    await waitFor(() => {
      expect(screen.getByText(/last 7/i)).toBeInTheDocument()
      expect(screen.getByText(/last 14/i)).toBeInTheDocument()
      expect(screen.getByText(/last 30/i)).toBeInTheDocument()
    })
  })

  it('shows overview stats when data loaded', async () => {
    renderReports()
    await waitFor(() => {
      expect(screen.getByText(/12/)).toBeInTheDocument()
    })
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  profileApi: {
    get: vi.fn(() => Promise.resolve({ data: { timezone: 'UTC' } })),
    update: vi.fn(() => Promise.resolve({ data: {} })),
  },
  suggestionsApi: {
    getToday: vi.fn(() => Promise.resolve({ data: null })),
  },
  readinessApi: {
    getByDate: vi.fn(() => Promise.resolve({ data: null })),
  },
  whoopApi: {
    getLatestRecovery: vi.fn(() => Promise.resolve({ data: null })),
    sync: vi.fn(() => Promise.resolve({ data: {} })),
  },
  checkinsApi: {
    getToday: vi.fn(() => Promise.resolve({ data: { checked_in: false, morning: null, midday: null, evening: null } })),
    getYesterday: vi.fn(() => Promise.resolve({ data: null })),
  },
  sessionsApi: {
    getByRange: vi.fn(() => Promise.resolve({ data: [] })),
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  goalsApi: {
    getCurrentWeek: vi.fn(() => Promise.resolve({ data: null })),
  },
  streaksApi: {
    getStatus: vi.fn(() => Promise.resolve({ data: { checkin: { current_streak: 0, longest_streak: 0 }, training: { current_streak: 0, longest_streak: 0 }, readiness: { current_streak: 0, longest_streak: 0 }, any_at_risk: false } })),
  },
  gymsApi: {
    getTodaysClasses: vi.fn(() => Promise.resolve({ data: { classes: [] } })),
  },
  grappleApi: {
    getInsights: vi.fn(() => Promise.resolve({ data: [] })),
  },
  gamePlansApi: {
    getCurrent: vi.fn(() => Promise.resolve({ data: null })),
  },
  weightLogsApi: {
    getLatest: vi.fn(() => Promise.resolve({ data: null })),
    create: vi.fn(),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com', first_name: 'Ruby', last_name: 'Test', subscription_tier: 'beta', is_beta_user: true },
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('../../utils/insightRefresh', () => ({
  refreshIfStale: vi.fn(),
  triggerInsightRefresh: vi.fn(),
}))

vi.mock('../../utils/date', () => ({
  getLocalDateString: () => '2026-02-16',
}))

// Mock child components that make their own API calls
vi.mock('../../components/dashboard/GettingStarted', () => ({ default: () => null }))
vi.mock('../../components/dashboard/TodayClassesWidget', () => ({ default: () => <div data-testid="today-classes" /> }))
vi.mock('../../components/dashboard/LastSession', () => ({ LastSession: () => <div data-testid="last-session" /> }))
vi.mock('../../components/dashboard/QuickLinks', () => ({ default: () => <div data-testid="quick-links" /> }))
vi.mock('../../components/dashboard/MorningPrompt', () => ({ default: () => <div data-testid="morning-prompt" /> }))
vi.mock('../../components/dashboard/MiddayPrompt', () => ({ default: () => <div data-testid="midday-prompt" /> }))
vi.mock('../../components/dashboard/EveningPrompt', () => ({ default: () => <div data-testid="evening-prompt" /> }))
vi.mock('../../components/dashboard/CheckinBadges', () => ({ default: () => null }))
vi.mock('../../components/dashboard/WeekComparison', () => ({ default: () => <div data-testid="week-comparison" /> }))

import Dashboard from '../Dashboard'
import {
  profileApi,
  suggestionsApi,
  readinessApi,
  whoopApi,
  checkinsApi,
  sessionsApi,
  goalsApi,
  streaksApi,
} from '../../api/client'

function renderDashboard() {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/log session/i)).toBeInTheDocument()
    })
  })

  it('renders the greeting bar', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/good/i)).toBeInTheDocument()
    })
  })

  it('renders weekly progress', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/this week/i)).toBeInTheDocument()
    })
  })
})

describe('Dashboard - loading state', () => {
  it('shows skeleton while data is loading', () => {
    // Make suggestions hang so loading stays true
    vi.mocked(suggestionsApi.getToday).mockReturnValue(new Promise(() => {}))

    const { container } = renderDashboard()
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })
})

describe('Dashboard - loaded state details', () => {
  beforeEach(() => {
    // Restore all API mocks to resolving defaults (loading-state test overrides some)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    vi.mocked(profileApi.get).mockImplementation(() => Promise.resolve({ data: { timezone: 'UTC' } }) as any)
    vi.mocked(profileApi.update).mockImplementation(() => Promise.resolve({ data: {} }) as any)
    vi.mocked(suggestionsApi.getToday).mockImplementation(() => Promise.resolve({ data: null }) as any)
    vi.mocked(readinessApi.getByDate).mockImplementation(() => Promise.resolve({ data: null }) as any)
    vi.mocked(whoopApi.getLatestRecovery).mockImplementation(() => Promise.resolve({ data: null }) as any)
    vi.mocked(checkinsApi.getToday).mockImplementation(() => Promise.resolve({ data: { checked_in: false, morning: null, midday: null, evening: null } }) as any)
    vi.mocked(checkinsApi.getYesterday).mockImplementation(() => Promise.resolve({ data: null }) as any)
    vi.mocked(sessionsApi.getByRange).mockImplementation(() => Promise.resolve({ data: [] }) as any)
    vi.mocked(goalsApi.getCurrentWeek).mockImplementation(() => Promise.resolve({ data: null }) as any)
    vi.mocked(streaksApi.getStatus).mockImplementation(() => Promise.resolve({ data: { checkin: { current_streak: 0, longest_streak: 0 }, training: { current_streak: 0, longest_streak: 0 }, readiness: { current_streak: 0, longest_streak: 0 }, any_at_risk: false } }) as any)
  })

  it('renders the sr-only Dashboard heading', async () => {
    renderDashboard()
    await waitFor(() => {
      const headings = screen.getAllByRole('heading', { level: 1 })
      const srOnlyHeading = headings.find(h => h.classList.contains('sr-only'))
      expect(srOnlyHeading).toBeDefined()
      expect(srOnlyHeading).toHaveTextContent('Dashboard')
    })
  })

  it('renders the quick-links widget', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('quick-links')).toBeInTheDocument()
    })
  })

  it('renders the week-comparison widget', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('week-comparison')).toBeInTheDocument()
    })
  })

  it('renders the last-session widget', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('last-session')).toBeInTheDocument()
    })
  })

  it('calls streaksApi.getStatus on mount', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(streaksApi.getStatus).toHaveBeenCalled()
    })
  })

  it('calls suggestionsApi.getToday on mount', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(suggestionsApi.getToday).toHaveBeenCalled()
    })
  })
})

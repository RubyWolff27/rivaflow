import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  readinessApi: {
    getByDate: vi.fn(() => Promise.resolve({ data: null })),
  },
  weightLogsApi: {
    getLatest: vi.fn(() => Promise.resolve({ data: null })),
    create: vi.fn(),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com', subscription_tier: 'beta', is_beta_user: true },
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

// Mock child components that make their own API calls
vi.mock('../../components/dashboard/WeekAtGlance', () => ({ WeekAtGlance: () => <div data-testid="week-at-glance" /> }))
vi.mock('../../components/dashboard/LastSession', () => ({ LastSession: () => <div data-testid="last-session" /> }))
vi.mock('../../components/dashboard/JourneyProgress', () => ({ JourneyProgress: () => <div data-testid="journey-progress" /> }))
vi.mock('../../components/dashboard/WeeklyGoalsBreakdown', () => ({ WeeklyGoalsBreakdown: () => <div data-testid="weekly-goals" /> }))
vi.mock('../../components/dashboard/ReadinessRecommendation', () => ({ default: () => <div data-testid="readiness-rec" /> }))
vi.mock('../../components/dashboard/NextEvent', () => ({ default: () => <div data-testid="next-event" /> }))
vi.mock('../../components/dashboard/MyGameWidget', () => ({ default: () => <div data-testid="my-game" /> }))
vi.mock('../../components/dashboard/LatestInsightWidget', () => ({ default: () => <div data-testid="latest-insight" /> }))

import Dashboard from '../Dashboard'

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

  it('shows loading skeletons initially', () => {
    renderDashboard()
    // Dashboard shows skeleton cards while loading
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders quick action buttons after loading', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/log session/i)).toBeInTheDocument()
    })
  })
})

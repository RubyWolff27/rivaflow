import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetDashboardStats = vi.fn()

vi.mock('../../api/client', () => ({
  adminApi: {
    getDashboardStats: (...args: unknown[]) => mockGetDashboardStats(...args),
    listUsers: vi.fn(),
    getUserDetails: vi.fn(),
    updateUser: vi.fn(),
    deleteUser: vi.fn(),
    listGyms: vi.fn(),
    getPendingGyms: vi.fn(),
    searchGyms: vi.fn(),
    createGym: vi.fn(),
    updateGym: vi.fn(),
    deleteGym: vi.fn(),
    mergeGyms: vi.fn(),
    verifyGym: vi.fn(),
    rejectGym: vi.fn(),
    listComments: vi.fn(),
    deleteComment: vi.fn(),
    listTechniques: vi.fn(),
    deleteTechnique: vi.fn(),
    listWaitlist: vi.fn(),
    getWaitlistStats: vi.fn(),
    inviteWaitlistEntry: vi.fn(),
    bulkInviteWaitlist: vi.fn(),
    declineWaitlistEntry: vi.fn(),
    updateWaitlistNotes: vi.fn(),
    listFeedback: vi.fn(),
    updateFeedbackStatus: vi.fn(),
    getFeedbackStats: vi.fn(),
    broadcastEmail: vi.fn(),
    getGrappleGlobalStats: vi.fn(),
    getGrappleProjections: vi.fn(),
    getGrappleProviderStats: vi.fn(),
    getGrappleTopUsers: vi.fn(),
    getGrappleFeedback: vi.fn(),
    getGrappleFeedbackSummary: vi.fn(),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

vi.mock('../../hooks/usePageTitle', () => ({
  usePageTitle: vi.fn(),
}))

vi.mock('../../components/AdminNav', () => ({
  default: () => <nav data-testid="admin-nav">Admin Nav</nav>,
}))

vi.mock('../../components/ui', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  ),
}))

import AdminDashboard from '../AdminDashboard'

const sampleStats = {
  total_users: 100,
  active_users: 50,
  new_users_week: 10,
  total_sessions: 500,
  total_gyms: 20,
  verified_gyms: 15,
  pending_gyms: 5,
  total_comments: 200,
}

function renderAdminDashboard() {
  return render(
    <BrowserRouter>
      <AdminDashboard />
    </BrowserRouter>
  )
}

describe('AdminDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state while fetching stats', () => {
    mockGetDashboardStats.mockImplementation(() => new Promise(() => {}))
    renderAdminDashboard()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders admin nav after data loads', async () => {
    mockGetDashboardStats.mockResolvedValue({ data: sampleStats })
    renderAdminDashboard()

    await waitFor(() => {
      expect(screen.getByTestId('admin-nav')).toBeInTheDocument()
    })
  })

  it('shows dashboard stats after successful load', async () => {
    mockGetDashboardStats.mockResolvedValue({ data: sampleStats })
    renderAdminDashboard()

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })

    // Stat values are rendered with toLocaleString()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('500')).toBeInTheDocument()
    expect(screen.getByText('200')).toBeInTheDocument()

    // Stat titles
    expect(screen.getByText('Total Users')).toBeInTheDocument()
    expect(screen.getByText('Active Users')).toBeInTheDocument()
    expect(screen.getByText('Total Sessions')).toBeInTheDocument()
    expect(screen.getByText('Comments')).toBeInTheDocument()
  })

  it('shows error state when API call fails', async () => {
    mockGetDashboardStats.mockRejectedValue(new Error('Network error'))
    renderAdminDashboard()

    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument()
    })
  })

  it('renders quick action links', async () => {
    mockGetDashboardStats.mockResolvedValue({ data: sampleStats })
    renderAdminDashboard()

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    expect(screen.getByText('Manage Users')).toBeInTheDocument()
    expect(screen.getByText('Manage Gyms')).toBeInTheDocument()
    expect(screen.getByText('Content Moderation')).toBeInTheDocument()
    expect(screen.getByText('Manage Techniques')).toBeInTheDocument()
  })

  it('renders platform health section with engagement rate', async () => {
    mockGetDashboardStats.mockResolvedValue({ data: sampleStats })
    renderAdminDashboard()

    await waitFor(() => {
      expect(screen.getByText('Platform Health')).toBeInTheDocument()
    })

    expect(screen.getByText('User Engagement')).toBeInTheDocument()
    // 50/100 = 50.0%
    expect(screen.getByText('50.0%')).toBeInTheDocument()
    expect(screen.getByText('Gym Verification Rate')).toBeInTheDocument()
    // 15/20 = 75.0%
    expect(screen.getByText('75.0%')).toBeInTheDocument()
  })
})

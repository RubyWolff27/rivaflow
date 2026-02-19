import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockListUsers = vi.fn()
const mockGetUserDetails = vi.fn()
const mockUpdateUser = vi.fn()
const mockDeleteUser = vi.fn()

vi.mock('../../api/client', () => ({
  adminApi: {
    listUsers: (...args: unknown[]) => mockListUsers(...args),
    getUserDetails: (...args: unknown[]) => mockGetUserDetails(...args),
    updateUser: (...args: unknown[]) => mockUpdateUser(...args),
    deleteUser: (...args: unknown[]) => mockDeleteUser(...args),
    getDashboardStats: vi.fn(),
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
  }),
}))

vi.mock('../../components/AdminNav', () => ({
  default: () => <nav data-testid="admin-nav">Admin Nav</nav>,
}))

vi.mock('../../components/ConfirmDialog', () => ({
  default: () => null,
}))

vi.mock('../../components/ui', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  ),
  PrimaryButton: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => (
    <button onClick={onClick} className={className}>{children}</button>
  ),
  SecondaryButton: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => (
    <button onClick={onClick} className={className}>{children}</button>
  ),
  EmptyState: ({ title, description }: { title: string; description: string; icon?: unknown }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}))

import AdminUsers from '../AdminUsers'

const sampleUsers = [
  {
    id: 1,
    email: 'admin@example.com',
    first_name: 'Admin',
    last_name: 'User',
    is_active: true,
    is_admin: true,
    subscription_tier: 'admin',
    is_beta_user: false,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    email: 'ruby@example.com',
    first_name: 'Ruby',
    last_name: 'Wolff',
    is_active: true,
    is_admin: false,
    subscription_tier: 'premium',
    is_beta_user: true,
    created_at: '2025-06-15T00:00:00Z',
  },
  {
    id: 3,
    email: 'inactive@example.com',
    first_name: 'Inactive',
    last_name: 'Person',
    is_active: false,
    is_admin: false,
    subscription_tier: 'free',
    is_beta_user: false,
    created_at: '2025-09-20T00:00:00Z',
  },
]

function renderAdminUsers() {
  return render(
    <BrowserRouter>
      <AdminUsers />
    </BrowserRouter>
  )
}

describe('AdminUsers', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state while fetching users', () => {
    mockListUsers.mockImplementation(() => new Promise(() => {}))
    renderAdminUsers()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders the page title and subtitle', async () => {
    mockListUsers.mockResolvedValue({ data: { users: [] } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument()
    })
    expect(screen.getByText('Manage user accounts and permissions')).toBeInTheDocument()
  })

  it('renders the admin nav component', async () => {
    mockListUsers.mockResolvedValue({ data: { users: [] } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByTestId('admin-nav')).toBeInTheDocument()
    })
  })

  it('shows empty state when no users found', async () => {
    mockListUsers.mockResolvedValue({ data: { users: [] } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('No Users Found')).toBeInTheDocument()
    })
  })

  it('renders user list with names and emails', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument()
    })
    expect(screen.getByText('admin@example.com')).toBeInTheDocument()
    expect(screen.getByText('Ruby Wolff')).toBeInTheDocument()
    expect(screen.getByText('ruby@example.com')).toBeInTheDocument()
    expect(screen.getByText('Inactive Person')).toBeInTheDocument()
    expect(screen.getByText('inactive@example.com')).toBeInTheDocument()
  })

  it('shows admin badge for admin users', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      // "Admin" appears twice: once as subscription tier badge, once as role badge
      const adminElements = screen.getAllByText('Admin')
      expect(adminElements.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows inactive badge for deactivated users', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  it('shows subscription tier badges', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('Premium')).toBeInTheDocument()
    })
    expect(screen.getByText('Free')).toBeInTheDocument()
  })

  it('renders search input', async () => {
    mockListUsers.mockResolvedValue({ data: { users: [] } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search by name or email...')).toBeInTheDocument()
    })
  })

  it('renders filter buttons', async () => {
    mockListUsers.mockResolvedValue({ data: { users: [] } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('Active Only')).toBeInTheDocument()
    })
    expect(screen.getByText('Inactive Only')).toBeInTheDocument()
    expect(screen.getByText('Admins Only')).toBeInTheDocument()
  })

  it('calls listUsers with search query when typing', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      expect(mockListUsers).toHaveBeenCalled()
    })

    const searchInput = screen.getByPlaceholderText('Search by name or email...')
    fireEvent.change(searchInput, { target: { value: 'ruby' } })

    await waitFor(() => {
      expect(mockListUsers).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'ruby' })
      )
    })
  })

  it('shows beta badge for beta users', async () => {
    mockListUsers.mockResolvedValue({ data: { users: sampleUsers } })
    renderAdminUsers()

    await waitFor(() => {
      expect(screen.getByText('Beta')).toBeInTheDocument()
    })
  })
})

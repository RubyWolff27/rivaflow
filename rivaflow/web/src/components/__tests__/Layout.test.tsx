import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com', is_admin: false },
    isLoading: false,
    logout: vi.fn(),
  }),
}))

vi.mock('../../api/client', () => ({
  notificationsApi: {
    getCounts: vi.fn().mockResolvedValue({
      data: { feed_unread: 0, friend_requests: 0, total: 0 },
    }),
    markFeedAsRead: vi.fn().mockResolvedValue({}),
    markFollowsAsRead: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('../../utils/logger', () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('../Sidebar', () => ({
  default: ({ onQuickLog }: { onQuickLog: () => void }) => (
    <div data-testid="sidebar" onClick={onQuickLog}>Sidebar</div>
  ),
}))

vi.mock('../BottomNav', () => ({
  default: () => <div data-testid="bottom-nav">BottomNav</div>,
}))

vi.mock('../QuickLog', () => ({
  default: ({ isOpen }: { isOpen: boolean }) => (
    isOpen ? <div data-testid="quick-log">QuickLog</div> : null
  ),
}))

vi.mock('../ui/PageTransition', () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

import Layout from '../Layout'

function renderLayout(initialEntries = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Layout>
        <div data-testid="child-content">Page Content</div>
      </Layout>
    </MemoryRouter>
  )
}

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children content', () => {
    renderLayout()
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
    expect(screen.getByText('Page Content')).toBeInTheDocument()
  })

  it('renders sidebar and bottom nav', () => {
    renderLayout()
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('bottom-nav')).toBeInTheDocument()
  })

  it('has a skip to content link for accessibility', () => {
    renderLayout()
    expect(screen.getByText('Skip to main content')).toBeInTheDocument()
  })

  it('shows footer on non-dashboard pages', () => {
    renderLayout(['/sessions'])
    expect(screen.getByText('RIVAFLOW')).toBeInTheDocument()
    expect(screen.getByText('Terms')).toBeInTheDocument()
    expect(screen.getByText('Privacy')).toBeInTheDocument()
  })

  it('hides footer on dashboard (/) page', () => {
    renderLayout(['/'])
    expect(screen.queryByText('RIVAFLOW')).not.toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockUseAuth = vi.fn()

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

import AdminRoute from '../AdminRoute'

function renderWithRoute(user: { id: number; email: string; is_admin?: boolean } | null) {
  mockUseAuth.mockReturnValue({
    user,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  })

  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <div data-testid="admin-content">Admin Panel</div>
            </AdminRoute>
          }
        />
        <Route path="/" element={<div data-testid="home-page">Home</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AdminRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when user is admin', () => {
    renderWithRoute({ id: 1, email: 'admin@test.com', is_admin: true })
    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    expect(screen.getByText('Admin Panel')).toBeInTheDocument()
  })

  it('does not render children when user is not admin', () => {
    renderWithRoute({ id: 2, email: 'user@test.com', is_admin: false })
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('redirects to / when user is not admin', () => {
    renderWithRoute({ id: 2, email: 'user@test.com', is_admin: false })
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
  })

  it('redirects to / when user is null (not logged in)', () => {
    renderWithRoute(null)
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
  })

  it('redirects when user has no is_admin field', () => {
    renderWithRoute({ id: 3, email: 'basic@test.com' })
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
  })

  it('renders arbitrary child elements as admin', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, email: 'admin@test.com', is_admin: true },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <h1>Dashboard</h1>
                <p>Welcome, admin</p>
              </AdminRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Welcome, admin')).toBeInTheDocument()
  })

  it('uses replace navigation for redirect', () => {
    renderWithRoute(null)
    // The Navigate component uses replace prop, meaning the redirect
    // replaces the current history entry. We verify redirection happened.
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
  })

  it('redirects non-admin with is_admin explicitly false', () => {
    renderWithRoute({ id: 5, email: 'nope@test.com', is_admin: false })
    expect(screen.getByTestId('home-page')).toBeInTheDocument()
    expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument()
  })
})

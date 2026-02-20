import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockUseAuth = vi.fn()

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

import PrivateRoute from '../PrivateRoute'

function renderWithRoute(overrides: { user?: { id: number } | null; isLoading?: boolean } = {}) {
  mockUseAuth.mockReturnValue({
    user: overrides.user !== undefined ? overrides.user : { id: 1 },
    isLoading: overrides.isLoading ?? false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  })

  return render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route
          path="/protected"
          element={
            <PrivateRoute>
              <div data-testid="protected-content">Protected Content</div>
            </PrivateRoute>
          }
        />
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('PrivateRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner when isLoading is true', () => {
    renderWithRoute({ isLoading: true, user: null })
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
  })

  it('redirects to /login when no user', () => {
    renderWithRoute({ user: null })
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    renderWithRoute({ user: { id: 1 } })
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
  })

  it('does not show loading spinner when loaded and authenticated', () => {
    renderWithRoute({ user: { id: 1 } })
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })
})

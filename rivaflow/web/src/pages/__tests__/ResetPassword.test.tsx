import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams('token=abc123')],
  }
})

vi.mock('../../api/auth', () => ({
  authApi: {
    resetPassword: vi.fn(),
  },
}))

vi.mock('../../hooks/usePageTitle', () => ({
  usePageTitle: vi.fn(),
}))

import ResetPassword from '../ResetPassword'
import { authApi } from '../../api/auth'

function renderResetPassword() {
  return render(
    <BrowserRouter>
      <ResetPassword />
    </BrowserRouter>
  )
}

describe('ResetPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form with password fields', () => {
    renderResetPassword()
    expect(screen.getByText('Set New Password')).toBeInTheDocument()
    expect(screen.getByLabelText('New Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /reset password/i })
    ).toBeInTheDocument()
  })

  it('validates passwords match', async () => {
    renderResetPassword()

    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'different456' },
    })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Passwords do not match')
      ).toBeInTheDocument()
    })
    expect(authApi.resetPassword).not.toHaveBeenCalled()
  })

  it('validates password length (min 8)', async () => {
    renderResetPassword()

    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'short' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'short' },
    })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Password must be at least 8 characters long')
      ).toBeInTheDocument()
    })
    expect(authApi.resetPassword).not.toHaveBeenCalled()
  })

  it('calls resetPassword API on valid submit', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValueOnce({} as any)
    renderResetPassword()

    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'newpassword123' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'newpassword123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(authApi.resetPassword).toHaveBeenCalledWith(
        'abc123',
        'newpassword123'
      )
    })

    await waitFor(() => {
      expect(
        screen.getByText('Password Reset Successfully')
      ).toBeInTheDocument()
    })
  })

  it('handles API error', async () => {
    vi.mocked(authApi.resetPassword).mockRejectedValueOnce({
      response: { data: { detail: 'Token expired' } },
    })
    renderResetPassword()

    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'newpassword123' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'newpassword123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(screen.getByText('Token expired')).toBeInTheDocument()
    })
  })

  it('has back to login link', () => {
    renderResetPassword()
    expect(screen.getByText(/back to login/i)).toBeInTheDocument()
  })
})

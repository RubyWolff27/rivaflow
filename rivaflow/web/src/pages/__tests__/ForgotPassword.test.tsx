import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/auth', () => ({
  authApi: {
    forgotPassword: vi.fn(),
  },
}))

vi.mock('../../hooks/usePageTitle', () => ({
  usePageTitle: vi.fn(),
}))

import ForgotPassword from '../ForgotPassword'
import { authApi } from '../../api/auth'

function renderForgotPassword() {
  return render(
    <BrowserRouter>
      <ForgotPassword />
    </BrowserRouter>
  )
}

describe('ForgotPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form with email input', () => {
    renderForgotPassword()
    expect(screen.getByText('Reset Your Password')).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /send reset link/i })
    ).toBeInTheDocument()
  })

  it('submits email and shows success message', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({} as any)
    renderForgotPassword()

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeInTheDocument()
    })
    expect(authApi.forgotPassword).toHaveBeenCalledWith('test@example.com')
  })

  it('shows error on API failure', async () => {
    vi.mocked(authApi.forgotPassword).mockRejectedValueOnce({
      response: { data: { detail: 'Rate limit exceeded' } },
    })
    renderForgotPassword()

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument()
    })
  })

  it('shows default error message when no detail provided', async () => {
    vi.mocked(authApi.forgotPassword).mockRejectedValueOnce(
      new Error('Network error')
    )
    renderForgotPassword()

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Failed to send reset email')
      ).toBeInTheDocument()
    })
  })

  it('has back to login link', () => {
    renderForgotPassword()
    expect(screen.getByText(/back to login/i)).toBeInTheDocument()
  })

  it('shows loading state during submission', async () => {
    vi.mocked(authApi.forgotPassword).mockImplementation(
      () => new Promise(() => {})
    )
    renderForgotPassword()

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText('Sending...')).toBeInTheDocument()
    })
  })
})

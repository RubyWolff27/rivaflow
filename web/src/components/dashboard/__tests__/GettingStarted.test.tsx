import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetOnboardingStatus = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../../api/client', () => ({
  profileApi: {
    getOnboardingStatus: (...args: unknown[]) => mockGetOnboardingStatus(...args),
  },
}))

vi.mock('../../ui', () => ({
  Card: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card">{children}</div>
  ),
}))

import GettingStarted from '../GettingStarted'

function renderGettingStarted() {
  return render(
    <BrowserRouter>
      <GettingStarted />
    </BrowserRouter>
  )
}

describe('GettingStarted', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders progress bar with steps', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: true },
          { key: 'readiness', label: 'Log your first readiness', done: false },
          { key: 'session', label: 'Log your first session', done: false },
          { key: 'goals', label: 'Set weekly goals', done: false },
        ],
        all_done: false,
        completed: 1,
        total: 4,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument()
    })

    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('Set up your profile')).toBeInTheDocument()
    expect(screen.getByText('Log your first readiness')).toBeInTheDocument()
    expect(screen.getByText('Log your first session')).toBeInTheDocument()
    expect(screen.getByText('Set weekly goals')).toBeInTheDocument()
  })

  it('dismissing hides component and persists to localStorage', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: false },
        ],
        all_done: false,
        completed: 0,
        total: 1,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Dismiss'))

    // Component should disappear
    await waitFor(() => {
      expect(screen.queryByText('Getting Started')).not.toBeInTheDocument()
    })

    // localStorage should be set
    expect(localStorage.getItem('onboarding_dismissed')).toBe('1')
  })

  it('auto-hides when all steps are complete', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: true },
          { key: 'session', label: 'Log your first session', done: true },
        ],
        all_done: true,
        completed: 2,
        total: 2,
      },
    })

    renderGettingStarted()

    // The component returns null when allDone is true
    // Wait for data to load then verify nothing is rendered
    await waitFor(() => {
      expect(mockGetOnboardingStatus).toHaveBeenCalled()
    })

    expect(screen.queryByText('Getting Started')).not.toBeInTheDocument()
  })

  it('clicking incomplete step navigates to correct page', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: true },
          { key: 'readiness', label: 'Log your first readiness', done: false },
          { key: 'session', label: 'Log your first session', done: false },
          { key: 'goals', label: 'Set weekly goals', done: false },
        ],
        all_done: false,
        completed: 1,
        total: 4,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Log your first readiness')).toBeInTheDocument()
    })

    // Click on the incomplete readiness step
    fireEvent.click(screen.getByText('Log your first readiness'))
    expect(mockNavigate).toHaveBeenCalledWith('/readiness')
  })

  it('clicking on session step navigates to /log', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'session', label: 'Log your first session', done: false },
        ],
        all_done: false,
        completed: 0,
        total: 1,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Log your first session')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Log your first session'))
    expect(mockNavigate).toHaveBeenCalledWith('/log')
  })

  it('clicking on goals step navigates to /profile', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'goals', label: 'Set weekly goals', done: false },
        ],
        all_done: false,
        completed: 0,
        total: 1,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Set weekly goals')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Set weekly goals'))
    expect(mockNavigate).toHaveBeenCalledWith('/profile')
  })

  it('completed steps are disabled and do not navigate', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: true },
          { key: 'session', label: 'Log your first session', done: false },
        ],
        all_done: false,
        completed: 1,
        total: 2,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Set up your profile')).toBeInTheDocument()
    })

    // Completed step button should be disabled
    const profileBtn = screen.getByText('Set up your profile').closest('button')
    expect(profileBtn).toBeDisabled()

    fireEvent.click(screen.getByText('Set up your profile'))
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('completed step labels have line-through class', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Set up your profile', done: true },
          { key: 'session', label: 'Log your first session', done: false },
        ],
        all_done: false,
        completed: 1,
        total: 2,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('Set up your profile')).toBeInTheDocument()
    })

    const completedLabel = screen.getByText('Set up your profile')
    expect(completedLabel).toHaveClass('line-through')
  })

  it('hides when previously dismissed via localStorage', () => {
    localStorage.setItem('onboarding_dismissed', '1')

    renderGettingStarted()

    expect(screen.queryByText('Getting Started')).not.toBeInTheDocument()
    expect(mockGetOnboardingStatus).not.toHaveBeenCalled()
  })

  it('renders with empty steps when API call fails gracefully', async () => {
    mockGetOnboardingStatus.mockRejectedValueOnce(new Error('Not found'))

    renderGettingStarted()

    // Wait for async load to complete
    await waitFor(() => {
      expect(mockGetOnboardingStatus).toHaveBeenCalled()
    })

    // Component renders with 0 steps and 0% since the catch block
    // sets loading to false but steps/allDone remain default
    // The component shows "Getting Started" with 0% and empty step list
    await waitFor(() => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument()
      expect(screen.getByText('0%')).toBeInTheDocument()
    })
  })

  it('shows correct percentage for 3 of 4 completed', async () => {
    mockGetOnboardingStatus.mockResolvedValueOnce({
      data: {
        steps: [
          { key: 'profile', label: 'Profile', done: true },
          { key: 'readiness', label: 'Readiness', done: true },
          { key: 'session', label: 'Session', done: true },
          { key: 'goals', label: 'Goals', done: false },
        ],
        all_done: false,
        completed: 3,
        total: 4,
      },
    })

    renderGettingStarted()

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument()
    })
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockMilestones = vi.fn()

vi.mock('../../../api/client', () => ({
  analyticsApi: {
    milestones: (...args: unknown[]) => mockMilestones(...args),
  },
}))

vi.mock('../../ui', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
}))

import LifetimeJourneyBar from '../LifetimeJourneyBar'

describe('LifetimeJourneyBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows lifetime hours as the hero number and the next milestone', async () => {
    mockMilestones.mockResolvedValueOnce({
      data: { rolling_totals: { lifetime: { hours: 158.3 } } },
    })

    render(<LifetimeJourneyBar />)

    await waitFor(() => {
      expect(screen.getByText('158.3')).toBeInTheDocument()
    })

    expect(screen.getByText('10,000-Hour Journey')).toBeInTheDocument()
    expect(screen.getByText('158 h → next: 250 h')).toBeInTheDocument()
    expect(screen.getByText('1.6% of the 10,000-hour journey')).toBeInTheDocument()
  })

  it('steps the target up as hours pass a milestone', async () => {
    mockMilestones.mockResolvedValueOnce({
      data: { rolling_totals: { lifetime: { hours: 1200 } } },
    })

    render(<LifetimeJourneyBar />)

    await waitFor(() => {
      expect(screen.getByText('1200 h → next: 2500 h')).toBeInTheDocument()
    })

    expect(screen.getByText('12% of the 10,000-hour journey')).toBeInTheDocument()
  })

  it('appends the start year when the API supplies a first session date', async () => {
    mockMilestones.mockResolvedValueOnce({
      data: {
        rolling_totals: { lifetime: { hours: 158.3 } },
        first_session_date: '2021-03-14',
      },
    })

    render(<LifetimeJourneyBar />)

    await waitFor(() => {
      expect(
        screen.getByText('1.6% of the 10,000-hour journey · since 2021')
      ).toBeInTheDocument()
    })
  })

  it('renders zero state without crashing when the API returns nothing useful', async () => {
    mockMilestones.mockResolvedValueOnce({ data: {} })

    render(<LifetimeJourneyBar />)

    await waitFor(() => {
      expect(screen.getByText('0.0')).toBeInTheDocument()
    })

    expect(screen.getByText('0 h → next: 100 h')).toBeInTheDocument()
  })
})

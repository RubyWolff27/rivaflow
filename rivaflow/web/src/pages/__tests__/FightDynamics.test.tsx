import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  analyticsApi: {
    fightDynamicsHeatmap: vi.fn(),
    fightDynamicsInsights: vi.fn(),
  },
}))

vi.mock('../../hooks/usePageTitle', () => ({
  usePageTitle: vi.fn(),
}))

vi.mock('../../utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), debug: vi.fn() },
}))

vi.mock('../../components/dynamics/DynamicsChart', () => ({
  default: () => <div data-testid="dynamics-chart" />,
}))

vi.mock('../../components/dynamics/MatchupCard', () => ({
  default: () => <div data-testid="matchup-card" />,
  SummaryStats: () => <div data-testid="summary-stats" />,
}))

import FightDynamics from '../FightDynamics'
import { analyticsApi } from '../../api/client'

function renderFightDynamics() {
  return render(
    <BrowserRouter>
      <FightDynamics />
    </BrowserRouter>
  )
}

describe('FightDynamics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the title', async () => {
    vi.mocked(analyticsApi.fightDynamicsHeatmap).mockResolvedValueOnce({
      data: [],
    } as any)
    vi.mocked(analyticsApi.fightDynamicsInsights).mockResolvedValueOnce({
      data: null,
    } as any)
    renderFightDynamics()

    expect(screen.getByText('Fight Dynamics')).toBeInTheDocument()
  })

  it('shows data after successful load', async () => {
    vi.mocked(analyticsApi.fightDynamicsHeatmap).mockResolvedValueOnce({
      data: [
        { label: 'Week 1', attacks_attempted: 10, defenses_attempted: 5 },
      ],
    } as any)
    vi.mocked(analyticsApi.fightDynamicsInsights).mockResolvedValueOnce({
      data: { total_attacks: 10, total_defenses: 5 },
    } as any)
    renderFightDynamics()

    await waitFor(() => {
      expect(screen.getByTestId('dynamics-chart')).toBeInTheDocument()
    })
    expect(screen.getByTestId('summary-stats')).toBeInTheDocument()
    expect(screen.getByTestId('matchup-card')).toBeInTheDocument()
  })

  it('shows error state on API failure', async () => {
    vi.mocked(analyticsApi.fightDynamicsHeatmap).mockRejectedValueOnce(
      new Error('Network error')
    )
    vi.mocked(analyticsApi.fightDynamicsInsights).mockRejectedValueOnce(
      new Error('Network error')
    )
    renderFightDynamics()

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load fight dynamics data.')
      ).toBeInTheDocument()
    })
  })

  it('shows empty state when no data', async () => {
    vi.mocked(analyticsApi.fightDynamicsHeatmap).mockResolvedValueOnce({
      data: [
        { label: 'Week 1', attacks_attempted: 0, defenses_attempted: 0 },
      ],
    } as any)
    vi.mocked(analyticsApi.fightDynamicsInsights).mockResolvedValueOnce({
      data: null,
    } as any)
    renderFightDynamics()

    await waitFor(() => {
      expect(
        screen.getByText('No Fight Dynamics Data Yet')
      ).toBeInTheDocument()
    })
  })

  it('renders view toggle buttons', async () => {
    vi.mocked(analyticsApi.fightDynamicsHeatmap).mockResolvedValueOnce({
      data: [],
    } as any)
    vi.mocked(analyticsApi.fightDynamicsInsights).mockResolvedValueOnce({
      data: null,
    } as any)
    renderFightDynamics()

    expect(screen.getByText('8 Weeks')).toBeInTheDocument()
    expect(screen.getByText('6 Months')).toBeInTheDocument()
  })
})

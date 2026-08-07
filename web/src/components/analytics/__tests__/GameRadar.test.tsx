import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGameDistribution = vi.fn()

vi.mock('../../../api/client', () => ({
  analyticsApi: {
    gameDistribution: (...args: unknown[]) => mockGameDistribution(...args),
  },
}))

vi.mock('../../ui', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
}))

import GameRadar from '../GameRadar'

function axis(key: string, label: string, coverageValue: number, axisMax: number) {
  return {
    key,
    label,
    coverage: { value: coverageValue, prev: null, axis_max: axisMax },
    frequency: { value: coverageValue, per_10h: 0.1, prev: null, axis_max: axisMax },
    load: { value: coverageValue, prev: null, axis_max: axisMax },
  }
}

const POPULATED = {
  window: { mode: 'all', start: null, end: '2026-08-04', prev_start: null, prev_end: null },
  axes: [
    axis('takedown', 'Takedowns', 3, 8),
    axis('pass', 'Passing', 5, 8),
    axis('sweep', 'Sweeps', 7, 8),
    axis('submission', 'Submissions', 22, 30),
    axis('escape', 'Escapes', 11, 20),
    axis('defense', 'Defence', 0, 0),
  ],
  gaps: {
    sessions_in_window: 167,
    sessions_with_techniques: 12,
    load_sessions_with_hr: 11,
    load_unattributed_pct: 87.2,
    other_category_touches: 3,
  },
  totals: { mat_hours: 158.3, touches: 39, distinct_movements: 26 },
}

function renderRadar() {
  return render(
    <BrowserRouter>
      <GameRadar />
    </BrowserRouter>
  )
}

describe('GameRadar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all six axis labels in contract order', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Takedowns')).toBeInTheDocument()
    })

    for (const label of ['Passing', 'Sweeps', 'Submissions', 'Escapes', 'Defence']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it('prints the raw value at every vertex that has data', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('22')).toBeInTheDocument()
    })

    for (const value of ['3', '5', '7', '11']) {
      expect(screen.getByText(value)).toBeInTheDocument()
    }
  })

  it('marks an axis with no all-time data rather than plotting it as low', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('no data yet')).toBeInTheDocument()
    })
  })

  it('shows the capture-gap note under the chart', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED })
    renderRadar()

    await waitFor(() => {
      expect(
        screen.getByText('Computed from 12 sessions with logged techniques (of 167 in window)')
      ).toBeInTheDocument()
    })
  })

  it('renders guidance instead of the wheel when fewer than 3 sessions have techniques', async () => {
    mockGameDistribution.mockResolvedValueOnce({
      data: {
        ...POPULATED,
        gaps: { ...POPULATED.gaps, sessions_with_techniques: 2 },
      },
    })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Your wheel is still filling in')).toBeInTheDocument()
    })

    expect(screen.getByText('Log a session').closest('a')).toHaveAttribute('href', '/log')
    expect(screen.queryByText('Takedowns')).not.toBeInTheDocument()
  })

  it('renders no legend when there is only one polygon', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Takedowns')).toBeInTheDocument()
    })

    expect(screen.queryByText('This window')).not.toBeInTheDocument()
    expect(screen.queryByText('Previous')).not.toBeInTheDocument()
  })

  it('renders a legend when every axis carries a previous-window value', async () => {
    mockGameDistribution.mockResolvedValueOnce({
      data: {
        ...POPULATED,
        axes: POPULATED.axes.map((a) => ({
          ...a,
          coverage: { ...a.coverage, prev: 2 },
        })),
      },
    })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('This window')).toBeInTheDocument()
    })

    expect(screen.getByText('Previous')).toBeInTheDocument()
  })

  it('disables the Load toggle while attribution is below 40%', async () => {
    mockGameDistribution.mockResolvedValueOnce({ data: POPULATED }) // 87.2% unattributed
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Takedowns')).toBeInTheDocument()
    })

    const loadBtn = screen.getByRole('button', { name: 'Load' })
    expect(loadBtn).toBeDisabled()
    expect(loadBtn).toHaveAttribute('title', expect.stringContaining('40%'))
  })

  it('enables the Load toggle once attribution reaches 40%', async () => {
    mockGameDistribution.mockResolvedValueOnce({
      data: { ...POPULATED, gaps: { ...POPULATED.gaps, load_unattributed_pct: 55 } },
    })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Takedowns')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Load' })).toBeEnabled()
  })

  it('disables the Load toggle when there is no TRIMP at all (null pct)', async () => {
    mockGameDistribution.mockResolvedValueOnce({
      data: { ...POPULATED, gaps: { ...POPULATED.gaps, load_unattributed_pct: null } },
    })
    renderRadar()

    await waitFor(() => {
      expect(screen.getByText('Takedowns')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Load' })).toBeDisabled()
  })
})

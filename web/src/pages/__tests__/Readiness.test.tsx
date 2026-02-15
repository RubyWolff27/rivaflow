import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  readinessApi: {
    getLatest: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          check_date: '2025-01-15',
          sleep: 4,
          stress: 2,
          soreness: 3,
          energy: 4,
          composite_score: 13,
          hotspot_note: '',
          weight_kg: 80,
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 2 } })),
    getByRange: vi.fn(() => Promise.resolve({ data: [] })),
  },
  profileApi: {
    get: vi.fn(() =>
      Promise.resolve({ data: { target_weight_kg: null, target_weight_date: null } })
    ),
  },
  suggestionsApi: {
    getToday: vi.fn(() => Promise.resolve({ data: null })),
  },
  whoopApi: {
    getReadinessAutoFill: vi.fn(() => Promise.resolve({ data: { auto_fill: null } })),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('../../utils/insightRefresh', () => ({
  triggerInsightRefresh: vi.fn(),
}))

vi.mock('../../components/ReadinessResult', () => ({
  default: () => <div data-testid="readiness-result" />,
}))

vi.mock('../../components/analytics/ReadinessTrendChart', () => ({
  default: () => <div data-testid="readiness-trend-chart" />,
}))

import Readiness from '../Readiness'

function renderReadiness() {
  return render(
    <BrowserRouter>
      <Readiness />
    </BrowserRouter>
  )
}

describe('Readiness', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    renderReadiness()
    await waitFor(() => {
      expect(screen.getByText('Daily Readiness')).toBeInTheDocument()
    })
  })

  it('fetches latest readiness on mount', async () => {
    const { readinessApi } = await import('../../api/client')
    renderReadiness()
    await waitFor(() => {
      expect(readinessApi.getLatest).toHaveBeenCalled()
    })
  })

  it('renders readiness form with sliders', async () => {
    renderReadiness()
    await waitFor(() => {
      expect(screen.getByText(/sleep/i)).toBeInTheDocument()
      expect(screen.getByText(/stress/i)).toBeInTheDocument()
      expect(screen.getByText(/soreness/i)).toBeInTheDocument()
      expect(screen.getByText(/energy/i)).toBeInTheDocument()
    })
  })

  it('displays latest readiness data', async () => {
    renderReadiness()
    await waitFor(() => {
      expect(screen.getByText(/latest/i)).toBeInTheDocument()
    })
  })

  it('renders composite score', async () => {
    renderReadiness()
    await waitFor(() => {
      expect(screen.getByText(/\/20/)).toBeInTheDocument()
    })
  })
})

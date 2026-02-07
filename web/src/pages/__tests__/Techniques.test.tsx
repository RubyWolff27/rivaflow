import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockList = vi.fn()
const mockGetStale = vi.fn()

vi.mock('../../api/client', () => ({
  techniquesApi: {
    list: (...args: unknown[]) => mockList(...args),
    getStale: (...args: unknown[]) => mockGetStale(...args),
  },
}))

import Techniques from '../Techniques'

function renderTechniques() {
  return render(
    <BrowserRouter>
      <Techniques />
    </BrowserRouter>
  )
}

describe('Techniques', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeletons while fetching', () => {
    mockList.mockImplementation(() => new Promise(() => {}))
    mockGetStale.mockImplementation(() => new Promise(() => {}))
    renderTechniques()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows empty state message when no techniques exist', async () => {
    mockList.mockResolvedValueOnce({ data: { techniques: [] } })
    mockGetStale.mockResolvedValueOnce({ data: [] })
    renderTechniques()

    await waitFor(() => {
      expect(screen.getByText(/no techniques tracked yet/i)).toBeInTheDocument()
    })
  })

  it('renders technique table when data is loaded', async () => {
    mockList.mockResolvedValueOnce({
      data: {
        techniques: [
          {
            id: 1,
            name: 'Armbar',
            category: 'submission',
            last_trained_date: '2025-01-20',
            train_count: 5,
          },
        ],
      },
    })
    mockGetStale.mockResolvedValueOnce({ data: [] })
    renderTechniques()

    await waitFor(() => {
      expect(screen.getByText('Armbar')).toBeInTheDocument()
    })
  })

  it('shows stale techniques alert when present', async () => {
    mockList.mockResolvedValueOnce({
      data: {
        techniques: [
          { id: 1, name: 'Armbar', category: 'submission', last_trained_date: '2025-01-01', train_count: 3 },
        ],
      },
    })
    mockGetStale.mockResolvedValueOnce({
      data: [
        { id: 1, name: 'Armbar', category: 'submission', last_trained_date: '2025-01-01', train_count: 3 },
      ],
    })
    renderTechniques()

    await waitFor(() => {
      expect(screen.getByText(/stale techniques/i)).toBeInTheDocument()
    })
  })
})

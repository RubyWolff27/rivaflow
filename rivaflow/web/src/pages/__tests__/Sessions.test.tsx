import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockList = vi.fn()

vi.mock('../../api/client', () => ({
  sessionsApi: {
    list: (...args: unknown[]) => mockList(...args),
  },
}))

import Sessions from '../Sessions'

function renderSessions() {
  return render(
    <BrowserRouter>
      <Sessions />
    </BrowserRouter>
  )
}

describe('Sessions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeletons while fetching', () => {
    mockList.mockImplementation(() => new Promise(() => {}))
    renderSessions()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders session list when data is loaded', async () => {
    mockList.mockResolvedValueOnce({
      data: [
        {
          id: 1,
          session_date: '2025-01-20',
          class_type: 'gi',
          gym_name: 'Gracie Barra',
          location: 'Sydney',
          duration_mins: 60,
          intensity: 4,
          rolls: 5,
          submissions_for: 2,
          submissions_against: 1,
          notes: 'Good session',
        },
      ],
    })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Gracie Barra')).toBeInTheDocument()
    })
  })

  it('shows empty state when no sessions exist', async () => {
    mockList.mockResolvedValueOnce({ data: [] })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText(/no sessions logged yet/i)).toBeInTheDocument()
    })
  })

  it('renders search and filter controls', async () => {
    mockList.mockResolvedValueOnce({ data: [] })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
    })
  })
})

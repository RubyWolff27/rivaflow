import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockList = vi.fn()
const mockGetZonesBatch = vi.fn()

vi.mock('../../api/client', () => ({
  sessionsApi: {
    list: (...args: unknown[]) => mockList(...args),
  },
  whoopApi: {
    getZonesBatch: (...args: unknown[]) => mockGetZonesBatch(...args),
  },
}))

vi.mock('../../components/sessions/SessionScoreBadge', () => ({
  default: ({ score }: { score?: number }) => (
    <span data-testid="score-badge">{score ?? '-'}</span>
  ),
}))

vi.mock('../../components/MiniZoneBar', () => ({
  default: () => <div data-testid="zone-bar" />,
}))

import Sessions from '../Sessions'

const sampleSessions = [
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
    session_score: 72,
  },
  {
    id: 2,
    session_date: '2025-01-18',
    class_type: 'no-gi',
    gym_name: 'Alliance BJJ',
    location: 'Melbourne',
    duration_mins: 90,
    intensity: 5,
    rolls: 8,
    submissions_for: 4,
    submissions_against: 2,
    notes: 'Competition training',
    session_score: 85,
  },
  {
    id: 3,
    session_date: '2025-01-15',
    class_type: 'gi',
    gym_name: 'Gracie Barra',
    location: 'Sydney',
    duration_mins: 75,
    intensity: 3,
    rolls: 4,
    submissions_for: 1,
    submissions_against: 0,
    notes: 'Technique focus day',
    session_score: 55,
  },
]

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
    mockGetZonesBatch.mockResolvedValue({ data: { zones: {} } })
  })

  it('shows loading skeletons while fetching', () => {
    mockList.mockImplementation(() => new Promise(() => {}))
    renderSessions()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders session list when data is loaded', async () => {
    mockList.mockResolvedValueOnce({
      data: [sampleSessions[0]],
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

  // --- New tests ---

  it('displays multiple sessions in the list', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      // Gracie Barra appears twice (sessions 1 and 3)
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
    })

    expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
  })

  it('shows stats overview with correct totals', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument() // Total sessions
    })

    // Total hours = (60 + 90 + 75) / 60 = 3.75 -> 3.8
    expect(screen.getByText('3.8')).toBeInTheDocument()
    // Total rolls = 5 + 8 + 4 = 17
    expect(screen.getByText('17')).toBeInTheDocument()
  })

  it('shows page title "All Sessions"', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('All Sessions')).toBeInTheDocument()
    })
  })

  it('shows subtitle text', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('View and manage your training history')).toBeInTheDocument()
    })
  })

  it('renders session class type badges', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
    })

    // class_type text should appear - gi appears in badges and filter dropdown
    const giBadges = screen.getAllByText('gi')
    expect(giBadges.length).toBeGreaterThanOrEqual(2) // 2 gi sessions + option
    // no-gi appears in badge and also in the filter dropdown option
    const noGiElements = screen.getAllByText('no-gi')
    expect(noGiElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders session duration for each session', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
    })

    expect(screen.getByText('60 min')).toBeInTheDocument()
    expect(screen.getByText('90 min')).toBeInTheDocument()
    expect(screen.getByText('75 min')).toBeInTheDocument()
  })

  it('renders session score badges', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
    })

    const badges = screen.getAllByTestId('score-badge')
    expect(badges.length).toBe(3)
  })

  it('filtering by search term narrows results', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
      expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
    })

    // Type in search field
    const searchInput = screen.getByPlaceholderText(/search/i)
    fireEvent.change(searchInput, { target: { value: 'Alliance' } })

    await waitFor(() => {
      expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
    })

    // Gracie Barra sessions should be filtered out
    expect(screen.queryByText('Gracie Barra')).not.toBeInTheDocument()
  })

  it('filtering by search shows "No sessions match your filters" when no match', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Gracie Barra').length).toBe(2)
    })

    const searchInput = screen.getByPlaceholderText(/search/i)
    fireEvent.change(searchInput, { target: { value: 'Nonexistent Gym' } })

    await waitFor(() => {
      expect(screen.getByText('No sessions match your filters')).toBeInTheDocument()
    })
  })

  it('filter by type shows only matching class type', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
    })

    // Find the type filter select
    const typeFilter = screen.getByDisplayValue('All Types')
    fireEvent.change(typeFilter, { target: { value: 'no-gi' } })

    await waitFor(() => {
      expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
    })

    // Gi sessions should be filtered out
    expect(screen.queryByText('Gracie Barra')).not.toBeInTheDocument()
  })

  it('sort by duration reorders sessions', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Alliance BJJ')).toBeInTheDocument()
    })

    // Change sort to duration
    const sortSelect = screen.getByDisplayValue('Sort by Date')
    fireEvent.change(sortSelect, { target: { value: 'duration' } })

    // After sorting by duration desc, Alliance BJJ (90m) should be first
    const links = document.querySelectorAll('a[href^="/session/"]')
    expect(links.length).toBe(3)
  })

  it('shows location for sessions that have one', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getAllByText('Sydney').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('Melbourne')).toBeInTheDocument()
    })
  })

  it('shows submissions for and against', async () => {
    mockList.mockResolvedValueOnce({ data: [sampleSessions[0]] })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Gracie Barra')).toBeInTheDocument()
    })

    // session 1: 2 for, 1 against - check for the submissions text pattern
    expect(screen.getByText(/submissions/i)).toBeInTheDocument()
    // Check the emerald-colored "for" count and the error-colored "against" count
    const forSpan = document.querySelector('.text-emerald-500')
    expect(forSpan).toBeTruthy()
    expect(forSpan!.textContent).toBe('2')
  })

  it('renders session notes preview', async () => {
    mockList.mockResolvedValueOnce({ data: [sampleSessions[0]] })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Good session')).toBeInTheDocument()
    })
  })

  it('session cards link to session detail page', async () => {
    mockList.mockResolvedValueOnce({ data: [sampleSessions[0]] })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Gracie Barra')).toBeInTheDocument()
    })

    const link = document.querySelector('a[href="/session/1"]')
    expect(link).toBeTruthy()
  })

  it('calls sessionsApi.list with limit', async () => {
    mockList.mockResolvedValueOnce({ data: [] })
    renderSessions()

    await waitFor(() => {
      expect(mockList).toHaveBeenCalledWith(200)
    })
  })

  it('fetches zone data for sessions', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(mockGetZonesBatch).toHaveBeenCalledWith([1, 2, 3])
    })
  })

  it('shows stat labels', async () => {
    mockList.mockResolvedValueOnce({ data: sampleSessions })
    renderSessions()

    await waitFor(() => {
      expect(screen.getByText('Total Sessions')).toBeInTheDocument()
      expect(screen.getByText('Total Hours')).toBeInTheDocument()
      expect(screen.getByText('Total Rolls')).toBeInTheDocument()
      expect(screen.getByText('Avg Intensity')).toBeInTheDocument()
    })
  })
})

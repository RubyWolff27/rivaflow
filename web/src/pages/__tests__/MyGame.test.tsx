import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockTechniqueBreakdown = vi.fn()
const mockSessionsList = vi.fn()

vi.mock('../../api/client', () => ({
  analyticsApi: {
    techniqueBreakdown: (...args: unknown[]) => mockTechniqueBreakdown(...args),
    partnerStats: vi.fn(),
    performanceOverview: vi.fn(),
    readinessTrends: vi.fn(),
    whoopAnalytics: vi.fn(),
    consistencyMetrics: vi.fn(),
  },
  sessionsApi: {
    list: (...args: unknown[]) => mockSessionsList(...args),
    create: vi.fn(),
    getById: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getAutocomplete: vi.fn(),
  },
  getErrorMessage: (err: unknown) => (err as Error)?.message || 'Unknown error',
}))

vi.mock('../../utils/logger', () => ({
  logger: { debug: vi.fn(), info: vi.fn(), error: vi.fn(), warn: vi.fn() },
}))

import MyGame from '../MyGame'

const sampleTechData = {
  summary: {
    total_unique_techniques_used: 12,
    stale_count: 3,
  },
  category_breakdown: [
    { category: 'submission', count: 8 },
    { category: 'position', count: 15 },
    { category: 'sweep', count: 5 },
    { category: 'pass', count: 7 },
  ],
  top_submissions: [
    { name: 'Armbar', category: 'submission', count: 6 },
    { name: 'Triangle', category: 'submission', count: 4 },
    { name: 'Guillotine', category: 'submission', count: 2 },
  ],
  submission_stats: {
    total_submissions_for: 15,
    total_submissions_against: 8,
    sessions_with_submissions: 10,
  },
  stale_techniques: [
    { id: 1, name: 'Kimura' },
    { id: 2, name: 'Omoplata' },
    { id: 3, name: 'Ezekiel' },
  ],
}

const sampleSessions = [
  {
    id: 1,
    session_date: '2026-03-07',
    class_type: 'Gi',
    gym_name: 'Gracie Barra',
    duration_mins: 60,
    intensity: 7,
    rolls: 5,
    submissions_for: 2,
    submissions_against: 1,
    notes: 'Worked on closed guard retention and sweeps. Good rolls today.',
    techniques: ['Armbar', 'Scissor Sweep', 'Triangle', 'Hip Escape', 'Knee Shield'],
  },
  {
    id: 2,
    session_date: '2026-03-05',
    class_type: 'No-Gi',
    gym_name: 'Gracie Barra',
    duration_mins: 90,
    intensity: 8,
    rolls: 6,
    submissions_for: 3,
    submissions_against: 0,
    notes: 'Competition prep. Focused on takedowns.',
    techniques: ['Single Leg', 'Guillotine'],
  },
]

function renderMyGame() {
  return render(
    <BrowserRouter>
      <MyGame />
    </BrowserRouter>
  )
}

describe('MyGame', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton while fetching data', () => {
    mockTechniqueBreakdown.mockImplementation(() => new Promise(() => {}))
    mockSessionsList.mockImplementation(() => new Promise(() => {}))
    renderMyGame()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows empty state when no data exists', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: { summary: { total_unique_techniques_used: 0 } } })
    mockSessionsList.mockResolvedValue({ data: [] })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Build Your Game')).toBeInTheDocument()
    })
    expect(screen.getByText(/Log sessions with techniques/)).toBeInTheDocument()
    expect(screen.getByText('Log a Session')).toBeInTheDocument()
  })

  it('renders stat cards with technique data', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Techniques')).toBeInTheDocument()
    })
    expect(screen.getByText('Subs For')).toBeInTheDocument()
    expect(screen.getByText('Subs Against')).toBeInTheDocument()
    expect(screen.getByText('Stale (30d)')).toBeInTheDocument()
  })

  it('renders submission ratio bar', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Submission Ratio')).toBeInTheDocument()
    })
    // 15/(15+8) = 65%
    expect(screen.getByText('65% yours')).toBeInTheDocument()
    expect(screen.getByText('15 for')).toBeInTheDocument()
    expect(screen.getByText('8 against')).toBeInTheDocument()
  })

  it('renders top submissions list', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Top Submissions')).toBeInTheDocument()
    })
    // Armbar appears in both top submissions and session chips
    const armbars = screen.getAllByText('Armbar')
    expect(armbars.length).toBeGreaterThanOrEqual(1)
    // Guillotine appears in both top submissions and session 2 chips
    const guillotines = screen.getAllByText('Guillotine')
    expect(guillotines.length).toBeGreaterThanOrEqual(1)
  })

  it('renders category breakdown', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Technique Categories')).toBeInTheDocument()
    })
    expect(screen.getByText('submission')).toBeInTheDocument()
    expect(screen.getByText('position')).toBeInTheDocument()
    expect(screen.getByText('sweep')).toBeInTheDocument()
    expect(screen.getByText('pass')).toBeInTheDocument()
  })

  it('renders recent training notes with session data', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Recent Training Notes')).toBeInTheDocument()
    })
    expect(screen.getByText(/closed guard retention/)).toBeInTheDocument()
    expect(screen.getByText(/Competition prep/)).toBeInTheDocument()
  })

  it('shows technique chips on session notes', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Scissor Sweep')).toBeInTheDocument()
    })
    // First session has 5 techniques, only 4 shown + "+1 more"
    expect(screen.getByText('+1 more')).toBeInTheDocument()
  })

  it('renders stale techniques section', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Stale Techniques')).toBeInTheDocument()
    })
    expect(screen.getByText('Kimura')).toBeInTheDocument()
    expect(screen.getByText('Omoplata')).toBeInTheDocument()
    expect(screen.getByText('Ezekiel')).toBeInTheDocument()
    expect(screen.getByText('Not trained in 30+ days')).toBeInTheDocument()
  })

  it('renders page header with title', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('My Game')).toBeInTheDocument()
    })
    expect(screen.getByText('Built from your actual training data')).toBeInTheDocument()
  })

  it('hides submission ratio when no submissions exist', async () => {
    const noSubsData = {
      ...sampleTechData,
      submission_stats: {
        total_submissions_for: 0,
        total_submissions_against: 0,
        sessions_with_submissions: 0,
      },
    }
    mockTechniqueBreakdown.mockResolvedValue({ data: noSubsData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('My Game')).toBeInTheDocument()
    })
    expect(screen.queryByText('Submission Ratio')).not.toBeInTheDocument()
  })

  it('navigates to session detail when clicking a note', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText(/closed guard retention/)).toBeInTheDocument()
    })

    const noteButton = screen.getByText(/closed guard retention/).closest('button')
    expect(noteButton).toBeTruthy()
    fireEvent.click(noteButton!)
    // Navigation happens via useNavigate — just verify button is clickable
  })
})

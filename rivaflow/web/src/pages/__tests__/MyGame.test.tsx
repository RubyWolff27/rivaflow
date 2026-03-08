import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockTechniqueBreakdown = vi.fn()
const mockSessionsList = vi.fn()
const mockGetCurrent = vi.fn()
const mockGenerate = vi.fn()
const mockAddNode = vi.fn()
const mockDeleteNode = vi.fn()

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
  gamePlansApi: {
    getCurrent: (...args: unknown[]) => mockGetCurrent(...args),
    generate: (...args: unknown[]) => mockGenerate(...args),
    getById: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    addNode: (...args: unknown[]) => mockAddNode(...args),
    updateNode: vi.fn(),
    deleteNode: (...args: unknown[]) => mockDeleteNode(...args),
    addEdge: vi.fn(),
    deleteEdge: vi.fn(),
    setFocus: vi.fn(),
  },
  getErrorMessage: (err: unknown) => (err as Error)?.message || 'Unknown error',
}))

vi.mock('../../utils/logger', () => ({
  logger: { debug: vi.fn(), info: vi.fn(), error: vi.fn(), warn: vi.fn() },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
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
    techniques: ['Scissor Sweep', 'Hip Escape', 'Knee Shield', 'Cross Collar Choke'],
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

const samplePlan = {
  id: 1,
  title: 'White Belt Guard Game',
  belt_level: 'white',
  archetype: 'guard_player',
  style: 'balanced',
  is_active: true,
  created_at: '2026-03-01',
  updated_at: '2026-03-08',
  nodes: [
    {
      id: 10,
      plan_id: 1,
      name: 'Closed Guard',
      node_type: 'position',
      confidence: 3,
      priority: 'normal',
      is_focus: true,
      attempts: 10,
      successes: 7,
      sort_order: 0,
      created_at: '2026-03-01',
      updated_at: '2026-03-08',
      children: [
        {
          id: 11,
          plan_id: 1,
          name: 'Armbar from Guard',
          node_type: 'submission',
          confidence: 2,
          priority: 'normal',
          is_focus: false,
          attempts: 5,
          successes: 2,
          sort_order: 0,
          created_at: '2026-03-01',
          updated_at: '2026-03-08',
          children: [],
        },
      ],
    },
    {
      id: 12,
      plan_id: 1,
      name: 'Half Guard',
      node_type: 'position',
      confidence: 4,
      priority: 'normal',
      is_focus: false,
      attempts: 8,
      successes: 5,
      sort_order: 1,
      created_at: '2026-03-01',
      updated_at: '2026-03-08',
      children: [],
    },
  ],
  flat_nodes: [
    { id: 10, name: 'Closed Guard' },
    { id: 11, name: 'Armbar from Guard' },
    { id: 12, name: 'Half Guard' },
  ],
  focus_nodes: [
    { id: 10, name: 'Closed Guard', node_type: 'position' },
  ],
}

function renderMyGame() {
  return render(
    <BrowserRouter>
      <MyGame />
    </BrowserRouter>
  )
}

function setupWithData(planData: unknown = samplePlan) {
  mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
  mockSessionsList.mockResolvedValue({ data: sampleSessions })
  mockGetCurrent.mockResolvedValue({ data: planData })
}

describe('MyGame', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Stats Section ---

  it('shows loading skeleton while fetching data', () => {
    mockTechniqueBreakdown.mockImplementation(() => new Promise(() => {}))
    mockSessionsList.mockImplementation(() => new Promise(() => {}))
    mockGetCurrent.mockImplementation(() => new Promise(() => {}))
    renderMyGame()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows empty state when no data and no plan exists', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: { summary: { total_unique_techniques_used: 0 } } })
    mockSessionsList.mockResolvedValue({ data: [] })
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Build Your Game')).toBeInTheDocument()
    })
    expect(screen.getByText(/Log sessions with techniques/)).toBeInTheDocument()
  })

  it('renders stat cards with technique data', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Techniques')).toBeInTheDocument()
    })
    expect(screen.getByText('Subs For')).toBeInTheDocument()
    expect(screen.getByText('Subs Against')).toBeInTheDocument()
    expect(screen.getByText('Stale (30d)')).toBeInTheDocument()
  })

  it('renders submission ratio bar', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Submission Ratio')).toBeInTheDocument()
    })
    expect(screen.getByText('65% yours')).toBeInTheDocument()
    expect(screen.getByText('15 for')).toBeInTheDocument()
    expect(screen.getByText('8 against')).toBeInTheDocument()
  })

  it('renders category breakdown', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Technique Categories')).toBeInTheDocument()
    })
  })

  it('renders stale techniques section', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Stale Techniques')).toBeInTheDocument()
    })
    expect(screen.getByText('Kimura')).toBeInTheDocument()
    expect(screen.getByText('Not trained in 30+ days')).toBeInTheDocument()
  })

  it('renders recent training notes', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Recent Training Notes')).toBeInTheDocument()
    })
    expect(screen.getByText(/closed guard retention/)).toBeInTheDocument()
    expect(screen.getByText(/Competition prep/)).toBeInTheDocument()
  })

  // --- Game Plan Tree Section ---

  it('shows create wizard when no plan exists', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Technique Mind Map')).toBeInTheDocument()
    })
    expect(screen.getByText(/technique mind map/)).toBeInTheDocument()
    expect(screen.getByText('Generate Game Plan')).toBeInTheDocument()
  })

  it('shows belt selection options in wizard', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('White')).toBeInTheDocument()
    })
    expect(screen.getByText('Blue')).toBeInTheDocument()
    expect(screen.getByText('Purple')).toBeInTheDocument()
    expect(screen.getByText('Brown')).toBeInTheDocument()
    expect(screen.getByText('Black')).toBeInTheDocument()
  })

  it('shows archetype options in wizard', async () => {
    mockTechniqueBreakdown.mockResolvedValue({ data: sampleTechData })
    mockSessionsList.mockResolvedValue({ data: sampleSessions })
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Guard Player')).toBeInTheDocument()
    })
    expect(screen.getByText('Top Passer')).toBeInTheDocument()
  })

  it('renders tree nodes when plan exists', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      // Closed Guard appears in tree and focus areas
      const closedGuards = screen.getAllByText('Closed Guard')
      expect(closedGuards.length).toBeGreaterThanOrEqual(2)
    })
    expect(screen.getByText('Half Guard')).toBeInTheDocument()
    expect(screen.getByText('Armbar from Guard')).toBeInTheDocument()
  })

  it('renders focus areas section', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Focus Areas')).toBeInTheDocument()
    })
  })

  it('shows Add Node button when plan exists', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Add Node')).toBeInTheDocument()
    })
  })

  it('shows add node form when Add Node clicked', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Add Node')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Node'))

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Node name...')).toBeInTheDocument()
    })
  })

  it('renders node type legend', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      // position appears in tree nodes and legend
      const positions = screen.getAllByText('position')
      expect(positions.length).toBeGreaterThanOrEqual(1)
    })
    // sweep/pass appear in both category breakdown and legend — use getAllByText
    expect(screen.getAllByText('sweep').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('pass').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('escape')).toBeInTheDocument()
  })

  it('shows attempt stats for nodes', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('7/10')).toBeInTheDocument()
    })
    expect(screen.getByText('2/5')).toBeInTheDocument()
    expect(screen.getByText('5/8')).toBeInTheDocument()
  })

  it('renders page header', async () => {
    setupWithData()
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('My Game')).toBeInTheDocument()
    })
    expect(screen.getByText('Built from your actual training data')).toBeInTheDocument()
  })
})

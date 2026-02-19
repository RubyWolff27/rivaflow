import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetCurrent = vi.fn()
const mockGenerate = vi.fn()
const mockAddNode = vi.fn()
const mockUpdateNode = vi.fn()
const mockDeleteNode = vi.fn()

vi.mock('../../api/client', () => ({
  gamePlansApi: {
    getCurrent: (...args: unknown[]) => mockGetCurrent(...args),
    generate: (...args: unknown[]) => mockGenerate(...args),
    getById: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    addNode: (...args: unknown[]) => mockAddNode(...args),
    updateNode: (...args: unknown[]) => mockUpdateNode(...args),
    deleteNode: (...args: unknown[]) => mockDeleteNode(...args),
    addEdge: vi.fn(),
    deleteEdge: vi.fn(),
    setFocus: vi.fn(),
  },
  getErrorMessage: (err: unknown) => (err as Error)?.message || 'Unknown error',
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

import MyGame from '../MyGame'

const samplePlan = {
  id: 1,
  title: 'White Belt Guard Game',
  belt_level: 'white',
  archetype: 'guard_player',
  nodes: [
    {
      id: 10,
      name: 'Closed Guard',
      node_type: 'position',
      confidence: 3,
      is_focus: true,
      attempts: 10,
      successes: 7,
      children: [
        {
          id: 11,
          name: 'Armbar from Guard',
          node_type: 'submission',
          confidence: 2,
          is_focus: false,
          attempts: 5,
          successes: 2,
          children: [],
        },
      ],
    },
    {
      id: 12,
      name: 'Half Guard',
      node_type: 'position',
      confidence: 4,
      is_focus: false,
      attempts: 8,
      successes: 5,
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

describe('MyGame', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton while fetching plan', () => {
    mockGetCurrent.mockImplementation(() => new Promise(() => {}))
    renderMyGame()
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows the plan wizard when no plan exists', async () => {
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Build Your Game')).toBeInTheDocument()
    })
    expect(screen.getByText(/technique mind map/)).toBeInTheDocument()
  })

  it('shows belt selection options in wizard', async () => {
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

  it('shows archetype selection options in wizard', async () => {
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Guard Player')).toBeInTheDocument()
    })
    expect(screen.getByText('Top Passer')).toBeInTheDocument()
    expect(screen.getByText('Bottom game focused')).toBeInTheDocument()
    expect(screen.getByText('Passing and pressure')).toBeInTheDocument()
  })

  it('shows Generate Game Plan button in wizard', async () => {
    mockGetCurrent.mockResolvedValue({ data: { plan: null } })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Generate Game Plan')).toBeInTheDocument()
    })
  })

  it('renders the game plan title and metadata when plan exists', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('White Belt Guard Game')).toBeInTheDocument()
    })
  })

  it('renders tree nodes when plan has data', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      // "Closed Guard" appears in both focus areas and tree
      const closedGuardElements = screen.getAllByText('Closed Guard')
      expect(closedGuardElements.length).toBeGreaterThanOrEqual(2)
    })
    expect(screen.getByText('Half Guard')).toBeInTheDocument()
    // Child node should be visible since depth < 2 is expanded by default
    expect(screen.getByText('Armbar from Guard')).toBeInTheDocument()
  })

  it('renders focus areas section', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Focus Areas')).toBeInTheDocument()
    })
  })

  it('shows Add Node button', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Add Node')).toBeInTheDocument()
    })
  })

  it('shows add node form when Add Node is clicked', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('Add Node')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Node'))

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Node name...')).toBeInTheDocument()
    })
  })

  it('renders the node type legend at the bottom', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      // "position" appears in node type badges and legend; use getAllByText
      const positionElements = screen.getAllByText('position')
      expect(positionElements.length).toBeGreaterThanOrEqual(1)
    })
    // These types only appear in the legend (no nodes of those types exist)
    expect(screen.getByText('sweep')).toBeInTheDocument()
    expect(screen.getByText('pass')).toBeInTheDocument()
    expect(screen.getByText('escape')).toBeInTheDocument()
    // "technique" and "submission" appear in both node badges and legend
    expect(screen.getAllByText('technique').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('submission').length).toBeGreaterThanOrEqual(1)
  })

  it('shows attempt stats for nodes with attempts', async () => {
    mockGetCurrent.mockResolvedValue({ data: samplePlan })
    renderMyGame()

    await waitFor(() => {
      expect(screen.getByText('7/10')).toBeInTheDocument()
    })
    expect(screen.getByText('2/5')).toBeInTheDocument()
    expect(screen.getByText('5/8')).toBeInTheDocument()
  })
})

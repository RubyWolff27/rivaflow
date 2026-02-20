import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockList = vi.fn()
const mockCreate = vi.fn()
const mockDelete = vi.fn()
const mockUpdate = vi.fn()

vi.mock('../../api/client', () => ({
  trainingGoalsApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    get: vi.fn(),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

vi.mock('../../hooks/usePageTitle', () => ({
  usePageTitle: vi.fn(),
}))

vi.mock('../../utils/logger', () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    debug: vi.fn(),
  },
}))

vi.mock('../../components/goals/MonthSelector', () => ({
  default: ({ onMonthChange }: { onMonthChange?: (m: string) => void }) => (
    <div data-testid="month-selector" onClick={() => onMonthChange?.('2026-03')} />
  ),
}))

vi.mock('../../components/goals/TrainingGoalCard', () => ({
  default: ({ goal }: { goal: { id: number; metric: string; target_value: number } }) => (
    <div data-testid="goal-card">{goal.metric} - {goal.target_value}</div>
  ),
}))

vi.mock('../../components/goals/CreateGoalModal', () => ({
  default: () => null,
}))

vi.mock('../../components/ui', () => ({
  PageHeader: ({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: React.ReactNode }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
      {actions}
    </div>
  ),
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  ),
  EmptyState: ({ title, description }: { title: string; description?: string; icon?: unknown }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      {description && <p>{description}</p>}
    </div>
  ),
}))

import MonthlyGoals from '../MonthlyGoals'

const sampleGoals = [
  {
    id: 1,
    goal_type: 'frequency' as const,
    metric: 'sessions' as const,
    target_value: 3,
    month: '2026-02',
    movement_id: null,
    class_type_filter: null,
    is_active: true,
    actual_value: 1,
    progress_pct: 33,
    completed: false,
  },
  {
    id: 2,
    goal_type: 'frequency' as const,
    metric: 'hours' as const,
    target_value: 10,
    month: '2026-02',
    movement_id: null,
    class_type_filter: null,
    is_active: true,
    actual_value: 6,
    progress_pct: 60,
    completed: false,
  },
]

function renderMonthlyGoals() {
  return render(
    <BrowserRouter>
      <MonthlyGoals />
    </BrowserRouter>
  )
}

describe('MonthlyGoals', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton while fetching goals', () => {
    mockList.mockImplementation(() => new Promise(() => {}))
    renderMonthlyGoals()

    // Loading state renders Card skeleton placeholders with animate-pulse
    const cards = screen.getAllByTestId('card')
    expect(cards.length).toBeGreaterThanOrEqual(1)
  })

  it('renders page header with title', async () => {
    mockList.mockResolvedValue({ data: sampleGoals })
    renderMonthlyGoals()

    await waitFor(() => {
      expect(screen.getByText('Monthly Goals')).toBeInTheDocument()
    })
    expect(screen.getByText('Set and track your training goals')).toBeInTheDocument()
  })

  it('renders month selector', async () => {
    mockList.mockResolvedValue({ data: sampleGoals })
    renderMonthlyGoals()

    await waitFor(() => {
      expect(screen.getByTestId('month-selector')).toBeInTheDocument()
    })
  })

  it('shows goal cards after successful load', async () => {
    mockList.mockResolvedValue({ data: sampleGoals })
    renderMonthlyGoals()

    await waitFor(() => {
      const goalCards = screen.getAllByTestId('goal-card')
      expect(goalCards).toHaveLength(2)
    })

    expect(screen.getByText('sessions - 3')).toBeInTheDocument()
    expect(screen.getByText('hours - 10')).toBeInTheDocument()
  })

  it('shows empty state when no goals exist', async () => {
    mockList.mockResolvedValue({ data: [] })
    renderMonthlyGoals()

    await waitFor(() => {
      expect(screen.getByText('No goals for this month')).toBeInTheDocument()
    })
  })

  it('renders the Add Goal button', async () => {
    mockList.mockResolvedValue({ data: sampleGoals })
    renderMonthlyGoals()

    await waitFor(() => {
      expect(screen.getByText('Add Goal')).toBeInTheDocument()
    })
  })
})

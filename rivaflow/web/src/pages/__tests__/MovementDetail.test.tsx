import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockNavigate = vi.fn()
const mockGetById = vi.fn()
const mockAddCustomVideo = vi.fn()
const mockDeleteCustomVideo = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '1' }),
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../../api/client', () => ({
  glossaryApi: {
    getById: (...args: unknown[]) => mockGetById(...args),
    addCustomVideo: (...args: unknown[]) => mockAddCustomVideo(...args),
    deleteCustomVideo: (...args: unknown[]) => mockDeleteCustomVideo(...args),
    list: vi.fn(),
    getCategories: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
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

vi.mock('../../components/ConfirmDialog', () => ({
  default: () => <div data-testid="confirm-dialog" />,
}))

vi.mock('../../components/ui', () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
}))

import MovementDetail from '../MovementDetail'

const sampleMovement = {
  id: 1,
  name: 'Armbar',
  category: 'submission' as const,
  subcategory: 'armlock',
  points: 0,
  description: 'Classic armbar from guard',
  aliases: ['juji gatame'],
  gi_applicable: true,
  nogi_applicable: true,
  ibjjf_legal_white: true,
  ibjjf_legal_blue: true,
  ibjjf_legal_purple: true,
  ibjjf_legal_brown: true,
  ibjjf_legal_black: true,
  custom: false,
  custom_videos: [],
}

function renderMovementDetail() {
  return render(
    <BrowserRouter>
      <MovementDetail />
    </BrowserRouter>
  )
}

describe('MovementDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeletons while fetching', () => {
    mockGetById.mockImplementation(() => new Promise(() => {}))
    renderMovementDetail()

    const skeletons = screen.getAllByTestId('card-skeleton')
    expect(skeletons.length).toBeGreaterThanOrEqual(1)
  })

  it('shows movement details after successful load', async () => {
    mockGetById.mockResolvedValue({ data: sampleMovement })
    renderMovementDetail()

    await waitFor(() => {
      expect(screen.getByText('Armbar')).toBeInTheDocument()
    })

    expect(screen.getByText('Classic armbar from guard')).toBeInTheDocument()
    expect(screen.getByText('Submission')).toBeInTheDocument()
    expect(screen.getByText('juji gatame')).toBeInTheDocument()
  })

  it('renders back button', async () => {
    mockGetById.mockResolvedValue({ data: sampleMovement })
    renderMovementDetail()

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument()
    })
  })

  it('shows movement not found when API returns error', async () => {
    mockGetById.mockRejectedValue(new Error('Not found'))
    renderMovementDetail()

    await waitFor(() => {
      expect(screen.getByText('Movement not found')).toBeInTheDocument()
    })
  })

  it('renders IBJJF legality information', async () => {
    mockGetById.mockResolvedValue({ data: sampleMovement })
    renderMovementDetail()

    await waitFor(() => {
      expect(screen.getByText('White')).toBeInTheDocument()
    })

    expect(screen.getByText('Blue')).toBeInTheDocument()
    expect(screen.getByText('Purple')).toBeInTheDocument()
    expect(screen.getByText('Brown')).toBeInTheDocument()
    expect(screen.getByText('Black')).toBeInTheDocument()
    // All are legal for this movement
    const legalTexts = screen.getAllByText('Legal')
    expect(legalTexts).toHaveLength(5)
  })

  it('renders custom videos section with add button', async () => {
    mockGetById.mockResolvedValue({ data: sampleMovement })
    renderMovementDetail()

    await waitFor(() => {
      expect(screen.getByText('Your Custom Videos')).toBeInTheDocument()
    })

    expect(screen.getByText('Add Video')).toBeInTheDocument()
  })
})

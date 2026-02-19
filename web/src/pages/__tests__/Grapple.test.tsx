import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetInfo = vi.fn()
const mockGetSessions = vi.fn()
const mockGetSession = vi.fn()
const mockChat = vi.fn()
const mockDeleteSession = vi.fn()
const mockSubmitFeedback = vi.fn()

vi.mock('../../api/client', () => ({
  grappleApi: {
    getInfo: (...args: unknown[]) => mockGetInfo(...args),
    getSessions: (...args: unknown[]) => mockGetSessions(...args),
    getSession: (...args: unknown[]) => mockGetSession(...args),
    deleteSession: (...args: unknown[]) => mockDeleteSession(...args),
    chat: (...args: unknown[]) => mockChat(...args),
    submitFeedback: (...args: unknown[]) => mockSubmitFeedback(...args),
    extractSession: vi.fn(),
    saveExtractedSession: vi.fn(),
    getInsights: vi.fn(),
    generateInsight: vi.fn(),
    createInsightChat: vi.fn(),
    techniqueQA: vi.fn(),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com', first_name: 'Ruby', last_name: 'Test', subscription_tier: 'beta', is_beta_user: true },
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('../../utils/logger', () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    isRecording: false,
    isTranscribing: false,
    hasSpeechApi: false,
    toggleRecording: vi.fn(),
  }),
}))

vi.mock('../../components/ConfirmDialog', () => ({
  default: () => null,
}))

vi.mock('../../components/grapple/SessionExtractionPanel', () => ({
  default: () => <div data-testid="extraction-panel">Extraction Panel</div>,
}))

vi.mock('../../components/grapple/InsightsPanel', () => ({
  default: () => <div data-testid="insights-panel">Insights Panel</div>,
}))

vi.mock('../../components/grapple/TechniqueQAPanel', () => ({
  default: () => <div data-testid="technique-qa-panel">Technique QA Panel</div>,
}))

import Grapple from '../Grapple'

const tierInfoEnabled = {
  tier: 'beta',
  is_beta: true,
  features: { grapple: true },
  limits: { grapple_messages_per_hour: 30 },
}

const tierInfoDisabled = {
  tier: 'free',
  is_beta: false,
  features: { grapple: false },
  limits: { grapple_messages_per_hour: 0 },
}

const sampleSessions = [
  { id: 'sess-1', title: 'Guard passing tips', message_count: 5, updated_at: '2026-02-18T10:00:00Z' },
  { id: 'sess-2', title: 'Takedown drill', message_count: 3, updated_at: '2026-02-17T10:00:00Z' },
]

function renderGrapple() {
  return render(
    <BrowserRouter>
      <Grapple />
    </BrowserRouter>
  )
}

describe('Grapple', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state while tier info is being fetched', () => {
    mockGetInfo.mockImplementation(() => new Promise(() => {}))
    mockGetSessions.mockImplementation(() => new Promise(() => {}))
    renderGrapple()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders the title and subtitle when grapple is enabled', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('Grapple AI Coach')).toBeInTheDocument()
    })
    expect(screen.getByText('Your BJJ training advisor')).toBeInTheDocument()
  })

  it('shows empty chat state with prompt suggestions', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('Start a conversation')).toBeInTheDocument()
    })
    expect(screen.getByText('What should I focus on this week?')).toBeInTheDocument()
    expect(screen.getByText('How do I improve my guard retention?')).toBeInTheDocument()
  })

  it('renders chat input and send button', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about techniques/i)).toBeInTheDocument()
    })
  })

  it('renders session list in sidebar', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: sampleSessions } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('Guard passing tips')).toBeInTheDocument()
    })
    expect(screen.getByText('Takedown drill')).toBeInTheDocument()
    expect(screen.getByText('5 messages')).toBeInTheDocument()
    expect(screen.getByText('3 messages')).toBeInTheDocument()
  })

  it('shows upgrade prompt when grapple feature is disabled', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoDisabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('Upgrade to Premium to unlock Grapple')).toBeInTheDocument()
    })
    expect(screen.getByText('Voice Logging')).toBeInTheDocument()
    expect(screen.getByText('Technique Q&A')).toBeInTheDocument()
    expect(screen.getByText('AI Coaching')).toBeInTheDocument()
    expect(screen.getByText('Smart Insights')).toBeInTheDocument()
  })

  it('renders quick action panel tabs', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /chat/i })).toBeInTheDocument()
    })
    expect(screen.getByRole('tab', { name: /voice log/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /ask technique/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /insights/i })).toBeInTheDocument()
  })

  it('clicking a prompt suggestion fills the input', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('What should I focus on this week?')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('What should I focus on this week?'))

    const input = screen.getByPlaceholderText(/ask about techniques/i) as HTMLInputElement
    expect(input.value).toBe('What should I focus on this week?')
  })

  it('shows the New button for creating a new chat', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: sampleSessions } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('New')).toBeInTheDocument()
    })
    expect(screen.getByText('Chats')).toBeInTheDocument()
  })

  it('shows beta badge and rate limit info for beta users', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText('BETA')).toBeInTheDocument()
    })
    expect(screen.getByText('30 messages/hour')).toBeInTheDocument()
  })

  it('switches to extraction panel when Voice Log tab is clicked', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoEnabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /voice log/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('tab', { name: /voice log/i }))

    await waitFor(() => {
      expect(screen.getByTestId('extraction-panel')).toBeInTheDocument()
    })
  })

  it('shows current tier in upgrade screen', async () => {
    mockGetInfo.mockResolvedValue({ data: tierInfoDisabled })
    mockGetSessions.mockResolvedValue({ data: { sessions: [] } })
    renderGrapple()

    await waitFor(() => {
      expect(screen.getByText(/current tier: free/i)).toBeInTheDocument()
    })
  })
})

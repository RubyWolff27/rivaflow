import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetByDate = vi.fn()

vi.mock('../../api/client', () => ({
  sessionsApi: {
    getAutocomplete: vi.fn(() =>
      Promise.resolve({
        data: { gyms: ['Test Gym'], locations: ['Test City'], partners: [], techniques: [] },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 1 } })),
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  readinessApi: {
    create: vi.fn(() => Promise.resolve({ data: { id: 1 } })),
    getByDate: (...args: unknown[]) => mockGetByDate(...args),
  },
  profileApi: {
    get: vi.fn(() =>
      Promise.resolve({
        data: {
          default_gym: 'Test Gym',
          default_location: 'Test City',
          primary_training_type: 'gi',
        },
      })
    ),
  },
  friendsApi: {
    listInstructors: vi.fn(() => Promise.resolve({ data: [] })),
    listPartners: vi.fn(() => Promise.resolve({ data: [] })),
  },
  socialApi: {
    getFriends: vi.fn(() => Promise.resolve({ data: { friends: [] } })),
  },
  glossaryApi: {
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  restApi: {
    logRestDay: vi.fn(() => Promise.resolve({ data: {} })),
  },
  whoopApi: {
    getStatus: vi.fn(() => Promise.resolve({ data: { connected: false } })),
    getWorkouts: vi.fn(() => Promise.resolve({ data: { workouts: [], count: 0 } })),
    getZonesBatch: vi.fn(() => Promise.resolve({ data: { zones: {} } })),
  },
  getErrorMessage: vi.fn((e: unknown) => String(e)),
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

vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    isRecording: false,
    isTranscribing: false,
    toggleRecording: vi.fn(),
    hasSpeechApi: false,
  }),
}))

vi.mock('../../components/WhoopMatchModal', () => ({
  default: () => null,
}))

vi.mock('../../components/GymSelector', () => ({
  default: ({ value }: { value: string }) => (
    <input data-testid="gym-selector" defaultValue={value} />
  ),
}))

vi.mock('../../components/ui', () => ({
  ClassTypeChips: ({ onChange }: { value: string; onChange: (v: string) => void }) => (
    <div data-testid="class-type-chips">
      <button onClick={() => onChange('gi')}>Gi</button>
      <button onClick={() => onChange('no-gi')}>No-Gi</button>
    </div>
  ),
  IntensityChips: ({ onChange }: { value: number; onChange: (v: number) => void }) => (
    <div data-testid="intensity-chips">
      {[1, 2, 3, 4, 5].map((i) => (
        <button key={i} onClick={() => onChange(i)}>
          {i}
        </button>
      ))}
    </div>
  ),
}))

vi.mock('../../components/sessions/ReadinessStep', () => ({
  default: ({ onNext, onSkip }: { onNext: () => void; onSkip: () => void }) => (
    <div data-testid="readiness-step">
      <p>Sleep</p>
      <p>Stress</p>
      <p>Soreness</p>
      <p>Energy</p>
      <button data-testid="readiness-next" onClick={onNext}>
        Next
      </button>
      <button data-testid="readiness-skip" onClick={onSkip}>
        Skip
      </button>
    </div>
  ),
}))

vi.mock('../../components/sessions/TechniqueTracker', () => ({
  default: () => <div data-testid="technique-tracker" />,
}))

vi.mock('../../components/sessions/RollTracker', () => ({
  default: () => <div data-testid="roll-tracker" />,
}))

vi.mock('../../components/sessions/ClassTimePicker', () => ({
  default: () => <div data-testid="class-time-picker" />,
}))

vi.mock('../../components/sessions/WhoopIntegrationPanel', () => ({
  default: () => <div data-testid="whoop-panel" />,
}))

vi.mock('../../components/sessions/FightDynamicsPanel', () => ({
  default: () => <div data-testid="fight-dynamics" />,
}))

import LogSession from '../LogSession'

function renderLogSession() {
  return render(
    <BrowserRouter>
      <LogSession />
    </BrowserRouter>
  )
}

describe('LogSession', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: no readiness logged today
    mockGetByDate.mockRejectedValue(new Error('Not found'))
  })

  it('renders without crashing', async () => {
    renderLogSession()
    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })
  })

  it('renders activity type selector', async () => {
    renderLogSession()
    await waitFor(() => {
      expect(screen.getByText(/training session/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/rest day/i)).toBeInTheDocument()
  })

  it('starts on readiness step', async () => {
    renderLogSession()
    await waitFor(() => {
      expect(screen.getByText(/sleep/i)).toBeInTheDocument()
      expect(screen.getByText(/stress/i)).toBeInTheDocument()
      expect(screen.getByText(/soreness/i)).toBeInTheDocument()
      expect(screen.getByText(/energy/i)).toBeInTheDocument()
    })
  })

  it('loads autocomplete data', async () => {
    const { sessionsApi } = await import('../../api/client')
    renderLogSession()
    await waitFor(() => {
      expect(sessionsApi.getAutocomplete).toHaveBeenCalled()
    })
  })

  it('loads profile defaults', async () => {
    const { profileApi } = await import('../../api/client')
    renderLogSession()
    await waitFor(() => {
      expect(profileApi.get).toHaveBeenCalled()
    })
  })

  // --- New interaction tests ---

  it('toggles from Training to Rest Day and shows rest form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })

    // Click Rest Day button
    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Log Rest Day' })).toBeInTheDocument()
    })

    // Rest day form should show rest type options
    expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    expect(screen.getByText(/full rest/i)).toBeInTheDocument()
  })

  it('toggles from Rest Day back to Training and shows readiness', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })

    // Switch to rest, then back to training
    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Log Rest Day' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/training session/i))

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })
  })

  it('advances to step 2 when clicking Next on readiness step', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })
  })

  it('advances to step 2 when clicking Skip on readiness step', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-skip'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })
  })

  it('shows duration chip buttons on step 2', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })

    // Check for standard duration chips
    expect(screen.getByText('60m')).toBeInTheDocument()
    expect(screen.getByText('75m')).toBeInTheDocument()
    expect(screen.getByText('90m')).toBeInTheDocument()
    expect(screen.getByText('120m')).toBeInTheDocument()
    expect(screen.getByText('Custom')).toBeInTheDocument()
  })

  it('duration chip selection updates selected state', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })

    // Click 90m chip
    const chip90 = screen.getByLabelText('90 minutes')
    fireEvent.click(chip90)

    // Verify the button is now pressed
    expect(chip90).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows Custom duration input when Custom chip is clicked', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Custom'))

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter duration/i)).toBeInTheDocument()
    })
  })

  it('skips readiness step automatically when readiness already logged today', async () => {
    // Mock that readiness was already logged today
    mockGetByDate.mockResolvedValueOnce({
      data: {
        sleep: 4,
        stress: 2,
        soreness: 3,
        energy: 4,
        hotspot_note: '',
        weight_kg: 80,
      },
    })

    renderLogSession()

    // Should skip directly to step 2
    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })

    // Should show auto-skip note
    expect(screen.getByText('Readiness already logged today')).toBeInTheDocument()
  })

  it('shows Back button on step 2 that navigates to step 1', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Training Session')).toBeInTheDocument()
    })

    // Click Back
    fireEvent.click(screen.getByText('Back'))

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })
  })

  it('shows rest type options when in rest mode', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Log Rest Day' })).toBeInTheDocument()
    })

    // Verify all rest type buttons
    expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    expect(screen.getByText(/full rest/i)).toBeInTheDocument()
    expect(screen.getByText(/injury/i)).toBeInTheDocument()
    expect(screen.getByText(/sick day/i)).toBeInTheDocument()
    expect(screen.getByText(/travelling/i)).toBeInTheDocument()
    expect(screen.getByText(/life got in the way/i)).toBeInTheDocument()
  })

  it('clicking rest type toggles aria-pressed', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Log Rest Day' })).toBeInTheDocument()
    })

    const fullRestBtn = screen.getByText('Full Rest')
    fireEvent.click(fullRestBtn)
    expect(fullRestBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows class type chips on step 2', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByTestId('class-type-chips')).toBeInTheDocument()
    })
  })

  it('shows intensity chips on step 2', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByTestId('intensity-chips')).toBeInTheDocument()
    })
  })

  it('shows the Log Session submit button on step 2', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('readiness-step')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('readiness-next'))

    await waitFor(() => {
      expect(screen.getByText('Log Session')).toBeInTheDocument()
    })
  })

  it('shows Log Rest Day button when in rest mode', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('How Are You Feeling?')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText('Log Rest Day', { selector: 'button' })).toBeInTheDocument()
    })
  })

  it('shows progress indicator with step numbers for training', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('Readiness Check')).toBeInTheDocument()
      expect(screen.getByText('Session Details')).toBeInTheDocument()
    })
  })
})

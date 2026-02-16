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

vi.mock('../../components/sessions/CompactReadiness', () => ({
  default: ({ alreadyLogged, compositeScore, onSkip }: { alreadyLogged: boolean; compositeScore: number; onSkip: () => void }) => (
    <div data-testid="compact-readiness">
      {alreadyLogged ? (
        <span data-testid="readiness-badge">Readiness: {compositeScore}/20</span>
      ) : (
        <>
          <p>Sleep</p>
          <p>Stress</p>
          <p>Soreness</p>
          <p>Energy</p>
          <button data-testid="readiness-skip" onClick={onSkip}>
            Skip
          </button>
        </>
      )}
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
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })
  })

  it('renders activity type selector', async () => {
    renderLogSession()
    await waitFor(() => {
      expect(screen.getByText(/training session/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/rest day/i)).toBeInTheDocument()
  })

  it('shows readiness sliders inline on the form', async () => {
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

  it('toggles from Training to Rest Day and shows rest form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/full rest/i)).toBeInTheDocument()
  })

  it('toggles from Rest Day back to Training and shows form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/training session/i))

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })
  })

  it('shows duration chip buttons on the form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('60m')).toBeInTheDocument()
    })
    expect(screen.getByText('75m')).toBeInTheDocument()
    expect(screen.getByText('90m')).toBeInTheDocument()
    expect(screen.getByText('120m')).toBeInTheDocument()
    expect(screen.getByText('Custom')).toBeInTheDocument()
  })

  it('duration chip selection updates selected state', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('60m')).toBeInTheDocument()
    })

    const chip90 = screen.getByLabelText('90 minutes')
    fireEvent.click(chip90)

    expect(chip90).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows Custom duration input when Custom chip is clicked', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Custom'))

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter duration/i)).toBeInTheDocument()
    })
  })

  it('shows readiness badge when readiness already logged today', async () => {
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

    await waitFor(() => {
      expect(screen.getByTestId('readiness-badge')).toBeInTheDocument()
    })
  })

  it('shows rest type options when in rest mode', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/full rest/i)).toBeInTheDocument()
    expect(screen.getByText(/injury/i)).toBeInTheDocument()
    expect(screen.getByText(/sick day/i)).toBeInTheDocument()
    expect(screen.getByText(/travelling/i)).toBeInTheDocument()
    expect(screen.getByText(/life got in the way/i)).toBeInTheDocument()
  })

  it('clicking rest type toggles aria-pressed', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText(/active recovery/i)).toBeInTheDocument()
    })

    const fullRestBtn = screen.getByText(/full rest/i)
    fireEvent.click(fullRestBtn)
    expect(fullRestBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows class type chips on the form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('class-type-chips')).toBeInTheDocument()
    })
  })

  it('shows intensity chips on the form', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('intensity-chips')).toBeInTheDocument()
    })
  })

  it('shows the Log Session submit button', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByText('Log Session')).toBeInTheDocument()
    })
  })

  it('shows Log Rest Day button when in rest mode', async () => {
    renderLogSession()

    await waitFor(() => {
      expect(screen.getByTestId('compact-readiness')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/rest day/i))

    await waitFor(() => {
      expect(screen.getByText('Log Rest Day', { selector: 'button' })).toBeInTheDocument()
    })
  })
})

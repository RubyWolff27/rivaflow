import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

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
    listInstructors: vi.fn(() => Promise.resolve({ data: { friends: [] } })),
    listPartners: vi.fn(() => Promise.resolve({ data: { friends: [] } })),
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

vi.mock('../../hooks/useInsightRefresh', () => ({
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
      expect(screen.getByText(/training/i)).toBeInTheDocument()
    })
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
})

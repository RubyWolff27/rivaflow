import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  profileApi: {
    get: vi.fn(() =>
      Promise.resolve({
        data: {
          first_name: 'Test',
          last_name: 'User',
          date_of_birth: '1990-01-01',
          default_gym: 'Test Gym',
          default_location: 'Test City',
          current_professor: 'Coach',
          primary_training_type: 'gi',
          weekly_sessions_target: 3,
          weekly_hours_target: 4.5,
          weekly_rolls_target: 15,
          avatar_url: '',
        },
      })
    ),
    update: vi.fn(() => Promise.resolve({ data: {} })),
    uploadPhoto: vi.fn(),
    deletePhoto: vi.fn(),
  },
  gradingsApi: {
    list: vi.fn(() => Promise.resolve({ data: [] })),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    uploadPhoto: vi.fn(),
  },
  friendsApi: {
    listInstructors: vi.fn(() => Promise.resolve({ data: [] })),
  },
  gymsApi: {
    search: vi.fn(() => Promise.resolve({ data: [] })),
  },
  adminApi: {
    createGym: vi.fn(),
  },
  whoopApi: {
    getStatus: vi.fn(() => Promise.resolve({ data: null })),
    checkScopes: vi.fn(() => Promise.resolve({ data: { needs_reauth: false } })),
    getAuthorizeUrl: vi.fn(),
    sync: vi.fn(),
    disconnect: vi.fn(),
    setAutoCreate: vi.fn(),
    setAutoFillReadiness: vi.fn(),
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

vi.mock('../../hooks/useTier', () => ({
  useTier: () => ({
    tier: 'beta',
    isFree: false,
    isBeta: true,
    isPro: false,
    label: 'Beta',
  }),
}))

vi.mock('../../components/GymSelector', () => ({
  default: ({ value }: { value: string }) => (
    <input data-testid="gym-selector" defaultValue={value} />
  ),
}))

vi.mock('../../components/ConfirmDialog', () => ({
  default: () => null,
}))

vi.mock('../../components/ui', () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
}))

import Profile from '../Profile'

function renderProfile() {
  return render(
    <BrowserRouter>
      <Profile />
    </BrowserRouter>
  )
}

describe('Profile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    renderProfile()
    await waitFor(() => {
      expect(screen.getAllByText(/profile/i).length).toBeGreaterThan(0)
    })
  })

  it('renders profile form fields after loading', async () => {
    renderProfile()
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test')).toBeInTheDocument()
      expect(screen.getByDisplayValue('User')).toBeInTheDocument()
    })
  })

  it('renders weekly goals section', async () => {
    renderProfile()
    await waitFor(() => {
      expect(screen.getByText('Weekly Goals')).toBeInTheDocument()
    })
  })

  it('loads existing profile data', async () => {
    const { profileApi } = await import('../../api/client')
    renderProfile()
    await waitFor(() => {
      expect(profileApi.get).toHaveBeenCalled()
    })
  })

  it('loads gradings list', async () => {
    const { gradingsApi } = await import('../../api/client')
    renderProfile()
    await waitFor(() => {
      expect(gradingsApi.list).toHaveBeenCalled()
    })
  })
})

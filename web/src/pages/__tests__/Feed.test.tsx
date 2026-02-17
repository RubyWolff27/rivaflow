import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  feedApi: {
    getActivity: vi.fn(() =>
      Promise.resolve({
        data: {
          items: [
            {
              id: 1,
              type: 'session',
              date: '2025-01-15',
              summary: 'Gi session at Test Gym (60 min)',
              data: {
                class_type: 'gi',
                gym_name: 'Test Gym',
                duration_mins: 60,
                intensity: 4,
              },
              likes_count: 2,
              comments_count: 1,
              user_liked: false,
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
          has_more: false,
        },
      })
    ),
    getFriends: vi.fn(() =>
      Promise.resolve({
        data: { items: [], total: 0, limit: 20, offset: 0, has_more: false },
      })
    ),
  },
  socialApi: {
    like: vi.fn(() => Promise.resolve({ data: { success: true } })),
    unlike: vi.fn(() => Promise.resolve({ data: {} })),
  },
  sessionsApi: {
    update: vi.fn(() => Promise.resolve({ data: {} })),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com', subscription_tier: 'beta', is_beta_user: true },
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('../../components/FeedToggle', () => ({
  default: ({ onChange }: { view: string; onChange: (v: string) => void }) => (
    <div data-testid="feed-toggle">
      <button onClick={() => onChange('my')}>My Feed</button>
      <button onClick={() => onChange('friends')}>Friends</button>
    </div>
  ),
}))

vi.mock('../../components/ActivitySocialActions', () => ({
  default: () => <div data-testid="social-actions" />,
}))

vi.mock('../../components/CommentSection', () => ({
  default: () => <div data-testid="comment-section" />,
}))

vi.mock('../../components/ui', () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
}))

import Feed from '../Feed'

function renderFeed() {
  return render(
    <BrowserRouter>
      <Feed />
    </BrowserRouter>
  )
}

describe('Feed', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    renderFeed()
    await waitFor(() => {
      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })
  })

  it('fetches activity feed on mount', async () => {
    const { feedApi } = await import('../../api/client')
    renderFeed()
    await waitFor(() => {
      expect(feedApi.getActivity).toHaveBeenCalled()
    })
  })

  it('renders feed items', async () => {
    renderFeed()
    await waitFor(() => {
      expect(screen.getByText(/Gi session at Test Gym/)).toBeInTheDocument()
    })
  })

  it('renders feed toggle', async () => {
    renderFeed()
    await waitFor(() => {
      expect(screen.getByTestId('feed-toggle')).toBeInTheDocument()
    })
  })

  it('shows empty state when no items', async () => {
    const { feedApi } = await import('../../api/client')
    vi.mocked(feedApi.getActivity).mockResolvedValueOnce({
      data: { items: [], total: 0, limit: 20, offset: 0, has_more: false },
    } as any)
    renderFeed()
    await waitFor(() => {
      expect(screen.getByText(/no activity/i)).toBeInTheDocument()
    })
  })
})

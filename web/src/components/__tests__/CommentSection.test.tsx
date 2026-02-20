import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  socialApi: {
    getComments: vi.fn(),
    addComment: vi.fn(),
    deleteComment: vi.fn(),
    updateComment: vi.fn(),
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

vi.mock('../../utils/logger', () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('../ConfirmDialog', () => ({
  default: () => null,
}))

import CommentSection from '../CommentSection'
import { socialApi } from '../../api/client'

const mockGetComments = socialApi.getComments as ReturnType<typeof vi.fn>

const defaultProps = {
  activityType: 'session' as const,
  activityId: 1,
  currentUserId: 1,
  isOpen: true,
}

describe('CommentSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not load comments when isOpen is false', () => {
    render(<CommentSection {...defaultProps} isOpen={false} />)
    expect(mockGetComments).not.toHaveBeenCalled()
    expect(screen.queryByText(/Comments/)).not.toBeInTheDocument()
  })

  it('shows loading state while fetching comments', () => {
    mockGetComments.mockReturnValue(new Promise(() => {}))
    render(<CommentSection {...defaultProps} />)
    expect(screen.getByText('Loading comments...')).toBeInTheDocument()
  })

  it('loads and renders comments when isOpen is true', async () => {
    mockGetComments.mockResolvedValue({
      data: {
        comments: [
          {
            id: 1,
            user_id: 1,
            activity_type: 'session',
            activity_id: 1,
            comment_text: 'Great session!',
            created_at: '2026-01-15T10:00:00Z',
            first_name: 'Test',
            last_name: 'User',
          },
        ],
      },
    })

    render(<CommentSection {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Great session!')).toBeInTheDocument()
    })
    expect(screen.getByText(/Test User/)).toBeInTheDocument()
    expect(screen.getByText('Comments (1)')).toBeInTheDocument()
  })

  it('shows empty state when no comments exist', async () => {
    mockGetComments.mockResolvedValue({ data: { comments: [] } })

    render(<CommentSection {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText(/No comments yet/)).toBeInTheDocument()
    })
  })

  it('shows input for new comment', async () => {
    mockGetComments.mockResolvedValue({ data: { comments: [] } })

    render(<CommentSection {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Add a comment...')).toBeInTheDocument()
    })
  })
})

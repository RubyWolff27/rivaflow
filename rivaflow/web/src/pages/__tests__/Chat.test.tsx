import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../api/client', () => ({
  chatApi: {
    send: vi.fn(),
  },
  getErrorMessage: (err: unknown) =>
    err instanceof Error ? err.message : 'Unknown error',
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, first_name: 'Test' },
    isLoading: false,
  }),
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

vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    isRecording: false,
    isTranscribing: false,
    hasSpeechApi: true,
    toggleRecording: vi.fn(),
  }),
}))

vi.mock('../../utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), debug: vi.fn() },
}))

import Chat from '../Chat'
import { chatApi } from '../../api/client'

function renderChat() {
  return render(
    <BrowserRouter>
      <Chat />
    </BrowserRouter>
  )
}

describe('Chat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders chat title', () => {
    renderChat()
    expect(screen.getByText('Chat')).toBeInTheDocument()
  })

  it('shows empty state message', () => {
    renderChat()
    expect(
      screen.getByText('Ask me anything about your training!')
    ).toBeInTheDocument()
  })

  it('sends a message and displays reply', async () => {
    vi.mocked(chatApi.send).mockResolvedValueOnce({
      data: { reply: 'Great question about training!' },
    } as any)
    renderChat()

    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'How do I improve?' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(chatApi.send).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(
        screen.getByText('Great question about training!')
      ).toBeInTheDocument()
    })
  })

  it('shows loading state while waiting for response', async () => {
    vi.mocked(chatApi.send).mockImplementation(() => new Promise(() => {}))
    renderChat()

    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText('Thinking...')).toBeInTheDocument()
    })
  })

  it('shows error message on API failure', async () => {
    vi.mocked(chatApi.send).mockRejectedValueOnce(new Error('Server error'))
    renderChat()

    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText(/Error: Server error/)).toBeInTheDocument()
    })
  })

  it('renders voice input button', () => {
    renderChat()
    expect(
      screen.getByRole('button', { name: /voice input/i })
    ).toBeInTheDocument()
  })
})

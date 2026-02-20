import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockToastError } = vi.hoisted(() => ({
  mockToastError: vi.fn(),
}))

vi.mock('../../api/client', () => ({
  photosApi: {
    upload: vi.fn().mockResolvedValue({ data: {} }),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: mockToastError,
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

vi.mock('../../utils/imageCompression', () => ({
  compressImage: vi.fn().mockResolvedValue(
    new File(['test'], 'test.jpg', { type: 'image/jpeg' })
  ),
}))

import PhotoUpload from '../PhotoUpload'

const defaultProps = {
  activityType: 'session' as const,
  activityId: 1,
  activityDate: '2026-01-15',
  currentPhotoCount: 3,
  onUploadSuccess: vi.fn(),
}

describe('PhotoUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area when under photo limit', () => {
    render(<PhotoUpload {...defaultProps} />)
    expect(screen.getByText(/Click to upload/)).toBeInTheDocument()
    expect(screen.getByText(/drag and drop/)).toBeInTheDocument()
  })

  it('shows max photos message when at limit', () => {
    render(<PhotoUpload {...defaultProps} currentPhotoCount={10} />)
    expect(screen.getByText(/Maximum 10 photos reached/)).toBeInTheDocument()
    expect(screen.queryByText(/Click to upload/)).not.toBeInTheDocument()
  })

  it('shows photo count text', () => {
    render(<PhotoUpload {...defaultProps} currentPhotoCount={3} />)
    expect(screen.getByText('3/10 photos uploaded')).toBeInTheDocument()
  })

  it('validates file type on selection', () => {
    render(<PhotoUpload {...defaultProps} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    expect(input).toBeTruthy()

    const invalidFile = new File(['content'], 'doc.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [invalidFile] } })

    expect(mockToastError).toHaveBeenCalledWith(
      'Invalid file type. Please upload a JPG, PNG, GIF, or WebP image.'
    )
  })

  it('shows accepted file types info', () => {
    render(<PhotoUpload {...defaultProps} />)
    expect(screen.getByText(/JPG, PNG, GIF, WebP/)).toBeInTheDocument()
  })
})

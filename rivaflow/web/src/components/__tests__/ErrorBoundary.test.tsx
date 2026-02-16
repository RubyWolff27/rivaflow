import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../utils/logger', () => ({
  logger: {
    error: vi.fn(),
    log: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
  },
}))

import { ErrorBoundary } from '../ErrorBoundary'

// A component that throws on render
function ThrowingChild({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test render error')
  }
  return <div data-testid="child-content">Child rendered successfully</div>
}


describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Suppress console.error from React's error boundary logging
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('renders children normally when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div data-testid="normal-child">Hello</div>
      </ErrorBoundary>
    )

    expect(screen.getByTestId('normal-child')).toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders multiple children without errors', () => {
    render(
      <ErrorBoundary>
        <p>First child</p>
        <p>Second child</p>
      </ErrorBoundary>
    )

    expect(screen.getByText('First child')).toBeInTheDocument()
    expect(screen.getByText('Second child')).toBeInTheDocument()
  })

  it('shows error UI when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.queryByTestId('child-content')).not.toBeInTheDocument()
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
  })

  it('shows "Try Again" button in default full-page fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows "Go to Dashboard" button in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument()
  })

  it('shows compact variant when compact prop is true', () => {
    render(
      <ErrorBoundary compact>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong.')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
    // Compact variant should NOT have the Go to Dashboard button
    expect(screen.queryByText('Go to Dashboard')).not.toBeInTheDocument()
  })

  it('"Try Again" button resets error state in default fallback', () => {
    // Use a stateful wrapper to control whether child throws
    let shouldThrow = true
    function MaybeThrow() {
      if (shouldThrow) throw new Error('Test error')
      return <div data-testid="child-ok">Recovered</div>
    }

    render(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>
    )

    // Error UI should be showing
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()

    // Stop throwing before resetting
    shouldThrow = false

    // Click "Try Again" to reset error boundary
    fireEvent.click(screen.getByText('Try Again'))

    // After reset, child renders without error
    expect(screen.getByTestId('child-ok')).toBeInTheDocument()
    expect(screen.getByText('Recovered')).toBeInTheDocument()
  })

  it('"Try again" button resets error state in compact variant', () => {
    let shouldThrow = true
    function MaybeThrow() {
      if (shouldThrow) throw new Error('Test error')
      return <div data-testid="child-ok">Recovered</div>
    }

    render(
      <ErrorBoundary compact>
        <MaybeThrow />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong.')).toBeInTheDocument()

    shouldThrow = false
    fireEvent.click(screen.getByText('Try again'))

    expect(screen.getByTestId('child-ok')).toBeInTheDocument()
  })

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div data-testid="custom-fallback">Custom Error Page</div>}>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
    expect(screen.getByText('Custom Error Page')).toBeInTheDocument()
    // Should NOT show the default error UI
    expect(screen.queryByText('Try Again')).not.toBeInTheDocument()
  })

  it('logs error via logger when error is caught', async () => {
    const { logger } = await import('../../utils/logger')

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(logger.error).toHaveBeenCalledWith(
      'ErrorBoundary caught an error:',
      expect.any(Error),
      expect.objectContaining({ componentStack: expect.any(String) })
    )
  })

  it('shows report issue link in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    )

    expect(screen.getByText(/report the issue/i)).toBeInTheDocument()
  })
})

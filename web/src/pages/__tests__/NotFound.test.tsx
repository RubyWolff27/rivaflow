import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('../../hooks/usePageTitle', () => ({ usePageTitle: vi.fn() }))

import NotFound from '../NotFound'

function renderNotFound() {
  return render(
    <BrowserRouter>
      <NotFound />
    </BrowserRouter>
  )
}

describe('NotFound', () => {
  it('renders 404 heading', () => {
    renderNotFound()
    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('renders Page Not Found message', () => {
    renderNotFound()
    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })

  it('renders description text', () => {
    renderNotFound()
    expect(
      screen.getByText(/doesn't exist or has been moved/)
    ).toBeInTheDocument()
  })

  it('has a link back to dashboard', () => {
    renderNotFound()
    const link = screen.getByText('Back to Dashboard')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })
})

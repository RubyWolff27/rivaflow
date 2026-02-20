import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('../../hooks/usePageTitle', () => ({ usePageTitle: vi.fn() }))

vi.mock('../../components/ui', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
    </div>
  ),
}))

import FAQ from '../FAQ'

function renderFAQ() {
  return render(
    <BrowserRouter>
      <FAQ />
    </BrowserRouter>
  )
}

describe('FAQ', () => {
  it('renders FAQ title', () => {
    renderFAQ()
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument()
  })

  it('renders all FAQ categories', () => {
    renderFAQ()
    expect(screen.getByText('Getting Started')).toBeInTheDocument()
    expect(screen.getByText('Training Logging')).toBeInTheDocument()
    expect(screen.getByText('Analytics & Insights')).toBeInTheDocument()
    expect(screen.getByText('Social')).toBeInTheDocument()
    expect(screen.getByText('Grapple AI Coach')).toBeInTheDocument()
    expect(screen.getByText('WHOOP Integration')).toBeInTheDocument()
    expect(screen.getByText('Account')).toBeInTheDocument()
  })

  it('renders the search input', () => {
    renderFAQ()
    expect(screen.getByPlaceholderText('Search FAQs...')).toBeInTheDocument()
  })

  it('search filters questions', () => {
    renderFAQ()
    const input = screen.getByPlaceholderText('Search FAQs...')
    fireEvent.change(input, { target: { value: 'WHOOP' } })

    // WHOOP-related categories should be visible
    expect(screen.getByText('WHOOP Integration')).toBeInTheDocument()

    // Categories with no matching items should be gone
    expect(screen.queryByText('Social')).not.toBeInTheDocument()
  })

  it('accordion expands on click and shows answer', () => {
    renderFAQ()
    const question = screen.getByText('How do I set up my profile?')
    const button = question.closest('button')!
    expect(button).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
    expect(
      screen.getByText(/Go to your Profile page to add your belt rank/)
    ).toBeInTheDocument()
  })

  it('accordion collapses on second click', () => {
    renderFAQ()
    const question = screen.getByText('How do I set up my profile?')
    const button = question.closest('button')!

    // Open
    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')

    // Close
    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(
      screen.queryByText(/Go to your Profile page to add your belt rank/)
    ).not.toBeInTheDocument()
  })

  it('shows empty state when search has no results', () => {
    renderFAQ()
    const input = screen.getByPlaceholderText('Search FAQs...')
    fireEvent.change(input, { target: { value: 'xyznonexistent123' } })

    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    expect(screen.getByText('No Results Found')).toBeInTheDocument()
  })

  it('renders contact support link', () => {
    renderFAQ()
    expect(screen.getByText('Contact Support')).toBeInTheDocument()
  })
})

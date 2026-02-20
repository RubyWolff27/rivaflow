import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('../../hooks/usePageTitle', () => ({ usePageTitle: vi.fn() }))

import Terms from '../Terms'

function renderTerms() {
  return render(
    <BrowserRouter>
      <Terms />
    </BrowserRouter>
  )
}

describe('Terms', () => {
  it('renders Terms & Conditions title', () => {
    renderTerms()
    expect(screen.getByText('Terms & Conditions')).toBeInTheDocument()
  })

  it('renders Acceptance of Terms section', () => {
    renderTerms()
    expect(screen.getByText('1. Acceptance of Terms')).toBeInTheDocument()
  })

  it('renders Description of Service section', () => {
    renderTerms()
    expect(screen.getByText('2. Description of Service')).toBeInTheDocument()
  })

  it('renders User Accounts section', () => {
    renderTerms()
    expect(screen.getByText('3. User Accounts')).toBeInTheDocument()
  })

  it('renders Limitation of Liability section', () => {
    renderTerms()
    expect(screen.getByText('7. Limitation of Liability')).toBeInTheDocument()
  })

  it('renders last updated date', () => {
    renderTerms()
    expect(screen.getByText('Last updated: February 2026')).toBeInTheDocument()
  })

  it('renders contact email', () => {
    renderTerms()
    expect(screen.getByText('support@rivaflow.app')).toBeInTheDocument()
  })

  it('renders all 10 sections', () => {
    renderTerms()
    for (let i = 1; i <= 10; i++) {
      expect(screen.getByText(new RegExp(`^${i}\\.\\s`))).toBeInTheDocument()
    }
  })
})

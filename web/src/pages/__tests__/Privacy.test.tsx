import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('../../hooks/usePageTitle', () => ({ usePageTitle: vi.fn() }))

import Privacy from '../Privacy'

function renderPrivacy() {
  return render(
    <BrowserRouter>
      <Privacy />
    </BrowserRouter>
  )
}

describe('Privacy', () => {
  it('renders Privacy & Data Safety title', () => {
    renderPrivacy()
    expect(screen.getByText('Privacy & Data Safety')).toBeInTheDocument()
  })

  it('renders Information We Collect section', () => {
    renderPrivacy()
    expect(screen.getByText('1. Information We Collect')).toBeInTheDocument()
  })

  it('renders How We Use Your Data section', () => {
    renderPrivacy()
    expect(screen.getByText('2. How We Use Your Data')).toBeInTheDocument()
  })

  it('renders Data Storage & Security section', () => {
    renderPrivacy()
    expect(screen.getByText('3. Data Storage & Security')).toBeInTheDocument()
  })

  it('renders Your Rights section', () => {
    renderPrivacy()
    expect(screen.getByText('5. Your Rights')).toBeInTheDocument()
  })

  it('renders last updated date', () => {
    renderPrivacy()
    expect(screen.getByText('Last updated: February 2026')).toBeInTheDocument()
  })

  it('renders contact emails', () => {
    renderPrivacy()
    expect(screen.getByText('privacy@rivaflow.app')).toBeInTheDocument()
    expect(screen.getByText('support@rivaflow.app')).toBeInTheDocument()
  })

  it('renders all 10 sections', () => {
    renderPrivacy()
    for (let i = 1; i <= 10; i++) {
      expect(screen.getByText(new RegExp(`^${i}\\.\\s`))).toBeInTheDocument()
    }
  })
})

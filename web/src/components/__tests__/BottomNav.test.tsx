import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockLogout = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'test@example.com' },
    isLoading: false,
    logout: mockLogout,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import BottomNav from '../BottomNav'

const navigation = [
  { name: 'Home', href: '/', icon: () => <span>H</span> },
  { name: 'Feed', href: '/feed', icon: () => <span>F</span>, badge: 0 },
]

const moreNavSections = [
  {
    label: 'Training',
    items: [
      { name: 'Techniques', href: '/techniques', icon: () => <span>T</span> },
    ],
  },
]

function renderBottomNav(initialEntries = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <BottomNav
        navigation={navigation}
        moreNavSections={moreNavSections}
        onQuickLog={vi.fn()}
      />
    </MemoryRouter>
  )
}

describe('BottomNav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders 5 bottom nav items', () => {
    renderBottomNav()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Feed')).toBeInTheDocument()
    expect(screen.getByText('Progress')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByLabelText('Quick Log')).toBeInTheDocument()
  })

  it('calls onQuickLog when Log button clicked', () => {
    const onQuickLog = vi.fn()
    render(
      <MemoryRouter>
        <BottomNav
          navigation={navigation}
          moreNavSections={moreNavSections}
          onQuickLog={onQuickLog}
        />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByLabelText('Quick Log'))
    expect(onQuickLog).toHaveBeenCalledTimes(1)
  })

  it('opens You menu sheet when You button clicked', () => {
    renderBottomNav()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('You menu'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Techniques')).toBeInTheDocument()
    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('closes You menu on Escape key', () => {
    renderBottomNav()
    fireEvent.click(screen.getByLabelText('You menu'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('calls logout and navigates to /login when Logout clicked', () => {
    renderBottomNav()
    fireEvent.click(screen.getByLabelText('You menu'))
    fireEvent.click(screen.getByText('Logout'))
    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })
})

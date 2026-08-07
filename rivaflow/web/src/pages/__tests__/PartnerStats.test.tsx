import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockPartnerRelationship = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ partnerId: '7' }),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('../../api/client', () => ({
  analyticsApi: {
    partnerRelationship: (...args: unknown[]) => mockPartnerRelationship(...args),
  },
}));

vi.mock('../../components/ui', () => ({
  CardSkeleton: () => <div data-testid="skeleton" />,
}));

import PartnerStats from '../PartnerStats';

const RELATIONSHIP = {
  partner_id: 7,
  partner_name: 'Alice Smith',
  belt_rank: 'blue',
  total_rolls: 24,
  total_minutes: 132,
  submissions_for: 9,
  submissions_against: 4,
  total_sessions_together: 12,
  first_roll_date: '2026-01-01',
  last_roll_date: '2026-07-15',
  days_known: 195,
  avg_rolls_per_session: 2.0,
  favorite_techniques_against: ['Armbar', 'Triangle'],
  most_common_positions: [],
};

function renderPage() {
  return render(
    <BrowserRouter>
      <PartnerStats />
    </BrowserRouter>
  );
}

describe('PartnerStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the server contract without NaN or Invalid Date', async () => {
    mockPartnerRelationship.mockResolvedValueOnce({ data: RELATIONSHIP });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });

    expect(screen.getByText('24')).toBeInTheDocument();
    expect(screen.getByText(/Across 12 sessions over 7 months/)).toBeInTheDocument();
    expect(screen.getByText('195 days ago')).toBeInTheDocument();
    expect(screen.getByText('2.0')).toBeInTheDocument();
    expect(screen.getByText('Armbar')).toBeInTheDocument();
    expect(screen.getByText('Triangle')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('NaN');
    expect(document.body.textContent).not.toContain('Invalid Date');
  });

  it('shows an em dash, not Invalid Date, for a partner with no rolls yet', async () => {
    mockPartnerRelationship.mockResolvedValueOnce({
      data: {
        ...RELATIONSHIP,
        total_rolls: 0,
        total_sessions_together: 0,
        first_roll_date: null,
        last_roll_date: null,
        days_known: 0,
        avg_rolls_per_session: 0,
        submissions_for: 0,
        submissions_against: 0,
        favorite_techniques_against: [],
      },
    });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });

    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
    expect(document.body.textContent).not.toContain('Invalid Date');
    expect(document.body.textContent).not.toContain('NaN');
    expect(document.body.textContent).not.toContain('1970');
  });

  it('shows the error state when the request fails', async () => {
    mockPartnerRelationship.mockRejectedValueOnce(new Error('boom'));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Could not load partner stats')).toBeInTheDocument();
    });
  });
});

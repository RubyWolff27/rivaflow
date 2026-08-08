import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import HRSeriesChart from '../HRSeriesChart';

const SERIES = [
  [0, 92],
  [60, 118],
  [120, 141],
  [180, 162],
  [240, 155],
];

describe('HRSeriesChart', () => {
  it('renders the line with an accessible summary', () => {
    render(<HRSeriesChart series={SERIES} avgHr={134} />);

    const svg = screen.getByRole('img');
    expect(svg.getAttribute('aria-label')).toContain('92 bpm at the start');
    expect(svg.getAttribute('aria-label')).toContain('peaking at 162 bpm');
    expect(svg.querySelector('path[stroke="var(--accent)"]')).toBeTruthy();
  });

  it('shows the avg reference line when provided', () => {
    render(<HRSeriesChart series={SERIES} avgHr={134} />);
    expect(screen.getByText('avg 134')).toBeInTheDocument();
  });

  it('labels the peak value', () => {
    render(<HRSeriesChart series={SERIES} avgHr={null} />);
    expect(screen.getByText('162')).toBeInTheDocument();
  });

  it('renders nothing for fewer than 2 points — a line needs a line', () => {
    const { container } = render(<HRSeriesChart series={[[0, 100]]} />);
    expect(container.firstChild).toBeNull();
  });

  it('ignores malformed pairs rather than crashing', () => {
    const dirty = [[0, 92], null, [60], [120, 141]] as unknown as number[][];
    render(<HRSeriesChart series={dirty} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });
});

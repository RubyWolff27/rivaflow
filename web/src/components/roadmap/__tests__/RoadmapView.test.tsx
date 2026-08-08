import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RoadmapView from '../RoadmapView';
import { crossSleeveRoadmap } from '../../../data/roadmaps/crossSleeve';
import type { Roadmap } from '../../../types/roadmap';

const FIXTURE: Roadmap = {
  id: 'test',
  title: 'Test roadmap',
  subtitle: 'sub',
  provenance: 'Your own system — not the AJJ syllabus.',
  root: {
    id: 'root',
    kind: 'choice',
    label: 'Root',
    children: [
      {
        id: 'free',
        kind: 'choice',
        label: 'A thing I choose',
        stage: 'entry',
        cues: ['Cue one', 'Cue two'],
        children: [{ id: 'deep', kind: 'choice', label: 'Deeper', stage: 'sweep' }],
      },
      {
        id: 'react',
        kind: 'reaction',
        label: 'If they post the knee',
        children: [{ id: 'forced', kind: 'choice', label: 'Forced option', stage: 'sweep' }],
      },
    ],
  },
};

describe('RoadmapView', () => {
  it('renders a reaction as a heading, never as a button', () => {
    render(<RoadmapView roadmap={FIXTURE} />);

    const reaction = screen.getByTestId('roadmap-reaction-react');
    expect(reaction).toBeInTheDocument();
    // The whole design rests on this: you cannot tap what your opponent does.
    expect(reaction.querySelector('button')).toBeNull();
    expect(reaction).toHaveTextContent('If they post the knee');
  });

  it('shows the choices a reaction unlocks beneath it', () => {
    render(<RoadmapView roadmap={FIXTURE} />);
    expect(screen.getByTestId('roadmap-choice-forced')).toBeInTheDocument();
  });

  it('drills into a choice and offers the breadcrumb back', () => {
    render(<RoadmapView roadmap={FIXTURE} />);

    fireEvent.click(screen.getByText('A thing I choose'));
    expect(screen.getByTestId('roadmap-choice-deep')).toBeInTheDocument();

    // Breadcrumb carries the committed path and returns you home.
    const crumbs = screen.getByLabelText('Roadmap path');
    expect(crumbs).toHaveTextContent('A thing I choose');
    fireEvent.click(crumbs.querySelectorAll('button')[0]);
    expect(screen.getByTestId('roadmap-choice-free')).toBeInTheDocument();
  });

  it('expands cues inline without navigating away', () => {
    render(<RoadmapView roadmap={FIXTURE} />);

    expect(screen.queryByText('Cue one')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Cues'));
    expect(screen.getByText('Cue one')).toBeInTheDocument();
    // still on the same level
    expect(screen.getByTestId('roadmap-choice-free')).toBeInTheDocument();
  });

  it('says a branch is empty rather than padding it', () => {
    render(<RoadmapView roadmap={FIXTURE} />);
    fireEvent.click(screen.getByText('A thing I choose'));
    fireEvent.click(screen.getByText('Deeper'));
    expect(screen.getByText(/honestly empty rather than padded/)).toBeInTheDocument();
  });
});

describe('cross sleeve roadmap data', () => {
  it('carries no curriculum slot references — it is not syllabus', () => {
    const walk = (n: typeof crossSleeveRoadmap.root): number[] => [
      ...(n.slotId ? [n.slotId] : []),
      ...(n.children ?? []).flatMap(walk),
    ];
    // Coaches sign off the AJJ syllabus. Ruby's own system must never appear
    // as one of their requirements, in any form.
    expect(walk(crossSleeveRoadmap.root)).toEqual([]);
  });

  it('states its provenance so it can never be mistaken for the syllabus', () => {
    expect(crossSleeveRoadmap.provenance).toMatch(/not the AJJ syllabus/i);
  });

  it('only marks a branch as a reaction when it reads as one', () => {
    const reactions: string[] = [];
    const walk = (n: typeof crossSleeveRoadmap.root) => {
      if (n.kind === 'reaction') reactions.push(n.label);
      (n.children ?? []).forEach(walk);
    };
    walk(crossSleeveRoadmap.root);
    expect(reactions.length).toBeGreaterThan(0);
    // The invariant is phrasing-as-a-read: a reaction is something you
    // observe, never something you pick.
    reactions.forEach((label) => expect(label).toMatch(/^If /i));
  });
});

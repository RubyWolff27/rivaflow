import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockSlots = vi.fn()
const mockSummary = vi.fn()
const mockExport = vi.fn()
const mockSeed = vi.fn()
const mockAddEvidence = vi.fn()
const mockAddSignoff = vi.fn()
const mockUpdateSlot = vi.fn()
const mockUpdateMeta = vi.fn()

vi.mock('../../api/client', () => ({
  curriculumApi: {
    slots: (...args: unknown[]) => mockSlots(...args),
    summary: (...args: unknown[]) => mockSummary(...args),
    export: (...args: unknown[]) => mockExport(...args),
    seed: (...args: unknown[]) => mockSeed(...args),
    addEvidence: (...args: unknown[]) => mockAddEvidence(...args),
    addSignoff: (...args: unknown[]) => mockAddSignoff(...args),
    updateSlot: (...args: unknown[]) => mockUpdateSlot(...args),
    updateMeta: (...args: unknown[]) => mockUpdateMeta(...args),
    createSlot: vi.fn(),
  },
  getErrorMessage: (err: unknown) => (err as Error)?.message || 'Unknown error',
}))

vi.mock('../../utils/logger', () => ({
  logger: { debug: vi.fn(), info: vi.fn(), error: vi.fn(), warn: vi.fn() },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ showToast: vi.fn(), success: vi.fn(), error: vi.fn() }),
}))

import Curriculum from '../Curriculum'
import type {
  CurriculumSlot,
  ExportResponse,
  SlotStatus,
  SummaryResponse,
} from '../../types/curriculum'

const ZERO_STATUS: Record<SlotStatus, number> = {
  'not-started': 0,
  drilled: 0,
  grooved: 0,
  live: 0,
  'coach-verified': 0,
}

function slot(over: Partial<CurriculumSlot> & { id: number }): CurriculumSlot {
  return {
    belt: 'purple',
    block: 'guard',
    requirement_key: 'guard-subs',
    requirement_label: 'Submissions of choice',
    slot_index: 1,
    of_choice: true,
    seq_entry: 'Collar drag',
    seq_position: 'Back exposure',
    seq_finish: 'Rear naked choke',
    game_tag: 'a-game',
    movement_ids: null,
    is_draft: false,
    tension_note: null,
    blocker_note: null,
    declared_at: '2026-06-01',
    declared: true,
    status: 'drilled',
    sessions: 1,
    drilled_entries: 1,
    live_occasions: 0,
    live_partners: 0,
    span_days: 0,
    last_evidence_at: '2026-07-01',
    staleness_days: 5,
    weak_evidence: false,
    signoff_verdict: null,
    signoff_count: 0,
    ...over,
  }
}

// One slot per ladder rung, plus the flagged rows the tree has to mark.
const SLOTS: CurriculumSlot[] = [
  slot({ id: 1, status: 'not-started', declared: false, seq_entry: null, seq_position: null, seq_finish: null }),
  slot({ id: 2, status: 'drilled', slot_index: 2 }),
  slot({ id: 3, status: 'grooved', slot_index: 3 }),
  slot({ id: 4, status: 'live', slot_index: 4, weak_evidence: true }),
  slot({ id: 5, status: 'coach-verified', slot_index: 5, signoff_verdict: 'verified', signoff_count: 1 }),
  slot({
    id: 6,
    block: 'guard',
    requirement_key: 'guard-sweeps',
    requirement_label: 'Sweeps → submission',
    status: 'grooved',
    game_tag: 'b-game',
    is_draft: true,
    tension_note: 'Competes with the knee shield entry',
  }),
  slot({
    id: 7,
    block: 'side',
    requirement_key: 'side-passes',
    requirement_label: 'Guard passes → side-control submission',
    status: 'live',
    game_tag: 'a-game',
  }),
  slot({
    id: 8,
    block: 'standup',
    requirement_key: 'td-grappling',
    requirement_label: 'Takedown sequences grappling-only → submission',
    status: 'drilled',
    game_tag: 'a-game',
    staleness_days: 120,
  }),
]

const SUMMARY: SummaryResponse = {
  belt: 'purple',
  hard_gates: [
    { key: 'competition', label: 'Competition experience', type: 'date', value: null, met: false, note: null },
    { key: 'classes', label: 'Classes since blue', type: 'count', value: 18, target: 50, source: 'derived', since: '2026-05-18', met: false, note: 'Counted from your logged sessions — not the Academy\u2019s official record' },
    { key: 'stripes', label: 'Stripes on blue', type: 'count', value: 3, met: null, note: "awarded at the instructor's discretion" },
  ],
  blocks: [
    { block: 'standup', label: 'Stand up', pace_weight: 'early', slot_count: 15, declared: 1, draft: 0, weak_evidence: 0, status_counts: { ...ZERO_STATUS, drilled: 1 }, game_tag_counts: { 'a-game': 1, 'b-game': 0, 'syllabus-only': 0 }, untagged: 0 },
    { block: 'guard', label: 'Guard', pace_weight: null, slot_count: 25, declared: 5, draft: 1, weak_evidence: 1, status_counts: { 'not-started': 1, drilled: 1, grooved: 2, live: 1, 'coach-verified': 1 }, game_tag_counts: { 'a-game': 5, 'b-game': 1, 'syllabus-only': 0 }, untagged: 0 },
    { block: 'side', label: 'Side control', pace_weight: null, slot_count: 20, declared: 1, draft: 0, weak_evidence: 0, status_counts: { ...ZERO_STATUS, live: 1 }, game_tag_counts: { 'a-game': 1, 'b-game': 0, 'syllabus-only': 0 }, untagged: 0 },
    { block: 'mount', label: 'Mount', pace_weight: null, slot_count: 14, declared: 0, draft: 0, weak_evidence: 0, status_counts: { ...ZERO_STATUS }, game_tag_counts: { 'a-game': 0, 'b-game': 0, 'syllabus-only': 0 }, untagged: 0 },
    { block: 'back', label: 'Back', pace_weight: null, slot_count: 16, declared: 0, draft: 0, weak_evidence: 0, status_counts: { ...ZERO_STATUS }, game_tag_counts: { 'a-game': 0, 'b-game': 0, 'syllabus-only': 0 }, untagged: 0 },
  ],
  totals: {
    slot_count: 90,
    declared: 7,
    draft: 1,
    weak_evidence: 1,
    status_counts: { 'not-started': 1, drilled: 2, grooved: 2, live: 2, 'coach-verified': 1 },
    game_tag_counts: { 'a-game': 7, 'b-game': 1, 'syllabus-only': 0 },
    untagged: 0,
  },
}

const EXPORT: ExportResponse = {
  belt: 'purple',
  generated_on: '2026-08-05',
  disclaimer:
    'Promotions are at the instructor’s discretion. This is a training log, not a claim — it has no authority over grading.',
  hard_gates: SUMMARY.hard_gates,
  blocks: [
    {
      block: 'guard',
      label: 'Guard',
      not_yet: [
        {
          id: 1,
          requirement_key: 'guard-subs',
          requirement_label: 'Submissions of choice',
          slot_index: 1,
          sequence: { entry: null, position: null, finish: null },
          status: 'not-started',
          declared: false,
          is_draft: false,
          sessions: 0,
          live_occasions: 0,
          live_partners: 0,
          staleness_days: null,
          weak_evidence: false,
          signoff_verdict: null,
          blocker_note: 'No drilling partner for this one yet',
          tension_note: null,
        },
      ],
      in_progress: [
        {
          id: 2,
          requirement_key: 'guard-subs',
          requirement_label: 'Submissions of choice',
          slot_index: 2,
          sequence: { entry: 'Collar drag', position: 'Back exposure', finish: 'Rear naked choke' },
          status: 'drilled',
          declared: true,
          is_draft: false,
          sessions: 1,
          live_occasions: 0,
          live_partners: 0,
          staleness_days: 5,
          weak_evidence: false,
          signoff_verdict: null,
          blocker_note: null,
          tension_note: null,
        },
      ],
      verified: [
        {
          id: 5,
          requirement_key: 'guard-subs',
          requirement_label: 'Submissions of choice',
          slot_index: 5,
          sequence: { entry: 'Knee shield', position: 'Underhook wrestle-up', finish: 'Guillotine' },
          status: 'coach-verified',
          declared: true,
          is_draft: false,
          sessions: 6,
          live_occasions: 3,
          live_partners: 3,
          staleness_days: 9,
          weak_evidence: false,
          signoff_verdict: 'verified',
          blocker_note: null,
          tension_note: null,
          signoff_coach_name: 'Professor Adam',
          signoff_at: '2026-07-20',
        },
      ],
    },
  ],
}

function setupSeeded() {
  mockSlots.mockResolvedValue({ data: { belt: 'purple', slot_count: SLOTS.length, status_ladder: [], slots: SLOTS } })
  mockSummary.mockResolvedValue({ data: SUMMARY })
  mockExport.mockResolvedValue({ data: EXPORT })
}

function setupEmpty() {
  mockSlots.mockResolvedValue({ data: { belt: 'purple', slot_count: 0, status_ladder: [], slots: [] } })
  mockSummary.mockResolvedValue({ data: { ...SUMMARY, blocks: [], hard_gates: SUMMARY.hard_gates } })
  mockExport.mockResolvedValue({ data: { ...EXPORT, blocks: [] } })
}

function renderPage() {
  return render(
    <BrowserRouter>
      <Curriculum />
    </BrowserRouter>
  )
}

/** The page fetches slots, summary and export before it renders its tabs. */
async function waitForLoad() {
  await waitFor(() => expect(screen.getByRole('tablist')).toBeInTheDocument())
}

async function openSyllabusTab() {
  await waitForLoad()
  fireEvent.click(screen.getByRole('tab', { name: 'Syllabus' }))
  await waitFor(() => expect(screen.getByTestId('syllabus-tree')).toBeInTheDocument())
}

/** Walk into the guard block → "Submissions of choice" requirement. */
async function expandGuardSubs() {
  await openSyllabusTab()
  fireEvent.click(screen.getByText('Guard'))
  await waitFor(() => expect(screen.getAllByText('Submissions of choice').length).toBeGreaterThan(0))
  fireEvent.click(screen.getAllByText('Submissions of choice')[0])
  await waitFor(() => expect(screen.getByTestId('slot-row-2')).toBeInTheDocument())
}

describe('Curriculum page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('opens on the System tab by default', async () => {
    setupSeeded()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('system-grid')).toBeInTheDocument())
    expect(screen.getByRole('tab', { name: 'System' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Syllabus' })).toHaveAttribute('aria-selected', 'false')
  })

  it('counts only declared a/b-game slots at grooved or better in the system grid', async () => {
    setupSeeded()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('system-grid')).toBeInTheDocument())

    // guard-subs → Half guard bottom / Offense: ids 3 (grooved), 4 (live), 5
    // (coach-verified) qualify; 1 (not-started) and 2 (drilled) do not.
    expect(screen.getByTestId('system-cell-Half guard bottom-Offense')).toHaveTextContent('3')
    // guard-sweeps → Half guard bottom / Entries: id 6 only.
    expect(screen.getByTestId('system-cell-Half guard bottom-Entries')).toHaveTextContent('1')
    // side-passes → Pressure pass / Offense: id 7 only.
    expect(screen.getByTestId('system-cell-Pressure pass-Offense')).toHaveTextContent('1')
  })

  it('renders an em dash rather than a zero for empty system cells', async () => {
    setupSeeded()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('system-grid')).toBeInTheDocument())

    // td-grappling maps here but is only drilled, so the count is a real zero.
    const cell = screen.getByTestId('system-cell-Pressure pass-Entries')
    expect(cell).toHaveTextContent('—')
    expect(cell).not.toHaveTextContent('0')
  })

  it('renders the tree from blocks, requirements and slots', async () => {
    setupSeeded()
    renderPage()
    await openSyllabusTab()

    expect(screen.getByText('Guard')).toBeInTheDocument()
    expect(screen.getByText('Side control')).toBeInTheDocument()
    expect(screen.getByText('Stand up')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Guard'))
    await waitFor(() => expect(screen.getAllByText('Submissions of choice').length).toBeGreaterThan(0))
    expect(screen.getByText('Sweeps → submission')).toBeInTheDocument()
  })

  it('renders a distinct chip for each of the five statuses', async () => {
    setupSeeded()
    renderPage()
    await expandGuardSubs()

    const statuses = ['not-started', 'drilled', 'grooved', 'live', 'coach-verified']
    const seen = new Set<string>()
    for (const status of statuses) {
      const chips = screen.getAllByTestId(`status-chip-${status}`)
      expect(chips.length).toBeGreaterThan(0)
      const style = chips[0].getAttribute('style') ?? ''
      expect(seen.has(style)).toBe(false)
      seen.add(style)
    }
  })

  it('treats staleness as dimming only, never as a different status', async () => {
    setupSeeded()
    renderPage()
    await openSyllabusTab()

    // The first block in syllabus order (Stand up) starts expanded.
    fireEvent.click(screen.getAllByText('Takedown sequences grappling-only → submission')[0])

    await waitFor(() => expect(screen.getByTestId('slot-row-8')).toBeInTheDocument())
    const chip = within(screen.getByTestId('slot-row-8')).getByTestId('status-chip-drilled')
    expect(chip).toHaveAttribute('data-status', 'drilled')
    expect(chip).toHaveAttribute('data-stale', 'true')
  })

  it('flags weak evidence, draft rows and tension notes in the tree', async () => {
    setupSeeded()
    renderPage()
    await expandGuardSubs()

    expect(screen.getByTestId('weak-evidence-4')).toHaveAttribute(
      'aria-label',
      'Live evidence only vs smaller/lower-ranked partners'
    )

    fireEvent.click(screen.getAllByText('Sweeps → submission')[0])
    await waitFor(() => expect(screen.getByTestId('slot-row-6')).toBeInTheDocument())
    expect(screen.getByText('draft — review me')).toBeInTheDocument()
    expect(screen.getByTestId('tension-note-6')).toHaveAttribute(
      'aria-label',
      'Tension: Competes with the knee shield entry'
    )
  })

  it('posts drilled evidence with the right payload from the detail sheet', async () => {
    setupSeeded()
    mockAddEvidence.mockResolvedValue({ data: {} })
    renderPage()
    await expandGuardSubs()

    fireEvent.click(screen.getByTestId('slot-row-2'))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Log drilled'))

    await waitFor(() => expect(mockAddEvidence).toHaveBeenCalledWith(2, { kind: 'drilled' }))
  })

  it('posts live evidence with the partner rank band and size', async () => {
    setupSeeded()
    mockAddEvidence.mockResolvedValue({ data: {} })
    renderPage()
    await expandGuardSubs()

    fireEvent.click(screen.getByTestId('slot-row-2'))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Log live'))

    await waitFor(() => expect(screen.getByLabelText('Partner rank band')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Partner rank band'), { target: { value: 'higher' } })
    fireEvent.change(screen.getByLabelText('Partner size'), { target: { value: 'bigger' } })
    fireEvent.click(screen.getByText('Save live evidence'))

    await waitFor(() =>
      expect(mockAddEvidence).toHaveBeenCalledWith(2, {
        kind: 'live',
        partner_rank_band: 'higher',
        partner_size: 'bigger',
      })
    )
  })

  it('puts the edited sequence and game tag back to the API', async () => {
    setupSeeded()
    mockUpdateSlot.mockResolvedValue({ data: {} })
    renderPage()
    await expandGuardSubs()

    fireEvent.click(screen.getByTestId('slot-row-2'))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Edit sequence'))

    await waitFor(() => expect(screen.getByLabelText('Sequence finish')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Sequence finish'), { target: { value: 'Bow and arrow' } })
    fireEvent.change(screen.getByLabelText('Game tag'), { target: { value: 'b-game' } })
    fireEvent.click(screen.getByText('Save sequence'))

    await waitFor(() =>
      expect(mockUpdateSlot).toHaveBeenCalledWith(2, {
        seq_entry: 'Collar drag',
        seq_position: 'Back exposure',
        seq_finish: 'Bow and arrow',
        game_tag: 'b-game',
      })
    )
  })

  it('renders the coach tab gap-first with no percentage anywhere', async () => {
    setupSeeded()
    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByRole('tab', { name: 'Coach view' }))
    await waitFor(() => expect(screen.getByTestId('coach-view')).toBeInTheDocument())

    const text = screen.getByTestId('coach-view').textContent ?? ''
    expect(text.length).toBeGreaterThan(100)
    expect(text).not.toMatch(/%|percent/i)

    const headings = screen.getAllByText(/Not there yet|Working on it|Signed off/)
    expect(headings.map((h) => h.textContent)).toEqual(['Not there yet', 'Working on it', 'Signed off'])
    expect(screen.getByText(/instructor’s discretion/)).toBeInTheDocument()
    expect(screen.getByText(/signed by Professor Adam on 2026-07-20/)).toBeInTheDocument()
  })

  it('posts an attributed coach verdict from the coach tab', async () => {
    setupSeeded()
    mockAddSignoff.mockResolvedValue({ data: {} })
    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByRole('tab', { name: 'Coach view' }))
    await waitFor(() => expect(screen.getByTestId('coach-view')).toBeInTheDocument())

    fireEvent.click(screen.getAllByText('Record coach verdict')[0])
    await waitFor(() => expect(screen.getByLabelText('Coach name')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Verdict'), { target: { value: 'show-me' } })
    fireEvent.change(screen.getByLabelText('Coach name'), { target: { value: 'Professor Adam' } })
    fireEvent.click(screen.getByText('Record verdict'))

    await waitFor(() =>
      expect(mockAddSignoff).toHaveBeenCalledWith(1, {
        verdict: 'show-me',
        coach_name: 'Professor Adam',
        note: null,
      })
    )
  })

  it('draws the radar and adds a pace line once a target date is set', async () => {
    setupSeeded()
    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByRole('tab', { name: 'Radar' }))
    await waitFor(() => expect(screen.getByTestId('curriculum-radar')).toBeInTheDocument())

    expect(screen.queryByTestId('pace-line')).not.toBeInTheDocument()
    expect(screen.getByText(/stored on this device only/)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Target grading date'), { target: { value: '2027-06-01' } })

    await waitFor(() => expect(screen.getByTestId('pace-line')).toBeInTheDocument())
    expect(screen.getByText(/not a promise about grading/)).toBeInTheDocument()
    expect(localStorage.getItem('rivaflow.curriculum.gradingHorizon')).toContain('2027-06-01')
  })

  it('offers a seed button on every tab when nothing is seeded', async () => {
    setupEmpty()
    mockSeed.mockResolvedValue({ data: { seeded: 90, existing: 0, skipped: false } })
    renderPage()

    await waitFor(() => expect(screen.getByTestId('curriculum-empty')).toBeInTheDocument())
    for (const tab of ['Syllabus', 'Radar', 'Coach view']) {
      fireEvent.click(screen.getByRole('tab', { name: tab }))
      expect(screen.getByTestId('curriculum-empty')).toBeInTheDocument()
    }

    fireEvent.click(screen.getByText('Seed my syllabus'))
    await waitFor(() => expect(mockSeed).toHaveBeenCalledWith(false))
  })

  it('seeds from the draft slate when asked', async () => {
    setupEmpty()
    mockSeed.mockResolvedValue({ data: { seeded: 90, existing: 0, skipped: false } })
    renderPage()

    await waitFor(() => expect(screen.getByTestId('curriculum-empty')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Seed with my draft slate'))
    await waitFor(() => expect(mockSeed).toHaveBeenCalledWith(true))
  })

  it('shows the hard gates above the tabs and saves edits through PUT /meta', async () => {
    setupSeeded()
    mockUpdateMeta.mockResolvedValue({ data: SUMMARY.hard_gates })
    renderPage()

    await waitFor(() => expect(screen.getAllByTestId('hard-gates-strip').length).toBeGreaterThan(0))
    // The derived count reads against AJJ's 50-class minimum, not as a bare number.
    expect(screen.getByText('18 / 50')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Edit'))
    await waitFor(() => expect(screen.getByLabelText(/Competition date/)).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText(/Competition date/), { target: { value: '2026-09-12' } })
    fireEvent.click(screen.getByText('Save gates'))

    // classes_logged stays null: opening Edit and saving must NOT freeze the
    // derived count into a manual override. That was the old behaviour and it
    // silently converted an auto-updating gate into a stale typed number.
    await waitFor(() =>
      expect(mockUpdateMeta).toHaveBeenCalledWith({
        competition_date: '2026-09-12',
        blue_promoted_at: '2026-05-18',
        classes_logged: null,
        stripes: 3,
      })
    )
  })
})

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockCreate = vi.fn();
const mockExtract = vi.fn();
const mockSaveExtracted = vi.fn();
const mockCandidates = vi.fn();

vi.mock('../../api/client', () => ({
  sessionsApi: {
    create: (...a: unknown[]) => mockCreate(...a),
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  profileApi: { get: vi.fn(() => Promise.resolve({ data: { default_gym: 'Academy Jiu-Jitsu' } })) },
  restApi: { logRestDay: vi.fn(() => Promise.resolve({ data: {} })) },
  friendsApi: { listPartners: vi.fn(() => Promise.resolve({ data: [] })) },
  socialApi: { getFriends: vi.fn(() => Promise.resolve({ data: { friends: [] } })) },
  grappleApi: {
    extractSession: (...a: unknown[]) => mockExtract(...a),
    saveExtractedSession: (...a: unknown[]) => mockSaveExtracted(...a),
  },
  curriculumApi: {
    evidenceCandidates: (...a: unknown[]) => mockCandidates(...a),
  },
}));

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), showToast: vi.fn() }),
}));

vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    isRecording: false,
    isTranscribing: false,
    hasSpeechApi: false,
    toggleRecording: vi.fn(),
  }),
}));

vi.mock('../../utils/insightRefresh', () => ({
  triggerInsightRefresh: vi.fn(),
}));

import QuickLog from '../QuickLog';

function renderQuickLog() {
  return render(
    <BrowserRouter>
      <QuickLog isOpen={true} onClose={vi.fn()} />
    </BrowserRouter>
  );
}

describe('QuickLog debrief flow (DES-F7)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCandidates.mockResolvedValue({ data: { candidates: [] } });
  });

  it('plain save (no debrief) uses the regular create endpoint', async () => {
    mockCreate.mockResolvedValueOnce({ data: { id: 77 } });
    renderQuickLog();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Academy Jiu-Jitsu')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Log Session'));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
    expect(mockExtract).not.toHaveBeenCalled();
    expect(mockSaveExtracted).not.toHaveBeenCalled();
  });

  it('a debrief routes through extraction, and the confirmed chips win', async () => {
    mockExtract.mockResolvedValueOnce({
      data: {
        class_type: 'no-gi', // extraction says no-gi; the user's chip says gi — chip wins
        rolls: 4,
        techniques: ['armbar'],
        events: [],
        partners: ['Tato'],
      },
    });
    mockSaveExtracted.mockResolvedValueOnce({
      data: { session_id: 88, movements_resolved: ['Armbar'], techniques_unresolved: [] },
    });
    renderQuickLog();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Academy Jiu-Jitsu')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText(/Drilled armbar/), {
      target: { value: 'drilled armbar, four rolls, tapped Tato' },
    });
    fireEvent.click(screen.getByText('Log Session'));

    await waitFor(() => {
      expect(mockSaveExtracted).toHaveBeenCalled();
    });
    const payload = mockSaveExtracted.mock.calls[0][0] as Record<string, unknown>;
    expect(payload.class_type).toBe('gi'); // user chip, not the extraction's no-gi
    expect(payload.rolls).toBe(4); // extraction fills what the user left empty
    expect(payload.techniques).toEqual(['armbar']);
    expect(mockCreate).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByText(/Logged from your debrief: Armbar/)).toBeInTheDocument();
    });
  });

  it('extraction failure falls back to the plain create — debrief text never lost', async () => {
    mockExtract.mockRejectedValueOnce(new Error('llm down'));
    mockCreate.mockResolvedValueOnce({ data: { id: 99 } });
    renderQuickLog();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Academy Jiu-Jitsu')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText(/Drilled armbar/), {
      target: { value: 'good rolls tonight' },
    });
    fireEvent.click(screen.getByText('Log Session'));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
    const payload = mockCreate.mock.calls[0][0] as Record<string, unknown>;
    expect(payload.notes).toBe('good rolls tonight');
  });

  it('post-save surfaces bridge candidates when the session matches slots', async () => {
    mockCreate.mockResolvedValueOnce({ data: { id: 55 } });
    mockCandidates.mockResolvedValueOnce({
      data: { candidates: [{ slot_id: 1 }, { slot_id: 2 }] },
    });
    renderQuickLog();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Academy Jiu-Jitsu')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Log Session'));

    await waitFor(() => {
      expect(screen.getByText(/2 purple-belt matches — review evidence/)).toBeInTheDocument();
    });
  });
});

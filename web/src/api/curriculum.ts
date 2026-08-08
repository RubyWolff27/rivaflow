import { api } from './_client';
import type {
  EvidenceCandidate,
  EvidencePayload,
  ExportResponse,
  HardGate,
  MetaPayload,
  CurriculumSlot,
  SeedResponse,
  SignoffPayload,
  SlotDeclaration,
  SlotStateResponse,
  SlotsResponse,
  SummaryResponse,
} from '../types/curriculum';

/** Everything is belt-scoped; purple is the only seeded syllabus today. */
export const curriculumApi = {
  slots: (belt = 'purple') =>
    api.get<SlotsResponse>('/curriculum/slots', { params: { belt } }),
  summary: (belt = 'purple') =>
    api.get<SummaryResponse>('/curriculum/summary', { params: { belt } }),
  export: (belt = 'purple') =>
    api.get<ExportResponse>('/curriculum/export', { params: { belt } }),
  createSlot: (data: SlotDeclaration & { block: string; requirement_key: string; slot_index: number }) =>
    api.post<CurriculumSlot>('/curriculum/slots', data),
  updateSlot: (slotId: number, data: SlotDeclaration) =>
    api.put<CurriculumSlot>(`/curriculum/slots/${slotId}`, data),
  addEvidence: (slotId: number, data: EvidencePayload) =>
    api.post<SlotStateResponse>(`/curriculum/slots/${slotId}/evidence`, data),
  evidenceCandidates: (sessionId: number) =>
    api.get<{ session_id: number; candidates: EvidenceCandidate[] }>(
      `/curriculum/sessions/${sessionId}/evidence-candidates`
    ),
  addSignoff: (slotId: number, data: SignoffPayload) =>
    api.post<SlotStateResponse>(`/curriculum/slots/${slotId}/signoff`, data),
  updateMeta: (data: MetaPayload, belt = 'purple') =>
    api.put<HardGate[]>('/curriculum/meta', data, { params: { belt } }),
  seed: (withDraft = false, belt = 'purple') =>
    api.post<SeedResponse>('/curriculum/seed', null, {
      params: { with_draft: withDraft, belt },
    }),
};

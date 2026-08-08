import { useCallback, useEffect, useState } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { curriculumApi, getErrorMessage } from '../api/client';
import { useToast } from '../contexts/ToastContext';
import { logger } from '../utils/logger';
import type {
  CurriculumSlot,
  EvidencePayload,
  ExportResponse,
  MetaPayload,
  SignoffPayload,
  SlotDeclaration,
  SummaryResponse,
} from '../types/curriculum';
import HardGatesStrip from '../components/curriculum/HardGatesStrip';
import SystemView from '../components/curriculum/SystemView';
import SyllabusTree from '../components/curriculum/SyllabusTree';
import CurriculumRadar from '../components/curriculum/CurriculumRadar';
import CoachView from '../components/curriculum/CoachView';
import SlotDetailSheet from '../components/curriculum/SlotDetailSheet';
import type { OfficialExample } from '../types/curriculum';

type TabKey = 'system' | 'syllabus' | 'radar' | 'coach';

// System is first and default: the depth question ("do I own a game?") is the
// one purple actually turns on, so it is what the page opens with.
const TABS: { key: TabKey; label: string }[] = [
  { key: 'system', label: 'System' },
  { key: 'syllabus', label: 'Syllabus' },
  { key: 'radar', label: 'Radar' },
  { key: 'coach', label: 'Coach view' },
];

export default function Curriculum() {
  usePageTitle('Purple Belt');
  const toast = useToast();

  const [activeTab, setActiveTab] = useState<TabKey>('system');
  const [slots, setSlots] = useState<CurriculumSlot[]>([]);
  const [officialExamples, setOfficialExamples] = useState<Record<string, OfficialExample[]>>({});
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [exportData, setExportData] = useState<ExportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSlot, setOpenSlot] = useState<CurriculumSlot | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [slotsRes, summaryRes, exportRes] = await Promise.all([
        curriculumApi.slots(),
        curriculumApi.summary(),
        curriculumApi.export(),
      ]);
      setSlots(slotsRes.data?.slots ?? []);
      setOfficialExamples(slotsRes.data?.official_examples ?? {});
      setSummary(summaryRes.data ?? null);
      setExportData(exportRes.data ?? null);
    } catch (err) {
      logger.error('Failed to load curriculum:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Every write recomputes status server-side, so the whole slate is refetched
  // rather than patched locally — a local guess at the next rung would be a
  // second implementation of the status ladder.
  const refresh = useCallback(async () => {
    await load();
  }, [load]);

  const seed = async (withDraft: boolean) => {
    setSeeding(true);
    try {
      await curriculumApi.seed(withDraft);
      await refresh();
      toast.success(withDraft ? 'Syllabus seeded from your draft slate' : 'Syllabus seeded');
    } catch (err) {
      logger.error('Failed to seed curriculum:', err);
      toast.error(getErrorMessage(err));
    } finally {
      setSeeding(false);
    }
  };

  const saveGates = async (payload: MetaPayload) => {
    try {
      await curriculumApi.updateMeta(payload);
      await refresh();
      toast.success('Hard gates updated');
    } catch (err) {
      logger.error('Failed to update hard gates:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const logEvidence = async (slotId: number, payload: EvidencePayload) => {
    try {
      await curriculumApi.addEvidence(slotId, payload);
      await refresh();
      toast.success(payload.kind === 'live' ? 'Live evidence logged' : 'Drilled evidence logged');
      setOpenSlot(null);
    } catch (err) {
      logger.error('Failed to log evidence:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const updateSlot = async (slotId: number, payload: SlotDeclaration) => {
    try {
      await curriculumApi.updateSlot(slotId, payload);
      await refresh();
      toast.success('Sequence updated');
      setOpenSlot(null);
    } catch (err) {
      logger.error('Failed to update slot:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const recordSignoff = async (slotId: number, payload: SignoffPayload) => {
    try {
      await curriculumApi.addSignoff(slotId, payload);
      await refresh();
      toast.success('Coach verdict recorded');
    } catch (err) {
      logger.error('Failed to record sign-off:', err);
      toast.error(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-24 rounded-2xl" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        <div className="animate-pulse h-64 rounded-2xl" style={{ backgroundColor: 'var(--surfaceElev)' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Purple Belt</h1>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>{error}</p>
        <button type="button" className="btn-secondary text-sm" onClick={() => { setLoading(true); load(); }}>
          Try again
        </button>
      </div>
    );
  }

  const seeded = slots.length > 0;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Purple Belt</h1>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Declared sequences, evidence, and the gates that actually decide the belt.
        </p>
      </div>

      {summary && <HardGatesStrip gates={summary.hard_gates} onSave={saveGates} />}

      <div className="flex overflow-x-auto" style={{ borderBottom: '1px solid var(--border)' }} role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors"
            style={{
              color: activeTab === tab.key ? 'var(--text)' : 'var(--muted)',
              borderBottom: activeTab === tab.key ? '2px solid var(--accent)' : '2px solid transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {!seeded ? (
        <div
          className="rounded-2xl p-5 text-center"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
          data-testid="curriculum-empty"
        >
          <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Your syllabus is not set up yet
          </p>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
            The AJJ purple syllabus is about 90 declared sequences — entry, position,
            finish. Seed it and every tab on this page starts working: the system grid,
            the tree, the radar and the coach summary all read the same rows.
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            <button type="button" className="btn-primary text-sm" onClick={() => seed(false)} disabled={seeding}>
              {seeding ? 'Seeding…' : 'Seed my syllabus'}
            </button>
            <button type="button" className="btn-secondary text-sm" onClick={() => seed(true)} disabled={seeding}>
              Seed with my draft slate
            </button>
          </div>
        </div>
      ) : (
        <>
          {activeTab === 'system' && <SystemView slots={slots} />}
          {activeTab === 'syllabus' && (
            <SyllabusTree slots={slots} blocks={summary?.blocks ?? []} onOpenSlot={setOpenSlot} />
          )}
          {activeTab === 'radar' && <CurriculumRadar blocks={summary?.blocks ?? []} />}
          {activeTab === 'coach' && exportData && (
            <CoachView data={exportData} onSaveGates={saveGates} onSignoff={recordSignoff} />
          )}
        </>
      )}

      {openSlot && (
        <SlotDetailSheet
          slot={openSlot}
          officialExamples={officialExamples[openSlot.requirement_key] ?? []}
          onClose={() => setOpenSlot(null)}
          onLogEvidence={logEvidence}
          onUpdateSlot={updateSlot}
        />
      )}
    </div>
  );
}

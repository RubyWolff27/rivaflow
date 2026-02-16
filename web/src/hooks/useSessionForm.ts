import { useState, useMemo, useCallback } from 'react';
import type { Friend, Movement, MediaUrl, WhoopWorkoutMatch } from '../types';
import type { RollEntry, TechniqueEntry } from '../components/sessions/sessionTypes';
import { SPARRING_TYPES } from '../components/sessions/sessionTypes';
import { whoopApi, getErrorMessage } from '../api/client';
import { useToast } from '../contexts/ToastContext';

// ── Types ────────────────────────────────────────────────────────────

export interface SessionFormData {
  session_date: string;
  class_time: string;
  class_type: string;
  gym_name: string;
  gym_id: number | null;
  location: string;
  duration_mins: number;
  intensity: number;
  instructor_id: number | null;
  instructor_name: string;
  rolls: number;
  submissions_for: number;
  submissions_against: number;
  partners: string;
  techniques: string;
  notes: string;
  whoop_strain: string;
  whoop_calories: string;
  whoop_avg_hr: string;
  whoop_max_hr: string;
}

export interface FightDynamicsData {
  attacks_attempted: number;
  attacks_successful: number;
  defenses_attempted: number;
  defenses_successful: number;
}

export interface WhoopSyncParams {
  session_date?: string;
  class_time?: string;
  duration_mins?: number;
  session_id?: number;
}

export interface UseSessionFormOptions {
  initialData?: Partial<SessionFormData>;
  initialRolls?: RollEntry[];
  initialTechniques?: TechniqueEntry[];
  initialDetailedMode?: boolean;
  /** Custom params builder for WHOOP sync (edit mode passes session_id) */
  whoopSyncParams?: () => WhoopSyncParams;
}

export interface UseSessionFormReturn {
  // Session form data
  sessionData: SessionFormData;
  setSessionData: React.Dispatch<React.SetStateAction<SessionFormData>>;

  // Roll tracking
  detailedMode: boolean;
  setDetailedMode: React.Dispatch<React.SetStateAction<boolean>>;
  rolls: RollEntry[];
  setRolls: React.Dispatch<React.SetStateAction<RollEntry[]>>;
  submissionSearchFor: Record<number, string>;
  setSubmissionSearchFor: React.Dispatch<
    React.SetStateAction<Record<number, string>>
  >;
  submissionSearchAgainst: Record<number, string>;
  setSubmissionSearchAgainst: React.Dispatch<
    React.SetStateAction<Record<number, string>>
  >;
  handleAddRoll: () => void;
  handleRemoveRoll: (index: number) => void;
  handleRollChange: (
    index: number,
    field: keyof RollEntry,
    value: RollEntry[keyof RollEntry]
  ) => void;
  handleToggleSubmission: (
    rollIndex: number,
    movementId: number,
    type: 'for' | 'against'
  ) => void;

  // Technique tracking
  techniques: TechniqueEntry[];
  setTechniques: React.Dispatch<React.SetStateAction<TechniqueEntry[]>>;
  techniqueSearch: Record<number, string>;
  setTechniqueSearch: React.Dispatch<
    React.SetStateAction<Record<number, string>>
  >;
  handleAddTechnique: () => void;
  handleRemoveTechnique: (index: number) => void;
  handleTechniqueChange: (
    index: number,
    field: keyof TechniqueEntry,
    value: TechniqueEntry[keyof TechniqueEntry]
  ) => void;
  handleSelectMovement: (
    index: number,
    movementId: number,
    movementName: string
  ) => void;
  handleAddMediaUrl: (techIndex: number) => void;
  handleRemoveMediaUrl: (techIndex: number, mediaIndex: number) => void;
  handleMediaUrlChange: (
    techIndex: number,
    mediaIndex: number,
    field: keyof MediaUrl,
    value: string
  ) => void;

  // Fight dynamics
  fightDynamics: FightDynamicsData;
  setFightDynamics: React.Dispatch<React.SetStateAction<FightDynamicsData>>;
  handleFightDynamicsIncrement: (field: keyof FightDynamicsData) => void;
  handleFightDynamicsDecrement: (field: keyof FightDynamicsData) => void;
  handleFightDynamicsChange: (
    field: keyof FightDynamicsData,
    value: number
  ) => void;

  // WHOOP integration
  whoopConnected: boolean;
  setWhoopConnected: React.Dispatch<React.SetStateAction<boolean>>;
  whoopSyncing: boolean;
  whoopSynced: boolean;
  setWhoopSynced: React.Dispatch<React.SetStateAction<boolean>>;
  whoopMatches: WhoopWorkoutMatch[];
  showWhoopModal: boolean;
  setShowWhoopModal: React.Dispatch<React.SetStateAction<boolean>>;
  whoopManualMode: boolean;
  setWhoopManualMode: React.Dispatch<React.SetStateAction<boolean>>;
  handleWhoopSync: () => Promise<void>;
  handleWhoopMatchSelect: (workoutCacheId: number) => void;
  handleWhoopClear: () => void;

  // UI toggles
  showWhoop: boolean;
  setShowWhoop: React.Dispatch<React.SetStateAction<boolean>>;
  showFightDynamics: boolean;
  setShowFightDynamics: React.Dispatch<React.SetStateAction<boolean>>;
  showMoreDetails: boolean;
  setShowMoreDetails: React.Dispatch<React.SetStateAction<boolean>>;
  showCustomDuration: boolean;
  setShowCustomDuration: React.Dispatch<React.SetStateAction<boolean>>;

  // Partner management
  selectedPartnerIds: Set<number>;
  setSelectedPartnerIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  handleTogglePartner: (partnerId: number) => void;
  topPartners: Friend[];

  // Computed values
  isSparringType: boolean;
  submissionMovements: Movement[];
  filterMovements: (search: string) => Movement[];
  filterSubmissions: (search: string) => Movement[];

  // Reference data (managed externally, but stored here for convenience)
  instructors: Friend[];
  setInstructors: React.Dispatch<React.SetStateAction<Friend[]>>;
  partners: Friend[];
  setPartners: React.Dispatch<React.SetStateAction<Friend[]>>;
  movements: Movement[];
  setMovements: React.Dispatch<React.SetStateAction<Movement[]>>;
  autocomplete: {
    gyms?: string[];
    locations?: string[];
    partners?: string[];
    techniques?: string[];
  };
  setAutocomplete: React.Dispatch<
    React.SetStateAction<{
      gyms?: string[];
      locations?: string[];
      partners?: string[];
      techniques?: string[];
    }>
  >;

  // Payload builders
  buildRollsPayload: () => {
    session_rolls?: Array<{
      roll_number: number;
      partner_id?: number | null;
      partner_name?: string;
      duration_mins?: number;
      submissions_for?: number[];
      submissions_against?: number[];
      notes?: string;
    }>;
    rolls?: number;
    submissions_for?: number;
    submissions_against?: number;
  };
  buildTechniquesPayload: () => {
    session_techniques?: Array<{
      movement_id: number;
      technique_number: number;
      notes?: string;
      media_urls?: MediaUrl[];
    }>;
  };
  buildWhoopPayload: () => {
    whoop_strain?: number;
    whoop_calories?: number;
    whoop_avg_hr?: number;
    whoop_max_hr?: number;
  };
  buildFightDynamicsPayload: () => {
    attacks_attempted?: number;
    attacks_successful?: number;
    defenses_attempted?: number;
    defenses_successful?: number;
  };
}

// ── Default values ───────────────────────────────────────────────────

const DEFAULT_SESSION_DATA: SessionFormData = {
  session_date: '',
  class_time: '',
  class_type: 'gi',
  gym_name: '',
  gym_id: null,
  location: '',
  duration_mins: 60,
  intensity: 4,
  instructor_id: null,
  instructor_name: '',
  rolls: 0,
  submissions_for: 0,
  submissions_against: 0,
  partners: '',
  techniques: '',
  notes: '',
  whoop_strain: '',
  whoop_calories: '',
  whoop_avg_hr: '',
  whoop_max_hr: '',
};

const DEFAULT_FIGHT_DYNAMICS: FightDynamicsData = {
  attacks_attempted: 0,
  attacks_successful: 0,
  defenses_attempted: 0,
  defenses_successful: 0,
};

// ── Helpers ──────────────────────────────────────────────────────────

/** Merge manual partners + instructors + social friends, deduped by name */
export function mergePartners(
  manualPartners: Friend[],
  loadedInstructors: Friend[],
  socialFriends: Friend[]
): Friend[] {
  const seenNames = new Set<string>();
  const merged: Friend[] = [];
  for (const p of [...manualPartners, ...loadedInstructors]) {
    const key = p.name.toLowerCase();
    if (!seenNames.has(key)) {
      seenNames.add(key);
      merged.push(p);
    }
  }
  for (const sf of socialFriends) {
    if (!seenNames.has(sf.name.toLowerCase())) {
      seenNames.add(sf.name.toLowerCase());
      merged.push(sf);
    }
  }
  return merged;
}

/** Map social API friends to Friend type */
export function mapSocialFriends(
  rawFriends: Array<{ id: number; first_name?: string; last_name?: string }>
): Friend[] {
  return rawFriends.map(
    (sf) => ({
      id: sf.id + 1000000,
      name: `${sf.first_name || ''} ${sf.last_name || ''}`.trim(),
      friend_type: 'training-partner' as const,
    })
  );
}

/** Reindex search state after removing an item */
function reindexSearchState(
  prev: Record<number, string>,
  removedIndex: number
): Record<number, string> {
  const result: Record<number, string> = {};
  Object.keys(prev).forEach((key) => {
    const idx = parseInt(key);
    if (idx < removedIndex) result[idx] = prev[idx];
    else if (idx > removedIndex) result[idx - 1] = prev[idx];
  });
  return result;
}

// ── Hook ─────────────────────────────────────────────────────────────

export function useSessionForm(
  options: UseSessionFormOptions = {}
): UseSessionFormReturn {
  const {
    initialData,
    initialRolls,
    initialTechniques,
    initialDetailedMode,
    whoopSyncParams,
  } = options;
  const toast = useToast();

  // ── Session form data ──────────────────────────────────────────────
  const [sessionData, setSessionData] = useState<SessionFormData>({
    ...DEFAULT_SESSION_DATA,
    ...initialData,
  });

  // ── Roll tracking ──────────────────────────────────────────────────
  const [detailedMode, setDetailedMode] = useState(
    initialDetailedMode ?? false
  );
  const [rolls, setRolls] = useState<RollEntry[]>(initialRolls ?? []);
  const [submissionSearchFor, setSubmissionSearchFor] = useState<
    Record<number, string>
  >({});
  const [submissionSearchAgainst, setSubmissionSearchAgainst] = useState<
    Record<number, string>
  >({});

  // ── Technique tracking ─────────────────────────────────────────────
  const [techniques, setTechniques] = useState<TechniqueEntry[]>(
    initialTechniques ?? []
  );
  const [techniqueSearch, setTechniqueSearch] = useState<
    Record<number, string>
  >({});

  // ── Fight dynamics ─────────────────────────────────────────────────
  const [fightDynamics, setFightDynamics] =
    useState<FightDynamicsData>(DEFAULT_FIGHT_DYNAMICS);

  // ── WHOOP integration ──────────────────────────────────────────────
  const [whoopConnected, setWhoopConnected] = useState(false);
  const [whoopSyncing, setWhoopSyncing] = useState(false);
  const [whoopSynced, setWhoopSynced] = useState(false);
  const [whoopMatches, setWhoopMatches] = useState<WhoopWorkoutMatch[]>([]);
  const [showWhoopModal, setShowWhoopModal] = useState(false);
  const [whoopManualMode, setWhoopManualMode] = useState(false);

  // ── UI toggles ─────────────────────────────────────────────────────
  const [showWhoop, setShowWhoop] = useState(false);
  const [showFightDynamics, setShowFightDynamics] = useState(false);
  const [showMoreDetails, setShowMoreDetails] = useState(false);
  const [showCustomDuration, setShowCustomDuration] = useState(false);

  // ── Partner management ─────────────────────────────────────────────
  const [selectedPartnerIds, setSelectedPartnerIds] = useState<Set<number>>(
    new Set()
  );

  // ── Reference data ─────────────────────────────────────────────────
  const [instructors, setInstructors] = useState<Friend[]>([]);
  const [partners, setPartners] = useState<Friend[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [autocomplete, setAutocomplete] = useState<{
    gyms?: string[];
    locations?: string[];
    partners?: string[];
    techniques?: string[];
  }>({});

  // ── Roll handlers ──────────────────────────────────────────────────

  const handleAddRoll = useCallback(() => {
    setRolls((prev) => [
      ...prev,
      {
        roll_number: prev.length + 1,
        partner_id: null,
        partner_name: '',
        duration_mins: 5,
        submissions_for: [],
        submissions_against: [],
        notes: '',
      },
    ]);
  }, []);

  const handleRemoveRoll = useCallback((index: number) => {
    setRolls((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      updated.forEach((roll, i) => {
        roll.roll_number = i + 1;
      });
      return updated;
    });
    setSubmissionSearchFor((prev) => reindexSearchState(prev, index));
    setSubmissionSearchAgainst((prev) => reindexSearchState(prev, index));
  }, []);

  const handleRollChange = useCallback(
    (
      index: number,
      field: keyof RollEntry,
      value: RollEntry[keyof RollEntry]
    ) => {
      setRolls((prev) => {
        const updated = [...prev];
        updated[index] = { ...updated[index], [field]: value };
        return updated;
      });
    },
    []
  );

  const handleToggleSubmission = useCallback(
    (rollIndex: number, movementId: number, type: 'for' | 'against') => {
      setRolls((prev) => {
        const updated = [...prev];
        const field =
          type === 'for' ? 'submissions_for' : 'submissions_against';
        const current = updated[rollIndex][field];
        if (current.includes(movementId)) {
          updated[rollIndex] = {
            ...updated[rollIndex],
            [field]: current.filter((id) => id !== movementId),
          };
        } else {
          updated[rollIndex] = {
            ...updated[rollIndex],
            [field]: [...current, movementId],
          };
        }
        return updated;
      });
    },
    []
  );

  // ── Technique handlers ─────────────────────────────────────────────

  const handleAddTechnique = useCallback(() => {
    setTechniques((prev) => [
      ...prev,
      {
        technique_number: prev.length + 1,
        movement_id: null,
        movement_name: '',
        notes: '',
        media_urls: [],
      },
    ]);
  }, []);

  const handleRemoveTechnique = useCallback((index: number) => {
    setTechniques((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      updated.forEach((tech, i) => {
        tech.technique_number = i + 1;
      });
      return updated;
    });
    setTechniqueSearch((prev) => reindexSearchState(prev, index));
  }, []);

  const handleTechniqueChange = useCallback(
    (
      index: number,
      field: keyof TechniqueEntry,
      value: TechniqueEntry[keyof TechniqueEntry]
    ) => {
      setTechniques((prev) => {
        const updated = [...prev];
        updated[index] = { ...updated[index], [field]: value };
        return updated;
      });
    },
    []
  );

  const handleSelectMovement = useCallback(
    (index: number, movementId: number, movementName: string) => {
      setTechniques((prev) => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          movement_id: movementId,
          movement_name: movementName,
        };
        return updated;
      });
    },
    []
  );

  const handleAddMediaUrl = useCallback((techIndex: number) => {
    setTechniques((prev) => {
      const updated = [...prev];
      updated[techIndex] = {
        ...updated[techIndex],
        media_urls: [
          ...updated[techIndex].media_urls,
          { type: 'video', url: '', title: '' },
        ],
      };
      return updated;
    });
  }, []);

  const handleRemoveMediaUrl = useCallback(
    (techIndex: number, mediaIndex: number) => {
      setTechniques((prev) => {
        const updated = [...prev];
        updated[techIndex] = {
          ...updated[techIndex],
          media_urls: updated[techIndex].media_urls.filter(
            (_, i) => i !== mediaIndex
          ),
        };
        return updated;
      });
    },
    []
  );

  const handleMediaUrlChange = useCallback(
    (
      techIndex: number,
      mediaIndex: number,
      field: keyof MediaUrl,
      value: string
    ) => {
      setTechniques((prev) => {
        const updated = [...prev];
        const mediaUrls = [...updated[techIndex].media_urls];
        mediaUrls[mediaIndex] = { ...mediaUrls[mediaIndex], [field]: value };
        updated[techIndex] = { ...updated[techIndex], media_urls: mediaUrls };
        return updated;
      });
    },
    []
  );

  // ── Fight dynamics handlers ────────────────────────────────────────

  const handleFightDynamicsIncrement = useCallback(
    (field: keyof FightDynamicsData) => {
      setFightDynamics((fd) => {
        if (field === 'attacks_successful')
          return {
            ...fd,
            [field]: Math.min(fd.attacks_attempted, fd[field] + 1),
          };
        if (field === 'defenses_successful')
          return {
            ...fd,
            [field]: Math.min(fd.defenses_attempted, fd[field] + 1),
          };
        return { ...fd, [field]: fd[field] + 1 };
      });
    },
    []
  );

  const handleFightDynamicsDecrement = useCallback(
    (field: keyof FightDynamicsData) => {
      setFightDynamics((fd) => ({
        ...fd,
        [field]: Math.max(0, fd[field] - 1),
      }));
    },
    []
  );

  const handleFightDynamicsChange = useCallback(
    (field: keyof FightDynamicsData, value: number) => {
      setFightDynamics((fd) => {
        const clamped = Math.max(0, value);
        if (field === 'attacks_successful')
          return {
            ...fd,
            [field]: Math.min(fd.attacks_attempted, clamped),
          };
        if (field === 'defenses_successful')
          return {
            ...fd,
            [field]: Math.min(fd.defenses_attempted, clamped),
          };
        return { ...fd, [field]: clamped };
      });
    },
    []
  );

  // ── WHOOP handlers ─────────────────────────────────────────────────

  const handleWhoopSync = useCallback(async () => {
    const params = whoopSyncParams
      ? whoopSyncParams()
      : {
          session_date: sessionData.session_date,
          class_time: sessionData.class_time,
          duration_mins: sessionData.duration_mins,
        };

    // Must have either session_id or (session_date + class_time)
    if (!params.session_id && (!params.session_date || !params.class_time))
      return;

    setWhoopSyncing(true);
    try {
      const res = await whoopApi.getWorkouts(params);
      const matches = res.data.workouts || [];
      if (matches.length === 0) {
        toast.warning('No matching WHOOP workouts found');
      } else if (matches.length === 1 && matches[0].overlap_pct >= 90) {
        const w = matches[0];
        setSessionData((prev) => ({
          ...prev,
          whoop_strain: w.strain?.toString() || '',
          whoop_calories: w.calories?.toString() || '',
          whoop_avg_hr: w.avg_heart_rate?.toString() || '',
          whoop_max_hr: w.max_heart_rate?.toString() || '',
        }));
        setWhoopSynced(true);
        toast.success('WHOOP data synced automatically');
      } else {
        setWhoopMatches(matches);
        setShowWhoopModal(true);
      }
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setWhoopSyncing(false);
    }
  }, [
    whoopSyncParams,
    sessionData.session_date,
    sessionData.class_time,
    sessionData.duration_mins,
    toast,
  ]);

  const handleWhoopMatchSelect = useCallback(
    (workoutCacheId: number) => {
      const workout = whoopMatches.find((w) => w.id === workoutCacheId);
      if (workout) {
        setSessionData((prev) => ({
          ...prev,
          whoop_strain: workout.strain?.toString() || '',
          whoop_calories: workout.calories?.toString() || '',
          whoop_avg_hr: workout.avg_heart_rate?.toString() || '',
          whoop_max_hr: workout.max_heart_rate?.toString() || '',
        }));
        setWhoopSynced(true);
        setShowWhoopModal(false);
        toast.success('WHOOP data applied');
      }
    },
    [whoopMatches, toast]
  );

  const handleWhoopClear = useCallback(() => {
    setSessionData((prev) => ({
      ...prev,
      whoop_strain: '',
      whoop_calories: '',
      whoop_avg_hr: '',
      whoop_max_hr: '',
    }));
    setWhoopSynced(false);
  }, []);

  // ── Partner management ─────────────────────────────────────────────

  const topPartners = useMemo(
    () =>
      partners
        .filter(
          (p) =>
            p.friend_type === 'training-partner' || p.friend_type === 'both'
        )
        .slice(0, 8),
    [partners]
  );

  const handleTogglePartner = useCallback((partnerId: number) => {
    setSelectedPartnerIds((prev) => {
      const next = new Set(prev);
      if (next.has(partnerId)) next.delete(partnerId);
      else next.add(partnerId);
      return next;
    });
  }, []);

  // ── Computed values ────────────────────────────────────────────────

  const isSparringType = useMemo(
    () => SPARRING_TYPES.includes(sessionData.class_type),
    [sessionData.class_type]
  );

  const submissionMovements = useMemo(
    () => movements.filter((m) => m.category === 'submission'),
    [movements]
  );

  const filterMovements = useCallback(
    (search: string) => {
      const s = search.toLowerCase();
      return movements.filter(
        (m) =>
          m.name?.toLowerCase().includes(s) ||
          m.category?.toLowerCase().includes(s) ||
          m.subcategory?.toLowerCase().includes(s) ||
          (m.aliases ?? []).some((alias) => alias.toLowerCase().includes(s))
      );
    },
    [movements]
  );

  const filterSubmissions = useCallback(
    (search: string) => {
      const s = search.toLowerCase();
      return submissionMovements.filter(
        (m) =>
          m.name?.toLowerCase().includes(s) ||
          m.subcategory?.toLowerCase().includes(s) ||
          (m.aliases ?? []).some((alias) => alias.toLowerCase().includes(s))
      );
    },
    [submissionMovements]
  );

  // ── Payload builders ───────────────────────────────────────────────

  const buildRollsPayload = useCallback(() => {
    if (!detailedMode || rolls.length === 0) return {};
    return {
      session_rolls: rolls.map((roll) => ({
        roll_number: roll.roll_number,
        partner_id: roll.partner_id || undefined,
        partner_name: roll.partner_name || undefined,
        duration_mins: roll.duration_mins || undefined,
        submissions_for:
          roll.submissions_for.length > 0
            ? roll.submissions_for
            : undefined,
        submissions_against:
          roll.submissions_against.length > 0
            ? roll.submissions_against
            : undefined,
        notes: roll.notes || undefined,
      })),
      rolls: rolls.length,
      submissions_for: rolls.reduce(
        (sum, roll) => sum + roll.submissions_for.length,
        0
      ),
      submissions_against: rolls.reduce(
        (sum, roll) => sum + roll.submissions_against.length,
        0
      ),
    };
  }, [detailedMode, rolls]);

  const buildTechniquesPayload = useCallback(() => {
    const filtered = techniques.filter((tech) => tech.movement_id !== null);
    if (filtered.length === 0) return {};
    return {
      session_techniques: filtered.map((tech) => ({
        movement_id: tech.movement_id!,
        technique_number: tech.technique_number,
        notes: tech.notes || undefined,
        media_urls:
          tech.media_urls.length > 0
            ? tech.media_urls.filter((m) => m.url)
            : undefined,
      })),
    };
  }, [techniques]);

  const buildWhoopPayload = useCallback(() => {
    const result: {
      whoop_strain?: number;
      whoop_calories?: number;
      whoop_avg_hr?: number;
      whoop_max_hr?: number;
    } = {};
    if (sessionData.whoop_strain)
      result.whoop_strain = parseFloat(sessionData.whoop_strain);
    if (sessionData.whoop_calories)
      result.whoop_calories = parseInt(sessionData.whoop_calories);
    if (sessionData.whoop_avg_hr)
      result.whoop_avg_hr = parseInt(sessionData.whoop_avg_hr);
    if (sessionData.whoop_max_hr)
      result.whoop_max_hr = parseInt(sessionData.whoop_max_hr);
    return result;
  }, [
    sessionData.whoop_strain,
    sessionData.whoop_calories,
    sessionData.whoop_avg_hr,
    sessionData.whoop_max_hr,
  ]);

  const buildFightDynamicsPayload = useCallback(() => {
    if (
      fightDynamics.attacks_attempted === 0 &&
      fightDynamics.defenses_attempted === 0
    )
      return {};
    return {
      attacks_attempted: fightDynamics.attacks_attempted,
      attacks_successful: Math.min(
        fightDynamics.attacks_successful,
        fightDynamics.attacks_attempted
      ),
      defenses_attempted: fightDynamics.defenses_attempted,
      defenses_successful: Math.min(
        fightDynamics.defenses_successful,
        fightDynamics.defenses_attempted
      ),
    };
  }, [fightDynamics]);

  // ── Return ─────────────────────────────────────────────────────────

  return {
    // Session form data
    sessionData,
    setSessionData,

    // Roll tracking
    detailedMode,
    setDetailedMode,
    rolls,
    setRolls,
    submissionSearchFor,
    setSubmissionSearchFor,
    submissionSearchAgainst,
    setSubmissionSearchAgainst,
    handleAddRoll,
    handleRemoveRoll,
    handleRollChange,
    handleToggleSubmission,

    // Technique tracking
    techniques,
    setTechniques,
    techniqueSearch,
    setTechniqueSearch,
    handleAddTechnique,
    handleRemoveTechnique,
    handleTechniqueChange,
    handleSelectMovement,
    handleAddMediaUrl,
    handleRemoveMediaUrl,
    handleMediaUrlChange,

    // Fight dynamics
    fightDynamics,
    setFightDynamics,
    handleFightDynamicsIncrement,
    handleFightDynamicsDecrement,
    handleFightDynamicsChange,

    // WHOOP integration
    whoopConnected,
    setWhoopConnected,
    whoopSyncing,
    whoopSynced,
    setWhoopSynced,
    whoopMatches,
    showWhoopModal,
    setShowWhoopModal,
    whoopManualMode,
    setWhoopManualMode,
    handleWhoopSync,
    handleWhoopMatchSelect,
    handleWhoopClear,

    // UI toggles
    showWhoop,
    setShowWhoop,
    showFightDynamics,
    setShowFightDynamics,
    showMoreDetails,
    setShowMoreDetails,
    showCustomDuration,
    setShowCustomDuration,

    // Partner management
    selectedPartnerIds,
    setSelectedPartnerIds,
    handleTogglePartner,
    topPartners,

    // Computed values
    isSparringType,
    submissionMovements,
    filterMovements,
    filterSubmissions,

    // Reference data
    instructors,
    setInstructors,
    partners,
    setPartners,
    movements,
    setMovements,
    autocomplete,
    setAutocomplete,

    // Payload builders
    buildRollsPayload,
    buildTechniquesPayload,
    buildWhoopPayload,
    buildFightDynamicsPayload,
  };
}

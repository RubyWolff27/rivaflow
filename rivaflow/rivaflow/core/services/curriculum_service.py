"""Belt-curriculum tracker — the declared slate, the status engine, coach export.

The atom is a declared SEQUENCE (entry/grip -> position/action -> terminal
finish), not a technique, because the AJJ syllabus is written that way ("10
sweeps -> submission"). ~88 of the ~90 purple slots are "of choice", so the
slate doubles as the game-system tracker via ``game_tag``.

INTEGRITY CORE — read this before changing anything here:

Status is DERIVED, never stored and never settable. ``compute_slot_state`` is a
pure function of a slot's evidence rows plus its sign-off rows; no API path can
write a status, because no table has a status column. The ladder:

    not-started -> drilled -> grooved -> live -> coach-verified

Rungs 0-3 come only from logged evidence. ``coach-verified`` is never inferred:
it requires a sign-off row whose verdict is ``verified``, and the LATEST
sign-off wins (a later "not yet" supersedes an earlier "verified" — the coach
changed their mind and the record should say so).

Staleness is reported in days and never demotes a status (council compromise:
the UI dims an old row, it does not take the rung away).

``weak_evidence`` flags slots whose live evidence is entirely against smaller
and lower-ranked partners — the strength-masks-technique confound.

No percentage is computed anywhere in the coach export. That is a binding
council rule, not a style preference, and ``get_export`` is tested for it.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.db.repositories.curriculum_repo import CurriculumRepository
from rivaflow.db.repositories.session_repo import MAT_CLASS_TYPES, SessionRepository

# AJJ requires a minimum of 50 classes between adult belts. This is the Academy's
# rule, not a RivaFlow preference — see reference_ajj_grading_system.
CLASSES_REQUIRED_FOR_PROMOTION = 50

# ---------------------------------------------------------------------------
# Status ladder constants — the whole integrity story lives in these five rules.
# ---------------------------------------------------------------------------

STATUS_NOT_STARTED = "not-started"
STATUS_DRILLED = "drilled"
STATUS_GROOVED = "grooved"
STATUS_LIVE = "live"
STATUS_COACH_VERIFIED = "coach-verified"

STATUS_LADDER: list[str] = [
    STATUS_NOT_STARTED,
    STATUS_DRILLED,
    STATUS_GROOVED,
    STATUS_LIVE,
    STATUS_COACH_VERIFIED,
]

#: drilled — the sequence appears in at least this many logged sessions.
DRILLED_MIN_SESSIONS = 1
#: grooved — spread across this many DISTINCT sessions...
GROOVED_MIN_SESSIONS = 3
#: ...spanning at least this many days end to end (3 weeks).
GROOVED_MIN_SPAN_DAYS = 21
#: live — landed under resistance on at least this many occasions...
LIVE_MIN_OCCASIONS = 2
#: ...against at least this many distinct partner identities.
LIVE_MIN_PARTNERS = 2

EVIDENCE_KINDS = ("drilled", "live")
SIGNOFF_VERDICTS = ("verified", "not-yet", "show-me")
GAME_TAGS = ("a-game", "b-game", "syllabus-only")

#: Relative partner bands. Live evidence only against the weak end of BOTH
#: scales is what raises ``weak_evidence``.
PARTNER_RANK_BANDS = ("lower", "same", "higher")
PARTNER_SIZES = ("smaller", "similar", "bigger")
WEAK_RANK_BAND = "lower"
WEAK_SIZE = "smaller"

DEFAULT_BELT = "purple"

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "curriculum"
SYLLABUS_PATH = _DATA_DIR / "ajj_purple_syllabus.json"
DRAFT_SLATE_PATH = _DATA_DIR / "draft_slate_ruby.json"


# ---------------------------------------------------------------------------
# Pure helpers — no DB, no I/O. These are the tested surface.
# ---------------------------------------------------------------------------


def _as_date(value: Any) -> date | None:
    """Coerce a stored date (PG ``date``, SQLite text, ISO string) to a date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _as_bool(value: Any) -> bool:
    """SQLite hands booleans back as 0/1; PostgreSQL as real booleans."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ("1", "true", "t", "yes")


def _session_key(row: dict) -> str:
    """Identity of the session an evidence row belongs to.

    Evidence linked to a real session uses its id. Evidence logged without a
    session (retro-entered from the notebook) falls back to its date, so two
    entries on the same day never inflate the distinct-session count.
    """
    session_id = row.get("session_id")
    if session_id is not None:
        return f"s:{session_id}"
    return f"d:{_as_date(row.get('logged_at'))}"


def _partner_key(row: dict) -> str:
    """Identity of the partner on a live evidence row.

    An explicit ``partner_ref`` wins when present. Otherwise the
    rank-band/size pair stands in, per the design note that the pair is enough
    to control the confound. Rows carrying neither collapse into a single
    "unknown" bucket — unidentified partners cannot corroborate each other.
    """
    ref = row.get("partner_ref")
    if ref:
        return f"ref:{ref}"
    band = row.get("partner_rank_band")
    size = row.get("partner_size")
    if band is None and size is None:
        return "unknown"
    return f"band:{band}|size:{size}"


def latest_signoff(signoffs: list[dict]) -> dict | None:
    """The most recent sign-off for a slot, or None.

    Rows are assumed to arrive oldest-first from the repository; ties fall back
    to the highest id so the ordering is deterministic either way.
    """
    if not signoffs:
        return None
    return max(
        signoffs,
        key=lambda s: (
            _as_date(s.get("created_at")) or date.min,
            int(s.get("id") or 0),
        ),
    )


def compute_slot_state(
    evidence: list[dict],
    signoffs: list[dict],
    today: date | None = None,
) -> dict[str, Any]:
    """Derive a slot's status and its supporting counters.

    This is the whole integrity core. It reads logs and sign-offs and nothing
    else — in particular it never reads a stored status, because none exists.

    Returns the status, the counters that produced it (so the UI can explain
    itself), ``staleness_days`` since the last evidence of any kind, and the
    ``weak_evidence`` confound flag.
    """
    today = today or date.today()

    drilled_rows = [e for e in evidence if e.get("kind") == "drilled"]
    live_rows = [e for e in evidence if e.get("kind") == "live"]

    # Any evidence, drilled or live, counts as having touched the sequence.
    session_keys = {_session_key(e) for e in evidence}
    dates = sorted(d for d in (_as_date(e.get("logged_at")) for e in evidence) if d)
    span_days = (dates[-1] - dates[0]).days if len(dates) >= 2 else 0
    last_evidence = dates[-1] if dates else None

    partner_keys = {_partner_key(e) for e in live_rows}
    live_occasions = len(live_rows)

    signoff = latest_signoff(signoffs)
    verdict = signoff.get("verdict") if signoff else None

    # Top-down: each rung has its own predicate, so the highest one that is
    # satisfied wins. coach-verified is never inferred from logs.
    if verdict == "verified":
        status = STATUS_COACH_VERIFIED
    elif (
        live_occasions >= LIVE_MIN_OCCASIONS and len(partner_keys) >= LIVE_MIN_PARTNERS
    ):
        status = STATUS_LIVE
    elif (
        len(session_keys) >= GROOVED_MIN_SESSIONS and span_days >= GROOVED_MIN_SPAN_DAYS
    ):
        status = STATUS_GROOVED
    elif len(session_keys) >= DRILLED_MIN_SESSIONS:
        status = STATUS_DRILLED
    else:
        status = STATUS_NOT_STARTED

    weak_evidence = bool(live_rows) and all(
        e.get("partner_rank_band") == WEAK_RANK_BAND
        and e.get("partner_size") == WEAK_SIZE
        for e in live_rows
    )

    return {
        "status": status,
        "sessions": len(session_keys),
        "drilled_entries": len(drilled_rows),
        "live_occasions": live_occasions,
        "live_partners": len(partner_keys),
        "span_days": span_days,
        "last_evidence_at": last_evidence.isoformat() if last_evidence else None,
        "staleness_days": (today - last_evidence).days if last_evidence else None,
        "weak_evidence": weak_evidence,
        "signoff_verdict": verdict,
        "signoff_count": len(signoffs),
        "signoff_coach_name": signoff.get("coach_name") if signoff else None,
        "signoff_at": signoff.get("created_at") if signoff else None,
    }


def is_declared(slot: dict) -> bool:
    """A slot counts as declared once it names a finish."""
    return bool((slot.get("seq_finish") or "").strip())


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class CurriculumService:
    """Business logic for the belt-curriculum tracker."""

    def __init__(self) -> None:
        self.repo = CurriculumRepository()

    # ------------------------------------------------------------ syllabus

    @staticmethod
    def load_syllabus() -> dict[str, Any]:
        """The AJJ purple syllabus shape (blocks -> requirements -> counts)."""
        with open(SYLLABUS_PATH) as fh:
            data: dict[str, Any] = json.load(fh)
        return data

    @staticmethod
    def load_draft_slate() -> dict[str, Any]:
        """Ruby's DRAFT slate — every of-choice slot pre-filled, unconfirmed."""
        with open(DRAFT_SLATE_PATH) as fh:
            data: dict[str, Any] = json.load(fh)
        return data

    @staticmethod
    def build_seed_rows(
        with_draft: bool = False, belt: str = DEFAULT_BELT
    ) -> list[dict[str, Any]]:
        """Build the ~90 slot rows for one user.

        Requirements with ``count: null`` are clusters (the armbar/choke defence
        groups) and produce a single non-of-choice slot. Of-choice slots start
        UNDECLARED unless ``with_draft`` is set, in which case Ruby's draft
        sequences are attached with ``is_draft`` true.
        """
        syllabus = CurriculumService.load_syllabus()
        draft_by_key: dict[tuple[str, int], dict[str, Any]] = {}
        if with_draft:
            for row in CurriculumService.load_draft_slate()["slots"]:
                draft_by_key[(row["requirement_key"], row["slot_index"])] = row

        rows: list[dict[str, Any]] = []
        for block in syllabus["blocks"]:
            for req in block["requirements"]:
                count = req.get("count")
                of_choice = bool(req.get("of_choice", True))
                # A cluster requirement is one slot, not N.
                n = int(count) if count else 1
                for index in range(1, n + 1):
                    row: dict[str, Any] = {
                        "belt": belt,
                        "block": block["key"],
                        "requirement_key": req["key"],
                        "requirement_label": req.get("label"),
                        "slot_index": index,
                        "of_choice": of_choice,
                        "is_draft": False,
                    }
                    draft = draft_by_key.get((req["key"], index))
                    if draft:
                        row.update(
                            {
                                "seq_entry": draft.get("seq_entry"),
                                "seq_position": draft.get("seq_position"),
                                "seq_finish": draft.get("seq_finish"),
                                "game_tag": draft.get("game_tag"),
                                "tension_note": draft.get("tension_note"),
                                "is_draft": True,
                            }
                        )
                    rows.append(row)
        return rows

    def seed_user(
        self,
        user_id: int,
        with_draft: bool = False,
        belt: str = DEFAULT_BELT,
        force: bool = False,
    ) -> dict[str, Any]:
        """Create the syllabus slots for a user. No-op when already seeded."""
        existing = self.repo.count_slots(user_id, belt)
        if existing and not force:
            return {"seeded": 0, "existing": existing, "skipped": True}

        rows = self.build_seed_rows(with_draft=with_draft, belt=belt)
        created = self.repo.bulk_create_slots(user_id, rows)
        return {"seeded": created, "existing": existing, "skipped": False}

    # --------------------------------------------------------------- reads

    def _slate(self, user_id: int, belt: str, today: date | None = None) -> list[dict]:
        """Slots joined with their derived state, in syllabus order."""
        slots = self.repo.list_slots(user_id, belt)
        evidence = self.repo.list_evidence(user_id, belt)
        signoffs = self.repo.list_signoffs(user_id, belt)

        ev_by_slot: dict[Any, list[dict]] = {}
        for row in evidence:
            ev_by_slot.setdefault(row["slot_id"], []).append(row)
        sign_by_slot: dict[Any, list[dict]] = {}
        for row in signoffs:
            sign_by_slot.setdefault(row["slot_id"], []).append(row)

        out: list[dict] = []
        for slot in slots:
            state = compute_slot_state(
                ev_by_slot.get(slot["id"], []),
                sign_by_slot.get(slot["id"], []),
                today=today,
            )
            enriched = dict(slot)
            enriched["of_choice"] = _as_bool(slot.get("of_choice"))
            enriched["is_draft"] = _as_bool(slot.get("is_draft"))
            enriched["declared"] = is_declared(slot)
            enriched.update(state)
            out.append(enriched)
        return out

    def get_slots(
        self, user_id: int, belt: str = DEFAULT_BELT, today: date | None = None
    ) -> dict[str, Any]:
        """Full slate with computed status per slot."""
        slate = self._slate(user_id, belt, today=today)
        # Official 2024 syllabus examples per requirement — grading answer key,
        # shown beside a slot when declaring (never auto-filled into the slate).
        official_examples = {
            r["key"]: r["official_examples"]
            for b in self.load_syllabus()["blocks"]
            for r in b.get("requirements", [])
            if r.get("official_examples")
        }
        return {
            "belt": belt,
            "slot_count": len(slate),
            "status_ladder": STATUS_LADDER,
            "slots": slate,
            "official_examples": official_examples,
        }

    def get_summary(
        self, user_id: int, belt: str = DEFAULT_BELT, today: date | None = None
    ) -> dict[str, Any]:
        """Per-block status counts, hard gates, and the radar's raw counts.

        Counts only — the frontend derives any share it wants to draw. Fabricated
        zeros and percentages both stay out, per the Game Distribution honesty
        rules this module inherits.
        """
        slate = self._slate(user_id, belt, today=today)
        syllabus = self.load_syllabus()
        pace_weight = {b["key"]: b.get("pace_weight") for b in syllabus["blocks"]}
        block_labels = {b["key"]: b.get("label") for b in syllabus["blocks"]}

        blocks: dict[str, dict[str, Any]] = {}
        for slot in slate:
            block = blocks.setdefault(
                slot["block"],
                {
                    "block": slot["block"],
                    "label": block_labels.get(slot["block"]),
                    "pace_weight": pace_weight.get(slot["block"]),
                    "slot_count": 0,
                    "declared": 0,
                    "draft": 0,
                    "weak_evidence": 0,
                    "status_counts": {s: 0 for s in STATUS_LADDER},
                    "game_tag_counts": {t: 0 for t in GAME_TAGS},
                    "untagged": 0,
                },
            )
            block["slot_count"] += 1
            block["status_counts"][slot["status"]] += 1
            if slot["declared"]:
                block["declared"] += 1
            if slot["is_draft"]:
                block["draft"] += 1
            if slot["weak_evidence"]:
                block["weak_evidence"] += 1
            tag = slot.get("game_tag")
            if tag in block["game_tag_counts"]:
                block["game_tag_counts"][tag] += 1
            else:
                block["untagged"] += 1

        totals_status = {s: 0 for s in STATUS_LADDER}
        totals_tag = {t: 0 for t in GAME_TAGS}
        untagged = 0
        for block in blocks.values():
            for key, value in block["status_counts"].items():
                totals_status[key] += value
            for key, value in block["game_tag_counts"].items():
                totals_tag[key] += value
            untagged += block["untagged"]

        ordered = [blocks[b["key"]] for b in syllabus["blocks"] if b["key"] in blocks]

        return {
            "belt": belt,
            "hard_gates": self.get_hard_gates(user_id, belt),
            "blocks": ordered,
            "totals": {
                "slot_count": len(slate),
                "declared": sum(1 for s in slate if s["declared"]),
                "draft": sum(1 for s in slate if s["is_draft"]),
                "weak_evidence": sum(1 for s in slate if s["weak_evidence"]),
                "status_counts": totals_status,
                "game_tag_counts": totals_tag,
                "untagged": untagged,
            },
        }

    def _classes_gate(self, user_id: int, meta: dict[str, Any]) -> dict[str, Any]:
        """The classes gate — derived from the log, manual override still wins.

        Derived is the default so the number can never go stale the way a typed
        integer does. ``classes_logged`` survives as an override for when Ruby's
        log and the Academy's record disagree, and ``source`` says which is on
        screen rather than letting the UI imply the wrong one.

        No baseline date means no count: an unanchored total would silently
        include pre-blue training, so the gate stays null and the UI prompts.
        """
        baseline = _as_date(meta.get("blue_promoted_at"))
        override = meta.get("classes_logged")

        if override is not None:
            value: int | None = override
            source = "manual"
        elif baseline is not None:
            value = SessionRepository.count_classes(
                user_id,
                since_date=baseline.isoformat(),
                class_types=MAT_CLASS_TYPES,
            )
            source = "derived"
        else:
            value = None
            source = "unset"

        return {
            "key": "classes",
            "label": "Classes since blue",
            "type": "count",
            "value": value,
            "target": CLASSES_REQUIRED_FOR_PROMOTION,
            "source": source,
            "since": baseline.isoformat() if baseline else None,
            "met": None if value is None else value >= CLASSES_REQUIRED_FOR_PROMOTION,
            "note": (
                "Counted from your logged sessions — not the Academy's official record"
                if source == "derived"
                else "my log — not the Academy's record"
            ),
        }

    def get_hard_gates(
        self, user_id: int, belt: str = DEFAULT_BELT
    ) -> list[dict[str, Any]]:
        """The gates that actually decide the belt, in first-class order."""
        meta = self.repo.get_meta(user_id, belt) or {}
        competition = _as_date(meta.get("competition_date"))
        return [
            {
                "key": "competition",
                "label": "Competition experience",
                "type": "date",
                "value": competition.isoformat() if competition else None,
                "met": competition is not None,
                "note": meta.get("competition_note"),
            },
            self._classes_gate(user_id, meta),
            {
                "key": "stripes",
                "label": "Stripes on blue",
                "type": "count",
                "value": meta.get("stripes"),
                "met": None,
                "note": "awarded at the instructor's discretion",
            },
        ]

    def get_export(
        self, user_id: int, belt: str = DEFAULT_BELT, today: date | None = None
    ) -> dict[str, Any]:
        """The gap-first coach view.

        Hard gates first, then each block with NOT-yet slots ahead of
        in-progress ahead of verified. Deliberately carries no percentage,
        ratio, or completion field of any kind: the coach view opens with what
        Ruby cannot do yet, and a score would invite exactly the reading the
        council ruled out.
        """
        slate = self._slate(user_id, belt, today=today)
        syllabus = self.load_syllabus()
        block_labels = {b["key"]: b.get("label") for b in syllabus["blocks"]}

        buckets: dict[str, dict[str, list[dict]]] = {}
        for slot in slate:
            group = buckets.setdefault(
                slot["block"], {"not_yet": [], "in_progress": [], "verified": []}
            )
            group[self._export_bucket(slot)].append(self._export_slot(slot))

        blocks = []
        for block in syllabus["blocks"]:
            key = block["key"]
            if key not in buckets:
                continue
            group = buckets[key]
            blocks.append(
                {
                    "block": key,
                    "label": block_labels.get(key),
                    "not_yet": group["not_yet"],
                    "in_progress": group["in_progress"],
                    "verified": group["verified"],
                }
            )

        return {
            "belt": belt,
            "generated_on": (today or date.today()).isoformat(),
            "disclaimer": (
                "Promotions are at the instructor's discretion. This is a "
                "training log, not a claim — it has no authority over grading."
            ),
            "hard_gates": self.get_hard_gates(user_id, belt),
            "blocks": blocks,
        }

    @staticmethod
    def _export_bucket(slot: dict) -> str:
        """Which gap-first bucket a slot belongs in.

        A coach's "not yet" or "show me on the mat" outranks the log: if the
        coach said it isn't there, it is a gap however many times it was drilled.
        """
        if slot.get("signoff_verdict") in ("not-yet", "show-me"):
            return "not_yet"
        if slot["status"] == STATUS_COACH_VERIFIED:
            return "verified"
        if slot["status"] == STATUS_NOT_STARTED:
            return "not_yet"
        return "in_progress"

    @staticmethod
    def _export_slot(slot: dict) -> dict[str, Any]:
        """Slot fields the coach view shows. No scores, no percentages."""
        return {
            "id": slot["id"],
            "requirement_key": slot["requirement_key"],
            "requirement_label": slot.get("requirement_label"),
            "slot_index": slot["slot_index"],
            "sequence": {
                "entry": slot.get("seq_entry"),
                "position": slot.get("seq_position"),
                "finish": slot.get("seq_finish"),
            },
            "status": slot["status"],
            "declared": slot["declared"],
            "is_draft": slot["is_draft"],
            "sessions": slot["sessions"],
            "live_occasions": slot["live_occasions"],
            "live_partners": slot["live_partners"],
            "staleness_days": slot["staleness_days"],
            "weak_evidence": slot["weak_evidence"],
            "signoff_verdict": slot["signoff_verdict"],
            "signoff_coach_name": slot.get("signoff_coach_name"),
            "signoff_at": slot.get("signoff_at"),
            "blocker_note": slot.get("blocker_note"),
            "tension_note": slot.get("tension_note"),
        }

    # -------------------------------------------------------------- writes

    def create_slot(self, user_id: int, payload: dict) -> dict[str, Any]:
        """Declare an extra slot (beyond the seeded syllabus shape)."""
        self._validate_declaration(payload)
        slot_id = self.repo.create_slot(user_id, payload)
        slot = self.repo.get_slot(slot_id, user_id)
        if slot is None:
            raise NotFoundError("Slot not found after creation")
        return slot

    def update_slot(self, user_id: int, slot_id: int, payload: dict) -> dict[str, Any]:
        """Edit a slot's declared sequence, tag, or notes.

        Status is not in the accepted field set and never will be.
        """
        if self.repo.get_slot(slot_id, user_id) is None:
            raise NotFoundError(f"Curriculum slot {slot_id} not found")
        self._validate_declaration(payload)
        self.repo.update_slot(slot_id, user_id, payload)
        if (payload.get("seq_finish") or "").strip():
            self.repo.mark_declared(slot_id, user_id, datetime.now().isoformat())
        slot = self.repo.get_slot(slot_id, user_id)
        if slot is None:
            raise NotFoundError(f"Curriculum slot {slot_id} not found")
        return slot

    def add_evidence(self, user_id: int, slot_id: int, payload: dict) -> dict[str, Any]:
        """Log drilled or live evidence against a slot."""
        if self.repo.get_slot(slot_id, user_id) is None:
            raise NotFoundError(f"Curriculum slot {slot_id} not found")

        kind = payload.get("kind")
        if kind not in EVIDENCE_KINDS:
            raise ValidationError(f"kind must be one of {', '.join(EVIDENCE_KINDS)}")

        band = payload.get("partner_rank_band")
        if band is not None and band not in PARTNER_RANK_BANDS:
            raise ValidationError(
                f"partner_rank_band must be one of {', '.join(PARTNER_RANK_BANDS)}"
            )
        size = payload.get("partner_size")
        if size is not None and size not in PARTNER_SIZES:
            raise ValidationError(
                f"partner_size must be one of {', '.join(PARTNER_SIZES)}"
            )

        data = dict(payload)
        data.setdefault("logged_at", date.today().isoformat())
        evidence_id = self.repo.create_evidence(user_id, slot_id, data)
        return {
            "id": evidence_id,
            "slot_id": slot_id,
            **self.get_slot_state(user_id, slot_id),
        }

    def add_signoff(self, user_id: int, slot_id: int, payload: dict) -> dict[str, Any]:
        """Record a coach sign-off. Create-only — there is no edit path.

        The row is an attributed record of what a coach said on a given day. If
        the verdict changes, the coach gives a new sign-off and both stay in the
        history; the latest one drives status.
        """
        if self.repo.get_slot(slot_id, user_id) is None:
            raise NotFoundError(f"Curriculum slot {slot_id} not found")

        verdict = payload.get("verdict")
        if verdict not in SIGNOFF_VERDICTS:
            raise ValidationError(
                f"verdict must be one of {', '.join(SIGNOFF_VERDICTS)}"
            )
        if not (payload.get("coach_name") or "").strip():
            raise ValidationError("coach_name is required — sign-offs are attributed")

        signoff_id = self.repo.create_signoff(user_id, slot_id, payload)
        return {
            "id": signoff_id,
            "slot_id": slot_id,
            **self.get_slot_state(user_id, slot_id),
        }

    def derive_evidence_candidates(
        self, user_id: int, session_id: int, belt: str = DEFAULT_BELT
    ) -> dict[str, Any]:
        """One-tap evidence candidates for a logged session (Wave 3, MA-F1).

        Matches the session's techniques and roll submissions against the
        slate's seq_finish names (folded, glossary-alias-aware — the seeded
        slate carries sequence TEXT, not movement_ids). Technique work → a
        'drilled' candidate; a roll submission → a 'live' candidate carrying
        the roll's partner name as partner_ref (MA-F6). Candidates only —
        evidence stays human-confirmed via POST /slots/{id}/evidence, and
        slots already evidenced from THIS session are excluded (idempotent).
        """
        from rivaflow.core.services.grapple.session_extraction_service import (
            _fold,
        )
        from rivaflow.db.repositories import GlossaryRepository
        from rivaflow.db.repositories.session_roll_repo import (
            SessionRollRepository,
        )
        from rivaflow.db.repositories.session_technique_repo import (
            SessionTechniqueRepository,
        )

        # Session side: movement ids from logged techniques + roll submissions.
        techniques = SessionTechniqueRepository.get_by_session_id(user_id, session_id)
        rolls = SessionRollRepository.get_by_session_id(user_id, session_id)
        drilled_ids = {
            t["movement_id"] for t in techniques if t.get("movement_id") is not None
        }
        live_hits: dict[int, str | None] = {}  # movement_id -> partner name
        for roll in rolls:
            for mid in roll.get("submissions_for") or []:
                if isinstance(mid, int) and mid not in live_hits:
                    live_hits[mid] = roll.get("partner_name")
        if not drilled_ids and not live_hits:
            return {"session_id": session_id, "candidates": []}

        # Folded name keys (name + aliases) for every session movement.
        glossary = {m["id"]: m for m in GlossaryRepository.list_all()}

        def keys_for(mid: int) -> set[str]:
            m = glossary.get(mid)
            if not m:
                return set()
            keys = {_fold(m["name"])}
            raw = m.get("aliases")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except (ValueError, TypeError):
                    raw = []
            keys.update(_fold(str(a)) for a in raw or [])
            return keys

        drilled_keys = {k: mid for mid in drilled_ids for k in keys_for(mid)}
        live_keys = {k: mid for mid in live_hits for k in keys_for(mid)}

        # Slots already evidenced from this session (idempotent re-display).
        evidenced_slots = {
            e["slot_id"]
            for e in self.repo.list_evidence(user_id, belt)
            if e.get("session_id") == session_id
        }

        candidates = []
        for slot in self.repo.list_slots(user_id, belt):
            if slot["id"] in evidenced_slots:
                continue
            finish_key = _fold(slot.get("seq_finish") or "")
            if not finish_key:
                continue
            matched_live = live_keys.get(finish_key)
            matched_drilled = drilled_keys.get(finish_key)
            if matched_live is not None:
                kind, mid = "live", matched_live
                partner = live_hits.get(mid)
            elif matched_drilled is not None:
                kind, mid = "drilled", matched_drilled
                partner = None
            else:
                continue
            candidates.append(
                {
                    "slot_id": slot["id"],
                    "block": slot.get("block"),
                    "label": slot.get("requirement_label") or slot.get("seq_finish"),
                    "sequence": " → ".join(
                        p
                        for p in (
                            slot.get("seq_entry"),
                            slot.get("seq_position"),
                            slot.get("seq_finish"),
                        )
                        if p
                    ),
                    "kind": kind,
                    "matched_movement": glossary.get(mid, {}).get("name"),
                    "partner_ref": partner,
                    "session_id": session_id,
                }
            )

        return {"session_id": session_id, "candidates": candidates}

    def get_slot_state(
        self, user_id: int, slot_id: int, belt: str = DEFAULT_BELT
    ) -> dict[str, Any]:
        """Recompute one slot's derived state after a write."""
        evidence = [
            e for e in self.repo.list_evidence(user_id, belt) if e["slot_id"] == slot_id
        ]
        signoffs = [
            s for s in self.repo.list_signoffs(user_id, belt) if s["slot_id"] == slot_id
        ]
        return compute_slot_state(evidence, signoffs)

    def upsert_meta(
        self, user_id: int, payload: dict, belt: str = DEFAULT_BELT
    ) -> list[dict[str, Any]]:
        """Set the hard gates (competition date, class count, stripes, notes)."""
        self.repo.upsert_meta(user_id, belt, payload)
        return self.get_hard_gates(user_id, belt)

    @staticmethod
    def _validate_declaration(payload: dict) -> None:
        """Reject bad tags early, and reject any attempt to set status."""
        if "status" in payload:
            raise ValidationError(
                "status is derived from evidence and sign-offs — it cannot be set"
            )
        tag = payload.get("game_tag")
        if tag is not None and tag not in GAME_TAGS:
            raise ValidationError(f"game_tag must be one of {', '.join(GAME_TAGS)}")

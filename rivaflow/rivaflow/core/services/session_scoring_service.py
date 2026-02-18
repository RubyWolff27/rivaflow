"""Session performance scoring engine (0-100 scale).

Calculates a composite score across multiple pillars to reflect session
quality, rewarding smart training that aligns effort with recovery state.
"""

import logging
from datetime import date

from rivaflow.core.constants import SPARRING_CLASS_TYPES
from rivaflow.db.repositories.readiness_repo import ReadinessRepository
from rivaflow.db.repositories.session_repo import SessionRepository

logger = logging.getLogger(__name__)

SCORE_VERSION = 1

# --- Tier labels -----------------------------------------------------------

TIERS = [
    (85, "Peak"),
    (70, "Excellent"),
    (50, "Strong"),
    (30, "Solid"),
    (0, "Light"),
]


def _tier_label(score: float) -> str:
    for threshold, label in TIERS:
        if score >= threshold:
            return label
    return "Light"


# --- Weight definitions -----------------------------------------------------

BJJ_WEIGHTS = {
    "effort": 25,
    "engagement": 25,
    "effectiveness": 20,
    "readiness_alignment": 15,
    "biometric_validation": 15,
}

COMPETITION_WEIGHTS = {
    "effort": 15,
    "engagement": 15,
    "effectiveness": 35,
    "readiness_alignment": 15,
    "biometric_validation": 20,
}

SUPPLEMENTARY_WEIGHTS = {
    "effort": 40,
    "consistency": 30,
    "readiness_alignment": 15,
    "biometric_validation": 15,
}


class SessionScoringService:
    """Calculate and persist session performance scores."""

    def __init__(self):
        self.session_repo = SessionRepository()

    # --- Public API ---------------------------------------------------------

    def score_session(self, user_id: int, session_id: int) -> dict | None:
        """Calculate and store a score for one session.  Returns breakdown."""
        session = self.session_repo.get_by_id(user_id, session_id)
        if not session:
            return None

        breakdown = self._calculate(user_id, session)
        self._persist(user_id, session_id, breakdown)
        return breakdown

    def recalculate_session(self, user_id: int, session_id: int) -> dict | None:
        """Force recalculate a session score."""
        return self.score_session(user_id, session_id)

    def backfill_user_scores(self, user_id: int) -> dict:
        """Score all unscored sessions for a user.  Returns summary."""
        sessions = self.session_repo.list_by_user(user_id)
        scored = 0
        skipped = 0
        for s in sessions:
            if s.get("session_score") is not None:
                skipped += 1
                continue
            try:
                self.score_session(user_id, s["id"])
                scored += 1
            except Exception:
                logger.warning("Failed to score session %s", s["id"], exc_info=True)
        return {"scored": scored, "skipped": skipped, "total": len(sessions)}

    # --- Internal -----------------------------------------------------------

    def _calculate(self, user_id: int, session: dict) -> dict:
        class_type = session.get("class_type", "")
        if class_type == "competition":
            return self._score_competition(user_id, session)
        elif class_type in SPARRING_CLASS_TYPES:
            return self._score_bjj(user_id, session)
        else:
            return self._score_supplementary(user_id, session)

    # --- BJJ scoring --------------------------------------------------------

    def _score_bjj(self, user_id: int, session: dict) -> dict:
        avgs = self._get_user_averages(user_id)
        readiness = self._get_readiness_for_date(user_id, session)
        has_whoop = self._has_whoop_data(session)
        has_readiness = readiness is not None

        available = dict(BJJ_WEIGHTS)
        if not has_readiness:
            del available["readiness_alignment"]
        if not has_whoop:
            del available["biometric_validation"]

        weights = self._redistribute_weights(available, 100)

        pillars = {}

        # Effort (intensity + duration relative to personal averages)
        pillars["effort"] = self._calc_effort(session, avgs, weights["effort"])

        # Engagement (rolls + partner variety + technique variety)
        pillars["engagement"] = self._calc_engagement(
            session, avgs, weights["engagement"]
        )

        # Effectiveness (sub ratio + attack/defense success)
        pillars["effectiveness"] = self._calc_effectiveness(
            session, weights["effectiveness"]
        )

        # Readiness alignment
        if has_readiness:
            pillars["readiness_alignment"] = self._calc_readiness_alignment(
                session, readiness, weights["readiness_alignment"]
            )

        # Biometric validation
        if has_whoop:
            pillars["biometric_validation"] = self._calc_biometric(
                session, avgs, weights["biometric_validation"]
            )

        total = round(sum(p["score"] for p in pillars.values()), 1)
        data_completeness = len(pillars) / len(BJJ_WEIGHTS)

        return {
            "version": SCORE_VERSION,
            "rubric": "bjj",
            "total": total,
            "label": _tier_label(total),
            "pillars": pillars,
            "data_completeness": round(data_completeness, 2),
        }

    # --- Competition scoring ------------------------------------------------

    def _score_competition(self, user_id: int, session: dict) -> dict:
        avgs = self._get_user_averages(user_id)
        readiness = self._get_readiness_for_date(user_id, session)
        has_whoop = self._has_whoop_data(session)
        has_readiness = readiness is not None

        available = dict(COMPETITION_WEIGHTS)
        if not has_readiness:
            del available["readiness_alignment"]
        if not has_whoop:
            del available["biometric_validation"]

        weights = self._redistribute_weights(available, 100)
        pillars = {}

        pillars["effort"] = self._calc_effort(session, avgs, weights["effort"])
        pillars["engagement"] = self._calc_engagement(
            session, avgs, weights["engagement"]
        )
        pillars["effectiveness"] = self._calc_effectiveness(
            session, weights["effectiveness"]
        )
        if has_readiness:
            pillars["readiness_alignment"] = self._calc_readiness_alignment(
                session, readiness, weights["readiness_alignment"]
            )
        if has_whoop:
            pillars["biometric_validation"] = self._calc_biometric(
                session, avgs, weights["biometric_validation"]
            )

        total = round(sum(p["score"] for p in pillars.values()), 1)
        data_completeness = len(pillars) / len(COMPETITION_WEIGHTS)

        return {
            "version": SCORE_VERSION,
            "rubric": "competition",
            "total": total,
            "label": _tier_label(total),
            "pillars": pillars,
            "data_completeness": round(data_completeness, 2),
        }

    # --- Supplementary scoring (S&C / Cardio / Mobility) --------------------

    def _score_supplementary(self, user_id: int, session: dict) -> dict:
        avgs = self._get_user_averages(user_id)
        readiness = self._get_readiness_for_date(user_id, session)
        has_whoop = self._has_whoop_data(session)
        has_readiness = readiness is not None

        available = dict(SUPPLEMENTARY_WEIGHTS)
        if not has_readiness:
            del available["readiness_alignment"]
        if not has_whoop:
            del available["biometric_validation"]

        weights = self._redistribute_weights(available, 100)
        pillars = {}

        pillars["effort"] = self._calc_effort(session, avgs, weights["effort"])
        pillars["consistency"] = self._calc_consistency(
            session, avgs, weights["consistency"]
        )
        if has_readiness:
            pillars["readiness_alignment"] = self._calc_readiness_alignment(
                session, readiness, weights["readiness_alignment"]
            )
        if has_whoop:
            pillars["biometric_validation"] = self._calc_biometric(
                session, avgs, weights["biometric_validation"]
            )

        total = round(sum(p["score"] for p in pillars.values()), 1)
        data_completeness = len(pillars) / len(SUPPLEMENTARY_WEIGHTS)

        return {
            "version": SCORE_VERSION,
            "rubric": "supplementary",
            "total": total,
            "label": _tier_label(total),
            "pillars": pillars,
            "data_completeness": round(data_completeness, 2),
        }

    # --- Pillar calculators -------------------------------------------------

    def _calc_effort(self, session: dict, avgs: dict, max_pts: float) -> dict:
        """Intensity (1-5) + duration relative to personal averages."""
        intensity = session.get("intensity", 3)
        duration = session.get("duration_mins", 60)
        avg_duration = avgs.get("avg_duration", 60) or 60

        # Intensity component (60% of effort)
        intensity_pct = min(intensity / 5.0, 1.0)

        # Duration component (40% of effort) — ratio vs personal avg, capped
        duration_ratio = min(duration / avg_duration, 1.5) / 1.5

        pct = intensity_pct * 0.6 + duration_ratio * 0.4
        score = round(pct * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(pct * 100)}

    def _calc_engagement(self, session: dict, avgs: dict, max_pts: float) -> dict:
        """Rolls count + partner variety + technique variety."""
        rolls = session.get("rolls", 0)
        partners = session.get("partners") or []
        techniques = session.get("techniques") or []
        avg_rolls = avgs.get("avg_rolls", 5) or 5

        # Rolls component (40%)
        rolls_ratio = min(rolls / max(avg_rolls, 1), 1.5) / 1.5
        if rolls == 0:
            rolls_ratio = 0.2  # Minimum credit for showing up

        # Partner variety (30%)
        partner_count = len(partners)
        partner_pct = min(partner_count / 4.0, 1.0)  # 4+ partners = max

        # Technique variety (30%)
        tech_count = len(techniques)
        tech_pct = min(tech_count / 3.0, 1.0)  # 3+ techniques = max

        pct = rolls_ratio * 0.4 + partner_pct * 0.3 + tech_pct * 0.3
        score = round(pct * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(pct * 100)}

    def _calc_effectiveness(self, session: dict, max_pts: float) -> dict:
        """Sub ratio + attack/defense success rates."""
        subs_for = session.get("submissions_for", 0)
        subs_against = session.get("submissions_against", 0)
        attacks_att = session.get("attacks_attempted", 0)
        attacks_suc = session.get("attacks_successful", 0)
        defenses_att = session.get("defenses_attempted", 0)
        defenses_suc = session.get("defenses_successful", 0)

        total_subs = subs_for + subs_against

        # Sub ratio (40%)
        if total_subs > 0:
            sub_ratio_pct = subs_for / total_subs
        elif subs_for > 0:
            sub_ratio_pct = 1.0
        else:
            sub_ratio_pct = 0.5  # No data = neutral

        # Attack success rate (30%)
        if attacks_att > 0:
            attack_pct = attacks_suc / attacks_att
        else:
            attack_pct = 0.5  # No data = neutral

        # Defense success rate (30%)
        if defenses_att > 0:
            defense_pct = defenses_suc / defenses_att
        else:
            defense_pct = 0.5  # No data = neutral

        pct = sub_ratio_pct * 0.4 + attack_pct * 0.3 + defense_pct * 0.3
        score = round(pct * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(pct * 100)}

    def _calc_readiness_alignment(
        self, session: dict, readiness: dict, max_pts: float
    ) -> dict:
        """Reward smart training: match effort to recovery state."""
        composite = readiness.get("composite_score", 12)
        intensity = session.get("intensity", 3)

        # Normalise composite (4-20) to 0-1
        recovery_pct = max(0, min((composite - 4) / 16.0, 1.0))

        # Classify recovery zone
        if recovery_pct >= 0.67:
            zone = "green"
        elif recovery_pct >= 0.34:
            zone = "yellow"
        else:
            zone = "red"

        intensity_norm = intensity / 5.0

        # Smart training logic
        if zone == "green" and intensity_norm >= 0.6:
            alignment = 1.0  # High recovery + high effort = great
        elif zone == "green" and intensity_norm < 0.4:
            alignment = 0.5  # High recovery + low effort = missed opportunity
        elif zone == "red" and intensity_norm <= 0.4:
            alignment = 0.9  # Low recovery + low effort = smart rest
        elif zone == "red" and intensity_norm >= 0.6:
            alignment = 0.2  # Low recovery + high effort = overtraining risk
        elif zone == "yellow":
            alignment = 0.6 + (0.2 * (1.0 - abs(intensity_norm - 0.5) * 2))
        else:
            alignment = 0.6  # Moderate default

        score = round(alignment * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(alignment * 100)}

    def _calc_biometric(self, session: dict, avgs: dict, max_pts: float) -> dict:
        """WHOOP strain + HR zones confirm real effort."""
        strain = session.get("whoop_strain") or 0
        avg_hr = session.get("whoop_avg_hr") or 0
        intensity = session.get("intensity", 3)

        components = []

        # Strain component (50%) — scale 0-21
        if strain > 0:
            strain_pct = min(strain / 15.0, 1.0)  # 15+ strain = max
            components.append(("strain", strain_pct, 0.5))
        else:
            components.append(("strain", 0.5, 0.5))

        # HR consistency with reported intensity (50%)
        if avg_hr > 0:
            # Higher HR should correlate with higher intensity
            # Approximate: 120-180 bpm range mapped to intensity 1-5
            expected_hr = 110 + (intensity * 14)
            hr_diff = abs(avg_hr - expected_hr)
            hr_consistency = max(0, 1.0 - (hr_diff / 50.0))
            components.append(("hr", hr_consistency, 0.5))
        else:
            components.append(("hr", 0.5, 0.5))

        total_weight = sum(c[2] for c in components)
        pct = sum(c[1] * c[2] for c in components) / total_weight
        score = round(pct * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(pct * 100)}

    def _calc_consistency(self, session: dict, avgs: dict, max_pts: float) -> dict:
        """For supplementary sessions: showing up + reasonable duration."""
        duration = session.get("duration_mins", 30)

        # Reasonable duration for supplementary (30-90 mins ideal)
        if 30 <= duration <= 90:
            duration_pct = 1.0
        elif duration < 30:
            duration_pct = duration / 30.0
        else:
            duration_pct = max(0.7, 1.0 - (duration - 90) / 120.0)

        # Credit for logging the session at all
        base_credit = 0.3
        pct = base_credit + (1 - base_credit) * duration_pct
        score = round(pct * max_pts, 1)
        return {"score": score, "max": max_pts, "pct": round(pct * 100)}

    # --- Helpers ------------------------------------------------------------

    def _redistribute_weights(
        self, available: dict[str, int], target: int
    ) -> dict[str, float]:
        """Scale available pillar weights proportionally to sum to target."""
        current_total = sum(available.values())
        if current_total == 0:
            return {k: 0 for k in available}
        factor = target / current_total
        return {k: round(v * factor, 1) for k, v in available.items()}

    def _get_user_averages(self, user_id: int) -> dict:
        """Get last-30-session averages for normalisation."""
        return SessionRepository.get_user_averages(user_id)

    def _get_readiness_for_date(self, user_id: int, session: dict) -> dict | None:
        """Fetch readiness check-in for the session date."""
        session_date = session.get("session_date")
        if not session_date:
            return None
        if isinstance(session_date, date):
            date_str = session_date.isoformat()
        else:
            date_str = str(session_date)[:10]

        return ReadinessRepository.get_readiness_with_composite(user_id, date_str)

    def _has_whoop_data(self, session: dict) -> bool:
        return bool(
            session.get("whoop_strain")
            or session.get("whoop_avg_hr")
            or session.get("whoop_max_hr")
        )

    def _persist(self, user_id: int, session_id: int, breakdown: dict) -> None:
        """Write score + breakdown to the session row."""
        self.session_repo.update(
            user_id=user_id,
            session_id=session_id,
            session_score=breakdown["total"],
            score_breakdown=breakdown,
            score_version=SCORE_VERSION,
        )

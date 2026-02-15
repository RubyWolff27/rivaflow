import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  parseTimeToday,
  computeSmartStatus,
} from "../components/dashboard/DailyActionHero";
import type { Session, WeeklyGoalProgress } from "../types";
import type { GymClass } from "../api/client";

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

/** Build a minimal Session stub. Fields not relevant to computeSmartStatus
 *  are filled with sensible defaults. */
function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    id: 1,
    session_date: "2026-02-15",
    class_type: "gi",
    gym_name: "Alliance Drummoyne",
    duration_mins: 60,
    intensity: 3,
    rolls: 4,
    submissions_for: 1,
    submissions_against: 0,
    created_at: "2026-02-15T10:00:00Z",
    ...overrides,
  };
}

/** Build a minimal GymClass stub. */
function makeGymClass(overrides: Partial<GymClass> = {}): GymClass {
  return {
    id: 1,
    gym_id: 1,
    day_of_week: 6,
    day_name: "Saturday",
    start_time: "9:00",
    end_time: "10:00",
    class_name: "Fundamentals",
    class_type: "gi",
    level: "all",
    is_active: 1,
    ...overrides,
  };
}

/** Build a WeeklyGoalProgress stub. */
function makeGoals(
  overrides: Partial<WeeklyGoalProgress> = {},
): WeeklyGoalProgress {
  return {
    week_start: "2026-02-09",
    week_end: "2026-02-15",
    targets: { sessions: 4, hours: 6, rolls: 20 },
    actual: { sessions: 2, hours: 3, rolls: 10 },
    progress: {
      sessions_pct: 50,
      hours_pct: 50,
      rolls_pct: 50,
      overall_pct: 50,
    },
    completed: false,
    days_remaining: 3,
    ...overrides,
  };
}

/* ------------------------------------------------------------------ */
/*  parseTimeToday                                                     */
/* ------------------------------------------------------------------ */

describe("parseTimeToday", () => {
  it('parses "9:00" correctly', () => {
    const result = parseTimeToday("9:00");
    expect(result.getHours()).toBe(9);
    expect(result.getMinutes()).toBe(0);
    expect(result.getSeconds()).toBe(0);
  });

  it('parses "14:30" correctly', () => {
    const result = parseTimeToday("14:30");
    expect(result.getHours()).toBe(14);
    expect(result.getMinutes()).toBe(30);
    expect(result.getSeconds()).toBe(0);
  });

  it('handles midnight "0:00"', () => {
    const result = parseTimeToday("0:00");
    expect(result.getHours()).toBe(0);
    expect(result.getMinutes()).toBe(0);
    expect(result.getSeconds()).toBe(0);
  });

  it('handles "23:59"', () => {
    const result = parseTimeToday("23:59");
    expect(result.getHours()).toBe(23);
    expect(result.getMinutes()).toBe(59);
    expect(result.getSeconds()).toBe(0);
  });

  it('handles time with seconds "14:30:45"', () => {
    const result = parseTimeToday("14:30:45");
    expect(result.getHours()).toBe(14);
    expect(result.getMinutes()).toBe(30);
    expect(result.getSeconds()).toBe(45);
  });

  it("returns a Date set to today", () => {
    const today = new Date();
    const result = parseTimeToday("12:00");
    expect(result.getFullYear()).toBe(today.getFullYear());
    expect(result.getMonth()).toBe(today.getMonth());
    expect(result.getDate()).toBe(today.getDate());
  });
});

/* ------------------------------------------------------------------ */
/*  computeSmartStatus                                                 */
/* ------------------------------------------------------------------ */

describe("computeSmartStatus", () => {
  beforeEach(() => {
    // Fix "now" to 2026-02-15 11:00:00 local time for deterministic tests
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 1, 15, 11, 0, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  /* ---- P1: trained-as-planned ---- */
  describe("P1 — trained-as-planned", () => {
    it("returns trained-planned when session matches an ended gym class", () => {
      // Class 9:00-10:00 has ended (now=11:00), session class_type matches
      const sessions = [makeSession({ class_type: "gi" })];
      const classes = [
        makeGymClass({ start_time: "9:00", end_time: "10:00", class_type: "gi" }),
      ];
      const result = computeSmartStatus(undefined, sessions, classes, null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("trained-planned");
      expect(result!.icon).toBe("check");
      expect(result!.showLogButton).toBe(false);
    });

    it("matches when gym class has null class_type (wildcard)", () => {
      // A class with class_type=null should match any session
      const sessions = [makeSession({ class_type: "no-gi" })];
      const classes = [
        makeGymClass({
          start_time: "9:00",
          end_time: "10:00",
          class_type: null,
        }),
      ];
      const result = computeSmartStatus(undefined, sessions, classes, null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("trained-planned");
    });

    it("does NOT match if class has not ended yet (30 min buffer)", () => {
      // Class 10:35-11:25: end_time - 30min = 10:55, now=11:00 => 11:00 >= 10:55, matches
      // But class 11:00-12:00: end_time - 30min = 11:30, now=11:00 => 11:00 < 11:30, does NOT match
      const sessions = [makeSession({ class_type: "gi" })];
      const classes = [
        makeGymClass({
          start_time: "11:00",
          end_time: "12:00",
          class_type: "gi",
        }),
      ];
      const result = computeSmartStatus(undefined, sessions, classes, null);

      // Since the class hasn't ended (now < endTime - 30min), P1 won't match.
      // But P3 checks for upcoming within 4hrs where start is in the future,
      // and start=11:00 = now so diffMs=0 which is not > 0. Falls through.
      // The class end_time (12:00) is in the future, so allPast is false for P5.
      // No goals, no intention => null (hidden)
      // Actually wait: sessions exist, so P2 (trained) will match
      expect(result).not.toBeNull();
      expect(result!.type).toBe("trained");
    });
  });

  /* ---- P2: session-logged ---- */
  describe("P2 — session-logged", () => {
    it("returns trained when sessions exist but no gym classes", () => {
      const sessions = [makeSession()];
      const result = computeSmartStatus(undefined, sessions, [], null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("trained");
      expect(result!.headline).toBe("Session logged — nice work!");
      expect(result!.icon).toBe("check");
      expect(result!.showLogButton).toBe(false);
    });

    it("returns trained when session class_type does not match any ended class", () => {
      // Class is gi, session is no-gi, class has ended
      const sessions = [makeSession({ class_type: "no-gi" })];
      const classes = [
        makeGymClass({
          start_time: "9:00",
          end_time: "10:00",
          class_type: "gi",
        }),
      ];
      const result = computeSmartStatus(undefined, sessions, classes, null);

      // P1: check matchedEnded — class ended, but session class_type "no-gi" !== "gi"
      // c.class_type is "gi" (not null), so it checks s.class_type === c.class_type
      // "no-gi" !== "gi" => no match => P1 fails
      // P2: hasSession is true => returns "trained"
      expect(result).not.toBeNull();
      expect(result!.type).toBe("trained");
    });
  });

  /* ---- P3: upcoming-class ---- */
  describe("P3 — upcoming-class", () => {
    it("returns upcoming when a class starts within 4 hours", () => {
      // Now=11:00, class starts at 14:00 (3 hours away, within 4hr window)
      const classes = [
        makeGymClass({
          start_time: "14:00",
          end_time: "15:00",
          class_name: "Advanced No-Gi",
          class_type: "no-gi",
        }),
      ];
      const result = computeSmartStatus(undefined, [], classes, null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("upcoming");
      expect(result!.headline).toContain("Next:");
      expect(result!.headline).toContain("No-Gi");
      expect(result!.subtext).toBe("Advanced No-Gi");
      expect(result!.icon).toBe("clock");
      expect(result!.showLogButton).toBe(false);
    });

    it("picks the earliest upcoming class when multiple exist", () => {
      const classes = [
        makeGymClass({
          id: 2,
          start_time: "14:00",
          end_time: "15:00",
          class_name: "Later Class",
          class_type: "no-gi",
        }),
        makeGymClass({
          id: 1,
          start_time: "12:00",
          end_time: "13:00",
          class_name: "Earlier Class",
          class_type: "gi",
        }),
      ];
      const result = computeSmartStatus(undefined, [], classes, null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("upcoming");
      expect(result!.subtext).toBe("Earlier Class");
    });

    it("does NOT return upcoming if class start is more than 4 hours away", () => {
      // Now=11:00, class at 16:00 (5 hours away)
      const classes = [
        makeGymClass({
          start_time: "16:00",
          end_time: "17:00",
        }),
      ];
      const result = computeSmartStatus(undefined, [], classes, null);

      // Not upcoming (too far), not past yet (end_time 17:00 > 11:00), no goals, no intention
      // => null (hidden)
      expect(result).toBeNull();
    });

    it("does NOT return upcoming if class start is in the past", () => {
      // Now=11:00, class started at 10:00, ends at 11:30 (still ongoing)
      const classes = [
        makeGymClass({
          start_time: "10:00",
          end_time: "11:30",
        }),
      ];
      const result = computeSmartStatus(undefined, [], classes, null);

      // P3: start=10:00, diffMs < 0, not upcoming
      // P5: end_time=11:30 > now=11:00, not allPast
      // => null
      expect(result).toBeNull();
    });
  });

  /* ---- P4: goal-nudge ---- */
  describe("P4 — goal-nudge", () => {
    it("returns goal-nudge when behind on S&C sessions with <=4 days remaining", () => {
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, sc_sessions: 2 },
        actual: { sessions: 2, hours: 3, rolls: 10, sc_sessions: 0 },
        days_remaining: 3,
      });
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("goal-nudge");
      expect(result!.headline).toContain("S&C");
      expect(result!.headline).toContain("2");
      expect(result!.subtext).toContain("3 days remaining");
      expect(result!.icon).toBe("alert");
      expect(result!.showLogButton).toBe(true);
    });

    it("returns goal-nudge for BJJ sessions gap", () => {
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, bjj_sessions: 3 },
        actual: { sessions: 1, hours: 2, rolls: 5, bjj_sessions: 1 },
        days_remaining: 2,
      });
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("goal-nudge");
      expect(result!.headline).toContain("BJJ");
      expect(result!.headline).toContain("2");
      expect(result!.subtext).toContain("2 days remaining");
    });

    it("returns goal-nudge for mobility sessions gap", () => {
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, mobility_sessions: 2 },
        actual: { sessions: 2, hours: 3, rolls: 10, mobility_sessions: 0 },
        days_remaining: 1,
      });
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("goal-nudge");
      expect(result!.headline).toContain("mobility");
      expect(result!.subtext).toContain("1 day remaining");
    });

    it("does NOT return goal-nudge when days_remaining > 4", () => {
      const goals = makeGoals({ days_remaining: 5 });
      const result = computeSmartStatus(undefined, [], [], goals);

      // days_remaining=5 > 4, so P4 is skipped => null
      expect(result).toBeNull();
    });

    it("does NOT return goal-nudge when no target gaps exist", () => {
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20 },
        actual: { sessions: 4, hours: 6, rolls: 20 },
        days_remaining: 2,
      });
      // No sc_sessions, mobility_sessions, or bjj_sessions targets defined
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).toBeNull();
    });

    it("does NOT return goal-nudge when all targets are met", () => {
      const goals = makeGoals({
        targets: {
          sessions: 4,
          hours: 6,
          rolls: 20,
          sc_sessions: 2,
          bjj_sessions: 3,
          mobility_sessions: 1,
        },
        actual: {
          sessions: 4,
          hours: 6,
          rolls: 20,
          sc_sessions: 3,
          bjj_sessions: 4,
          mobility_sessions: 2,
        },
        days_remaining: 1,
      });
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).toBeNull();
    });
  });

  /* ---- P5: missed-class ---- */
  describe("P5 — missed-class", () => {
    it("returns missed when all classes are past and no sessions logged", () => {
      const classes = [
        makeGymClass({ start_time: "7:00", end_time: "8:00" }),
        makeGymClass({
          id: 2,
          start_time: "9:00",
          end_time: "10:00",
        }),
      ];
      // Now=11:00, both classes ended
      const result = computeSmartStatus(undefined, [], classes, null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("missed");
      expect(result!.headline).toContain("Missed");
      expect(result!.icon).toBe("calendar");
      expect(result!.showLogButton).toBe(false);
    });

    it("does NOT return missed if any class has not ended yet", () => {
      const classes = [
        makeGymClass({ start_time: "7:00", end_time: "8:00" }),
        makeGymClass({
          id: 2,
          start_time: "10:30",
          end_time: "11:30",
        }),
      ];
      // Now=11:00, second class ends at 11:30 which is still in the future
      // P3: start_time=10:30, diffMs < 0 (in the past), so not upcoming
      // P5: not allPast (11:30 > 11:00)
      const result = computeSmartStatus(undefined, [], classes, null);

      // Falls through to P6 (no intention) => null
      expect(result).toBeNull();
    });
  });

  /* ---- P6: intention ---- */
  describe("P6 — intention", () => {
    it("returns intention when a plan string is provided", () => {
      const result = computeSmartStatus(
        "BJJ No-Gi at 17:30",
        [],
        [],
        null,
      );

      expect(result).not.toBeNull();
      expect(result!.type).toBe("intention");
      expect(result!.headline).toBe("BJJ No-Gi at 17:30");
      expect(result!.subtext).toBe("Your plan today");
      expect(result!.icon).toBe("calendar");
      expect(result!.showLogButton).toBe(true);
    });

    it("returns intention even with empty classes and no goals", () => {
      const result = computeSmartStatus("Rest and stretch", [], [], null);

      expect(result).not.toBeNull();
      expect(result!.type).toBe("intention");
      expect(result!.headline).toBe("Rest and stretch");
    });
  });

  /* ---- P7: hidden (null) ---- */
  describe("P7 — hidden", () => {
    it("returns null when no sessions, no classes, no goals behind, no intention", () => {
      const result = computeSmartStatus(undefined, [], [], null);

      expect(result).toBeNull();
    });

    it("returns null with empty intention string", () => {
      // Empty string is falsy
      const result = computeSmartStatus("", [], [], null);

      expect(result).toBeNull();
    });

    it("returns null when goals exist but days_remaining > 4", () => {
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, sc_sessions: 2 },
        actual: { sessions: 0, hours: 0, rolls: 0, sc_sessions: 0 },
        days_remaining: 5,
      });
      const result = computeSmartStatus(undefined, [], [], goals);

      expect(result).toBeNull();
    });

    it("returns null when future classes exist but are more than 4 hours away", () => {
      const classes = [
        makeGymClass({ start_time: "18:00", end_time: "19:00" }),
      ];
      // Now=11:00, class at 18:00 is 7 hours away
      const result = computeSmartStatus(undefined, [], classes, null);

      // Not upcoming (>4hrs), not all past => falls through to null
      expect(result).toBeNull();
    });
  });

  /* ---- Priority ordering ---- */
  describe("priority ordering", () => {
    it("trained-as-planned (P1) takes precedence over goal-nudge (P4)", () => {
      const sessions = [makeSession({ class_type: "gi" })];
      const classes = [
        makeGymClass({
          start_time: "9:00",
          end_time: "10:00",
          class_type: "gi",
        }),
      ];
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, sc_sessions: 3 },
        actual: { sessions: 1, hours: 1, rolls: 2, sc_sessions: 0 },
        days_remaining: 1,
      });

      const result = computeSmartStatus(undefined, sessions, classes, goals);
      expect(result!.type).toBe("trained-planned");
    });

    it("session-logged (P2) takes precedence over intention (P6)", () => {
      const sessions = [makeSession()];
      const result = computeSmartStatus(
        "Train BJJ Gi",
        sessions,
        [],
        null,
      );

      expect(result!.type).toBe("trained");
    });

    it("upcoming-class (P3) takes precedence over goal-nudge (P4)", () => {
      const classes = [
        makeGymClass({
          start_time: "14:00",
          end_time: "15:00",
          class_type: "gi",
        }),
      ];
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, bjj_sessions: 3 },
        actual: { sessions: 0, hours: 0, rolls: 0, bjj_sessions: 0 },
        days_remaining: 2,
      });

      const result = computeSmartStatus(undefined, [], classes, goals);
      expect(result!.type).toBe("upcoming");
    });

    it("goal-nudge (P4) takes precedence over missed-class (P5)", () => {
      // All classes past AND goals behind
      const classes = [
        makeGymClass({ start_time: "7:00", end_time: "8:00" }),
      ];
      const goals = makeGoals({
        targets: { sessions: 4, hours: 6, rolls: 20, sc_sessions: 2 },
        actual: { sessions: 0, hours: 0, rolls: 0, sc_sessions: 0 },
        days_remaining: 2,
      });

      const result = computeSmartStatus(undefined, [], classes, goals);
      expect(result!.type).toBe("goal-nudge");
    });

    it("missed-class (P5) takes precedence over intention (P6)", () => {
      const classes = [
        makeGymClass({ start_time: "7:00", end_time: "8:00" }),
      ];

      const result = computeSmartStatus(
        "Train later",
        [],
        classes,
        null,
      );
      expect(result!.type).toBe("missed");
    });

    it("intention (P6) takes precedence over hidden (P7)", () => {
      const result = computeSmartStatus("Morning jog", [], [], null);
      expect(result).not.toBeNull();
      expect(result!.type).toBe("intention");
    });
  });
});

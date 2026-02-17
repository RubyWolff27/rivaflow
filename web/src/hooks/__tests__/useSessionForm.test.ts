import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  whoopApi: {
    getWorkouts: vi.fn(() =>
      Promise.resolve({ data: { workouts: [], count: 0 } })
    ),
  },
  getErrorMessage: vi.fn((e: unknown) => String(e)),
}));

vi.mock("../../contexts/ToastContext", () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  }),
}));

import {
  mergePartners,
  mapSocialFriends,
  useSessionForm,
} from "../useSessionForm";
import type { Friend } from "../../types";

describe("mergePartners", () => {
  it("deduplicates by name (case-insensitive)", () => {
    const manual: Friend[] = [
      { id: 1, name: "Alice", friend_type: "training-partner" },
      { id: 2, name: "Bob", friend_type: "training-partner" },
    ];
    const instructors: Friend[] = [
      { id: 3, name: "alice", friend_type: "instructor" },
    ];
    const social: Friend[] = [
      { id: 1000004, name: "Charlie", friend_type: "training-partner" },
    ];

    const result = mergePartners(manual, instructors, social);

    expect(result).toHaveLength(3);
    const names = result.map((r) => r.name);
    expect(names).toContain("Alice");
    expect(names).toContain("Bob");
    expect(names).toContain("Charlie");
    // Should keep the first occurrence (manual Alice, not instructor alice)
    const alice = result.find(
      (r) => r.name.toLowerCase() === "alice"
    );
    expect(alice?.id).toBe(1);
  });

  it("merges empty arrays", () => {
    const result = mergePartners([], [], []);
    expect(result).toHaveLength(0);
  });

  it("includes social friends that are not duplicates", () => {
    const manual: Friend[] = [
      { id: 1, name: "Alice", friend_type: "training-partner" },
    ];
    const social: Friend[] = [
      { id: 1000002, name: "Dan", friend_type: "training-partner" },
      { id: 1000003, name: "alice", friend_type: "training-partner" },
    ];

    const result = mergePartners(manual, [], social);
    expect(result).toHaveLength(2);
    const names = result.map((r) => r.name);
    expect(names).toContain("Alice");
    expect(names).toContain("Dan");
  });
});

describe("mapSocialFriends", () => {
  it("maps friend data correctly", () => {
    const raw = [
      { id: 10, first_name: "Jane", last_name: "Doe" },
      { id: 20, first_name: "John", last_name: "Smith" },
    ];

    const result = mapSocialFriends(raw);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe(1000010);
    expect(result[0].name).toBe("Jane Doe");
    expect(result[0].friend_type).toBe("training-partner");
    expect(result[1].id).toBe(1000020);
    expect(result[1].name).toBe("John Smith");
  });

  it("handles missing first_name or last_name", () => {
    const raw = [
      { id: 1, first_name: undefined, last_name: "Solo" },
      { id: 2, first_name: "One", last_name: undefined },
      { id: 3, first_name: undefined, last_name: undefined },
    ];

    const result = mapSocialFriends(raw);
    expect(result[0].name).toBe("Solo");
    expect(result[1].name).toBe("One");
    expect(result[2].name).toBe("");
  });

  it("returns empty array for empty input", () => {
    const result = mapSocialFriends([]);
    expect(result).toHaveLength(0);
  });
});

describe("useSessionForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initializes with defaults", () => {
    const { result } = renderHook(() => useSessionForm());

    expect(result.current.sessionData.class_type).toBe("gi");
    expect(result.current.sessionData.duration_mins).toBe(60);
    expect(result.current.sessionData.intensity).toBe(4);
    expect(result.current.sessionData.gym_name).toBe("");
    expect(result.current.sessionData.session_date).toBe("");
    expect(result.current.sessionData.notes).toBe("");
    expect(result.current.detailedMode).toBe(false);
    expect(result.current.rolls).toHaveLength(0);
    expect(result.current.techniques).toHaveLength(0);
  });

  it("accepts initialData", () => {
    const { result } = renderHook(() =>
      useSessionForm({
        initialData: {
          gym_name: "My Gym",
          class_type: "no-gi",
          duration_mins: 90,
        },
      })
    );

    expect(result.current.sessionData.gym_name).toBe("My Gym");
    expect(result.current.sessionData.class_type).toBe("no-gi");
    expect(result.current.sessionData.duration_mins).toBe(90);
    // Other defaults should remain
    expect(result.current.sessionData.intensity).toBe(4);
  });

  it("isSparringType returns true for gi/no-gi/open-mat", () => {
    const { result: giResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "gi" } })
    );
    expect(giResult.current.isSparringType).toBe(true);

    const { result: noGiResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "no-gi" } })
    );
    expect(noGiResult.current.isSparringType).toBe(true);

    const { result: openMatResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "open-mat" } })
    );
    expect(openMatResult.current.isSparringType).toBe(true);

    const { result: compResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "competition" } })
    );
    expect(compResult.current.isSparringType).toBe(true);
  });

  it("isSparringType returns false for non-sparring types", () => {
    const { result: scResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "s&c" } })
    );
    expect(scResult.current.isSparringType).toBe(false);

    const { result: cardioResult } = renderHook(() =>
      useSessionForm({ initialData: { class_type: "cardio" } })
    );
    expect(cardioResult.current.isSparringType).toBe(false);
  });

  it("handleAddRoll adds a roll entry", () => {
    const { result } = renderHook(() => useSessionForm());

    act(() => {
      result.current.handleAddRoll();
    });

    expect(result.current.rolls).toHaveLength(1);
    expect(result.current.rolls[0].roll_number).toBe(1);
    expect(result.current.rolls[0].partner_name).toBe("");
    expect(result.current.rolls[0].duration_mins).toBe(5);
  });

  it("handleRemoveRoll removes a roll and reindexes", () => {
    const { result } = renderHook(() => useSessionForm());

    act(() => {
      result.current.handleAddRoll();
      result.current.handleAddRoll();
      result.current.handleAddRoll();
    });

    expect(result.current.rolls).toHaveLength(3);

    act(() => {
      result.current.handleRemoveRoll(1);
    });

    expect(result.current.rolls).toHaveLength(2);
    expect(result.current.rolls[0].roll_number).toBe(1);
    expect(result.current.rolls[1].roll_number).toBe(2);
  });

  it("handleAddTechnique adds a technique entry", () => {
    const { result } = renderHook(() => useSessionForm());

    act(() => {
      result.current.handleAddTechnique();
    });

    expect(result.current.techniques).toHaveLength(1);
    expect(result.current.techniques[0].technique_number).toBe(1);
    expect(result.current.techniques[0].movement_id).toBeNull();
    expect(result.current.techniques[0].media_urls).toHaveLength(0);
  });

  it("accepts initialDetailedMode", () => {
    const { result } = renderHook(() =>
      useSessionForm({ initialDetailedMode: true })
    );
    expect(result.current.detailedMode).toBe(true);
  });

  it("buildWhoopPayload returns empty object when no whoop data", () => {
    const { result } = renderHook(() => useSessionForm());
    expect(result.current.buildWhoopPayload()).toEqual({});
  });

  it("buildWhoopPayload returns parsed numbers", () => {
    const { result } = renderHook(() =>
      useSessionForm({
        initialData: {
          whoop_strain: "14.5",
          whoop_calories: "350",
          whoop_avg_hr: "145",
          whoop_max_hr: "180",
        },
      })
    );

    const payload = result.current.buildWhoopPayload();
    expect(payload.whoop_strain).toBe(14.5);
    expect(payload.whoop_calories).toBe(350);
    expect(payload.whoop_avg_hr).toBe(145);
    expect(payload.whoop_max_hr).toBe(180);
  });
});

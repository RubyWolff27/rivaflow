import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  coachPreferencesApi: {
    get: vi.fn(() =>
      Promise.resolve({
        data: {
          competition_ruleset: "ibjjf",
          training_mode: "lifestyle",
          coaching_style: "balanced",
          primary_position: "both",
          focus_areas: ["guard_passing"],
          weaknesses: "leg locks",
          injuries: [],
          training_start_date: "2022-01-01",
          years_training: 3,
          competition_experience: "beginner",
          available_days_per_week: 4,
          motivations: ["fitness"],
          additional_context: "",
          gi_nogi_preference: "both",
          gi_bias_pct: 50,
        },
      })
    ),
    update: vi.fn(() => Promise.resolve({ data: {} })),
  },
  profileApi: {
    get: vi.fn(() =>
      Promise.resolve({
        data: {
          current_grade: "blue",
        },
      })
    ),
  },
}));

vi.mock("../../contexts/ToastContext", () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  }),
}));

vi.mock("../../hooks/usePageTitle", () => ({
  usePageTitle: vi.fn(),
}));

vi.mock("../../components/ui", () => ({
  PrimaryButton: ({
    children,
    onClick,
    disabled,
    className,
  }: {
    children: React.ReactNode;
    onClick: () => void;
    disabled?: boolean;
    className?: string;
  }) => (
    <button
      data-testid="primary-button"
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      {children}
    </button>
  ),
}));

vi.mock("../../components/coach/CoachSettingsForm", () => ({
  default: ({ currentGrade }: { currentGrade: string }) => (
    <div data-testid="coach-settings-form">
      <span>Grade: {currentGrade}</span>
    </div>
  ),
}));

vi.mock("../../components/coach/InjuryManager", () => ({
  default: ({
    injuries,
    onAdd,
  }: {
    injuries: unknown[];
    onAdd: () => void;
  }) => (
    <div data-testid="injury-manager">
      <span>{injuries.length} injuries</span>
      <button onClick={onAdd}>Add Injury</button>
    </div>
  ),
}));

import CoachSettings from "../CoachSettings";

function renderCoachSettings() {
  return render(
    <BrowserRouter>
      <CoachSettings />
    </BrowserRouter>
  );
}

describe("CoachSettings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Coach Settings heading after loading", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByText("Coach Settings")).toBeInTheDocument();
    });
  });

  it("renders the subtitle text", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(
        screen.getByText("Personalise how Grapple coaches you")
      ).toBeInTheDocument();
    });
  });

  it("loads coach preferences from API on mount", async () => {
    const { coachPreferencesApi } = await import("../../api/client");
    renderCoachSettings();
    await waitFor(() => {
      expect(coachPreferencesApi.get).toHaveBeenCalled();
    });
  });

  it("loads profile data for current grade", async () => {
    const { profileApi } = await import("../../api/client");
    renderCoachSettings();
    await waitFor(() => {
      expect(profileApi.get).toHaveBeenCalled();
    });
  });

  it("renders the CoachSettingsForm component with grade", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByTestId("coach-settings-form")).toBeInTheDocument();
    });
    expect(screen.getByText("Grade: blue")).toBeInTheDocument();
  });

  it("renders the InjuryManager component", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByTestId("injury-manager")).toBeInTheDocument();
    });
  });

  it("renders the Save Preferences button", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByText("Save Preferences")).toBeInTheDocument();
    });
  });

  it("calls coachPreferencesApi.update when Save is clicked", async () => {
    const { coachPreferencesApi } = await import("../../api/client");
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByText("Save Preferences")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Save Preferences"));
    await waitFor(() => {
      expect(coachPreferencesApi.update).toHaveBeenCalled();
    });
  });

  it("renders back button for navigation", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(screen.getByLabelText("Go back")).toBeInTheDocument();
    });
  });

  it("renders the disclaimer text", async () => {
    renderCoachSettings();
    await waitFor(() => {
      expect(
        screen.getByText(/Changes take effect on your next interaction/)
      ).toBeInTheDocument();
    });
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ id: "1" }),
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  sessionsApi: {
    getWithRolls: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          session_date: "2026-02-15",
          class_time: "17:30",
          class_type: "gi",
          gym_name: "Test Gym",
          location: "Sydney, NSW",
          duration_mins: 60,
          intensity: 4,
          rolls: 3,
          submissions_for: 1,
          submissions_against: 0,
          partners: ["Alice", "Bob"],
          techniques: ["armbar", "triangle"],
          notes: "Great rolling session",
          instructor_name: "Coach Dan",
          detailed_rolls: [],
          session_techniques: [],
          whoop_strain: null,
          whoop_calories: null,
          whoop_avg_hr: null,
          whoop_max_hr: null,
          session_score: 78,
          score_breakdown: null,
          needs_review: false,
          created_at: "2026-02-15T17:30:00Z",
        },
      })
    ),
    recalculateScore: vi.fn(() =>
      Promise.resolve({
        data: { session_score: 80, score_breakdown: null },
      })
    ),
  },
  whoopApi: {
    sessionContext: vi.fn(() =>
      Promise.resolve({ data: null })
    ),
  },
}));

vi.mock("../../contexts/ToastContext", () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

vi.mock("../../hooks/usePageTitle", () => ({
  usePageTitle: vi.fn(),
}));

vi.mock("../../utils/logger", () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock("../../components/PhotoGallery", () => ({
  default: () => <div data-testid="photo-gallery" />,
}));

vi.mock("../../components/PhotoUpload", () => ({
  default: () => <div data-testid="photo-upload" />,
}));

vi.mock("../../components/SessionInsights", () => ({
  default: () => <div data-testid="session-insights" />,
}));

vi.mock("../../components/sessions/SessionScoreCard", () => ({
  default: () => <div data-testid="session-score-card" />,
}));

vi.mock("../../components/ui", () => ({
  CardSkeleton: ({ lines }: { lines: number }) => (
    <div data-testid="card-skeleton">Skeleton {lines} lines</div>
  ),
}));

import SessionDetail from "../SessionDetail";

function renderSessionDetail() {
  return render(
    <BrowserRouter>
      <SessionDetail />
    </BrowserRouter>
  );
}

describe("SessionDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("handles loading state", () => {
    renderSessionDetail();
    // While loading, skeleton should show
    expect(screen.getAllByTestId("card-skeleton").length).toBeGreaterThan(
      0
    );
  });

  it("renders session details after load", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("Session Details")).toBeInTheDocument();
    });
    expect(screen.getByText("Test Gym")).toBeInTheDocument();
    expect(screen.getByText("60 mins")).toBeInTheDocument();
  });

  it("shows session date and class type", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("gi")).toBeInTheDocument();
    });
    // Date is formatted as "Sunday, February 15, 2026"
    expect(
      screen.getByText("Sunday, February 15, 2026")
    ).toBeInTheDocument();
  });

  it("shows edit button for own sessions", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /edit session/i })
      ).toBeInTheDocument();
    });
    const editLink = screen.getByRole("link", {
      name: /edit session/i,
    });
    expect(editLink).toHaveAttribute("href", "/session/edit/1");
  });

  it("shows instructor name", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("Coach Dan")).toBeInTheDocument();
    });
  });

  it("shows training partners", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeInTheDocument();
    });
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("shows techniques practiced", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("armbar")).toBeInTheDocument();
    });
    expect(screen.getByText("triangle")).toBeInTheDocument();
  });

  it("shows notes", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(
        screen.getByText("Great rolling session")
      ).toBeInTheDocument();
    });
  });

  it("shows location", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("Sydney, NSW")).toBeInTheDocument();
    });
  });

  it("shows submissions count", async () => {
    renderSessionDetail();
    await waitFor(() => {
      expect(screen.getByText("1 / 0")).toBeInTheDocument();
    });
  });

  it("calls sessionsApi.getWithRolls with correct id", async () => {
    const { sessionsApi } = await import("../../api/client");
    renderSessionDetail();
    await waitFor(() => {
      expect(sessionsApi.getWithRolls).toHaveBeenCalledWith(1);
    });
  });
});

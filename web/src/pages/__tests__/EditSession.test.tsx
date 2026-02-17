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
          instructor_id: null,
          rolls: 3,
          submissions_for: 1,
          submissions_against: 0,
          partners: ["Alice", "Bob"],
          techniques: ["armbar"],
          notes: "Great session",
          whoop_strain: null,
          whoop_calories: null,
          whoop_avg_hr: null,
          whoop_max_hr: null,
          detailed_rolls: [],
          session_techniques: [],
        },
      })
    ),
    getAutocomplete: vi.fn(() =>
      Promise.resolve({
        data: {
          gyms: ["Test Gym"],
          locations: ["Sydney, NSW"],
          partners: [],
          techniques: [],
        },
      })
    ),
    update: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  friendsApi: {
    listInstructors: vi.fn(() => Promise.resolve({ data: [] })),
    listPartners: vi.fn(() => Promise.resolve({ data: [] })),
  },
  socialApi: {
    getFriends: vi.fn(() =>
      Promise.resolve({ data: { friends: [] } })
    ),
  },
  glossaryApi: {
    list: vi.fn(() => Promise.resolve({ data: [] })),
  },
  whoopApi: {
    getStatus: vi.fn(() =>
      Promise.resolve({ data: { connected: false } })
    ),
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

vi.mock("../../utils/logger", () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock("../../hooks/usePageTitle", () => ({
  usePageTitle: vi.fn(),
}));

vi.mock("../../components/WhoopMatchModal", () => ({
  default: () => <div data-testid="whoop-match-modal" />,
}));

vi.mock("../../components/sessions/WhoopIntegrationPanel", () => ({
  default: () => <div data-testid="whoop-panel" />,
}));

vi.mock("../../components/PhotoGallery", () => ({
  default: () => <div data-testid="photo-gallery" />,
}));

vi.mock("../../components/PhotoUpload", () => ({
  default: () => <div data-testid="photo-upload" />,
}));

vi.mock("../../components/ConfirmDialog", () => ({
  default: () => <div data-testid="confirm-dialog" />,
}));

import EditSession from "../EditSession";

function renderEditSession() {
  return render(
    <BrowserRouter>
      <EditSession />
    </BrowserRouter>
  );
}

describe("EditSession", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    renderEditSession();
    expect(screen.getByText("Loading session...")).toBeInTheDocument();
  });

  it("renders the form after data loads", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(screen.getByText("Edit Session")).toBeInTheDocument();
    });
    expect(screen.getByText("Date")).toBeInTheDocument();
  });

  it("shows session data (date, class type, etc.)", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(screen.getByDisplayValue("2026-02-15")).toBeInTheDocument();
    });
    // Class type select shows "gi"
    const classSelect = screen.getByDisplayValue("Gi");
    expect(classSelect).toBeInTheDocument();
    // Gym name
    expect(screen.getByDisplayValue("Test Gym")).toBeInTheDocument();
    // Duration
    expect(screen.getByDisplayValue("60")).toBeInTheDocument();
    // Intensity
    expect(screen.getByDisplayValue("4")).toBeInTheDocument();
  });

  it("has save button", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(screen.getByText("Save Changes")).toBeInTheDocument();
    });
  });

  it("has delete button", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /delete session/i })
      ).toBeInTheDocument();
    });
  });

  it("has back button", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /back to session/i })
      ).toBeInTheDocument();
    });
  });

  it("loads session data from API", async () => {
    const { sessionsApi } = await import("../../api/client");
    renderEditSession();
    await waitFor(() => {
      expect(sessionsApi.getWithRolls).toHaveBeenCalledWith(1);
    });
  });

  it("loads instructors and partners from API", async () => {
    const { friendsApi } = await import("../../api/client");
    renderEditSession();
    await waitFor(() => {
      expect(friendsApi.listInstructors).toHaveBeenCalled();
      expect(friendsApi.listPartners).toHaveBeenCalled();
    });
  });

  it("shows location field", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(
        screen.getByDisplayValue("Sydney, NSW")
      ).toBeInTheDocument();
    });
  });

  it("shows notes field with session notes", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(
        screen.getByDisplayValue("Great session")
      ).toBeInTheDocument();
    });
  });

  it("shows photo section", async () => {
    renderEditSession();
    await waitFor(() => {
      expect(screen.getByText("Photos")).toBeInTheDocument();
    });
    expect(screen.getByTestId("photo-gallery")).toBeInTheDocument();
    expect(screen.getByTestId("photo-upload")).toBeInTheDocument();
  });
});

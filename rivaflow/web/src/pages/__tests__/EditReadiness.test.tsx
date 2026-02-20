import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ date: "2026-01-15" }),
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  readinessApi: {
    getByDate: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          check_date: "2026-01-15",
          sleep: 4,
          stress: 2,
          soreness: 2,
          energy: 4,
          hotspot_note: "shoulder tight",
          weight_kg: 85.5,
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 1 } })),
  },
}));

vi.mock("../../contexts/ToastContext", () => ({
  useToast: () => ({
    showToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
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

import EditReadiness from "../EditReadiness";

function renderEditReadiness() {
  return render(
    <BrowserRouter>
      <EditReadiness />
    </BrowserRouter>
  );
}

describe("EditReadiness", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    renderEditReadiness();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("loads and displays form data after fetch", async () => {
    renderEditReadiness();
    await waitFor(() => {
      expect(
        screen.getByText("Edit Readiness Check-in")
      ).toBeInTheDocument();
    });
    // Sleep slider label shows loaded value
    expect(screen.getByText(/Sleep Quality: 4\/5/)).toBeInTheDocument();
    expect(screen.getByText(/Stress Level: 2\/5/)).toBeInTheDocument();
    expect(screen.getByText(/Muscle Soreness: 2\/5/)).toBeInTheDocument();
    expect(screen.getByText(/Energy Level: 4\/5/)).toBeInTheDocument();
  });

  it("shows the save button", async () => {
    renderEditReadiness();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /save changes/i })
      ).toBeInTheDocument();
    });
  });

  it("shows hotspot note from loaded data", async () => {
    renderEditReadiness();
    await waitFor(() => {
      expect(
        screen.getByDisplayValue("shoulder tight")
      ).toBeInTheDocument();
    });
  });

  it("shows weight from loaded data", async () => {
    renderEditReadiness();
    await waitFor(() => {
      expect(screen.getByDisplayValue("85.5")).toBeInTheDocument();
    });
  });

  it("handles load error by navigating to feed", async () => {
    const { readinessApi } = await import("../../api/client");
    (readinessApi.getByDate as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error")
    );
    renderEditReadiness();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/feed");
    });
  });
});

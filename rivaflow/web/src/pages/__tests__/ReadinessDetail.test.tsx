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
          hotspot_note: "shoulder",
          weight_kg: 85,
          composite_score: 4,
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

import ReadinessDetail from "../ReadinessDetail";

function renderReadinessDetail() {
  return render(
    <BrowserRouter>
      <ReadinessDetail />
    </BrowserRouter>
  );
}

describe("ReadinessDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    renderReadinessDetail();
    expect(screen.getByText("Loading readiness...")).toBeInTheDocument();
  });

  it("shows readiness details after load", async () => {
    renderReadinessDetail();
    await waitFor(() => {
      expect(
        screen.getByText("Readiness Check-in")
      ).toBeInTheDocument();
    });
    // Scores section
    expect(screen.getByText("Readiness Scores")).toBeInTheDocument();
    expect(screen.getByText("Sleep Quality")).toBeInTheDocument();
    expect(screen.getByText("Stress Level")).toBeInTheDocument();
    expect(screen.getByText("Energy Level")).toBeInTheDocument();
  });

  it("shows edit link pointing to correct URL", async () => {
    renderReadinessDetail();
    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /edit readiness/i })
      ).toBeInTheDocument();
    });
    const editLink = screen.getByRole("link", {
      name: /edit readiness/i,
    });
    expect(editLink).toHaveAttribute(
      "href",
      "/readiness/edit/2026-01-15"
    );
  });

  it("shows weight when provided", async () => {
    renderReadinessDetail();
    await waitFor(() => {
      expect(screen.getByText(/85 kg/)).toBeInTheDocument();
    });
  });

  it("shows hotspot note when provided", async () => {
    renderReadinessDetail();
    await waitFor(() => {
      expect(screen.getByText(/shoulder/)).toBeInTheDocument();
    });
  });

  it("handles error by navigating to feed", async () => {
    const { readinessApi } = await import("../../api/client");
    (readinessApi.getByDate as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error")
    );
    renderReadinessDetail();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/feed");
    });
  });
});

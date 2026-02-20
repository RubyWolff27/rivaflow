import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ date: "2026-01-16" }),
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  restApi: {
    getByDate: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          rest_date: "2026-01-16",
          rest_type: "full",
          rest_note: "Full rest day",
          tomorrow_intention: "Training tomorrow",
          created_at: "2026-01-16T10:00:00Z",
        },
      })
    ),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
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

vi.mock("../../components/ui", () => ({
  CardSkeleton: ({ lines }: { lines?: number }) => (
    <div data-testid="card-skeleton">Skeleton {lines ?? 0} lines</div>
  ),
}));

import RestDetail from "../RestDetail";

function renderRestDetail() {
  return render(
    <BrowserRouter>
      <RestDetail />
    </BrowserRouter>
  );
}

describe("RestDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton initially", () => {
    renderRestDetail();
    expect(
      screen.getAllByTestId("card-skeleton").length
    ).toBeGreaterThan(0);
  });

  it("shows rest day details after load", async () => {
    renderRestDetail();
    await waitFor(() => {
      expect(screen.getByText("Rest Day")).toBeInTheDocument();
    });
    // Rest type label
    expect(screen.getByText(/Full Rest/)).toBeInTheDocument();
  });

  it("shows rest note when provided", async () => {
    renderRestDetail();
    await waitFor(() => {
      expect(screen.getByText("Full rest day")).toBeInTheDocument();
    });
  });

  it("shows tomorrow intention when provided", async () => {
    renderRestDetail();
    await waitFor(() => {
      expect(
        screen.getByText(/Training tomorrow/)
      ).toBeInTheDocument();
    });
  });

  it("shows edit link pointing to correct URL", async () => {
    renderRestDetail();
    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /edit rest day/i })
      ).toBeInTheDocument();
    });
    const editLink = screen.getByRole("link", {
      name: /edit rest day/i,
    });
    expect(editLink).toHaveAttribute("href", "/rest/edit/2026-01-16");
  });

  it("handles error by navigating to feed", async () => {
    const { restApi } = await import("../../api/client");
    (restApi.getByDate as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error")
    );
    renderRestDetail();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/feed");
    });
  });
});

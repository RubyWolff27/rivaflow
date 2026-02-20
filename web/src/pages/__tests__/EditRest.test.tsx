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
          rest_type: "active",
          rest_note: "Light stretching",
          tomorrow_intention: "Gi class",
          created_at: "2026-01-16T10:00:00Z",
        },
      })
    ),
    logRestDay: vi.fn(() => Promise.resolve({ data: {} })),
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

import EditRest from "../EditRest";

function renderEditRest() {
  return render(
    <BrowserRouter>
      <EditRest />
    </BrowserRouter>
  );
}

describe("EditRest", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    renderEditRest();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("loads and displays form data after fetch", async () => {
    renderEditRest();
    await waitFor(() => {
      expect(screen.getByText("Edit Rest Day")).toBeInTheDocument();
    });
    // Rest note textarea should contain loaded value
    expect(
      screen.getByDisplayValue("Light stretching")
    ).toBeInTheDocument();
    // Tomorrow intention input should contain loaded value
    expect(screen.getByDisplayValue("Gi class")).toBeInTheDocument();
  });

  it("shows rest type options in select", async () => {
    renderEditRest();
    await waitFor(() => {
      expect(screen.getByText("Edit Rest Day")).toBeInTheDocument();
    });
    // All rest type options should be available
    expect(screen.getByText(/Active Recovery/)).toBeInTheDocument();
    expect(screen.getByText(/Full Rest/)).toBeInTheDocument();
    expect(screen.getByText(/Injury/)).toBeInTheDocument();
    expect(screen.getByText(/Sick Day/)).toBeInTheDocument();
    expect(screen.getByText(/Travelling/)).toBeInTheDocument();
    expect(screen.getByText(/Life Got in the Way/)).toBeInTheDocument();
  });

  it("shows the save button", async () => {
    renderEditRest();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /save changes/i })
      ).toBeInTheDocument();
    });
  });

  it("shows delete rest day button", async () => {
    renderEditRest();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /delete rest day/i })
      ).toBeInTheDocument();
    });
  });

  it("handles load error by navigating to feed", async () => {
    const { restApi } = await import("../../api/client");
    (restApi.getByDate as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error")
    );
    renderEditRest();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/feed");
    });
  });
});

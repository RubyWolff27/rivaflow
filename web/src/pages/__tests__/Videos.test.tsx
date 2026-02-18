import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  videosApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          videos: [
            {
              id: 1,
              url: "https://youtube.com/watch?v=abc123",
              title: "Armbar Tutorial",
              movement_id: 1,
              movement_name: "Armbar",
              video_type: "general",
            },
            {
              id: 2,
              url: "https://youtube.com/watch?v=def456",
              title: "Guard Passing Masterclass",
              movement_id: 2,
              movement_name: "Torreando Pass",
              video_type: "gi",
            },
          ],
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 3 } })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  glossaryApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          movements: [
            {
              id: 1,
              name: "Armbar",
              category: "submission",
            },
            {
              id: 2,
              name: "Torreando Pass",
              category: "pass",
            },
          ],
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

vi.mock("../../components/ConfirmDialog", () => ({
  default: () => <div data-testid="confirm-dialog" />,
}));

vi.mock("../../components/ui", () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
  EmptyState: ({
    title,
    description,
  }: {
    title: string;
    description: string;
  }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}));

import Videos from "../Videos";

function renderVideos() {
  return render(
    <BrowserRouter>
      <Videos />
    </BrowserRouter>
  );
}

describe("Videos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Video Library heading after data loads", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("Video Library")).toBeInTheDocument();
    });
  });

  it("calls videosApi.list and glossaryApi.list on mount", async () => {
    const { videosApi, glossaryApi } = await import("../../api/client");
    renderVideos();
    await waitFor(() => {
      expect(videosApi.list).toHaveBeenCalled();
      expect(glossaryApi.list).toHaveBeenCalled();
    });
  });

  it("renders video cards with titles", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("Armbar Tutorial")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Guard Passing Masterclass")
    ).toBeInTheDocument();
  });

  it("shows linked movement names", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("Linked to: Armbar")).toBeInTheDocument();
      expect(
        screen.getByText("Linked to: Torreando Pass")
      ).toBeInTheDocument();
    });
  });

  it("renders the Add Video button", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("Add Video")).toBeInTheDocument();
    });
  });

  it("shows the add video form when button is clicked", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("Add Video")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Add Video"));
    expect(screen.getByText("Add New Video")).toBeInTheDocument();
  });

  it("renders library description text", async () => {
    renderVideos();
    await waitFor(() => {
      expect(
        screen.getByText(
          /Manage your instructional video library/
        )
      ).toBeInTheDocument();
    });
  });

  it("shows empty state when no videos exist", async () => {
    const { videosApi } = await import("../../api/client");
    vi.mocked(videosApi.list).mockResolvedValueOnce({
      data: { videos: [] },
    } as any);
    renderVideos();
    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    });
    expect(
      screen.getByText("No videos in your library yet")
    ).toBeInTheDocument();
  });

  it("shows video type badge for non-general type", async () => {
    renderVideos();
    await waitFor(() => {
      expect(screen.getByText("gi")).toBeInTheDocument();
    });
  });

  it("renders external links for each video", async () => {
    renderVideos();
    await waitFor(() => {
      const links = document.querySelectorAll(
        'a[target="_blank"][rel="noopener noreferrer"]'
      );
      expect(links.length).toBe(2);
    });
  });
});

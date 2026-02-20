import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ userId: "2" }),
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  usersApi: {
    getProfile: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 2,
          first_name: "Jane",
          last_name: "Doe",
          avatar_url: null,
          current_grade: "blue",
          default_gym: "Gracie Barra",
          follower_count: 10,
          following_count: 5,
        },
      })
    ),
    getStats: vi.fn(() =>
      Promise.resolve({
        data: {
          total_sessions: 50,
          total_hours: 75,
          total_rolls: 200,
          sessions_this_week: 3,
        },
      })
    ),
    getActivity: vi.fn(() =>
      Promise.resolve({ data: { items: [] } })
    ),
  },
  socialApi: {
    getFriendshipStatus: vi.fn(() =>
      Promise.resolve({ data: { status: "none" } })
    ),
    sendFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
    follow: vi.fn(() => Promise.resolve({ data: {} })),
    getReceivedRequests: vi.fn(() =>
      Promise.resolve({ data: { requests: [] } })
    ),
    acceptFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
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

vi.mock("../../contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, first_name: "Test", last_name: "User" },
    isLoading: false,
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
    debug: vi.fn(),
  },
}));

vi.mock("../../components/ui", () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
}));

import UserProfile from "../UserProfile";

function renderUserProfile() {
  return render(
    <BrowserRouter>
      <UserProfile />
    </BrowserRouter>
  );
}

describe("UserProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton initially", () => {
    renderUserProfile();
    expect(
      screen.getAllByTestId("card-skeleton").length
    ).toBeGreaterThan(0);
  });

  it("shows user profile data after load", async () => {
    renderUserProfile();
    await waitFor(() => {
      expect(screen.getByText(/Jane/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Doe/)).toBeInTheDocument();
    expect(screen.getByText("Gracie Barra")).toBeInTheDocument();
    expect(screen.getByText("blue")).toBeInTheDocument();
  });

  it("shows follower and following counts", async () => {
    renderUserProfile();
    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
    });
    expect(screen.getByText("followers")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("following")).toBeInTheDocument();
  });

  it("shows add friend button for non-friends", async () => {
    renderUserProfile();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /add friend/i })
      ).toBeInTheDocument();
    });
  });

  it("shows stats after load", async () => {
    renderUserProfile();
    await waitFor(() => {
      expect(screen.getByText("Total Sessions")).toBeInTheDocument();
    });
    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.getByText("Total Hours")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("handles load error and shows error state", async () => {
    const { usersApi } = await import("../../api/client");
    (usersApi.getProfile as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error")
    );
    renderUserProfile();
    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
    expect(screen.getByText("Back to Feed")).toBeInTheDocument();
  });
});

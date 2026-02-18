import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  socialApi: {
    searchUsers: vi.fn(() =>
      Promise.resolve({
        data: {
          users: [
            {
              id: 10,
              first_name: "Jane",
              last_name: "Doe",
              email: "jane@example.com",
            },
          ],
        },
      })
    ),
    getFriendshipStatus: vi.fn(() =>
      Promise.resolve({ data: { status: "none" } })
    ),
    sendFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
    getReceivedRequests: vi.fn(() =>
      Promise.resolve({ data: { requests: [] } })
    ),
    acceptFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
    declineFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
    unfriend: vi.fn(() => Promise.resolve({ data: {} })),
    getRecommended: vi.fn(() =>
      Promise.resolve({
        data: {
          recommendations: [],
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

vi.mock("../../components/ui", () => ({
  Card: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  PrimaryButton: ({
    children,
    onClick,
    disabled,
    className,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
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
  SecondaryButton: ({
    children,
    onClick,
    disabled,
    className,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    className?: string;
  }) => (
    <button
      data-testid="secondary-button"
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      {children}
    </button>
  ),
}));

vi.mock("../../components/FriendSuggestions", () => ({
  FriendSuggestions: () => (
    <div data-testid="friend-suggestions">Suggestions</div>
  ),
}));

import FindFriends from "../FindFriends";

function renderFindFriends() {
  return render(
    <BrowserRouter>
      <FindFriends />
    </BrowserRouter>
  );
}

describe("FindFriends", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Find Friends heading", async () => {
    renderFindFriends();
    expect(screen.getByText("Find Friends")).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    renderFindFriends();
    expect(
      screen.getByText("Connect with athletes at your gym")
    ).toBeInTheDocument();
  });

  it("renders the search input", () => {
    renderFindFriends();
    expect(
      screen.getByPlaceholderText("Search by name or email...")
    ).toBeInTheDocument();
  });

  it("renders discovery tabs (For You, At Your Gym)", () => {
    renderFindFriends();
    expect(screen.getByText("For You")).toBeInTheDocument();
    expect(screen.getByText("At Your Gym")).toBeInTheDocument();
  });

  it("shows FriendSuggestions on the suggestions tab by default", () => {
    renderFindFriends();
    expect(screen.getByTestId("friend-suggestions")).toBeInTheDocument();
  });

  it("performs search and shows results when query is entered", async () => {
    const { socialApi } = await import("../../api/client");
    renderFindFriends();
    const searchInput = screen.getByPlaceholderText(
      "Search by name or email..."
    );
    fireEvent.change(searchInput, { target: { value: "Jane" } });
    await waitFor(() => {
      expect(socialApi.searchUsers).toHaveBeenCalledWith("Jane");
    });
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    });
  });

  it("shows Add Friend button for users with no friendship", async () => {
    renderFindFriends();
    const searchInput = screen.getByPlaceholderText(
      "Search by name or email..."
    );
    fireEvent.change(searchInput, { target: { value: "Jane" } });
    await waitFor(() => {
      expect(screen.getByText("Add Friend")).toBeInTheDocument();
    });
  });

  it("calls socialApi.getFriendshipStatus for each search result", async () => {
    const { socialApi } = await import("../../api/client");
    renderFindFriends();
    const searchInput = screen.getByPlaceholderText(
      "Search by name or email..."
    );
    fireEvent.change(searchInput, { target: { value: "Jane" } });
    await waitFor(() => {
      expect(socialApi.getFriendshipStatus).toHaveBeenCalledWith(10);
    });
  });

  it("switches to gym tab and loads recommendations", async () => {
    const { socialApi } = await import("../../api/client");
    renderFindFriends();
    fireEvent.click(screen.getByText("At Your Gym"));
    await waitFor(() => {
      expect(socialApi.getRecommended).toHaveBeenCalled();
    });
  });

  it("shows no results message for empty search", async () => {
    const { socialApi } = await import("../../api/client");
    vi.mocked(socialApi.searchUsers).mockResolvedValueOnce({
      data: { users: [] },
    } as any);
    renderFindFriends();
    const searchInput = screen.getByPlaceholderText(
      "Search by name or email..."
    );
    fireEvent.change(searchInput, { target: { value: "Nobody" } });
    await waitFor(() => {
      expect(
        screen.getByText(/No users found matching "Nobody"/)
      ).toBeInTheDocument();
    });
  });
});

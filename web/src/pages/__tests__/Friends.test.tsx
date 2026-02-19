import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMockToast, createMockLogger, createMockPageTitle } from "../../__tests__/test-utils";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api/client", () => ({
  friendsApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          friends: [
            {
              id: 1,
              name: "Alice Smith",
              friend_type: "training-partner",
              belt_rank: "blue",
              belt_stripes: 2,
              instructor_certification: "",
              phone: "",
              email: "alice@example.com",
              notes: "",
            },
            {
              id: 2,
              name: "Coach Bob",
              friend_type: "instructor",
              belt_rank: "black",
              belt_stripes: 3,
              instructor_certification: "IBJJF",
              phone: "",
              email: "",
              notes: "",
            },
          ],
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: {} })),
    update: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  socialApi: {
    getReceivedRequests: vi.fn(() =>
      Promise.resolve({ data: { requests: [] } })
    ),
    getFriends: vi.fn(() =>
      Promise.resolve({ data: { friends: [] } })
    ),
    acceptFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
    declineFriendRequest: vi.fn(() => Promise.resolve({ data: {} })),
  },
}));

vi.mock("../../contexts/ToastContext", () => createMockToast());
vi.mock("../../utils/logger", () => createMockLogger());
vi.mock("../../hooks/usePageTitle", () => createMockPageTitle());

vi.mock("../../components/ConfirmDialog", () => ({
  default: () => <div data-testid="confirm-dialog" />,
}));

vi.mock("../../components/ui", () => ({
  CardSkeleton: () => <div data-testid="card-skeleton" />,
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock("../../components/friends/FriendCard", () => ({
  default: ({ friend }: { friend: { name: string } }) => (
    <div data-testid="friend-card">{friend.name}</div>
  ),
}));

vi.mock("../../components/friends/FriendRequestCard", () => ({
  default: ({ pendingRequests }: { pendingRequests: unknown[] }) => (
    <div data-testid="friend-request-card">
      {pendingRequests.length} pending
    </div>
  ),
  SocialFriendsList: ({ socialFriends }: { socialFriends: unknown[] }) => (
    <div data-testid="social-friends-list">
      {socialFriends.length} social friends
    </div>
  ),
}));

vi.mock("../../components/friends/FriendForm", () => ({
  default: ({
    onSubmit,
    onCancel,
    isEditing,
  }: {
    onSubmit: (e: React.FormEvent) => void;
    onCancel: () => void;
    isEditing: boolean;
  }) => (
    <form data-testid="friend-form" onSubmit={onSubmit}>
      <span>{isEditing ? "Edit" : "Add"}</span>
      <button type="button" onClick={onCancel}>
        Cancel Form
      </button>
      <button type="submit">Submit Form</button>
    </form>
  ),
}));

import Friends from "../Friends";

function renderFriends() {
  return render(
    <BrowserRouter>
      <Friends />
    </BrowserRouter>
  );
}

describe("Friends", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Friends heading after data loads", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText("Friends")).toBeInTheDocument();
    });
  });

  it("renders friend cards for loaded friends", async () => {
    renderFriends();
    await waitFor(() => {
      const cards = screen.getAllByTestId("friend-card");
      expect(cards).toHaveLength(2);
    });
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    expect(screen.getByText("Coach Bob")).toBeInTheDocument();
  });

  it("calls friendsApi.list on mount", async () => {
    const { friendsApi } = await import("../../api/client");
    renderFriends();
    await waitFor(() => {
      expect(friendsApi.list).toHaveBeenCalled();
    });
  });

  it("calls socialApi for pending requests and social friends", async () => {
    const { socialApi } = await import("../../api/client");
    renderFriends();
    await waitFor(() => {
      expect(socialApi.getReceivedRequests).toHaveBeenCalled();
      expect(socialApi.getFriends).toHaveBeenCalled();
    });
  });

  it("renders filter buttons (All, Instructors, Training Partners)", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText(/All \(2\)/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Instructors \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Training Partners \(1\)/)).toBeInTheDocument();
  });

  it("renders the Add Friend button", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText("Add Friend")).toBeInTheDocument();
    });
  });

  it("shows add form when Add Friend button is clicked", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText("Add Friend")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Add Friend"));
    await waitFor(() => {
      expect(screen.getByTestId("friend-form")).toBeInTheDocument();
    });
  });

  it("renders the Discover button", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText("Discover")).toBeInTheDocument();
    });
  });

  it("navigates to find-friends when Discover is clicked", async () => {
    renderFriends();
    await waitFor(() => {
      expect(screen.getByText("Discover")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Discover"));
    expect(mockNavigate).toHaveBeenCalledWith("/find-friends");
  });

  it("shows empty state when no friends are returned", async () => {
    const { friendsApi } = await import("../../api/client");
    vi.mocked(friendsApi.list).mockResolvedValueOnce({
      data: { friends: [] },
    } as any);
    renderFriends();
    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    });
    expect(screen.getByText("No friends found")).toBeInTheDocument();
  });
});

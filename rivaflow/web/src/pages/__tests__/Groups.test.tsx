import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  groupsApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          groups: [
            {
              id: 1,
              name: "Morning Crew",
              description: "Early morning training group",
              group_type: "training_crew",
              privacy: "invite_only",
              member_count: 5,
            },
            {
              id: 2,
              name: "Comp Team",
              description: "Competition preparation squad",
              group_type: "comp_team",
              privacy: "open",
              member_count: 8,
            },
          ],
        },
      })
    ),
    discover: vi.fn(() =>
      Promise.resolve({
        data: {
          groups: [
            {
              id: 3,
              name: "Open Mat Crew",
              description: "Open mat sessions",
              group_type: "training_crew",
              privacy: "open",
              member_count: 12,
            },
          ],
        },
      })
    ),
    get: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          name: "Morning Crew",
          description: "Early morning training group",
          group_type: "training_crew",
          privacy: "invite_only",
          members: [],
          member_count: 5,
          user_role: "admin",
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 4 } })),
    join: vi.fn(() => Promise.resolve({ data: {} })),
    leave: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    addMember: vi.fn(() => Promise.resolve({ data: {} })),
    removeMember: vi.fn(() => Promise.resolve({ data: {} })),
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

vi.mock("../../components/ui/EmptyState", () => ({
  default: ({
    title,
    description,
    action,
  }: {
    title: string;
    description: string;
    action?: React.ReactNode;
  }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
      {action}
    </div>
  ),
}));

vi.mock("../../components/groups/GroupCard", () => ({
  default: ({
    group,
    onClick,
  }: {
    group: { name: string };
    onClick: () => void;
  }) => (
    <div data-testid="group-card" onClick={onClick}>
      {group.name}
    </div>
  ),
  DiscoverGroupCard: ({
    group,
    onJoin,
  }: {
    group: { name: string };
    onJoin: () => void;
  }) => (
    <div data-testid="discover-group-card" onClick={onJoin}>
      {group.name}
    </div>
  ),
}));

vi.mock("../../components/groups/GroupForm", () => ({
  default: ({
    onSubmit,
    onClose,
  }: {
    onSubmit: (e: React.FormEvent) => void;
    onClose: () => void;
  }) => (
    <form data-testid="group-form" onSubmit={onSubmit}>
      <button type="button" onClick={onClose}>
        Close
      </button>
      <button type="submit">Submit</button>
    </form>
  ),
}));

vi.mock("../../components/groups/GroupDetailView", () => ({
  default: ({
    group,
    onBack,
  }: {
    group: { name: string };
    onBack: () => void;
  }) => (
    <div data-testid="group-detail-view">
      <p>{group.name}</p>
      <button onClick={onBack}>Back</button>
    </div>
  ),
}));

import Groups from "../Groups";

function renderGroups() {
  return render(
    <BrowserRouter>
      <Groups />
    </BrowserRouter>
  );
}

describe("Groups", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Groups heading after data loads", async () => {
    renderGroups();
    await waitFor(() => {
      expect(screen.getByText("Groups")).toBeInTheDocument();
    });
  });

  it("renders subtitle text", async () => {
    renderGroups();
    await waitFor(() => {
      expect(
        screen.getByText("Training crews, comp teams & study groups")
      ).toBeInTheDocument();
    });
  });

  it("calls groupsApi.list on mount", async () => {
    const { groupsApi } = await import("../../api/client");
    renderGroups();
    await waitFor(() => {
      expect(groupsApi.list).toHaveBeenCalled();
    });
  });

  it("renders group cards for loaded groups", async () => {
    renderGroups();
    await waitFor(() => {
      const cards = screen.getAllByTestId("group-card");
      expect(cards).toHaveLength(2);
    });
    expect(screen.getByText("Morning Crew")).toBeInTheDocument();
    expect(screen.getByText("Comp Team")).toBeInTheDocument();
  });

  it("renders the New Group button", async () => {
    renderGroups();
    await waitFor(() => {
      expect(screen.getByText("New Group")).toBeInTheDocument();
    });
  });

  it("shows create form when New Group is clicked", async () => {
    renderGroups();
    await waitFor(() => {
      expect(screen.getByText("New Group")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("New Group"));
    expect(screen.getByTestId("group-form")).toBeInTheDocument();
  });

  it("renders My Groups and Discover tabs", async () => {
    renderGroups();
    await waitFor(() => {
      expect(screen.getByText("My Groups")).toBeInTheDocument();
      expect(screen.getByText("Discover")).toBeInTheDocument();
    });
  });

  it("switches to Discover tab and loads discover groups", async () => {
    const { groupsApi } = await import("../../api/client");
    renderGroups();
    await waitFor(() => {
      expect(screen.getByText("Discover")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Discover"));
    await waitFor(() => {
      expect(groupsApi.discover).toHaveBeenCalled();
    });
  });

  it("shows empty state when no groups exist", async () => {
    const { groupsApi } = await import("../../api/client");
    vi.mocked(groupsApi.list).mockResolvedValueOnce({
      data: { groups: [] },
    } as any);
    renderGroups();
    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    });
    expect(screen.getByText("No groups yet")).toBeInTheDocument();
  });

  it("opens group detail when a group card is clicked", async () => {
    const { groupsApi } = await import("../../api/client");
    renderGroups();
    await waitFor(() => {
      expect(screen.getAllByTestId("group-card")).toHaveLength(2);
    });
    fireEvent.click(screen.getByText("Morning Crew"));
    await waitFor(() => {
      expect(groupsApi.get).toHaveBeenCalledWith(1);
    });
  });
});

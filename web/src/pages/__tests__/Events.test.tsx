import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  eventsApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          events: [
            {
              id: 1,
              name: "IBJJF Sydney Open",
              event_type: "competition",
              event_date: "2026-04-15",
              location: "Sydney Olympic Park",
              weight_class: "Middleweight",
              target_weight: 82,
              division: "Adult Blue Belt",
              notes: "First competition",
              status: "registered",
            },
            {
              id: 2,
              name: "Seminar with Danaher",
              event_type: "seminar",
              event_date: "2026-03-10",
              location: "Gracie Barra HQ",
              weight_class: "",
              target_weight: null,
              division: "",
              notes: "",
              status: "upcoming",
            },
            {
              id: 3,
              name: "Last Month Comp",
              event_type: "competition",
              event_date: "2026-01-15",
              location: "Melbourne",
              weight_class: "",
              target_weight: null,
              division: "",
              notes: "",
              status: "completed",
            },
          ],
        },
      })
    ),
    getNext: vi.fn(() =>
      Promise.resolve({
        data: {
          event: {
            id: 2,
            name: "Seminar with Danaher",
            event_type: "seminar",
            event_date: "2026-03-10",
            location: "Gracie Barra HQ",
            target_weight: null,
            division: "",
            weight_class: "",
          },
          days_until: 19,
          current_weight: null,
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 4 } })),
    update: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  weightLogsApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          logs: [
            { id: 1, weight: 83.5, logged_date: "2026-02-15" },
            { id: 2, weight: 82.8, logged_date: "2026-02-16" },
          ],
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: {} })),
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

vi.mock("../../components/events/PrepChecklist", () => ({
  default: () => <div data-testid="prep-checklist" />,
}));

import Events from "../Events";

function renderEvents() {
  return render(
    <BrowserRouter>
      <Events />
    </BrowserRouter>
  );
}

describe("Events", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Events page heading after data loads", async () => {
    renderEvents();
    await waitFor(() => {
      expect(
        screen.getByText("Events & Competition Prep")
      ).toBeInTheDocument();
    });
  });

  it("renders subtitle text", async () => {
    renderEvents();
    await waitFor(() => {
      expect(
        screen.getByText(
          "Plan competitions, track your weight, and prepare for game day."
        )
      ).toBeInTheDocument();
    });
  });

  it("calls eventsApi.list, eventsApi.getNext, and weightLogsApi.list on mount", async () => {
    const { eventsApi, weightLogsApi } = await import("../../api/client");
    renderEvents();
    await waitFor(() => {
      expect(eventsApi.list).toHaveBeenCalled();
      expect(eventsApi.getNext).toHaveBeenCalled();
      expect(weightLogsApi.list).toHaveBeenCalled();
    });
  });

  it("renders the New Event button", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getByText("New Event")).toBeInTheDocument();
    });
  });

  it("renders the hero countdown section for next event", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getByText("Next Event")).toBeInTheDocument();
    });
    expect(
      screen.getAllByText("Seminar with Danaher").length
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("19").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/days/i).length
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders upcoming events section", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getByText(/Upcoming Events \(2\)/)).toBeInTheDocument();
    });
    expect(screen.getByText("IBJJF Sydney Open")).toBeInTheDocument();
  });

  it("renders the Weight Tracker section", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getByText("Weight Tracker")).toBeInTheDocument();
    });
  });

  it("shows the New Event form when button is clicked", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getByText("New Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("New Event"));
    await waitFor(() => {
      expect(screen.getByText("Event Name *")).toBeInTheDocument();
    });
  });

  it("shows event type badges for upcoming events", async () => {
    renderEvents();
    await waitFor(() => {
      expect(screen.getAllByText("competition").length).toBeGreaterThanOrEqual(
        1
      );
    });
  });

  it("renders edit and delete buttons for each event", async () => {
    renderEvents();
    await waitFor(() => {
      const editButtons = screen.getAllByLabelText("Edit event");
      expect(editButtons.length).toBeGreaterThanOrEqual(2);
      const deleteButtons = screen.getAllByLabelText("Delete event");
      expect(deleteButtons.length).toBeGreaterThanOrEqual(2);
    });
  });
});

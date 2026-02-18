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
  glossaryApi: {
    list: vi.fn(() =>
      Promise.resolve({
        data: {
          movements: [
            {
              id: 1,
              name: "Armbar",
              category: "submission",
              subcategory: "armlock",
              points: 0,
              description: "Classic armbar from closed guard",
              gi_applicable: true,
              nogi_applicable: true,
              custom: false,
              aliases: ["juji gatame"],
            },
            {
              id: 2,
              name: "Scissor Sweep",
              category: "sweep",
              subcategory: "",
              points: 2,
              description: "Sweep from closed guard",
              gi_applicable: true,
              nogi_applicable: true,
              custom: false,
              aliases: [],
            },
            {
              id: 3,
              name: "Custom Move",
              category: "submission",
              subcategory: "",
              points: 0,
              description: "My custom technique",
              gi_applicable: true,
              nogi_applicable: false,
              custom: true,
              aliases: [],
            },
          ],
        },
      })
    ),
    getCategories: vi.fn(() =>
      Promise.resolve({
        data: {
          categories: ["submission", "sweep", "pass", "takedown"],
        },
      })
    ),
    create: vi.fn(() => Promise.resolve({ data: { id: 4 } })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
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
}));

import Glossary from "../Glossary";

function renderGlossary() {
  return render(
    <BrowserRouter>
      <Glossary />
    </BrowserRouter>
  );
}

describe("Glossary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the BJJ Glossary heading after data loads", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText("BJJ Glossary")).toBeInTheDocument();
    });
  });

  it("renders the technique count", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(
        screen.getByText("Showing 3 of 3 techniques")
      ).toBeInTheDocument();
    });
  });

  it("calls glossaryApi.list and glossaryApi.getCategories on mount", async () => {
    const { glossaryApi } = await import("../../api/client");
    renderGlossary();
    await waitFor(() => {
      expect(glossaryApi.list).toHaveBeenCalled();
      expect(glossaryApi.getCategories).toHaveBeenCalled();
    });
  });

  it("renders technique cards", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText("Armbar")).toBeInTheDocument();
    });
    expect(screen.getByText("Scissor Sweep")).toBeInTheDocument();
    expect(screen.getByText("Custom Move")).toBeInTheDocument();
  });

  it("renders category filter buttons", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText(/All \(3\)/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Submissions \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Sweeps \(1\)/)).toBeInTheDocument();
  });

  it("renders the search input", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(
          "Search techniques, descriptions, aliases..."
        )
      ).toBeInTheDocument();
    });
  });

  it("filters techniques by search query", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText("Armbar")).toBeInTheDocument();
    });
    const searchInput = screen.getByPlaceholderText(
      "Search techniques, descriptions, aliases..."
    );
    fireEvent.change(searchInput, { target: { value: "Scissor" } });
    await waitFor(() => {
      expect(screen.getByText("Scissor Sweep")).toBeInTheDocument();
      expect(screen.queryByText("Armbar")).not.toBeInTheDocument();
    });
  });

  it("renders the Add Custom button", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText("Add Custom")).toBeInTheDocument();
    });
  });

  it("shows add custom form when button is clicked", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText("Add Custom")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Add Custom"));
    expect(
      screen.getByText("Add Custom Technique")
    ).toBeInTheDocument();
  });

  it("shows alias text for movements with aliases", async () => {
    renderGlossary();
    await waitFor(() => {
      expect(screen.getByText(/juji gatame/)).toBeInTheDocument();
    });
  });
});

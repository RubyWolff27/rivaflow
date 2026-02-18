import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../api/client", () => ({
  waitlistApi: {
    getCount: vi.fn(() =>
      Promise.resolve({ data: { count: 42 } })
    ),
    join: vi.fn(() =>
      Promise.resolve({
        data: {
          position: 43,
          message: "You're in! We'll notify you when it's your turn.",
        },
      })
    ),
  },
}));

vi.mock("../../hooks/usePageTitle", () => ({
  usePageTitle: vi.fn(),
}));

import Waitlist from "../Waitlist";

function renderWaitlist() {
  return render(
    <BrowserRouter>
      <Waitlist />
    </BrowserRouter>
  );
}

describe("Waitlist", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the RivaFlow heading", () => {
    renderWaitlist();
    expect(screen.getByText("RivaFlow")).toBeInTheDocument();
  });

  it("renders the tagline", () => {
    renderWaitlist();
    expect(
      screen.getByText("Train with intent. Flow to mastery.")
    ).toBeInTheDocument();
  });

  it("renders the Join the Waitlist form heading", () => {
    renderWaitlist();
    expect(screen.getByText("Join the Waitlist")).toBeInTheDocument();
  });

  it("renders the email input field", () => {
    renderWaitlist();
    expect(screen.getByLabelText("Email address *")).toBeInTheDocument();
  });

  it("renders the first name input field", () => {
    renderWaitlist();
    expect(screen.getByLabelText("First name")).toBeInTheDocument();
  });

  it("renders the belt rank selector", () => {
    renderWaitlist();
    expect(screen.getByLabelText("Belt")).toBeInTheDocument();
  });

  it("shows waitlist count", async () => {
    renderWaitlist();
    await waitFor(() => {
      expect(
        screen.getByText("42 people already waiting")
      ).toBeInTheDocument();
    });
  });

  it("renders the submit button", () => {
    renderWaitlist();
    expect(screen.getByText("Join Waitlist")).toBeInTheDocument();
  });

  it("submits the form and shows success state", async () => {
    const { waitlistApi } = await import("../../api/client");
    renderWaitlist();
    const emailInput = screen.getByLabelText("Email address *");
    fireEvent.change(emailInput, {
      target: { value: "test@example.com" },
    });
    fireEvent.click(screen.getByText("Join Waitlist"));
    await waitFor(() => {
      expect(waitlistApi.join).toHaveBeenCalledWith(
        expect.objectContaining({ email: "test@example.com" })
      );
    });
    await waitFor(() => {
      expect(screen.getByText("You're on the list!")).toBeInTheDocument();
    });
    expect(screen.getByText("Position #43")).toBeInTheDocument();
  });

  it("renders feature preview cards", () => {
    renderWaitlist();
    expect(screen.getByText("Session Tracking")).toBeInTheDocument();
    expect(screen.getByText("Streaks & Milestones")).toBeInTheDocument();
    expect(screen.getByText("Training Partners")).toBeInTheDocument();
    expect(screen.getByText("Analytics & Reports")).toBeInTheDocument();
  });
});

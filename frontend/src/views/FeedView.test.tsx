import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FeedView } from "./FeedView";
import type { Opportunity } from "../types";

const filters = {
  keyword: "",
  opportunity_type: "",
  country: "",
  career_stage: "",
  source: "",
  active_only: true,
  min_score: 0,
  include_ignored: false,
  status_filter: "visible",
  sort_by: "match_score",
  sort_order: "desc",
};

const opportunity: Opportunity = {
  id: 11,
  title: "Climate Mobility Grant",
  opportunity_type: "grant",
  source: "horizon_europe",
  url: "https://example.org/climate",
  summary: "Collaborative funding for climate mobility research.",
  eligibility: "Open to early-career researchers.",
  disciplines: ["Environmental Science"],
  keywords: ["climate", "mobility"],
  countries: ["European Union"],
  career_stages: ["early_career"],
  deadline: "2026-10-10",
};

function renderFeed(overrides = {}) {
  const props = {
    filters,
    sourceOptions: ["horizon_europe", "msca"],
    countryOptions: ["European Union", "Germany"],
    keywordOptions: ["climate", "AI"],
    workspaceLoading: false,
    isSignedIn: true,
    activeProfile: false,
    recommendations: [],
    opportunities: [opportunity],
    page: 1,
    hasNextPage: true,
    totalPages: 3,
    totalIsEstimate: false,
    onFiltersChange: vi.fn(),
    onResetFilters: vi.fn(),
    onPageChange: vi.fn(),
    onViewChange: vi.fn(),
    onSelectOpportunity: vi.fn(),
    onStatus: vi.fn(),
    ...overrides,
  };
  render(<FeedView {...props} />);
  return props;
}

describe("FeedView", () => {
  it("renders filter controls, explanation, pagination, and public catalog cards", () => {
    renderFeed();

    expect(screen.getByText("Matches")).toBeInTheDocument();
    expect(screen.getByLabelText(/Keyword search uses Elasticsearch/)).toBeInTheDocument();
    expect(screen.getByText("Browse research opportunities, compare fit, and move promising items into your application workflow.")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("AI, biology, mobility...")).toBeInTheDocument();
    expect(screen.getByLabelText("Sort matches")).toHaveTextContent("Deadline");
    expect(screen.getByRole("button", { name: "Filters active: 0" })).toBeInTheDocument();
    expect(screen.queryByText("Active only")).not.toBeInTheDocument();
    expect(screen.getByText("Climate Mobility Grant")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Previous" })[0]).toBeDisabled();
    expect(screen.getAllByText("Page 1 of 3")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Next" })[0]).toBeEnabled();
  });

  it("applies multi-value filters and pagination actions through callbacks", async () => {
    const user = userEvent.setup();
    const props = renderFeed();

    await user.type(screen.getByPlaceholderText("AI, biology, mobility..."), "climate,");
    await user.click(screen.getByLabelText("Sort matches"));
    await user.click(screen.getByRole("option", { name: "Newest added" }));
    await user.click(screen.getByRole("button", { name: /sort descending/i }));
    await user.click(screen.getByRole("button", { name: "Filters active: 0" }));
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.click(screen.getAllByRole("button", { name: "Next" })[0]);

    expect(props.onFiltersChange).toHaveBeenCalledWith({ ...filters, keyword: "climate" });
    expect(props.onFiltersChange).toHaveBeenCalledWith({ ...filters, sort_by: "created_at" });
    expect(props.onFiltersChange).toHaveBeenCalledWith({ ...filters, sort_order: "asc" });
    expect(props.onPageChange).toHaveBeenCalledWith(2);
    expect(props.onResetFilters).toHaveBeenCalledTimes(1);
  });

  it("opens cards and sends quick status actions for signed-in profiles", async () => {
    const user = userEvent.setup();
    const props = renderFeed({ activeProfile: true, recommendations: [] });
    const card = screen.getByRole("button", { name: /climate mobility grant/i });

    await user.click(within(card).getByRole("button", { name: "Save" }));
    await user.click(card);

    expect(props.onStatus).toHaveBeenCalledWith(11, "saved");
    expect(props.onSelectOpportunity).toHaveBeenCalledWith(opportunity);
  });
});

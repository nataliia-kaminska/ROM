import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { OpportunityDetailsView } from "./OpportunityDetailsView";
import type { Opportunity, Recommendation, StatusRecord } from "../types";

const opportunity: Opportunity = {
  id: 21,
  title: "MSCA Postdoctoral Fellowship",
  opportunity_type: "fellowship",
  source: "msca",
  url: "https://example.org/msca",
  summary: "European fellowship for international postdoctoral mobility.",
  eligibility: "Applicants must hold a doctoral degree and satisfy mobility rules.",
  disciplines: ["Computer Science"],
  keywords: ["AI", "mobility"],
  countries: ["European Union"],
  career_stages: ["postdoc"],
  deadline: "2026-09-15",
  extracted_requirements: {
    career_stages: ["postdoc"],
    countries: ["European Union"],
    required_degree: "phd",
    languages: ["English"],
    publication_expectation: "Publication record is expected.",
    mobility: "Mobility rules apply.",
    citizenship: "",
    years_since_phd: null,
    key_details: ["Requires a host institution before submission."],
    why_it_matters: ["Strong fit for researchers seeking European mobility funding."],
    snippets: ["Applicants must hold a doctoral degree."],
    confidence: 84,
  },
  requirements_confidence: 84,
};

const recommendation: Recommendation = {
  opportunity,
  match_score: 91,
  semantic_score: 80,
  score_breakdown: { semantic: 80, eligibility: 95, deadline: 75, user_history: 60, final: 91 },
  reasons: ["Semantic similarity to your profile is strong (80%)", "Eligible career stage: postdoc"],
  readiness_score: 76,
  gaps: ["Confirm host institution."],
  strengths: ["Strong topic fit."],
  user_status: "saved",
};

const status: StatusRecord = {
  id: 1,
  profile_id: 1,
  opportunity_id: 21,
  status: "saved",
  notes: "",
};

describe("OpportunityDetailsView", () => {
  it("renders full opportunity review sections and match evidence", () => {
    render(
      <OpportunityDetailsView
        opportunity={opportunity}
        recommendation={recommendation}
        reminders={[]}
        assistantResult={null}
        status={status}
        canTrack
        onStatus={vi.fn()}
        onViewChange={vi.fn()}
        onAssistantSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("MSCA Postdoctoral Fellowship")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Eligibility" })).toBeInTheDocument();
    expect(screen.getByText("Eligibility signals")).toBeInTheDocument();
    expect(screen.getByText("Requires a host institution before submission.")).toBeInTheDocument();
    expect(screen.getByText("Strong fit for researchers seeking European mobility funding.")).toBeInTheDocument();
    expect(screen.getAllByText("91%").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText("Fit compass")).toBeInTheDocument();
    expect(screen.getByText("Why it matters")).toBeInTheDocument();
    expect(screen.getByText("Application plan")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute("href", "https://example.org/msca");
  });

  it("updates status and opens assistant workflow", async () => {
    const onStatus = vi.fn();
    const onAssistantSelect = vi.fn();

    render(
      <OpportunityDetailsView
        opportunity={opportunity}
        recommendation={recommendation}
        reminders={[]}
        assistantResult={null}
        status={status}
        canTrack
        onStatus={onStatus}
        onViewChange={vi.fn()}
        onAssistantSelect={onAssistantSelect}
      />,
    );

    fireEvent.change(screen.getByLabelText("Opportunity status"), { target: { value: "1" } });
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Generate advisor memo" }));

    expect(onStatus).toHaveBeenCalledWith(21, "planned");
    expect(onAssistantSelect).toHaveBeenCalledWith(21);
  });
});

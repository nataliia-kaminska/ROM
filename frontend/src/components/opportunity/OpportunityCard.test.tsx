import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { OpportunityCard } from "./OpportunityCard";
import type { Recommendation } from "../../types";

const item: Pick<Recommendation, "opportunity" | "match_score" | "semantic_score" | "score_breakdown" | "reasons" | "user_status"> = {
  opportunity: {
    id: 7,
    title: "AI Mobility Fellowship",
    opportunity_type: "fellowship",
    source: "msca",
    url: "https://example.org/ai-mobility",
    summary: "Funding for applied AI mobility research.",
    eligibility: "Open to PhD and postdoctoral researchers.",
    disciplines: ["Computer Science"],
    keywords: ["AI", "mobility"],
    countries: ["European Union"],
    career_stages: ["phd", "postdoc"],
    deadline: "2026-09-01",
  },
  match_score: 87,
  semantic_score: 72,
  score_breakdown: { semantic: 72, eligibility: 90, deadline: 80, user_history: 60, final: 87 },
  reasons: ["Semantic similarity to your profile is strong (72%)", "Eligible career stage: phd"],
  user_status: null,
};

describe("OpportunityCard", () => {
  it("renders triage information and opens details from card click", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(<OpportunityCard item={item} canTrack actionNote="Sign in" onSelect={onSelect} onStatus={vi.fn()} />);

    expect(screen.getByText("87% match")).toBeInTheDocument();
    expect(screen.getByText("AI Mobility Fellowship")).toBeInTheDocument();
    expect(screen.getByText("Funding for applied AI mobility research.")).toBeInTheDocument();
    expect(screen.getByText("Semantic similarity to your profile is strong (72%)")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /ai mobility fellowship/i }));

    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("saves and ignores without opening the card", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onStatus = vi.fn();

    render(<OpportunityCard item={item} canTrack onSelect={onSelect} onStatus={onStatus} />);

    await user.click(screen.getByRole("button", { name: "Save" }));
    await user.click(screen.getByRole("button", { name: "Ignore" }));

    expect(onStatus).toHaveBeenNthCalledWith(1, "saved");
    expect(onStatus).toHaveBeenNthCalledWith(2, "ignored");
    expect(onSelect).not.toHaveBeenCalled();
  });
});

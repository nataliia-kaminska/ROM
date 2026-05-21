import type { Recommendation } from "../../types";

export function ScoreBreakdown({ item }: { item: Pick<Recommendation, "readiness_score" | "score_breakdown"> }) {
  const entries = [
    ["Topic", item.score_breakdown.semantic, "Topic and text similarity between your profile and the opportunity."],
    ["Eligibility", item.score_breakdown.eligibility, "Fit against career stage, country, parsed requirements, and profile details."],
    ["Deadline", item.score_breakdown.deadline, "Boost for opportunities that are active and actionable soon."],
    ["Readiness", item.readiness_score, "How complete your current profile evidence is for this opportunity."],
    ["History", item.score_breakdown.user_history, "Learns from opportunities you saved, planned, applied to, or ignored."],
  ] as const;
  return (
    <div className="score-bars">
      {entries.map(([name, value, description]) => (
        <div className="score-bar" key={name}>
          <span title={description}>{name}</span>
          <div>
            <i style={{ width: `${Math.max(4, value)}%` }} />
          </div>
          <b>{value}</b>
          <small>{description}</small>
        </div>
      ))}
    </div>
  );
}

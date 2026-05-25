import type React from "react";
import type { OpportunityStatus, Recommendation } from "../../types";
import { addedLabel, deadlineLabel, label, opportunitySummary } from "../../utils/format";

export function OpportunityCard({
  item,
  canTrack,
  actionNote = "Sign in to save or plan",
  onSelect,
  onStatus,
}: {
  item: Pick<Recommendation, "opportunity" | "match_score" | "semantic_score" | "score_breakdown" | "reasons" | "user_status">;
  canTrack: boolean;
  actionNote?: string;
  onSelect: () => void;
  onStatus: (status: OpportunityStatus) => void;
}) {
  const topReasons = item.reasons.slice(0, 2);
  function handleCardKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  }

  function handleQuickStatus(event: React.MouseEvent<HTMLButtonElement>, status: OpportunityStatus) {
    event.stopPropagation();
    onStatus(status);
  }

  return (
    <article className="opportunity-card clickable-card" role="button" tabIndex={0} onClick={onSelect} onKeyDown={handleCardKeyDown}>
      <div className="card-head">
        <span className={item.match_score ? "score" : "score score-muted"}>{item.match_score ? `${item.match_score}% match` : "Catalog"}</span>
        <span className="date-pill deadline-pill"><small>Deadline</small>{deadlineLabel(item.opportunity.deadline).replace(/^Due\s/, "")}</span>
      </div>
      <span className="added-pill">{addedLabel(item.opportunity.created_at)}</span>
      <h3>{item.opportunity.title}</h3>
      <p className="card-summary">{opportunitySummary(item.opportunity)}</p>
      <div className="chips">
        <span>{label(item.opportunity.opportunity_type)}</span>
        <span>{item.opportunity.source}</span>
        {canTrack && <span className={`status-chip status-${item.user_status ?? "browsing"}`}>{label(item.user_status ?? "browsing")}</span>}
      </div>
      {topReasons.length > 0 && (
        <ul className="reasons">
          {topReasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <div className="actions">
        {canTrack ? (
          <>
            <button className="secondary" title="Keep this opportunity for later." onClick={(event) => handleQuickStatus(event, "saved")}>
              Save
            </button>
            <button className="tertiary" title="Hide this kind of result and teach ranking preferences." onClick={(event) => handleQuickStatus(event, "ignored")}>
              Ignore
            </button>
          </>
        ) : (
          <span className="card-action-note">{actionNote}</span>
        )}
      </div>
    </article>
  );
}

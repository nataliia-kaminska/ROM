import type React from "react";
import type { OpportunityStatus, Recommendation } from "../../types";
import { label } from "../../utils/format";

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
        <span className="deadline-pill">{item.opportunity.deadline ?? "No deadline"}</span>
      </div>
      <h3>{item.opportunity.title}</h3>
      <p className="card-summary">{item.opportunity.summary || "No summary provided."}</p>
      <div className="chips">
        <span>{label(item.opportunity.opportunity_type)}</span>
        <span>{item.opportunity.source}</span>
        {item.user_status && <span>{label(item.user_status)}</span>}
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

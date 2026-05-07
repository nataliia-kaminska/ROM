import type { OpportunityStatus, Recommendation } from "../../types";
import { label } from "../../utils/format";

export function OpportunityCard({
  item,
  canTrack,
  onSelect,
  onStatus,
}: {
  item: Pick<Recommendation, "opportunity" | "match_score" | "semantic_score" | "score_breakdown" | "reasons" | "user_status">;
  canTrack: boolean;
  onSelect: () => void;
  onStatus: (status: OpportunityStatus) => void;
}) {
  return (
    <article className="opportunity-card">
      <div className="card-head">
        <span className="score">{item.match_score ? `${item.match_score}%` : "Catalog"}</span>
        {item.semantic_score ? <span>Semantic {item.semantic_score}%</span> : null}
        <span>{item.opportunity.deadline ?? "No deadline"}</span>
      </div>
      <h3>{item.opportunity.title}</h3>
      <p>{item.opportunity.summary || "No summary provided."}</p>
      <div className="chips">
        <span>{label(item.opportunity.opportunity_type)}</span>
        <span>{item.opportunity.source}</span>
        {item.user_status && <span>{label(item.user_status)}</span>}
      </div>
      {item.match_score > 0 && (
        <div className="score-grid">
          <span>Semantic {item.score_breakdown.semantic}</span>
          <span>Eligibility {item.score_breakdown.eligibility}</span>
          <span>Deadline {item.score_breakdown.deadline}</span>
          <span>History {item.score_breakdown.user_history}</span>
        </div>
      )}
      {item.reasons.length > 0 && (
        <ul className="reasons">
          {item.reasons.slice(0, 3).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <div className="actions">
        <button className="secondary" onClick={onSelect}>
          Details
        </button>
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Keep this opportunity for later." : "Create a profile before saving opportunities."} onClick={() => onStatus("saved")}>
          Save
        </button>
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Add this opportunity to your application plan." : "Create a profile before planning opportunities."} onClick={() => onStatus("planned")}>
          Plan
        </button>
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Hide this kind of result and teach ranking preferences." : "Create a profile before ignoring opportunities."} onClick={() => onStatus("ignored")}>
          Ignore
        </button>
      </div>
    </article>
  );
}

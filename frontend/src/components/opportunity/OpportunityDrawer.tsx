import type { View } from "../../constants";
import type { ApplicationAssistantResult, Opportunity, OpportunityStatus, Recommendation, Reminder, StatusRecord } from "../../types";
import { label, opportunitySummary } from "../../utils/format";
import { ScoreBreakdown } from "./ScoreBreakdown";

export function OpportunityDrawer({
  selectedOpportunity,
  selectedRecommendation,
  selectedOpportunityReminders,
  assistantResult,
  selectedStatusIds,
  statusByOpportunity,
  canTrack,
  onClose,
  onStatus,
  setAssistantForm,
  setView,
  onOpenFullDetails,
}: {
  selectedOpportunity: Opportunity;
  selectedRecommendation: Recommendation | null;
  selectedOpportunityReminders: Reminder[];
  assistantResult: ApplicationAssistantResult | null;
  selectedStatusIds: ReadonlySet<number>;
  statusByOpportunity: ReadonlyMap<number, StatusRecord>;
  canTrack: boolean;
  onClose: () => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
  setAssistantForm: (form: { opportunity_id: string }) => void;
  setView: (view: View) => void;
  onOpenFullDetails: (opportunityId: number) => void;
}) {
  const topReasons = selectedRecommendation?.reasons.slice(0, 3) ?? [];
  const currentStatus = statusByOpportunity.get(selectedOpportunity.id);
  const currentAssistant = assistantResult?.opportunity_id === selectedOpportunity.id ? assistantResult : null;

  return (
    <div className="drawer" role="dialog" aria-modal="true" onClick={onClose}>
      <article className="quick-drawer" onClick={(event) => event.stopPropagation()}>
        <button className="close" onClick={onClose}>
          x
        </button>
        <p className="eyebrow">{selectedOpportunity.source}</p>
        <h2>{selectedOpportunity.title}</h2>
        <div className="meta">
          <span>{label(selectedOpportunity.opportunity_type)}</span>
          <span>{selectedOpportunity.deadline ?? "No deadline"}</span>
          {currentStatus && <span>{label(currentStatus.status)}</span>}
        </div>
        <p>{opportunitySummary(selectedOpportunity)}</p>
        {selectedRecommendation && (
          <div className="intelligence-panel">
            <strong>{selectedRecommendation.match_score}% match</strong>
            <ScoreBreakdown item={selectedRecommendation} />
          </div>
        )}
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
              <button className="secondary" type="button" onClick={() => onStatus(selectedOpportunity.id, "saved")}>
                Save
              </button>
              <button className="tertiary" type="button" onClick={() => onStatus(selectedOpportunity.id, "ignored")}>
                Ignore
              </button>
            </>
          ) : (
            <span className="card-action-note">Sign in to save or plan</span>
          )}
          <button className="primary" type="button" onClick={() => onOpenFullDetails(selectedOpportunity.id)}>
            View full details
          </button>
        </div>
        <div className="quick-drawer-foot">
          {currentAssistant ? <span>{currentAssistant.readiness_score}% advisor readiness</span> : <span>{canTrack ? selectedStatusIds.has(selectedOpportunity.id) ? "Assistant ready from Apply Assistant" : "Save to unlock advisor planning" : "Create an account for personalized planning"}</span>}
          {selectedOpportunityReminders.length > 0 && <span>{selectedOpportunityReminders.length} reminder{selectedOpportunityReminders.length === 1 ? "" : "s"}</span>}
          <button
            className="tertiary"
            disabled={!selectedStatusIds.has(selectedOpportunity.id)}
            onClick={() => {
              setAssistantForm({ opportunity_id: String(selectedOpportunity.id) });
              setView("assistant");
              onClose();
            }}
          >
            Open assistant
          </button>
        </div>
        <a className="secondary link-button" href={selectedOpportunity.url} target="_blank" rel="noreferrer">
          Open source
        </a>
        {!currentStatus && (
          <p className="muted">Click the card title area for a quick check, then open full details when it looks worth deeper review.</p>
        )}
      </article>
    </div>
  );
}

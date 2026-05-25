import type { View } from "../../constants";
import { displayStatuses } from "../../constants";
import type { ApplicationAssistantResult, DisplayOpportunityStatus, Opportunity, Recommendation, Reminder, StatusRecord } from "../../types";
import { CustomSelect } from "../ui";
import { addedLabel, deadlineLabel, label, opportunitySummary } from "../../utils/format";
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
  onStatus: (opportunityId: number, status: DisplayOpportunityStatus) => void;
  setAssistantForm: (form: { opportunity_id: string }) => void;
  setView: (view: View) => void;
  onOpenFullDetails: (opportunityId: number) => void;
}) {
  const topReasons = selectedRecommendation?.reasons.slice(0, 3) ?? [];
  const currentStatus = statusByOpportunity.get(selectedOpportunity.id);
  const currentAssistant = assistantResult?.opportunity_id === selectedOpportunity.id ? assistantResult : null;
  const nearestReminder = [...selectedOpportunityReminders].sort((a, b) => a.remind_on.localeCompare(b.remind_on))[0] ?? null;

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
          <span>{deadlineLabel(selectedOpportunity.deadline)}</span>
          <span>{addedLabel(selectedOpportunity.created_at)}</span>
          {currentStatus && <span className={`status-chip status-${currentStatus.status}`}>{label(currentStatus.status)}</span>}
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
        <div className="actions drawer-primary-actions">
          {!canTrack && <span className="card-action-note">Sign in to save or plan</span>}
          <button className="primary" type="button" onClick={() => onOpenFullDetails(selectedOpportunity.id)}>
            View full details
          </button>
          <a className="secondary" href={selectedOpportunity.url} target="_blank" rel="noreferrer">
            Open source
          </a>
        </div>
        {canTrack && (
          <div className="drawer-status-select">
            <span>Status</span>
            <CustomSelect
              value={currentStatus?.status ?? "browsing"}
              ariaLabel="Opportunity status"
              options={displayStatuses.map((status) => ({ value: status, label: label(status) }))}
              onChange={(status: DisplayOpportunityStatus) => onStatus(selectedOpportunity.id, status)}
            />
          </div>
        )}
        <div className="quick-drawer-foot">
          <div>
            <span>{currentAssistant ? `${currentAssistant.readiness_score}% advisor readiness` : canTrack ? selectedStatusIds.has(selectedOpportunity.id) ? "Apply assistant is ready" : "Save to unlock advisor planning" : "Create an account for personalized planning"}</span>
            <button
              className="primary assistant-drawer-button"
              disabled={!selectedStatusIds.has(selectedOpportunity.id)}
              onClick={() => {
                setAssistantForm({ opportunity_id: String(selectedOpportunity.id) });
                setView("assistant");
                onClose();
              }}
            >
              Plan with assistant
            </button>
          </div>
          {nearestReminder && (
            <div>
              <span>{selectedOpportunityReminders.length} reminder{selectedOpportunityReminders.length === 1 ? "" : "s"}</span>
              <strong>{nearestReminder.remind_on}</strong>
            </div>
          )}
        </div>
        {!currentStatus && (
          <p className="muted">Click the card title area for a quick check, then open full details when it looks worth deeper review.</p>
        )}
      </article>
    </div>
  );
}

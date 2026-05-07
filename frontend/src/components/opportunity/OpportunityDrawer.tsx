import type { DetailTab, View } from "../../constants";
import { detailTabLabels, trackedStatuses } from "../../constants";
import type { ApplicationAssistantResult, Opportunity, OpportunityStatus, Recommendation, Reminder, StatusRecord } from "../../types";
import { label, statusHelp } from "../../utils/format";
import { EmptyState } from "../ui";
import { RequirementSummary } from "./RequirementSummary";
import { ScoreBreakdown } from "./ScoreBreakdown";

export function OpportunityDrawer({
  selectedOpportunity,
  selectedRecommendation,
  selectedOpportunityReminders,
  assistantResult,
  selectedStatusIds,
  statusByOpportunity,
  detailTab,
  setDetailTab,
  onClose,
  onStatus,
  setAssistantForm,
  setView,
}: {
  selectedOpportunity: Opportunity;
  selectedRecommendation: Recommendation | null;
  selectedOpportunityReminders: Reminder[];
  assistantResult: ApplicationAssistantResult | null;
  selectedStatusIds: ReadonlySet<number>;
  statusByOpportunity: ReadonlyMap<number, StatusRecord>;
  detailTab: DetailTab;
  setDetailTab: (tab: DetailTab) => void;
  onClose: () => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
  setAssistantForm: (form: { opportunity_id: string }) => void;
  setView: (view: View) => void;
}) {
  return (
    <div className="drawer" role="dialog" aria-modal="true">
      <article>
        <button className="close" onClick={onClose}>
          x
        </button>
        <p className="eyebrow">{selectedOpportunity.source}</p>
        <h2>{selectedOpportunity.title}</h2>
        <div className="meta">
          <span>{label(selectedOpportunity.opportunity_type)}</span>
          <span>{selectedOpportunity.deadline ?? "No deadline"}</span>
        </div>
        {selectedRecommendation && (
          <div className="intelligence-panel">
            <strong>{selectedRecommendation.match_score}% match</strong>
            <ScoreBreakdown item={selectedRecommendation} />
          </div>
        )}
        <div className="tabs">
          {(["overview", "reasons", "eligibility", "assistant", "reminders"] as const).map((tab) => (
            <button className={detailTab === tab ? "active" : ""} key={tab} onClick={() => setDetailTab(tab)}>
              {detailTabLabels[tab]}
            </button>
          ))}
        </div>
        {detailTab === "overview" && (
          <>
            <p>{selectedOpportunity.summary || "No summary provided."}</p>
            <div className="chips">
              {[...selectedOpportunity.disciplines, ...selectedOpportunity.keywords, ...selectedOpportunity.countries].map((chip) => (
                <span key={chip}>{chip}</span>
              ))}
            </div>
          </>
        )}
        {detailTab === "reasons" && (
          selectedRecommendation ? (
            <div className="explanation-grid">
              {selectedRecommendation.reasons.map((reason) => (
                <article key={reason}>
                  <strong>{reason.includes("lower") ? "Risk" : "Signal"}</strong>
                  <p>{reason}</p>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No match reasons" detail="Recommendations explain semantic, eligibility, deadline, and history signals once a profile is selected." />
          )
        )}
        {detailTab === "eligibility" && (
          <>
            <h3>Eligibility</h3>
            <p>{selectedOpportunity.eligibility || "No eligibility text provided."}</p>
            <RequirementSummary opportunity={selectedOpportunity} />
            <div className="score-grid">
              <span>Career stages {selectedOpportunity.career_stages.join(", ") || "Not specified"}</span>
              <span>Countries {selectedOpportunity.countries.join(", ") || "Not specified"}</span>
            </div>
          </>
        )}
        {detailTab === "assistant" && (
          <div>
            {assistantResult?.opportunity_id === selectedOpportunity.id ? (
              <>
                <h3>Research Fit</h3>
                <p>{assistantResult.research_fit_statement}</p>
                <h3>Readiness</h3>
                <p>{assistantResult.readiness_score}% application readiness</p>
                <h3>Advisor Memo</h3>
                <p>{assistantResult.advisor_memo}</p>
                <h3>Warnings</h3>
                <ul className="reasons">{(assistantResult.eligibility_warnings.length ? assistantResult.eligibility_warnings : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
                <h3>Gaps</h3>
                <ul className="reasons">{(assistantResult.gap_analysis.length ? assistantResult.gap_analysis : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
              </>
            ) : (
              <button
                className="primary"
                disabled={!selectedStatusIds.has(selectedOpportunity.id)}
                onClick={() => {
                  setAssistantForm({ opportunity_id: String(selectedOpportunity.id) });
                  setView("assistant");
                  onClose();
                }}
              >
                {selectedStatusIds.has(selectedOpportunity.id) ? "Open assistant for this opportunity" : "Save or plan to use assistant"}
              </button>
            )}
          </div>
        )}
        {detailTab === "reminders" && (
          <div className="table">
            {selectedOpportunityReminders.map((reminder) => (
              <div className="table-row compact-row" key={reminder.id}>
                <span>{reminder.message || "Deadline reminder"}</span>
                <span>{reminder.remind_on}</span>
                <span>{label(reminder.status)}</span>
              </div>
            ))}
            {selectedOpportunityReminders.length === 0 && <EmptyState title="No reminders for this opportunity" detail="Saving or planning opportunities can create deadline reminders automatically." />}
          </div>
        )}
        <a className="primary link-button" href={selectedOpportunity.url} target="_blank" rel="noreferrer">
          Open source
        </a>
        <div className="actions">
          {trackedStatuses.map((status) => (
            <button key={status} className="secondary" title={statusHelp(status)} onClick={() => onStatus(selectedOpportunity.id, status)}>
              {label(status)}
            </button>
          ))}
        </div>
        {statusByOpportunity.get(selectedOpportunity.id) && (
          <p className="muted">Current status: {label(statusByOpportunity.get(selectedOpportunity.id)!.status)}</p>
        )}
      </article>
    </div>
  );
}

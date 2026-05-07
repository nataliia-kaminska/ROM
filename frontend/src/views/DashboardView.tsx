import type { Reminder, Recommendation, StatusRecord } from "../types";
import type { View } from "../constants";
import type { OpportunityStatus, Opportunity } from "../types";
import { OpportunityCard } from "../components/opportunities";
import { EmptyState } from "../components/ui";

export function DashboardView({
  nextAction,
  topMatches,
  plannedStatuses,
  nextReminder,
  opportunitiesById,
  canTrack,
  onViewChange,
  onSelectOpportunity,
  onStatus,
}: {
  nextAction: { title: string; detail: string; target: View };
  topMatches: Recommendation[];
  plannedStatuses: StatusRecord[];
  nextReminder: Reminder | null;
  opportunitiesById: ReadonlyMap<number, Opportunity>;
  canTrack: boolean;
  onViewChange: (view: View) => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
}) {
  return (
    <section className="dashboard-grid">
      <article className="panel next-action">
        <p className="eyebrow">Next best action</p>
        <h2>{nextAction.title}</h2>
        <p>{nextAction.detail}</p>
        <button className="primary" onClick={() => onViewChange(nextAction.target)}>
          Go there
        </button>
      </article>
      <article className="panel metric-panel">
        <span>Top matches</span>
        <strong>{topMatches.length}</strong>
        <p className="muted">High-signal opportunities ready for review.</p>
      </article>
      <article className="panel metric-panel">
        <span>In application plan</span>
        <strong>{plannedStatuses.length}</strong>
        <p className="muted">Planned or submitted opportunities.</p>
      </article>
      <article className="panel metric-panel">
        <span>Next reminder</span>
        <strong>{nextReminder?.remind_on ?? "None"}</strong>
        <p className="muted">{nextReminder ? opportunitiesById.get(nextReminder.opportunity_id)?.title ?? "Opportunity reminder" : "Plan an opportunity to start reminders."}</p>
      </article>
      <section className="panel span-2">
        <div className="section-title">
          <div>
            <h2>Strongest Matches</h2>
            <p>Review these first, then save, plan, or ignore to teach the system.</p>
          </div>
          <button className="secondary" onClick={() => onViewChange("feed")}>
            Open matches
          </button>
        </div>
        <div className="cards compact-cards">
          {topMatches.map((item) => (
            <OpportunityCard
              key={item.opportunity.id}
              item={item}
              canTrack={canTrack}
              onSelect={() => onSelectOpportunity(item.opportunity)}
              onStatus={(status) => onStatus(item.opportunity.id, status)}
            />
          ))}
          {topMatches.length === 0 && <EmptyState title="No matches yet" detail="Complete your profile or import opportunities, then refresh the workspace." />}
        </div>
      </section>
      <section className="panel workflow-panel">
        <h2>Workspace Guide</h2>
        <div className="workflow-list">
          <button type="button" onClick={() => onViewChange("profile")}>
            <strong>Profile</strong>
            <span>Controls eligibility, keywords, readiness, and gaps.</span>
          </button>
          <button type="button" onClick={() => onViewChange("feed")}>
            <strong>Matches</strong>
            <span>Review ranked opportunities and teach preferences.</span>
          </button>
          <button type="button" onClick={() => onViewChange("assistant")}>
            <strong>Apply Assistant</strong>
            <span>Turns saved/planned opportunities into an application plan.</span>
          </button>
        </div>
      </section>
    </section>
  );
}

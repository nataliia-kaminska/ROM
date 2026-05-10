import type { Reminder, Recommendation, StatusRecord } from "../types";
import type { View } from "../constants";
import type { OpportunityStatus, Opportunity } from "../types";
import { OpportunityCard } from "../components/opportunities";
import { EmptyState } from "../components/ui";

export function DashboardView({
  nextAction,
  topMatches,
  plannedStatuses,
  statuses,
  nextReminder,
  opportunitiesById,
  canTrack,
  onViewChange,
  onProfileFocus,
  onSelectOpportunity,
  onStatus,
}: {
  nextAction: { title: string; detail: string; target: View; focusFields?: string[] };
  topMatches: Recommendation[];
  plannedStatuses: StatusRecord[];
  statuses: StatusRecord[];
  nextReminder: Reminder | null;
  opportunitiesById: ReadonlyMap<number, Opportunity>;
  canTrack: boolean;
  onViewChange: (view: View) => void;
  onProfileFocus: (fields: string[]) => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
}) {
  const recentSavedStatus = [...statuses]
    .filter((status) => ["saved", "planned", "applied"].includes(status.status))
    .sort((a, b) => b.id - a.id)[0] ?? null;
  const recentSavedOpportunity = recentSavedStatus ? opportunitiesById.get(recentSavedStatus.opportunity_id) ?? null : null;

  return (
    <section className="dashboard-grid">
      <article className="panel next-action">
        <p className="eyebrow">Next best action</p>
        <h2>{nextAction.title}</h2>
        <p>{nextAction.detail}</p>
        <button
          className="primary"
          onClick={() => {
            if (nextAction.target === "profile") {
              onProfileFocus(nextAction.focusFields ?? []);
            }
            onViewChange(nextAction.target);
          }}
        >
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
      <article className="panel reminder-panel">
        <div className="reminder-split">
          <div>
            <span>Next reminder</span>
            <strong>{nextReminder?.remind_on ?? "None"}</strong>
            <p className="muted">{nextReminder ? opportunitiesById.get(nextReminder.opportunity_id)?.title ?? "Opportunity reminder" : "Plan an opportunity to start reminders."}</p>
          </div>
          <div>
            <span>Latest saved</span>
            {recentSavedOpportunity ? (
              <button className="recent-link" type="button" onClick={() => onSelectOpportunity(recentSavedOpportunity)}>
                {recentSavedOpportunity.title}
              </button>
            ) : (
              <p className="muted">Save an opportunity to keep it visible here.</p>
            )}
          </div>
        </div>
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
          {topMatches.length === 0 && <EmptyState title="No matches yet" detail="Complete your profile or import opportunities, then open Matches to review the latest results." />}
        </div>
      </section>
    </section>
  );
}

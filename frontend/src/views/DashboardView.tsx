import type { Reminder, Recommendation, StatusRecord } from "../types";
import type { View } from "../constants";
import type { OpportunityStatus, Opportunity } from "../types";
import { OpportunityCard } from "../components/opportunities";
import { EmptyState, PageHeader } from "../components/ui";
import { deadlineLabel, label } from "../utils/format";

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
  const currentStatuses = latestStatusesByOpportunity(statuses);
  const pipeline = ["saved", "planned", "applied"] as const;
  const pipelineItems = pipeline.map((status) => {
    const records = currentStatuses.filter((item) => item.status === status);
    return {
      status,
      count: records.length,
    };
  });
  const trackedDeadlines = currentStatuses
    .filter((status) => ["saved", "planned", "applied"].includes(status.status))
    .map((status) => opportunitiesById.get(status.opportunity_id) ?? null)
    .filter((opportunity): opportunity is Opportunity => Boolean(opportunity?.deadline))
    .sort((a, b) => String(a.deadline).localeCompare(String(b.deadline)));
  const visibleDeadlines = trackedDeadlines.slice(0, 5);
  const visibleTopMatches = topMatches.slice(0, 2);

  return (
    <section className="dashboard-page">
      <PageHeader
        title="Dashboard"
        description="Your daily control room for profile gaps, tracked applications, strongest matches, and upcoming deadlines."
        hint="The dashboard summarizes the latest workspace data. Open Matches for discovery, Board for status work, and Reminders for dates."
      />
      <div className="dashboard-grid">
      <article className="panel next-action">
        <p className="eyebrow">Do this next</p>
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
      <article className="panel dashboard-pipeline">
        <div className="section-title">
          <div>
            <h2>Application board</h2>
            <p>Current tracked work by status.</p>
          </div>
          <button className="secondary" type="button" onClick={() => onViewChange("board")}>Open board</button>
        </div>
        <div className="dashboard-mini-board">
          {pipelineItems.map((lane) => (
            <button className={`dashboard-lane status-surface status-${lane.status}`} key={lane.status} type="button" onClick={() => onViewChange("board")}>
              <span>{label(lane.status)}</span>
              <strong>{lane.count}</strong>
              <small>{pipelineHint(lane.status, lane.count)}</small>
            </button>
          ))}
        </div>
      </article>
      <article className="panel dashboard-deadlines">
        <div className="section-title">
          <div>
            <h2>Upcoming deadlines</h2>
            <p>Nearest tracked deadlines and reminders.</p>
          </div>
        </div>
        <div className="deadline-scroll">
          {nextReminder && (
            <button className="deadline-reminder" type="button" onClick={() => onViewChange("reminders")}>
              Reminder: {nextReminder.remind_on}
            </button>
          )}
          <div className="deadline-list">
            {visibleDeadlines.map((opportunity) => (
              <button type="button" key={opportunity.id} onClick={() => onSelectOpportunity(opportunity)}>
                <span>{deadlineLabel(opportunity.deadline)}</span>
                <strong>{opportunity.title}</strong>
                <small>{deadlineDistance(opportunity.deadline)}</small>
              </button>
            ))}
            {trackedDeadlines.length === 0 && <p className="muted">Save or plan opportunities with deadlines to build a timeline here.</p>}
          </div>
          {trackedDeadlines.length > 5 && (
            <button className="secondary" type="button" onClick={() => onViewChange("reminders")}>
              Show all reminders
            </button>
          )}
        </div>
      </article>
      <section className="panel dashboard-strongest">
        <div className="section-title">
          <div>
            <h2>Strongest matches</h2>
            <p>Review these first, then save, plan, or ignore to teach the system.</p>
          </div>
          <button className="secondary" onClick={() => onViewChange("feed")}>
            Open matches
          </button>
        </div>
        <div className="cards compact-cards">
          {visibleTopMatches.map((item) => (
            <OpportunityCard
              key={item.opportunity.id}
              item={item}
              canTrack={canTrack}
              onSelect={() => onSelectOpportunity(item.opportunity)}
              onStatus={(status) => onStatus(item.opportunity.id, status)}
            />
          ))}
          {visibleTopMatches.length === 0 && <EmptyState title="No matches yet" detail="Complete your profile or import opportunities, then open Matches to review the latest results." />}
        </div>
      </section>
      </div>
    </section>
  );
}

function latestStatusesByOpportunity(statuses: StatusRecord[]): StatusRecord[] {
  const byOpportunity = new Map<number, StatusRecord>();
  for (const status of statuses) {
    const current = byOpportunity.get(status.opportunity_id);
    if (!current || status.id > current.id) {
      byOpportunity.set(status.opportunity_id, status);
    }
  }
  return [...byOpportunity.values()];
}

function pipelineHint(status: "saved" | "planned" | "applied", count: number): string {
  if (count === 0) return "No current cards";
  if (status === "saved") return "Ready to review";
  if (status === "planned") return "Being prepared";
  return "Submitted or in progress";
}

function deadlineDistance(deadline: string | null): string {
  if (!deadline) return "No date";
  const target = new Date(`${deadline}T00:00:00`);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.ceil((target.getTime() - today.getTime()) / 86400000);
  if (days < 0) return "Passed";
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  return `${days} days left`;
}

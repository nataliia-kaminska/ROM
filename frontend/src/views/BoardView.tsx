import type { Opportunity, OpportunityStatus, StatusRecord } from "../types";
import { trackedStatuses } from "../constants";
import { label, statusHelp } from "../utils/format";

export function BoardView({
  statuses,
  opportunitiesById,
  onSelectOpportunity,
}: {
  statuses: StatusRecord[];
  opportunitiesById: ReadonlyMap<number, Opportunity>;
  onSelectOpportunity: (opportunity: Opportunity) => void;
}) {
  return (
    <section className="board">
      {trackedStatuses.map((status: OpportunityStatus) => (
        <div className="lane" key={status}>
          <div>
            <h2>{label(status)}</h2>
            <small>{statusHelp(status)}</small>
          </div>
          {statuses
            .filter((record) => record.status === status)
            .map((record) => opportunitiesById.get(record.opportunity_id))
            .filter(Boolean)
            .map((opportunity) => (
              <article className="mini-card" key={opportunity!.id} onClick={() => onSelectOpportunity(opportunity!)}>
                <strong>{opportunity!.title}</strong>
                <small>{opportunity!.deadline ?? "No deadline"}</small>
              </article>
            ))}
        </div>
      ))}
    </section>
  );
}

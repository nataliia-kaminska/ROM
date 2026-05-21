import { useState } from "react";
import type { Opportunity, OpportunityStatus, StatusRecord } from "../types";
import { trackedStatuses } from "../constants";
import { label, statusHelp } from "../utils/format";

export function BoardView({
  statuses,
  opportunitiesById,
  onSelectOpportunity,
  onStatus,
}: {
  statuses: StatusRecord[];
  opportunitiesById: ReadonlyMap<number, Opportunity>;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
}) {
  const [dragged, setDragged] = useState<{ opportunityId: number; status: OpportunityStatus } | null>(null);
  const [dragOverStatus, setDragOverStatus] = useState<OpportunityStatus | null>(null);
  const [suppressClick, setSuppressClick] = useState(false);

  function handleDrop(nextStatus: OpportunityStatus) {
    if (!dragged) return;
    if (dragged.status !== nextStatus) {
      onStatus(dragged.opportunityId, nextStatus);
    }
    setDragged(null);
    setDragOverStatus(null);
  }

  return (
    <section className="board">
      {trackedStatuses.map((status: OpportunityStatus) => (
        <div
          className={`lane ${dragOverStatus === status ? "lane-drop-target" : ""}`}
          key={status}
          onDragOver={(event) => {
            event.preventDefault();
            if (dragged) {
              event.dataTransfer.dropEffect = dragged.status === status ? "none" : "move";
              setDragOverStatus(status);
            }
          }}
          onDragLeave={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
              setDragOverStatus(null);
            }
          }}
          onDrop={(event) => {
            event.preventDefault();
            handleDrop(status);
          }}
        >
          <div>
            <h2>{label(status)}</h2>
            <small>{statusHelp(status)}</small>
          </div>
          {statuses
            .filter((record) => record.status === status)
            .map((record) => opportunitiesById.get(record.opportunity_id))
            .filter(Boolean)
            .map((opportunity) => (
              <article
                className="mini-card draggable-card"
                draggable
                key={opportunity!.id}
                title="Drag to another column or click to open details"
                onClick={() => {
                  if (!suppressClick) onSelectOpportunity(opportunity!);
                }}
                onDragStart={(event) => {
                  setDragged({ opportunityId: opportunity!.id, status });
                  setSuppressClick(true);
                  event.dataTransfer.effectAllowed = "move";
                  event.dataTransfer.setData("text/plain", String(opportunity!.id));
                }}
                onDragEnd={() => {
                  setDragged(null);
                  setDragOverStatus(null);
                  window.setTimeout(() => setSuppressClick(false), 0);
                }}
              >
                <strong>{opportunity!.title}</strong>
                <small>{opportunity!.deadline ?? "No deadline"}</small>
              </article>
            ))}
        </div>
      ))}
    </section>
  );
}

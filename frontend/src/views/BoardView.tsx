import { useState } from "react";
import type { Opportunity, OpportunityStatus, StatusRecord } from "../types";
import { trackedStatuses } from "../constants";
import { deadlineLabel, label, statusHelp } from "../utils/format";
import { PageHeader } from "../components/ui";

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
  const currentStatuses = latestStatusesByOpportunity(statuses);

  function handleDrop(nextStatus: OpportunityStatus) {
    if (!dragged) return;
    if (dragged.status !== nextStatus) {
      onStatus(dragged.opportunityId, nextStatus);
    }
    setDragged(null);
    setDragOverStatus(null);
  }

  return (
    <section className="board-page">
      <PageHeader
        title="Application board"
        description="Move saved opportunities through planning, submission, and final outcomes."
        hint="Drag cards between columns or click a card to inspect details before changing status."
      />
      <div className="board">
      {trackedStatuses.map((status: OpportunityStatus) => (
        <div
          className={`lane lane-${status} ${dragOverStatus === status ? "lane-drop-target" : ""}`}
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
          {currentStatuses
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
                <small>{deadlineLabel(opportunity!.deadline)}</small>
              </article>
            ))}
        </div>
      ))}
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

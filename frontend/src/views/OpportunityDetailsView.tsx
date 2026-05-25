import type { ApplicationAssistantResult, DisplayOpportunityStatus, Opportunity, OpportunityStatus, Recommendation, Reminder, StatusRecord } from "../types";
import type { View } from "../constants";
import { displayStatuses } from "../constants";
import { EmptyState, PageHeader } from "../components/ui";
import { RequirementSummary, ScoreBreakdown } from "../components/opportunities";
import { addedLabel, deadlineLabel, formatDate, label, opportunityEligibility, opportunitySummary, statusHelp } from "../utils/format";

export function OpportunityDetailsView({
  opportunity,
  recommendation,
  reminders,
  assistantResult,
  status,
  canTrack,
  onStatus,
  onViewChange,
  onAssistantSelect,
}: {
  opportunity: Opportunity | null;
  recommendation: Recommendation | null;
  reminders: Reminder[];
  assistantResult: ApplicationAssistantResult | null;
  status: StatusRecord | null;
  canTrack: boolean;
  onStatus: (opportunityId: number, status: DisplayOpportunityStatus) => void;
  onViewChange: (view: View) => void;
  onAssistantSelect: (opportunityId: number) => void;
}) {
  if (!opportunity) {
    return (
      <section className="panel">
        <EmptyState title="Opportunity not found" detail="This item is not in the current catalog cache. Go back to Matches and open it again." />
        <button className="secondary" type="button" onClick={() => onViewChange("feed")}>
          Back to matches
        </button>
      </section>
    );
  }

  const currentAssistant = assistantResult?.opportunity_id === opportunity.id ? assistantResult : null;
  const currentStatus = status?.status ?? recommendation?.user_status ?? null;

  return (
    <section className="opportunity-detail-page">
      <PageHeader
        title="Opportunity details"
        description="Review the source content, fit evidence, status, and preparation signals for this opportunity."
        hint="Detailed text comes from imported source fields and AI-assisted parsing. Always verify final eligibility on the official source page."
      />
      <div className="detail-hero panel">
        <div>
          <p className="eyebrow">{opportunity.source}</p>
          <h2>{opportunity.title}</h2>
          <div className="meta">
            <span>{label(opportunity.opportunity_type)}</span>
            <span>{deadlineLabel(opportunity.deadline)}</span>
            <span>{addedLabel(opportunity.created_at)}</span>
            {currentStatus && <span className={`status-chip status-${currentStatus}`}>{label(currentStatus)}</span>}
          </div>
        </div>
        <div className="detail-hero-actions">
          <a className="primary" href={opportunity.url} target="_blank" rel="noreferrer">
            Open source
          </a>
        </div>
      </div>

      <div className="detail-grid">
        <article className="panel detail-main">
          <h3>Description</h3>
          <p>{opportunitySummary(opportunity)}</p>
          <DetailList title="Key details" items={opportunity.extracted_requirements?.key_details ?? []} />
          <h3>Eligibility</h3>
          <p>{opportunityEligibility(opportunity)}</p>
          <RequirementSummary opportunity={opportunity} />
          <div className="chips">
            {[...opportunity.disciplines, ...opportunity.keywords, ...opportunity.countries, ...opportunity.career_stages].map((chip) => (
              <span key={chip}>{chip}</span>
            ))}
          </div>
          <section className="detail-main-panels">
            <article>
              <h3>Why it matters</h3>
              {whyItMatters(opportunity, recommendation).length ? (
                <ul className="reasons">
                  {whyItMatters(opportunity, recommendation).map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Match reasons appear after personalized recommendations are available.</p>
              )}
            </article>
            <article>
              <h3>Reminders</h3>
              {reminders.length ? (
                <div className="detail-reminder-list">
                  {reminders.map((reminder) => (
                    <div className={`reminder-node detail-reminder-node ${reminder.status === "completed" ? "completed" : ""}`} key={reminder.id}>
                      <ReminderStatusIcon status={reminder.status} />
                      <div>
                        <div className="reminder-meta">
                          <span>{formatDate(reminder.remind_on)}</span>
                        </div>
                        <strong>{reminder.message || "Deadline reminder"}</strong>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No reminders yet.</p>
              )}
            </article>
          </section>
        </article>

        <aside className="detail-side">
          <article className="panel">
            <h3>Match</h3>
            {recommendation ? (
              <>
                <strong className="detail-score">{recommendation.match_score}%</strong>
                <FitCompass recommendation={recommendation} />
                <ScoreBreakdown item={recommendation} />
              </>
            ) : (
              <EmptyState title="No personalized score" detail="Create or select a profile to see semantic fit, eligibility, deadline, and history scoring." />
            )}
          </article>

          <article className="panel">
            <h3>Application plan</h3>
            {currentAssistant ? (
              <>
                <p>{currentAssistant.research_fit_statement}</p>
                <strong>{currentAssistant.readiness_score}% readiness</strong>
                <ul className="reasons">
                  {(currentAssistant.application_checklist.length ? currentAssistant.application_checklist : currentAssistant.gap_analysis).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : (
              <button
                className="primary"
                type="button"
                disabled={!canTrack || !status || status.status === "ignored"}
                onClick={() => onAssistantSelect(opportunity.id)}
              >
                {canTrack ? "Generate advisor memo" : "Sign in to use assistant"}
              </button>
            )}
          </article>

          <article className="panel">
            <h3>Status</h3>
            {canTrack ? (
              <StatusStagePicker value={currentStatus} onChange={(nextStatus) => onStatus(opportunity.id, nextStatus)} />
            ) : (
              <p className="muted">Create an account to save, ignore, and plan applications.</p>
            )}
          </article>
        </aside>
      </div>
    </section>
  );
}

function whyItMatters(opportunity: Opportunity, recommendation: Recommendation | null): string[] {
  const extracted = opportunity.extracted_requirements?.why_it_matters ?? [];
  if (extracted.length) return extracted;
  if (recommendation?.reasons.length) return recommendation.reasons;
  const fallback = [
    opportunity.deadline ? `${deadlineLabel(opportunity.deadline)}.` : "",
    opportunity.countries.length ? `Relevant region: ${opportunity.countries.slice(0, 3).join(", ")}.` : "",
    opportunity.keywords.length ? `Themes: ${opportunity.keywords.slice(0, 4).join(", ")}.` : "",
  ].filter(Boolean);
  return fallback;
}

function StatusStagePicker({ value, onChange }: { value: OpportunityStatus | null; onChange: (status: DisplayOpportunityStatus) => void }) {
  const selectedStatus: DisplayOpportunityStatus = value ?? "browsing";
  const statusOptions = displayStatuses;
  return (
    <div className="status-stage-picker">
      <header>
        <strong>{label(selectedStatus)}</strong>
        <span>{statusHelp(selectedStatus)}</span>
      </header>
      <div>
        {statusOptions.map((status, index) => (
          <button
            className={`${status === selectedStatus ? "active" : ""} status-${status}`}
            key={status}
            type="button"
            title={statusHelp(status)}
            onClick={() => onChange(status)}
          >
            <span>{index + 1}</span>
            <div>
              <strong>{label(status)}</strong>
              <small>{statusHelp(status)}</small>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function DetailList({ title, items, muted = false }: { title: string; items: string[]; muted?: boolean }) {
  const visibleItems = items.filter(Boolean).slice(0, 8);
  if (!visibleItems.length) return null;
  return (
    <div className={muted ? "detail-list detail-list-muted" : "detail-list"}>
      <h3>{title}</h3>
      <ul>
        {visibleItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function FitCompass({ recommendation }: { recommendation: Recommendation }) {
  const scores = [
    ["Topic", recommendation.score_breakdown.semantic],
    ["Eligibility", recommendation.score_breakdown.eligibility],
    ["Deadline", recommendation.score_breakdown.deadline],
    ["Readiness", recommendation.readiness_score],
    ["History", recommendation.score_breakdown.user_history],
  ] as const;
  const matchScale = Math.max(0, Math.min(100, recommendation.match_score)) / 100;
  const scaleRadius = matchScale * 38;
  const points = scores.map(([, score], index) => {
    const angle = -90 + (360 / scores.length) * index;
    const normalizedScore = Math.max(0, Math.min(100, score)) / 100;
    const radius = normalizedScore * 38;
    const radians = (angle * Math.PI) / 180;
    return `${50 + Math.cos(radians) * radius},${50 + Math.sin(radians) * radius}`;
  });
  return (
    <div className="fit-compass" aria-label="Fit compass">
      <svg viewBox="0 0 100 100" role="img">
        <circle className="compass-ring" cx="50" cy="50" r="38" />
        <circle className="compass-ring" cx="50" cy="50" r="25.33" />
        <circle className="compass-ring" cx="50" cy="50" r="12.66" />
        <circle className="compass-overall" cx="50" cy="50" r={scaleRadius} />
        {scores.map(([name, score], index) => {
          const angle = -90 + (360 / scores.length) * index;
          const radians = (angle * Math.PI) / 180;
          const labelRadius = 43;
          return (
            <g key={name}>
              <line x1="50" y1="50" x2={50 + Math.cos(radians) * 38} y2={50 + Math.sin(radians) * 38} />
              <text
                x={50 + Math.cos(radians) * labelRadius}
                y={50 + Math.sin(radians) * labelRadius}
                textAnchor={Math.cos(radians) > 0.25 ? "start" : Math.cos(radians) < -0.25 ? "end" : "middle"}
                dominantBaseline={Math.sin(radians) > 0.25 ? "hanging" : Math.sin(radians) < -0.25 ? "text-after-edge" : "middle"}
              >
                {name}
              </text>
              <title>{name}: {score}% before overall match scaling</title>
            </g>
          );
        })}
        <polygon points={points.join(" ")} />
        <circle className="compass-center" cx="50" cy="50" r="1.4" />
      </svg>
      <div>
        <span>
          <b>Overall scale</b>
          {recommendation.match_score}%
        </span>
        {scores.map(([name, score]) => (
          <span key={name}>
            <b>{name}</b>
            {score}%
          </span>
        ))}
      </div>
    </div>
  );
}

function ReminderStatusIcon({ status }: { status: Reminder["status"] }) {
  return (
    <div className={`reminder-icon reminder-icon-${status}`} title={label(status)} aria-label={label(status)}>
      {status === "completed" ? "✓" : "!"}
    </div>
  );
}

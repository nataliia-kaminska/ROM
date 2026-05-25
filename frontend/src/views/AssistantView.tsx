import { useState, type FormEvent } from "react";
import type { ApplicationAssistantResult, Opportunity } from "../types";
import { CustomSelect, EmptyState, HelpTip, PageHeader } from "../components/ui";
import { label, opportunitySummary } from "../utils/format";

export function AssistantView({
  assistantForm,
  assistantResult,
  assistantLoading,
  reminderEligibleOpportunities,
  onAssistantFormChange,
  onGenerate,
}: {
  assistantForm: { opportunity_id: string };
  assistantResult: ApplicationAssistantResult | null;
  assistantLoading: boolean;
  reminderEligibleOpportunities: Opportunity[];
  onAssistantFormChange: (form: { opportunity_id: string }) => void;
  onGenerate: (event: FormEvent) => void;
}) {
  const selectedOpportunity = reminderEligibleOpportunities.find((opportunity) => String(opportunity.id) === assistantForm.opportunity_id) ?? null;
  const generatedForSelected = Boolean(assistantForm.opportunity_id && assistantResult?.opportunity_id === Number(assistantForm.opportunity_id));
  const generateLabel = assistantLoading ? "Generating plan..." : generatedForSelected ? "Plan generated" : "Generate plan";
  return (
    <section className="assistant-page assistant-page-compact">
      <PageHeader
        title="Apply Assistant"
        description="Generate a grounded preparation memo for one saved or planned opportunity."
        hint="The assistant retrieves profile and opportunity evidence first, then turns it into application-specific planning notes."
        actions={<AssistantMiniFlow />}
      />

      <form className="panel assistant-picker assistant-picker-compact" onSubmit={onGenerate}>
        <div className="field">
          <span>Opportunity to prepare</span>
          <CustomSelect
            value={assistantForm.opportunity_id}
            ariaLabel="Opportunity to prepare"
            placeholder="Select a saved or planned opportunity"
            options={[
              { value: "", label: "Select a saved or planned opportunity" },
              ...reminderEligibleOpportunities.map((opportunity) => ({ value: String(opportunity.id), label: opportunity.title })),
            ]}
            onChange={(opportunity_id) => onAssistantFormChange({ opportunity_id })}
          />
        </div>
        <button className="primary assistant-generate-button" disabled={assistantLoading || !assistantForm.opportunity_id || generatedForSelected}>
          {assistantLoading && <span className="spinner" aria-hidden="true" />}
          {generateLabel}
        </button>
        {selectedOpportunity && (
          <div className="assistant-selected assistant-selected-compact">
            <span>{label(selectedOpportunity.opportunity_type)} - {selectedOpportunity.deadline ?? "No deadline"}</span>
            <strong>{selectedOpportunity.title}</strong>
            <p>{opportunitySummary(selectedOpportunity)}</p>
          </div>
        )}
      </form>

      {reminderEligibleOpportunities.length === 0 && (
        <EmptyState title="No saved or planned opportunities" detail="Save or plan an opportunity from the feed before using the assistant." />
      )}
      {assistantResult && <AssistantWorkspace result={assistantResult} opportunity={selectedOpportunity} />}
    </section>
  );
}

function AssistantWorkspace({ result, opportunity }: { result: ApplicationAssistantResult; opportunity: Opportunity | null }) {
  const [showAllActions, setShowAllActions] = useState(false);
  const primaryActions = result.application_checklist.slice(0, 4);
  const hiddenActions = result.application_checklist.slice(4);
  const visibleActions = showAllActions ? result.application_checklist : primaryActions;

  return (
    <div className="assistant-workspace assistant-workspace-compact">
      <section className="panel assistant-summary assistant-summary-compact">
        <ReadinessRing score={result.readiness_score} />
        <div>
          <p className="eyebrow">Application signal</p>
          <h3>{readinessLabel(result.readiness_score)}</h3>
          <p>{result.research_fit_statement}</p>
          <ReadinessExplainer result={result} />
        </div>
      </section>

      {opportunity && <OpportunityInsightGrid result={result} opportunity={opportunity} />}

      <section className="assistant-focus-grid assistant-focus-single assistant-full-width">
        <article className="panel assistant-priority">
          <SectionHead title="Next actions" detail="Do these concrete tasks after checking the insight cards above." />
          <ol className="assistant-timeline assistant-timeline-compact">
            {visibleActions.map((item, index) => (
              <li key={item}>
                <span>{index + 1}</span>
                <p>{item}</p>
              </li>
            ))}
          </ol>
          {hiddenActions.length > 0 && (
            <button className="assistant-expand-button" type="button" onClick={() => setShowAllActions((current) => !current)}>
              {showAllActions ? "Show fewer steps" : `Show ${hiddenActions.length} more steps`}
            </button>
          )}
        </article>

      </section>

      <section className="assistant-collapsible-stack">
        <details className="panel assistant-collapse-card" open>
          <summary>
            <span>Advisor memo</span>
            <small>
              {result.advisor_provider}
              <HelpTip text={`A strategic memo grounded in ${result.retrieved_context.length} profile and opportunity snippets. It is meant to shape positioning, reviewer objections, and draft wording, not repeat the checklist.`} />
            </small>
          </summary>
          <MemoText result={result} />
        </details>
        {result.web_research.length > 0 && (
          <details className="panel assistant-collapse-card" open>
            <summary>
          <span>Web research links</span>
              <small>
                Links to explore this program
                <HelpTip text="When enabled, the assistant searches DuckDuckGo using the opportunity title, source, official domain, keywords, disciplines, eligibility, and deadline terms. Results are cached during the server process and used as supporting context, not as verified eligibility rules." />
              </small>
            </summary>
            <p className="assistant-source-note">
              Search results that can help you verify official pages, program context, and wording outside the imported record.
            </p>
            <WebResearchList items={result.web_research} />
          </details>
        )}
      </section>
    </div>
  );
}

function OpportunityInsightGrid({ result, opportunity }: { result: ApplicationAssistantResult; opportunity: Opportunity }) {
  const requirements = opportunity.extracted_requirements;
  const cards = [
    {
      title: "Call focus",
      body: opportunity.keywords.concat(opportunity.disciplines).slice(0, 5).join(", ") || opportunitySummary(opportunity),
      detail: `${label(opportunity.opportunity_type)} from ${opportunity.source}`,
    },
    {
      title: "Eligibility to verify",
      body: firstUseful([
        requirements?.required_degree,
        requirements?.citizenship,
        requirements?.mobility,
        opportunity.eligibility,
        result.eligibility_warnings[0],
      ]),
      detail: "Use this as the first manual check.",
    },
    {
      title: "Evidence to use",
      body: evidenceToUse(result),
      detail: "Profile proof to reuse in a CV, statement, or cover note.",
    },
    {
      title: "Decision pressure",
      body: deadlineText(opportunity),
      detail: result.gap_analysis[0] || "No major preparation gap was detected.",
    },
  ];
  return (
    <section className="assistant-insight-grid">
      {cards.map((card) => (
        <article className="panel assistant-insight-card" key={card.title}>
          <span>{card.title}</span>
          <strong>{card.body}</strong>
          <p>{card.detail}</p>
        </article>
      ))}
    </section>
  );
}

function evidenceToUse(result: ApplicationAssistantResult): string {
  const evidence = firstUseful([
        result.strengths.find((item) => item.toLowerCase().includes("publication")),
        result.retrieved_context.find((item) => item.startsWith("Publication evidence")),
        result.research_fit_statement,
  ]).replace(/^[^:]+:\s*/, "").trim();
  const sentence = evidence.split(/(?<=[.!?])\s+/)[0]?.trim();
  return sentence || "Use your strongest profile evidence in the application narrative.";
}

function WebResearchList({ items }: { items: string[] }) {
  return (
    <div className="web-research-list">
      {items.map((item) => {
        const parsed = parseWebResearch(item);
        return (
          <article key={item}>
            <strong>{parsed.title}</strong>
            {parsed.body && <p>{parsed.body}</p>}
            {parsed.source && (
              <a href={parsed.source} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>
                Open source
              </a>
            )}
          </article>
        );
      })}
    </div>
  );
}

function parseWebResearch(item: string) {
  const withoutPrefix = item.replace(/^Web research:\s*/i, "");
  const [main, source = ""] = withoutPrefix.split(" Source: ");
  const [title = main, ...bodyParts] = main.split(". ");
  return {
    title: title.trim() || "External source",
    body: bodyParts.join(". ").trim(),
    source: source.trim(),
  };
}

function firstUseful(values: Array<string | undefined | null>): string {
  return values.find((value) => value && value.trim())?.trim() ?? "No specific signal extracted yet.";
}

function compactText(value: string, limit: number): string {
  const text = cleanMemoText(value).replace(/^[^:]+:\s*/, "").trim();
  return text.length <= limit ? text : `${text.slice(0, limit).trim()}...`;
}

function deadlineText(opportunity: Opportunity): string {
  if (!opportunity.deadline) return "No deadline is listed. Confirm timing on the official page.";
  const today = new Date();
  const deadline = new Date(`${opportunity.deadline}T00:00:00`);
  const days = Math.ceil((deadline.getTime() - new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()) / 86400000);
  if (days < 0) return `Deadline passed on ${opportunity.deadline}.`;
  if (days <= 14) return `${days} days left. Decide quickly before drafting.`;
  if (days <= 45) return `${days} days left. Start evidence collection now.`;
  return `${days} days left. Good window for preparation.`;
}

function AssistantMiniFlow() {
  return (
    <div className="assistant-flow" aria-label="Assistant flow">
      <span>Retrieve</span>
      <i />
      <span>Assess</span>
      <i />
      <span>Plan</span>
    </div>
  );
}

function ReadinessRing({ score }: { score: number }) {
  const normalizedScore = Math.max(0, Math.min(100, score));
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (normalizedScore / 100) * circumference;
  return (
    <div className="readiness-ring" aria-label={`Application readiness ${normalizedScore}%`}>
      <svg viewBox="0 0 112 112" role="img">
        <circle cx="56" cy="56" r={radius} />
        <circle cx="56" cy="56" r={radius} style={{ strokeDasharray: circumference, strokeDashoffset: offset }} />
      </svg>
      <div>
        <strong>{normalizedScore}%</strong>
        <span>readiness</span>
      </div>
    </div>
  );
}

function ReadinessExplainer({ result }: { result: ApplicationAssistantResult }) {
  const [activeSignal, setActiveSignal] = useState<"strengths" | "gaps" | "fields" | "warnings">("gaps");
  const signals = {
    strengths: {
      label: `${result.strengths.length} strengths`,
      detail: "Signals that make this application look more plausible.",
      items: result.strengths,
    },
    gaps: {
      label: `${result.gap_analysis.length} preparation gaps`,
      detail: "Things to prepare before the application is convincing.",
      items: result.gap_analysis,
    },
    fields: {
      label: `${result.missing_profile_fields.length} missing profile fields`,
      detail: "Profile data that would improve readiness scoring and advisor notes.",
      items: result.missing_profile_fields.map((item) => `Add ${item} to your profile.`),
    },
    warnings: {
      label: `${result.eligibility_warnings.length} eligibility warnings`,
      detail: "Potential requirement conflicts or call rules to verify manually.",
      items: result.eligibility_warnings,
    },
  };
  const active = signals[activeSignal];
  return (
    <div className="readiness-explainer">
      <strong>What affects this score?</strong>
      <p>
        Readiness combines your profile evidence with parsed opportunity requirements: eligibility, publications, languages, missing fields,
        and warnings from the call text.
      </p>
      <div>
        {(Object.keys(signals) as Array<keyof typeof signals>).map((key) => (
          <button className={activeSignal === key ? "active" : ""} key={key} type="button" onClick={() => setActiveSignal(key)}>
            {signals[key].label}
          </button>
        ))}
      </div>
      <section className="readiness-detail">
        <span>{active.detail}</span>
        {active.items.length ? (
          <ul>
            {active.items.slice(0, 4).map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <p>No items in this category yet.</p>
        )}
      </section>
    </div>
  );
}

function SectionHead({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="assistant-section-head">
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}

function MemoText({ result }: { result: ApplicationAssistantResult }) {
  const blocks = parseMemoSections(result.advisor_memo);
  const [leadBlock, ...secondaryBlocks] = blocks;
  const strategyLine = findMainStrategy(blocks) ?? result.research_fit_statement;
  return (
    <div className="memo-body memo-brief">
      <header className="memo-brief-header">
        <div>
          <h3>Advisor memo</h3>
          <p>{result.profile_name || "Researcher"} &rarr; {result.opportunity_title || "Selected opportunity"}</p>
        </div>
        <div>
          <span>Overall fit: {memoFitLabel(result.readiness_score)}</span>
          <strong>Main strategy: {compactText(stripListMarker(strategyLine), 150)}</strong>
        </div>
      </header>
      <aside className="memo-brief-index" aria-label="Advisor memo sections">
        {blocks.map((block, index) => (
          <a href={`#memo-section-${slugify(block.heading)}`} key={block.heading}>
            <i>{index + 1}</i>
            {block.heading}
          </a>
        ))}
      </aside>
      <div className="memo-brief-content">
      {leadBlock && <MemoSection block={leadBlock} />}
        {secondaryBlocks.map((block) => (
          <MemoSection block={block} key={`${block.heading}-${block.lines.join("|")}`} />
        ))}
      </div>
    </div>
  );
}

function MemoSection({ block, variant = "standard" }: { block: { heading: string; lines: string[] }; variant?: "lead" | "standard" }) {
  const headingClass = slugify(block.heading);
  return (
    <section className={`memo-section memo-section-${headingClass} ${variant === "lead" ? "memo-section-lead" : ""}`} id={`memo-section-${headingClass}`}>
      <h4>{block.heading}</h4>
      {headingClass === "draft-snippets" ? (
        <div className="memo-snippets">
          {block.lines.map((line) => (
            <div className="memo-copy-block" key={line}>
              <span>{parseSnippet(line).label}</span>
              <blockquote>{parseSnippet(line).text}</blockquote>
              <button className="secondary memo-copy-button" type="button" onClick={() => void navigator.clipboard?.writeText(parseSnippet(line).text)}>Copy</button>
            </div>
          ))}
        </div>
      ) : block.lines.length > 1 || block.lines.some((line) => isListLine(line)) ? (
        <ul>
          {block.lines.map((line) => (
            <li key={line}>{stripListMarker(line)}</li>
          ))}
        </ul>
      ) : (
        <p>{stripListMarker(block.lines[0])}</p>
      )}
    </section>
  );
}

function parseSnippet(value: string): { label: string; text: string } {
  const clean = stripListMarker(value);
  const match = clean.match(/^([^:]{2,40}):\s*(.+)$/);
  if (!match) return { label: "Snippet", text: clean };
  return { label: match[1], text: match[2] };
}

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function parseMemoSections(text: string): Array<{ heading: string; lines: string[] }> {
  const knownHeadings = new Set([
    "decision summary",
    "decision snapshot",
    "official-source checks",
    "official source checks",
    "application angle",
    "application strategy",
    "before drafting",
    "risks to clear",
    "recommended next actions",
    "next move",
    "source leads",
    "best angle",
    "reviewer concerns",
    "how to answer",
    "draft snippets",
    "do not overclaim",
  ]);
  const sections: Array<{ heading: string; lines: string[] }> = [];
  let current: { heading: string; lines: string[] } = { heading: "Advisor note", lines: [] };

  function pushCurrent() {
    const lines = current.lines.map(stripEmptyMarkup).filter((line) => line && !isMemoTitleLine(line));
    if (lines.length) sections.push({ heading: current.heading, lines });
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const line = stripEmptyMarkup(rawLine);
    if (!line) continue;
    const normalizedHeading = normalizeHeading(line);
    if (normalizedHeading && (knownHeadings.has(normalizedHeading.toLowerCase()) || line.endsWith(":") || rawLine.trim().startsWith("#"))) {
      pushCurrent();
      current = { heading: normalizedHeading, lines: [] };
      continue;
    }
    current.lines.push(line);
  }
  pushCurrent();
  return sections.length ? sections : [{ heading: "Advisor note", lines: ["No advisor memo content was generated for this opportunity."] }];
}

function findMainStrategy(blocks: Array<{ heading: string; lines: string[] }>): string | null {
  const bestAngle = blocks.find((block) => block.heading.toLowerCase() === "best angle");
  const line = bestAngle?.lines.find((item) => !isMemoTitleLine(stripListMarker(item)));
  return line ? stripListMarker(line) : null;
}

function normalizeHeading(value: string): string {
  return cleanMemoText(value)
    .replace(/^#+\s*/, "")
    .replace(/:$/, "")
    .trim();
}

function stripEmptyMarkup(value: string): string {
  return cleanMemoText(value);
}

function isMemoTitleLine(value: string): boolean {
  return /^advisor memo(\s+for\b.*)?$/i.test(stripListMarker(value).replace(/:$/, "").trim());
}

function isListLine(value: string): boolean {
  return /^[•\-*]\s+/.test(value) || /^\d+[.)]\s+/.test(value);
}

function stripListMarker(value: string): string {
  return cleanMemoText(value).replace(/^[•\-*]\s+/, "").replace(/^\d+[.)]\s+/, "").trim();
}

function cleanMemoText(value: string): string {
  return value.replace(/\*\*/g, "").trim();
}

function readinessLabel(score: number) {
  if (score >= 80) return "Strong application candidate";
  if (score >= 60) return "Promising with a few checks";
  if (score >= 40) return "Needs profile evidence";
  return "High preparation needed";
}

function memoFitLabel(score: number) {
  if (score >= 80) return "Strong match";
  if (score >= 60) return "Promising match";
  if (score >= 40) return "Partial match";
  return "Needs preparation";
}

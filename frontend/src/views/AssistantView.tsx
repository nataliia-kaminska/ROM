import type { FormEvent } from "react";
import type { ApplicationAssistantResult, Opportunity } from "../types";
import { EmptyState, HelpTip } from "../components/ui";

export function AssistantView({
  assistantForm,
  assistantResult,
  reminderEligibleOpportunities,
  onAssistantFormChange,
  onGenerate,
}: {
  assistantForm: { opportunity_id: string };
  assistantResult: ApplicationAssistantResult | null;
  reminderEligibleOpportunities: Opportunity[];
  onAssistantFormChange: (form: { opportunity_id: string }) => void;
  onGenerate: (event: FormEvent) => void;
}) {
  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <div className="title-with-help">
            <h2>Apply Assistant</h2>
            <HelpTip text="Save or plan an opportunity first, then generate structured notes for that specific application." />
          </div>
          <p>Generate a checklist, motivation outline, fit statement, eligibility warnings, and exportable notes.</p>
        </div>
      </div>
      <form className="grid-form" onSubmit={onGenerate}>
        <label className="field span-2">
          <span>Opportunity</span>
          <select value={assistantForm.opportunity_id} onChange={(event) => onAssistantFormChange({ opportunity_id: event.target.value })}>
            <option value="">Select a saved or planned opportunity</option>
            {reminderEligibleOpportunities.map((opportunity) => (
              <option value={opportunity.id} key={opportunity.id}>
                {opportunity.title}
              </option>
            ))}
          </select>
        </label>
        <button className="primary span-2">Generate notes</button>
      </form>
      {reminderEligibleOpportunities.length === 0 && (
        <EmptyState title="No saved or planned opportunities" detail="Save or plan an opportunity from the feed before using the assistant." />
      )}
      {assistantResult && (
        <div className="assistant-grid separated">
          <section className="span-2 advisor-memo">
            <div className="card-head">
              <h3>Advisor Memo</h3>
              <span>{assistantResult.advisor_provider}</span>
            </div>
            <p>{assistantResult.advisor_memo}</p>
          </section>
          <section className="span-2">
            <h3>Retrieved Context</h3>
            <ul className="reasons">{assistantResult.retrieved_context.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section className="span-2">
            <h3>Readiness</h3>
            <div className="completeness">
              <div>
                <span>Application readiness</span>
                <strong>{assistantResult.readiness_score}%</strong>
              </div>
              <div className="progress"><i style={{ width: `${assistantResult.readiness_score}%` }} /></div>
            </div>
          </section>
          <section>
            <h3>Checklist</h3>
            <ul>{assistantResult.application_checklist.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section>
            <h3>Motivation Outline</h3>
            <ul>{assistantResult.motivation_letter_outline.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section className="span-2">
            <h3>Research Fit</h3>
            <p>{assistantResult.research_fit_statement}</p>
          </section>
          <section>
            <h3>Missing Fields</h3>
            <ul>{assistantResult.missing_profile_fields.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section>
            <h3>Eligibility Warnings</h3>
            <ul>{assistantResult.eligibility_warnings.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section>
            <h3>Strengths</h3>
            <ul>{(assistantResult.strengths.length ? assistantResult.strengths : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section>
            <h3>Gap Analysis</h3>
            <ul>{(assistantResult.gap_analysis.length ? assistantResult.gap_analysis : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <section className="span-2">
            <h3>Export Notes</h3>
            <pre className="job-detail">{assistantResult.exported_notes}</pre>
          </section>
        </div>
      )}
    </section>
  );
}

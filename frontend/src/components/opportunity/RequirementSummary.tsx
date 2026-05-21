import type { Opportunity } from "../../types";
import { HelpTip } from "../ui";

export function RequirementSummary({ opportunity }: { opportunity: Opportunity }) {
  const requirements = opportunity.extracted_requirements;
  if (!requirements || (requirements.confidence ?? 0) === 0) {
    return null;
  }
  const rows = [
    ["Career stages", requirements.career_stages.join(", ")],
    ["Countries", requirements.countries.join(", ")],
    ["Degree", requirements.required_degree],
    ["Languages", requirements.languages.join(", ")],
    ["Years since PhD", requirements.years_since_phd ? String(requirements.years_since_phd) : ""],
  ].filter(([, value]) => value);
  return (
    <div className="requirement-summary">
      <strong>
        Eligibility signals
        <HelpTip text={`Automatically extracted from the opportunity text. Extraction confidence: ${requirements.confidence}%.`} />
      </strong>
      <div className="score-grid">
        {rows.map(([name, value]) => (
          <span key={name}>{name}: {value}</span>
        ))}
      </div>
      {requirements.publication_expectation && <p className="muted">Publication signal: {requirements.publication_expectation}</p>}
      {requirements.mobility && <p className="muted">Mobility signal: {requirements.mobility}</p>}
      {requirements.citizenship && <p className="muted">Citizenship signal: {requirements.citizenship}</p>}
    </div>
  );
}

import type { Opportunity, OpportunityStatus, OpportunityType, Recommendation } from "../types";
import { opportunityTypes } from "../constants";
import { OpportunityCard } from "../components/opportunities";
import { ActionButton, EmptyState, Field, SelectField, SkeletonCards } from "../components/ui";

type FeedFilters = {
  keyword: string;
  opportunity_type: string;
  country: string;
  career_stage: string;
  source: string;
  active_only: boolean;
  min_score: number;
  include_ignored: boolean;
};

export function FeedView({
  filters,
  sourceOptions,
  countryOptions,
  keywordOptions,
  workspaceLoading,
  activeProfile,
  recommendations,
  opportunities,
  onFiltersChange,
  onApplyFilters,
  onResetFilters,
  onSelectOpportunity,
  onStatus,
}: {
  filters: FeedFilters;
  sourceOptions: string[];
  countryOptions: string[];
  keywordOptions: string[];
  workspaceLoading: boolean;
  activeProfile: boolean;
  recommendations: Recommendation[];
  opportunities: Opportunity[];
  onFiltersChange: (filters: FeedFilters) => void;
  onApplyFilters: () => void;
  onResetFilters: () => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
}) {
  const catalogRecommendations = opportunities.map((opportunity) => ({
    opportunity,
    match_score: 0,
    semantic_score: 0,
    score_breakdown: { semantic: 0, eligibility: 0, deadline: 0, user_history: 0, final: 0 },
    reasons: [],
    readiness_score: 0,
    gaps: [],
    strengths: [],
    user_status: null,
  }));
  const items = activeProfile ? recommendations : catalogRecommendations;

  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <h2>Matches</h2>
          <p>Recommended opportunities appear first. Use Save, Plan, or Ignore to make future results smarter.</p>
        </div>
      </div>
      <div className="filters">
        <Field labelText="Keyword" value={filters.keyword} list="keyword-options" placeholder="AI, biology, mobility..." onChange={(keyword) => onFiltersChange({ ...filters, keyword })} />
        <SelectField
          labelText="Type"
          value={(filters.opportunity_type || "") as OpportunityType | ""}
          options={["", ...opportunityTypes] as (OpportunityType | "")[]}
          onChange={(opportunity_type) => onFiltersChange({ ...filters, opportunity_type })}
        />
        <Field labelText="Country" value={filters.country} list="country-options" placeholder="Germany, EU, USA..." onChange={(country) => onFiltersChange({ ...filters, country })} />
        <Field labelText="Source" value={filters.source} list="source-options" placeholder="euraxess, daad, grants.gov..." onChange={(source) => onFiltersChange({ ...filters, source })} />
        <label className="toggle">
          <input
            type="checkbox"
            checked={filters.active_only}
            onChange={(event) => onFiltersChange({ ...filters, active_only: event.target.checked })}
          />
          Active only
        </label>
        <ActionButton variant="secondary" type="button" busy={workspaceLoading} onClick={onApplyFilters}>
          Apply filters
        </ActionButton>
        <button className="secondary" type="button" onClick={onResetFilters}>
          Clear filters
        </button>
      </div>
      <datalist id="source-options">{sourceOptions.map((item) => <option value={item} key={item} />)}</datalist>
      <datalist id="country-options">{countryOptions.map((item) => <option value={item} key={item} />)}</datalist>
      <datalist id="keyword-options">{keywordOptions.map((item) => <option value={item} key={item} />)}</datalist>
      <div className="cards">
        {workspaceLoading ? <SkeletonCards /> : items.map(
          (item) => (
            <OpportunityCard
              key={item.opportunity.id}
              item={item}
              canTrack={activeProfile}
              onSelect={() => onSelectOpportunity(item.opportunity)}
              onStatus={(status) => onStatus(item.opportunity.id, status)}
            />
          ),
        )}
        {activeProfile && !workspaceLoading && recommendations.length === 0 && (
          <EmptyState title="No matches found" detail="Try clearing filters, lowering the score threshold, or searching broader terms like fellowship, mobility, AI, health, or Europe." />
        )}
        {!activeProfile && !workspaceLoading && opportunities.length === 0 && (
          <EmptyState title="No opportunities found" detail="Try clearing filters or searching broader terms like fellowship, mobility, AI, health, or Europe." />
        )}
      </div>
    </section>
  );
}

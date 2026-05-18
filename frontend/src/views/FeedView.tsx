import type { Opportunity, OpportunityStatus, Recommendation } from "../types";
import { careerStages, opportunityTypes, type View } from "../constants";
import { OpportunityCard } from "../components/opportunities";
import { EmptyState, HelpTip, MultiValueField, SkeletonCards } from "../components/ui";
import { label, splitList } from "../utils/format";

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
  isSignedIn,
  activeProfile,
  recommendations,
  opportunities,
  page,
  hasNextPage,
  onFiltersChange,
  onResetFilters,
  onPageChange,
  onViewChange,
  onSelectOpportunity,
  onStatus,
}: {
  filters: FeedFilters;
  sourceOptions: string[];
  countryOptions: string[];
  keywordOptions: string[];
  workspaceLoading: boolean;
  isSignedIn: boolean;
  activeProfile: boolean;
  recommendations: Recommendation[];
  opportunities: Opportunity[];
  page: number;
  hasNextPage: boolean;
  onFiltersChange: (filters: FeedFilters) => void;
  onResetFilters: () => void;
  onPageChange: (page: number) => void;
  onViewChange: (view: View) => void;
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
  const showingPersonalized = activeProfile && recommendations.length > 0;
  const items = (showingPersonalized ? recommendations : catalogRecommendations).filter((item) =>
    recommendationMatchesFilters(item, filters),
  );

  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <div className="title-with-help">
            <h2>Matches</h2>
            <HelpTip text="Keyword search uses Elasticsearch when it is enabled. Elasticsearch ranks full-text matches across title, summary, eligibility, keywords, and disciplines; profile recommendations still use embedding similarity plus eligibility, deadline, and history scoring." />
          </div>
          {showingPersonalized ? (
            <p>Recommended opportunities appear first. Save, Plan, or Ignore to make future results smarter.</p>
          ) : activeProfile ? (
            <p className="muted">Showing the opportunity catalog while personalized matching warms up. Save or plan useful items to teach the system.</p>
          ) : (
            <p className="muted">You are viewing the public catalog. Create an account and profile to unlock personalized match scores and planning tools.</p>
          )}
        </div>
        <button className="secondary" type="button" onClick={() => onViewChange("about")}>
          How it works
        </button>
      </div>
      <div className="filters">
        <MultiValueField
          className="filter-field filter-field-wide"
          labelText="Keywords"
          values={splitList(filters.keyword)}
          suggestions={keywordOptions}
          placeholder="AI, biology, mobility..."
          onChange={(keyword) => onFiltersChange({ ...filters, keyword: keyword.join(", ") })}
        />
        <MultiValueField
          className="filter-field"
          labelText="Type"
          values={splitList(filters.opportunity_type)}
          suggestions={opportunityTypes.map(label)}
          placeholder="Grant, fellowship..."
          onChange={(types) => onFiltersChange({ ...filters, opportunity_type: types.join(", ") })}
        />
        <MultiValueField
          className="filter-field"
          labelText="Countries"
          values={splitList(filters.country)}
          suggestions={countryOptions}
          placeholder="Germany, EU, USA..."
          onChange={(country) => onFiltersChange({ ...filters, country: country.join(", ") })}
        />
        <MultiValueField
          className="filter-field"
          labelText="Career stages"
          values={splitList(filters.career_stage)}
          suggestions={careerStages.map(label)}
          placeholder="PhD, postdoc..."
          onChange={(career_stage) => onFiltersChange({ ...filters, career_stage: career_stage.join(", ") })}
        />
        <MultiValueField
          className="filter-field"
          labelText="Sources"
          values={splitList(filters.source)}
          suggestions={sourceOptions}
          placeholder="euraxess, daad..."
          onChange={(source) => onFiltersChange({ ...filters, source: source.join(", ") })}
        />
        <div className="filter-actions">
          <label className="toggle filter-toggle">
            <input
              type="checkbox"
              checked={filters.active_only}
              onChange={(event) => onFiltersChange({ ...filters, active_only: event.target.checked })}
            />
            <span>Active only</span>
          </label>
          <button className="tertiary" type="button" onClick={onResetFilters}>
            Clear filters
          </button>
        </div>
      </div>
      <div className="pagination-bar">
        <span>Page {page}</span>
        <div className="actions">
          <button className="secondary" type="button" disabled={workspaceLoading || page === 1} onClick={() => onPageChange(page - 1)}>
            Previous
          </button>
          <button className="secondary" type="button" disabled={workspaceLoading || !hasNextPage} onClick={() => onPageChange(page + 1)}>
            Next
          </button>
        </div>
      </div>
      <div className="cards">
        {workspaceLoading ? <SkeletonCards /> : items.map(
          (item) => (
            <OpportunityCard
              key={item.opportunity.id}
              item={item}
              canTrack={activeProfile}
              actionNote={isSignedIn ? "Create a profile to save or plan" : "Sign in to save or plan"}
              onSelect={() => onSelectOpportunity(item.opportunity)}
              onStatus={(status) => onStatus(item.opportunity.id, status)}
            />
          ),
        )}
        {!workspaceLoading && items.length === 0 && (
          <EmptyState title="No opportunities found" detail="Try clearing filters or searching broader terms like fellowship, mobility, AI, health, or Europe." />
        )}
      </div>
    </section>
  );
}

function recommendationMatchesFilters(item: Recommendation, filters: FeedFilters): boolean {
  const opportunity = item.opportunity;
  const keywords = normalizeTerms(filters.keyword);
  const types = normalizeTerms(filters.opportunity_type).map((value) => value.replaceAll(" ", "_"));
  const countries = normalizeTerms(filters.country);
  const selectedStages = normalizeTerms(filters.career_stage).map((value) => value.replaceAll(" ", "_"));
  const sources = normalizeTerms(filters.source);
  const now = new Date();
  const deadline = opportunity.deadline ? new Date(`${opportunity.deadline}T00:00:00`) : null;

  if (filters.active_only && deadline && deadline < new Date(now.getFullYear(), now.getMonth(), now.getDate())) return false;
  if (types.length > 0 && !types.includes(opportunity.opportunity_type)) return false;
  if (sources.length > 0 && !sources.includes(opportunity.source.toLowerCase())) return false;
  if (countries.length > 0 && !opportunity.countries.some((country) => countries.includes(country.toLowerCase()))) return false;
  if (selectedStages.length > 0 && !opportunity.career_stages.some((stage) => selectedStages.includes(stage.toLowerCase()))) return false;
  if (keywords.length === 0) return true;

  const searchable = [
    opportunity.title,
    opportunity.summary,
    opportunity.eligibility,
    opportunity.source,
    ...opportunity.keywords,
    ...opportunity.disciplines,
    ...opportunity.countries,
  ].join(" ").toLowerCase();
  return keywords.some((keyword) => searchable.includes(keyword));
}

function normalizeTerms(value: string): string[] {
  return splitList(value).map((item) => item.toLowerCase());
}

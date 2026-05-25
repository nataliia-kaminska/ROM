import { useState } from "react";
import type { Opportunity, OpportunityStatus, Recommendation } from "../types";
import { careerStages, opportunityTypes, type View } from "../constants";
import { OpportunityCard } from "../components/opportunities";
import { CustomSelect, EmptyState, MultiValueField, PageHeader, SkeletonCards } from "../components/ui";
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
  status_filter: string;
  sort_by: string;
  sort_order: string;
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
  totalPages,
  totalIsEstimate,
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
  totalPages: number;
  totalIsEstimate: boolean;
  onFiltersChange: (filters: FeedFilters) => void;
  onResetFilters: () => void;
  onPageChange: (page: number) => void;
  onViewChange: (view: View) => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
}) {
  const [filtersOpen, setFiltersOpen] = useState(false);
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
  const selectedSortBy = activeProfile ? filters.sort_by : catalogSortBy(filters.sort_by);
  const activeFilterCount = countActiveFilters(filters);
  const items = (showingPersonalized ? recommendations : catalogRecommendations).filter((item) =>
    recommendationMatchesFilters(item, filters),
  );

  return (
    <section className="feed-page">
      <PageHeader
        title="Matches"
        description="Browse research opportunities, compare fit, and move promising items into your application workflow."
        hint="Keyword search uses Elasticsearch when it is enabled. Elasticsearch ranks full-text matches across title, summary, eligibility, keywords, and disciplines; profile recommendations still use embedding similarity plus eligibility, deadline, and history scoring."
        actions={
        <button className="secondary" type="button" onClick={() => onViewChange("about")}>
          How it works
        </button>
        }
      />
      <div className="panel">
      <div className="match-toolbar-row">
        <MultiValueField
          className="filter-field match-keywords"
          labelText="Keywords"
          values={splitList(filters.keyword)}
          suggestions={keywordOptions}
          suggestionsOnFocusOnly
          placeholder="AI, biology, mobility..."
          onChange={(keyword) => onFiltersChange({ ...filters, keyword: keyword.join(", ") })}
        />
        <div className="match-secondary-controls">
          <label className="field sort-combo">
            <span>Sort</span>
            <div>
              <CustomSelect
                value={selectedSortBy}
                ariaLabel="Sort matches"
                options={[
                  ...(activeProfile ? [
                    { value: "match_score", label: "Match score" },
                    { value: "semantic_score", label: "Semantic fit" },
                    { value: "readiness_score", label: "Readiness" },
                  ] : []),
                  { value: "deadline", label: "Deadline" },
                  { value: "created_at", label: "Newest added" },
                  { value: "source", label: "Source" },
                  { value: "title", label: "Title" },
                ]}
                onChange={(sort_by) => onFiltersChange({ ...filters, sort_by })}
              />
              <button
                className="secondary sort-direction"
                type="button"
                title={sortOrderLabel(selectedSortBy, filters.sort_order === "desc" ? "asc" : "desc")}
                aria-label={`Sort ${filters.sort_order === "desc" ? "descending" : "ascending"}`}
                onClick={() => onFiltersChange({ ...filters, sort_order: filters.sort_order === "desc" ? "asc" : "desc" })}
              >
                {filters.sort_order === "desc" ? "↓" : "↑"}
              </button>
            </div>
          </label>
          <button className={`secondary filters-toggle ${activeFilterCount > 0 ? "active" : ""}`} type="button" onClick={() => setFiltersOpen((current) => !current)}>
            Filters active: {activeFilterCount}
          </button>
        </div>
      </div>
      {filtersOpen && (
        <div className="filters collapsible-filters">
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
          <div className="filter-actions-row">
            {activeProfile && (
              <MultiValueField
                className="filter-field status-filter-field"
                labelText="Status"
                values={statusLabelsFromFilter(filters.status_filter)}
                suggestions={["All", "Not in my board", "Saved", "Planned", "Applied", "Accepted", "Rejected", "Ignored"]}
                placeholder="Choose statuses..."
                onChange={(statusLabels) => onFiltersChange(statusFilterChange(filters, statusLabels))}
              />
            )}
            <label className="toggle filter-toggle">
              <input
                type="checkbox"
                checked={filters.active_only}
                onChange={(event) => onFiltersChange({ ...filters, active_only: event.target.checked })}
              />
              <span>Active only</span>
            </label>
            <button className="primary" type="button" onClick={() => setFiltersOpen(false)}>
              Apply
            </button>
            <button
              className="tertiary"
              type="button"
              onClick={() => {
                onResetFilters();
                setFiltersOpen(false);
              }}
            >
              Clear filters
            </button>
          </div>
        </div>
      )}
      <PaginationBar page={page} totalPages={totalPages} totalIsEstimate={totalIsEstimate} hasNextPage={hasNextPage} loading={workspaceLoading} onPageChange={onPageChange} />
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
      <PaginationBar page={page} totalPages={totalPages} totalIsEstimate={totalIsEstimate} hasNextPage={hasNextPage} loading={workspaceLoading} onPageChange={onPageChange} position="bottom" />
      </div>
    </section>
  );
}

function PaginationBar({
  page,
  totalPages,
  totalIsEstimate,
  hasNextPage,
  loading,
  onPageChange,
  position = "top",
}: {
  page: number;
  totalPages: number;
  totalIsEstimate: boolean;
  hasNextPage: boolean;
  loading: boolean;
  onPageChange: (page: number) => void;
  position?: "top" | "bottom";
}) {
  return (
    <div className={`pagination-bar pagination-${position}`}>
      <span>Page {page} of {totalPages}{totalIsEstimate ? "+" : ""}</span>
      <div className="actions">
        <button className="secondary" type="button" disabled={loading || page === 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </button>
        <button className="secondary" type="button" disabled={loading || !hasNextPage} onClick={() => onPageChange(page + 1)}>
          Next
        </button>
      </div>
    </div>
  );
}

function sortOrderLabel(sortBy: string, order: string): string {
  if (sortBy === "deadline") return order === "asc" ? "Soonest first" : "Latest first";
  if (sortBy === "created_at") return order === "desc" ? "Newest first" : "Oldest first";
  if (sortBy === "title" || sortBy === "source") return order === "asc" ? "A to Z" : "Z to A";
  return order === "desc" ? "Highest first" : "Lowest first";
}

function catalogSortBy(sortBy: string): string {
  return ["deadline", "created_at", "source", "title"].includes(sortBy) ? sortBy : "deadline";
}

function countActiveFilters(filters: FeedFilters): number {
  return [
    filters.opportunity_type,
    filters.country,
    filters.career_stage,
    filters.source,
    filters.status_filter === "visible" ? "" : filters.status_filter,
    filters.active_only ? "" : "inactive",
  ].filter((value) => splitList(value).length > 0).length;
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

  if (!statusMatches(item.user_status, filters.status_filter)) return false;
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

function statusFilterChange(filters: FeedFilters, statusLabels: string[]): FeedFilters {
  const statuses = normalizeStatusLabels(statusLabels);
  return {
    ...filters,
    status_filter: statuses.join(", "),
    include_ignored: statuses.includes("ignored") || statuses.includes("all"),
  };
}

function statusMatches(status: OpportunityStatus | null, statusFilter: string): boolean {
  const statuses = normalizeStatusLabels(splitList(statusFilter));
  if (statuses.length === 0 || statuses.includes("visible")) return status !== "ignored";
  if (statuses.includes("all")) return true;
  if (statuses.includes("browsing") && status === null) return true;
  return Boolean(status && statuses.includes(status));
}

function statusLabelsFromFilter(statusFilter: string): string[] {
  return splitList(statusFilter).filter((status) => status !== "visible").map((status) => (status === "browsing" ? "Not in my board" : label(status)));
}

function normalizeStatusLabels(values: string[]): string[] {
  const map: Record<string, string> = {
    all: "all",
    visible: "visible",
    "not in my board": "browsing",
    browsing: "browsing",
    saved: "saved",
    planned: "planned",
    applied: "applied",
    accepted: "accepted",
    rejected: "rejected",
    ignored: "ignored",
  };
  return [...new Set(values.map((value) => map[value.toLowerCase().trim()] ?? value.toLowerCase().trim()).filter(Boolean))];
}

import type { OpportunityPayload, ProfileDetailsPayload, ProfilePayload } from "./api";
import type { CareerStage, DisplayOpportunityStatus, OpportunityStatus, OpportunityType } from "./types";

export const careerStages: CareerStage[] = ["bachelor", "master", "phd", "postdoc", "early_career", "senior"];
export const opportunityTypes: OpportunityType[] = ["grant", "exchange", "fellowship", "internship", "research_position", "training"];
export const trackedStatuses: OpportunityStatus[] = ["saved", "planned", "applied", "accepted", "rejected", "ignored"];
export const displayStatuses: DisplayOpportunityStatus[] = ["browsing", ...trackedStatuses];
export const reminderStatuses: OpportunityStatus[] = ["saved", "planned"];
export const researcherViews = ["about", "dashboard", "profile", "feed", "board", "assistant", "reminders"] as const;

export type View =
  | "auth"
  | "dashboard"
  | "feed"
  | "profile"
  | "account"
  | "board"
  | "reminders"
  | "notifications"
  | "assistant"
  | "about"
  | "verify_email"
  | "orcid_callback"
  | "admin"
  | "opportunity";

export const viewRoutes: Record<View, string> = {
  auth: "/sign-in",
  dashboard: "/dashboard",
  feed: "/matches",
  profile: "/profile",
  account: "/account",
  board: "/board",
  assistant: "/assistant",
  about: "/about",
  verify_email: "/verify-email",
  orcid_callback: "/orcid-callback",
  reminders: "/reminders",
  notifications: "/notifications",
  admin: "/admin",
  opportunity: "/opportunities",
};

const routeViews = Object.fromEntries(Object.entries(viewRoutes).map(([view, path]) => [path, view])) as Record<string, View>;

export function viewFromPath(pathname: string): View {
  if (/^\/opportunities\/\d+$/.test(pathname)) return "opportunity";
  return routeViews[pathname] ?? "dashboard";
}

export function opportunityIdFromPath(pathname: string): number | null {
  const match = pathname.match(/^\/opportunities\/(\d+)$/);
  return match ? Number(match[1]) : null;
}

export const defaultFilters = {
  keyword: "",
  opportunity_type: "",
  country: "",
  career_stage: "",
  source: "",
  active_only: true,
  min_score: 0,
  include_ignored: false,
  status_filter: "",
  sort_by: "match_score",
  sort_order: "desc",
};

export const blankProfile: ProfilePayload = {
  full_name: "",
  email: "",
  career_stage: "phd",
  country: "",
  disciplines: [],
  keywords: [],
  preferred_countries: [],
  orcid_id: "",
  google_scholar_url: "",
  linkedin_url: "",
};

export const blankDetails: ProfileDetailsPayload = {
  research_summary: "",
  publications: [],
  degrees: [],
  languages: [],
  funding_interests: [],
  unavailable_countries: [],
  preferred_opportunity_types: [],
  min_duration_months: null,
  max_duration_months: null,
};

export const blankOpportunity: OpportunityPayload = {
  title: "",
  opportunity_type: "grant",
  source: "curated",
  url: "",
  summary: "",
  eligibility: "",
  disciplines: [],
  keywords: [],
  countries: [],
  career_stages: [],
  deadline: null,
};

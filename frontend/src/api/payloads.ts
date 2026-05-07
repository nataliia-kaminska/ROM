import type { CareerStage, OpportunityType } from "../types";

export type ProfilePayload = {
  full_name: string;
  email: string | null;
  career_stage: CareerStage;
  country: string | null;
  disciplines: string[];
  keywords: string[];
  preferred_countries: string[];
  orcid_id: string | null;
  google_scholar_url: string | null;
  linkedin_url: string | null;
};

export type ProfileDetailsPayload = {
  research_summary: string;
  publications: string[];
  degrees: string[];
  languages: string[];
  funding_interests: string[];
  unavailable_countries: string[];
  preferred_opportunity_types: OpportunityType[];
  min_duration_months: number | null;
  max_duration_months: number | null;
};

export type OpportunityPayload = {
  title: string;
  opportunity_type: OpportunityType;
  source: string;
  url: string;
  summary: string;
  eligibility: string;
  disciplines: string[];
  keywords: string[];
  countries: string[];
  career_stages: string[];
  deadline: string | null;
};

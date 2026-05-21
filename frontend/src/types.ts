export type CareerStage = "bachelor" | "master" | "phd" | "postdoc" | "early_career" | "senior";

export type OpportunityType = "grant" | "exchange" | "fellowship" | "internship" | "research_position" | "training";

export type OpportunityStatus = "saved" | "ignored" | "planned" | "applied" | "rejected" | "accepted";

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: "researcher" | "admin";
  is_active: boolean;
  email_verified: boolean;
  auth_provider: "local" | "orcid" | string;
  orcid_id: string | null;
  password_login_enabled: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type RegisterResponse = {
  message: string;
  email: string;
};

export type AuthProviderConfig = {
  orcid_oauth_enabled: boolean;
};

export type Profile = {
  id: number;
  user_id: number | null;
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

export type ProfileDetails = {
  id: number;
  profile_id: number;
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

export type OpenAlexPreview = {
  display_name: string;
  summary: string;
  concepts: string[];
  works: string[];
  openalex_author_id: string | null;
  suggested_disciplines: string[];
  suggested_keywords: string[];
  suggested_funding_interests: string[];
  new_publications: string[];
  existing_publications: number;
  works_count: number;
};

export type Opportunity = {
  id: number;
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
  created_at?: string | null;
  extracted_requirements?: {
    career_stages: string[];
    countries: string[];
    required_degree: string;
    languages: string[];
    publication_expectation: string;
    mobility: string;
    citizenship: string;
    years_since_phd: number | null;
    key_details?: string[];
    why_it_matters?: string[];
    snippets: string[];
    confidence: number;
  } | null;
  requirements_confidence?: number;
};

export type OpportunityFilterOptions = {
  sources: string[];
  countries: string[];
  keywords: string[];
  disciplines: string[];
  career_stages: string[];
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type Recommendation = {
  opportunity: Opportunity;
  match_score: number;
  semantic_score: number;
  score_breakdown: {
    semantic: number;
    eligibility: number;
    deadline: number;
    user_history: number;
    final: number;
  };
  reasons: string[];
  readiness_score: number;
  gaps: string[];
  strengths: string[];
  user_status: OpportunityStatus | null;
};

export type Reminder = {
  id: number;
  profile_id: number;
  opportunity_id: number;
  remind_on: string;
  message: string;
  status: "pending" | "completed";
  completed_at: string | null;
};

export type StatusRecord = {
  id: number;
  profile_id: number;
  opportunity_id: number;
  status: OpportunityStatus;
  notes: string;
};

export type QueueStats = {
  name: string;
  queued_count: number;
  failed_count: number;
  started_count: number;
  finished_count: number;
  deferred_count: number;
};

export type JobSummary = {
  job_id: string;
  queue: string;
  status: string;
};

export type NotificationItem = {
  id: number;
  notification_type: string;
  subject: string;
  body: string;
  status: string;
  skip_reason: string;
  recipient: string;
  provider: string;
  provider_message_id: string;
  delivery_attempts: number;
  last_error: string;
  created_at: string;
  sent_at: string | null;
};

export type NotificationPreference = {
  email_enabled: boolean;
  deadline_reminders_enabled: boolean;
  weekly_digest_enabled: boolean;
  high_match_alerts_enabled: boolean;
  min_alert_score: number;
};

export type ApplicationAssistantResult = {
  opportunity_id: number;
  profile_id: number;
  profile_name: string;
  opportunity_title: string;
  retrieved_context: string[];
  web_research: string[];
  application_checklist: string[];
  motivation_letter_outline: string[];
  research_fit_statement: string;
  missing_profile_fields: string[];
  eligibility_warnings: string[];
  readiness_score: number;
  gap_analysis: string[];
  strengths: string[];
  advisor_provider: string;
  advisor_memo: string;
  exported_notes: string;
};

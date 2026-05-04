import type {
  AuthResponse,
  ApplicationAssistantResult,
  CareerStage,
  Opportunity,
  OpportunityStatus,
  OpportunityType,
  Profile,
  ProfileDetails,
  JobSummary,
  NotificationItem,
  NotificationPreference,
  QueueStats,
  Recommendation,
  Reminder,
  StatusRecord,
  User,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type RequestOptions = {
  token?: string | null;
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  Object.entries(options.query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  const response = await fetch(url, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

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

export const api = {
  baseUrl: API_BASE_URL,
  register: (body: { email: string; password: string; full_name: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body }),
  login: (body: { email: string; password: string }) => request<AuthResponse>("/auth/login", { method: "POST", body }),
  me: (token: string) => request<User>("/auth/me", { token }),
  profiles: (token: string) => request<Profile[]>("/profiles/me", { token }),
  createProfile: (token: string, body: ProfilePayload) => request<Profile>("/profiles", { token, method: "POST", body }),
  getProfileDetails: (token: string, profileId: number) =>
    request<ProfileDetails>(`/profiles/${profileId}/details`, { token }),
  saveProfileDetails: (token: string, profileId: number, body: ProfileDetailsPayload) =>
    request<ProfileDetails>(`/profiles/${profileId}/details`, { token, method: "PUT", body }),
  importOrcid: (
    token: string,
    body: {
      orcid_id: string;
      email: string | null;
      career_stage: CareerStage;
      disciplines: string[];
      preferred_countries: string[];
    },
  ) => request<{ imported: boolean; profile: Profile; preview: Record<string, unknown> }>("/integrations/orcid/import", {
    token,
    method: "POST",
    body,
  }),
  importOpenAlex: (
    token: string,
    body: { profile_id: number; openalex_author_id?: string | null; orcid_id?: string | null; max_works: number },
  ) =>
    request<{ profile: Profile; details: ProfileDetails; preview: Record<string, unknown> }>("/integrations/openalex/import", {
      token,
      method: "POST",
      body,
    }),
  opportunities: (query: Record<string, string | number | boolean | null | undefined>) =>
    request<Opportunity[]>("/opportunities", { query }),
  opportunity: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  recommendations: (token: string, profileId: number, query: { min_score: number; include_ignored: boolean }) =>
    request<Recommendation[]>(`/recommendations/${profileId}`, { token, query: { ...query, limit: 100 } }),
  setStatus: (token: string, profileId: number, opportunityId: number, status: OpportunityStatus, notes = "") =>
    request<StatusRecord>(`/profiles/${profileId}/opportunities/${opportunityId}/status`, {
      token,
      method: "PUT",
      body: { status, notes },
    }),
  statuses: (token: string, profileId: number) =>
    request<StatusRecord[]>(`/profiles/${profileId}/opportunities/statuses`, { token }),
  reminders: (token: string, profileId: number, includeCompleted = false) =>
    request<Reminder[]>(`/profiles/${profileId}/reminders`, {
      token,
      query: { include_completed: includeCompleted },
    }),
  createReminder: (token: string, profileId: number, body: { opportunity_id: number; remind_on: string; message: string }) =>
    request<Reminder>(`/profiles/${profileId}/reminders`, { token, method: "POST", body }),
  completeReminder: (token: string, profileId: number, reminderId: number) =>
    request<Reminder>(`/profiles/${profileId}/reminders/${reminderId}/complete`, { token, method: "PUT" }),
  grantsGov: (body: { keyword: string; limit: number; import_results: boolean }) =>
    request<{ source: string; batch_id: number; imported_count: number; skipped_count: number; opportunities: Opportunity[] }>(
      "/ingestion/grants-gov/search",
      { method: "POST", body },
    ),
  enqueueGrantsGov: (body: { keyword: string; limit: number; import_results: boolean }) =>
    request<JobSummary>("/jobs/ingestion/grants-gov", { method: "POST", body }),
  enqueueReminderScan: () => request<JobSummary>("/jobs/reminders/scan", { method: "POST" }),
  enqueueEmbeddingRefresh: () => request<JobSummary>("/jobs/embeddings/refresh", { method: "POST" }),
  queues: () => request<QueueStats[]>("/jobs"),
  job: (jobId: string, queueName?: string) => request<Record<string, unknown>>(`/jobs/${jobId}`, { query: { queue_name: queueName } }),
  notifications: (token: string, includeRead = false) =>
    request<NotificationItem[]>("/notifications", { token, query: { include_read: includeRead } }),
  notificationPreferences: (token: string) => request<NotificationPreference>("/notifications/preferences", { token }),
  saveNotificationPreferences: (token: string, body: NotificationPreference) =>
    request<NotificationPreference>("/notifications/preferences", { token, method: "PUT", body }),
  markNotificationRead: (token: string, notificationId: number) =>
    request<NotificationItem>(`/notifications/${notificationId}/read`, { token, method: "PUT" }),
  unsubscribeNotifications: (token: string) =>
    request<NotificationPreference>("/notifications/unsubscribe", { token, method: "POST" }),
  adminDashboard: () => request<Record<string, unknown>>("/admin/dashboard"),
  adminAnalytics: () => request<Record<string, unknown>>("/admin/analytics"),
  adminAuditLog: () => request<Record<string, unknown>[]>("/admin/audit-log"),
  adminDuplicates: () => request<Record<string, unknown>[]>("/admin/opportunities/duplicates"),
  applicationAssistant: (token: string, body: { profile_id: number; opportunity_id: number }) =>
    request<ApplicationAssistantResult>("/application-assistant", { token, method: "POST", body }),
  bulkImport: (body: { source: string; dry_run: boolean; opportunities: OpportunityPayload[] }) =>
    request<{ imported_count: number; updated_count: number; skipped_count: number; dry_run: boolean; opportunities: Opportunity[] }>(
      "/opportunities/bulk-import",
      { method: "POST", body },
    ),
  externalSourceImport: (body: {
    source_name: string;
    source_url: string;
    source_kind: "rss" | "json";
    import_results: boolean;
    limit: number;
    default_opportunity_type: OpportunityType;
    default_country: string | null;
    default_career_stage: string | null;
    default_discipline: string | null;
    keyword: string | null;
  }) =>
    request<{
      source: string;
      batch_id: number | null;
      imported_count: number;
      updated_count: number;
      skipped_count: number;
      opportunities: Opportunity[];
    }>("/ingestion/external-source/import", { method: "POST", body }),
};

import type { JobSummary, QueueStats } from "../types";
import { request } from "./client";

export const adminApi = {
  enqueueGrantsGov: (token: string, body: { keyword: string; limit: number; import_results: boolean }) =>
    request<JobSummary>("/jobs/ingestion/grants-gov", { token, method: "POST", body }),
  enqueueReminderScan: (token: string) => request<JobSummary>("/jobs/reminders/scan", { token, method: "POST" }),
  enqueueWeeklyDigest: (token: string) => request<JobSummary>("/jobs/notifications/weekly-digest", { token, method: "POST" }),
  enqueueHighMatchAlerts: (token: string) => request<JobSummary>("/jobs/notifications/high-match-alerts", { token, method: "POST" }),
  enqueueEmbeddingRefresh: (token: string) => request<JobSummary>("/jobs/embeddings/refresh", { token, method: "POST" }),
  queues: (token: string) => request<QueueStats[]>("/jobs", { token }),
  job: (token: string, jobId: string, queueName?: string) => request<Record<string, unknown>>(`/jobs/${jobId}`, { token, query: { queue_name: queueName } }),
  adminDashboard: (token: string) => request<Record<string, unknown>>("/admin/dashboard", { token }),
  adminAnalytics: (token: string) => request<Record<string, unknown>>("/admin/analytics", { token }),
  adminAuditLog: (token: string) => request<Record<string, unknown>[]>("/admin/audit-log", { token }),
  adminDuplicates: (token: string) => request<Record<string, unknown>[]>("/admin/opportunities/duplicates", { token }),
};

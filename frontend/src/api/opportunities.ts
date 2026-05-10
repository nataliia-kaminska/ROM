import type { Opportunity, OpportunityStatus, OpportunityType, Recommendation, StatusRecord } from "../types";
import type { OpportunityPayload } from "./payloads";
import { request } from "./client";

export const opportunitiesApi = {
  opportunities: (query: Record<string, string | number | boolean | null | undefined>) =>
    request<Opportunity[]>("/opportunities", { query }),
  opportunity: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  recommendations: (token: string, profileId: number, query: { min_score: number; include_ignored: boolean; limit: number; offset: number }) =>
    request<Recommendation[]>(`/recommendations/${profileId}`, { token, query }),
  setStatus: (token: string, profileId: number, opportunityId: number, status: OpportunityStatus, notes = "") =>
    request<StatusRecord>(`/profiles/${profileId}/opportunities/${opportunityId}/status`, {
      token,
      method: "PUT",
      body: { status, notes },
    }),
  statuses: (token: string, profileId: number) =>
    request<StatusRecord[]>(`/profiles/${profileId}/opportunities/statuses`, { token }),
  bulkImport: (body: { source: string; dry_run: boolean; opportunities: OpportunityPayload[] }) =>
    request<{ imported_count: number; updated_count: number; skipped_count: number; dry_run: boolean; opportunities: Opportunity[] }>(
      "/opportunities/bulk-import",
      { method: "POST", body },
    ),
  externalSourceImport: (body: {
    source_name: string;
    source_url: string;
    source_kind: "rss" | "json" | "html";
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
  grantsGov: (body: { keyword: string; limit: number; import_results: boolean }) =>
    request<{ source: string; batch_id: number; imported_count: number; skipped_count: number; opportunities: Opportunity[] }>(
      "/ingestion/grants-gov/search",
      { method: "POST", body },
    ),
};

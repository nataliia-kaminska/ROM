import { type FormEvent, useState } from "react";
import { api, type OpportunityPayload } from "../api";
import { blankOpportunity } from "../constants";
import type { OpportunityType, Profile } from "../types";
import { normalizeText } from "../utils/format";

export function useAdminOps({
  token,
  activeProfile,
  setError,
  setNotice,
  refreshWorkspace,
}: {
  token: string | null;
  activeProfile: Profile | null;
  setError: (message: string) => void;
  setNotice: (message: string) => void;
  refreshWorkspace: (profile?: Profile | null) => Promise<void>;
}) {
  const [adminData, setAdminData] = useState<Record<string, unknown> | null>(null);
  const [auditLog, setAuditLog] = useState<Record<string, unknown>[]>([]);
  const [duplicateGroups, setDuplicateGroups] = useState<Record<string, unknown>[]>([]);
  const [importForm, setImportForm] = useState({ source: "curated", dry_run: true, payload: JSON.stringify([blankOpportunity], null, 2) });
  const [grantsForm, setGrantsForm] = useState({ keyword: "", limit: 10, import_results: true });
  const [externalForm, setExternalForm] = useState({
    source_name: "nrfu",
    source_url: "",
    source_kind: "html" as "rss" | "json" | "html",
    import_results: true,
    limit: 25,
    default_opportunity_type: "fellowship" as OpportunityType,
    default_country: "",
    default_career_stage: "",
    default_discipline: "",
    keyword: "",
  });
  const [jobForm, setJobForm] = useState({ job_id: "", queue_name: "" });
  const [queueStats, setQueueStats] = useState<{ name: string; queued_count: number; failed_count: number; started_count: number; finished_count: number; deferred_count: number }[]>([]);
  const [jobDetail, setJobDetail] = useState<Record<string, unknown> | null>(null);
  const [adminBusy, setAdminBusy] = useState<string | null>(null);

  async function loadAdminOps() {
    if (!token) return;
    setError("");
    setAdminBusy("operations");
    try {
      const [dashboard, audit, duplicates] = await Promise.all([api.adminDashboard(token), api.adminAuditLog(token), api.adminDuplicates(token)]);
      setAdminData(dashboard);
      setAuditLog(audit);
      setDuplicateGroups(duplicates);
      setNotice("Operations data loaded");
    } catch (adminError) {
      setError((adminError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function runBulkImport(event: FormEvent) {
    event.preventDefault();
    setError("");
    setAdminBusy("curated");
    try {
      const opportunities = JSON.parse(importForm.payload) as OpportunityPayload[];
      if (!Array.isArray(opportunities) || opportunities.length === 0) {
        throw new Error("Curated import JSON must be a non-empty opportunity array.");
      }
      const result = await api.bulkImport({ source: importForm.source, dry_run: importForm.dry_run, opportunities });
      setNotice(
        `${result.dry_run ? "Validated" : "Imported"} ${result.imported_count} new, ${result.updated_count} updated, ${result.skipped_count} skipped`,
      );
      await refreshWorkspace(activeProfile);
    } catch (importError) {
      setError((importError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function runExternalImport(event: FormEvent) {
    event.preventDefault();
    if (!externalForm.source_name || !externalForm.source_url) {
      setError("Source name and feed URL are required.");
      return;
    }
    setError("");
    setAdminBusy("external");
    try {
      const result = await api.externalSourceImport({
        ...externalForm,
        default_country: normalizeText(externalForm.default_country),
        default_career_stage: normalizeText(externalForm.default_career_stage),
        default_discipline: normalizeText(externalForm.default_discipline),
        keyword: normalizeText(externalForm.keyword),
      });
      setNotice(`${result.source}: ${result.imported_count} imported, ${result.updated_count} updated, ${result.skipped_count} skipped`);
      await refreshWorkspace(activeProfile);
    } catch (importError) {
      setError((importError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function runGrantsGov(event: FormEvent) {
    event.preventDefault();
    setError("");
    setAdminBusy("grants-now");
    try {
      const result = await api.grantsGov(grantsForm);
      setNotice(`${result.source}: ${result.imported_count} imported, ${result.skipped_count} skipped`);
      await refreshWorkspace(activeProfile);
    } catch (importError) {
      setError((importError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function enqueueGrantsGov(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    setAdminBusy("grants-queue");
    try {
      const result = await api.enqueueGrantsGov(token, grantsForm);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued Grants.gov job ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function enqueueReminderScan() {
    if (!token) return;
    setError("");
    setAdminBusy("reminder-scan");
    try {
      const result = await api.enqueueReminderScan(token);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued reminder scan ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function enqueueEmbeddingRefresh() {
    if (!token) return;
    setError("");
    setAdminBusy("embeddings");
    try {
      const result = await api.enqueueEmbeddingRefresh(token);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued embedding refresh ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function enqueueWeeklyDigest() {
    if (!token) return;
    setError("");
    setAdminBusy("digest");
    try {
      const job = await api.enqueueWeeklyDigest(token);
      setJobForm({ job_id: job.job_id, queue_name: job.queue });
      setNotice(`Queued weekly digest ${job.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function enqueueHighMatchAlerts() {
    if (!token) return;
    setError("");
    setAdminBusy("alerts");
    try {
      const job = await api.enqueueHighMatchAlerts(token);
      setJobForm({ job_id: job.job_id, queue_name: job.queue });
      setNotice(`Queued high-match alerts ${job.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function loadQueues() {
    if (!token) return;
    setError("");
    setAdminBusy("queues");
    try {
      setQueueStats(await api.queues(token));
      setNotice("Queue stats loaded");
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  async function loadJob(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    setAdminBusy("job-detail");
    try {
      setJobDetail(await api.job(token, jobForm.job_id, jobForm.queue_name));
      setNotice("Job detail loaded");
    } catch (jobError) {
      setError((jobError as Error).message);
    } finally {
      setAdminBusy(null);
    }
  }

  return {
    importForm,
    grantsForm,
    externalForm,
    jobForm,
    queueStats,
    jobDetail,
    adminData,
    duplicateGroups,
    auditLog,
    adminBusy,
    setImportForm,
    setGrantsForm,
    setExternalForm,
    setJobForm,
    enqueueGrantsGov,
    runGrantsGov,
    runBulkImport,
    runExternalImport,
    loadQueues,
    enqueueReminderScan,
    enqueueWeeklyDigest,
    enqueueHighMatchAlerts,
    enqueueEmbeddingRefresh,
    loadJob,
    loadAdminOps,
  };
}

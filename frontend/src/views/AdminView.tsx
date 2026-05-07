import type { FormEvent } from "react";
import type { OpportunityType } from "../types";
import { opportunityTypes } from "../constants";
import { Field, JsonTextArea, SelectField } from "../components/ui";

type ImportForm = { source: string; dry_run: boolean; payload: string };
type GrantsForm = { keyword: string; limit: number; import_results: boolean };
type ExternalForm = {
  source_name: string;
  source_url: string;
  source_kind: "rss" | "json";
  import_results: boolean;
  limit: number;
  default_opportunity_type: OpportunityType;
  default_country: string;
  default_career_stage: string;
  default_discipline: string;
  keyword: string;
};
type JobForm = { job_id: string; queue_name: string };
type QueueStats = { name: string; queued_count: number; failed_count: number; started_count: number; finished_count: number; deferred_count: number };

export function AdminView({
  importForm,
  grantsForm,
  externalForm,
  jobForm,
  queueStats,
  jobDetail,
  adminData,
  duplicateGroups,
  auditLog,
  onImportFormChange,
  onGrantsFormChange,
  onExternalFormChange,
  onJobFormChange,
  onEnqueueGrantsGov,
  onRunGrantsGovNow,
  onRunBulkImport,
  onRunExternalImport,
  onLoadQueues,
  onEnqueueReminderScan,
  onEnqueueWeeklyDigest,
  onEnqueueHighMatchAlerts,
  onEnqueueEmbeddingRefresh,
  onLoadJob,
  onLoadAdminOps,
}: {
  importForm: ImportForm;
  grantsForm: GrantsForm;
  externalForm: ExternalForm;
  jobForm: JobForm;
  queueStats: QueueStats[];
  jobDetail: Record<string, unknown> | null;
  adminData: Record<string, unknown> | null;
  duplicateGroups: Record<string, unknown>[];
  auditLog: Record<string, unknown>[];
  onImportFormChange: (form: ImportForm) => void;
  onGrantsFormChange: (form: GrantsForm) => void;
  onExternalFormChange: (form: ExternalForm) => void;
  onJobFormChange: (form: JobForm) => void;
  onEnqueueGrantsGov: (event: FormEvent) => void;
  onRunGrantsGovNow: (event: FormEvent) => void;
  onRunBulkImport: (event: FormEvent) => void;
  onRunExternalImport: (event: FormEvent) => void;
  onLoadQueues: () => void;
  onEnqueueReminderScan: () => void;
  onEnqueueWeeklyDigest: () => void;
  onEnqueueHighMatchAlerts: () => void;
  onEnqueueEmbeddingRefresh: () => void;
  onLoadJob: (event: FormEvent) => void;
  onLoadAdminOps: () => void;
}) {
  return (
    <section className="panel">
      <h2>Admin Imports</h2>
      <form className="grid-form" onSubmit={onEnqueueGrantsGov}>
        <Field labelText="Grants.gov keyword" value={grantsForm.keyword} onChange={(keyword) => onGrantsFormChange({ ...grantsForm, keyword })} />
        <Field labelText="Limit" type="number" value={String(grantsForm.limit)} onChange={(limit) => onGrantsFormChange({ ...grantsForm, limit: Number(limit) })} />
        <label className="toggle">
          <input
            type="checkbox"
            checked={grantsForm.import_results}
            onChange={(event) => onGrantsFormChange({ ...grantsForm, import_results: event.target.checked })}
          />
          Import results
        </label>
        <button className="primary">Queue Grants.gov search</button>
        <button className="secondary" type="button" onClick={onRunGrantsGovNow}>
          Run now
        </button>
      </form>
      <form className="grid-form separated" onSubmit={onRunBulkImport}>
        <Field labelText="Source" value={importForm.source} onChange={(source) => onImportFormChange({ ...importForm, source })} />
        <label className="toggle">
          <input type="checkbox" checked={importForm.dry_run} onChange={(event) => onImportFormChange({ ...importForm, dry_run: event.target.checked })} />
          Dry run
        </label>
        <JsonTextArea labelText="Curated opportunities JSON" value={importForm.payload} onChange={(payload) => onImportFormChange({ ...importForm, payload })} />
        <button className="primary span-2">Import curated list</button>
      </form>
      <form className="grid-form separated" onSubmit={onRunExternalImport}>
        <div className="span-2">
          <h2>External Source Import</h2>
          <p className="muted">Normalize RSS or JSON feeds from EURAXESS, DAAD, Fulbright, Erasmus+, MSCA, universities, or foundations.</p>
        </div>
        <Field labelText="Source name" value={externalForm.source_name} onChange={(source_name) => onExternalFormChange({ ...externalForm, source_name })} />
        <Field labelText="Feed URL" value={externalForm.source_url} onChange={(source_url) => onExternalFormChange({ ...externalForm, source_url })} />
        <SelectField labelText="Kind" value={externalForm.source_kind} options={["rss", "json"]} onChange={(source_kind) => onExternalFormChange({ ...externalForm, source_kind })} />
        <SelectField labelText="Default type" value={externalForm.default_opportunity_type} options={opportunityTypes} onChange={(default_opportunity_type) => onExternalFormChange({ ...externalForm, default_opportunity_type })} />
        <Field labelText="Limit" type="number" value={String(externalForm.limit)} onChange={(limit) => onExternalFormChange({ ...externalForm, limit: Number(limit) })} />
        <Field labelText="Default country" value={externalForm.default_country} onChange={(default_country) => onExternalFormChange({ ...externalForm, default_country })} />
        <Field labelText="Default career stage" value={externalForm.default_career_stage} onChange={(default_career_stage) => onExternalFormChange({ ...externalForm, default_career_stage })} />
        <Field labelText="Default discipline" value={externalForm.default_discipline} onChange={(default_discipline) => onExternalFormChange({ ...externalForm, default_discipline })} />
        <Field labelText="Keyword tag" value={externalForm.keyword} onChange={(keyword) => onExternalFormChange({ ...externalForm, keyword })} />
        <label className="toggle">
          <input
            type="checkbox"
            checked={externalForm.import_results}
            onChange={(event) => onExternalFormChange({ ...externalForm, import_results: event.target.checked })}
          />
          Import results
        </label>
        <button className="primary span-2">Import external source</button>
      </form>
      <div className="separated">
        <div className="section-title">
          <div>
            <h2>Background Jobs</h2>
            <p>Queue health, failed-job visibility, and reminder scans use Redis + RQ.</p>
          </div>
          <div className="actions">
            <button className="secondary" onClick={onLoadQueues}>Load queues</button>
            <button className="secondary" onClick={onEnqueueReminderScan}>Queue reminder scan</button>
            <button className="secondary" onClick={onEnqueueWeeklyDigest}>Queue digest</button>
            <button className="secondary" onClick={onEnqueueHighMatchAlerts}>Queue alerts</button>
            <button className="secondary" onClick={onEnqueueEmbeddingRefresh}>Refresh embeddings</button>
          </div>
        </div>
        <div className="queue-grid">
          {queueStats.map((queue) => (
            <article className="mini-card" key={queue.name}>
              <strong>{queue.name}</strong>
              <small>Queued {queue.queued_count}</small>
              <small>Started {queue.started_count}</small>
              <small>Finished {queue.finished_count}</small>
              <small>Failed {queue.failed_count}</small>
            </article>
          ))}
        </div>
        <form className="grid-form separated" onSubmit={onLoadJob}>
          <Field labelText="Job id" value={jobForm.job_id} onChange={(job_id) => onJobFormChange({ ...jobForm, job_id })} />
          <Field labelText="Queue" value={jobForm.queue_name} onChange={(queue_name) => onJobFormChange({ ...jobForm, queue_name })} />
          <button className="primary span-2">Load job</button>
        </form>
        {jobDetail && <pre className="job-detail">{JSON.stringify(jobDetail, null, 2)}</pre>}
      </div>
      <div className="separated">
        <div className="section-title">
          <div>
            <h2>Operations</h2>
            <p>Source health, duplicate groups, analytics, and audit log.</p>
          </div>
          <button className="secondary" onClick={onLoadAdminOps}>Load operations</button>
        </div>
        {adminData && <pre className="job-detail">{JSON.stringify(adminData, null, 2)}</pre>}
        {duplicateGroups.length > 0 && <pre className="job-detail">{JSON.stringify(duplicateGroups, null, 2)}</pre>}
        {auditLog.length > 0 && <pre className="job-detail">{JSON.stringify(auditLog, null, 2)}</pre>}
      </div>
    </section>
  );
}

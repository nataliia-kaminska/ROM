import { type FormEvent, useState } from "react";
import type { OpportunityType } from "../types";
import { opportunityTypes } from "../constants";
import { ActionButton, Field, JsonTextArea, SelectField } from "../components/ui";

type ImportForm = { source: string; dry_run: boolean; payload: string };
type GrantsForm = { keyword: string; limit: number; import_results: boolean };
type EUFundingForm = { keyword: string; source_name: string; programme: string; limit: number; import_results: boolean };
type ExternalForm = {
  source_name: string;
  source_url: string;
  source_kind: "rss" | "json" | "html";
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

const supportedExternalSources = [
  "nrfu",
  "nauka_gov_ua",
  "house_of_europe",
  "science_for_ukraine",
  "msca4ukraine",
  "daad_ukraine",
  "fulbright_ukraine",
  "erasmus",
  "euraxess",
  "horizon_europe",
  "daad",
  "fulbright",
  "msca",
  "nawa",
];

const adminTabs = ["sources", "curated", "jobs", "operations"] as const;
type AdminTab = (typeof adminTabs)[number];

const sourcePresets = [
  {
    label: "Horizon Europe",
    group: "European",
    source_name: "horizon_europe",
    source_url: "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals",
    source_kind: "html" as const,
    default_opportunity_type: "grant" as OpportunityType,
    default_country: "European Union",
    default_career_stage: "postdoc",
    default_discipline: "Research and Innovation",
    keyword: "horizon europe, european commission, research",
  },
  {
    label: "Erasmus+",
    group: "European",
    source_name: "erasmus",
    source_url: "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals",
    source_kind: "html" as const,
    default_opportunity_type: "exchange" as OpportunityType,
    default_country: "European Union",
    default_career_stage: "",
    default_discipline: "Education",
    keyword: "erasmus, mobility, exchange, europe",
  },
  {
    label: "NAWA",
    group: "European",
    source_name: "nawa",
    source_url: "https://nawa.gov.pl/en/",
    source_kind: "html" as const,
    default_opportunity_type: "fellowship" as OpportunityType,
    default_country: "Poland",
    default_career_stage: "",
    default_discipline: "Research",
    keyword: "nawa, poland, scholarship, academic exchange",
  },
  {
    label: "NRFU",
    group: "Ukraine",
    source_name: "nrfu",
    source_url: "https://nrfu.org.ua/en/contests/current-calls/",
    source_kind: "html" as const,
    default_opportunity_type: "grant" as OpportunityType,
    default_country: "Ukraine",
    default_career_stage: "",
    default_discipline: "Research",
    keyword: "ukraine, research, grant",
  },
  {
    label: "House of Europe",
    group: "Ukraine",
    source_name: "house_of_europe",
    source_url: "https://houseofeurope.org.ua/en/opportunities",
    source_kind: "html" as const,
    default_opportunity_type: "grant" as OpportunityType,
    default_country: "Ukraine",
    default_career_stage: "",
    default_discipline: "",
    keyword: "ukraine, europe, culture, research",
  },
  {
    label: "Science for Ukraine",
    group: "Ukraine",
    source_name: "science_for_ukraine",
    source_url: "https://scienceforukraine.eu/",
    source_kind: "html" as const,
    default_opportunity_type: "research_position" as OpportunityType,
    default_country: "Ukraine",
    default_career_stage: "",
    default_discipline: "Research",
    keyword: "ukraine, researcher support",
  },
  {
    label: "MSCA4Ukraine",
    group: "Ukraine",
    source_name: "msca4ukraine",
    source_url: "https://sareurope.eu/msca4ukraine/",
    source_kind: "html" as const,
    default_opportunity_type: "fellowship" as OpportunityType,
    default_country: "Ukraine",
    default_career_stage: "phd",
    default_discipline: "Research",
    keyword: "ukraine, msca, fellowship",
  },
  {
    label: "DAAD Ukraine",
    group: "Ukraine",
    source_name: "daad_ukraine",
    source_url: "https://www.daad-ukraine.org/en/",
    source_kind: "html" as const,
    default_opportunity_type: "fellowship" as OpportunityType,
    default_country: "Germany",
    default_career_stage: "",
    default_discipline: "",
    keyword: "ukraine, germany, mobility",
  },
  {
    label: "Fulbright Ukraine",
    group: "Ukraine",
    source_name: "fulbright_ukraine",
    source_url: "https://fulbright.org.ua/en/",
    source_kind: "html" as const,
    default_opportunity_type: "fellowship" as OpportunityType,
    default_country: "United States",
    default_career_stage: "",
    default_discipline: "",
    keyword: "ukraine, fulbright, exchange",
  },
];

const euFundingPresets = [
  { label: "Horizon Europe", source_name: "horizon_europe", programme: "Horizon Europe", keyword: "research innovation" },
  { label: "MSCA", source_name: "msca", programme: "Marie Sklodowska-Curie", keyword: "postdoctoral fellowship doctoral network staff exchanges" },
  { label: "Erasmus+ Calls", source_name: "erasmus", programme: "Erasmus+", keyword: "erasmus mobility education cooperation" },
  { label: "All EU Funding", source_name: "eu_funding_tenders", programme: "", keyword: "research fellowship mobility" },
];

export function AdminView({
  importForm,
  grantsForm,
  euFundingForm,
  externalForm,
  jobForm,
  queueStats,
  jobDetail,
  adminData,
  duplicateGroups,
  auditLog,
  adminBusy,
  onImportFormChange,
  onGrantsFormChange,
  onEuFundingFormChange,
  onExternalFormChange,
  onJobFormChange,
  onEnqueueGrantsGov,
  onRunGrantsGovNow,
  onRunEuFundingTenders,
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
  euFundingForm: EUFundingForm;
  externalForm: ExternalForm;
  jobForm: JobForm;
  queueStats: QueueStats[];
  jobDetail: Record<string, unknown> | null;
  adminData: Record<string, unknown> | null;
  duplicateGroups: Record<string, unknown>[];
  auditLog: Record<string, unknown>[];
  adminBusy: string | null;
  onImportFormChange: (form: ImportForm) => void;
  onGrantsFormChange: (form: GrantsForm) => void;
  onEuFundingFormChange: (form: EUFundingForm) => void;
  onExternalFormChange: (form: ExternalForm) => void;
  onJobFormChange: (form: JobForm) => void;
  onEnqueueGrantsGov: (event: FormEvent) => void;
  onRunGrantsGovNow: (event: FormEvent) => void;
  onRunEuFundingTenders: (event: FormEvent) => void;
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
  const [activeTab, setActiveTab] = useState<AdminTab>("sources");
  const healthChecks = adminHealthChecks(adminData);

  return (
    <section className="panel admin-page">
      <div className="section-title">
        <div>
          <h2>Admin Console</h2>
          <p>Import opportunity sources, monitor background jobs, and review operational health from one controlled workspace.</p>
        </div>
      </div>

      <div className="tabs admin-tabs">
        {adminTabs.map((tab) => (
          <button key={tab} className={activeTab === tab ? "active" : ""} type="button" onClick={() => setActiveTab(tab)}>
            {adminTabLabel(tab)}
          </button>
        ))}
      </div>

      {activeTab === "sources" && (
        <div className="admin-tab-panel">
          <div className="admin-help-grid">
            <article>
              <strong>Structured EU imports</strong>
              <p>Use EU Funding & Tenders for Horizon, MSCA, Erasmus+ organisation calls, and other official Commission funding records.</p>
            </article>
            <article>
              <strong>External imports</strong>
              <p>Use RSS, JSON, or HTML only when a provider has concrete opportunity pages. Avoid generic landing pages.</p>
            </article>
            <article>
              <strong>Quality check</strong>
              <p>Imported records are deduplicated by URL. For richer fields, review the imported cards and update metadata where needed.</p>
            </article>
          </div>

          <div className="source-presets">
            {euFundingPresets.map((preset) => (
              <button
                key={preset.source_name}
                type="button"
                onClick={() =>
                  onEuFundingFormChange({
                    ...euFundingForm,
                    source_name: preset.source_name,
                    programme: preset.programme,
                    keyword: preset.keyword,
                  })
                }
              >
                <strong>{preset.label}</strong>
                <span>EU Funding & Tenders API</span>
              </button>
            ))}
          </div>

          <form className="grid-form admin-form" onSubmit={onRunEuFundingTenders}>
            <div className="span-2">
              <h3>EU Funding & Tenders</h3>
              <p className="muted">Imports concrete calls from the Commission SEDIA search API. This is preferred over scraping Erasmus or Horizon landing pages.</p>
            </div>
            <Field labelText="Keyword" value={euFundingForm.keyword} onChange={(keyword) => onEuFundingFormChange({ ...euFundingForm, keyword })} />
            <SelectField
              labelText="Save as source"
              value={euFundingForm.source_name}
              options={["eu_funding_tenders", "horizon_europe", "erasmus", "msca"]}
              onChange={(source_name) => onEuFundingFormChange({ ...euFundingForm, source_name })}
            />
            <Field labelText="Programme hint" value={euFundingForm.programme} onChange={(programme) => onEuFundingFormChange({ ...euFundingForm, programme })} />
            <Field labelText="Limit" type="number" value={String(euFundingForm.limit)} onChange={(limit) => onEuFundingFormChange({ ...euFundingForm, limit: Number(limit) })} />
            <div className="admin-form-actions span-2">
              <label className="toggle filter-toggle">
                <input
                  type="checkbox"
                  checked={euFundingForm.import_results}
                  onChange={(event) => onEuFundingFormChange({ ...euFundingForm, import_results: event.target.checked })}
                />
                <span>Import results</span>
              </label>
              <ActionButton busy={adminBusy === "eu-funding"}>Import EU calls</ActionButton>
            </div>
          </form>

          <div className="source-presets">
            {sourcePresets.map((preset) => (
              <button
                key={preset.source_name}
                type="button"
                onClick={() =>
                  onExternalFormChange({
                    ...externalForm,
                    source_name: preset.source_name,
                    source_url: preset.source_url,
                    source_kind: preset.source_kind,
                    default_opportunity_type: preset.default_opportunity_type,
                    default_country: preset.default_country,
                    default_career_stage: preset.default_career_stage,
                    default_discipline: preset.default_discipline,
                    keyword: preset.keyword,
                  })
                }
              >
                <strong>{preset.label}</strong>
                <span>{preset.group} · {preset.source_name}</span>
              </button>
            ))}
          </div>

          <form className="grid-form admin-form" onSubmit={onRunExternalImport}>
            <Field
              labelText="Source name"
              value={externalForm.source_name}
              list="external-source-options"
              onChange={(source_name) => onExternalFormChange({ ...externalForm, source_name })}
            />
            <datalist id="external-source-options">
              {supportedExternalSources.map((source) => (
                <option value={source} key={source} />
              ))}
            </datalist>
            <Field
              labelText="Feed or page URL"
              value={externalForm.source_url}
              placeholder="https://houseofeurope.org.ua/en/opportunities"
              onChange={(source_url) => onExternalFormChange({ ...externalForm, source_url })}
            />
            <SelectField labelText="Kind" value={externalForm.source_kind} options={["rss", "json", "html"]} onChange={(source_kind) => onExternalFormChange({ ...externalForm, source_kind })} />
            <SelectField labelText="Default type" value={externalForm.default_opportunity_type} options={opportunityTypes} onChange={(default_opportunity_type) => onExternalFormChange({ ...externalForm, default_opportunity_type })} />
            <Field labelText="Limit" type="number" value={String(externalForm.limit)} onChange={(limit) => onExternalFormChange({ ...externalForm, limit: Number(limit) })} />
            <Field labelText="Default country" value={externalForm.default_country} onChange={(default_country) => onExternalFormChange({ ...externalForm, default_country })} />
            <Field labelText="Default career stage" value={externalForm.default_career_stage} onChange={(default_career_stage) => onExternalFormChange({ ...externalForm, default_career_stage })} />
            <Field labelText="Default discipline" value={externalForm.default_discipline} onChange={(default_discipline) => onExternalFormChange({ ...externalForm, default_discipline })} />
            <Field labelText="Keyword tag" value={externalForm.keyword} onChange={(keyword) => onExternalFormChange({ ...externalForm, keyword })} />
            <div className="admin-form-actions">
              <label className="toggle filter-toggle">
                <input
                  type="checkbox"
                  checked={externalForm.import_results}
                  onChange={(event) => onExternalFormChange({ ...externalForm, import_results: event.target.checked })}
                />
                <span>Import results</span>
              </label>
              <ActionButton busy={adminBusy === "external"}>Import external source</ActionButton>
            </div>
          </form>

          <form className="grid-form admin-form separated" onSubmit={onEnqueueGrantsGov}>
            <div className="span-2">
              <h3>Grants.gov</h3>
              <p className="muted">Queue or run a US Grants.gov keyword search. Use queued mode when Redis/RQ workers are running.</p>
            </div>
            <Field labelText="Keyword" value={grantsForm.keyword} onChange={(keyword) => onGrantsFormChange({ ...grantsForm, keyword })} />
            <Field labelText="Limit" type="number" value={String(grantsForm.limit)} onChange={(limit) => onGrantsFormChange({ ...grantsForm, limit: Number(limit) })} />
            <div className="admin-form-actions span-2">
              <label className="toggle filter-toggle">
                <input
                  type="checkbox"
                  checked={grantsForm.import_results}
                  onChange={(event) => onGrantsFormChange({ ...grantsForm, import_results: event.target.checked })}
                />
                <span>Import results</span>
              </label>
              <ActionButton busy={adminBusy === "grants-queue"}>Queue search</ActionButton>
              <button className="secondary" type="button" onClick={onRunGrantsGovNow}>
                {adminBusy === "grants-now" ? <span className="spinner" aria-hidden="true" /> : null}
                {adminBusy === "grants-now" ? "Working..." : "Run now"}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === "curated" && (
        <form className="grid-form admin-form" onSubmit={onRunBulkImport}>
          <div className="span-2">
            <h3>Curated JSON Import</h3>
            <p className="muted">Use this when a provider has no usable feed or when you manually prepared opportunity records.</p>
          </div>
          <Field labelText="Source" value={importForm.source} onChange={(source) => onImportFormChange({ ...importForm, source })} />
          <label className="toggle filter-toggle">
            <input type="checkbox" checked={importForm.dry_run} onChange={(event) => onImportFormChange({ ...importForm, dry_run: event.target.checked })} />
            <span>Dry run</span>
          </label>
          <JsonTextArea labelText="Curated opportunities JSON" value={importForm.payload} onChange={(payload) => onImportFormChange({ ...importForm, payload })} />
          <ActionButton busy={adminBusy === "curated"} className="span-2">Import curated list</ActionButton>
        </form>
      )}

      {activeTab === "jobs" && (
        <div className="admin-tab-panel">
          <div className="section-title">
            <div>
              <h3>Background Jobs</h3>
              <p>Queue health, failed-job visibility, reminder scans, digests, alerts, and embedding refreshes use Redis + RQ.</p>
            </div>
            <ActionButton variant="secondary" type="button" busy={adminBusy === "queues"} onClick={onLoadQueues}>Load queues</ActionButton>
          </div>
          <div className="job-actions">
            <ActionButton variant="secondary" type="button" busy={adminBusy === "reminder-scan"} onClick={onEnqueueReminderScan}>Queue reminder scan</ActionButton>
            <ActionButton variant="secondary" type="button" busy={adminBusy === "digest"} onClick={onEnqueueWeeklyDigest}>Queue digest</ActionButton>
            <ActionButton variant="secondary" type="button" busy={adminBusy === "alerts"} onClick={onEnqueueHighMatchAlerts}>Queue alerts</ActionButton>
            <ActionButton variant="secondary" type="button" busy={adminBusy === "embeddings"} onClick={onEnqueueEmbeddingRefresh}>Queue embedding backfill</ActionButton>
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
            <ActionButton busy={adminBusy === "job-detail"} className="span-2">Load job</ActionButton>
          </form>
          {jobDetail && <pre className="job-detail">{JSON.stringify(jobDetail, null, 2)}</pre>}
        </div>
      )}

      {activeTab === "operations" && (
        <div className="admin-tab-panel">
          <div className="section-title">
            <div>
              <h3>Operations</h3>
              <p>Source health, recent batches, duplicate groups, analytics, and audit visibility.</p>
            </div>
            <ActionButton variant="secondary" type="button" busy={adminBusy === "operations"} onClick={onLoadAdminOps}>Load operations</ActionButton>
          </div>
          {healthChecks.length > 0 && (
            <div className="health-grid">
              {healthChecks.map((check) => (
                <article className={`health-card health-${check.status}`} key={check.name}>
                  <div>
                    <strong>{check.name}</strong>
                    <span>{check.status}</span>
                  </div>
                  <p>{check.detail}</p>
                  {typeof check.latency_ms === "number" && <small>{check.latency_ms} ms</small>}
                </article>
              ))}
            </div>
          )}
          <div className="admin-output-grid">
            {adminData && <pre className="job-detail">{JSON.stringify(adminData, null, 2)}</pre>}
            {duplicateGroups.length > 0 && <pre className="job-detail">{JSON.stringify(duplicateGroups, null, 2)}</pre>}
            {auditLog.length > 0 && <pre className="job-detail">{JSON.stringify(auditLog, null, 2)}</pre>}
          </div>
        </div>
      )}
    </section>
  );
}

function adminTabLabel(tab: AdminTab): string {
  const labels: Record<AdminTab, string> = {
    sources: "Source Imports",
    curated: "Curated JSON",
    jobs: "Jobs",
    operations: "Operations",
  };
  return labels[tab];
}

type HealthCheck = { name: string; status: string; detail: string; latency_ms?: number | null };

function adminHealthChecks(adminData: Record<string, unknown> | null): HealthCheck[] {
  const health = adminData?.health;
  if (!Array.isArray(health)) return [];
  return health.filter(isHealthCheck);
}

function isHealthCheck(value: unknown): value is HealthCheck {
  return (
    typeof value === "object" &&
    value !== null &&
    "name" in value &&
    "status" in value &&
    "detail" in value &&
    typeof (value as HealthCheck).name === "string" &&
    typeof (value as HealthCheck).status === "string" &&
    typeof (value as HealthCheck).detail === "string"
  );
}

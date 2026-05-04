import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, type OpportunityPayload, type ProfileDetailsPayload, type ProfilePayload } from "./api";
import type {
  ApplicationAssistantResult,
  CareerStage,
  NotificationItem,
  NotificationPreference,
  Opportunity,
  OpportunityStatus,
  OpportunityType,
  Profile,
  Recommendation,
  Reminder,
  StatusRecord,
  User,
} from "./types";

const careerStages: CareerStage[] = ["bachelor", "master", "phd", "postdoc", "early_career", "senior"];
const opportunityTypes: OpportunityType[] = ["grant", "exchange", "fellowship", "internship", "research_position", "training"];
const trackedStatuses: OpportunityStatus[] = ["saved", "planned", "applied", "accepted", "rejected", "ignored"];

type View = "feed" | "profile" | "orcid" | "board" | "reminders" | "notifications" | "assistant" | "admin";

const blankProfile: ProfilePayload = {
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

const blankDetails: ProfileDetailsPayload = {
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

const blankOpportunity: OpportunityPayload = {
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

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(value: string[] | undefined): string {
  return (value ?? []).join(", ");
}

function label(value: string): string {
  return value.replaceAll("_", " ");
}

function normalizeUrl(value: string | null): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed === "" ? null : trimmed;
}

function normalizeText(value: string | null): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed === "" ? null : trimmed;
}

function Field({
  labelText,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="field">
      <span>{labelText}</span>
      <input type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function TextArea({
  labelText,
  value,
  onChange,
  placeholder,
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="field span-2">
      <span>{labelText}</span>
      <textarea value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} rows={4} />
    </label>
  );
}

function SelectField<T extends string>({
  labelText,
  value,
  options,
  onChange,
}: {
  labelText: string;
  value: T;
  options: T[];
  onChange: (value: T) => void;
}) {
  return (
    <label className="field">
      <span>{labelText}</span>
      <select value={value} onChange={(event) => onChange(event.target.value as T)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {label(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("rom_token"));
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authForm, setAuthForm] = useState({ email: "", password: "", full_name: "" });
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [view, setView] = useState<View>("feed");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [profileForm, setProfileForm] = useState<ProfilePayload>(blankProfile);
  const [detailsForm, setDetailsForm] = useState<ProfileDetailsPayload>(blankDetails);
  const [orcidForm, setOrcidForm] = useState({
    orcid_id: "",
    email: "",
    career_stage: "phd" as CareerStage,
    disciplines: "",
    preferred_countries: "",
  });
  const [openAlexForm, setOpenAlexForm] = useState({ openalex_author_id: "", orcid_id: "", max_works: 10 });
  const [filters, setFilters] = useState({
    keyword: "",
    opportunity_type: "",
    country: "",
    career_stage: "",
    source: "",
    active_only: true,
    min_score: 0,
    include_ignored: false,
  });
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [statuses, setStatuses] = useState<StatusRecord[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationPrefs, setNotificationPrefs] = useState<NotificationPreference>({
    email_enabled: true,
    deadline_reminders_enabled: true,
    weekly_digest_enabled: true,
    high_match_alerts_enabled: true,
    min_alert_score: 80,
  });
  const [adminData, setAdminData] = useState<Record<string, unknown> | null>(null);
  const [auditLog, setAuditLog] = useState<Record<string, unknown>[]>([]);
  const [duplicateGroups, setDuplicateGroups] = useState<Record<string, unknown>[]>([]);
  const [assistantForm, setAssistantForm] = useState({ opportunity_id: "" });
  const [assistantResult, setAssistantResult] = useState<ApplicationAssistantResult | null>(null);
  const [reminderForm, setReminderForm] = useState({ opportunity_id: "", remind_on: "", message: "" });
  const [importForm, setImportForm] = useState({ source: "curated", dry_run: true, payload: JSON.stringify([blankOpportunity], null, 2) });
  const [grantsForm, setGrantsForm] = useState({ keyword: "", limit: 10, import_results: true });
  const [externalForm, setExternalForm] = useState({
    source_name: "euraxess",
    source_url: "",
    source_kind: "rss" as "rss" | "json",
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

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === activeProfileId) ?? profiles[0] ?? null,
    [activeProfileId, profiles],
  );

  async function loadSession(nextToken = token) {
    if (!nextToken) return;
    setLoading(true);
    setError("");
    try {
      const [me, ownedProfiles] = await Promise.all([api.me(nextToken), api.profiles(nextToken)]);
      setUser(me);
      setProfiles(ownedProfiles);
      const chosen = ownedProfiles.find((profile) => profile.id === activeProfileId) ?? ownedProfiles[0] ?? null;
      setActiveProfileId(chosen?.id ?? null);
      if (chosen) {
        setProfileForm({
          full_name: chosen.full_name,
          email: chosen.email,
          career_stage: chosen.career_stage,
          country: chosen.country,
          disciplines: chosen.disciplines,
          keywords: chosen.keywords,
          preferred_countries: chosen.preferred_countries,
          orcid_id: chosen.orcid_id,
          google_scholar_url: chosen.google_scholar_url,
          linkedin_url: chosen.linkedin_url,
        });
      }
    } catch (sessionError) {
      setError((sessionError as Error).message);
      logout();
    } finally {
      setLoading(false);
    }
  }

  async function refreshWorkspace(profile = activeProfile) {
    setError("");
    try {
      const opportunityQuery = {
        keyword: filters.keyword,
        opportunity_type: filters.opportunity_type,
        country: filters.country,
        career_stage: filters.career_stage,
        source: filters.source,
        active_only: filters.active_only,
        limit: 100,
      };
      const catalogPromise = api.opportunities(opportunityQuery);
      if (token && profile) {
        const [nextRecommendations, nextStatuses, nextReminders, nextOpportunities] = await Promise.all([
          api.recommendations(token, profile.id, {
            min_score: filters.min_score,
            include_ignored: filters.include_ignored,
          }),
          api.statuses(token, profile.id),
          api.reminders(token, profile.id, true),
          catalogPromise,
        ]);
        setRecommendations(nextRecommendations);
        setStatuses(nextStatuses);
        setReminders(nextReminders);
        setOpportunities(nextOpportunities);
      } else {
        setOpportunities(await catalogPromise);
      }
    } catch (workspaceError) {
      setError((workspaceError as Error).message);
    }
  }

  useEffect(() => {
    void loadSession();
  }, []);

  useEffect(() => {
    if (token) {
      void refreshWorkspace(activeProfile);
    }
  }, [token, activeProfileId]);

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response =
        authMode === "register"
          ? await api.register(authForm)
          : await api.login({ email: authForm.email, password: authForm.password });
      localStorage.setItem("rom_token", response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      setNotice(`Signed in as ${response.user.email}`);
      await loadSession(response.access_token);
    } catch (authError) {
      setError((authError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("rom_token");
    setToken(null);
    setUser(null);
    setProfiles([]);
    setActiveProfileId(null);
    setRecommendations([]);
    setStatuses([]);
    setReminders([]);
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const profile = await api.createProfile(token, {
        ...profileForm,
        email: normalizeText(profileForm.email),
        country: normalizeText(profileForm.country),
        orcid_id: normalizeText(profileForm.orcid_id),
        google_scholar_url: normalizeUrl(profileForm.google_scholar_url),
        linkedin_url: normalizeUrl(profileForm.linkedin_url),
      });
      setNotice("Profile created");
      setActiveProfileId(profile.id);
      await loadSession(token);
    } catch (profileError) {
      setError((profileError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails() {
    if (!token || !activeProfile) return;
    setError("");
    try {
      const details = await api.getProfileDetails(token, activeProfile.id);
      setDetailsForm({
        research_summary: details.research_summary,
        publications: details.publications,
        degrees: details.degrees,
        languages: details.languages,
        funding_interests: details.funding_interests,
        unavailable_countries: details.unavailable_countries,
        preferred_opportunity_types: details.preferred_opportunity_types,
        min_duration_months: details.min_duration_months,
        max_duration_months: details.max_duration_months,
      });
    } catch {
      setDetailsForm(blankDetails);
    }
  }

  async function saveDetails(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setLoading(true);
    setError("");
    try {
      await api.saveProfileDetails(token, activeProfile.id, detailsForm);
      setNotice("Profile details saved");
      await refreshWorkspace(activeProfile);
    } catch (detailsError) {
      setError((detailsError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function importOrcid(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.importOrcid(token, {
        orcid_id: orcidForm.orcid_id,
        email: normalizeText(orcidForm.email),
        career_stage: orcidForm.career_stage,
        disciplines: splitList(orcidForm.disciplines),
        preferred_countries: splitList(orcidForm.preferred_countries),
      });
      setNotice(result.imported ? "ORCID profile imported" : "ORCID profile enriched");
      setActiveProfileId(result.profile.id);
      await loadSession(token);
    } catch (orcidError) {
      setError((orcidError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function importOpenAlex(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setLoading(true);
    setError("");
    try {
      await api.importOpenAlex(token, {
        profile_id: activeProfile.id,
        openalex_author_id: normalizeText(openAlexForm.openalex_author_id),
        orcid_id: normalizeText(openAlexForm.orcid_id) ?? activeProfile.orcid_id,
        max_works: openAlexForm.max_works,
      });
      setNotice("OpenAlex profile data imported");
      await loadSession(token);
      await loadDetails();
      await refreshWorkspace(activeProfile);
    } catch (openAlexError) {
      setError((openAlexError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(opportunityId: number, status: OpportunityStatus) {
    if (!token || !activeProfile) return;
    setError("");
    try {
      await api.setStatus(token, activeProfile.id, opportunityId, status);
      setNotice(`Marked as ${label(status)}`);
      await refreshWorkspace(activeProfile);
    } catch (statusError) {
      setError((statusError as Error).message);
    }
  }

  async function createReminder(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setError("");
    try {
      await api.createReminder(token, activeProfile.id, {
        opportunity_id: Number(reminderForm.opportunity_id),
        remind_on: reminderForm.remind_on,
        message: reminderForm.message,
      });
      setReminderForm({ opportunity_id: "", remind_on: "", message: "" });
      setNotice("Reminder created");
      await refreshWorkspace(activeProfile);
    } catch (reminderError) {
      setError((reminderError as Error).message);
    }
  }

  async function completeReminder(reminderId: number) {
    if (!token || !activeProfile) return;
    setError("");
    try {
      await api.completeReminder(token, activeProfile.id, reminderId);
      setNotice("Reminder completed");
      await refreshWorkspace(activeProfile);
    } catch (reminderError) {
      setError((reminderError as Error).message);
    }
  }

  async function loadNotifications() {
    if (!token) return;
    setError("");
    try {
      const [items, prefs] = await Promise.all([api.notifications(token, true), api.notificationPreferences(token)]);
      setNotifications(items);
      setNotificationPrefs(prefs);
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function saveNotificationPrefs(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    try {
      setNotificationPrefs(await api.saveNotificationPreferences(token, notificationPrefs));
      setNotice("Notification preferences saved");
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function markRead(notificationId: number) {
    if (!token) return;
    setError("");
    try {
      await api.markNotificationRead(token, notificationId);
      await loadNotifications();
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function unsubscribe() {
    if (!token) return;
    setError("");
    try {
      setNotificationPrefs(await api.unsubscribeNotifications(token));
      setNotice("Email notifications disabled");
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function loadAdminOps() {
    setError("");
    try {
      const [dashboard, audit, duplicates] = await Promise.all([api.adminDashboard(), api.adminAuditLog(), api.adminDuplicates()]);
      setAdminData(dashboard);
      setAuditLog(audit);
      setDuplicateGroups(duplicates);
    } catch (adminError) {
      setError((adminError as Error).message);
    }
  }

  async function generateApplicationNotes(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setError("");
    try {
      const opportunityId = Number(assistantForm.opportunity_id);
      setAssistantResult(await api.applicationAssistant(token, { profile_id: activeProfile.id, opportunity_id: opportunityId }));
    } catch (assistantError) {
      setError((assistantError as Error).message);
    }
  }

  async function runBulkImport(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const opportunities = JSON.parse(importForm.payload) as OpportunityPayload[];
      const result = await api.bulkImport({ source: importForm.source, dry_run: importForm.dry_run, opportunities });
      setNotice(
        `${result.dry_run ? "Validated" : "Imported"} ${result.imported_count} new, ${result.updated_count} updated, ${result.skipped_count} skipped`,
      );
      await refreshWorkspace(activeProfile);
    } catch (importError) {
      setError((importError as Error).message);
    }
  }

  async function runExternalImport(event: FormEvent) {
    event.preventDefault();
    setError("");
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
    }
  }

  async function runGrantsGov(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await api.grantsGov(grantsForm);
      setNotice(`${result.source}: ${result.imported_count} imported, ${result.skipped_count} skipped`);
      await refreshWorkspace(activeProfile);
    } catch (importError) {
      setError((importError as Error).message);
    }
  }

  async function enqueueGrantsGov(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await api.enqueueGrantsGov(grantsForm);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued Grants.gov job ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function enqueueReminderScan() {
    setError("");
    try {
      const result = await api.enqueueReminderScan();
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued reminder scan ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function enqueueEmbeddingRefresh() {
    setError("");
    try {
      const result = await api.enqueueEmbeddingRefresh();
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued embedding refresh ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function loadQueues() {
    setError("");
    try {
      setQueueStats(await api.queues());
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function loadJob(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      setJobDetail(await api.job(jobForm.job_id, jobForm.queue_name));
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  const statusByOpportunity = useMemo(
    () => new Map(statuses.map((status) => [status.opportunity_id, status])),
    [statuses],
  );

  const opportunitiesById = useMemo(
    () => new Map([...opportunities, ...recommendations.map((item) => item.opportunity)].map((item) => [item.id, item])),
    [opportunities, recommendations],
  );

  if (!token || !user) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div>
            <p className="eyebrow">Research Opportunity Matcher</p>
            <h1>{authMode === "login" ? "Welcome back" : "Create your research account"}</h1>
            <p className="muted">Discover, rank, save, and plan academic opportunities from one focused workspace.</p>
          </div>
          <form className="grid-form" onSubmit={submitAuth}>
            {authMode === "register" && (
              <Field labelText="Full name" value={authForm.full_name} onChange={(full_name) => setAuthForm({ ...authForm, full_name })} />
            )}
            <Field labelText="Email" type="email" value={authForm.email} onChange={(email) => setAuthForm({ ...authForm, email })} />
            <Field labelText="Password" type="password" value={authForm.password} onChange={(password) => setAuthForm({ ...authForm, password })} />
            {error && <div className="alert error span-2">{error}</div>}
            <button className="primary span-2" disabled={loading}>
              {loading ? "Working..." : authMode === "login" ? "Sign in" : "Sign up"}
            </button>
          </form>
          <button className="ghost" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
            {authMode === "login" ? "Need an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark">ROM</span>
          <div>
            <strong>Research Matcher</strong>
            <small>{api.baseUrl}</small>
          </div>
        </div>
        <nav>
          {(["feed", "profile", "orcid", "board", "reminders", "notifications", "assistant", "admin"] as View[]).map((item) => (
            <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
              {label(item)}
            </button>
          ))}
        </nav>
        <div className="profile-switcher">
          <span>Active profile</span>
          <select value={activeProfile?.id ?? ""} onChange={(event) => setActiveProfileId(Number(event.target.value))}>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.full_name}
              </option>
            ))}
          </select>
        </div>
        <button className="ghost" onClick={logout}>
          Sign out
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{user.role}</p>
            <h1>{activeProfile ? activeProfile.full_name : "Create your first profile"}</h1>
          </div>
          <button className="secondary" onClick={() => void refreshWorkspace(activeProfile)}>
            Refresh
          </button>
        </header>

        {notice && <div className="alert success">{notice}</div>}
        {error && <div className="alert error">{error}</div>}

        {view === "feed" && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Opportunity Feed</h2>
                <p>Recommended matches appear first when a profile is selected.</p>
              </div>
            </div>
            <div className="filters">
              <Field labelText="Keyword" value={filters.keyword} onChange={(keyword) => setFilters({ ...filters, keyword })} />
              <SelectField
                labelText="Type"
                value={(filters.opportunity_type || "") as OpportunityType | ""}
                options={["", ...opportunityTypes] as (OpportunityType | "")[]}
                onChange={(opportunity_type) => setFilters({ ...filters, opportunity_type })}
              />
              <Field labelText="Country" value={filters.country} onChange={(country) => setFilters({ ...filters, country })} />
              <Field labelText="Source" value={filters.source} onChange={(source) => setFilters({ ...filters, source })} />
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={filters.active_only}
                  onChange={(event) => setFilters({ ...filters, active_only: event.target.checked })}
                />
                Active only
              </label>
              <button className="secondary" onClick={() => void refreshWorkspace(activeProfile)}>
                Apply filters
              </button>
            </div>
            <div className="cards">
              {(activeProfile ? recommendations : opportunities.map((opportunity) => ({ opportunity, match_score: 0, semantic_score: 0, score_breakdown: { semantic: 0, eligibility: 0, deadline: 0, user_history: 0, final: 0 }, reasons: [], user_status: null }))).map(
                (item) => (
                  <OpportunityCard
                    key={item.opportunity.id}
                    item={item}
                    onSelect={() => setSelectedOpportunity(item.opportunity)}
                    onStatus={(status) => void updateStatus(item.opportunity.id, status)}
                  />
                ),
              )}
              {activeProfile && recommendations.length === 0 && (
                <EmptyState title="No recommendations yet" detail="Create a profile, import opportunities, or loosen filters to populate this feed." />
              )}
            </div>
          </section>
        )}

        {view === "profile" && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Profile Wizard and Editor</h2>
                <p>Create the profile used by recommendations, then enrich matching preferences.</p>
              </div>
              <button className="secondary" onClick={() => void loadDetails()}>
                Load details
              </button>
            </div>
            <form className="grid-form" onSubmit={saveProfile}>
              <Field labelText="Full name" value={profileForm.full_name} onChange={(full_name) => setProfileForm({ ...profileForm, full_name })} />
              <Field labelText="Email" value={profileForm.email ?? ""} onChange={(email) => setProfileForm({ ...profileForm, email })} />
              <SelectField labelText="Career stage" value={profileForm.career_stage} options={careerStages} onChange={(career_stage) => setProfileForm({ ...profileForm, career_stage })} />
              <Field labelText="Country" value={profileForm.country ?? ""} onChange={(country) => setProfileForm({ ...profileForm, country })} />
              <Field labelText="Disciplines" value={joinList(profileForm.disciplines)} onChange={(value) => setProfileForm({ ...profileForm, disciplines: splitList(value) })} />
              <Field labelText="Keywords" value={joinList(profileForm.keywords)} onChange={(value) => setProfileForm({ ...profileForm, keywords: splitList(value) })} />
              <Field labelText="Preferred countries" value={joinList(profileForm.preferred_countries)} onChange={(value) => setProfileForm({ ...profileForm, preferred_countries: splitList(value) })} />
              <Field labelText="ORCID" value={profileForm.orcid_id ?? ""} onChange={(orcid_id) => setProfileForm({ ...profileForm, orcid_id })} />
              <Field labelText="Google Scholar URL" value={profileForm.google_scholar_url ?? ""} onChange={(google_scholar_url) => setProfileForm({ ...profileForm, google_scholar_url })} />
              <Field labelText="LinkedIn URL" value={profileForm.linkedin_url ?? ""} onChange={(linkedin_url) => setProfileForm({ ...profileForm, linkedin_url })} />
              <button className="primary span-2">Create profile</button>
            </form>
            <form className="grid-form separated" onSubmit={saveDetails}>
              <TextArea labelText="Research summary" value={detailsForm.research_summary} onChange={(research_summary) => setDetailsForm({ ...detailsForm, research_summary })} />
              <Field labelText="Publications" value={joinList(detailsForm.publications)} onChange={(value) => setDetailsForm({ ...detailsForm, publications: splitList(value) })} />
              <Field labelText="Degrees" value={joinList(detailsForm.degrees)} onChange={(value) => setDetailsForm({ ...detailsForm, degrees: splitList(value) })} />
              <Field labelText="Languages" value={joinList(detailsForm.languages)} onChange={(value) => setDetailsForm({ ...detailsForm, languages: splitList(value) })} />
              <Field labelText="Funding interests" value={joinList(detailsForm.funding_interests)} onChange={(value) => setDetailsForm({ ...detailsForm, funding_interests: splitList(value) })} />
              <Field labelText="Unavailable countries" value={joinList(detailsForm.unavailable_countries)} onChange={(value) => setDetailsForm({ ...detailsForm, unavailable_countries: splitList(value) })} />
              <Field
                labelText="Preferred types"
                value={joinList(detailsForm.preferred_opportunity_types)}
                onChange={(value) => setDetailsForm({ ...detailsForm, preferred_opportunity_types: splitList(value) as OpportunityType[] })}
              />
              <button className="primary span-2">Save details</button>
            </form>
          </section>
        )}

        {view === "orcid" && (
          <section className="panel">
            <h2>ORCID Import</h2>
            <form className="grid-form" onSubmit={importOrcid}>
              <Field labelText="ORCID iD" value={orcidForm.orcid_id} onChange={(orcid_id) => setOrcidForm({ ...orcidForm, orcid_id })} placeholder="0000-0000-0000-0000" />
              <Field labelText="Email" value={orcidForm.email} onChange={(email) => setOrcidForm({ ...orcidForm, email })} />
              <SelectField labelText="Career stage" value={orcidForm.career_stage} options={careerStages} onChange={(career_stage) => setOrcidForm({ ...orcidForm, career_stage })} />
              <Field labelText="Disciplines" value={orcidForm.disciplines} onChange={(disciplines) => setOrcidForm({ ...orcidForm, disciplines })} />
              <Field labelText="Preferred countries" value={orcidForm.preferred_countries} onChange={(preferred_countries) => setOrcidForm({ ...orcidForm, preferred_countries })} />
              <button className="primary span-2">Import public profile</button>
            </form>
            <form className="grid-form separated" onSubmit={importOpenAlex}>
              <div className="span-2">
                <h2>OpenAlex Enrichment</h2>
                <p className="muted">Merge public concepts and publication titles into the active profile.</p>
              </div>
              <Field labelText="OpenAlex author id" value={openAlexForm.openalex_author_id} onChange={(openalex_author_id) => setOpenAlexForm({ ...openAlexForm, openalex_author_id })} placeholder="A1234567890" />
              <Field labelText="ORCID override" value={openAlexForm.orcid_id} onChange={(orcid_id) => setOpenAlexForm({ ...openAlexForm, orcid_id })} />
              <Field labelText="Max works" type="number" value={String(openAlexForm.max_works)} onChange={(max_works) => setOpenAlexForm({ ...openAlexForm, max_works: Number(max_works) })} />
              <button className="primary">Import OpenAlex</button>
            </form>
          </section>
        )}

        {view === "board" && (
          <section className="board">
            {trackedStatuses.map((status) => (
              <div className="lane" key={status}>
                <h2>{label(status)}</h2>
                {statuses
                  .filter((record) => record.status === status)
                  .map((record) => opportunitiesById.get(record.opportunity_id))
                  .filter(Boolean)
                  .map((opportunity) => (
                    <article className="mini-card" key={opportunity!.id} onClick={() => setSelectedOpportunity(opportunity!)}>
                      <strong>{opportunity!.title}</strong>
                      <small>{opportunity!.deadline ?? "No deadline"}</small>
                    </article>
                  ))}
              </div>
            ))}
          </section>
        )}

        {view === "reminders" && (
          <section className="panel">
            <h2>Reminders</h2>
            <form className="grid-form" onSubmit={createReminder}>
              <label className="field">
                <span>Opportunity</span>
                <select value={reminderForm.opportunity_id} onChange={(event) => setReminderForm({ ...reminderForm, opportunity_id: event.target.value })}>
                  <option value="">Select an opportunity</option>
                  {[...opportunitiesById.values()].map((opportunity) => (
                    <option value={opportunity.id} key={opportunity.id}>
                      {opportunity.title}
                    </option>
                  ))}
                </select>
              </label>
              <Field labelText="Remind on" type="date" value={reminderForm.remind_on} onChange={(remind_on) => setReminderForm({ ...reminderForm, remind_on })} />
              <Field labelText="Message" value={reminderForm.message} onChange={(message) => setReminderForm({ ...reminderForm, message })} />
              <button className="primary">Create reminder</button>
            </form>
            <div className="table">
              {reminders.map((reminder) => (
                <div className="table-row" key={reminder.id}>
                  <span>{opportunitiesById.get(reminder.opportunity_id)?.title ?? `Opportunity ${reminder.opportunity_id}`}</span>
                  <span>{reminder.remind_on}</span>
                  <span>{label(reminder.status)}</span>
                  {reminder.status === "pending" && (
                    <button className="secondary" onClick={() => void completeReminder(reminder.id)}>
                      Complete
                    </button>
                  )}
                </div>
              ))}
              {reminders.length === 0 && <EmptyState title="No reminders" detail="Saved, planned, and applied opportunities can generate deadline reminders automatically." />}
            </div>
          </section>
        )}

        {view === "notifications" && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Notifications</h2>
                <p>Review reminder history and tune proactive alerts.</p>
              </div>
              <button className="secondary" onClick={() => void loadNotifications()}>
                Load notifications
              </button>
            </div>
            <form className="grid-form" onSubmit={saveNotificationPrefs}>
              <label className="toggle">
                <input type="checkbox" checked={notificationPrefs.email_enabled} onChange={(event) => setNotificationPrefs({ ...notificationPrefs, email_enabled: event.target.checked })} />
                Email enabled
              </label>
              <label className="toggle">
                <input type="checkbox" checked={notificationPrefs.deadline_reminders_enabled} onChange={(event) => setNotificationPrefs({ ...notificationPrefs, deadline_reminders_enabled: event.target.checked })} />
                Deadline reminders
              </label>
              <label className="toggle">
                <input type="checkbox" checked={notificationPrefs.weekly_digest_enabled} onChange={(event) => setNotificationPrefs({ ...notificationPrefs, weekly_digest_enabled: event.target.checked })} />
                Weekly digest
              </label>
              <label className="toggle">
                <input type="checkbox" checked={notificationPrefs.high_match_alerts_enabled} onChange={(event) => setNotificationPrefs({ ...notificationPrefs, high_match_alerts_enabled: event.target.checked })} />
                High-match alerts
              </label>
              <Field labelText="Minimum alert score" type="number" value={String(notificationPrefs.min_alert_score)} onChange={(min_alert_score) => setNotificationPrefs({ ...notificationPrefs, min_alert_score: Number(min_alert_score) })} />
              <div className="actions">
                <button className="primary">Save preferences</button>
                <button className="secondary" type="button" onClick={() => void unsubscribe()}>
                  Unsubscribe
                </button>
              </div>
            </form>
            <div className="table">
              {notifications.map((item) => (
                <div className="table-row" key={item.id}>
                  <span>{item.subject}</span>
                  <span>{label(item.notification_type)}</span>
                  <span>{label(item.status)}</span>
                  {item.status !== "read" && (
                    <button className="secondary" onClick={() => void markRead(item.id)}>
                      Read
                    </button>
                  )}
                </div>
              ))}
              {notifications.length === 0 && <EmptyState title="No notifications yet" detail="Deadline reminders, digests, and alerts will appear here once generated." />}
            </div>
          </section>
        )}

        {view === "assistant" && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Application Assistant</h2>
                <p>Generate a checklist, motivation outline, fit statement, eligibility warnings, and exportable notes.</p>
              </div>
            </div>
            <form className="grid-form" onSubmit={generateApplicationNotes}>
              <label className="field span-2">
                <span>Opportunity</span>
                <select value={assistantForm.opportunity_id} onChange={(event) => setAssistantForm({ opportunity_id: event.target.value })}>
                  <option value="">Select an opportunity</option>
                  {[...opportunitiesById.values()].map((opportunity) => (
                    <option value={opportunity.id} key={opportunity.id}>
                      {opportunity.title}
                    </option>
                  ))}
                </select>
              </label>
              <button className="primary span-2">Generate notes</button>
            </form>
            {assistantResult && (
              <div className="assistant-grid separated">
                <section>
                  <h3>Checklist</h3>
                  <ul>{assistantResult.application_checklist.map((item) => <li key={item}>{item}</li>)}</ul>
                </section>
                <section>
                  <h3>Motivation Outline</h3>
                  <ul>{assistantResult.motivation_letter_outline.map((item) => <li key={item}>{item}</li>)}</ul>
                </section>
                <section className="span-2">
                  <h3>Research Fit</h3>
                  <p>{assistantResult.research_fit_statement}</p>
                </section>
                <section>
                  <h3>Missing Fields</h3>
                  <ul>{assistantResult.missing_profile_fields.map((item) => <li key={item}>{item}</li>)}</ul>
                </section>
                <section>
                  <h3>Eligibility Warnings</h3>
                  <ul>{assistantResult.eligibility_warnings.map((item) => <li key={item}>{item}</li>)}</ul>
                </section>
                <section className="span-2">
                  <h3>Export Notes</h3>
                  <pre className="job-detail">{assistantResult.exported_notes}</pre>
                </section>
              </div>
            )}
          </section>
        )}

        {view === "admin" && (
          <section className="panel">
            <h2>Admin Imports</h2>
            <form className="grid-form" onSubmit={enqueueGrantsGov}>
              <Field labelText="Grants.gov keyword" value={grantsForm.keyword} onChange={(keyword) => setGrantsForm({ ...grantsForm, keyword })} />
              <Field labelText="Limit" type="number" value={String(grantsForm.limit)} onChange={(limit) => setGrantsForm({ ...grantsForm, limit: Number(limit) })} />
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={grantsForm.import_results}
                  onChange={(event) => setGrantsForm({ ...grantsForm, import_results: event.target.checked })}
                />
                Import results
              </label>
              <button className="primary">Queue Grants.gov search</button>
              <button className="secondary" type="button" onClick={(event) => void runGrantsGov(event as unknown as FormEvent)}>
                Run now
              </button>
            </form>
            <form className="grid-form separated" onSubmit={runBulkImport}>
              <Field labelText="Source" value={importForm.source} onChange={(source) => setImportForm({ ...importForm, source })} />
              <label className="toggle">
                <input type="checkbox" checked={importForm.dry_run} onChange={(event) => setImportForm({ ...importForm, dry_run: event.target.checked })} />
                Dry run
              </label>
              <TextArea labelText="Curated opportunities JSON" value={importForm.payload} onChange={(payload) => setImportForm({ ...importForm, payload })} />
              <button className="primary span-2">Import curated list</button>
            </form>
            <form className="grid-form separated" onSubmit={runExternalImport}>
              <div className="span-2">
                <h2>External Source Import</h2>
                <p className="muted">Normalize RSS or JSON feeds from EURAXESS, DAAD, Fulbright, Erasmus+, MSCA, universities, or foundations.</p>
              </div>
              <Field labelText="Source name" value={externalForm.source_name} onChange={(source_name) => setExternalForm({ ...externalForm, source_name })} />
              <Field labelText="Feed URL" value={externalForm.source_url} onChange={(source_url) => setExternalForm({ ...externalForm, source_url })} />
              <SelectField labelText="Kind" value={externalForm.source_kind} options={["rss", "json"]} onChange={(source_kind) => setExternalForm({ ...externalForm, source_kind })} />
              <SelectField labelText="Default type" value={externalForm.default_opportunity_type} options={opportunityTypes} onChange={(default_opportunity_type) => setExternalForm({ ...externalForm, default_opportunity_type })} />
              <Field labelText="Limit" type="number" value={String(externalForm.limit)} onChange={(limit) => setExternalForm({ ...externalForm, limit: Number(limit) })} />
              <Field labelText="Default country" value={externalForm.default_country} onChange={(default_country) => setExternalForm({ ...externalForm, default_country })} />
              <Field labelText="Default career stage" value={externalForm.default_career_stage} onChange={(default_career_stage) => setExternalForm({ ...externalForm, default_career_stage })} />
              <Field labelText="Default discipline" value={externalForm.default_discipline} onChange={(default_discipline) => setExternalForm({ ...externalForm, default_discipline })} />
              <Field labelText="Keyword tag" value={externalForm.keyword} onChange={(keyword) => setExternalForm({ ...externalForm, keyword })} />
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={externalForm.import_results}
                  onChange={(event) => setExternalForm({ ...externalForm, import_results: event.target.checked })}
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
                  <button className="secondary" onClick={() => void loadQueues()}>
                    Load queues
                  </button>
                  <button className="secondary" onClick={() => void enqueueReminderScan()}>
                    Queue reminder scan
                  </button>
                  <button className="secondary" onClick={() => void enqueueEmbeddingRefresh()}>
                    Refresh embeddings
                  </button>
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
              <form className="grid-form separated" onSubmit={loadJob}>
                <Field labelText="Job id" value={jobForm.job_id} onChange={(job_id) => setJobForm({ ...jobForm, job_id })} />
                <Field labelText="Queue" value={jobForm.queue_name} onChange={(queue_name) => setJobForm({ ...jobForm, queue_name })} />
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
                <button className="secondary" onClick={() => void loadAdminOps()}>
                  Load operations
                </button>
              </div>
              {adminData && <pre className="job-detail">{JSON.stringify(adminData, null, 2)}</pre>}
              {duplicateGroups.length > 0 && <pre className="job-detail">{JSON.stringify(duplicateGroups, null, 2)}</pre>}
              {auditLog.length > 0 && <pre className="job-detail">{JSON.stringify(auditLog, null, 2)}</pre>}
            </div>
          </section>
        )}
      </section>

      {selectedOpportunity && (
        <div className="drawer" role="dialog" aria-modal="true">
          <article>
            <button className="close" onClick={() => setSelectedOpportunity(null)}>
              x
            </button>
            <p className="eyebrow">{selectedOpportunity.source}</p>
            <h2>{selectedOpportunity.title}</h2>
            <div className="meta">
              <span>{label(selectedOpportunity.opportunity_type)}</span>
              <span>{selectedOpportunity.deadline ?? "No deadline"}</span>
            </div>
            <p>{selectedOpportunity.summary || "No summary provided."}</p>
            <h3>Eligibility</h3>
            <p>{selectedOpportunity.eligibility || "No eligibility text provided."}</p>
            <div className="chips">
              {[...selectedOpportunity.disciplines, ...selectedOpportunity.keywords, ...selectedOpportunity.countries].map((chip) => (
                <span key={chip}>{chip}</span>
              ))}
            </div>
            <a className="primary link-button" href={selectedOpportunity.url} target="_blank" rel="noreferrer">
              Open source
            </a>
            <div className="actions">
              {trackedStatuses.map((status) => (
                <button key={status} className="secondary" onClick={() => void updateStatus(selectedOpportunity.id, status)}>
                  {label(status)}
                </button>
              ))}
            </div>
            {statusByOpportunity.get(selectedOpportunity.id) && (
              <p className="muted">Current status: {label(statusByOpportunity.get(selectedOpportunity.id)!.status)}</p>
            )}
          </article>
        </div>
      )}
    </main>
  );
}

function OpportunityCard({
  item,
  onSelect,
  onStatus,
}: {
  item: Pick<Recommendation, "opportunity" | "match_score" | "semantic_score" | "score_breakdown" | "reasons" | "user_status">;
  onSelect: () => void;
  onStatus: (status: OpportunityStatus) => void;
}) {
  return (
    <article className="opportunity-card">
      <div className="card-head">
        <span className="score">{item.match_score ? `${item.match_score}%` : "Catalog"}</span>
        {item.semantic_score ? <span>Semantic {item.semantic_score}%</span> : null}
        <span>{item.opportunity.deadline ?? "No deadline"}</span>
      </div>
      <h3>{item.opportunity.title}</h3>
      <p>{item.opportunity.summary || "No summary provided."}</p>
      <div className="chips">
        <span>{label(item.opportunity.opportunity_type)}</span>
        <span>{item.opportunity.source}</span>
        {item.user_status && <span>{label(item.user_status)}</span>}
      </div>
      {item.match_score > 0 && (
        <div className="score-grid">
          <span>Semantic {item.score_breakdown.semantic}</span>
          <span>Eligibility {item.score_breakdown.eligibility}</span>
          <span>Deadline {item.score_breakdown.deadline}</span>
          <span>History {item.score_breakdown.user_history}</span>
        </div>
      )}
      {item.reasons.length > 0 && (
        <ul className="reasons">
          {item.reasons.slice(0, 3).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <div className="actions">
        <button className="secondary" onClick={onSelect}>
          Details
        </button>
        <button className="secondary" onClick={() => onStatus("saved")}>
          Save
        </button>
        <button className="secondary" onClick={() => onStatus("planned")}>
          Plan
        </button>
        <button className="secondary" onClick={() => onStatus("ignored")}>
          Ignore
        </button>
      </div>
    </article>
  );
}

export default App;

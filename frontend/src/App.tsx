import { FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
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
const reminderStatuses: OpportunityStatus[] = ["saved", "planned"];
const researcherViews = ["dashboard", "feed", "profile", "board", "assistant", "reminders", "notifications"] as const;

const defaultFilters = {
  keyword: "",
  opportunity_type: "",
  country: "",
  career_stage: "",
  source: "",
  active_only: true,
  min_score: 0,
  include_ignored: false,
};

type View = "dashboard" | "feed" | "profile" | "board" | "reminders" | "notifications" | "assistant" | "admin";

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

function viewLabel(value: View): string {
  const labels: Record<View, string> = {
    dashboard: "Dashboard",
    feed: "Matches",
    profile: "Profile",
    board: "Application Board",
    assistant: "Apply Assistant",
    reminders: "Reminders",
    notifications: "Notifications",
    admin: "Admin",
  };
  return labels[value];
}

function statusHelp(status: OpportunityStatus): string {
  const descriptions: Record<OpportunityStatus, string> = {
    saved: "Interesting, maybe later.",
    planned: "You intend to apply.",
    applied: "Application submitted.",
    accepted: "Accepted or awarded.",
    rejected: "Not selected.",
    ignored: "Hidden and used as ranking feedback.",
  };
  return descriptions[status];
}

const detailTabLabels = {
  overview: "Overview",
  reasons: "Why it matches",
  eligibility: "Requirements",
  assistant: "Apply plan",
  reminders: "Reminders",
} as const;

function profileLabel(profile: Profile, fallbackEmail?: string): string {
  return profile.full_name || profile.email || fallbackEmail || `Profile ${profile.id}`;
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
  disabled,
  list,
  title,
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  list?: string;
  title?: string;
}) {
  return (
    <label className="field">
      <span>{labelText}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        list={list}
        title={title}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function HelpTip({ text }: { text: string }) {
  return (
    <span className="help-tip" title={text} aria-label={text}>
      ?
    </span>
  );
}

function TextArea({
  labelText,
  value,
  onChange,
  placeholder,
  className = "span-2",
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <label className={`field ${className}`}>
      <span>{labelText}</span>
      <textarea value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} rows={4} />
    </label>
  );
}

function MultiValueField({
  labelText,
  values,
  onChange,
  placeholder = "Comma-separated values",
}: {
  labelText: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}) {
  return (
    <label className="field">
      <span>{labelText}</span>
      <input value={joinList(values)} placeholder={placeholder} onChange={(event) => onChange(splitList(event.target.value))} />
      {values.length > 0 && (
        <div className="inline-tags">
          {values.slice(0, 6).map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
      )}
    </label>
  );
}

function JsonTextArea({
  labelText,
  value,
  onChange,
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return <TextArea className="span-2 mono-field" labelText={labelText} value={value} onChange={onChange} />;
}

function ActionButton({
  children,
  busy,
  variant = "primary",
  type = "submit",
  onClick,
  disabled,
  className = "",
}: {
  children: ReactNode;
  busy?: boolean;
  variant?: "primary" | "secondary";
  type?: "submit" | "button";
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button className={`${variant} ${className}`} type={type} onClick={onClick} disabled={busy || disabled}>
      {busy && <span className="spinner" aria-hidden="true" />}
      {busy ? "Working..." : children}
    </button>
  );
}

function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <article className="opportunity-card skeleton-card" key={index}>
          <span />
          <strong />
          <p />
          <p />
        </article>
      ))}
    </>
  );
}

function ScoreBreakdown({ item }: { item: Pick<Recommendation, "score_breakdown"> }) {
  const entries = [
    ["Semantic", item.score_breakdown.semantic],
    ["Eligibility", item.score_breakdown.eligibility],
    ["Deadline", item.score_breakdown.deadline],
    ["History", item.score_breakdown.user_history],
  ] as const;
  return (
    <div className="score-bars">
      {entries.map(([name, value]) => (
        <div className="score-bar" key={name}>
          <span>{name}</span>
          <div>
            <i style={{ width: `${Math.max(4, value)}%` }} />
          </div>
          <b>{value}</b>
        </div>
      ))}
    </div>
  );
}

function RequirementSummary({ opportunity }: { opportunity: Opportunity }) {
  const requirements = opportunity.extracted_requirements;
  if (!requirements || (requirements.confidence ?? 0) === 0) {
    return <EmptyState title="No parsed requirements yet" detail="Add richer eligibility text to extract career stage, country, degree, language, and publication requirements." />;
  }
  const rows = [
    ["Career stages", requirements.career_stages.join(", ")],
    ["Countries", requirements.countries.join(", ")],
    ["Degree", requirements.required_degree],
    ["Languages", requirements.languages.join(", ")],
    ["Years since PhD", requirements.years_since_phd ? String(requirements.years_since_phd) : ""],
  ].filter(([, value]) => value);
  return (
    <div className="requirement-summary">
      <strong>Parsed requirements ({requirements.confidence}% confidence)</strong>
      <div className="score-grid">
        {rows.map(([name, value]) => (
          <span key={name}>{name}: {value}</span>
        ))}
      </div>
      {requirements.publication_expectation && <p className="muted">Publication signal: {requirements.publication_expectation}</p>}
      {requirements.mobility && <p className="muted">Mobility signal: {requirements.mobility}</p>}
      {requirements.citizenship && <p className="muted">Citizenship signal: {requirements.citizenship}</p>}
    </div>
  );
}

function ProfileCompleteness({ profile, details }: { profile: Profile | null; details: ProfileDetailsPayload }) {
  const checks = [
    Boolean(profile?.full_name),
    Boolean(profile?.email),
    Boolean(profile?.country),
    Boolean(profile?.disciplines.length),
    Boolean(profile?.keywords.length),
    Boolean(details.research_summary),
    Boolean(details.publications.length),
    Boolean(details.languages.length),
  ];
  const score = Math.round((checks.filter(Boolean).length / checks.length) * 100);
  return (
    <div className="completeness">
      <div>
        <span>Profile completeness</span>
        <strong>{score}%</strong>
      </div>
      <div className="progress"><i style={{ width: `${score}%` }} /></div>
    </div>
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
  const [view, setView] = useState<View>("dashboard");
  const [loading, setLoading] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
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
  const [filters, setFilters] = useState(defaultFilters);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [detailTab, setDetailTab] = useState<"overview" | "reasons" | "eligibility" | "assistant" | "reminders">("overview");
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
  const selectedRecommendation = useMemo(
    () => recommendations.find((item) => item.opportunity.id === selectedOpportunity?.id) ?? null,
    [recommendations, selectedOpportunity],
  );
  const selectedOpportunityReminders = useMemo(
    () => reminders.filter((reminder) => reminder.opportunity_id === selectedOpportunity?.id),
    [reminders, selectedOpportunity],
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

  async function refreshWorkspace(profile = activeProfile, nextFilters = filters) {
    setError("");
    setWorkspaceLoading(true);
    try {
      const opportunityQuery = {
        keyword: nextFilters.keyword,
        opportunity_type: nextFilters.opportunity_type,
        country: nextFilters.country,
        career_stage: nextFilters.career_stage,
        source: nextFilters.source,
        active_only: nextFilters.active_only,
        limit: 100,
      };
      const catalogPromise = api.opportunities(opportunityQuery);
      if (token && profile) {
        const [nextRecommendations, nextStatuses, nextReminders, nextOpportunities] = await Promise.all([
          api.recommendations(token, profile.id, {
            min_score: nextFilters.min_score,
            include_ignored: nextFilters.include_ignored,
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
    } finally {
      setWorkspaceLoading(false);
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

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    if (!authForm.email || !authForm.password || (authMode === "register" && !authForm.full_name)) {
      setError("Email, password, and name are required.");
      return;
    }
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

  function resetFilters() {
    setFilters(defaultFilters);
    void refreshWorkspace(activeProfile, defaultFilters);
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (!profileForm.full_name || !profileForm.career_stage) {
      setError("Full name and career stage are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const profile = await api.createProfile(token, {
        ...profileForm,
        email: user?.email ?? normalizeText(profileForm.email),
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
      const updated = await api.setStatus(token, activeProfile.id, opportunityId, status);
      setStatuses((current) => {
        const others = current.filter((item) => item.opportunity_id !== opportunityId);
        return [...others, updated];
      });
      setRecommendations((current) =>
        current.map((item) => (item.opportunity.id === opportunityId ? { ...item, user_status: status } : item)),
      );
      setNotice(`Marked as ${label(status)}`);
    } catch (statusError) {
      setError((statusError as Error).message);
    }
  }

  async function createReminder(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    if (!reminderForm.opportunity_id || !reminderForm.remind_on) {
      setError("Choose an opportunity and reminder date.");
      return;
    }
    if (!selectedStatusIds.has(Number(reminderForm.opportunity_id))) {
      setError("Save or plan the opportunity before creating a reminder.");
      return;
    }
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
    if (!token) return;
    setError("");
    try {
      const [dashboard, audit, duplicates] = await Promise.all([api.adminDashboard(token), api.adminAuditLog(token), api.adminDuplicates(token)]);
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
    if (!assistantForm.opportunity_id) {
      setError("Choose an opportunity before generating notes.");
      return;
    }
    if (!selectedStatusIds.has(Number(assistantForm.opportunity_id))) {
      setError("Save or plan the opportunity before opening the assistant.");
      return;
    }
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
    }
  }

  async function runExternalImport(event: FormEvent) {
    event.preventDefault();
    if (!externalForm.source_name || !externalForm.source_url) {
      setError("Source name and feed URL are required.");
      return;
    }
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
    if (!token) return;
    setError("");
    try {
      const result = await api.enqueueGrantsGov(token, grantsForm);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued Grants.gov job ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function enqueueReminderScan() {
    if (!token) return;
    setError("");
    try {
      const result = await api.enqueueReminderScan(token);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued reminder scan ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function enqueueEmbeddingRefresh() {
    if (!token) return;
    setError("");
    try {
      const result = await api.enqueueEmbeddingRefresh(token);
      setJobForm({ job_id: result.job_id, queue_name: result.queue });
      setNotice(`Queued embedding refresh ${result.job_id}`);
      await loadQueues();
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function loadQueues() {
    if (!token) return;
    setError("");
    try {
      setQueueStats(await api.queues(token));
    } catch (jobError) {
      setError((jobError as Error).message);
    }
  }

  async function loadJob(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    try {
      setJobDetail(await api.job(token, jobForm.job_id, jobForm.queue_name));
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
  const selectedStatusIds = useMemo(
    () => new Set(statuses.filter((record) => reminderStatuses.includes(record.status)).map((record) => record.opportunity_id)),
    [statuses],
  );
  const reminderEligibleOpportunities = useMemo(
    () => [...opportunitiesById.values()].filter((opportunity) => selectedStatusIds.has(opportunity.id)),
    [opportunitiesById, selectedStatusIds],
  );
  const sourceOptions = useMemo(
    () => [...new Set([...opportunitiesById.values()].map((opportunity) => opportunity.source).filter(Boolean))].sort(),
    [opportunitiesById],
  );
  const countryOptions = useMemo(
    () => [...new Set([...opportunitiesById.values()].flatMap((opportunity) => opportunity.countries).filter(Boolean))].sort(),
    [opportunitiesById],
  );
  const keywordOptions = useMemo(
    () => [...new Set([...opportunitiesById.values()].flatMap((opportunity) => [...opportunity.keywords, ...opportunity.disciplines]).filter(Boolean))].sort(),
    [opportunitiesById],
  );
  const visibleViews = useMemo(
    () => (user?.role === "admin" ? [...researcherViews, "admin" as const] : [...researcherViews]),
    [user?.role],
  );
  const topMatches = useMemo(() => recommendations.slice(0, 3), [recommendations]);
  const plannedStatuses = useMemo(
    () => statuses.filter((status) => ["planned", "applied"].includes(status.status)),
    [statuses],
  );
  const nextReminder = useMemo(
    () => reminders.filter((reminder) => reminder.status === "pending").sort((a, b) => a.remind_on.localeCompare(b.remind_on))[0] ?? null,
    [reminders],
  );
  const nextAction = useMemo(() => {
    if (!activeProfile) return { title: "Create your research profile", detail: "Start with career stage, country, disciplines, and keywords.", target: "profile" as View };
    if (!activeProfile.country || activeProfile.disciplines.length === 0 || activeProfile.keywords.length === 0) {
      return { title: "Complete your profile basics", detail: "Country, disciplines, and keywords make the match explanations much better.", target: "profile" as View };
    }
    if (!detailsForm.research_summary || detailsForm.publications.length === 0) {
      return { title: "Add evidence for readiness scoring", detail: "Research summary and publications improve advisor gaps and fit statements.", target: "profile" as View };
    }
    if (topMatches.length > 0 && plannedStatuses.length === 0) {
      return { title: "Review your strongest matches", detail: `Start with ${topMatches[0].opportunity.title}. Save or plan anything worth applying to.`, target: "feed" as View };
    }
    if (reminderEligibleOpportunities.length > 0 && !assistantResult) {
      return { title: "Generate an advisor memo", detail: "Use the Apply Assistant for one saved or planned opportunity.", target: "assistant" as View };
    }
    if (nextReminder) {
      return { title: "Check your next deadline reminder", detail: `${opportunitiesById.get(nextReminder.opportunity_id)?.title ?? "Opportunity"} on ${nextReminder.remind_on}.`, target: "reminders" as View };
    }
    return { title: "Keep refining matches", detail: "Review new opportunities, ignore poor fits, and plan applications from the board.", target: "feed" as View };
  }, [activeProfile, assistantResult, detailsForm, nextReminder, opportunitiesById, plannedStatuses.length, reminderEligibleOpportunities.length, topMatches]);

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
            <ActionButton busy={loading} variant="primary" className="span-2">
              {authMode === "login" ? "Sign in" : "Sign up"}
            </ActionButton>
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
          {visibleViews.map((item) => (
            <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
              {viewLabel(item)}
            </button>
          ))}
        </nav>
        <div className="profile-switcher">
          <span>Active profile</span>
          <select value={activeProfile?.id ?? ""} onChange={(event) => setActiveProfileId(Number(event.target.value))}>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profileLabel(profile, user.email)}
              </option>
            ))}
          </select>
        </div>
        <div className="account-summary">
          <span>{user.email}</span>
          <small>{user.role}</small>
        </div>
        <button className="ghost" onClick={logout}>
          Sign out
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{viewLabel(view)}</p>
            <h1>{activeProfile ? profileLabel(activeProfile, user.email) : "Create your first profile"}</h1>
          </div>
          <ActionButton busy={workspaceLoading} variant="secondary" type="button" onClick={() => void refreshWorkspace(activeProfile)}>
            Refresh
          </ActionButton>
        </header>
        <ProfileCompleteness profile={activeProfile} details={detailsForm} />

        {notice && <div className="alert success">{notice}</div>}
        {error && <div className="alert error">{error}</div>}

        {view === "dashboard" && (
          <section className="dashboard-grid">
            <article className="panel next-action">
              <p className="eyebrow">Next best action</p>
              <h2>{nextAction.title}</h2>
              <p>{nextAction.detail}</p>
              <button className="primary" onClick={() => setView(nextAction.target)}>
                Go there
              </button>
            </article>
            <article className="panel metric-panel">
              <span>Top matches</span>
              <strong>{topMatches.length}</strong>
              <p className="muted">High-signal opportunities ready for review.</p>
            </article>
            <article className="panel metric-panel">
              <span>In application plan</span>
              <strong>{plannedStatuses.length}</strong>
              <p className="muted">Planned or submitted opportunities.</p>
            </article>
            <article className="panel metric-panel">
              <span>Next reminder</span>
              <strong>{nextReminder?.remind_on ?? "None"}</strong>
              <p className="muted">{nextReminder ? opportunitiesById.get(nextReminder.opportunity_id)?.title ?? "Opportunity reminder" : "Plan an opportunity to start reminders."}</p>
            </article>
            <section className="panel span-2">
              <div className="section-title">
                <div>
                  <h2>Strongest Matches</h2>
                  <p>Review these first, then save, plan, or ignore to teach the system.</p>
                </div>
                <button className="secondary" onClick={() => setView("feed")}>
                  Open matches
                </button>
              </div>
              <div className="cards compact-cards">
                {topMatches.map((item) => (
                  <OpportunityCard
                    key={item.opportunity.id}
                    item={item}
                    canTrack={Boolean(activeProfile)}
                    onSelect={() => setSelectedOpportunity(item.opportunity)}
                    onStatus={(status) => void updateStatus(item.opportunity.id, status)}
                  />
                ))}
                {topMatches.length === 0 && <EmptyState title="No matches yet" detail="Complete your profile or import opportunities, then refresh the workspace." />}
              </div>
            </section>
            <section className="panel">
              <h2>How This Flows</h2>
              <div className="flow-steps">
                <span>1. Profile</span>
                <span>2. Matches</span>
                <span>3. Save or plan</span>
                <span>4. Advisor memo</span>
                <span>5. Board and reminders</span>
              </div>
            </section>
          </section>
        )}

        {view === "feed" && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Matches</h2>
                <p>Recommended opportunities appear first. Use Save, Plan, or Ignore to make future results smarter.</p>
              </div>
            </div>
            <div className="filters">
              <Field labelText="Keyword" value={filters.keyword} list="keyword-options" placeholder="AI, biology, mobility..." onChange={(keyword) => setFilters({ ...filters, keyword })} />
              <SelectField
                labelText="Type"
                value={(filters.opportunity_type || "") as OpportunityType | ""}
                options={["", ...opportunityTypes] as (OpportunityType | "")[]}
                onChange={(opportunity_type) => setFilters({ ...filters, opportunity_type })}
              />
              <Field labelText="Country" value={filters.country} list="country-options" placeholder="Germany, EU, USA..." onChange={(country) => setFilters({ ...filters, country })} />
              <Field labelText="Source" value={filters.source} list="source-options" placeholder="euraxess, daad, grants.gov..." onChange={(source) => setFilters({ ...filters, source })} />
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={filters.active_only}
                  onChange={(event) => setFilters({ ...filters, active_only: event.target.checked })}
                />
                Active only
              </label>
              <ActionButton variant="secondary" type="button" busy={workspaceLoading} onClick={() => void refreshWorkspace(activeProfile)}>
                Apply filters
              </ActionButton>
              <button className="secondary" type="button" onClick={resetFilters}>
                Clear filters
              </button>
            </div>
            <datalist id="source-options">{sourceOptions.map((item) => <option value={item} key={item} />)}</datalist>
            <datalist id="country-options">{countryOptions.map((item) => <option value={item} key={item} />)}</datalist>
            <datalist id="keyword-options">{keywordOptions.map((item) => <option value={item} key={item} />)}</datalist>
            <div className="cards">
              {workspaceLoading ? <SkeletonCards /> : (activeProfile ? recommendations : opportunities.map((opportunity) => ({ opportunity, match_score: 0, semantic_score: 0, score_breakdown: { semantic: 0, eligibility: 0, deadline: 0, user_history: 0, final: 0 }, reasons: [], readiness_score: 0, gaps: [], strengths: [], user_status: null }))).map(
                (item) => (
                  <OpportunityCard
                    key={item.opportunity.id}
                    item={item}
                    canTrack={Boolean(activeProfile)}
                    onSelect={() => setSelectedOpportunity(item.opportunity)}
                    onStatus={(status) => void updateStatus(item.opportunity.id, status)}
                  />
                ),
              )}
              {activeProfile && !workspaceLoading && recommendations.length === 0 && (
                <EmptyState title="No matches found" detail="Try clearing filters, lowering the score threshold, or searching broader terms like fellowship, mobility, AI, health, or Europe." />
              )}
              {!activeProfile && !workspaceLoading && opportunities.length === 0 && (
                <EmptyState title="No opportunities found" detail="Try clearing filters or searching broader terms like fellowship, mobility, AI, health, or Europe." />
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
              <Field labelText="Account email" value={user.email} disabled onChange={() => undefined} title="Profile email is linked to the signed-in account." />
              <SelectField labelText="Career stage" value={profileForm.career_stage} options={careerStages} onChange={(career_stage) => setProfileForm({ ...profileForm, career_stage })} />
              <Field labelText="Country" value={profileForm.country ?? ""} list="country-options" placeholder="Use countries visible in the feed" onChange={(country) => setProfileForm({ ...profileForm, country })} />
              <MultiValueField labelText="Disciplines" values={profileForm.disciplines} placeholder="Try values from current opportunities" onChange={(disciplines) => setProfileForm({ ...profileForm, disciplines })} />
              <MultiValueField labelText="Keywords" values={profileForm.keywords} placeholder="Try values from current opportunities" onChange={(keywords) => setProfileForm({ ...profileForm, keywords })} />
              <MultiValueField labelText="Preferred countries" values={profileForm.preferred_countries} onChange={(preferred_countries) => setProfileForm({ ...profileForm, preferred_countries })} />
              <Field labelText="ORCID" value={profileForm.orcid_id ?? ""} onChange={(orcid_id) => setProfileForm({ ...profileForm, orcid_id })} />
              <Field labelText="Google Scholar URL" value={profileForm.google_scholar_url ?? ""} onChange={(google_scholar_url) => setProfileForm({ ...profileForm, google_scholar_url })} />
              <Field labelText="LinkedIn URL" value={profileForm.linkedin_url ?? ""} onChange={(linkedin_url) => setProfileForm({ ...profileForm, linkedin_url })} />
              <ActionButton busy={loading} className="span-2">Create profile</ActionButton>
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
              <ActionButton busy={loading} className="span-2">Save details</ActionButton>
            </form>
          </section>
        )}

        {view === "profile" && (
          <section className="panel">
            <div className="section-title">
              <div className="title-with-help">
                <h2>Profile Imports</h2>
                <HelpTip text="ORCID is a public researcher identifier. This app uses it to prefill your profile and improve matching with public academic metadata." />
              </div>
            </div>
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
                <div className="title-with-help">
                  <h2>OpenAlex Enrichment</h2>
                  <HelpTip text="OpenAlex is an open scholarly graph. Enrichment adds public publication titles and concepts to improve profile completeness and recommendation explanations." />
                </div>
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
                <div>
                  <h2>{label(status)}</h2>
                  <small>{statusHelp(status)}</small>
                </div>
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
            <div className="title-with-help">
              <h2>Reminders</h2>
              <HelpTip text="Create reminders only for opportunities you saved or planned, so the reminder list stays tied to real intent." />
            </div>
            <form className="grid-form" onSubmit={createReminder}>
              <label className="field">
                <span>Opportunity</span>
                <select value={reminderForm.opportunity_id} onChange={(event) => setReminderForm({ ...reminderForm, opportunity_id: event.target.value })}>
                  <option value="">Select a saved or planned opportunity</option>
                  {reminderEligibleOpportunities.map((opportunity) => (
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
                    <button className="secondary" title="Mark this reminder as done so it leaves the pending workflow." onClick={() => void completeReminder(reminder.id)}>
                      Mark done
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
              <button className="secondary" title="Fetch the latest notification history and saved alert preferences." onClick={() => void loadNotifications()}>
                Refresh notifications
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
              <label className="field">
                <span>
                  Minimum alert score <HelpTip text="High-match alerts only send when a recommendation score is at or above this number." />
                </span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={String(notificationPrefs.min_alert_score)}
                  onChange={(event) => setNotificationPrefs({ ...notificationPrefs, min_alert_score: Number(event.target.value) })}
                />
              </label>
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
                <div className="title-with-help">
                  <h2>Apply Assistant</h2>
                  <HelpTip text="Save or plan an opportunity first, then generate structured notes for that specific application." />
                </div>
                <p>Generate a checklist, motivation outline, fit statement, eligibility warnings, and exportable notes.</p>
              </div>
            </div>
            <form className="grid-form" onSubmit={generateApplicationNotes}>
              <label className="field span-2">
                <span>Opportunity</span>
                <select value={assistantForm.opportunity_id} onChange={(event) => setAssistantForm({ opportunity_id: event.target.value })}>
                  <option value="">Select a saved or planned opportunity</option>
                  {reminderEligibleOpportunities.map((opportunity) => (
                    <option value={opportunity.id} key={opportunity.id}>
                      {opportunity.title}
                    </option>
                  ))}
                </select>
              </label>
              <button className="primary span-2">Generate notes</button>
            </form>
            {reminderEligibleOpportunities.length === 0 && (
              <EmptyState title="No saved or planned opportunities" detail="Save or plan an opportunity from the feed before using the assistant." />
            )}
            {assistantResult && (
              <div className="assistant-grid separated">
                <section className="span-2 advisor-memo">
                  <div className="card-head">
                    <h3>Advisor Memo</h3>
                    <span>{assistantResult.advisor_provider}</span>
                  </div>
                  <p>{assistantResult.advisor_memo}</p>
                </section>
                <section className="span-2">
                  <h3>Readiness</h3>
                  <div className="completeness">
                    <div>
                      <span>Application readiness</span>
                      <strong>{assistantResult.readiness_score}%</strong>
                    </div>
                    <div className="progress"><i style={{ width: `${assistantResult.readiness_score}%` }} /></div>
                  </div>
                </section>
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
                <section>
                  <h3>Strengths</h3>
                  <ul>{(assistantResult.strengths.length ? assistantResult.strengths : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
                </section>
                <section>
                  <h3>Gap Analysis</h3>
                  <ul>{(assistantResult.gap_analysis.length ? assistantResult.gap_analysis : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
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
              <JsonTextArea labelText="Curated opportunities JSON" value={importForm.payload} onChange={(payload) => setImportForm({ ...importForm, payload })} />
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
                  <button className="secondary" onClick={() => token && void api.enqueueWeeklyDigest(token).then((job) => { setJobForm({ job_id: job.job_id, queue_name: job.queue }); setNotice(`Queued weekly digest ${job.job_id}`); void loadQueues(); }).catch((err) => setError((err as Error).message))}>
                    Queue digest
                  </button>
                  <button className="secondary" onClick={() => token && void api.enqueueHighMatchAlerts(token).then((job) => { setJobForm({ job_id: job.job_id, queue_name: job.queue }); setNotice(`Queued high-match alerts ${job.job_id}`); void loadQueues(); }).catch((err) => setError((err as Error).message))}>
                    Queue alerts
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
            {selectedRecommendation && (
              <div className="intelligence-panel">
                <strong>{selectedRecommendation.match_score}% match</strong>
                <ScoreBreakdown item={selectedRecommendation} />
              </div>
            )}
            <div className="tabs">
              {(["overview", "reasons", "eligibility", "assistant", "reminders"] as const).map((tab) => (
                <button className={detailTab === tab ? "active" : ""} key={tab} onClick={() => setDetailTab(tab)}>
                  {detailTabLabels[tab]}
                </button>
              ))}
            </div>
            {detailTab === "overview" && (
              <>
                <p>{selectedOpportunity.summary || "No summary provided."}</p>
                <div className="chips">
                  {[...selectedOpportunity.disciplines, ...selectedOpportunity.keywords, ...selectedOpportunity.countries].map((chip) => (
                    <span key={chip}>{chip}</span>
                  ))}
                </div>
              </>
            )}
            {detailTab === "reasons" && (
              selectedRecommendation ? (
                <div className="explanation-grid">
                  {selectedRecommendation.reasons.map((reason) => (
                    <article key={reason}>
                      <strong>{reason.includes("lower") ? "Risk" : "Signal"}</strong>
                      <p>{reason}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState title="No match reasons" detail="Recommendations explain semantic, eligibility, deadline, and history signals once a profile is selected." />
              )
            )}
            {detailTab === "eligibility" && (
              <>
                <h3>Eligibility</h3>
                <p>{selectedOpportunity.eligibility || "No eligibility text provided."}</p>
                <RequirementSummary opportunity={selectedOpportunity} />
                <div className="score-grid">
                  <span>Career stages {selectedOpportunity.career_stages.join(", ") || "Not specified"}</span>
                  <span>Countries {selectedOpportunity.countries.join(", ") || "Not specified"}</span>
                </div>
              </>
            )}
            {detailTab === "assistant" && (
              <div>
                {assistantResult?.opportunity_id === selectedOpportunity.id ? (
                  <>
                    <h3>Research Fit</h3>
                    <p>{assistantResult.research_fit_statement}</p>
                    <h3>Readiness</h3>
                    <p>{assistantResult.readiness_score}% application readiness</p>
                    <h3>Advisor Memo</h3>
                    <p>{assistantResult.advisor_memo}</p>
                    <h3>Warnings</h3>
                    <ul className="reasons">{(assistantResult.eligibility_warnings.length ? assistantResult.eligibility_warnings : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
                    <h3>Gaps</h3>
                    <ul className="reasons">{(assistantResult.gap_analysis.length ? assistantResult.gap_analysis : ["None flagged"]).map((item) => <li key={item}>{item}</li>)}</ul>
                  </>
                ) : (
                  <button
                    className="primary"
                    disabled={!selectedStatusIds.has(selectedOpportunity.id)}
                    onClick={() => {
                      setAssistantForm({ opportunity_id: String(selectedOpportunity.id) });
                      setView("assistant");
                      setSelectedOpportunity(null);
                    }}
                  >
                    {selectedStatusIds.has(selectedOpportunity.id) ? "Open assistant for this opportunity" : "Save or plan to use assistant"}
                  </button>
                )}
              </div>
            )}
            {detailTab === "reminders" && (
              <div className="table">
                {selectedOpportunityReminders.map((reminder) => (
                  <div className="table-row compact-row" key={reminder.id}>
                    <span>{reminder.message || "Deadline reminder"}</span>
                    <span>{reminder.remind_on}</span>
                    <span>{label(reminder.status)}</span>
                  </div>
                ))}
                {selectedOpportunityReminders.length === 0 && <EmptyState title="No reminders for this opportunity" detail="Saving or planning opportunities can create deadline reminders automatically." />}
              </div>
            )}
            <a className="primary link-button" href={selectedOpportunity.url} target="_blank" rel="noreferrer">
              Open source
            </a>
            <div className="actions">
              {trackedStatuses.map((status) => (
                <button key={status} className="secondary" title={statusHelp(status)} onClick={() => void updateStatus(selectedOpportunity.id, status)}>
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
  canTrack,
  onSelect,
  onStatus,
}: {
  item: Pick<Recommendation, "opportunity" | "match_score" | "semantic_score" | "score_breakdown" | "reasons" | "user_status">;
  canTrack: boolean;
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
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Keep this opportunity for later." : "Create a profile before saving opportunities."} onClick={() => onStatus("saved")}>
          Save
        </button>
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Add this opportunity to your application plan." : "Create a profile before planning opportunities."} onClick={() => onStatus("planned")}>
          Plan
        </button>
        <button className="secondary" disabled={!canTrack} title={canTrack ? "Hide this kind of result and teach ranking preferences." : "Create a profile before ignoring opportunities."} onClick={() => onStatus("ignored")}>
          Ignore
        </button>
      </div>
    </article>
  );
}

export default App;

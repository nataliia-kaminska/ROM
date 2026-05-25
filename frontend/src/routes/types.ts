import type { FormEvent } from "react";
import type { OpportunityPayload, ProfileDetailsPayload, ProfilePayload } from "../api";
import type { View } from "../constants";
import type {
  ApplicationAssistantResult,
  CareerStage,
  NotificationItem,
  NotificationPreference,
  OpenAlexPreview,
  Opportunity,
  DisplayOpportunityStatus,
  OpportunityStatus,
  OpportunityType,
  Profile,
  ProfileDiscoveryCandidate,
  QueueStats,
  Recommendation,
  Reminder,
  StatusRecord,
} from "../types";

type Filters = {
  keyword: string;
  opportunity_type: string;
  country: string;
  career_stage: string;
  source: string;
  active_only: boolean;
  min_score: number;
  include_ignored: boolean;
  status_filter: string;
  sort_by: string;
  sort_order: string;
};

type GrantsForm = { keyword: string; limit: number; import_results: boolean };
type EUFundingForm = { keyword: string; source_name: string; programme: string; limit: number; import_results: boolean };
type ImportForm = { source: string; dry_run: boolean; payload: string };
type JobForm = { job_id: string; queue_name: string };
type OrcidForm = {
  orcid_id: string;
  email: string;
  career_stage: CareerStage;
  disciplines: string;
  preferred_countries: string;
};
type OpenAlexForm = { openalex_author_id: string; orcid_id: string; max_works: number };
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

export type RouteController = {
  view: View;
  opportunityId: number | null;
  onViewChange: (view: View) => void;
};

export type WorkspaceController = {
  activeProfile: Profile | null;
  isSignedIn: boolean;
  workspaceLoading: boolean;
  filters: Filters;
  recommendations: Recommendation[];
  opportunities: Opportunity[];
  matchesPage: number;
  matchesHasNextPage: boolean;
  matchesTotalPages: number;
  matchesTotalIsEstimate: boolean;
  statuses: StatusRecord[];
  reminders: Reminder[];
  reminderForm: { opportunity_id: string; remind_on: string; message: string };
  nextAction: { title: string; detail: string; target: View; focusFields?: string[] };
  topMatches: Recommendation[];
  plannedStatuses: StatusRecord[];
  nextReminder: Reminder | null;
  opportunitiesById: Map<number, Opportunity>;
  reminderEligibleOpportunities: Opportunity[];
  sourceOptions: string[];
  countryOptions: string[];
  disciplineOptions: string[];
  keywordOptions: string[];
  onProfileFocus: (fields: string[]) => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: DisplayOpportunityStatus) => void;
  onFiltersChange: (filters: Filters) => void;
  onResetFilters: () => void;
  onMatchesPageChange: (page: number) => void;
  onReminderFormChange: (form: { opportunity_id: string; remind_on: string; message: string }) => void;
  onCreateReminder: (event: FormEvent) => void;
  onCompleteReminder: (reminderId: number) => void;
};

export type ProfileController = {
  userEmail: string;
  userFullName: string;
  userAuthProvider: string;
  userOrcidId: string | null;
  passwordLoginEnabled: boolean;
  loading: boolean;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  accountForm: { full_name: string; email: string };
  passwordForm: { current_password: string; new_password: string; confirm_password: string };
  orcidForm: OrcidForm;
  openAlexForm: OpenAlexForm;
  openAlexPreview: OpenAlexPreview | null;
  profileDiscoveryCandidates: ProfileDiscoveryCandidate[];
  profileDiscoveryConfirmed: ProfileDiscoveryCandidate[];
  profileDiscoveryLoading: boolean;
  onProfileChange: (profile: ProfilePayload) => void;
  onDetailsChange: (details: ProfileDetailsPayload) => void;
  onAccountChange: (account: { full_name: string; email: string }) => void;
  onPasswordChange: (password: { current_password: string; new_password: string; confirm_password: string }) => void;
  onLoadDetails: () => void;
  highlightFields: string[];
  onSaveProfile: (event: FormEvent) => void;
  onSaveDetails: (event: FormEvent) => void;
  onSaveAccount: (event: FormEvent) => void;
  onSavePassword: (event: FormEvent) => void;
  onOrcidChange: (form: OrcidForm) => void;
  onOpenAlexChange: (form: OpenAlexForm) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: () => void;
  onPreviewOpenAlex: (event: FormEvent) => void;
  onDiscoverProfileCandidates: () => void;
  onApplyProfileCandidate: (candidate: ProfileDiscoveryCandidate) => void;
  onDismissProfileCandidate: (candidate: ProfileDiscoveryCandidate) => void;
};

export type NotificationsController = {
  notifications: NotificationItem[];
  notificationPrefs: NotificationPreference;
  onPrefsChange: (prefs: NotificationPreference) => void;
  onSavePrefs: (event: FormEvent) => void;
  onUnsubscribe: () => void;
  onMarkRead: (notificationId: number) => void;
};

export type AssistantController = {
  assistantForm: { opportunity_id: string };
  assistantResult: ApplicationAssistantResult | null;
  assistantLoading: boolean;
  onAssistantFormChange: (form: { opportunity_id: string }) => void;
  onGenerateAssistant: (event: FormEvent) => void;
};

export type AdminController = {
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
};

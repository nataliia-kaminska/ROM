import type { FormEvent } from "react";
import type { OpportunityPayload, ProfileDetailsPayload, ProfilePayload } from "../api";
import type { View } from "../constants";
import { AdminView } from "../views/AdminView";
import { AssistantView } from "../views/AssistantView";
import { BoardView } from "../views/BoardView";
import { DashboardView } from "../views/DashboardView";
import { FeedView } from "../views/FeedView";
import { NotificationsView } from "../views/NotificationsView";
import { ProfileImportsView, ProfileView } from "../views/ProfileView";
import { RemindersView } from "../views/RemindersView";
import type {
  ApplicationAssistantResult,
  CareerStage,
  NotificationItem,
  NotificationPreference,
  Opportunity,
  OpportunityStatus,
  OpportunityType,
  Profile,
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
};

type GrantsForm = { keyword: string; limit: number; import_results: boolean };
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
  source_kind: "rss" | "json";
  import_results: boolean;
  limit: number;
  default_opportunity_type: OpportunityType;
  default_country: string;
  default_career_stage: string;
  default_discipline: string;
  keyword: string;
};

type RouteController = {
  view: View;
  onViewChange: (view: View) => void;
};

type WorkspaceController = {
  activeProfile: Profile | null;
  workspaceLoading: boolean;
  filters: Filters;
  recommendations: Recommendation[];
  opportunities: Opportunity[];
  statuses: StatusRecord[];
  reminders: Reminder[];
  reminderForm: { opportunity_id: string; remind_on: string; message: string };
  nextAction: { title: string; detail: string; target: View };
  topMatches: Recommendation[];
  plannedStatuses: StatusRecord[];
  nextReminder: Reminder | null;
  opportunitiesById: Map<number, Opportunity>;
  reminderEligibleOpportunities: Opportunity[];
  sourceOptions: string[];
  countryOptions: string[];
  keywordOptions: string[];
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onStatus: (opportunityId: number, status: OpportunityStatus) => void;
  onFiltersChange: (filters: Filters) => void;
  onApplyFilters: () => void;
  onResetFilters: () => void;
  onReminderFormChange: (form: { opportunity_id: string; remind_on: string; message: string }) => void;
  onCreateReminder: (event: FormEvent) => void;
  onCompleteReminder: (reminderId: number) => void;
};

type ProfileController = {
  userEmail: string;
  loading: boolean;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  orcidForm: OrcidForm;
  openAlexForm: OpenAlexForm;
  onProfileChange: (profile: ProfilePayload) => void;
  onDetailsChange: (details: ProfileDetailsPayload) => void;
  onLoadDetails: () => void;
  onSaveProfile: (event: FormEvent) => void;
  onSaveDetails: (event: FormEvent) => void;
  onOrcidChange: (form: OrcidForm) => void;
  onOpenAlexChange: (form: OpenAlexForm) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: (event: FormEvent) => void;
};

type NotificationsController = {
  notifications: NotificationItem[];
  notificationPrefs: NotificationPreference;
  onPrefsChange: (prefs: NotificationPreference) => void;
  onLoadNotifications: () => void;
  onSavePrefs: (event: FormEvent) => void;
  onUnsubscribe: () => void;
  onMarkRead: (notificationId: number) => void;
};

type AssistantController = {
  assistantForm: { opportunity_id: string };
  assistantResult: ApplicationAssistantResult | null;
  onAssistantFormChange: (form: { opportunity_id: string }) => void;
  onGenerateAssistant: (event: FormEvent) => void;
};

type AdminController = {
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
};

export function WorkspaceRoutes({
  route,
  workspace,
  profile,
  notifications,
  assistant,
  admin,
}: {
  route: RouteController;
  workspace: WorkspaceController;
  profile: ProfileController;
  notifications: NotificationsController;
  assistant: AssistantController;
  admin: AdminController;
}) {
  switch (route.view) {
    case "dashboard":
      return (
        <DashboardView
          nextAction={workspace.nextAction}
          topMatches={workspace.topMatches}
          plannedStatuses={workspace.plannedStatuses}
          nextReminder={workspace.nextReminder}
          opportunitiesById={workspace.opportunitiesById}
          canTrack={Boolean(workspace.activeProfile)}
          onViewChange={route.onViewChange}
          onSelectOpportunity={workspace.onSelectOpportunity}
          onStatus={workspace.onStatus}
        />
      );
    case "feed":
      return (
        <FeedView
          filters={workspace.filters}
          sourceOptions={workspace.sourceOptions}
          countryOptions={workspace.countryOptions}
          keywordOptions={workspace.keywordOptions}
          workspaceLoading={workspace.workspaceLoading}
          activeProfile={Boolean(workspace.activeProfile)}
          recommendations={workspace.recommendations}
          opportunities={workspace.opportunities}
          onFiltersChange={workspace.onFiltersChange}
          onApplyFilters={workspace.onApplyFilters}
          onResetFilters={workspace.onResetFilters}
          onSelectOpportunity={workspace.onSelectOpportunity}
          onStatus={workspace.onStatus}
        />
      );
    case "profile":
      return (
        <>
          <ProfileView
            userEmail={profile.userEmail}
            activeProfileExists={Boolean(workspace.activeProfile)}
            loading={profile.loading}
            profileForm={profile.profileForm}
            detailsForm={profile.detailsForm}
            keywordOptions={workspace.keywordOptions}
            countryOptions={workspace.countryOptions}
            onProfileChange={profile.onProfileChange}
            onDetailsChange={profile.onDetailsChange}
            onLoadDetails={profile.onLoadDetails}
            onSaveProfile={profile.onSaveProfile}
            onSaveDetails={profile.onSaveDetails}
          />
          <ProfileImportsView
            orcidForm={profile.orcidForm}
            openAlexForm={profile.openAlexForm}
            onOrcidChange={profile.onOrcidChange}
            onOpenAlexChange={profile.onOpenAlexChange}
            onImportOrcid={profile.onImportOrcid}
            onImportOpenAlex={profile.onImportOpenAlex}
          />
        </>
      );
    case "board":
      return (
        <BoardView
          statuses={workspace.statuses}
          opportunitiesById={workspace.opportunitiesById}
          onSelectOpportunity={workspace.onSelectOpportunity}
        />
      );
    case "reminders":
      return (
        <RemindersView
          reminderForm={workspace.reminderForm}
          reminders={workspace.reminders}
          reminderEligibleOpportunities={workspace.reminderEligibleOpportunities}
          opportunitiesById={workspace.opportunitiesById}
          onReminderFormChange={workspace.onReminderFormChange}
          onCreateReminder={workspace.onCreateReminder}
          onCompleteReminder={workspace.onCompleteReminder}
        />
      );
    case "notifications":
      return (
        <NotificationsView
          notifications={notifications.notifications}
          notificationPrefs={notifications.notificationPrefs}
          onPrefsChange={notifications.onPrefsChange}
          onLoadNotifications={notifications.onLoadNotifications}
          onSavePrefs={notifications.onSavePrefs}
          onUnsubscribe={notifications.onUnsubscribe}
          onMarkRead={notifications.onMarkRead}
        />
      );
    case "assistant":
      return (
        <AssistantView
          assistantForm={assistant.assistantForm}
          assistantResult={assistant.assistantResult}
          reminderEligibleOpportunities={workspace.reminderEligibleOpportunities}
          onAssistantFormChange={assistant.onAssistantFormChange}
          onGenerate={assistant.onGenerateAssistant}
        />
      );
    case "admin":
      return (
        <AdminView
          importForm={admin.importForm}
          grantsForm={admin.grantsForm}
          externalForm={admin.externalForm}
          jobForm={admin.jobForm}
          queueStats={admin.queueStats}
          jobDetail={admin.jobDetail}
          adminData={admin.adminData}
          duplicateGroups={admin.duplicateGroups}
          auditLog={admin.auditLog}
          onImportFormChange={admin.onImportFormChange}
          onGrantsFormChange={admin.onGrantsFormChange}
          onExternalFormChange={admin.onExternalFormChange}
          onJobFormChange={admin.onJobFormChange}
          onEnqueueGrantsGov={admin.onEnqueueGrantsGov}
          onRunGrantsGovNow={admin.onRunGrantsGovNow}
          onRunBulkImport={admin.onRunBulkImport}
          onRunExternalImport={admin.onRunExternalImport}
          onLoadQueues={admin.onLoadQueues}
          onEnqueueReminderScan={admin.onEnqueueReminderScan}
          onEnqueueWeeklyDigest={admin.onEnqueueWeeklyDigest}
          onEnqueueHighMatchAlerts={admin.onEnqueueHighMatchAlerts}
          onEnqueueEmbeddingRefresh={admin.onEnqueueEmbeddingRefresh}
          onLoadJob={admin.onLoadJob}
          onLoadAdminOps={admin.onLoadAdminOps}
        />
      );
  }
}

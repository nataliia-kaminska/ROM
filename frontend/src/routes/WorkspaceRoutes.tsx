import { AdminView } from "../views/AdminView";
import { AssistantView } from "../views/AssistantView";
import { BoardView } from "../views/BoardView";
import { DashboardView } from "../views/DashboardView";
import { FeedView } from "../views/FeedView";
import { NotificationsView } from "../views/NotificationsView";
import { ProfileImportsView, ProfileView } from "../views/ProfileView";
import { RemindersView } from "../views/RemindersView";
import type { AdminController, AssistantController, NotificationsController, ProfileController, RouteController, WorkspaceController } from "./types";

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

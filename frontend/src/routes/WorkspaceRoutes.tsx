import { AdminView } from "../views/AdminView";
import { AboutView } from "../views/AboutView";
import { AccountSettingsView } from "../views/AccountSettingsView";
import { AssistantView } from "../views/AssistantView";
import { BoardView } from "../views/BoardView";
import { DashboardView } from "../views/DashboardView";
import { FeedView } from "../views/FeedView";
import { NotificationsView } from "../views/NotificationsView";
import { OpportunityDetailsView } from "../views/OpportunityDetailsView";
import { OrcidCallbackView } from "../views/OrcidCallbackView";
import { ProfileView } from "../views/ProfileView";
import { RemindersView } from "../views/RemindersView";
import { VerifyEmailView } from "../views/VerifyEmailView";
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
    case "auth":
      return null;
    case "verify_email":
      return <VerifyEmailView onViewChange={route.onViewChange} />;
    case "orcid_callback":
      return <OrcidCallbackView onViewChange={route.onViewChange} />;
    case "about":
      return <AboutView isSignedIn={workspace.isSignedIn} onViewChange={route.onViewChange} />;
    case "dashboard":
      return (
        <DashboardView
          nextAction={workspace.nextAction}
          topMatches={workspace.topMatches}
          plannedStatuses={workspace.plannedStatuses}
          statuses={workspace.statuses}
          nextReminder={workspace.nextReminder}
          opportunitiesById={workspace.opportunitiesById}
          canTrack={Boolean(workspace.activeProfile)}
          onViewChange={route.onViewChange}
          onProfileFocus={workspace.onProfileFocus}
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
          isSignedIn={workspace.isSignedIn}
          activeProfile={Boolean(workspace.activeProfile)}
          recommendations={workspace.recommendations}
          opportunities={workspace.opportunities}
          page={workspace.matchesPage}
          hasNextPage={workspace.matchesHasNextPage}
          totalPages={workspace.matchesTotalPages}
          totalIsEstimate={workspace.matchesTotalIsEstimate}
          onFiltersChange={workspace.onFiltersChange}
          onResetFilters={workspace.onResetFilters}
          onPageChange={workspace.onMatchesPageChange}
          onViewChange={route.onViewChange}
          onSelectOpportunity={workspace.onSelectOpportunity}
          onStatus={workspace.onStatus}
        />
      );
    case "opportunity":
      return (
        <OpportunityDetailsView
          opportunity={workspace.opportunitiesById.get(route.opportunityId ?? 0) ?? null}
          recommendation={workspace.recommendations.find((item) => item.opportunity.id === route.opportunityId) ?? null}
          reminders={workspace.reminders.filter((reminder) => reminder.opportunity_id === route.opportunityId)}
          assistantResult={assistant.assistantResult}
          status={workspace.statuses.find((item) => item.opportunity_id === route.opportunityId) ?? null}
          canTrack={Boolean(workspace.activeProfile)}
          onStatus={workspace.onStatus}
          onViewChange={route.onViewChange}
          onAssistantSelect={(opportunityId) => {
            assistant.onAssistantFormChange({ opportunity_id: String(opportunityId) });
            route.onViewChange("assistant");
          }}
        />
      );
    case "profile":
      return (
        <ProfileView
          userEmail={profile.userEmail}
          userFullName={profile.userFullName}
          userAuthProvider={profile.userAuthProvider}
          userOrcidId={profile.userOrcidId}
          activeProfileExists={Boolean(workspace.activeProfile)}
          loading={profile.loading}
          profileForm={profile.profileForm}
          detailsForm={profile.detailsForm}
          keywordOptions={workspace.keywordOptions}
          disciplineOptions={workspace.disciplineOptions}
          countryOptions={workspace.countryOptions}
          orcidForm={profile.orcidForm}
          openAlexForm={profile.openAlexForm}
          openAlexPreview={profile.openAlexPreview}
          profileDiscoveryCandidates={profile.profileDiscoveryCandidates}
          profileDiscoveryConfirmed={profile.profileDiscoveryConfirmed}
          profileDiscoveryLoading={profile.profileDiscoveryLoading}
          highlightFields={profile.highlightFields}
          onProfileChange={profile.onProfileChange}
          onDetailsChange={profile.onDetailsChange}
          onSaveProfile={profile.onSaveProfile}
          onSaveDetails={profile.onSaveDetails}
          onOrcidChange={profile.onOrcidChange}
          onOpenAlexChange={profile.onOpenAlexChange}
          onImportOrcid={profile.onImportOrcid}
          onImportOpenAlex={profile.onImportOpenAlex}
          onPreviewOpenAlex={profile.onPreviewOpenAlex}
          onDiscoverProfileCandidates={profile.onDiscoverProfileCandidates}
          onApplyProfileCandidate={profile.onApplyProfileCandidate}
          onDismissProfileCandidate={profile.onDismissProfileCandidate}
          onOpenAccountSettings={() => route.onViewChange("account")}
        />
      );
    case "account":
      return (
        <AccountSettingsView
          accountForm={profile.accountForm}
          passwordForm={profile.passwordForm}
          loading={profile.loading}
          userAuthProvider={profile.userAuthProvider}
          userOrcidId={profile.userOrcidId}
          passwordLoginEnabled={profile.passwordLoginEnabled}
          notifications={notifications.notifications}
          notificationPrefs={notifications.notificationPrefs}
          onAccountChange={profile.onAccountChange}
          onPasswordChange={profile.onPasswordChange}
          onSaveAccount={profile.onSaveAccount}
          onSavePassword={profile.onSavePassword}
          onPrefsChange={notifications.onPrefsChange}
          onSavePrefs={notifications.onSavePrefs}
          onUnsubscribe={notifications.onUnsubscribe}
          onMarkRead={notifications.onMarkRead}
        />
      );
    case "board":
      return (
        <BoardView
          statuses={workspace.statuses}
          opportunitiesById={workspace.opportunitiesById}
          onSelectOpportunity={workspace.onSelectOpportunity}
          onStatus={workspace.onStatus}
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
          assistantLoading={assistant.assistantLoading}
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
          euFundingForm={admin.euFundingForm}
          externalForm={admin.externalForm}
          jobForm={admin.jobForm}
          queueStats={admin.queueStats}
          jobDetail={admin.jobDetail}
          adminData={admin.adminData}
          duplicateGroups={admin.duplicateGroups}
          auditLog={admin.auditLog}
          adminBusy={admin.adminBusy}
          onImportFormChange={admin.onImportFormChange}
          onGrantsFormChange={admin.onGrantsFormChange}
          onEuFundingFormChange={admin.onEuFundingFormChange}
          onExternalFormChange={admin.onExternalFormChange}
          onJobFormChange={admin.onJobFormChange}
          onEnqueueGrantsGov={admin.onEnqueueGrantsGov}
          onRunGrantsGovNow={admin.onRunGrantsGovNow}
          onRunEuFundingTenders={admin.onRunEuFundingTenders}
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

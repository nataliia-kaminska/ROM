import { useEffect, useState } from "react";
import { api } from "./api";
import { OpportunityDrawer } from "./components/opportunities";
import { AppShell, AuthScreen } from "./components/layout";
import { useAdminOps } from "./hooks/useAdminOps";
import { useApplicationAssistant } from "./hooks/useApplicationAssistant";
import { useAppRoute } from "./hooks/useAppRoute";
import { useNotifications } from "./hooks/useNotifications";
import { useProfileForms } from "./hooks/useProfileForms";
import { useSession } from "./hooks/useSession";
import { useWorkspace } from "./hooks/useWorkspace";
import { useWorkspaceSelectors } from "./hooks/useWorkspaceSelectors";
import { WorkspaceRoutes } from "./routes/WorkspaceRoutes";

function App() {
  const { view, navigateTo } = useAppRoute();
  const [notice, setNotice] = useState("");

  const {
    token,
    user,
    authMode,
    authForm,
    profiles,
    activeProfileId,
    loading,
    error,
    setAuthMode,
    setAuthForm,
    setActiveProfileId,
    setError,
    setLoading,
    loadSession,
    submitAuth,
    logout,
  } = useSession();

  const activeProfile = profiles.find((profile) => profile.id === activeProfileId) ?? profiles[0] ?? null;

  const workspace = useWorkspace({
    token,
    activeProfile,
    setError,
    setNotice,
  });

  const notifications = useNotifications({
    token,
    setError,
    setNotice,
  });

  const admin = useAdminOps({
    token,
    activeProfile,
    setError,
    setNotice,
    refreshWorkspace: workspace.refreshWorkspace,
  });

  const profile = useProfileForms({
    token,
    user,
    activeProfile,
    setActiveProfileId,
    setLoading,
    setError,
    setNotice,
    loadSession,
    refreshWorkspace: workspace.refreshWorkspace,
  });

  const assistant = useApplicationAssistant({
    token,
    activeProfile,
    selectedStatusIds: workspace.selectedStatusIds,
    setError,
  });

  const {
    selectedRecommendation,
    selectedOpportunityReminders,
    statusByOpportunity,
    opportunitiesById,
    selectedStatusIds,
    reminderEligibleOpportunities,
    sourceOptions,
    countryOptions,
    keywordOptions,
    visibleViews,
    topMatches,
    plannedStatuses,
    nextReminder,
    nextAction,
  } = useWorkspaceSelectors({
    activeProfileId,
    profiles,
    recommendations: workspace.recommendations,
    opportunities: workspace.opportunities,
    selectedOpportunity: workspace.selectedOpportunity,
    statuses: workspace.statuses,
    reminders: workspace.reminders,
    user,
    detailsForm: profile.detailsForm,
    assistantResult: assistant.assistantResult,
  });

  useEffect(() => {
    void loadSession();
  }, []);

  useEffect(() => {
    if (token) {
      void workspace.refreshWorkspace(activeProfile);
    }
  }, [token, activeProfileId]);

  useEffect(() => {
    if (!token || !user) return;
    if (view === "admin" && user.role !== "admin") {
      navigateTo("dashboard", true);
    }
  }, [token, user, view]);

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  function handleLogout() {
    logout();
    workspace.clearWorkspace();
  }

  if (!token || !user) {
    return (
      <AuthScreen
        authMode={authMode}
        authForm={authForm}
        error={error}
        loading={loading}
        onSubmit={submitAuth}
        onAuthFormChange={setAuthForm}
        onAuthModeChange={setAuthMode}
      />
    );
  }

  return (
    <AppShell
      apiBaseUrl={api.baseUrl}
      user={user}
      activeProfile={activeProfile}
      detailsForm={profile.detailsForm}
      view={view}
      visibleViews={visibleViews}
      workspaceLoading={workspace.workspaceLoading}
      notice={notice}
      error={error}
      onViewChange={navigateTo}
      onRefresh={() => void workspace.refreshWorkspace(activeProfile)}
      onLogout={handleLogout}
    >
      <WorkspaceRoutes
        route={{ view, onViewChange: navigateTo }}
        workspace={{
          activeProfile,
          workspaceLoading: workspace.workspaceLoading,
          filters: workspace.filters,
          recommendations: workspace.recommendations,
          opportunities: workspace.opportunities,
          statuses: workspace.statuses,
          reminders: workspace.reminders,
          reminderForm: workspace.reminderForm,
          nextAction,
          topMatches,
          plannedStatuses,
          nextReminder,
          opportunitiesById,
          reminderEligibleOpportunities,
          sourceOptions,
          countryOptions,
          keywordOptions,
          onSelectOpportunity: workspace.setSelectedOpportunity,
          onStatus: (opportunityId, status) => void workspace.updateStatus(opportunityId, status),
          onFiltersChange: workspace.setFilters,
          onApplyFilters: () => void workspace.refreshWorkspace(activeProfile),
          onResetFilters: workspace.resetFilters,
          onReminderFormChange: workspace.setReminderForm,
          onCreateReminder: workspace.createReminder,
          onCompleteReminder: (reminderId) => void workspace.completeReminder(reminderId),
        }}
        profile={{
          userEmail: user.email,
          loading,
          profileForm: profile.profileForm,
          detailsForm: profile.detailsForm,
          orcidForm: profile.orcidForm,
          openAlexForm: profile.openAlexForm,
          onProfileChange: profile.setProfileForm,
          onDetailsChange: profile.setDetailsForm,
          onLoadDetails: () => void profile.loadDetails(),
          onSaveProfile: profile.saveProfile,
          onSaveDetails: profile.saveDetails,
          onOrcidChange: profile.setOrcidForm,
          onOpenAlexChange: profile.setOpenAlexForm,
          onImportOrcid: profile.importOrcid,
          onImportOpenAlex: profile.importOpenAlex,
        }}
        notifications={{
          notifications: notifications.notifications,
          notificationPrefs: notifications.notificationPrefs,
          onPrefsChange: notifications.setNotificationPrefs,
          onLoadNotifications: () => void notifications.loadNotifications(),
          onSavePrefs: notifications.saveNotificationPrefs,
          onUnsubscribe: () => void notifications.unsubscribe(),
          onMarkRead: (notificationId) => void notifications.markRead(notificationId),
        }}
        assistant={{
          assistantForm: assistant.assistantForm,
          assistantResult: assistant.assistantResult,
          onAssistantFormChange: assistant.setAssistantForm,
          onGenerateAssistant: assistant.generateApplicationNotes,
        }}
        admin={{
          importForm: admin.importForm,
          grantsForm: admin.grantsForm,
          externalForm: admin.externalForm,
          jobForm: admin.jobForm,
          queueStats: admin.queueStats,
          jobDetail: admin.jobDetail,
          adminData: admin.adminData,
          duplicateGroups: admin.duplicateGroups,
          auditLog: admin.auditLog,
          onImportFormChange: admin.setImportForm,
          onGrantsFormChange: admin.setGrantsForm,
          onExternalFormChange: admin.setExternalForm,
          onJobFormChange: admin.setJobForm,
          onEnqueueGrantsGov: admin.enqueueGrantsGov,
          onRunGrantsGovNow: (event) => void admin.runGrantsGov(event),
          onRunBulkImport: admin.runBulkImport,
          onRunExternalImport: admin.runExternalImport,
          onLoadQueues: () => void admin.loadQueues(),
          onEnqueueReminderScan: () => void admin.enqueueReminderScan(),
          onEnqueueWeeklyDigest: () => void admin.enqueueWeeklyDigest(),
          onEnqueueHighMatchAlerts: () => void admin.enqueueHighMatchAlerts(),
          onEnqueueEmbeddingRefresh: () => void admin.enqueueEmbeddingRefresh(),
          onLoadJob: admin.loadJob,
          onLoadAdminOps: () => void admin.loadAdminOps(),
        }}
      />
      {workspace.selectedOpportunity && (
        <OpportunityDrawer
          selectedOpportunity={workspace.selectedOpportunity}
          selectedRecommendation={selectedRecommendation}
          selectedOpportunityReminders={selectedOpportunityReminders}
          assistantResult={assistant.assistantResult}
          selectedStatusIds={selectedStatusIds}
          statusByOpportunity={statusByOpportunity}
          detailTab={workspace.detailTab}
          setDetailTab={workspace.setDetailTab}
          onClose={() => workspace.setSelectedOpportunity(null)}
          onStatus={(opportunityId, status) => void workspace.updateStatus(opportunityId, status)}
          setAssistantForm={assistant.setAssistantForm}
          setView={navigateTo}
        />
      )}
    </AppShell>
  );
}

export default App;

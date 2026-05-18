import { useEffect, useState } from "react";
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
import { OrcidCallbackView } from "./views/OrcidCallbackView";
import { VerifyEmailView } from "./views/VerifyEmailView";

function App() {
  const { view, navigateTo } = useAppRoute();
  const [notice, setNotice] = useState("");
  const [guestMode, setGuestMode] = useState(false);
  const [profileHighlights, setProfileHighlights] = useState<string[]>([]);

  const {
    token,
    user,
    authMode,
    authForm,
    authNotice,
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
    setError,
    setNotice,
    refreshCatalogOptions: () => workspace.loadFilterOptions(true),
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
    disciplineOptions,
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
    const workspaceViews = new Set(["dashboard", "feed", "board", "assistant", "reminders"]);
    if ((token || guestMode) && workspaceViews.has(view)) {
      void workspace.refreshWorkspace(activeProfile, workspace.filters, 1);
    }
  }, [token, guestMode, activeProfileId, view]);

  useEffect(() => {
    const guestViews = new Set(["about", "feed"]);
    if (guestMode && !guestViews.has(view)) {
      navigateTo("feed", true);
      return;
    }
    if (!token || !user) return;
    if (view === "admin" && user.role !== "admin") {
      navigateTo("dashboard", true);
    }
  }, [guestMode, token, user, view]);

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  function handleLogout() {
    setGuestMode(false);
    logout();
    workspace.clearWorkspace();
  }

  function enterGuestMode() {
    setGuestMode(true);
    setError("");
    workspace.clearWorkspace();
    navigateTo("feed", true);
  }

  if ((!token || !user) && !guestMode) {
    if (view === "orcid_callback") {
      return <OrcidCallbackView onViewChange={navigateTo} />;
    }
    if (view === "verify_email") {
      return <VerifyEmailView onViewChange={navigateTo} />;
    }
    return (
      <AuthScreen
        authMode={authMode}
        authForm={authForm}
        authNotice={authNotice}
        error={error}
        loading={loading}
        onSubmit={submitAuth}
        onAuthFormChange={setAuthForm}
        onAuthModeChange={setAuthMode}
        onContinueAsGuest={enterGuestMode}
      />
    );
  }

  return (
    <AppShell
      user={user}
      isGuest={guestMode}
      activeProfile={activeProfile}
      detailsForm={profile.detailsForm}
      view={view}
      visibleViews={visibleViews}
      notice={notice}
      error={error}
      onViewChange={navigateTo}
      onLogout={handleLogout}
    >
      <WorkspaceRoutes
        route={{ view, onViewChange: navigateTo }}
        workspace={{
          activeProfile,
          isSignedIn: Boolean(token && user),
          workspaceLoading: workspace.workspaceLoading,
          filters: workspace.filters,
          recommendations: workspace.recommendations,
          opportunities: workspace.opportunities,
          matchesPage: workspace.matchesPage,
          matchesHasNextPage: workspace.matchesHasNextPage,
          statuses: workspace.statuses,
          reminders: workspace.reminders,
          reminderForm: workspace.reminderForm,
          nextAction,
          topMatches,
          plannedStatuses,
          nextReminder,
          opportunitiesById,
          reminderEligibleOpportunities,
          sourceOptions: workspace.filterOptions.sources.length ? workspace.filterOptions.sources : sourceOptions,
          countryOptions: workspace.filterOptions.countries.length ? workspace.filterOptions.countries : countryOptions,
          disciplineOptions: workspace.filterOptions.disciplines.length ? workspace.filterOptions.disciplines : disciplineOptions,
          keywordOptions: workspace.filterOptions.keywords.length ? workspace.filterOptions.keywords : keywordOptions,
          onProfileFocus: setProfileHighlights,
          onSelectOpportunity: workspace.setSelectedOpportunity,
          onStatus: (opportunityId, status) => void workspace.updateStatus(opportunityId, status),
          onFiltersChange: workspace.setFilters,
          onResetFilters: workspace.resetFilters,
          onMatchesPageChange: workspace.goToMatchesPage,
          onReminderFormChange: workspace.setReminderForm,
          onCreateReminder: workspace.createReminder,
          onCompleteReminder: (reminderId) => void workspace.completeReminder(reminderId),
        }}
        profile={{
          userEmail: user?.email ?? "",
          userFullName: user?.full_name ?? "",
          loading,
          profileForm: profile.profileForm,
          detailsForm: profile.detailsForm,
          orcidForm: profile.orcidForm,
          openAlexForm: profile.openAlexForm,
          onProfileChange: profile.setProfileForm,
          onDetailsChange: profile.setDetailsForm,
          onLoadDetails: () => void profile.loadDetails(),
          highlightFields: profileHighlights,
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
          euFundingForm: admin.euFundingForm,
          externalForm: admin.externalForm,
          jobForm: admin.jobForm,
          queueStats: admin.queueStats,
          jobDetail: admin.jobDetail,
          adminData: admin.adminData,
          duplicateGroups: admin.duplicateGroups,
          auditLog: admin.auditLog,
          adminBusy: admin.adminBusy,
          onImportFormChange: admin.setImportForm,
          onGrantsFormChange: admin.setGrantsForm,
          onEuFundingFormChange: admin.setEuFundingForm,
          onExternalFormChange: admin.setExternalForm,
          onJobFormChange: admin.setJobForm,
          onEnqueueGrantsGov: admin.enqueueGrantsGov,
          onRunGrantsGovNow: (event) => void admin.runGrantsGov(event),
          onRunEuFundingTenders: (event) => void admin.runEuFundingTenders(event),
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

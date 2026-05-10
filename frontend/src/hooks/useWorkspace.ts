import { type FormEvent, useMemo, useState } from "react";
import { api } from "../api";
import { defaultFilters, reminderStatuses, type DetailTab } from "../constants";
import type { Opportunity, OpportunityStatus, Profile, Recommendation, Reminder, StatusRecord } from "../types";
import { label } from "../utils/format";

const PAGE_SIZE = 20;

export function useWorkspace({
  token,
  activeProfile,
  setError,
  setNotice,
}: {
  token: string | null;
  activeProfile: Profile | null;
  setError: (message: string) => void;
  setNotice: (message: string) => void;
}) {
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [filters, setFilters] = useState(defaultFilters);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [matchesPage, setMatchesPage] = useState(1);
  const [matchesHasNextPage, setMatchesHasNextPage] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("overview");
  const [statuses, setStatuses] = useState<StatusRecord[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [reminderForm, setReminderForm] = useState({ opportunity_id: "", remind_on: "", message: "" });
  const selectedStatusIds = useMemo(
    () => new Set(statuses.filter((record) => reminderStatuses.includes(record.status)).map((record) => record.opportunity_id)),
    [statuses],
  );

  async function refreshWorkspace(profile = activeProfile, nextFilters = filters, page = matchesPage) {
    setError("");
    setWorkspaceLoading(true);
    try {
      const limit = PAGE_SIZE + 1;
      const offset = (page - 1) * PAGE_SIZE;
      const opportunityQuery = {
        keyword: nextFilters.keyword,
        opportunity_type: nextFilters.opportunity_type,
        country: nextFilters.country,
        career_stage: nextFilters.career_stage,
        source: nextFilters.source,
        active_only: nextFilters.active_only,
        limit,
        offset,
      };
      const catalogPromise = api.opportunities(opportunityQuery);
      if (token && profile) {
        const recommendationPromise = api
          .recommendations(token, profile.id, {
            min_score: nextFilters.min_score,
            include_ignored: nextFilters.include_ignored,
            limit,
            offset,
          })
          .catch((recommendationError) => {
            setError(`Personalized matching is temporarily unavailable. Showing catalog results instead. ${(recommendationError as Error).message}`);
            return [] as Recommendation[];
          });
        const [nextRecommendations, nextStatuses, nextReminders, nextOpportunities] = await Promise.all([
          recommendationPromise,
          api.statuses(token, profile.id),
          api.reminders(token, profile.id, true),
          catalogPromise,
        ]);
        setRecommendations(nextRecommendations.slice(0, PAGE_SIZE));
        setStatuses(nextStatuses);
        setReminders(nextReminders);
        setOpportunities(nextOpportunities.slice(0, PAGE_SIZE));
        setMatchesHasNextPage((nextRecommendations.length > 0 ? nextRecommendations : nextOpportunities).length > PAGE_SIZE);
      } else {
        const nextOpportunities = await catalogPromise;
        setOpportunities(nextOpportunities.slice(0, PAGE_SIZE));
        setMatchesHasNextPage(nextOpportunities.length > PAGE_SIZE);
      }
      setMatchesPage(page);
    } catch (workspaceError) {
      setError((workspaceError as Error).message);
    } finally {
      setWorkspaceLoading(false);
    }
  }

  function resetFilters() {
    setFilters(defaultFilters);
    void refreshWorkspace(activeProfile, defaultFilters, 1);
  }

  function applyFilters() {
    void refreshWorkspace(activeProfile, filters, 1);
  }

  function goToMatchesPage(page: number) {
    if (page < 1 || workspaceLoading) return;
    void refreshWorkspace(activeProfile, filters, page);
  }

  function clearWorkspace() {
    setRecommendations([]);
    setStatuses([]);
    setReminders([]);
    setSelectedOpportunity(null);
    setMatchesPage(1);
    setMatchesHasNextPage(false);
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

  return {
    workspaceLoading,
    filters,
    recommendations,
    opportunities,
    selectedOpportunity,
    matchesPage,
    matchesHasNextPage,
    detailTab,
    statuses,
    reminders,
    reminderForm,
    selectedStatusIds,
    setFilters,
    setRecommendations,
    setSelectedOpportunity,
    setDetailTab,
    setReminderForm,
    refreshWorkspace,
    resetFilters,
    applyFilters,
    goToMatchesPage,
    clearWorkspace,
    updateStatus,
    createReminder,
    completeReminder,
  };
}

import { type FormEvent, useMemo, useRef, useState } from "react";
import { api } from "../api";
import { defaultFilters, reminderStatuses } from "../constants";
import type { DisplayOpportunityStatus, Opportunity, Profile, Recommendation, Reminder, StatusRecord } from "../types";
import { label } from "../utils/format";

const PAGE_SIZE = 18;

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
  const [filters, setFiltersState] = useState(defaultFilters);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [trackedOpportunities, setTrackedOpportunities] = useState<Opportunity[]>([]);
  const [matchesPage, setMatchesPage] = useState(1);
  const [matchesHasNextPage, setMatchesHasNextPage] = useState(false);
  const [matchesTotalPages, setMatchesTotalPages] = useState(1);
  const [matchesTotalIsEstimate, setMatchesTotalIsEstimate] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [statuses, setStatuses] = useState<StatusRecord[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [filterOptions, setFilterOptions] = useState({ sources: [] as string[], countries: [] as string[], keywords: [] as string[], disciplines: [] as string[], career_stages: [] as string[] });
  const [reminderForm, setReminderForm] = useState({ opportunity_id: "", remind_on: "", message: "" });
  const loadedWorkspaceKey = useRef("");
  const requestSequence = useRef(0);
  const currentStatuses = useMemo(() => latestStatusesByOpportunity(statuses), [statuses]);
  const selectedStatusIds = useMemo(
    () => new Set(currentStatuses.filter((record) => reminderStatuses.includes(record.status)).map((record) => record.opportunity_id)),
    [currentStatuses],
  );

  async function refreshWorkspace(
    profile = activeProfile,
    nextFilters = filters,
    page = matchesPage,
    options: { force?: boolean } = {},
  ) {
    const workspaceKey = buildWorkspaceKey(token, profile?.id ?? null, nextFilters, page);
    if (!options.force && loadedWorkspaceKey.current === workspaceKey && (recommendations.length > 0 || opportunities.length > 0)) {
      return;
    }
    const sequence = requestSequence.current + 1;
    requestSequence.current = sequence;
    setError("");
    setWorkspaceLoading(true);
    try {
      const limit = PAGE_SIZE;
      const offset = (page - 1) * PAGE_SIZE;
      const opportunityQuery = {
        keyword: nextFilters.keyword,
        opportunity_type: nextFilters.opportunity_type,
        country: nextFilters.country,
        career_stage: nextFilters.career_stage,
        source: nextFilters.source,
        active_only: nextFilters.active_only,
        sort_by: nextFilters.sort_by === "match_score" || nextFilters.sort_by === "semantic_score" || nextFilters.sort_by === "readiness_score" ? "deadline" : nextFilters.sort_by,
        sort_order: nextFilters.sort_order,
        limit,
        offset,
      };
      const catalogPromise = api.opportunitiesPage(opportunityQuery);
      void loadFilterOptions();
      if (token && profile) {
        const recommendationLimit = PAGE_SIZE + 1;
        const recommendationPromise = api
          .recommendations(token, profile.id, {
            min_score: nextFilters.min_score,
            include_ignored: nextFilters.include_ignored,
            keyword: nextFilters.keyword,
            opportunity_type: nextFilters.opportunity_type,
            country: nextFilters.country,
            career_stage: nextFilters.career_stage,
            source: nextFilters.source,
            active_only: nextFilters.active_only,
            sort_by: nextFilters.sort_by,
            sort_order: nextFilters.sort_order,
            limit: recommendationLimit,
            offset,
          })
          .catch((recommendationError) => {
            setError(`Personalized matching is temporarily unavailable. Showing catalog results instead. ${(recommendationError as Error).message}`);
            return [] as Recommendation[];
          });
        const [nextRecommendations, nextStatuses, nextReminders, nextOpportunitiesPage] = await Promise.all([
          recommendationPromise,
          api.statuses(token, profile.id),
          api.reminders(token, profile.id, true),
          catalogPromise,
        ]);
        if (requestSequence.current !== sequence) return;
        const nextTrackedOpportunities = await loadTrackedOpportunities(
          nextStatuses,
          [...nextOpportunitiesPage.items, ...nextRecommendations.map((item) => item.opportunity)],
        );
        if (requestSequence.current !== sequence) return;
        const hasPersonalizedResults = nextRecommendations.length > 0;
        const hasMoreRecommendations = nextRecommendations.length > PAGE_SIZE;
        const total = hasPersonalizedResults ? offset + nextRecommendations.length : nextOpportunitiesPage.total;
        setRecommendations(nextRecommendations.slice(0, PAGE_SIZE));
        setStatuses(nextStatuses);
        setReminders(nextReminders);
        setTrackedOpportunities(nextTrackedOpportunities);
        setOpportunities(nextOpportunitiesPage.items);
        setMatchesHasNextPage(hasPersonalizedResults ? hasMoreRecommendations : offset + PAGE_SIZE < total);
        setMatchesTotalPages(hasPersonalizedResults ? page + (hasMoreRecommendations ? 1 : 0) : Math.max(1, Math.ceil(total / PAGE_SIZE)));
        setMatchesTotalIsEstimate(hasPersonalizedResults && hasMoreRecommendations);
      } else {
        const nextOpportunitiesPage = await catalogPromise;
        if (requestSequence.current !== sequence) return;
        setOpportunities(nextOpportunitiesPage.items);
        setMatchesHasNextPage(offset + PAGE_SIZE < nextOpportunitiesPage.total);
        setMatchesTotalPages(Math.max(1, Math.ceil(nextOpportunitiesPage.total / PAGE_SIZE)));
        setMatchesTotalIsEstimate(false);
      }
      setMatchesPage(page);
      loadedWorkspaceKey.current = workspaceKey;
    } catch (workspaceError) {
      if (requestSequence.current !== sequence) return;
      setError((workspaceError as Error).message);
    } finally {
      if (requestSequence.current === sequence) {
        setWorkspaceLoading(false);
      }
    }
  }

  function setFilters(nextFilters: typeof defaultFilters) {
    setFiltersState(nextFilters);
    void refreshWorkspace(activeProfile, nextFilters, 1);
  }

  function resetFilters() {
    setFiltersState(defaultFilters);
    void refreshWorkspace(activeProfile, defaultFilters, 1);
  }

  function goToMatchesPage(page: number) {
    if (page < 1 || workspaceLoading) return;
    void refreshWorkspace(activeProfile, filters, page);
  }

  function clearWorkspace() {
    setRecommendations([]);
    setStatuses([]);
    setReminders([]);
    setTrackedOpportunities([]);
    setSelectedOpportunity(null);
    loadedWorkspaceKey.current = "";
    setMatchesPage(1);
    setMatchesHasNextPage(false);
    setMatchesTotalPages(1);
    setMatchesTotalIsEstimate(false);
  }

  async function loadFilterOptions(force = false) {
    if (!force && (filterOptions.sources.length || filterOptions.countries.length || filterOptions.keywords.length)) return;
    try {
      setFilterOptions(await api.opportunityOptions());
    } catch {
      // Filter suggestions are optional; the page can still render from loaded opportunities.
    }
  }

  async function updateStatus(opportunityId: number, status: DisplayOpportunityStatus) {
    if (!token || !activeProfile) return;
    setError("");
    try {
      if (status === "browsing") {
        await api.clearStatus(token, activeProfile.id, opportunityId);
        setStatuses((current) => current.filter((item) => item.opportunity_id !== opportunityId));
        setRecommendations((current) =>
          current.map((item) => (item.opportunity.id === opportunityId ? { ...item, user_status: null } : item)),
        );
        setNotice("Opportunity moved back to browsing.");
        return;
      }
      const updated = await api.setStatus(token, activeProfile.id, opportunityId, status);
      setStatuses((current) => {
        const others = current.filter((item) => item.opportunity_id !== opportunityId);
        return [...others, updated];
      });
      setRecommendations((current) =>
        current.map((item) => (item.opportunity.id === opportunityId ? { ...item, user_status: status } : item)),
      );
      setNotice(`Opportunity moved to ${label(status)}.`);
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
      const reminder = await api.createReminder(token, activeProfile.id, {
        opportunity_id: Number(reminderForm.opportunity_id),
        remind_on: reminderForm.remind_on,
        message: reminderForm.message,
      });
      setReminderForm({ opportunity_id: "", remind_on: "", message: "" });
      setReminders((current) => [...current.filter((item) => item.id !== reminder.id), reminder]);
      setNotice("Reminder created");
    } catch (reminderError) {
      setError((reminderError as Error).message);
    }
  }

  async function completeReminder(reminderId: number) {
    if (!token || !activeProfile) return;
    setError("");
    try {
      const reminder = await api.completeReminder(token, activeProfile.id, reminderId);
      setReminders((current) => current.map((item) => (item.id === reminderId ? reminder : item)));
      setNotice("Reminder completed");
    } catch (reminderError) {
      setError((reminderError as Error).message);
    }
  }

  return {
    workspaceLoading,
    filters,
    recommendations,
    opportunities,
    trackedOpportunities,
    selectedOpportunity,
    matchesPage,
    matchesHasNextPage,
    matchesTotalPages,
    matchesTotalIsEstimate,
    statuses,
    reminders,
    filterOptions,
    reminderForm,
    selectedStatusIds,
    setFilters,
    setRecommendations,
    setSelectedOpportunity,
    setReminderForm,
    refreshWorkspace,
    resetFilters,
    goToMatchesPage,
    clearWorkspace,
    loadFilterOptions,
    updateStatus,
    createReminder,
    completeReminder,
  };
}

async function loadTrackedOpportunities(statuses: StatusRecord[], knownOpportunities: Opportunity[]): Promise<Opportunity[]> {
  const knownIds = new Set(knownOpportunities.map((opportunity) => opportunity.id));
  const missingIds = latestStatusesByOpportunity(statuses)
    .map((status) => status.opportunity_id)
    .filter((id, index, ids) => !knownIds.has(id) && ids.indexOf(id) === index);
  const loaded = await Promise.all(
    missingIds.map((id) =>
      api
        .opportunity(id)
        .catch(() => null),
    ),
  );
  return loaded.filter((opportunity): opportunity is Opportunity => Boolean(opportunity));
}

function latestStatusesByOpportunity(statuses: StatusRecord[]): StatusRecord[] {
  const byOpportunity = new Map<number, StatusRecord>();
  for (const status of statuses) {
    const current = byOpportunity.get(status.opportunity_id);
    if (!current || status.id > current.id) {
      byOpportunity.set(status.opportunity_id, status);
    }
  }
  return [...byOpportunity.values()];
}

function buildWorkspaceKey(
  token: string | null,
  profileId: number | null,
  filters: typeof defaultFilters,
  page: number,
): string {
  return JSON.stringify({
    auth: Boolean(token),
    profileId,
    page,
    filters,
  });
}

import { useMemo } from "react";
import type { ProfileDetailsPayload } from "../api";
import { reminderStatuses, researcherViews, type View } from "../constants";
import { curatedDisciplines, curatedKeywords, mergeSuggestions } from "../suggestions";
import type { ApplicationAssistantResult, Opportunity, Profile, Recommendation, Reminder, StatusRecord, User } from "../types";

export function useWorkspaceSelectors({
  activeProfileId,
  profiles,
  recommendations,
  opportunities,
  trackedOpportunities,
  selectedOpportunity,
  statuses,
  reminders,
  user,
  detailsForm,
  assistantResult,
}: {
  activeProfileId: number | null;
  profiles: Profile[];
  recommendations: Recommendation[];
  opportunities: Opportunity[];
  trackedOpportunities: Opportunity[];
  selectedOpportunity: Opportunity | null;
  statuses: StatusRecord[];
  reminders: Reminder[];
  user: User | null;
  detailsForm: ProfileDetailsPayload;
  assistantResult: ApplicationAssistantResult | null;
}) {
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
  const currentStatuses = useMemo(() => latestStatusesByOpportunity(statuses), [statuses]);
  const statusByOpportunity = useMemo(
    () => new Map(currentStatuses.map((status) => [status.opportunity_id, status])),
    [currentStatuses],
  );
  const opportunitiesById = useMemo(
    () => new Map([...opportunities, ...trackedOpportunities, ...recommendations.map((item) => item.opportunity)].map((item) => [item.id, item])),
    [opportunities, recommendations, trackedOpportunities],
  );
  const selectedStatusIds = useMemo(
    () => new Set(currentStatuses.filter((record) => reminderStatuses.includes(record.status)).map((record) => record.opportunity_id)),
    [currentStatuses],
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
  const disciplineOptions = useMemo(
    () => mergeSuggestions(curatedDisciplines, [...opportunitiesById.values()].flatMap((opportunity) => opportunity.disciplines)),
    [opportunitiesById],
  );
  const keywordOptions = useMemo(
    () => mergeSuggestions(curatedKeywords, [...opportunitiesById.values()].flatMap((opportunity) => opportunity.keywords)),
    [opportunitiesById],
  );
  const visibleViews = useMemo(
    () => {
      if (!user) return ["about" as const, "feed" as const];
      return user.role === "admin" ? [...researcherViews, "admin" as const] : [...researcherViews];
    },
    [user?.role],
  );
  const topMatches = useMemo(() => recommendations.slice(0, 3), [recommendations]);
  const plannedStatuses = useMemo(
    () => currentStatuses.filter((status) => ["planned", "applied"].includes(status.status)),
    [currentStatuses],
  );
  const nextReminder = useMemo(
    () => reminders.filter((reminder) => reminder.status === "pending").sort((a, b) => a.remind_on.localeCompare(b.remind_on))[0] ?? null,
    [reminders],
  );
  const nextAction = useMemo(() => {
    if (!activeProfile) return { title: "Create your research profile", detail: "Start with career stage, country, disciplines, and keywords.", target: "profile" as View, focusFields: ["career_stage", "country", "disciplines", "keywords"] };
    if (!activeProfile.country || activeProfile.disciplines.length === 0 || activeProfile.keywords.length === 0) {
      return {
        title: "Complete your profile basics",
        detail: "Country, disciplines, and keywords make the match explanations much better.",
        target: "profile" as View,
        focusFields: [
          ...(!activeProfile.country ? ["country"] : []),
          ...(activeProfile.disciplines.length === 0 ? ["disciplines"] : []),
          ...(activeProfile.keywords.length === 0 ? ["keywords"] : []),
        ],
      };
    }
    if (!detailsForm.research_summary || detailsForm.publications.length === 0) {
      return {
        title: "Add evidence for readiness scoring",
        detail: "Research summary and publications improve advisor gaps and fit statements.",
        target: "profile" as View,
        focusFields: [
          ...(!detailsForm.research_summary ? ["research_summary"] : []),
          ...(detailsForm.publications.length === 0 ? ["publications"] : []),
        ],
      };
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

  return {
    activeProfile,
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
  };
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

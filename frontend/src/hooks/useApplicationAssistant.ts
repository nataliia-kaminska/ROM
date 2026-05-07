import { type FormEvent, useState } from "react";
import { api } from "../api";
import type { ApplicationAssistantResult, Profile } from "../types";

export function useApplicationAssistant({
  token,
  activeProfile,
  selectedStatusIds,
  setError,
}: {
  token: string | null;
  activeProfile: Profile | null;
  selectedStatusIds: ReadonlySet<number>;
  setError: (message: string) => void;
}) {
  const [assistantForm, setAssistantForm] = useState({ opportunity_id: "" });
  const [assistantResult, setAssistantResult] = useState<ApplicationAssistantResult | null>(null);

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

  return {
    assistantForm,
    assistantResult,
    setAssistantForm,
    generateApplicationNotes,
  };
}

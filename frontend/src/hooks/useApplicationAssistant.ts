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
  const [assistantLoading, setAssistantLoading] = useState(false);

  function updateAssistantForm(nextForm: { opportunity_id: string }) {
    setAssistantForm((current) => {
      if (current.opportunity_id !== nextForm.opportunity_id) {
        setAssistantResult(null);
        setAssistantLoading(false);
      }
      return nextForm;
    });
  }

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
    const opportunityId = Number(assistantForm.opportunity_id);
    if (assistantLoading || assistantResult?.opportunity_id === opportunityId) return;
    setError("");
    setAssistantLoading(true);
    try {
      setAssistantResult(await api.applicationAssistant(token, { profile_id: activeProfile.id, opportunity_id: opportunityId }));
    } catch (assistantError) {
      setError((assistantError as Error).message);
    } finally {
      setAssistantLoading(false);
    }
  }

  return {
    assistantForm,
    assistantResult,
    assistantLoading,
    setAssistantForm: updateAssistantForm,
    generateApplicationNotes,
  };
}

import type { Reminder } from "../types";
import { request } from "./client";

export const remindersApi = {
  reminders: (token: string, profileId: number, includeCompleted = false) =>
    request<Reminder[]>(`/profiles/${profileId}/reminders`, {
      token,
      query: { include_completed: includeCompleted },
    }),
  createReminder: (token: string, profileId: number, body: { opportunity_id: number; remind_on: string; message: string }) =>
    request<Reminder>(`/profiles/${profileId}/reminders`, { token, method: "POST", body }),
  completeReminder: (token: string, profileId: number, reminderId: number) =>
    request<Reminder>(`/profiles/${profileId}/reminders/${reminderId}/complete`, { token, method: "PUT" }),
};

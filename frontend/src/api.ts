import { adminApi } from "./api/admin";
import { assistantApi } from "./api/assistant";
import { authApi } from "./api/auth";
import { API_BASE_URL } from "./api/client";
import { notificationsApi } from "./api/notifications";
import { opportunitiesApi } from "./api/opportunities";
import { profilesApi } from "./api/profiles";
import { remindersApi } from "./api/reminders";

export type { OpportunityPayload, ProfileDetailsPayload, ProfilePayload } from "./api/payloads";

export const api = {
  baseUrl: API_BASE_URL,
  ...authApi,
  ...profilesApi,
  ...opportunitiesApi,
  ...remindersApi,
  ...notificationsApi,
  ...adminApi,
  ...assistantApi,
};

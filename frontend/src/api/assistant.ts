import type { ApplicationAssistantResult } from "../types";
import { request } from "./client";

export const assistantApi = {
  applicationAssistant: (token: string, body: { profile_id: number; opportunity_id: number }) =>
    request<ApplicationAssistantResult>("/application-assistant", { token, method: "POST", body }),
};

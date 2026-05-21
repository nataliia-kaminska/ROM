import type { CareerStage, OpenAlexPreview, Profile, ProfileDetails } from "../types";
import type { ProfileDetailsPayload, ProfilePayload } from "./payloads";
import { request } from "./client";

export const profilesApi = {
  profiles: (token: string) => request<Profile[]>("/profiles/me", { token }),
  createProfile: (token: string, body: ProfilePayload) => request<Profile>("/profiles", { token, method: "POST", body }),
  updateProfile: (token: string, profileId: number, body: ProfilePayload) =>
    request<Profile>(`/profiles/${profileId}`, { token, method: "PUT", body }),
  getProfileDetails: (token: string, profileId: number) =>
    request<ProfileDetails>(`/profiles/${profileId}/details`, { token }),
  saveProfileDetails: (token: string, profileId: number, body: ProfileDetailsPayload) =>
    request<ProfileDetails>(`/profiles/${profileId}/details`, { token, method: "PUT", body }),
  importOrcid: (
    token: string,
    body: {
      orcid_id: string;
      email: string | null;
      career_stage: CareerStage;
      disciplines: string[];
      preferred_countries: string[];
    },
  ) => request<{ imported: boolean; profile: Profile; preview: Record<string, unknown> }>("/integrations/orcid/import", {
    token,
    method: "POST",
    body,
  }),
  importOpenAlex: (
    token: string,
    body: { profile_id: number; openalex_author_id?: string | null; orcid_id?: string | null; max_works: number },
  ) =>
    request<{ profile: Profile; details: ProfileDetails; preview: OpenAlexPreview }>("/integrations/openalex/import", {
      token,
      method: "POST",
      body,
    }),
  previewOpenAlex: (
    token: string,
    body: { profile_id: number; openalex_author_id?: string | null; orcid_id?: string | null; max_works: number },
  ) =>
    request<OpenAlexPreview>("/integrations/openalex/preview", {
      token,
      method: "POST",
      body,
    }),
};

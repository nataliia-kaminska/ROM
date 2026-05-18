import type { AuthProviderConfig, AuthResponse, RegisterResponse, User } from "../types";
import { API_BASE_URL, request } from "./client";

export const authApi = {
  register: (body: { email: string; password: string; full_name: string }) =>
    request<RegisterResponse>("/auth/register", { method: "POST", body }),
  login: (body: { email: string; password: string }) => request<AuthResponse>("/auth/login", { method: "POST", body }),
  refresh: () => request<AuthResponse>("/auth/refresh", { method: "POST" }),
  logout: (token: string) => request<void>("/auth/logout", { token, method: "POST" }),
  verifyEmail: (token: string) => request<User>("/auth/verify-email", { method: "POST", body: { token } }),
  me: (token: string) => request<User>("/auth/me", { token }),
  authProviders: () => request<AuthProviderConfig>("/auth/providers"),
  orcidStartUrl: () => new URL("/auth/orcid/start", API_BASE_URL).toString(),
};

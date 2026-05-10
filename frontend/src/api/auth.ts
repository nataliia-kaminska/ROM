import type { AuthResponse, RegisterResponse, User } from "../types";
import { request } from "./client";

export const authApi = {
  register: (body: { email: string; password: string; full_name: string }) =>
    request<RegisterResponse>("/auth/register", { method: "POST", body }),
  login: (body: { email: string; password: string }) => request<AuthResponse>("/auth/login", { method: "POST", body }),
  verifyEmail: (token: string) => request<User>("/auth/verify-email", { method: "POST", body: { token } }),
  me: (token: string) => request<User>("/auth/me", { token }),
};

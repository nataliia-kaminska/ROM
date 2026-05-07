import type { AuthResponse, User } from "../types";
import { request } from "./client";

export const authApi = {
  register: (body: { email: string; password: string; full_name: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body }),
  login: (body: { email: string; password: string }) => request<AuthResponse>("/auth/login", { method: "POST", body }),
  me: (token: string) => request<User>("/auth/me", { token }),
};

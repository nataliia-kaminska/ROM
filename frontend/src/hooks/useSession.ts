import { type FormEvent, useState } from "react";
import { api } from "../api";
import type { Profile, User } from "../types";

type AuthMode = "login" | "register";
type AuthForm = { email: string; password: string; full_name: string };

export function useSession({ onLogout }: { onLogout?: () => void } = {}) {
  const [token, setToken] = useState(() => localStorage.getItem("rom_token"));
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authForm, setAuthForm] = useState<AuthForm>({ email: "", password: "", full_name: "" });
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadSession(nextToken = token, preferredProfileId = activeProfileId) {
    if (!nextToken) return;
    setLoading(true);
    setError("");
    try {
      const [me, ownedProfiles] = await Promise.all([api.me(nextToken), api.profiles(nextToken)]);
      setUser(me);
      setProfiles(ownedProfiles);
      const chosen = ownedProfiles.find((profile) => profile.id === preferredProfileId) ?? ownedProfiles[0] ?? null;
      setActiveProfileId(chosen?.id ?? null);
    } catch (sessionError) {
      setError((sessionError as Error).message);
      logout();
    } finally {
      setLoading(false);
    }
  }

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    if (!authForm.email || !authForm.password || (authMode === "register" && !authForm.full_name)) {
      setError("Email, password, and name are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response =
        authMode === "register"
          ? await api.register(authForm)
          : await api.login({ email: authForm.email, password: authForm.password });
      localStorage.setItem("rom_token", response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      await loadSession(response.access_token);
    } catch (authError) {
      setError((authError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("rom_token");
    setToken(null);
    setUser(null);
    setProfiles([]);
    setActiveProfileId(null);
    onLogout?.();
  }

  return {
    token,
    user,
    authMode,
    authForm,
    profiles,
    activeProfileId,
    loading,
    error,
    setAuthMode,
    setAuthForm,
    setActiveProfileId,
    setError,
    setLoading,
    setUser,
    loadSession,
    submitAuth,
    logout,
  };
}

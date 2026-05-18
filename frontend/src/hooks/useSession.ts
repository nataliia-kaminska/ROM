import { type FormEvent, useState } from "react";
import { api } from "../api";
import type { Profile, User } from "../types";

type AuthMode = "login" | "register";
type AuthForm = { email: string; password: string; confirm_password: string; full_name: string };

export function useSession({ onLogout }: { onLogout?: () => void } = {}) {
  const [token, setToken] = useState(() => sessionStorage.getItem("rom_access_token") ?? localStorage.getItem("rom_token"));
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authForm, setAuthForm] = useState<AuthForm>({ email: "", password: "", confirm_password: "", full_name: "" });
  const [authNotice, setAuthNotice] = useState("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadSession(nextToken = token, preferredProfileId = activeProfileId) {
    setLoading(true);
    setError("");
    try {
      let effectiveToken = nextToken;
      if (!effectiveToken) {
        try {
          effectiveToken = (await api.refresh()).access_token;
        } catch {
          return;
        }
      }
      persistAccessToken(effectiveToken);
      let me: User;
      let ownedProfiles: Profile[];
      try {
        [me, ownedProfiles] = await Promise.all([api.me(effectiveToken), api.profiles(effectiveToken)]);
      } catch {
        const refreshed = await api.refresh();
        effectiveToken = refreshed.access_token;
        persistAccessToken(effectiveToken);
        [me, ownedProfiles] = await Promise.all([api.me(effectiveToken), api.profiles(effectiveToken)]);
      }
      const availableProfiles = ownedProfiles.length > 0 ? ownedProfiles : [await createStarterProfile(effectiveToken, me)];
      setToken(effectiveToken);
      setUser(me);
      setProfiles(availableProfiles);
      const chosen = availableProfiles.find((profile) => profile.id === preferredProfileId) ?? availableProfiles[0] ?? null;
      setActiveProfileId(chosen?.id ?? null);
    } catch (sessionError) {
      setError((sessionError as Error).message);
      logout();
    } finally {
      setLoading(false);
    }
  }

  async function createStarterProfile(nextToken: string, me: User) {
    return api.createProfile(nextToken, {
      full_name: me.full_name || me.email,
      email: me.auth_provider === "orcid" ? null : me.email,
      career_stage: "phd",
      country: null,
      disciplines: [],
      keywords: [],
      preferred_countries: [],
      orcid_id: null,
      google_scholar_url: null,
      linkedin_url: null,
    });
  }

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    if (!authForm.email || !authForm.password || (authMode === "register" && !authForm.full_name)) {
      setError("Email, password, and name are required.");
      return;
    }
    if (authMode === "register") {
      const fullNameError = validateFullName(authForm.full_name);
      if (fullNameError) {
        setError(fullNameError);
        return;
      }
      if (authForm.password !== authForm.confirm_password) {
        setError("Password confirmation must match the password.");
        return;
      }
    }
    setLoading(true);
    setError("");
    try {
      if (authMode === "register") {
        const response = await api.register({ email: authForm.email, password: authForm.password, full_name: authForm.full_name.trim() });
        setAuthNotice(response.message);
        setAuthMode("login");
        setAuthForm({ email: response.email, password: "", confirm_password: "", full_name: "" });
        return;
      }
      const response = await api.login({ email: authForm.email, password: authForm.password });
      persistAccessToken(response.access_token);
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
    if (token) void api.logout(token).catch(() => undefined);
    sessionStorage.removeItem("rom_access_token");
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
    authNotice,
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

function persistAccessToken(value: string) {
  sessionStorage.setItem("rom_access_token", value);
  localStorage.removeItem("rom_token");
}

function validateFullName(value: string): string {
  const normalized = value.trim().replace(/\s+/g, " ");
  if (normalized.length < 3) return "Full name must be at least 3 characters.";
  if (!normalized.includes(" ")) return "Please enter at least first and last name.";
  if (!/^[A-Za-zÀ-žА-Яа-яІіЇїЄєҐґ' -]+$/.test(normalized)) return "Full name can contain only letters, spaces, hyphens, and apostrophes.";
  return "";
}

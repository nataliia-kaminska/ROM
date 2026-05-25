import { type FormEvent, useEffect, useState } from "react";
import { api, type ProfileDetailsPayload, type ProfilePayload } from "../api";
import { blankDetails, blankProfile, defaultFilters } from "../constants";
import type { CareerStage, OpenAlexPreview, Profile, ProfileDiscoveryCandidate, User } from "../types";
import { normalizeText, normalizeUrl, splitList } from "../utils/format";

export function useProfileForms({
  token,
  user,
  activeProfile,
  setActiveProfileId,
  setLoading,
  setError,
  setNotice,
  loadSession,
  refreshWorkspace,
}: {
  token: string | null;
  user: User | null;
  activeProfile: Profile | null;
  setActiveProfileId: (profileId: number | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (message: string) => void;
  setNotice: (message: string) => void;
  loadSession: (token?: string | null, preferredProfileId?: number | null) => Promise<void>;
  refreshWorkspace: (profile?: Profile | null, nextFilters?: typeof defaultFilters, page?: number, options?: { force?: boolean }) => Promise<void>;
}) {
  const [profileForm, setProfileForm] = useState<ProfilePayload>(blankProfile);
  const [detailsForm, setDetailsForm] = useState<ProfileDetailsPayload>(blankDetails);
  const [orcidForm, setOrcidForm] = useState({
    orcid_id: "",
    email: "",
    career_stage: "phd" as CareerStage,
    disciplines: "",
    preferred_countries: "",
  });
  const [openAlexForm, setOpenAlexForm] = useState({ openalex_author_id: "", orcid_id: "", max_works: 10 });
  const [openAlexPreview, setOpenAlexPreview] = useState<OpenAlexPreview | null>(null);
  const [profileDiscoveryCandidates, setProfileDiscoveryCandidates] = useState<ProfileDiscoveryCandidate[]>([]);
  const [profileDiscoveryConfirmed, setProfileDiscoveryConfirmed] = useState<ProfileDiscoveryCandidate[]>([]);
  const [profileDiscoveryLoading, setProfileDiscoveryLoading] = useState(false);
  const [accountForm, setAccountForm] = useState({ full_name: "", email: "" });
  const [passwordForm, setPasswordForm] = useState({ current_password: "", new_password: "", confirm_password: "" });

  useEffect(() => {
    setAccountForm({ full_name: user?.full_name ?? "", email: user?.email ?? "" });
  }, [user?.email, user?.full_name]);

  useEffect(() => {
    if (!activeProfile) {
      setProfileForm({
        ...blankProfile,
        full_name: user?.full_name ?? "",
        email: user?.email ?? "",
      });
      setProfileDiscoveryCandidates([]);
      setProfileDiscoveryConfirmed([]);
      return;
    }
    setProfileForm({
      full_name: user?.full_name || activeProfile.full_name,
      email: activeProfile.email,
      career_stage: activeProfile.career_stage,
      country: activeProfile.country,
      disciplines: activeProfile.disciplines,
      keywords: activeProfile.keywords,
      preferred_countries: activeProfile.preferred_countries,
      orcid_id: activeProfile.orcid_id,
      google_scholar_url: activeProfile.google_scholar_url,
      linkedin_url: activeProfile.linkedin_url,
    });
    setOrcidForm((current) => ({
      ...current,
      orcid_id: activeProfile.orcid_id ?? user?.orcid_id ?? "",
      email: activeProfile.email ?? user?.email ?? "",
      career_stage: activeProfile.career_stage,
      disciplines: activeProfile.disciplines.join(", "),
      preferred_countries: activeProfile.preferred_countries.join(", "),
    }));
    setOpenAlexForm((current) => ({ ...current, orcid_id: activeProfile.orcid_id ?? user?.orcid_id ?? current.orcid_id }));
    setProfileDiscoveryCandidates([]);
    setProfileDiscoveryConfirmed(readProfileDiscoveryReviews(activeProfile.id).filter((item) => item.decision === "confirmed").map((item) => item.candidate));
  }, [activeProfile?.id, user?.email, user?.full_name]);

  useEffect(() => {
    if (!token || !activeProfile) {
      setDetailsForm(blankDetails);
      return;
    }
    void loadDetails();
  }, [token, activeProfile?.id]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    const accountName = normalizeText(user?.full_name ?? null) ?? normalizeText(profileForm.full_name);
    const homeCountry = normalizeText(profileForm.country);
    if (!accountName || !profileForm.career_stage || !homeCountry) {
      setError("Account name, career stage, and home country are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...profileForm,
        full_name: accountName,
        email: user?.email ?? normalizeText(profileForm.email),
        country: homeCountry,
        orcid_id: normalizeText(profileForm.orcid_id),
        google_scholar_url: normalizeUrl(profileForm.google_scholar_url),
        linkedin_url: normalizeUrl(profileForm.linkedin_url),
      };
      const profile = activeProfile
        ? await api.updateProfile(token, activeProfile.id, payload)
        : await api.createProfile(token, payload);
      setNotice(activeProfile ? "Profile updated" : "Profile created");
      setActiveProfileId(profile.id);
      await loadSession(token, profile.id);
      await refreshWorkspace(profile, undefined, undefined, { force: true });
    } catch (profileError) {
      setError((profileError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails() {
    if (!token || !activeProfile) return;
    setError("");
    try {
      const details = await api.getProfileDetails(token, activeProfile.id);
      setDetailsForm({
        research_summary: details.research_summary,
        publications: details.publications,
        degrees: details.degrees,
        languages: details.languages,
        funding_interests: details.funding_interests,
        unavailable_countries: details.unavailable_countries,
        preferred_opportunity_types: details.preferred_opportunity_types,
        min_duration_months: details.min_duration_months,
        max_duration_months: details.max_duration_months,
      });
    } catch {
      setDetailsForm(blankDetails);
    }
  }

  async function saveAccount(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (user?.auth_provider === "orcid") {
      setError("Name and email are managed by ORCID for this account.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.updateMe(token, { full_name: accountForm.full_name, email: accountForm.email });
      setNotice("Account updated");
      await loadSession(token, activeProfile?.id ?? null);
    } catch (accountError) {
      setError((accountError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function savePassword(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError("Password confirmation must match the new password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.updatePassword(token, {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      setNotice("Password updated");
      await loadSession(token, activeProfile?.id ?? null);
    } catch (passwordError) {
      setError((passwordError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function saveDetails(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setLoading(true);
    setError("");
    try {
      await api.saveProfileDetails(token, activeProfile.id, detailsForm);
      setNotice("Profile details saved");
      await refreshWorkspace(activeProfile, undefined, undefined, { force: true });
    } catch (detailsError) {
      setError((detailsError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function importOrcid(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.importOrcid(token, {
        orcid_id: orcidForm.orcid_id,
        email: normalizeText(orcidForm.email),
        career_stage: orcidForm.career_stage,
        disciplines: splitList(orcidForm.disciplines),
        preferred_countries: splitList(orcidForm.preferred_countries),
      });
      setNotice(result.imported ? "ORCID profile imported" : "ORCID profile enriched");
      setActiveProfileId(result.profile.id);
      await loadSession(token, result.profile.id);
    } catch (orcidError) {
      setError((orcidError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function importOpenAlex(event?: FormEvent) {
    event?.preventDefault();
    if (!token || !activeProfile) return;
    setLoading(true);
    setError("");
    try {
      await api.importOpenAlex(token, {
        profile_id: activeProfile.id,
        openalex_author_id: normalizeText(openAlexForm.openalex_author_id),
        orcid_id: normalizeText(openAlexForm.orcid_id) ?? activeProfile.orcid_id,
        max_works: openAlexForm.max_works,
      });
      setOpenAlexPreview(null);
      setNotice("OpenAlex profile data imported");
      await loadSession(token);
      await loadDetails();
      await refreshWorkspace(activeProfile, undefined, undefined, { force: true });
    } catch (openAlexError) {
      setError((openAlexError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function previewOpenAlex(event: FormEvent) {
    event.preventDefault();
    if (!token || !activeProfile) return;
    setLoading(true);
    setError("");
    try {
      const preview = await api.previewOpenAlex(token, {
        profile_id: activeProfile.id,
        openalex_author_id: normalizeText(openAlexForm.openalex_author_id),
        orcid_id: normalizeText(openAlexForm.orcid_id) ?? activeProfile.orcid_id,
        max_works: openAlexForm.max_works,
      });
      setOpenAlexPreview(preview);
      setNotice("OpenAlex preview ready");
    } catch (openAlexError) {
      setError((openAlexError as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function discoverProfileCandidates() {
    if (!token || !activeProfile) return;
    setProfileDiscoveryLoading(true);
    setError("");
    try {
      const candidates = await api.discoverProfileCandidates(token, activeProfile.id, 3);
      const reviewed = new Set(readProfileDiscoveryReviews(activeProfile.id).map((item) => item.candidate.url));
      const freshCandidates = candidates.filter((candidate) => !reviewed.has(candidate.url));
      setProfileDiscoveryCandidates(freshCandidates);
      setNotice(freshCandidates.length ? "Profile evidence suggestions ready" : "No new confident public profile suggestions found");
    } catch (discoveryError) {
      setError((discoveryError as Error).message);
    } finally {
      setProfileDiscoveryLoading(false);
    }
  }

  async function applyProfileCandidate(candidate: ProfileDiscoveryCandidate) {
    if (!token || !activeProfile) return;
    setProfileDiscoveryLoading(true);
    setError("");
    try {
      const result = await api.applyProfileCandidate(token, activeProfile.id, {
        title: candidate.title,
        url: candidate.url,
        snippet: candidate.snippet,
      });
      setProfileDiscoveryCandidates((current) => current.filter((item) => item.url !== candidate.url));
      rememberProfileDiscoveryReview(activeProfile.id, candidate, "confirmed");
      setProfileDiscoveryConfirmed(readProfileDiscoveryReviews(activeProfile.id).filter((item) => item.decision === "confirmed").map((item) => item.candidate));
      setDetailsForm({
        research_summary: result.details.research_summary,
        publications: result.details.publications,
        degrees: result.details.degrees,
        languages: result.details.languages,
        funding_interests: result.details.funding_interests,
        unavailable_countries: result.details.unavailable_countries,
        preferred_opportunity_types: result.details.preferred_opportunity_types,
        min_duration_months: result.details.min_duration_months,
        max_duration_months: result.details.max_duration_months,
      });
      setNotice(`Profile enriched from public evidence: ${result.applied_fields.join(", ")}`);
      setActiveProfileId(result.profile.id);
      await loadSession(token, result.profile.id);
      await refreshWorkspace(result.profile, undefined, undefined, { force: true });
    } catch (discoveryError) {
      setError((discoveryError as Error).message);
    } finally {
      setProfileDiscoveryLoading(false);
    }
  }

  function dismissProfileCandidate(candidate: ProfileDiscoveryCandidate) {
    if (activeProfile) {
      rememberProfileDiscoveryReview(activeProfile.id, candidate, "dismissed");
    }
    setProfileDiscoveryCandidates((current) => current.filter((item) => item.url !== candidate.url));
  }

  return {
    profileForm,
    detailsForm,
    orcidForm,
    openAlexForm,
    openAlexPreview,
    profileDiscoveryCandidates,
    profileDiscoveryConfirmed,
    profileDiscoveryLoading,
    accountForm,
    passwordForm,
    setProfileForm,
    setDetailsForm,
    setOrcidForm,
    setOpenAlexForm,
    setAccountForm,
    setPasswordForm,
    saveAccount,
    savePassword,
    saveProfile,
    loadDetails,
    saveDetails,
    importOrcid,
    importOpenAlex,
    previewOpenAlex,
    discoverProfileCandidates,
    applyProfileCandidate,
    dismissProfileCandidate,
  };
}

type ProfileDiscoveryReview = {
  candidate: ProfileDiscoveryCandidate;
  decision: "confirmed" | "dismissed";
};

function discoveryReviewKey(profileId: number): string {
  return `rom.profileDiscovery.reviewed.${profileId}`;
}

function readProfileDiscoveryReviews(profileId: number): ProfileDiscoveryReview[] {
  try {
    const raw = window.localStorage.getItem(discoveryReviewKey(profileId));
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function rememberProfileDiscoveryReview(profileId: number, candidate: ProfileDiscoveryCandidate, decision: ProfileDiscoveryReview["decision"]) {
  const current = readProfileDiscoveryReviews(profileId).filter((item) => item.candidate.url !== candidate.url);
  window.localStorage.setItem(discoveryReviewKey(profileId), JSON.stringify([{ candidate, decision }, ...current].slice(0, 20)));
}

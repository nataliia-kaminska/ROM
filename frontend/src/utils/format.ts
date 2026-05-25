import type { DisplayOpportunityStatus, Opportunity, Profile } from "../types";
import type { View } from "../constants";

export function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinList(value: string[] | undefined): string {
  return (value ?? []).join(", ");
}

export function label(value: string): string {
  return value.replaceAll("_", " ");
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value.includes("T") ? value : `${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${day}.${month}.${date.getFullYear()}`;
}

export function deadlineLabel(value: string | null | undefined): string {
  return value ? `Due ${formatDate(value)}` : "No deadline";
}

export function addedLabel(value: string | null | undefined): string {
  return value ? `Added ${formatDate(value)}` : "Added date unknown";
}

export function viewLabel(value: View): string {
  const labels: Record<View, string> = {
    dashboard: "Dashboard",
    auth: "Sign In",
    feed: "Matches",
    profile: "Profile",
    account: "Account Settings",
    board: "Application Board",
    assistant: "Apply Assistant",
    about: "How It Works",
    verify_email: "Verify Email",
    orcid_callback: "ORCID Sign In",
    reminders: "Application Reminders",
    notifications: "Notification Center",
    admin: "Admin",
    opportunity: "Opportunity Details",
  };
  return labels[value];
}

export function statusHelp(status: DisplayOpportunityStatus): string {
  const descriptions: Record<DisplayOpportunityStatus, string> = {
    browsing: "No action yet. You are only viewing this opportunity.",
    saved: "Interesting, maybe later.",
    planned: "You intend to apply.",
    applied: "Application submitted.",
    accepted: "Accepted or awarded.",
    rejected: "Not selected.",
    ignored: "Hidden and used as ranking feedback.",
  };
  return descriptions[status];
}

export function profileLabel(profile: Profile, fallbackEmail?: string): string {
  return profile.full_name || profile.email || fallbackEmail || `Profile ${profile.id}`;
}

export function normalizeUrl(value: string | null): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed === "" ? null : trimmed;
}

export function normalizeText(value: string | null): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed === "" ? null : trimmed;
}

export function opportunitySummary(opportunity: Opportunity): string {
  if (opportunity.summary?.trim()) return opportunity.summary;
  const snippet = [
    ...(opportunity.extracted_requirements?.key_details ?? []),
    ...(opportunity.extracted_requirements?.snippets ?? []),
  ].find((item) => item.trim());
  if (snippet) return snippet;
  const tags = [...opportunity.disciplines, ...opportunity.keywords].slice(0, 4);
  if (tags.length) return `Opportunity related to ${tags.join(", ")}. Open the source page for the full programme text.`;
  return "Open the source page for the full opportunity description.";
}

export function opportunityEligibility(opportunity: Opportunity): string {
  if (opportunity.eligibility?.trim()) return opportunity.eligibility;
  const requirements = opportunity.extracted_requirements;
  const parts = [
    requirements?.career_stages.length ? `Career stage: ${requirements.career_stages.join(", ")}` : "",
    requirements?.countries.length ? `Location or eligibility region: ${requirements.countries.join(", ")}` : "",
    requirements?.required_degree ? `Degree: ${requirements.required_degree}` : "",
    requirements?.languages.length ? `Languages: ${requirements.languages.join(", ")}` : "",
  ].filter(Boolean);
  if (parts.length) return parts.join(". ");
  return "Eligibility details were not available in the imported record. Check the source page before planning an application.";
}

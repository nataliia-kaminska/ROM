import type { OpportunityStatus, Profile } from "../types";
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

export function viewLabel(value: View): string {
  const labels: Record<View, string> = {
    dashboard: "Dashboard",
    feed: "Matches",
    profile: "Profile",
    board: "Application Board",
    assistant: "Apply Assistant",
    about: "How It Works",
    verify_email: "Verify Email",
    orcid_callback: "ORCID Sign In",
    reminders: "Application Reminders",
    notifications: "Notification Center",
    admin: "Admin",
  };
  return labels[value];
}

export function statusHelp(status: OpportunityStatus): string {
  const descriptions: Record<OpportunityStatus, string> = {
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

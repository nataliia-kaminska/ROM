import type { FormEvent, ReactNode } from "react";
import type { ProfileDetailsPayload } from "../api";
import { viewRoutes, type View } from "../constants";
import type { Profile, User } from "../types";
import { profileLabel, viewLabel } from "../utils/format";
import { ActionButton, Field, ProfileCompleteness, ToastStack } from "./ui";

export function AuthScreen({
  authMode,
  authForm,
  authNotice,
  error,
  loading,
  onSubmit,
  onAuthFormChange,
  onAuthModeChange,
  onContinueAsGuest,
}: {
  authMode: "login" | "register";
  authForm: { email: string; password: string; confirm_password: string; full_name: string };
  authNotice: string;
  error: string;
  loading: boolean;
  onSubmit: (event: FormEvent) => void;
  onAuthFormChange: (form: { email: string; password: string; confirm_password: string; full_name: string }) => void;
  onAuthModeChange: (mode: "login" | "register") => void;
  onContinueAsGuest: () => void;
}) {
  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Research Opportunity Matcher</p>
          <h1>{authMode === "login" ? "Welcome back" : "Create your research account"}</h1>
          <p className="muted">Discover, rank, save, and plan academic opportunities from one focused workspace.</p>
        </div>
        <form className="grid-form" onSubmit={onSubmit}>
          {authMode === "register" && (
            <Field labelText="Full name" value={authForm.full_name} onChange={(full_name) => onAuthFormChange({ ...authForm, full_name })} />
          )}
          <Field labelText="Email" type="email" value={authForm.email} onChange={(email) => onAuthFormChange({ ...authForm, email })} />
          <Field labelText="Password" type="password" value={authForm.password} onChange={(password) => onAuthFormChange({ ...authForm, password })} />
          {authMode === "register" && (
            <Field labelText="Confirm password" type="password" value={authForm.confirm_password} onChange={(confirm_password) => onAuthFormChange({ ...authForm, confirm_password })} />
          )}
          {authNotice && <div className="alert success span-2">{authNotice}</div>}
          {error && <div className="alert error span-2">{error}</div>}
          <ActionButton busy={loading} variant="primary" className="span-2">
            {authMode === "login" ? "Sign in" : "Sign up"}
          </ActionButton>
        </form>
        <button className="ghost" onClick={() => onAuthModeChange(authMode === "login" ? "register" : "login")}>
          {authMode === "login" ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
        <button className="secondary span-2" type="button" onClick={onContinueAsGuest}>
          Continue as guest
        </button>
      </section>
    </main>
  );
}

export function AppShell({
  user,
  isGuest,
  activeProfile,
  detailsForm,
  view,
  visibleViews,
  notice,
  error,
  onViewChange,
  onLogout,
  children,
}: {
  user: User | null;
  isGuest: boolean;
  activeProfile: Profile | null;
  detailsForm: ProfileDetailsPayload;
  view: View;
  visibleViews: readonly View[];
  notice: string;
  error: string;
  onViewChange: (view: View) => void;
  onLogout: () => void;
  children: ReactNode;
}) {
  const title = view === "about" ? "Research Opportunity Matcher" : activeProfile ? profileLabel(activeProfile, user?.email) : isGuest ? "Browse opportunities" : "Create your first profile";
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark">ROM</span>
          <div>
            <strong>Research Matcher</strong>
          </div>
        </div>
        <nav>
          {visibleViews.map((item) => (
            <a
              key={item}
              className={view === item ? "active" : ""}
              href={viewRoutes[item]}
              onClick={(event) => {
                event.preventDefault();
                onViewChange(item);
              }}
            >
              {viewLabel(item)}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="account-summary">
            <small>{isGuest ? "Guest access" : "Signed in"}</small>
            <span>{isGuest ? "Browsing public catalog" : user?.email}</span>
            {activeProfile && <small>Profile: {profileLabel(activeProfile, user?.email)}</small>}
          </div>
          <button className="ghost" onClick={onLogout}>
            {isGuest ? "Back to sign in" : "Sign out"}
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{viewLabel(view)}</p>
            <h1>{title}</h1>
          </div>
        </header>
        {!isGuest && <ProfileCompleteness profile={activeProfile} details={detailsForm} />}
        {isGuest && (
          <div className="alert guest-callout">
            Create an account to get personalized recommendations, save opportunities, plan applications, and receive reminders.
          </div>
        )}

        {children}
      </section>
      <ToastStack notice={notice} error={error} />
    </main>
  );
}

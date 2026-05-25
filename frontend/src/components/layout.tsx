import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { api, type ProfileDetailsPayload } from "../api";
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
  const [orcidEnabled, setOrcidEnabled] = useState(false);

  useEffect(() => {
    let mounted = true;
    api
      .authProviders()
      .then((providers) => {
        if (mounted) setOrcidEnabled(providers.orcid_oauth_enabled);
      })
      .catch(() => {
        if (mounted) setOrcidEnabled(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

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
        {orcidEnabled && (
          <>
            <div className="auth-divider">
              <span>or</span>
            </div>
            <button className="secondary span-2" type="button" onClick={() => { window.location.href = api.orcidStartUrl(); }}>
              Sign in with ORCID
            </button>
          </>
        )}
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
  onAccountSettings,
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
  onAccountSettings: () => void;
  onLogout: () => void;
  children: ReactNode;
}) {
  const accountName = activeProfile ? profileLabel(activeProfile, user?.email) : user?.full_name || "Guest";
  const accountIdentity = isGuest ? "Browsing public catalog" : user?.email;
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark">ROM</span>
          <div>
            <strong>Research Opportunity Matcher</strong>
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
          {!isGuest && <ProfileCompleteness profile={activeProfile} details={detailsForm} />}
          <button className="account-summary" type="button" onClick={isGuest ? undefined : onAccountSettings}>
            <span>{accountName}</span>
            <small>{accountIdentity}</small>
          </button>
          <button className="ghost" onClick={onLogout}>
            {isGuest ? "Back to sign in" : "Sign out"}
          </button>
        </div>
      </aside>

      <section className="workspace">
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

import type { FormEvent, ReactNode } from "react";
import type { ProfileDetailsPayload } from "../api";
import { viewRoutes, type View } from "../constants";
import type { Profile, User } from "../types";
import { profileLabel, viewLabel } from "../utils/format";
import { ActionButton, Field, ProfileCompleteness } from "./ui";

export function AuthScreen({
  authMode,
  authForm,
  error,
  loading,
  onSubmit,
  onAuthFormChange,
  onAuthModeChange,
}: {
  authMode: "login" | "register";
  authForm: { email: string; password: string; full_name: string };
  error: string;
  loading: boolean;
  onSubmit: (event: FormEvent) => void;
  onAuthFormChange: (form: { email: string; password: string; full_name: string }) => void;
  onAuthModeChange: (mode: "login" | "register") => void;
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
          {error && <div className="alert error span-2">{error}</div>}
          <ActionButton busy={loading} variant="primary" className="span-2">
            {authMode === "login" ? "Sign in" : "Sign up"}
          </ActionButton>
        </form>
        <button className="ghost" onClick={() => onAuthModeChange(authMode === "login" ? "register" : "login")}>
          {authMode === "login" ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </section>
    </main>
  );
}

export function AppShell({
  apiBaseUrl,
  user,
  activeProfile,
  detailsForm,
  view,
  visibleViews,
  workspaceLoading,
  notice,
  error,
  onViewChange,
  onRefresh,
  onLogout,
  children,
}: {
  apiBaseUrl: string;
  user: User;
  activeProfile: Profile | null;
  detailsForm: ProfileDetailsPayload;
  view: View;
  visibleViews: readonly View[];
  workspaceLoading: boolean;
  notice: string;
  error: string;
  onViewChange: (view: View) => void;
  onRefresh: () => void;
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark">ROM</span>
          <div>
            <strong>Research Matcher</strong>
            <small>{apiBaseUrl}</small>
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
          {user.role !== "admin" && (
            <button disabled title="Admin tools are available only to users with the admin role. Current roles are researcher and admin.">
              Admin
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="account-summary">
            <small>Signed in</small>
            <span>{user.email}</span>
            <small>Role: {user.role}</small>
            {activeProfile && <small>Profile: {profileLabel(activeProfile, user.email)}</small>}
          </div>
          <button className="ghost" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{viewLabel(view)}</p>
            <h1>{activeProfile ? profileLabel(activeProfile, user.email) : "Create your first profile"}</h1>
          </div>
          <ActionButton busy={workspaceLoading} variant="secondary" type="button" onClick={onRefresh}>
            Refresh
          </ActionButton>
        </header>
        <ProfileCompleteness profile={activeProfile} details={detailsForm} />

        {notice && <div className="alert success">{notice}</div>}
        {error && <div className="alert error">{error}</div>}

        {children}
      </section>
    </main>
  );
}

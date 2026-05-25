import { useState, type FormEvent } from "react";
import { ActionButton, Field, PageHeader } from "../components/ui";
import type { NotificationItem, NotificationPreference } from "../types";
import { NotificationCenterContent } from "./NotificationsView";

type AccountTab = "account" | "notifications";

export function AccountSettingsView({
  accountForm,
  passwordForm,
  loading,
  userAuthProvider,
  userOrcidId,
  passwordLoginEnabled,
  notifications,
  notificationPrefs,
  onAccountChange,
  onPasswordChange,
  onSaveAccount,
  onSavePassword,
  onPrefsChange,
  onSavePrefs,
  onUnsubscribe,
  onMarkRead,
}: {
  accountForm: { full_name: string; email: string };
  passwordForm: { current_password: string; new_password: string; confirm_password: string };
  loading: boolean;
  userAuthProvider: string;
  userOrcidId: string | null;
  passwordLoginEnabled: boolean;
  notifications: NotificationItem[];
  notificationPrefs: NotificationPreference;
  onAccountChange: (form: { full_name: string; email: string }) => void;
  onPasswordChange: (form: { current_password: string; new_password: string; confirm_password: string }) => void;
  onSaveAccount: (event: FormEvent) => void;
  onSavePassword: (event: FormEvent) => void;
  onPrefsChange: (prefs: NotificationPreference) => void;
  onSavePrefs: (event: FormEvent) => void;
  onUnsubscribe: () => void;
  onMarkRead: (notificationId: number) => void;
}) {
  const [tab, setTab] = useState<AccountTab>("account");
  const isOrcidAccount = userAuthProvider === "orcid";

  return (
    <section className="account-settings-page">
      <PageHeader
        title="Account settings"
        description="Manage sign-in details, security, and communication preferences in one place."
        hint="ORCID accounts keep name, email, and ORCID iD locked to the identity provider."
      />

      <div className="panel">
      <nav className="tabs" aria-label="Account settings sections">
        <button className={tab === "account" ? "active" : ""} type="button" onClick={() => setTab("account")}>
          Account settings
        </button>
        <button className={tab === "notifications" ? "active" : ""} type="button" onClick={() => setTab("notifications")}>
          Notification center
        </button>
      </nav>

      {tab === "account" && (
        <div className="account-settings-grid separated">
          <form className="grid-form" onSubmit={onSaveAccount}>
            <div className="span-2 focus-strip">
              <strong>Account</strong>
              <span>{isOrcidAccount ? "Name, email, and ORCID iD come from ORCID sign-in." : "Update your display name and login email."}</span>
            </div>
            <Field labelText="Full name" value={accountForm.full_name} disabled={isOrcidAccount} onChange={(full_name) => onAccountChange({ ...accountForm, full_name })} />
            <Field labelText="Email" type="email" value={accountForm.email} disabled={isOrcidAccount} onChange={(email) => onAccountChange({ ...accountForm, email })} />
            {isOrcidAccount && <Field labelText="ORCID iD" value={userOrcidId ?? ""} disabled onChange={() => undefined} />}
            <ActionButton busy={loading} disabled={isOrcidAccount} className="span-2">
              Save account
            </ActionButton>
          </form>

          <form className="grid-form separated" onSubmit={onSavePassword}>
            <div className="span-2 focus-strip">
              <strong>Security</strong>
              <span>{passwordLoginEnabled ? "Change the password used for email sign-in." : "Password login is disabled for ORCID-only accounts."}</span>
            </div>
            <Field labelText="Current password" type="password" value={passwordForm.current_password} disabled={!passwordLoginEnabled} onChange={(current_password) => onPasswordChange({ ...passwordForm, current_password })} />
            <Field labelText="New password" type="password" value={passwordForm.new_password} disabled={!passwordLoginEnabled} onChange={(new_password) => onPasswordChange({ ...passwordForm, new_password })} />
            <Field labelText="Confirm new password" type="password" value={passwordForm.confirm_password} disabled={!passwordLoginEnabled} onChange={(confirm_password) => onPasswordChange({ ...passwordForm, confirm_password })} />
            <ActionButton busy={loading} disabled={!passwordLoginEnabled} className="span-2">
              Change password
            </ActionButton>
          </form>
        </div>
      )}

      {tab === "notifications" && (
        <div className="separated">
          <NotificationCenterContent
            notifications={notifications}
            notificationPrefs={notificationPrefs}
            onPrefsChange={onPrefsChange}
            onSavePrefs={onSavePrefs}
            onUnsubscribe={onUnsubscribe}
            onMarkRead={onMarkRead}
          />
        </div>
      )}
      </div>
    </section>
  );
}

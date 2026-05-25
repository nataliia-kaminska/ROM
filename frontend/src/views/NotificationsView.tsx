import { useState, type FormEvent } from "react";
import type { NotificationItem, NotificationPreference } from "../types";
import { formatDate, label } from "../utils/format";
import { EmptyState, HelpTip, PageHeader } from "../components/ui";

type NotificationsViewProps = {
  notifications: NotificationItem[];
  notificationPrefs: NotificationPreference;
  onPrefsChange: (prefs: NotificationPreference) => void;
  onSavePrefs: (event: FormEvent) => void;
  onUnsubscribe: () => void;
  onMarkRead: (notificationId: number) => void;
};

export function NotificationsView(props: NotificationsViewProps) {
  return (
    <section className="panel">
      <PageHeader
        title="Notification center"
        description="Review delivery history and tune proactive alerts without leaving account settings."
        hint="Email preferences affect generated digests, deadline reminders, and high-match alerts. In-app history remains visible here."
      />
      <NotificationCenterContent {...props} />
    </section>
  );
}

export function NotificationCenterContent({
  notifications,
  notificationPrefs,
  onPrefsChange,
  onSavePrefs,
  onUnsubscribe,
  onMarkRead,
}: NotificationsViewProps) {
  const [page, setPage] = useState(1);
  const pageSize = 6;
  const totalPages = Math.max(1, Math.ceil(notifications.length / pageSize));
  const visibleNotifications = notifications.slice((page - 1) * pageSize, page * pageSize);
  return (
    <>
      <form className="notification-layout" onSubmit={onSavePrefs}>
        <PreferenceSwitch icon="@" title="Email" detail="Allow outbound email delivery." checked={notificationPrefs.email_enabled} onChange={(email_enabled) => onPrefsChange({ ...notificationPrefs, email_enabled })} />
        <PreferenceSwitch icon="!" title="Deadlines" detail="Send reminders before important dates." checked={notificationPrefs.deadline_reminders_enabled} onChange={(deadline_reminders_enabled) => onPrefsChange({ ...notificationPrefs, deadline_reminders_enabled })} />
        <PreferenceSwitch icon="≋" title="Weekly digest" detail="Bundle new matches into a weekly update." checked={notificationPrefs.weekly_digest_enabled} onChange={(weekly_digest_enabled) => onPrefsChange({ ...notificationPrefs, weekly_digest_enabled })} />
        <PreferenceSwitch icon="★" title="High-match alerts" detail="Notify when strong personalized matches appear." checked={notificationPrefs.high_match_alerts_enabled} onChange={(high_match_alerts_enabled) => onPrefsChange({ ...notificationPrefs, high_match_alerts_enabled })} />
        <label className="field">
          <span>
            Minimum alert score <HelpTip text="High-match alerts only send when a recommendation score is at or above this number." />
          </span>
          <input
            type="number"
            min="0"
            max="100"
            value={String(notificationPrefs.min_alert_score)}
            onChange={(event) => onPrefsChange({ ...notificationPrefs, min_alert_score: Number(event.target.value) })}
          />
        </label>
        <div className="actions">
          <button className="primary">Save preferences</button>
          <button className="secondary" type="button" onClick={onUnsubscribe}>
            Unsubscribe
          </button>
        </div>
      </form>
      <div className="notification-list">
        {visibleNotifications.map((item) => (
          <article className={`notification-item ${item.status === "read" ? "read" : ""}`} key={item.id}>
            <span className="notification-icon">{notificationIcon(item.notification_type)}</span>
            <div>
              <strong>{item.subject}</strong>
              <p>{label(item.notification_type)} · {item.created_at ? formatDate(item.created_at) : "No date"}</p>
            </div>
            <span className={`notification-status-icon status-${item.status}`} title={label(item.status)} aria-label={label(item.status)}>
              {statusIcon(item.status)}
            </span>
            {item.status !== "read" && (
              <button className="secondary" onClick={() => onMarkRead(item.id)}>
                Mark read
              </button>
            )}
          </article>
        ))}
        {notifications.length === 0 && <EmptyState title="No notification history yet" detail="Deadline reminders, digests, and alerts will appear here once generated." />}
      </div>
      {notifications.length > pageSize && (
        <div className="pagination-bar pagination-bottom">
          <span>Page {page} of {totalPages}</span>
          <div className="actions">
            <button className="secondary" type="button" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>Previous</button>
            <button className="secondary" type="button" disabled={page === totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>Next</button>
          </div>
        </div>
      )}
    </>
  );
}

function PreferenceSwitch({ icon, title, detail, checked, onChange }: { icon: string; title: string; detail: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className={`preference-switch ${checked ? "active" : ""}`}>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{icon}</span>
      <div>
        <strong>{title}</strong>
        <small>{detail}</small>
      </div>
    </label>
  );
}

function notificationIcon(type: string): string {
  if (type.includes("deadline")) return "!";
  if (type.includes("digest")) return "≋";
  if (type.includes("match")) return "★";
  return "@";
}

function statusIcon(status: string): string {
  if (status === "sent" || status === "read") return "✓";
  if (status === "pending") return "…";
  if (status === "skipped") return "↷";
  if (status === "failed") return "!";
  return "•";
}

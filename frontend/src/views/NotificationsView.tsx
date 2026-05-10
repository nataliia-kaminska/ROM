import type { FormEvent } from "react";
import type { NotificationItem, NotificationPreference } from "../types";
import { label } from "../utils/format";
import { EmptyState, HelpTip } from "../components/ui";

export function NotificationsView({
  notifications,
  notificationPrefs,
  onPrefsChange,
  onSavePrefs,
  onUnsubscribe,
  onMarkRead,
}: {
  notifications: NotificationItem[];
  notificationPrefs: NotificationPreference;
  onPrefsChange: (prefs: NotificationPreference) => void;
  onSavePrefs: (event: FormEvent) => void;
  onUnsubscribe: () => void;
  onMarkRead: (notificationId: number) => void;
}) {
  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <h2>Notification Center</h2>
          <p>Review delivery history and tune proactive alerts.</p>
        </div>
      </div>
      <form className="grid-form" onSubmit={onSavePrefs}>
        <label className="toggle">
          <input type="checkbox" checked={notificationPrefs.email_enabled} onChange={(event) => onPrefsChange({ ...notificationPrefs, email_enabled: event.target.checked })} />
          Email enabled
        </label>
        <label className="toggle">
          <input type="checkbox" checked={notificationPrefs.deadline_reminders_enabled} onChange={(event) => onPrefsChange({ ...notificationPrefs, deadline_reminders_enabled: event.target.checked })} />
          Deadline reminders
        </label>
        <label className="toggle">
          <input type="checkbox" checked={notificationPrefs.weekly_digest_enabled} onChange={(event) => onPrefsChange({ ...notificationPrefs, weekly_digest_enabled: event.target.checked })} />
          Weekly digest
        </label>
        <label className="toggle">
          <input type="checkbox" checked={notificationPrefs.high_match_alerts_enabled} onChange={(event) => onPrefsChange({ ...notificationPrefs, high_match_alerts_enabled: event.target.checked })} />
          High-match alerts
        </label>
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
      <div className="table">
        {notifications.map((item) => (
          <div className="table-row" key={item.id}>
            <span>{item.subject}</span>
            <span>{label(item.notification_type)}</span>
            <span>{label(item.status)}</span>
            {item.status !== "read" && (
              <button className="secondary" onClick={() => onMarkRead(item.id)}>
                Read
              </button>
            )}
          </div>
        ))}
        {notifications.length === 0 && <EmptyState title="No notification history yet" detail="Deadline reminders, digests, and alerts will appear here once generated." />}
      </div>
    </section>
  );
}

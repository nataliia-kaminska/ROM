import { type FormEvent, useState } from "react";
import { api } from "../api";
import type { NotificationItem, NotificationPreference } from "../types";

export function useNotifications({
  token,
  setError,
  setNotice,
}: {
  token: string | null;
  setError: (message: string) => void;
  setNotice: (message: string) => void;
}) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationPrefs, setNotificationPrefs] = useState<NotificationPreference>({
    email_enabled: true,
    deadline_reminders_enabled: true,
    weekly_digest_enabled: true,
    high_match_alerts_enabled: true,
    min_alert_score: 80,
  });

  async function loadNotifications() {
    if (!token) return;
    setError("");
    try {
      const [items, prefs] = await Promise.all([api.notifications(token, true), api.notificationPreferences(token)]);
      setNotifications(items);
      setNotificationPrefs(prefs);
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function saveNotificationPrefs(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    try {
      setNotificationPrefs(await api.saveNotificationPreferences(token, notificationPrefs));
      setNotice("Notification preferences saved");
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function markRead(notificationId: number) {
    if (!token) return;
    setError("");
    try {
      await api.markNotificationRead(token, notificationId);
      await loadNotifications();
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  async function unsubscribe() {
    if (!token) return;
    setError("");
    try {
      setNotificationPrefs(await api.unsubscribeNotifications(token));
      setNotice("Email notifications disabled");
    } catch (notificationError) {
      setError((notificationError as Error).message);
    }
  }

  return {
    notifications,
    notificationPrefs,
    setNotificationPrefs,
    loadNotifications,
    saveNotificationPrefs,
    markRead,
    unsubscribe,
  };
}

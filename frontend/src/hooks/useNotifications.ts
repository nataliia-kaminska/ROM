import { type FormEvent, useEffect, useState } from "react";
import { api } from "../api";
import { API_BASE_URL } from "../api/client";
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

  useEffect(() => {
    if (!token) return;
    void loadNotifications();
    const websocket = new WebSocket(`${websocketBaseUrl()}/ws/notifications?token=${encodeURIComponent(token)}`);
    websocket.onmessage = (event) => {
      const incoming = JSON.parse(event.data) as Partial<NotificationItem>;
      const notificationId = incoming.id;
      if (!notificationId) return;
      setNotifications((items) => [
        {
          id: notificationId,
          notification_type: incoming.notification_type ?? "high_match_alert",
          subject: incoming.subject ?? "New notification",
          body: incoming.body ?? "",
          status: incoming.status ?? "pending",
          skip_reason: incoming.skip_reason ?? "",
          recipient: incoming.recipient ?? "",
          provider: incoming.provider ?? "",
          provider_message_id: incoming.provider_message_id ?? "",
          delivery_attempts: incoming.delivery_attempts ?? 0,
          last_error: incoming.last_error ?? "",
          created_at: incoming.created_at ?? new Date().toISOString(),
          sent_at: incoming.sent_at ?? null,
        },
        ...items.filter((item) => item.id !== incoming.id),
      ]);
      setNotice("New notification received");
    };
    websocket.onerror = () => {
      setError("Realtime notification connection failed");
    };
    return () => websocket.close();
  }, [token, setError, setNotice]);

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


function websocketBaseUrl() {
  return API_BASE_URL.replace(/^http/, "ws");
}

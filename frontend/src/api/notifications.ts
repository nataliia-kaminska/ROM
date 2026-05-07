import type { NotificationItem, NotificationPreference } from "../types";
import { request } from "./client";

export const notificationsApi = {
  notifications: (token: string, includeRead = false) =>
    request<NotificationItem[]>("/notifications", { token, query: { include_read: includeRead } }),
  notificationPreferences: (token: string) => request<NotificationPreference>("/notifications/preferences", { token }),
  saveNotificationPreferences: (token: string, body: NotificationPreference) =>
    request<NotificationPreference>("/notifications/preferences", { token, method: "PUT", body }),
  markNotificationRead: (token: string, notificationId: number) =>
    request<NotificationItem>(`/notifications/${notificationId}/read`, { token, method: "PUT" }),
  unsubscribeNotifications: (token: string) =>
    request<NotificationPreference>("/notifications/unsubscribe", { token, method: "POST" }),
};

import { apiClient } from './client';
import {
  CreatePlansRequest,
  ReminderPlanOut,
  ReminderEventOut,
  TodayRemindersResponse,
  UpdateEventRequest,
  UpdatePlanRequest,
  PushSubscribeRequest,
  VapidPublicKeyResponse,
  AdherenceReportResponse,
} from '../types/api';

export async function createReminderPlansApi(
  req: CreatePlansRequest
): Promise<ReminderPlanOut[]> {
  const response = await apiClient.post<ReminderPlanOut[]>('/reminders/plans', req);
  return response.data;
}

export async function getTodayRemindersApi(
  timezone?: string
): Promise<TodayRemindersResponse> {
  const tz = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
  const response = await apiClient.get<TodayRemindersResponse>('/reminders/today', {
    params: { timezone: tz },
  });
  return response.data;
}

export async function actOnReminderEventApi(
  eventId: string,
  action: 'TAKEN' | 'SNOOZE' | 'SKIP'
): Promise<ReminderEventOut> {
  const response = await apiClient.patch<ReminderEventOut>(
    `/reminders/events/${eventId}`,
    { action }
  );
  return response.data;
}

export async function updateReminderPlanApi(
  planId: string,
  req: UpdatePlanRequest
): Promise<ReminderPlanOut> {
  const response = await apiClient.patch<ReminderPlanOut>(
    `/reminders/plans/${planId}`,
    req
  );
  return response.data;
}

export async function deleteReminderPlanApi(planId: string): Promise<void> {
  await apiClient.delete(`/reminders/plans/${planId}`);
}

export function getPlanIcsDownloadUrl(planId: string): string {
  const baseUrl = apiClient.defaults.baseURL || '/api/v1';
  return `${baseUrl}/reminders/plans/${planId}/calendar.ics`;
}

export async function getVapidPublicKeyApi(): Promise<string> {
  const response = await apiClient.get<VapidPublicKeyResponse>(
    '/reminders/vapid-public-key'
  );
  return response.data.public_key;
}

export async function subscribeWebPushApi(
  sub: PushSubscribeRequest
): Promise<void> {
  await apiClient.post('/reminders/push/subscribe', sub);
}

export async function unsubscribeWebPushApi(endpoint: string): Promise<void> {
  await apiClient.delete('/reminders/push/subscribe', {
    params: { endpoint },
  });
}

export async function getAdherenceReportApi(): Promise<AdherenceReportResponse> {
  const response = await apiClient.get<AdherenceReportResponse>(
    '/reminders/adherence'
  );
  return response.data;
}


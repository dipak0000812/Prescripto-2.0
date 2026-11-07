import { apiClient } from './client';
import {
  AnalyticsDashboardResponse,
  PrescriptionVolume,
  SafetyMetrics,
  DateRangeParams,
} from '../types/analytics';

export type { DateRangeParams };

export async function getAnalyticsDashboardApi(
  params?: DateRangeParams
): Promise<AnalyticsDashboardResponse> {
  const response = await apiClient.get<AnalyticsDashboardResponse>('/analytics/dashboard', {
    params,
  });
  return response.data;
}

export async function getPrescriptionTrendsApi(
  params?: DateRangeParams
): Promise<PrescriptionVolume[]> {
  const response = await apiClient.get<PrescriptionVolume[]>('/analytics/prescription-trends', {
    params,
  });
  return response.data;
}

export async function getSafetySummaryApi(
  params?: DateRangeParams
): Promise<SafetyMetrics> {
  const response = await apiClient.get<SafetyMetrics>('/analytics/safety-summary', {
    params,
  });
  return response.data;
}
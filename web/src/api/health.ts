import { apiClient } from './client';
import { HealthStatus } from '../types/api';

export async function getHealthApi(): Promise<HealthStatus> {
  const response = await apiClient.get<HealthStatus>('/health');
  return response.data;
}

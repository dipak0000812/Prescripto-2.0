import { apiClient } from './client';
import {
  AnalysisStatusResponse,
  AnalysisResult,
  ReviewSubmission,
  ReviewRecord,
} from '../types/api';

export async function getAnalysisStatusApi(id: string): Promise<AnalysisStatusResponse> {
  const response = await apiClient.get<AnalysisStatusResponse>(`/analyses/${id}`);
  return response.data;
}

export async function getAnalysisResultApi(id: string): Promise<AnalysisResult> {
  const response = await apiClient.get<AnalysisResult>(`/analyses/${id}/result`);
  return response.data;
}

export async function submitReviewApi(
  id: string,
  submission: ReviewSubmission
): Promise<ReviewRecord> {
  const response = await apiClient.post<ReviewRecord>(`/analyses/${id}/review`, submission);
  return response.data;
}

export interface ClinicalSummaryResponse {
  engine: string;
  executive_summary: string;
  patient_instructions: string[];
  clinical_alerts: string[];
  doctor_recommendations: string[];
  llm_ready: boolean;
  note?: string;
}

export async function getClinicalSummaryApi(id: string): Promise<ClinicalSummaryResponse> {
  const response = await apiClient.get<ClinicalSummaryResponse>(`/analyses/${id}/clinical-summary`);
  return response.data;
}

export interface MedicationUpdatePayload {
  line_index: number;
  name?: string;
  strength?: string;
  dose?: string;
  frequency?: string;
  route?: string;
  duration?: string;
  instructions?: string;
}

export async function updateAnalysisMedicationsApi(
  id: string,
  medications: MedicationUpdatePayload[]
): Promise<AnalysisResult> {
  const response = await apiClient.patch<AnalysisResult>(`/analyses/${id}/medications`, {
    medications,
  });
  return response.data;
}

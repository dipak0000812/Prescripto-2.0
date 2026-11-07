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

export interface PatientMedicineItem {
  name: string;
  original_text: string;
  plain_explanation: string;
  strength?: string | null;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  duration?: string | null;
  instructions?: string | null;
  missing_details?: string[];
  needs_confirmation?: boolean;
}

export interface DoctorWrittenSection {
  symptoms?: string[];
  clinical_impression?: string[];
  vitals?: string[];
}

export interface RecognitionMetadata {
  provider_used?: string;
  fallback_occurred?: boolean;
  fallback_reason?: string | null;
}

export interface ClinicalSummaryResponse {
  engine: string;
  summary_source?: string;
  summary_warning?: string;
  prescription_summary?: string;
  executive_summary: string;
  what_doctor_wrote?: DoctorWrittenSection;
  medicines_and_treatments?: PatientMedicineItem[];
  patient_instructions: string[];
  other_advice?: string[];
  needs_confirmation?: string[];
  safety_notice?: string;
  clinical_alerts: string[];
  doctor_recommendations: string[];
  recognition_metadata?: RecognitionMetadata;
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

export async function retryAnalysisApi(id: string): Promise<AnalysisStatusResponse> {
  const response = await apiClient.post<AnalysisStatusResponse>(`/analyses/${id}/retry`);
  return response.data;
}

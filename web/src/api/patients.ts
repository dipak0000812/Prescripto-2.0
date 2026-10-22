import { apiClient } from './client';

export interface PatientSummary {
  id: string;
  patient_id: string;
  name: string;
  phone_number: string;
  age?: number | null;
  gender?: string | null;
  blood_group?: string | null;
  prescriptions_count: number;
  latest_visit?: string | null;
  created_at: string;
}

export interface TimelineEvent {
  document_id: string;
  analysis_id?: string | null;
  file_name?: string | null;
  uploaded_at: string;
  analysis_status?: string | null;
  review_required: boolean;
  review_reasons: string[];
  medications: Array<{
    line_index: number;
    name: string;
    strength?: string | null;
    dose?: string | null;
    frequency?: string | null;
    duration?: string | null;
    instructions?: string | null;
    state: string;
    resolution_status?: string | null;
    match_score?: number | null;
  }>;
  safety_findings: Array<{
    check_type: string;
    status: string;
    severity?: string | null;
    detail: string;
    recommendation?: string | null;
  }>;
  clinical_reviews: Array<{
    action: string;
    reviewer_id: string;
    notes?: string | null;
    reviewed_at: string;
  }>;
}

export interface PatientDetail {
  id: string;
  patient_id: string;
  name: string;
  phone_number: string;
  age?: number | null;
  gender?: string | null;
  blood_group?: string | null;
  address?: string | null;
  medical_history?: string | null;
  allergies?: string | null;
  emergency_contact?: string | null;
  created_at: string;
  total_prescriptions: number;
  active_medications: Array<{
    line_index: number;
    name: string;
    strength?: string | null;
    dose?: string | null;
    frequency?: string | null;
    duration?: string | null;
    instructions?: string | null;
    state: string;
    prescribed_date?: string;
    analysis_id?: string;
  }>;
  timeline: TimelineEvent[];
}

export async function searchPatientsApi(query: string = ''): Promise<PatientSummary[]> {
  const response = await apiClient.get<PatientSummary[]>('/patients/search', {
    params: { q: query },
  });
  return response.data;
}

export async function getPatientTimelineApi(patientIdentifier: string): Promise<PatientDetail> {
  const response = await apiClient.get<PatientDetail>(`/patients/${encodeURIComponent(patientIdentifier)}`);
  return response.data;
}

export async function createPatientApi(data: Partial<PatientDetail>): Promise<PatientSummary> {
  const response = await apiClient.post<PatientSummary>('/patients', data);
  return response.data;
}

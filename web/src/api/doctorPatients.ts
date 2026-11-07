import { apiClient } from './client';

export interface DoctorPatientLinkRequest {
  patient_id: string;
}

export interface DoctorPatientLinkResponse {
  id: string;
  doctor_id: string;
  patient_id: string;
  created_at: string;
}

export interface DoctorPatientSummary {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_patient_id: string;
  phone_number: string;
  created_at: string;
}

export interface VerifyAccessResponse {
  has_access: boolean;
  patient_id: string;
  linked_at?: string;
}

export async function linkPatientToDoctorApi(
  patientId: string
): Promise<DoctorPatientLinkResponse> {
  const response = await apiClient.post<DoctorPatientLinkResponse>('/doctor/patients/link', {
    patient_id: patientId,
  });
  return response.data;
}

export async function listDoctorPatientsApi(): Promise<DoctorPatientSummary[]> {
  const response = await apiClient.get<DoctorPatientSummary[]>('/doctor/patients');
  return response.data;
}

export async function unlinkPatientFromDoctorApi(
  patientId: string
): Promise<void> {
  await apiClient.post('/doctor/patients/unlink', { patient_id: patientId });
}

export async function verifyDoctorPatientAccessApi(
  patientId: string
): Promise<VerifyAccessResponse> {
  const response = await apiClient.get<VerifyAccessResponse>(
    `/doctor/patients/${patientId}/verify`
  );
  return response.data;
}
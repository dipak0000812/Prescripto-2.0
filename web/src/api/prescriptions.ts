import { apiClient, generateUUID } from './client';
import {
  UploadAccepted,
  PrescriptionListResponse,
  PrescriptionDetail,
  DeletionAccepted,
} from '../types/api';

export async function uploadPrescriptionApi(
  file: File,
  patientExternalId?: string,
  idempotencyKey?: string
): Promise<UploadAccepted> {
  const formData = new FormData();
  formData.append('file', file);
  if (patientExternalId && patientExternalId.trim()) {
    formData.append('patient_external_id', patientExternalId.trim());
  }

  const key = idempotencyKey || generateUUID();

  const response = await apiClient.post<UploadAccepted>('/prescriptions', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'Idempotency-Key': key,
    },
  });
  return response.data;
}

export async function listPrescriptionsApi(
  page: number = 1,
  pageSize: number = 20
): Promise<PrescriptionListResponse> {
  const response = await apiClient.get<PrescriptionListResponse>('/prescriptions', {
    params: {
      page,
      page_size: pageSize,
    },
  });
  return response.data;
}

export async function getPrescriptionApi(id: string): Promise<PrescriptionDetail> {
  const response = await apiClient.get<PrescriptionDetail>(`/prescriptions/${id}`);
  return response.data;
}

export async function deletePrescriptionApi(id: string): Promise<DeletionAccepted> {
  const response = await apiClient.delete<DeletionAccepted>(`/prescriptions/${id}`);
  return response.data;
}

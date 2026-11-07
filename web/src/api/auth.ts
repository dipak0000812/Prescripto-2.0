import { apiClient } from './client';
import { TokenResponse } from '../types/api';

export async function loginApi(username: string, password: string): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await apiClient.post<TokenResponse>('/auth/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
}

export async function refreshApi(refreshToken: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
}

export async function requestPatientOtpApi(email: string, purpose: string = 'LOGIN'): Promise<{
  status: string;
  email: string;
  message: string;
}> {
  const response = await apiClient.post('/auth/patient/request-otp', {
    email,
    purpose,
  });
  return response.data;
}

export async function registerPatientApi(
  email: string,
  otp: string,
  name: string,
  password?: string
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/patient/register', {
    email,
    otp,
    name,
    password: password || 'Patient@123',
  });
  return response.data;
}

export async function loginPatientApi(
  email: string,
  otp: string
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/patient/login', {
    email,
    otp,
  });
  return response.data;
}

export async function verifyOtpApi(
  email: string,
  otp: string,
  purpose: string = 'LOGIN'
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/verify-otp', {
    email,
    otp,
    purpose,
  });
  return response.data;
}

export async function doctorLoginApi(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/doctor/login', {
    email,
    password,
  });
  return response.data;
}

export async function registerDoctorApi(
  email: string,
  password: string,
  name: string,
  specialization?: string,
  license_number?: string,
  clinic_name?: string,
  clinic_address?: string,
  phone_number?: string,
  bio?: string
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/doctor/register', {
    email,
    password,
    name,
    specialization,
    license_number,
    clinic_name,
    clinic_address,
    phone_number,
    bio,
  });
  return response.data;
}

export async function forgotPasswordApi(email: string): Promise<{
  status: string;
  email: string;
  message: string;
}> {
  const response = await apiClient.post('/auth/forgot-password', { email });
  return response.data;
}

export async function resetPasswordApi(email: string, token: string, new_password: string): Promise<any> {
  const response = await apiClient.post('/auth/reset-password', {
    email,
    token,
    new_password,
  });
  return response.data;
}

export async function getMeApi(): Promise<any> {
  const response = await apiClient.get('/auth/me');
  return response.data;
}
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

export async function sendOtpApi(phoneNumber: string): Promise<{
  status: string;
  phone_number: string;
  message: string;
  mock_otp: string;
}> {
  const response = await apiClient.post('/auth/send-otp', {
    phone_number: phoneNumber,
  });
  return response.data;
}

export async function verifyOtpApi(
  phoneNumber: string,
  otp: string,
  name?: string
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/verify-otp', {
    phone_number: phoneNumber,
    otp,
    name,
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

export async function getMeApi(): Promise<any> {
  const response = await apiClient.get('/auth/me');
  return response.data;
}

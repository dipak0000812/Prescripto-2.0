import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiError, TokenResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
});

// Helper to generate UUIDv4 for X-Request-ID
export function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Request interceptor: injects token & X-Request-ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('prescripto_access_token');
    if (token && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    if (!config.headers['X-Request-ID']) {
      config.headers['X-Request-ID'] = generateUUID();
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor: error normalization & auto-refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ error?: ApiError }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 on login or refresh itself, don't attempt loop
    if (
      error.response?.status === 401 &&
      !originalRequest.url?.includes('/auth/token') &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest._retry
    ) {
      const refreshToken = localStorage.getItem('prescripto_refresh_token');

      if (!refreshToken) {
        localStorage.removeItem('prescripto_access_token');
        localStorage.removeItem('prescripto_refresh_token');
        localStorage.removeItem('prescripto_user');
        window.dispatchEvent(new CustomEvent('prescripto_session_expired'));
        return Promise.reject(normalizeApiError(error));
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers['Authorization'] = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResponse = await axios.post<TokenResponse>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json', 'X-Request-ID': generateUUID() } }
        );

        const newAccessToken = refreshResponse.data.access_token;
        const newRefreshToken = refreshResponse.data.refresh_token;

        localStorage.setItem('prescripto_access_token', newAccessToken);
        localStorage.setItem('prescripto_refresh_token', newRefreshToken);

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        }

        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem('prescripto_access_token');
        localStorage.removeItem('prescripto_refresh_token');
        localStorage.removeItem('prescripto_user');
        window.dispatchEvent(new CustomEvent('prescripto_session_expired'));
        return Promise.reject(normalizeApiError(refreshErr as AxiosError<{ error?: ApiError }>));
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(normalizeApiError(error));
  }
);

/**
 * Normalizes Axios errors into a consistent ApiError object.
 */
export function normalizeApiError(error: AxiosError<{ error?: ApiError }> | any): ApiError {
  if (error?.response?.data?.error) {
    return error.response.data.error;
  }

  const status = error?.response?.status;
  const requestId = (error?.response?.headers?.['x-request-id'] as string) || generateUUID();

  if (status === 400) {
    return {
      code: 'BAD_REQUEST',
      message: 'The request could not be processed due to invalid parameters.',
      request_id: requestId,
    };
  }

  if (status === 401) {
    return {
      code: 'UNAUTHORIZED',
      message: 'Authentication failed or session has expired. Please sign in again.',
      request_id: requestId,
    };
  }

  if (status === 403) {
    return {
      code: 'INSUFFICIENT_ROLE',
      message: 'You do not have permission to perform this clinical action.',
      request_id: requestId,
    };
  }

  if (status === 404) {
    return {
      code: 'RESOURCE_NOT_FOUND',
      message: 'The requested resource could not be found or is not yet available.',
      request_id: requestId,
    };
  }

  if (status === 409) {
    return {
      code: 'CONFLICT',
      message: 'A state conflict occurred. Please review the item and try again.',
      request_id: requestId,
    };
  }

  if (status === 413) {
    return {
      code: 'FILE_TOO_LARGE',
      message: 'The selected file exceeds the 20 MB size limit.',
      request_id: requestId,
    };
  }

  if (status === 415) {
    return {
      code: 'UNSUPPORTED_MEDIA_TYPE',
      message: 'File format not supported. Only JPEG, PNG, TIFF, or PDF files are accepted.',
      request_id: requestId,
    };
  }

  if (status === 503) {
    return {
      code: 'STORAGE_UNAVAILABLE',
      message: 'Storage service is temporarily unavailable. Please retry shortly.',
      request_id: requestId,
    };
  }

  return {
    code: 'NETWORK_OR_SERVER_ERROR',
    message: error?.message || 'A network error occurred. Please check your connection.',
    request_id: requestId,
  };
}

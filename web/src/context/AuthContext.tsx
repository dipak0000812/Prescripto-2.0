import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserSession, Role, TokenResponse } from '../types/api';
import {
  loginApi,
  refreshApi,
  requestPatientOtpApi,
  registerPatientApi,
  loginPatientApi,
  doctorLoginApi,
  registerDoctorApi,
  forgotPasswordApi,
  resetPasswordApi,
  getMeApi,
  verifyOtpApi,
} from '../api/auth';

interface AuthContextType {
  session: UserSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  doctorLogin: (email: string, password: string) => Promise<void>;
  doctorRegister: (data: {
    email: string;
    password: string;
    name: string;
    specialization?: string;
    license_number?: string;
    clinic_name?: string;
    clinic_address?: string;
    phone_number?: string;
    bio?: string;
  }) => Promise<void>;
  requestPatientOtp: (email: string, purpose?: string) => Promise<{ status: string; email: string; message: string }>;
  registerPatient: (email: string, otp: string, name: string, password?: string) => Promise<void>;
  loginPatient: (email: string, otp: string) => Promise<void>;
  verifyOtp: (email: string, otp: string, purpose?: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (email: string, token: string, newPassword: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function parseJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const setSessionFromTokens = (data: TokenResponse) => {
    const payload = parseJwt(data.access_token);
    if (!payload) {
      throw new Error('Received invalid token from authentication service');
    }

    localStorage.setItem('prescripto_access_token', data.access_token);
    localStorage.setItem('prescripto_refresh_token', data.refresh_token);

    const extra: any = data.user || {};
    const newSession: UserSession = {
      user_id: payload.sub,
      username: payload.username,
      role: payload.role,
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_at: payload.exp,
      email: extra.email,
      patient_id: payload.patient_id || extra.patient_id,
      patient_name: payload.patient_name || extra.patient_name,
      phone_number: payload.phone_number || extra.phone_number,
      is_patient: payload.is_patient || extra.is_patient,
    };
    setSession(newSession);
  };

  const initSession = async () => {
    const accessToken = localStorage.getItem('prescripto_access_token');
    const refreshToken = localStorage.getItem('prescripto_refresh_token');

    if (!accessToken || !refreshToken) {
      setSession(null);
      setIsLoading(false);
      return;
    }

    const payload = parseJwt(accessToken);
    const now = Math.floor(Date.now() / 1000);

    if (payload && payload.exp > now + 30) {
      setSession({
        user_id: payload.sub,
        username: payload.username,
        role: payload.role,
        access_token: accessToken,
        refresh_token: refreshToken,
        expires_at: payload.exp,
        patient_id: payload.patient_id,
        patient_name: payload.patient_name,
        phone_number: payload.phone_number,
        is_patient: payload.is_patient,
      });
      setIsLoading(false);
      return;
    }

    // Access token expired -> attempt refresh
    try {
      const refreshed = await refreshApi(refreshToken);
      setSessionFromTokens(refreshed);
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProfile = async () => {
    try {
      const data = await getMeApi();
      if (data && session) {
        const updatedSession = { ...session };
        if (data.patient) {
          updatedSession.patient_id = data.patient.patient_id;
          updatedSession.patient_name = data.patient.name;
          updatedSession.phone_number = data.patient.phone_number;
          updatedSession.is_patient = true;
        }
        if (data.doctor) {
          // Doctor info available
        }
        if (data.email) {
          // Email is available
        }
        if (data.is_verified !== undefined) {
          // is_verified available
        }
        setSession(updatedSession);
      }
    } catch {
      // Ignore profile refresh errors
    }
  };

  useEffect(() => {
    initSession();

    const handleExpired = () => {
      logout();
    };

    window.addEventListener('prescripto_session_expired', handleExpired);
    return () => {
      window.removeEventListener('prescripto_session_expired', handleExpired);
    };
  }, []);

  const login = async (usernameOrEmail: string, password: string): Promise<void> => {
    const data = await loginApi(usernameOrEmail, password);
    setSessionFromTokens(data);
  };

  const doctorLogin = async (email: string, password: string): Promise<void> => {
    const data = await doctorLoginApi(email, password);
    setSessionFromTokens(data);
  };

  const doctorRegister = async (data: {
    email: string;
    password: string;
    name: string;
    specialization?: string;
    license_number?: string;
    clinic_name?: string;
    clinic_address?: string;
    phone_number?: string;
    bio?: string;
  }): Promise<void> => {
    const result = await registerDoctorApi(
      data.email,
      data.password,
      data.name,
      data.specialization,
      data.license_number,
      data.clinic_name,
      data.clinic_address,
      data.phone_number,
      data.bio,
    );
    setSessionFromTokens(result);
  };

  const requestPatientOtp = async (email: string, purpose: string = 'LOGIN') => {
    return await requestPatientOtpApi(email, purpose);
  };

  const registerPatient = async (email: string, otp: string, name: string, password?: string): Promise<void> => {
    const data = await registerPatientApi(email, otp, name, password);
    setSessionFromTokens(data);
  };

  const loginPatient = async (email: string, otp: string): Promise<void> => {
    const data = await loginPatientApi(email, otp);
    setSessionFromTokens(data);
  };

  const verifyOtp = async (email: string, otp: string, purpose: string = 'LOGIN'): Promise<void> => {
    const data = await verifyOtpApi(email, otp, purpose);
    setSessionFromTokens(data);
  };

  const forgotPassword = async (email: string): Promise<void> => {
    await forgotPasswordApi(email);
  };

  const resetPassword = async (email: string, token: string, newPassword: string): Promise<void> => {
    await resetPasswordApi(email, token, newPassword);
  };

  const logout = () => {
    localStorage.removeItem('prescripto_access_token');
    localStorage.removeItem('prescripto_refresh_token');
    setSession(null);
  };

  const hasRole = (...roles: Role[]): boolean => {
    if (!session) return false;
    return roles.includes(session.role);
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        isAuthenticated: !!session,
        isLoading,
        login,
        doctorLogin,
        doctorRegister,
        requestPatientOtp,
        registerPatient,
        loginPatient,
        verifyOtp,
        forgotPassword,
        resetPassword,
        logout,
        hasRole,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
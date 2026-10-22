import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserSession, Role, TokenResponse } from '../types/api';
import { loginApi, refreshApi, sendOtpApi, verifyOtpApi, doctorLoginApi } from '../api/auth';

interface AuthContextType {
  session: UserSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  doctorLogin: (email: string, password: string) => Promise<void>;
  sendOtp: (phoneNumber: string) => Promise<{ status: string; phone_number: string; message: string; mock_otp: string }>;
  loginWithOtp: (phoneNumber: string, otp: string, name?: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
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

  const sendOtp = async (phoneNumber: string) => {
    return await sendOtpApi(phoneNumber);
  };

  const loginWithOtp = async (phoneNumber: string, otp: string, name?: string): Promise<void> => {
    const data = await verifyOtpApi(phoneNumber, otp, name);
    setSessionFromTokens(data);
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
        sendOtp,
        loginWithOtp,
        logout,
        hasRole,
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

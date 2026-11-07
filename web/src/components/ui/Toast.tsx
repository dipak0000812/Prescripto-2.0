import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { X, CheckCircle2, AlertCircle, AlertTriangle, Info, Loader2 } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => string;
  hideToast: (id: string) => void;
  success: (title: string, message?: string, duration?: number) => string;
  error: (title: string, message?: string, duration?: number) => string;
  warning: (title: string, message?: string, duration?: number) => string;
  info: (title: string, message?: string, duration?: number) => string;
  loading: (title: string, message?: string) => string;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

const toastIcons = {
  success: <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" aria-hidden="true" />,
  error: <AlertCircle className="w-5 h-5 text-[#BE123C] shrink-0" aria-hidden="true" />,
  warning: <AlertTriangle className="w-5 h-5 text-[#B45309] shrink-0" aria-hidden="true" />,
  info: <Info className="w-5 h-5 text-[#0F5147] shrink-0" aria-hidden="true" />,
  loading: <Loader2 className="w-5 h-5 text-[#0F5147] shrink-0 animate-spin" aria-hidden="true" />,
};

const toastStyles = {
  success: 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]',
  error: 'bg-[#FFE4E6] border-[#FDA4AF] text-[#881337]',
  warning: 'bg-[#FEF3C7] border-[#FCD34D] text-[#78350F]',
  info: 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]',
  loading: 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]',
};

const badgeStyles = {
  success: 'bg-white/90 text-[#047857] border border-[#A7F3D0]',
  error: 'bg-white/90 text-[#BE123C] border border-[#FDA4AF]',
  warning: 'bg-white/90 text-[#B45309] border border-[#FCD34D]',
  info: 'bg-white/90 text-[#0F5147] border border-[#9DC1BB]',
  loading: 'bg-white/90 text-[#0F5147] border border-[#9DC1BB]',
};

const defaultTitles = {
  success: 'Confirmed',
  error: 'Problem',
  warning: 'Please check',
  info: 'Note',
  loading: 'Loading',
};

const roles = {
  success: 'status',
  error: 'alert',
  warning: 'alert',
  info: 'status',
  loading: 'status',
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (toast: Omit<Toast, 'id'>): string => {
    const id = crypto.randomUUID();
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? (toast.type === 'loading' ? 0 : 5000),
    };
    setToasts((prev) => [...prev, newToast]);
    return id;
  };

  const hideToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Auto-hide toasts
  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    toasts.forEach((toast) => {
      if (toast.duration && toast.duration > 0) {
        const timer = setTimeout(() => hideToast(toast.id), toast.duration);
        timers.push(timer);
      }
    });
    return () => timers.forEach(clearTimeout);
  }, [toasts]);

  const helpers = {
    success: (title: string, message?: string, duration?: number) =>
      showToast({ type: 'success', title, message, duration }),
    error: (title: string, message?: string, duration?: number) =>
      showToast({ type: 'error', title, message, duration }),
    warning: (title: string, message?: string, duration?: number) =>
      showToast({ type: 'warning', title, message, duration }),
    info: (title: string, message?: string, duration?: number) =>
      showToast({ type: 'info', title, message, duration }),
    loading: (title: string, message?: string) =>
      showToast({ type: 'loading', title, message, duration: 0 }),
  };

  return (
    <ToastContext.Provider value={{ toasts, showToast, hideToast, ...helpers }}>
      {children}
      <ToastContainer toasts={toasts} onClose={hideToast} />
    </ToastContext.Provider>
  );
};

const ToastContainer: React.FC<{ toasts: Toast[]; onClose: (id: string) => void }> = ({
  toasts,
  onClose,
}) => {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 sm:bottom-6 sm:right-6"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: Toast; onClose: (id: string) => void }> = ({
  toast,
  onClose,
}) => {
  const styles = toastStyles[toast.type];
  const badgeStyle = badgeStyles[toast.type];
  const Icon = toastIcons[toast.type];
  const defaultTitle = defaultTitles[toast.type];
  const role = roles[toast.type];

  return (
    <div
      role={role}
      aria-live={toast.type === 'error' || toast.type === 'warning' ? 'assertive' : 'polite'}
      className={`rounded-xl border p-4 shadow-lg max-w-sm w-full animate-in slide-in-from-right duration-200 ${styles}`}
    >
      <div className="flex items-start gap-3">
        {Icon}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${badgeStyle}`}>
              {defaultTitle}
            </span>
            <h4 className="text-sm font-bold">{toast.title}</h4>
          </div>
          {toast.message && (
            <div className="text-sm leading-normal text-stone-800">{toast.message}</div>
          )}
          {toast.action && (
            <button
              onClick={() => {
                toast.action?.onClick();
                onClose(toast.id);
              }}
              className="mt-3 text-xs font-semibold underline hover:no-underline"
            >
              {toast.action.label}
            </button>
          )}
        </div>
        <button
          onClick={() => onClose(toast.id)}
          className="p-1 rounded-lg hover:bg-stone-200/50 transition cursor-pointer shrink-0 text-stone-500"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default ToastProvider;
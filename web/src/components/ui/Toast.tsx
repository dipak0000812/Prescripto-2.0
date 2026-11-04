import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastProps {
  type?: ToastType;
  message: string;
  onClose?: () => void;
  className?: string;
}

export const Toast: React.FC<ToastProps> = ({
  type = 'info',
  message,
  onClose,
  className = '',
}) => {
  const configs = {
    success: {
      bg: 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]',
      icon: <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" aria-hidden="true" />,
    },
    error: {
      bg: 'bg-[#FFE4E6] border-[#FDA4AF] text-[#881337]',
      icon: <AlertCircle className="w-5 h-5 text-[#BE123C] shrink-0" aria-hidden="true" />,
    },
    info: {
      bg: 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]',
      icon: <Info className="w-5 h-5 text-[#0F5147] shrink-0" aria-hidden="true" />,
    },
  };

  const current = configs[type];

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border shadow-md text-sm font-medium ${current.bg} ${className}`}
    >
      <div className="flex items-center gap-2.5">
        {current.icon}
        <span>{message}</span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-black/5 transition text-current"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default Toast;


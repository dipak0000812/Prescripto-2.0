import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

export interface AlertBannerProps {
  type?: 'info' | 'warning' | 'error' | 'success';
  title?: string;
  badgeLabel?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'info',
  title,
  badgeLabel,
  children,
  className = '',
  action,
}) => {
  // Always combine Icon + Plain Word Badge + Accessible Color
  const configs = {
    info: {
      bg: 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]',
      icon: <Info className="w-5 h-5 text-[#0F5147] shrink-0 mt-0.5" aria-hidden="true" />,
      defaultBadge: 'Note',
      badgeClass: 'bg-white/80 text-[#0F5147] border border-[#9DC1BB]',
      titleColor: 'text-[#0A3831] font-bold',
      role: 'status',
    },
    warning: {
      bg: 'bg-[#FEF3C7] border-[#FCD34D] text-[#78350F]',
      icon: <AlertTriangle className="w-5 h-5 text-[#B45309] shrink-0 mt-0.5" aria-hidden="true" />,
      defaultBadge: 'Please check',
      badgeClass: 'bg-white/90 text-[#B45309] border border-[#FCD34D]',
      titleColor: 'text-[#78350F] font-bold',
      role: 'alert',
    },
    error: {
      bg: 'bg-[#FFE4E6] border-[#FDA4AF] text-[#881337]',
      icon: <AlertCircle className="w-5 h-5 text-[#BE123C] shrink-0 mt-0.5" aria-hidden="true" />,
      defaultBadge: 'Problem',
      badgeClass: 'bg-white/90 text-[#BE123C] border border-[#FDA4AF]',
      titleColor: 'text-[#881337] font-bold',
      role: 'alert',
    },
    success: {
      bg: 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]',
      icon: <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0 mt-0.5" aria-hidden="true" />,
      defaultBadge: 'Confirmed',
      badgeClass: 'bg-white/90 text-[#047857] border border-[#A7F3D0]',
      titleColor: 'text-[#064E3B] font-bold',
      role: 'status',
    },
  };

  const current = configs[type];
  const displayBadge = badgeLabel || current.defaultBadge;

  return (
    <div
      role={current.role}
      aria-live={type === 'error' || type === 'warning' ? 'assertive' : 'polite'}
      className={`rounded-xl border p-4 text-sm leading-relaxed ${current.bg} ${className}`}
    >
      <div className="flex items-start gap-3">
        {current.icon}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${current.badgeClass}`}>
              {displayBadge}
            </span>
            {title && <h4 className={`text-sm sm:text-base font-bold ${current.titleColor}`}>{title}</h4>}
          </div>
          <div className="text-sm leading-normal text-stone-800">{children}</div>
          {action && <div className="mt-3">{action}</div>}
        </div>
      </div>
    </div>
  );
};

export default AlertBanner;

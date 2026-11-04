import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle, ShieldCheck, Clock } from 'lucide-react';

export type StatusChipVariant = 'success' | 'warning' | 'error' | 'neutral' | 'brand';

export interface StatusChipProps {
  label: string;
  variant?: StatusChipVariant;
  icon?: React.ReactNode;
  className?: string;
}

export const StatusChip: React.FC<StatusChipProps> = ({
  label,
  variant = 'neutral',
  icon,
  className = '',
}) => {
  const configs = {
    brand: {
      bg: 'bg-[#E6F0EE] text-[#0F5147] border-[#9DC1BB]',
      defaultIcon: <ShieldCheck className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />,
    },
    success: {
      bg: 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]',
      defaultIcon: <CheckCircle2 className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />,
    },
    warning: {
      bg: 'bg-[#FEF3C7] text-[#78350F] border-[#FCD34D]',
      defaultIcon: <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />,
    },
    error: {
      bg: 'bg-[#FFE4E6] text-[#881337] border-[#FDA4AF]',
      defaultIcon: <AlertCircle className="w-3.5 h-3.5 text-[#BE123C]" aria-hidden="true" />,
    },
    neutral: {
      bg: 'bg-[#F4F2EC] text-[#1C252E] border-stone-200',
      defaultIcon: <Clock className="w-3.5 h-3.5 text-stone-500" aria-hidden="true" />,
    },
  };

  const current = configs[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${current.bg} ${className}`}
    >
      {icon ?? current.defaultIcon}
      <span>{label}</span>
    </span>
  );
};

export default StatusChip;


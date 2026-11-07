import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: 'brand' | 'success' | 'warning' | 'danger' | 'neutral' | 'outline';
  size?: 'sm' | 'md';
  dot?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  icon,
  className = '',
  ...props
}) => {
  const variantStyles = {
    brand: 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]',
    success: 'bg-[#ECFDF5] text-[#047857] border border-[#A7F3D0]',
    warning: 'bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]',
    danger: 'bg-[#FFE4E6] text-[#BE123C] border border-[#FDA4AF]',
    neutral: 'bg-[#F4F2EC] text-[#1C252E] border border-stone-200',
    outline: 'bg-white text-[#4B5563] border border-stone-300',
  };

  const dotColors = {
    brand: 'bg-[#0F5147]',
    success: 'bg-[#047857]',
    warning: 'bg-[#B45309]',
    danger: 'bg-[#BE123C]',
    neutral: 'bg-stone-500',
    outline: 'bg-stone-400',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 rounded-md gap-1',
    md: 'text-xs sm:text-sm px-2.5 py-1 rounded-lg gap-1.5',
  };

  return (
    <span
      className={`inline-flex items-center font-medium select-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant]}`}
          aria-hidden="true"
        />
      )}
      {icon && <span className="shrink-0" aria-hidden="true">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

export default Badge;


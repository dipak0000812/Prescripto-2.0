import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'muted' | 'amber' | 'emerald' | 'rose';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  ...props
}) => {
  // Paper-like subtle surfaces, hairline borders, consistent 12px (rounded-xl) radius
  const variantStyles = {
    default: 'bg-white border-stone-200 text-[#1C252E] shadow-2xs',
    muted: 'bg-[#F4F2EC] border-stone-200 text-[#1C252E]',
    amber: 'bg-[#FFFBEB] border-amber-300 text-amber-950',
    emerald: 'bg-[#F0FDF4] border-emerald-300 text-emerald-950',
    rose: 'bg-[#FFF1F2] border-rose-300 text-rose-950',
  };

  return (
    <div
      className={`rounded-xl border p-4 sm:p-6 transition-all ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`border-b border-stone-100 pb-3.5 mb-3.5 ${className}`}>
    {children}
  </div>
);

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
  className?: string;
  as?: 'h2' | 'h3' | 'h4';
  id?: string;
}

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  className = '',
  as: Component = 'h3',
  id,
  ...props
}) => (
  <Component id={id} className={`text-base sm:text-lg font-bold text-[#1C252E] tracking-tight flex items-center gap-2 ${className}`} {...props}>
    {children}
  </Component>
);

export const CardDescription: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <p className={`text-xs sm:text-sm text-stone-600 mt-1 leading-relaxed ${className}`}>
    {children}
  </p>
);

export default Card;

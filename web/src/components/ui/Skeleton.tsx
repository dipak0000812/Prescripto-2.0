import React from 'react';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string | number;
  height?: string | number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rectangular',
  width,
  height,
  className = '',
  style,
  ...props
}) => {
  const variantStyles = {
    text: 'h-4 w-full rounded-md',
    circular: 'rounded-full shrink-0',
    rectangular: 'rounded-xl',
    card: 'rounded-xl border border-stone-200 p-5 space-y-3 bg-white',
  };

  const inlineStyles: React.CSSProperties = {
    ...style,
    ...(width !== undefined ? { width } : {}),
    ...(height !== undefined ? { height } : {}),
  };

  if (variant === 'card') {
    return (
      <div
        className={`animate-pulse ${variantStyles.card} ${className}`}
        style={inlineStyles}
        aria-hidden="true"
        {...props}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-stone-200" />
          <div className="space-y-1.5 flex-1">
            <div className="h-4 bg-stone-200 rounded-md w-1/3" />
            <div className="h-3 bg-stone-200 rounded-md w-1/4" />
          </div>
        </div>
        <div className="space-y-2 pt-2">
          <div className="h-4 bg-stone-200 rounded-md w-full" />
          <div className="h-4 bg-stone-200 rounded-md w-4/5" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`animate-pulse bg-stone-200/75 ${variantStyles[variant]} ${className}`}
      style={inlineStyles}
      aria-hidden="true"
      {...props}
    />
  );
};

export default Skeleton;


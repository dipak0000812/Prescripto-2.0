import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = '',
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      type = 'button',
      ...props
    },
    ref
  ) => {
    // 48px min touch target on mobile, high contrast accessible focus ring, restrained radius
    const baseStyles =
      'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-150 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 select-none cursor-pointer';

    // Warm, trustworthy healthcare palette (Forest Teal, Warm Stone, Rose Red)
    const variantStyles = {
      primary:
        'bg-[#0F5147] hover:bg-[#0A3831] active:bg-[#072621] text-white shadow-2xs border border-[#0F5147]',
      secondary:
        'bg-[#F4F2EC] hover:bg-[#EAE7DF] active:bg-[#DFDCD4] text-[#1C252E] border border-[#E5E7EB]',
      outline:
        'bg-white hover:bg-[#FAF9F6] active:bg-[#F4F2EC] text-[#1C252E] border border-stone-300 hover:border-stone-400 shadow-2xs',
      ghost:
        'bg-transparent hover:bg-[#F4F2EC] active:bg-[#EAE7DF] text-[#1C252E]',
      destructive:
        'bg-[#BE123C] hover:bg-[#9F1239] active:bg-[#881337] text-white shadow-2xs border border-[#BE123C]',
    };

    // Touch targets at least 48px for WCAG AA compliance on mobile devices
    const sizeStyles = {
      sm: 'text-xs px-3.5 py-2.5 min-h-[44px] sm:min-h-[40px] gap-2',
      md: 'text-sm sm:text-base px-5 py-3 min-h-[48px] gap-2.5',
      lg: 'text-base sm:text-lg px-6 py-3.5 min-h-[52px] gap-3',
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin shrink-0" aria-hidden="true" />
            <span>{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="shrink-0" aria-hidden="true">{leftIcon}</span>}
            <span>{children}</span>
            {rightIcon && <span className="shrink-0" aria-hidden="true">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
export default Button;

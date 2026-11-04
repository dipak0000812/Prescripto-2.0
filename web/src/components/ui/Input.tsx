import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  errorMessage?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      errorMessage,
      leftIcon,
      rightIcon,
      id,
      className = '',
      disabled = false,
      required = false,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-semibold text-[#1C252E] mb-1.5"
          >
            {label}
            {required && <span className="text-[#BE123C] ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 text-stone-500 pointer-events-none shrink-0" aria-hidden="true">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={Boolean(errorMessage)}
            aria-describedby={
              errorMessage
                ? `${inputId}-error`
                : helperText
                ? `${inputId}-helper`
                : undefined
            }
            className={`w-full rounded-xl border bg-white text-[#1C252E] transition-all duration-150 min-h-[48px] px-3.5 text-base sm:text-base placeholder:text-stone-400 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-2 disabled:bg-stone-100 disabled:cursor-not-allowed ${
              leftIcon ? 'pl-11' : ''
            } ${rightIcon ? 'pr-11' : ''} ${
              errorMessage
                ? 'border-[#FDA4AF] bg-[#FFF1F2] text-[#881337] focus-visible:ring-[#BE123C]'
                : 'border-stone-300 hover:border-stone-400 focus-visible:border-[#0F5147] focus-visible:ring-[#0F5147]'
            } ${className}`}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3.5 text-stone-500 pointer-events-none shrink-0" aria-hidden="true">
              {rightIcon}
            </div>
          )}
        </div>

        {errorMessage ? (
          <p
            id={`${inputId}-error`}
            role="alert"
            className="mt-1.5 text-xs sm:text-sm text-[#BE123C] flex items-center gap-1.5 font-medium"
          >
            <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span>{errorMessage}</span>
          </p>
        ) : helperText ? (
          <p
            id={`${inputId}-helper`}
            className="mt-1.5 text-xs text-stone-600"
          >
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
export default Input;


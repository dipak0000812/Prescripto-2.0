import React from 'react';
import { ChevronDown, AlertCircle } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  errorMessage?: string;
  options: SelectOption[];
  leftIcon?: React.ReactNode;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      helperText,
      errorMessage,
      options,
      leftIcon,
      id,
      className = '',
      disabled = false,
      required = false,
      ...props
    },
    ref
  ) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full text-left">
        {label && (
          <label
            htmlFor={selectId}
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

          <select
            ref={ref}
            id={selectId}
            disabled={disabled}
            aria-invalid={Boolean(errorMessage)}
            aria-describedby={
              errorMessage
                ? `${selectId}-error`
                : helperText
                ? `${selectId}-helper`
                : undefined
            }
            className={`w-full min-h-[48px] rounded-xl border bg-white text-[#1C252E] font-medium text-base transition-colors duration-150 appearance-none cursor-pointer pr-10 ${
              leftIcon ? 'pl-11' : 'pl-3.5'
            } ${
              errorMessage
                ? 'border-[#BE123C] focus:border-[#BE123C] focus:ring-2 focus:ring-[#BE123C]/20'
                : 'border-stone-300 hover:border-stone-400 focus:border-[#0F5147] focus:ring-2 focus:ring-[#0F5147]/20'
            } ${
              disabled
                ? 'bg-[#F4F2EC] text-stone-400 cursor-not-allowed border-stone-200'
                : ''
            } focus:outline-hidden ${className}`}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>

          <div className="absolute right-3.5 text-stone-500 pointer-events-none shrink-0" aria-hidden="true">
            <ChevronDown className="w-5 h-5" />
          </div>
        </div>

        {errorMessage && (
          <div
            id={`${selectId}-error`}
            role="alert"
            className="mt-1.5 flex items-center gap-1.5 text-xs font-medium text-[#BE123C]"
          >
            <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span>{errorMessage}</span>
          </div>
        )}

        {helperText && !errorMessage && (
          <p id={`${selectId}-helper`} className="mt-1.5 text-xs text-stone-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
export default Select;


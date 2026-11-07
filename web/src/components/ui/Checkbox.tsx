import React from 'react';
import { Check } from 'lucide-react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: React.ReactNode;
  description?: React.ReactNode;
  errorMessage?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, errorMessage, id, checked, className = '', disabled, ...props }, ref) => {
    const inputId = id || `chk-${Math.random().toString(36).substring(2, 9)}`;

    return (
      <div className="w-full text-left">
        <label
          htmlFor={inputId}
          className={`flex items-start gap-3.5 min-h-[48px] py-1 cursor-pointer select-none ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          } ${className}`}
        >
          <div className="relative flex items-center justify-center shrink-0 mt-0.5">
            <input
              ref={ref}
              type="checkbox"
              id={inputId}
              checked={checked}
              disabled={disabled}
              className="sr-only peer"
              aria-invalid={Boolean(errorMessage)}
              {...props}
            />
            {/* Visual checkbox container: 22x22px */}
            <div className="w-[22px] height-[22px] h-[22px] rounded-md border-2 border-stone-300 bg-white transition-colors duration-150 peer-focus-visible:ring-2 peer-focus-visible:ring-[#0F5147] peer-focus-visible:ring-offset-2 peer-checked:bg-[#0F5147] peer-checked:border-[#0F5147] flex items-center justify-center">
              <Check
                className={`w-3.5 h-3.5 text-white transition-transform duration-100 ${
                  checked ? 'scale-100 opacity-100 stroke-[3]' : 'scale-50 opacity-0'
                }`}
                aria-hidden="true"
              />
            </div>
          </div>

          <div className="flex-1">
            <span className="block text-sm sm:text-base font-medium text-[#1C252E] leading-snug">
              {label}
            </span>
            {description && (
              <p className="mt-0.5 text-xs sm:text-sm text-[#4B5563] leading-relaxed">
                {description}
              </p>
            )}
          </div>
        </label>

        {errorMessage && (
          <p role="alert" className="mt-1 text-xs font-medium text-[#BE123C] pl-9">
            {errorMessage}
          </p>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';
export default Checkbox;


import React from 'react';

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel = 'Choose option',
  className = '',
  size = 'md',
}: SegmentedControlProps<T>) {
  const sizeClasses = {
    sm: 'p-1 gap-1 text-xs min-h-[40px]',
    md: 'p-1.5 gap-1.5 text-sm sm:text-base min-h-[48px]',
    lg: 'p-2 gap-2 text-base sm:text-lg min-h-[54px]',
  };

  const buttonSizeClasses = {
    sm: 'py-1.5 px-3 min-h-[34px]',
    md: 'py-2.5 px-4 min-h-[40px]',
    lg: 'py-3 px-5 min-h-[46px]',
  };

  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={`inline-flex w-full items-center bg-[#F4F2EC] rounded-xl border border-stone-200 select-none ${sizeClasses[size]} ${className}`}
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            disabled={opt.disabled}
            onClick={() => onChange(opt.value)}
            className={`flex-1 inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:ring-offset-1 ${
              buttonSizeClasses[size]
            } ${
              isSelected
                ? 'bg-white text-[#0F5147] font-semibold shadow-2xs border border-stone-200/80'
                : 'text-[#4B5563] hover:text-[#1C252E] hover:bg-stone-200/50'
            } ${opt.disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
          >
            {opt.icon && <span className="mr-2 shrink-0" aria-hidden="true">{opt.icon}</span>}
            <span className="truncate">{opt.label}</span>
            {opt.badge !== undefined && (
              <span
                className={`ml-2 px-1.5 py-0.5 rounded-full text-xs font-semibold ${
                  isSelected
                    ? 'bg-[#E6F0EE] text-[#0F5147]'
                    : 'bg-stone-200 text-stone-700'
                }`}
              >
                {opt.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default SegmentedControl;


import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
  stepIndicator?: string;
  subtext?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
  stepIndicator,
  subtext,
  className = '',
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-xl border border-stone-200 bg-white p-8 sm:p-12 text-center max-w-md mx-auto shadow-2xs ${className}`}
    >
      <div className="w-14 h-14 rounded-xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center mx-auto mb-4 border border-[#9DC1BB]">
        <Loader2 className="w-7 h-7 text-[#0F5147] animate-spin" aria-hidden="true" />
      </div>

      {stepIndicator && (
        <span className="inline-block px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider bg-[#F4F2EC] text-[#0F5147] border border-stone-200 mb-2">
          {stepIndicator}
        </span>
      )}

      <h3 className="text-base sm:text-lg font-bold text-[#1C252E]">{message}</h3>

      {subtext && (
        <p className="text-xs sm:text-sm text-stone-600 mt-2 leading-relaxed">
          {subtext}
        </p>
      )}
    </div>
  );
};

export default LoadingState;


import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

export interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxHeight?: string;
  className?: string;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxHeight = 'max-h-[88vh]',
  className = '',
}) => {
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'bottomsheet-title' : undefined}
      className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/60 backdrop-blur-xs transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={sheetRef}
        className={`w-full max-w-2xl bg-white rounded-t-2xl shadow-2xl border-t border-x border-stone-200 flex flex-col ${maxHeight} ${className} animate-in slide-in-from-bottom duration-250`}
      >
        {/* Drag Handle */}
        <div className="pt-3 pb-1 flex justify-center shrink-0">
          <div className="w-12 h-1.5 bg-stone-300 rounded-full" aria-hidden="true" />
        </div>

        {/* Header */}
        {(title || subtitle) && (
          <div className="px-5 py-3 border-b border-stone-100 flex items-start justify-between gap-4 shrink-0">
            <div>
              {title && (
                <h3 id="bottomsheet-title" className="text-lg font-bold text-[#1C252E]">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs sm:text-sm text-[#4B5563] mt-0.5">{subtitle}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close sheet"
              className="p-2 -mr-1 -mt-1 rounded-lg text-stone-500 hover:text-[#1C252E] hover:bg-stone-100 min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147]"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="p-5 overflow-y-auto flex-1 text-left">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-5 py-3.5 bg-[#FAF9F6] border-t border-stone-100 shrink-0 safe-bottom">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default BottomSheet;


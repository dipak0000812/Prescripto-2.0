import React, { useState, useRef, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';

export interface HelpTooltipProps {
  label?: string;
  title: string;
  content: string | React.ReactNode;
}

export const HelpTooltip: React.FC<HelpTooltipProps> = ({ label, title, content }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative inline-block" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-label={`What does ${title} mean?`}
        className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-teal-700 p-0.5 rounded focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-teal-700 transition"
      >
        <HelpCircle className="w-3.5 h-3.5 text-slate-400 hover:text-teal-600 shrink-0" aria-hidden="true" />
        {label && <span className="underline decoration-dotted">{label}</span>}
      </button>

      {isOpen && (
        <div
          role="region"
          aria-label={title}
          className="absolute z-30 bottom-full left-0 mb-2 w-72 sm:w-80 rounded-xl bg-slate-900 text-white p-3.5 shadow-xl text-xs space-y-1.5 animate-in fade-in zoom-in-95 duration-150"
        >
          <div className="flex items-center justify-between pb-1 border-b border-slate-700/60">
            <span className="font-bold text-slate-100 flex items-center gap-1.5">
              {title}
            </span>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white p-0.5 rounded"
              aria-label="Close explainer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="text-[11px] text-slate-300 leading-relaxed font-normal">
            {content}
          </div>
        </div>
      )}
    </div>
  );
};

export default HelpTooltip;

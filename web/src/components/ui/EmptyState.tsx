import React from 'react';
import { Button } from './Button';
import { FileQuestion } from 'lucide-react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`rounded-xl border border-dashed border-stone-300 bg-white p-8 sm:p-12 text-center max-w-lg mx-auto ${className}`}
    >
      <div className="w-14 h-14 rounded-xl bg-[#F4F2EC] text-[#0F5147] flex items-center justify-center mx-auto mb-4 border border-stone-200">
        {icon || <FileQuestion className="w-7 h-7 text-[#0F5147]" aria-hidden="true" />}
      </div>
      <h3 className="text-lg font-bold text-[#1C252E] tracking-tight">{title}</h3>
      <p className="text-sm text-stone-600 mt-2 leading-relaxed max-w-sm mx-auto">
        {description}
      </p>
      {actionLabel && onAction && (
        <div className="mt-6">
          <Button variant="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export default EmptyState;


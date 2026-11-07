import React from 'react';

export interface AvatarProps {
  name: string;
  role?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  src?: string;
  className?: string;
  status?: 'online' | 'busy' | 'offline';
}

export const Avatar: React.FC<AvatarProps> = ({
  name,
  role,
  size = 'md',
  src,
  className = '',
  status,
}) => {
  // Extract 1-2 initials cleanly
  const initials = name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'P';

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm font-semibold',
    lg: 'w-12 h-12 text-base font-bold',
    xl: 'w-16 h-16 text-xl font-bold',
  };

  const statusDotSizes = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
    xl: 'w-3.5 h-3.5',
  };

  const statusColors = {
    online: 'bg-[#047857]',
    busy: 'bg-[#B45309]',
    offline: 'bg-stone-400',
  };

  return (
    <div className={`relative inline-flex items-center justify-center shrink-0 select-none ${className}`}>
      {src ? (
        <img
          src={src}
          alt={name}
          className={`${sizeClasses[size]} rounded-full object-cover border border-stone-200`}
        />
      ) : (
        <div
          aria-label={`${name}${role ? ` (${role})` : ''}`}
          className={`${sizeClasses[size]} rounded-full bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]/50 flex items-center justify-center tracking-tight`}
        >
          {initials}
        </div>
      )}

      {status && (
        <span
          className={`absolute bottom-0 right-0 rounded-full border-2 border-white ${
            statusDotSizes[size]
          } ${statusColors[status]}`}
          aria-hidden="true"
        />
      )}
    </div>
  );
};

export default Avatar;


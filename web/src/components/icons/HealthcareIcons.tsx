import React from 'react';

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  className?: string;
}

// ---------------------------------------------------------------------------
// 1. Medicine Form Icons (1.75px stroke, 24x24 viewBox)
// ---------------------------------------------------------------------------

export const TabletIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M5.6 5.6l12.8 12.8" />
  </svg>
);

export const CapsuleIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <rect x="5.5" y="4" width="13" height="16" rx="6.5" transform="rotate(35 12 12)" />
    <path d="M7.8 15.3l8.4-5.9" />
  </svg>
);

export const SyrupIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    {/* Bottle */}
    <path d="M5 9a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9z" />
    <path d="M7 7V4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3" />
    <path d="M5 13h8" />
    {/* Measuring Spoon */}
    <path d="M19 11a2.5 2.5 0 0 1-2.5 2.5c-.8 0-1.5-.4-2-1" />
    <path d="M16.5 13.5v6a1.5 1.5 0 0 0 3 0v-6" />
  </svg>
);

export const InjectionIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="m18 2 4 4" />
    <path d="m14 6 4 4" />
    <path d="M15 8 9.5 13.5" />
    <path d="m5 13 6 6" />
    <path d="M7 11 3.5 14.5a2 2 0 0 0 0 2.8l3.2 3.2a2 2 0 0 0 2.8 0L13 17" />
    <path d="m3 21 3-3" />
    <path d="m9 9 2 2" />
    <path d="m11 7 2 2" />
  </svg>
);

export const DropsIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    <path d="M12 12a3 3 0 0 0 3 3" />
  </svg>
);

export const CreamIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M7 21h10a1 1 0 0 0 1-1l-2-12H8L6 20a1 1 0 0 0 1 1z" />
    <path d="M9 8V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4" />
    <path d="M8 14h8" />
  </svg>
);

export const InhalerIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M8 3h8v7a4 4 0 0 1-4 4H7a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2" />
    <path d="M8 3v5" />
    <path d="M16 3v5" />
  </svg>
);

// ---------------------------------------------------------------------------
// 2. Schedule Slot Icons (Sunrise, Midday Sun, Moon)
// ---------------------------------------------------------------------------

export const SunriseIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M12 2v4" />
    <path d="m4.93 7.93 2.83 2.83" />
    <path d="m19.07 7.93-2.83 2.83" />
    <path d="M2 18h20" />
    <path d="M20 22H4" />
    <path d="M8 18a4 4 0 0 1 8 0" />
  </svg>
);

export const MiddaySunIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v2" />
    <path d="M12 21v2" />
    <path d="M4.22 4.22l1.42 1.42" />
    <path d="M18.36 18.36l1.42 1.42" />
    <path d="M1 12h2" />
    <path d="M21 12h2" />
    <path d="M4.22 19.78l1.42-1.42" />
    <path d="M18.36 5.64l1.42-1.42" />
  </svg>
);

export const MoonIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
  </svg>
);

// ---------------------------------------------------------------------------
// 3. Food Timing Icons (Before Food, After Food, With Food)
// ---------------------------------------------------------------------------

export const BeforeFoodIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    {/* Plate */}
    <circle cx="15" cy="12" r="7" />
    <circle cx="15" cy="12" r="3.5" />
    {/* Arrow pointing left (before food) */}
    <path d="M7 12H2" />
    <path d="m4.5 9.5-2.5 2.5 2.5 2.5" />
  </svg>
);

export const AfterFoodIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    {/* Plate */}
    <circle cx="9" cy="12" r="7" />
    <circle cx="9" cy="12" r="3.5" />
    {/* Arrow pointing right (after food) */}
    <path d="M17 12h5" />
    <path d="m19.5 9.5 2.5 2.5-2.5 2.5" />
  </svg>
);

export const WithFoodIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    {/* Plate */}
    <circle cx="12" cy="12" r="7" />
    <circle cx="12" cy="12" r="3.5" />
    {/* Fork / Spoon markers */}
    <path d="M3 8v8" />
    <path d="M21 8v8" />
  </svg>
);

// ---------------------------------------------------------------------------
// 4. Clinical Safety & Utility Icons
// ---------------------------------------------------------------------------

export const ShieldSafetyIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

export const CheckmarkIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export const AlertAmberIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

export const ListenIcon: React.FC<IconProps> = ({ size = 24, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
    {...props}
  >
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
  </svg>
);

// Helper function to resolve medicine form string to matching icon
export function getMedicineFormIcon(form?: string | null): React.FC<IconProps> {
  const norm = (form || '').toLowerCase().trim();
  if (norm.includes('cap')) return CapsuleIcon;
  if (norm.includes('syp') || norm.includes('syrup') || norm.includes('susp') || norm.includes('liq')) return SyrupIcon;
  if (norm.includes('inj') || norm.includes('vial') || norm.includes('amp')) return InjectionIcon;
  if (norm.includes('drop')) return DropsIcon;
  if (norm.includes('cream') || norm.includes('gel') || norm.includes('oint') || norm.includes('lotion')) return CreamIcon;
  if (norm.includes('inhal') || norm.includes('respule') || norm.includes('rotacap')) return InhalerIcon;
  return TabletIcon;
}


import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  ariaLabel?: string;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  ariaLabel = 'Navigation tabs',
  className = '',
}) => {
  return (
    <div className={`border-b border-stone-200 w-full ${className}`}>
      <nav
        role="tablist"
        aria-label={ariaLabel}
        className="flex space-x-2 sm:space-x-6 overflow-x-auto no-scrollbar"
      >
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              role="tab"
              id={`tab-${tab.id}`}
              aria-controls={`tabpanel-${tab.id}`}
              aria-selected={isActive}
              disabled={tab.disabled}
              onClick={() => onChange(tab.id)}
              className={`inline-flex items-center gap-2 py-3.5 px-2 text-sm sm:text-base font-semibold border-b-2 transition-colors duration-150 cursor-pointer shrink-0 min-h-[48px] focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] ${
                isActive
                  ? 'border-[#0F5147] text-[#0F5147]'
                  : 'border-transparent text-[#4B5563] hover:text-[#1C252E] hover:border-stone-300'
              } ${tab.disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              {tab.icon && <span className="shrink-0" aria-hidden="true">{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`ml-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                    isActive
                      ? 'bg-[#E6F0EE] text-[#0F5147]'
                      : 'bg-stone-100 text-stone-600'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export const TabPanel: React.FC<{
  id: string;
  activeTab: string;
  children: React.ReactNode;
  className?: string;
}> = ({ id, activeTab, children, className = '' }) => {
  if (id !== activeTab) return null;
  return (
    <div
      role="tabpanel"
      id={`tabpanel-${id}`}
      aria-labelledby={`tab-${id}`}
      className={`py-4 ${className}`}
    >
      {children}
    </div>
  );
};

export default Tabs;


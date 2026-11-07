import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

export const OfflineBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-amber-600 text-white text-xs font-medium px-4 py-2 flex items-center justify-center gap-2 shadow-xs shrink-0"
    >
      <WifiOff className="w-4 h-4 shrink-0" />
      <span>You are currently offline. Medicines and schedules saved locally remain readable.</span>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="underline font-bold ml-1 cursor-pointer hover:text-amber-100"
      >
        Retry
      </button>
    </div>
  );
};

export default OfflineBanner;


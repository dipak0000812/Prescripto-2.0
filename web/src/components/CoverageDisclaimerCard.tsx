import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface CoverageDisclaimerCardProps {
  disclaimer?: string;
}

export const CoverageDisclaimerCard: React.FC<CoverageDisclaimerCardProps> = ({ disclaimer }) => {
  const defaultDisclaimer =
    'Prescripto 2.0 extracts structured medication data and checks against clinical safety guidelines. It does not replace professional diagnosis or prescriptions. Always verify each medicine with your doctor or chemist.';

  return (
    <div className="bg-[#FEF3C7]/60 border-l-4 border-[#B45309] border border-[#FCD34D] rounded-r-2xl rounded-l-md p-4 text-xs text-[#78350F] shadow-2xs text-left">
      <div className="flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-[#B45309] shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-1">
          <div className="font-bold tracking-tight text-[#78350F] uppercase text-[11px]">
            Clinical Safety & Decision Support Notice
          </div>
          <p className="leading-relaxed text-[#78350F]">
            {disclaimer || defaultDisclaimer}
          </p>
          <div className="text-[11px] text-[#B45309] font-medium">
            Clinical Notice: Assistive AI output provides clinical decision support and does not replace professional medical judgment.
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoverageDisclaimerCard;

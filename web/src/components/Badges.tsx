import React from 'react';
import { FieldState, FindingStatus, AnalysisStatusEnum, Role, ResolutionStatus } from '../types/api';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle, ShieldAlert, Clock, Eye, ShieldCheck } from 'lucide-react';

export const FieldStateBadge: React.FC<{ state: FieldState }> = ({ state }) => {
  switch (state) {
    case 'CLEAR':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />
          <span>Readable · verify</span>
        </span>
      );
    case 'AMBIGUOUS':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FEF3C7] text-[#78350F] border border-[#FCD34D]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />
          <span>Needs review</span>
        </span>
      );
    case 'UNREADABLE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FFE4E6] text-[#881337] border border-[#FDA4AF]">
          <AlertCircle className="w-3.5 h-3.5 text-[#BE123C]" aria-hidden="true" />
          <span>Illegible Text</span>
        </span>
      );
    case 'NOT_PRESENT':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F4F2EC] text-[#1C252E] border border-stone-200">
          <HelpCircle className="w-3.5 h-3.5 text-stone-500" aria-hidden="true" />
          <span>No value extracted</span>
        </span>
      );
  }
};

export const ResolutionStatusBadge: React.FC<{ status: ResolutionStatus }> = ({ status }) => {
  switch (status) {
    case 'RESOLVED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
          <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />
          <span>Catalog match</span>
        </span>
      );
    case 'AMBIGUOUS':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FEF3C7] text-[#78350F] border border-[#FCD34D]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />
          <span>Multiple Matches</span>
        </span>
      );
    case 'UNRESOLVED':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F4F2EC] text-[#1C252E] border border-stone-200">
          <HelpCircle className="w-3.5 h-3.5 text-stone-500" aria-hidden="true" />
          <span>No catalog match</span>
        </span>
      );
  }
};

export const FindingStatusBadge: React.FC<{ status: FindingStatus }> = ({ status }) => {
  switch (status) {
    case 'CONFIRMED_BY_SOURCE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-[#FFE4E6] text-[#881337] border border-[#FDA4AF]">
          <AlertCircle className="w-3.5 h-3.5 text-[#BE123C]" aria-hidden="true" />
          <span>Active Clinical Alert</span>
        </span>
      );
    case 'POTENTIAL':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FEF3C7] text-[#78350F] border border-[#FCD34D]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />
          <span>Potential Concern</span>
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          <HelpCircle className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
          <span>Check Evidence</span>
        </span>
      );
    case 'NOT_EVALUATED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F4F2EC] text-[#1C252E] border border-stone-200">
          <Clock className="w-3.5 h-3.5 text-stone-500" aria-hidden="true" />
          <span>Deferred Check</span>
        </span>
      );
    case 'REQUIRES_REVIEW':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FEF3C7] text-[#78350F] border border-[#FCD34D]">
          <Eye className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />
          <span>Human review needed</span>
        </span>
      );
  }
};

export const AnalysisStatusBadge: React.FC<{ status: AnalysisStatusEnum }> = ({ status }) => {
  switch (status) {
    case 'QUEUED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F4F2EC] text-[#1C252E] border border-stone-200">
          <Clock className="w-3.5 h-3.5 text-stone-500" aria-hidden="true" />
          <span>In Queue</span>
        </span>
      );
    case 'PROCESSING':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          <div className="w-2 h-2 rounded-full bg-[#0F5147] animate-pulse" aria-hidden="true" />
          <span>Reading Prescription...</span>
        </span>
      );
    case 'COMPLETED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />
          <span>Extraction complete</span>
        </span>
      );
    case 'REQUIRES_REVIEW':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FEF3C7] text-[#78350F] border border-[#FCD34D]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#B45309]" aria-hidden="true" />
          <span>Doctor Review Needed</span>
        </span>
      );
    case 'REVIEWING':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          <Eye className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
          <span>In Clinical Review</span>
        </span>
      );
    case 'REVIEWED_COMPLETE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />
          <span>Human review complete</span>
        </span>
      );
    case 'REVIEWED_ESCALATED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FFE4E6] text-[#881337] border border-[#FDA4AF]">
          <ShieldAlert className="w-3.5 h-3.5 text-[#BE123C]" aria-hidden="true" />
          <span>Escalated for Consultation</span>
        </span>
      );
    case 'FAILED':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#FFE4E6] text-[#881337] border border-[#FDA4AF]">
          <AlertCircle className="w-3.5 h-3.5 text-[#BE123C]" aria-hidden="true" />
          <span>Scan Error</span>
        </span>
      );
  }
};

export const RoleBadge: React.FC<{ role: Role; isPatient?: boolean }> = ({ role, isPatient }) => {
  if (isPatient) {
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
        Patient
      </span>
    );
  }
  switch (role) {
    case 'ADMIN':
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-[#F4F2EC] text-[#1C252E] border border-stone-300">
          Administrator
        </span>
      );
    case 'REVIEWER':
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          Doctor / Reviewer
        </span>
      );
    case 'OPERATOR':
    default:
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          Intake Staff
        </span>
      );
  }
};

import React from 'react';
import { FieldState, FindingStatus, AnalysisStatusEnum, Role, ResolutionStatus } from '../types/api';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle, ShieldAlert, Clock, Check, Eye, ShieldCheck } from 'lucide-react';

export const FieldStateBadge: React.FC<{ state: FieldState; confidence?: number }> = ({ state, confidence }) => {
  const pct = confidence !== undefined ? `${Math.round(confidence * 100)}%` : null;

  switch (state) {
    case 'CLEAR':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          <span>Clear {pct && `(${pct})`}</span>
        </span>
      );
    case 'AMBIGUOUS':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" />
          <span>Low Confidence {pct && `(${pct})`}</span>
        </span>
      );
    case 'UNREADABLE':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200">
          <AlertCircle className="w-3 h-3 text-rose-600" />
          <span>Illegible Text</span>
        </span>
      );
    case 'NOT_PRESENT':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
          <HelpCircle className="w-3 h-3 text-slate-500" />
          <span>Not Indicated</span>
        </span>
      );
  }
};

export const ResolutionStatusBadge: React.FC<{ status: ResolutionStatus }> = ({ status }) => {
  switch (status) {
    case 'RESOLVED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          Drug Verified
        </span>
      );
    case 'AMBIGUOUS':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" />
          Multiple Potential Matches
        </span>
      );
    case 'UNRESOLVED':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
          <HelpCircle className="w-3 h-3 text-slate-500" />
          Unregistered Medication
        </span>
      );
  }
};

export const FindingStatusBadge: React.FC<{ status: FindingStatus }> = ({ status }) => {
  switch (status) {
    case 'CONFIRMED_BY_SOURCE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
          Active Clinical Alert
        </span>
      );
    case 'POTENTIAL':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          Potential Concern
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-purple-50 text-purple-800 border border-purple-200">
          <HelpCircle className="w-3.5 h-3.5 text-purple-600" />
          Check Evidence
        </span>
      );
    case 'NOT_EVALUATED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          Deferred Check
        </span>
      );
    case 'REQUIRES_REVIEW':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          <Eye className="w-3.5 h-3.5 text-amber-600" />
          Physician Review Needed
        </span>
      );
  }
};

export const AnalysisStatusBadge: React.FC<{ status: AnalysisStatusEnum }> = ({ status }) => {
  switch (status) {
    case 'QUEUED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          In Queue
        </span>
      );
    case 'PROCESSING':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
          <div className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
          Analyzing Prescription...
        </span>
      );
    case 'COMPLETED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          Safety Verified
        </span>
      );
    case 'REQUIRES_REVIEW':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          Doctor Review Needed
        </span>
      );
    case 'REVIEWING':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200">
          <Eye className="w-3.5 h-3.5 text-indigo-600" />
          In Clinical Review
        </span>
      );
    case 'REVIEWED_COMPLETE':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
          Clinically Approved
        </span>
      );
    case 'REVIEWED_ESCALATED':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
          <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
          Escalated for Consultation
        </span>
      );
    case 'FAILED':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
          Scan Error
        </span>
      );
  }
};

export const RoleBadge: React.FC<{ role: Role; isPatient?: boolean }> = ({ role, isPatient }) => {
  if (isPatient) {
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-emerald-50 text-emerald-800 border border-emerald-200">
        Patient
      </span>
    );
  }
  switch (role) {
    case 'ADMIN':
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-purple-50 text-purple-800 border border-purple-200">
          Administrator
        </span>
      );
    case 'REVIEWER':
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-blue-50 text-blue-800 border border-blue-200">
          Doctor / Reviewer
        </span>
      );
    case 'OPERATOR':
    default:
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase bg-teal-50 text-teal-800 border border-teal-200">
          Intake Staff
        </span>
      );
  }
};

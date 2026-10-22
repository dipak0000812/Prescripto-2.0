/**
 * Prescripto AI 2.0 — Canonical API & Domain Types
 * Strictly aligned with OPENAPI.yaml and PROJECT-SPEC.md.
 */

export type Role = 'OPERATOR' | 'REVIEWER' | 'ADMIN' | 'DOCTOR' | 'CLINICIAN';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user?: {
    id: string;
    username: string;
    email: string;
    role: Role;
    patient_id?: string;
    patient_name?: string;
    phone_number?: string;
    is_patient?: boolean;
    [key: string]: any;
  };
}

export interface PatientProfile {
  id?: string;
  patient_id: string;
  name: string;
  phone_number: string;
  age?: number | null;
  gender?: string | null;
  blood_group?: string | null;
  address?: string | null;
  medical_history?: string | null;
  allergies?: string | null;
  emergency_contact?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface UserSession {
  user_id: string;
  username: string;
  email?: string;
  role: Role;
  access_token: string;
  refresh_token: string;
  expires_at: number; // Unix timestamp in seconds
  patient_id?: string;
  patient_name?: string;
  phone_number?: string;
  is_patient?: boolean;
}

export type FieldState = 'CLEAR' | 'AMBIGUOUS' | 'UNREADABLE' | 'NOT_PRESENT';

export type ResolutionStatus = 'RESOLVED' | 'UNRESOLVED' | 'AMBIGUOUS';

export type FindingStatus =
  | 'CONFIRMED_BY_SOURCE'
  | 'POTENTIAL'
  | 'INSUFFICIENT_EVIDENCE'
  | 'NOT_EVALUATED'
  | 'REQUIRES_REVIEW';

export type SafetyCheckType =
  | 'DUPLICATE_MEDICATION'
  | 'EVIDENCE_LOOKUP'
  | 'ADVERSE_EFFECT';

export type AnalysisStatusEnum =
  | 'QUEUED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'REQUIRES_REVIEW'
  | 'REVIEWING'
  | 'REVIEWED_COMPLETE'
  | 'REVIEWED_ESCALATED'
  | 'FAILED';

export type StageName =
  | 'INGESTION'
  | 'QUALITY_CHECK'
  | 'TEXT_DETECTION'
  | 'OCR_RECOGNITION'
  | 'STRUCTURED_EXTRACTION'
  | 'MEDICATION_NORMALIZATION'
  | 'SAFETY_SCREENING'
  | 'REPORT_ASSEMBLY';

export type StageStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

export type DocumentStatus =
  | 'UPLOAD_PENDING'
  | 'UPLOADED'
  | 'DELETION_REQUESTED'
  | 'DELETION_IN_PROGRESS'
  | 'DELETED';

export type NotEvaluatedReason =
  | 'SOURCE_UNAVAILABLE'
  | 'PROVIDER_LACKS_CAPABILITY'
  | 'UNRESOLVED_IDENTITY'
  | 'AMBIGUOUS_IDENTITY'
  | 'SOURCE_NOT_COVERING'
  | 'CHECK_TYPE_DEFERRED'
  | 'LICENSE_MODE_EXCLUDED'
  | string;

export type ReviewAction = 'APPROVED' | 'FLAGGED' | 'ESCALATED';

export interface FieldValue {
  value: string | null;
  state: FieldState;
  confidence: number;
}

export interface MedicationLine {
  line_index: number;
  name: FieldValue;
  strength: FieldValue;
  dose: FieldValue;
  unit: FieldValue;
  frequency: FieldValue;
  route: FieldValue;
  duration: FieldValue;
  instructions: FieldValue;
  resolved_medication_id: string | null;
  resolution_status: ResolutionStatus;
}

export interface RiskFindingOut {
  finding_id: string;
  finding_status: FindingStatus;
  check_type: SafetyCheckType;
  medication_ids: string[];
  evidence_text: string | null;
  source_name: string;
  source_version: string;
  confidence_score: number | null;
  check_timestamp: string;
  not_evaluated_reason: string | null;
}

export interface NotEvaluatedItem {
  medication_ids: string[];
  reason: NotEvaluatedReason;
}

export interface AnalysisStageOut {
  stage_name: StageName;
  status: StageStatus;
  error_code: string | null;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: AnalysisStatusEnum;
  stages: AnalysisStageOut[];
}

export interface AnalysisResult {
  analysis_id: string;
  status: AnalysisStatusEnum;
  analysis_timestamp: string;
  model_versions: string[];
  knowledge_snapshots: string[];
  medications: MedicationLine[];
  findings: RiskFindingOut[];
  not_evaluated: NotEvaluatedItem[];
  coverage_disclaimer: string;
}

export interface ReviewDecision {
  finding_id: string;
  action: ReviewAction;
  notes?: string | null;
}

export interface ReviewSubmission {
  decisions: ReviewDecision[];
}

export interface ReviewRecord {
  review_id: string;
  analysis_id: string;
  reviewer_id: string;
  submitted_at: string;
  overall_status: 'REVIEWED_COMPLETE' | 'REVIEWED_ESCALATED';
}

export interface PrescriptionSummary {
  prescription_id: string;
  uploaded_at: string;
  status: DocumentStatus;
  latest_analysis_status: AnalysisStatusEnum | null;
  latest_analysis_id?: string | null;
  patient_ref?: string | null;
  patient_name?: string | null;
}

export interface PrescriptionListResponse {
  items: PrescriptionSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface AnalysisSummaryItem {
  analysis_id: string;
  status: AnalysisStatusEnum;
  created_at: string;
}

export interface PrescriptionDetail {
  prescription_id: string;
  status: DocumentStatus;
  uploaded_at: string;
  mime_type: string;
  file_size_bytes: number;
  patient_ref: string | null;
  image_url: string | null;
  analyses: AnalysisSummaryItem[];
}

export interface UploadAccepted {
  analysis_id: string;
  prescription_id: string;
}

export interface DeletionAccepted {
  deletion_job_id: string;
}

export interface HealthStatus {
  database: 'ok' | 'degraded' | 'down';
  object_storage: 'ok' | 'degraded' | 'down';
  worker_heartbeat: 'ok' | 'stale' | 'down';
}

export interface ApiError {
  code: string;
  message: string;
  request_id: string;
}

export interface ApiErrorResponse {
  error: ApiError;
}

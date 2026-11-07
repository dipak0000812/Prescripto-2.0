export interface PrescriptionVolume {
  date: string;
  count: number;
  completed: number;
  pending_review: number;
  failed: number;
}

export interface SafetyMetrics {
  total_findings: number;
  confirmed_by_source: number;
  potential: number;
  requires_review: number;
  insufficient_evidence: number;
  not_evaluated: number;
  top_check_types: Array<{ check_type: string; count: number }>;
}

export interface DoctorWorkload {
  doctor_id: string;
  doctor_name: string;
  assigned_patients: number;
  pending_reviews: number;
  completed_reviews: number;
  avg_review_time_hours: number;
}

export interface SystemHealthMetrics {
  api_uptime_pct: number;
  avg_response_time_ms: number;
  error_rate_pct: number;
  active_workers: number;
  queue_depth: number;
  storage_used_gb: number;
}

export interface AnalyticsDashboardResponse {
  prescription_volume: PrescriptionVolume[];
  safety_metrics: SafetyMetrics;
  doctor_workload: DoctorWorkload[];
  system_health: SystemHealthMetrics;
  generated_at: string;
}

export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
  granularity?: 'day' | 'week' | 'month';
}
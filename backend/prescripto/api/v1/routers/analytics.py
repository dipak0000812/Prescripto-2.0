"""
Analytics Router: Clinical Workload, Safety Metrics, and System Health Dashboard.
Restricted to ADMIN and REVIEWER roles.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date

from prescripto.db.session import get_db
from prescripto.auth.dependencies import get_current_user, require_role
from prescripto.db.models.enums import Role
from prescripto.db.models.users import User
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.doctor_patient import DoctorPatient
from prescripto.db.models.review import Review
from prescripto.api.v1.schemas.analytics import (
    AnalyticsDashboardResponse,
    PrescriptionVolume,
    SafetyMetrics,
    DoctorWorkload,
    SystemHealthMetrics,
    DateRangeParams,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def parse_date_range(start: str | None, end: str | None, default_days: int = 30) -> tuple[datetime, datetime]:
    """Parse date range with defaults."""
    now = datetime.now(timezone.utc)
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else now
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else (end_dt - timedelta(days=default_days))
    return start_dt, end_dt


@router.get(
    "/dashboard",
    response_model=AnalyticsDashboardResponse,
    summary="Get clinical dashboard analytics (Admin/Reviewer only)",
    operation_id="getAnalyticsDashboard",
)
def get_analytics_dashboard(
    start_date: str | None = Query(default=None, description="ISO date start"),
    end_date: str | None = Query(default=None, description="ISO date end"),
    granularity: str = Query(default="day", description="day | week | month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.REVIEWER)),
) -> AnalyticsDashboardResponse:
    """
    Returns comprehensive analytics dashboard for clinical operations.
    Includes prescription volume, safety metrics, doctor workload, and system health.
    """
    start_dt, end_dt = parse_date_range(start_date, end_date)

    # 1. Prescription Volume over time
    volume_query = db.query(
        cast(PrescriptionDocument.uploaded_at, Date).label("date"),
        func.count(PrescriptionDocument.id).label("count"),
        func.sum(
            func.case(
                (PrescriptionDocument.status == "UPLOADED", 1),
                else_=0
            )
        ).label("uploaded"),
        func.sum(
            func.case(
                (Analysis.status.in_(["REQUIRES_REVIEW", "REVIEWING"]), 1),
                else_=0
            )
        ).label("pending_review"),
        func.sum(
            func.case(
                (Analysis.status == "FAILED", 1),
                else_=0
            )
        ).label("failed"),
    ).outerjoin(
        Analysis, Analysis.document_id == PrescriptionDocument.id
    ).filter(
        PrescriptionDocument.uploaded_at >= start_dt,
        PrescriptionDocument.uploaded_at <= end_dt,
        PrescriptionDocument.status != "DELETED",
    ).group_by(
        cast(PrescriptionDocument.uploaded_at, Date)
    ).order_by(
        cast(PrescriptionDocument.uploaded_at, Date)
    ).all()

    prescription_volume = [
        PrescriptionVolume(
            date=str(row.date),
            count=row.count or 0,
            completed=(row.count or 0) - (row.pending_review or 0) - (row.failed or 0),
            pending_review=row.pending_review or 0,
            failed=row.failed or 0,
        )
        for row in volume_query
    ]

    # 2. Safety Metrics
    safety_query = db.query(
        RiskFinding.finding_status,
        RiskFinding.check_type,
        func.count(RiskFinding.id).label("count"),
    ).join(
        Analysis, Analysis.id == RiskFinding.analysis_id
    ).join(
        PrescriptionDocument, PrescriptionDocument.id == Analysis.document_id
    ).filter(
        Analysis.created_at >= start_dt,
        Analysis.created_at <= end_dt,
    ).group_by(
        RiskFinding.finding_status,
        RiskFinding.check_type
    ).all()

    status_counts: Dict[str, int] = {}
    check_type_counts: Dict[str, int] = {}

    for row in safety_query:
        status_counts[row.finding_status] = status_counts.get(row.finding_status, 0) + row.count
        check_type_counts[row.check_type] = check_type_counts.get(row.check_type, 0) + row.count

    top_check_types = [
        {"check_type": k, "count": v}
        for k, v in sorted(check_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    safety_metrics = SafetyMetrics(
        total_findings=sum(status_counts.values()),
        confirmed_by_source=status_counts.get("CONFIRMED_BY_SOURCE", 0),
        potential=status_counts.get("POTENTIAL", 0),
        requires_review=status_counts.get("REQUIRES_REVIEW", 0),
        insufficient_evidence=status_counts.get("INSUFFICIENT_EVIDENCE", 0),
        not_evaluated=status_counts.get("NOT_EVALUATED", 0),
        top_check_types=top_check_types,
    )

    # 3. Doctor Workload
    workload_query = db.query(
        User.id,
        User.username,
        func.count(DoctorPatient.patient_id).label("assigned_patients"),
        func.count(Review.id).label("completed_reviews"),
        func.avg(
            func.extract('epoch', Review.submitted_at - Analysis.created_at) / 3600
        ).label("avg_review_time_hours"),
    ).outerjoin(
        DoctorPatient, DoctorPatient.doctor_id == User.id
    ).outerjoin(
        Review, Review.reviewer_id == User.id
    ).outerjoin(
        Analysis, Analysis.id == Review.analysis_id
    ).filter(
        User.role.in_([Role.REVIEWER.value, "DOCTOR", "CLINICIAN"]),
        User.is_active == True,
    ).group_by(
        User.id, User.username
    ).all()

    doctor_workload = [
        DoctorWorkload(
            doctor_id=str(row.id),
            doctor_name=row.username,
            assigned_patients=row.assigned_patients or 0,
            pending_reviews=0,  # Would need more complex query
            completed_reviews=row.completed_reviews or 0,
            avg_review_time_hours=round(float(row.avg_review_time_hours), 2) if row.avg_review_time_hours else 0.0,
        )
        for row in workload_query
    ]

    # 4. System Health (placeholder - would integrate with actual monitoring)
    system_health = SystemHealthMetrics(
        api_uptime_pct=99.9,
        avg_response_time_ms=145.0,
        error_rate_pct=0.2,
        active_workers=1,
        queue_depth=db.query(Analysis).filter(Analysis.status.in_(["QUEUED", "PROCESSING"])).count(),
        storage_used_gb=0.0,
    )

    return AnalyticsDashboardResponse(
        prescription_volume=prescription_volume,
        safety_metrics=safety_metrics,
        doctor_workload=doctor_workload,
        system_health=system_health,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/prescription-trends",
    response_model=List[PrescriptionVolume],
    summary="Get prescription volume trends over time",
    operation_id="getPrescriptionTrends",
)
def get_prescription_trends(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    granularity: str = Query(default="day"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.REVIEWER)),
) -> List[PrescriptionVolume]:
    """Get prescription upload volume trends for charting."""
    start_dt, end_dt = parse_date_range(start_date, end_date)

    volume_query = db.query(
        cast(PrescriptionDocument.uploaded_at, Date).label("date"),
        func.count(PrescriptionDocument.id).label("count"),
    ).filter(
        PrescriptionDocument.uploaded_at >= start_dt,
        PrescriptionDocument.uploaded_at <= end_dt,
        PrescriptionDocument.status != "DELETED",
    ).group_by(
        cast(PrescriptionDocument.uploaded_at, Date)
    ).order_by(
        cast(PrescriptionDocument.uploaded_at, Date)
    ).all()

    return [
        PrescriptionVolume(
            date=str(row.date),
            count=row.count or 0,
            completed=row.count or 0,
            pending_review=0,
            failed=0,
        )
        for row in volume_query
    ]


@router.get(
    "/safety-summary",
    response_model=SafetyMetrics,
    summary="Get aggregated safety screening metrics",
    operation_id="getSafetySummary",
)
def get_safety_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.REVIEWER)),
) -> SafetyMetrics:
    """Get safety finding summary statistics."""
    start_dt, end_dt = parse_date_range(start_date, end_date)

    safety_query = db.query(
        RiskFinding.finding_status,
        RiskFinding.check_type,
        func.count(RiskFinding.id).label("count"),
    ).join(
        Analysis, Analysis.id == RiskFinding.analysis_id
    ).filter(
        Analysis.created_at >= start_dt,
        Analysis.created_at <= end_dt,
    ).group_by(
        RiskFinding.finding_status,
        RiskFinding.check_type
    ).all()

    status_counts: Dict[str, int] = {}
    check_type_counts: Dict[str, int] = {}

    for row in safety_query:
        status_counts[row.finding_status] = status_counts.get(row.finding_status, 0) + row.count
        check_type_counts[row.check_type] = check_type_counts.get(row.check_type, 0) + row.count

    top_check_types = [
        {"check_type": k, "count": v}
        for k, v in sorted(check_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return SafetyMetrics(
        total_findings=sum(status_counts.values()),
        confirmed_by_source=status_counts.get("CONFIRMED_BY_SOURCE", 0),
        potential=status_counts.get("POTENTIAL", 0),
        requires_review=status_counts.get("REQUIRES_REVIEW", 0),
        insufficient_evidence=status_counts.get("INSUFFICIENT_EVIDENCE", 0),
        not_evaluated=status_counts.get("NOT_EVALUATED", 0),
        top_check_types=top_check_types,
    )
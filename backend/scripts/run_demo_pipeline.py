"""
Prescripto AI 2.0 — Interactive End-to-End Demonstration Script.
Loads a prescription image, executes the real AI/ML OCR pipeline, and outputs
extracted medications, dosages, normalization matches, and safety alerts.
"""
import os
import sys
import uuid
import hashlib
from io import BytesIO
from PIL import Image

# Ensure backend is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from prescripto.db.session import SessionLocal
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.users import User
from prescripto.db.base import utc_now
from prescripto.storage.client import get_storage_client
from prescripto.worker.main import WorkerRunner
from prescripto.ml.rapid_runtime import RapidOCRRuntime


def run_demo(image_path: str = "sample_prescription.png"):
    repo_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
    full_image_path = os.path.join(repo_root, image_path) if not os.path.isabs(image_path) else image_path
    
    if not os.path.exists(full_image_path):
        # Generate sample prescription if missing
        from sample_prescription import generate_prescription
        generate_prescription(full_image_path)

    print("\n" + "=" * 70)
    print("      PRESCRIPTO AI 2.0 — END-TO-END DEMO EXECUTION")
    print("=" * 70)
    print(f"[1] Target Prescription Image: {full_image_path}")
    
    with open(full_image_path, "rb") as f:
        img_bytes = f.read()

    file_hash = hashlib.sha256(img_bytes).hexdigest()
    file_size_kb = len(img_bytes) / 1024.0

    db = SessionLocal()
    storage = get_storage_client()
    doc_id = uuid.uuid4()
    storage_key = storage.generate_prescription_key(doc_id, "png")
    storage.put_object(key=storage_key, data=img_bytes, content_type="image/png")

    active_model = db.query(ModelVersion).first()
    if not active_model:
        active_model = ModelVersion(
            id=uuid.uuid4(),
            model_name="rapidocr-onnx",
            model_version="1.4.4",
            checkpoint_sha256="default",
            artifact_storage_key="models/rapidocr",
            framework="ONNX",
            license="Apache-2.0",
        )
        db.add(active_model)
        db.flush()

    uploader = db.query(User).first()
    uploader_id = uploader.id if uploader else uuid.uuid4()

    doc = PrescriptionDocument(
        id=doc_id,
        uploader_id=uploader_id,
        patient_ref="PATIENT-DEMO-001",
        storage_key=storage_key,
        file_hash_sha256=file_hash,
        mime_type="image/png",
        file_size_bytes=len(img_bytes),
        status="UPLOADED",
        uploaded_at=utc_now(),
    )
    db.add(doc)
    db.flush()

    analysis_id = uuid.uuid4()
    analysis = Analysis(
        id=analysis_id,
        document_id=doc_id,
        status="QUEUED",
        pipeline_version="1.0.0",
        model_snapshot_id=active_model.id,
    )
    db.add(analysis)
    db.flush()

    job_id = uuid.uuid4()
    job = AnalysisJob(
        id=job_id,
        analysis_id=analysis_id,
        status="PENDING",
        lease_token=0,
        retry_count=0,
        max_retries=3,
    )
    db.add(job)
    db.commit()

    print(f"[2] Ingested Document ID: {doc_id} ({file_size_kb:.1f} KB)")
    print(f"[3] Queued Analysis Job ID: {job_id}")
    print("[4] Executing 8 Canonical Pipeline Stages with Real OCR...")

    # Run the worker engine using RapidOCRRuntime (ONNX CPU PaddleOCR)
    ocr_runtime = RapidOCRRuntime()
    runner = WorkerRunner(
        session_factory=SessionLocal,
        worker_id="demo-runner-01",
        poll_interval=0.1,
        lease_seconds=600,
        ocr_runtime=ocr_runtime,
    )
    success = runner.run_once()

    print(f"\n[5] Pipeline Run Complete (Worker Success: {success})")

    # Fetch and display structured results
    db.expire_all()
    analysis_res = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    meds = db.query(PrescriptionMedication).filter(PrescriptionMedication.analysis_id == analysis_id).order_by(PrescriptionMedication.line_index).all()
    risks = db.query(RiskFinding).filter(RiskFinding.analysis_id == analysis_id).all()

    status_str = getattr(analysis_res.status, "value", str(analysis_res.status))
    print("-" * 70)
    print(f"ANALYSIS STATUS  : {status_str}")
    print(f"REVIEW REQUIRED  : {analysis_res.review_required}")
    print("-" * 70)

    print("\n" + "=" * 70)
    print("           EXTRACTED MEDICATIONS & PRESCRIPTION DETAILS")
    print("=" * 70)
    
    recognized_drugs_count = 0
    for med in meds:
        # Check if this line contains medicine or prescription info
        has_drug_info = med.strength_raw or med.dose_raw or med.frequency_raw or med.duration_raw
        cand = db.query(MedicationCandidate).filter(MedicationCandidate.prescription_med_id == med.id).first()
        if cand and cand.candidate_score > 0:
            drug_name = cand.resolved_medication.brand_name if cand.resolved_medication else cand.extracted_text
            matched_str = f"-> Matched Master: {drug_name} ({cand.matching_strategy}, Score: {cand.candidate_score})"
        else:
            matched_str = "-> No master match"

        if has_drug_info or (cand and cand.candidate_score >= 0.85):
            recognized_drugs_count += 1
            print(f"\n[Medication #{recognized_drugs_count}] (Line {med.line_index})")
            print(f"  • Extracted Text  : {med.name_raw}")
            if med.strength_raw:
                print(f"  • Strength        : {med.strength_raw} (State: {med.strength_state})")
            if med.dose_raw:
                print(f"  • Dosage / Form   : {med.dose_raw} (Unit: {med.unit_raw or 'N/A'})")
            if med.frequency_raw:
                print(f"  • Frequency (Sig) : {med.frequency_raw}")
            if med.duration_raw:
                print(f"  • Duration        : {med.duration_raw}")
            if med.instructions_raw:
                print(f"  • Instructions    : {med.instructions_raw}")
            print(f"  • Catalog Status  : {matched_str}")

    print("\n" + "=" * 70)
    print(f"Summary: Found {recognized_drugs_count} actionable medication items across {len(meds)} lines.")
    if risks:
        print(f"Safety Warnings: {len(risks)} risk findings generated.")
        for r in risks:
            print(f"  [!] [{r.check_type}] {r.finding_key} ({r.finding_status}): {r.evidence_text or 'Flagged for review'}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    img_arg = sys.argv[1] if len(sys.argv) > 1 else "sample_prescription.png"
    run_demo(img_arg)

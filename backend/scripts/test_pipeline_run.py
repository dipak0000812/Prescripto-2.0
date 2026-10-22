import uuid
import hashlib
from prescripto.db.session import SessionLocal
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.users import User
from prescripto.db.base import utc_now
from prescripto.storage.client import get_storage_client
from prescripto.worker.main import WorkerRunner
from prescripto.ml.rapid_runtime import RapidOCRRuntime

def test():
    db = SessionLocal()
    storage = get_storage_client()
    with open('sample_prescription.png', 'rb') as f:
        img_bytes = f.read()

    file_hash = hashlib.sha256(img_bytes).hexdigest()
    doc_id = uuid.uuid4()
    storage_key = storage.generate_prescription_key(doc_id, 'png')
    storage.put_object(key=storage_key, data=img_bytes, content_type='image/png')

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
        patient_ref="TEST-PATIENT-001",
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
        review_required=False,
        review_reasons=[],
        created_at=utc_now(),
    )
    db.add(analysis)

    # Clean any stale jobs from previous tests
    db.query(AnalysisJob).delete()
    db.commit()

    # Pre-warm RapidOCR so engine is ready
    ocr = RapidOCRRuntime()
    ocr._get_engine()

    job = AnalysisJob(
        id=uuid.uuid4(),
        analysis_id=analysis_id,
        status="PENDING",
        retry_count=0,
        max_retries=3,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(job)
    db.commit()
    db.close()

    print(f"Queued Job for Analysis ID: {analysis_id}")

    # Run WorkerRunner with RapidOCRRuntime
    worker = WorkerRunner(ocr_runtime=ocr)
    found_and_ran = worker.run_once()
    print(f"Worker executed job: {found_and_ran}")

    # Inspect results
    db = SessionLocal()
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    print(f"Analysis Status: {analysis.status}")
    print(f"Review Required: {analysis.review_required}")
    print(f"Review Reasons: {analysis.review_reasons}")

    from prescripto.db.models.medication import PrescriptionMedication
    meds = db.query(PrescriptionMedication).filter(PrescriptionMedication.analysis_id == analysis_id).all()
    print(f"Total lines extracted in DB: {len(meds)}")
    for m in meds:
        if m.name_raw:
            print(f"Line {m.line_index}: raw='{m.name_raw}' | Str: {m.strength_raw} | Dose: {m.dose_raw} | Freq: {m.frequency_raw} | State: {m.name_state}")

    from prescripto.db.models.medication import MedicationCandidate
    candidates = db.query(MedicationCandidate).filter(MedicationCandidate.analysis_id == analysis_id).all()
    print(f"Total candidates/resolutions: {len(candidates)}")
    for c in candidates:
        med_name = c.resolved_medication.brand_name if c.resolved_medication else "None"
        print(f"Resolution status: {c.resolution_status} | Extracted: '{c.extracted_text}' | Match: {c.matching_strategy} ({c.candidate_score}) | Resolved: {med_name}")

    db.close()

if __name__ == '__main__':
    test()

"""
API-Level Smoke Test for Prescripto 2.0.
Can run against a live running stack (e.g. http://127.0.0.1:8000) or in-process via TestClient.
Executes operator upload workflow, Gemini recognition validation, image URL check, and PATIENT RBAC gating.
"""
from __future__ import annotations

import io
import os
import sys
import time
import uuid
from typing import Any, Dict, Optional

# Ensure project root and backend are on PYTHONPATH
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
for p in [BACKEND_DIR, PROJECT_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from prescripto.config.settings import settings
from prescripto.db.session import SessionLocal
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.patient import Patient
from prescripto.auth.crypto import hash_password


OPERATOR_USER = "smoke_operator"
OPERATOR_PASS = "OperatorPass123!"
PATIENT_USER = "smoke_patient"
PATIENT_PASS = "PatientPass123!"
OTHER_PATIENT_ID = "PAT-1001"


def ensure_db_fixtures():
    """Ensures test users, model version, and target patient exist in the DB."""
    db = SessionLocal()
    try:
        # Operator user
        op = db.query(User).filter(User.username == OPERATOR_USER).first()
        if not op:
            op = User(
                id=uuid.uuid4(),
                username=OPERATOR_USER,
                email="smoke_op@prescripto.local",
                hashed_password=hash_password(OPERATOR_PASS),
                role=Role.OPERATOR.value,
                is_active=True,
            )
            db.add(op)

        # Active ModelVersion
        mv = db.query(ModelVersion).first()
        if not mv:
            mv = ModelVersion(
                id=uuid.uuid4(),
                model_name="rapidocr-onnx",
                model_version="1.4.4",
                checkpoint_sha256="0" * 64,
                artifact_storage_key="models/rapidocr",
                framework="ONNX",
                license="Apache-2.0",
            )
            db.add(mv)

        # Other patient record (not owned by the smoke test patient)
        other_pat = db.query(Patient).filter(Patient.patient_id == OTHER_PATIENT_ID).first()
        if not other_pat:
            other_pat = Patient(
                id=uuid.uuid4(),
                patient_id=OTHER_PATIENT_ID,
                name="Rahul Verma",
                phone_number="9876543210",
                age=34,
                gender="Male",
                user_id=None,
            )
            db.add(other_pat)

        db.commit()
    finally:
        db.close()


def find_sample_prescription_image() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "sample_prescription.png"),
        os.path.join(BACKEND_DIR, "sample_prescription.png"),
        "sample_prescription.png",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("sample_prescription.png not found")


class SmokeTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.is_live = False
        self.client = None
        self.mock_storage = None

    def record_check(self, name: str, success: bool, detail: str = ""):
        if success:
            self.passed += 1
            print(f"[PASS] {name}{f' ({detail})' if detail else ''}")
        else:
            self.failed += 1
            print(f"[FAIL] {name}{f' ({detail})' if detail else ''}")

    def setup_client(self):
        import urllib.request
        live_url = os.environ.get("PRESCRIPTO_API_URL", "http://127.0.0.1:8000/api/v1")
        try:
            req = urllib.request.Request(f"{live_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    self.is_live = True
                    self.live_base_url = live_url
                    print(f"[*] Running against LIVE stack at {live_url}")
                    return
        except Exception:
            pass

        print("[*] Running against IN-PROCESS stack via FastAPI TestClient")
        from fastapi.testclient import TestClient
        from fastapi import Response
        from prescripto.api.main import app
        from prescripto.storage.client import get_storage_client
        from prescripto.storage.exceptions import StorageObjectNotFoundException

        class InMemoryStorageClient:
            def __init__(self):
                self.objects: Dict[str, tuple[bytes, str]] = {}

            @staticmethod
            def generate_prescription_key(document_id, extension):
                clean_ext = extension.lstrip(".").lower()
                return f"prescriptions/{document_id}/original.{clean_ext}"

            def ensure_bucket_exists(self, bucket_name=None):
                pass

            def put_object(self, key, data, content_type="application/octet-stream", bucket_name=None):
                self.objects[key] = (data, content_type)

            def get_object(self, key, bucket_name=None):
                if key not in self.objects:
                    raise StorageObjectNotFoundException(f"Object {key} not found")
                return self.objects[key][0]

            def generate_presigned_url(self, key, expires_in=60, bucket_name=None):
                return f"/mock-storage/{key}"

        self.mock_storage = InMemoryStorageClient()
        app.dependency_overrides[get_storage_client] = lambda: self.mock_storage

        # Endpoint to resolve presigned image URL in TestClient
        has_mock_route = any(getattr(r, "path", None) == "/mock-storage/{key:path}" for r in app.routes)
        if not has_mock_route:
            @app.get("/mock-storage/{key:path}", include_in_schema=False)
            def _serve_mock_storage(key: str):
                data = self.mock_storage.get_object(key)
                return Response(content=data, media_type="image/png")

        self.client = TestClient(app)

    def post(self, path: str, **kwargs):
        if self.is_live:
            import requests
            url = f"{self.live_base_url}{path.replace('/api/v1', '')}"
            return requests.post(url, **kwargs)
        return self.client.post(path, **kwargs)

    def get(self, path: str, **kwargs):
        if self.is_live:
            import requests
            url = path if path.startswith("http") else f"{self.live_base_url}{path.replace('/api/v1', '')}"
            return requests.get(url, **kwargs)
        return self.client.get(path, **kwargs)

    def run(self) -> int:
        ensure_db_fixtures()
        self.setup_client()

        # 1. Operator Login
        op_res = self.post(
            "/api/v1/auth/token",
            data={"username": OPERATOR_USER, "password": OPERATOR_PASS},
        )
        op_ok = op_res.status_code == 200 and "access_token" in op_res.json()
        self.record_check("Operator login", op_ok, f"status: {op_res.status_code}")
        if not op_ok:
            return 1
        op_token = op_res.json()["access_token"]
        op_headers = {"Authorization": f"Bearer {op_token}"}

        # 2. Upload sample_prescription.png
        image_path = find_sample_prescription_image()
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        idem_key = f"smoke-{uuid.uuid4()}"
        upload_headers = dict(op_headers)
        upload_headers["Idempotency-Key"] = idem_key

        files = {"file": ("sample_prescription.png", io.BytesIO(image_bytes), "image/png")}
        data = {"patient_external_id": OTHER_PATIENT_ID}

        up_res = self.post("/api/v1/prescriptions", headers=upload_headers, files=files, data=data)
        up_ok = up_res.status_code == 202 and "analysis_id" in up_res.json()
        self.record_check("Upload sample_prescription.png", up_ok, f"status: {up_res.status_code}")
        if not up_ok:
            return 1

        prescription_id = up_res.json()["prescription_id"]
        analysis_id = up_res.json()["analysis_id"]

        # 3. Poll analysis until done
        if not self.is_live:
            from prescripto.worker.main import WorkerRunner
            runner = WorkerRunner(poll_interval=0.1, storage_client=self.mock_storage)
            runner.run_once()

        status = "QUEUED"
        poll_attempts = 0
        max_polls = 40
        while status in ("QUEUED", "PROCESSING") and poll_attempts < max_polls:
            time.sleep(1)
            poll_attempts += 1
            st_res = self.get(f"/api/v1/analyses/{analysis_id}", headers=op_headers)
            if st_res.status_code == 200:
                status = st_res.json().get("status")
            if not self.is_live and status in ("QUEUED", "PROCESSING"):
                from prescripto.worker.main import WorkerRunner
                WorkerRunner(poll_interval=0.1, storage_client=self.mock_storage).run_once()

        poll_ok = status in ("COMPLETED", "REQUIRES_REVIEW")
        self.record_check("Poll analysis completion", poll_ok, f"terminal status: {status}")
        if not poll_ok:
            return 1

        # 4. Assert: provider_used == gemini & 3 medicines returned
        result_res = self.get(f"/api/v1/analyses/{analysis_id}/result", headers=op_headers)
        res_data = result_res.json() if result_res.status_code == 200 else {}

        provider_used = res_data.get("provider_used") or (
            res_data.get("document_extraction", {}).get("provider_used")
        )
        provider_ok = (provider_used == "gemini")
        self.record_check("Assert provider_used == gemini", provider_ok, f"got: {provider_used}")

        medications = res_data.get("medications", [])
        if not medications and "document_extraction" in res_data:
            medications = res_data["document_extraction"].get("medication_orders", [])
        meds_ok = (len(medications) == 3)
        self.record_check("Assert 3 medicines returned", meds_ok, f"got: {len(medications)}")

        # 5. Assert: prescription image URL returns HTTP 200
        detail_res = self.get(f"/api/v1/prescriptions/{prescription_id}", headers=op_headers)
        detail_data = detail_res.json() if detail_res.status_code == 200 else {}
        image_url = detail_data.get("image_url")
        image_url_ok = False
        img_status = None
        if image_url:
            img_fetch = self.get(image_url)
            img_status = img_fetch.status_code
            image_url_ok = (img_status == 200)

        self.record_check("Prescription image URL returns HTTP 200", image_url_ok, f"status: {img_status}")

        # 6. Patient-role login (via patient OTP auth endpoint)
        pat_res = self.post(
            "/api/v1/auth/verify-otp",
            json={"phone_number": "9123456789", "otp": "123456", "name": "Smoke Patient"},
        )
        pat_ok = pat_res.status_code == 200 and "access_token" in pat_res.json()
        self.record_check("Patient login", pat_ok, f"status: {pat_res.status_code}")
        if not pat_ok:
            return 1
        pat_token = pat_res.json()["access_token"]
        pat_headers = {"Authorization": f"Bearer {pat_token}"}

        # 7. Assert: GET /patients/search returns 403
        search_res = self.get("/api/v1/patients/search?q=Rahul", headers=pat_headers)
        search_403 = (search_res.status_code == 403)
        self.record_check("GET /patients/search returns 403", search_403, f"status: {search_res.status_code}")

        # 8. Assert: another patient's timeline returns 403
        timeline_res = self.get(f"/api/v1/patients/{OTHER_PATIENT_ID}", headers=pat_headers)
        timeline_403 = (timeline_res.status_code == 403)
        self.record_check(f"GET /patients/{OTHER_PATIENT_ID} timeline returns 403", timeline_403, f"status: {timeline_res.status_code}")

        print("-" * 50)
        print(f"Summary: {self.passed} passed, {self.failed} failed")
        return 0 if self.failed == 0 else 1


if __name__ == "__main__":
    runner = SmokeTestRunner()
    sys.exit(runner.run())

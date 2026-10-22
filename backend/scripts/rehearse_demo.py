"""
Prescripto AI 2.0 — End-to-End Demo Rehearsal Script.
Executes the live operator upload, distributed worker processing,
result retrieval, and clinical reviewer decision workflow.
"""
from __future__ import annotations

import json
import sys
import time
import uuid
import urllib.request
import urllib.parse


BASE_URL = "http://127.0.0.1:8000/api/v1"


def http_post(url: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def login(username: str, password: str) -> str:
    body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
    resp = http_post(
        f"{BASE_URL}/auth/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return resp["access_token"]


def upload_prescription(token: str, image_path: str) -> dict:
    with open(image_path, "rb") as f:
        file_bytes = f.read()

    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()
    
    # file field
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="sample_rx.png"\r\n')
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")
    
    # patient_external_id field
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="patient_external_id"\r\n\r\n')
    body.extend(b"PAT-9842\r\n")
    
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    return http_post(f"{BASE_URL}/prescriptions", data=bytes(body), headers=headers)


def main():
    print("=" * 60)
    print("PRESCRIPTO AI 2.0 — DEMO REHEARSAL")
    print("=" * 60)

    # 1. Operator login
    print("\n[Step 1] Authenticating operator1...")
    operator_token = login("operator1", "Demo#12345")
    print("  -> Logged in successfully. Bearer token acquired.")

    # 2. Upload prescription
    import os
    image_path = sys.argv[1] if len(sys.argv) > 1 else ("sample_prescription.png" if os.path.exists("sample_prescription.png") else "/app/sample_rx.png")
    print(f"\n[Step 2] Uploading prescription image ({image_path})...")
    upload_res = upload_prescription(operator_token, image_path)
    analysis_id = upload_res["analysis_id"]
    prescription_id = upload_res["prescription_id"]
    print(f"  -> Upload Accepted (202): analysis_id={analysis_id}, prescription_id={prescription_id}")

    # 3. Poll analysis status
    print("\n[Step 3] Waiting for worker pipeline processing...")
    headers = {"Authorization": f"Bearer {operator_token}"}
    status = "QUEUED"
    poll_count = 0
    while status in ("QUEUED", "PROCESSING") and poll_count < 30:
        time.sleep(1)
        poll_count += 1
        status_res = http_get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers)
        status = status_res["status"]
        print(f"  [T+{poll_count}s] Status: {status} | Stages: {status_res.get('stages', [])}")

    if status not in ("COMPLETED", "REQUIRES_REVIEW"):
        print(f"\n[ERROR] Pipeline ended with unexpected status: {status}")
        sys.exit(1)

    print(f"\n  -> Pipeline successfully reached terminal/review state: {status}")

    # 4. Fetch full analysis result
    print("\n[Step 4] Fetching structured analysis result...")
    result_res = http_get(f"{BASE_URL}/analyses/{analysis_id}/result", headers=headers)
    print(f"  Summary: {result_res.get('status')}")
    print(f"  Requires Review: {result_res.get('requires_review')}")
    print(f"  Confidence Score: {result_res.get('confidence_score')}")
    print(f"  Safety Alerts: {result_res.get('safety_alerts')}")
    print(f"  Medications ({len(result_res.get('medications', []))} items):")
    for med in result_res.get("medications", []):
        print(f"    - Raw: '{med.get('raw_name')}' | Normalized: '{med.get('normalized_name')}' | Dose: {med.get('dosage')} | Freq: {med.get('frequency')}")

    # 5. If REQUIRES_REVIEW, perform clinical review submission
    if status == "REQUIRES_REVIEW":
        print("\n[Step 5] Logging in as clinical reviewer (reviewer1)...")
        reviewer_token = login("reviewer1", "Demo#12345")
        rev_headers = {
            "Authorization": f"Bearer {reviewer_token}",
            "Content-Type": "application/json",
        }

        findings = result_res.get("findings", [])
        print(f"  -> Total findings to review: {len(findings)}")
        for f in findings:
            print(f"     * Finding ID: {f.get('finding_id')} | Type: {f.get('check_type')} | Evidence: {f.get('evidence_text')}")

        # Build review payload
        review_payload = {
            "decisions": [
                {
                    "finding_id": f["finding_id"],
                    "action": "APPROVED",
                    "notes": "Clinically reviewed and confirmed during live demo rehearsal.",
                }
                for f in findings
            ],
        }

        print("  -> Submitting review decisions...")
        rev_post = http_post(
            f"{BASE_URL}/analyses/{analysis_id}/review",
            data=json.dumps(review_payload).encode("utf-8"),
            headers=rev_headers,
        )
        print(f"  -> Review submitted: review_id={rev_post.get('review_id')}, overall_status={rev_post.get('overall_status')}")

        # Check final status
        final_status = http_get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers)
        print(f"  -> Final Analysis Status after review: {final_status.get('status')}")

    print("\n" + "=" * 60)
    print("DEMO REHEARSAL: PASSED ALL GATES SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()

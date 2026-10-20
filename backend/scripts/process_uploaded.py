"""
Process the user-uploaded image from MinIO through the live Prescripto pipeline.
"""
import json
import time
import urllib.parse
import urllib.request
import uuid

from prescripto.storage.client import get_storage_client


def main():
    print("=" * 60)
    print("PROCESSING USER UPLOADED PRESCRIPTION FROM MinIO")
    print("=" * 60)

    # 1. Fetch image from MinIO
    client = get_storage_client()
    file_bytes = client.get_object("prescription.jpeg")
    print(f"1. Retrieved 'prescription.jpeg' from MinIO ({len(file_bytes)} bytes)")

    # 2. Login as operator
    login_data = urllib.parse.urlencode({
        "username": "operator1",
        "password": "Demo#12345",
    }).encode("utf-8")

    req_login = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    token = json.loads(urllib.request.urlopen(req_login).read().decode("utf-8"))["access_token"]
    print("2. Authenticated operator1 successfully")

    # 3. Submit to Ingestion API
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="prescription.jpeg"\r\n')
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="patient_external_id"\r\n\r\n')
    body.extend(b"PAT-MINIO-UPLOAD\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    idempotency_key = str(uuid.uuid4())
    req_upload = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/prescriptions",
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    upload_res = json.loads(urllib.request.urlopen(req_upload).read().decode("utf-8"))
    analysis_id = upload_res["analysis_id"]
    prescription_id = upload_res["prescription_id"]
    print(f"3. Upload Accepted (202):")
    print(f"   - Analysis ID:     {analysis_id}")
    print(f"   - Prescription ID: {prescription_id}")

    # 4. Poll status
    print("\n4. Worker Pipeline executing across 8 stages...")
    headers = {"Authorization": f"Bearer {token}"}
    for poll in range(1, 20):
        time.sleep(1)
        req_status = urllib.request.Request(
            f"http://127.0.0.1:8000/api/v1/analyses/{analysis_id}",
            headers=headers,
        )
        status_res = json.loads(urllib.request.urlopen(req_status).read().decode("utf-8"))
        current_status = status_res["status"]
        stages = [s["stage_name"] for s in status_res.get("stages", []) if s["status"] == "COMPLETED"]
        print(f"   [T+{poll}s] Status: {current_status} | Completed stages: {', '.join(stages) or 'None'}")
        if current_status in ("COMPLETED", "REQUIRES_REVIEW", "FAILED"):
            break

    # 5. Fetch full results
    print("\n5. Fetching Analysis Result:")
    req_result = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/analyses/{analysis_id}/result",
        headers=headers,
    )
    result_data = json.loads(urllib.request.urlopen(req_result).read().decode("utf-8"))
    print(f"   Status:            {result_data.get('status')}")
    print(f"   Disclaimers:       {result_data.get('coverage_disclaimer')}")
    print(f"   Medications Found: {len(result_data.get('medications', []))}")
    for med in result_data.get("medications", []):
        print(f"     - Name: {med.get('raw_name')} -> Normalized: {med.get('normalized_name')}")
        print(f"       Dosage: {med.get('dosage')} | Frequency: {med.get('frequency')}")
    print(f"   Safety Findings:   {len(result_data.get('findings', []))}")
    for f in result_data.get("findings", []):
        print(f"     * [{f.get('check_type')}] {f.get('evidence_text')}")
    print("=" * 60)


if __name__ == "__main__":
    main()

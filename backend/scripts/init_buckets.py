"""
Initialize MinIO buckets for Prescripto 2.0.
Used during container startup or local dev orchestration.
"""
from __future__ import annotations

import sys
import time

from prescripto.storage.client import get_storage_client


def init_buckets() -> int:
    client = get_storage_client()
    print("Checking storage buckets...", flush=True)
    for attempt in range(1, 31):
        try:
            client.ensure_bucket_exists("prescripto")
            client.ensure_bucket_exists("prescripto-retention")
            print("MinIO buckets initialized successfully.", flush=True)
            return 0
        except Exception as exc:
            print(f"Waiting for MinIO (attempt {attempt}/30): {exc}", flush=True)
            time.sleep(2)
    print("Failed to initialize MinIO buckets after 30 attempts.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(init_buckets())

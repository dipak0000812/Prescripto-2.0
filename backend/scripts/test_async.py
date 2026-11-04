import os
import sys
from pathlib import Path

_BACKEND_DIR = str(Path(__file__).resolve().parents[1])
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

os.environ["PYTEST_CURRENT_TEST"] = "1"

import asyncio
import httpx
from prescripto.api.main import app

async def main():
    print("Creating transport...", flush=True)
    transport = httpx.ASGITransport(app=app)
    print("Transport created, requesting...", flush=True)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/api/v1/auth/me")
        print("STATUS:", r.status_code, flush=True)
        print("BODY:", r.text, flush=True)

if __name__ == "__main__":
    asyncio.run(main())


"""
Prescripto AI 2.0 — Architecture and Workflow Diagram Generator.
Generates four rich, publication-grade SVG and PNG diagrams:
1. System Architecture
2. System Design & ML Processing Pipeline
3. Patient & Clinician User Workflows
4. Complete Technology Stack Workflow
"""
import os
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("docs/architecture_diagrams").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WEB_PUBLIC_DIR = Path("web/public/diagrams").resolve()
WEB_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# -----------------------------------------------------------------------------
# 1. SYSTEM ARCHITECTURE DIAGRAM
# -----------------------------------------------------------------------------
SVG_SYSTEM_ARCHITECTURE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#06221D"/>
      <stop offset="50%" stop-color="#0A3831"/>
      <stop offset="100%" stop-color="#0F5147"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.04"/>
    </linearGradient>
    <linearGradient id="emeraldGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#10B981"/>
      <stop offset="100%" stop-color="#34D399"/>
    </linearGradient>
    <linearGradient id="amberGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#FBBF24"/>
    </linearGradient>
    <linearGradient id="blueGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#3B82F6"/>
      <stop offset="100%" stop-color="#60A5FA"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1000" fill="url(#bg)"/>

  <!-- Subtle Grid Pattern -->
  <g opacity="0.06">
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#FFFFFF" stroke-width="1"/>
    </pattern>
    <rect width="1600" height="1000" fill="url(#grid)"/>
  </g>

  <!-- Header Banner -->
  <g transform="translate(80, 50)">
    <rect x="0" y="0" width="48" height="48" rx="14" fill="#10B981" filter="url(#glow)"/>
    <path d="M24 14 L34 18 L34 26 C34 32 29 36 24 38 C19 36 14 32 14 26 L14 18 Z" fill="#0A3831"/>
    <text x="64" y="28" font-family="Segoe UI, -apple-system, sans-serif" font-size="28" font-weight="900" fill="#FFFFFF" letter-spacing="-0.5">PRESCRIPTO AI 2.0</text>
    <text x="64" y="46" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600" fill="#6EE7B7" letter-spacing="1.5">END-TO-END SYSTEM ARCHITECTURE</text>
    <rect x="1260" y="8" width="180" height="32" rx="16" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.2)"/>
    <circle cx="1278" cy="24" r="5" fill="#10B981"/>
    <text x="1292" y="29" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">LOCKED BASELINE v1.1</text>
  </g>

  <!-- 1. CLIENT TIER (LEFT) -->
  <g transform="translate(80, 130)" filter="url(#shadow)">
    <rect width="320" height="800" rx="20" fill="url(#cardGrad)" stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
    <rect width="320" height="52" rx="20" fill="rgba(16,185,129,0.15)"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800" fill="#34D399" letter-spacing="1">1. PRESENTATION TIER</text>
    <text x="240" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">SPA / PWA</text>

    <!-- Patient App -->
    <g transform="translate(20, 75)">
      <rect width="280" height="330" rx="14" fill="rgba(0,0,0,0.3)" stroke="rgba(52,211,153,0.3)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle" fill="#34D399">&#128241;</text>
      <text x="60" y="34" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="#FFFFFF">Patient Mobile App Shell</text>
      <text x="60" y="50" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Multilingual (EN, HI, GU, MR)</text>

      <rect x="20" y="75" width="240" height="46" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="96" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128247; Camera &amp; Gallery Upload</text>
      <text x="32" y="112" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Frame alignment, DPDPA consent</text>

      <rect x="20" y="130" width="240" height="46" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="151" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#9728;&#65039; 3-Slot Schedule Cards</text>
      <text x="32" y="167" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Sunrise (Morning), Sun, Moon (Night)</text>

      <rect x="20" y="185" width="240" height="46" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="206" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128266; Native Voice Readout</text>
      <text x="32" y="222" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Web Speech API speech synthesis</text>

      <rect x="20" y="240" width="240" height="46" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="261" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128276; Medication Reminders</text>
      <text x="32" y="277" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Taken / Snooze / Skip (48px buttons)</text>

      <rect x="20" y="295" width="240" height="24" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="140" y="311" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" text-anchor="middle" fill="#6EE7B7">10-Digit Phone + Auto-OTP Login</text>
    </g>

    <!-- Clinician Workspace -->
    <g transform="translate(20, 425)">
      <rect width="280" height="350" rx="14" fill="rgba(0,0,0,0.3)" stroke="rgba(96,165,250,0.3)"/>
      <circle cx="35" cy="35" r="15" fill="#3B82F6" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle" fill="#60A5FA">&#129658;</text>
      <text x="60" y="34" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="#FFFFFF">Doctor / Reviewer Portal</text>
      <text x="60" y="50" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Desktop High-Speed Console</text>

      <rect x="20" y="75" width="240" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="96" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128337; Clinical Review Queue</text>
      <text x="32" y="112" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Sorted by wait time &amp; ambiguity severity</text>

      <rect x="20" y="135" width="240" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="156" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128269; Split-View Photo Verifier</text>
      <text x="32" y="172" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Zoom/pan/crop slip vs extracted lines</text>

      <rect x="20" y="195" width="240" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="216" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#9999;&#65039; Inline Dose / Form Editor</text>
      <text x="32" y="232" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Correct shorthand with audit logging</text>

      <rect x="20" y="255" width="240" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="276" font-family="Segoe UI, sans-serif" font-size="12" font-weight="600" fill="#E5E7EB">&#128196; Patient Medical History</text>
      <text x="32" y="292" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Patient timeline dossier &amp; visits</text>

      <rect x="20" y="315" width="240" height="24" rx="6" fill="#3B82F6" opacity="0.2"/>
      <text x="140" y="331" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" text-anchor="middle" fill="#93C5FD">RS256 Staff JWT &amp; Role Check</text>
    </g>
  </g>

  <!-- Connectors: Presentation -> Gateway -->
  <g stroke="#34D399" stroke-width="2" stroke-dasharray="6,4" opacity="0.8">
    <path d="M 400 300 L 460 300 L 460 380 L 510 380"/>
    <path d="M 400 600 L 460 600 L 460 420 L 510 420"/>
  </g>

  <!-- 2. API GATEWAY & MODULAR MONOLITH (CENTER) -->
  <g transform="translate(510, 130)" filter="url(#shadow)">
    <rect width="360" height="800" rx="20" fill="url(#cardGrad)" stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
    <rect width="360" height="52" rx="20" fill="rgba(16,185,129,0.15)"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800" fill="#34D399" letter-spacing="1">2. FASTAPI MONOLITH</text>
    <text x="260" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">UVICORN / ASGI</text>

    <!-- Middlewares -->
    <g transform="translate(20, 70)">
      <rect width="320" height="70" rx="10" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.1)"/>
      <text x="16" y="24" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#34D399">HTTP MIDDLEWARE PIPELINE</text>
      <text x="16" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; X-Request-ID Correlation</text>
      <text x="175" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; CORS Whitelist</text>
      <text x="16" y="60" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Zero-PHI Structured Logging</text>
      <text x="175" y="60" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Idempotency-Key Gate</text>
    </g>

    <!-- Subsystem Routers -->
    <g transform="translate(20, 155)">
      <text x="4" y="16" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#9CA3AF">MODULAR ROUTERS (/api/v1)</text>

      <rect x="0" y="26" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="48" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">POST /api/v1/prescriptions</text>
      <text x="16" y="66" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Multipart upload &#8594; 202 Accepted + SHA-256 Checksum</text>

      <rect x="0" y="86" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="108" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">GET /api/v1/prescriptions</text>
      <text x="16" y="126" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Paginated list with patient_name &amp; patient_ref</text>

      <rect x="0" y="146" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="168" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">GET /api/v1/analyses/{id}</text>
      <text x="16" y="186" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Gated status check + 60s signed image URL</text>

      <rect x="0" y="206" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="228" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">POST /api/v1/analyses/{id}/review</text>
      <text x="16" y="246" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Clinician review submission &amp; status transition</text>

      <rect x="0" y="266" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="288" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">/api/v1/patients &amp; /timeline</text>
      <text x="16" y="306" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Patient search &amp; full historical medical visits</text>

      <rect x="0" y="326" width="320" height="52" rx="8" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="348" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">/api/v1/reminders</text>
      <text x="16" y="366" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">VAPID Web Push subscription &amp; dose logging</text>
    </g>

    <!-- Embedded Worker Daemon -->
    <g transform="translate(20, 580)">
      <rect width="320" height="190" rx="12" fill="rgba(16,185,129,0.12)" stroke="rgba(52,211,153,0.4)" stroke-width="1.5"/>
      <text x="16" y="26" font-family="Segoe UI, sans-serif" font-size="13" font-weight="800" fill="#34D399">&#9881;&#65039; BACKGROUND WORKER THREAD</text>
      <text x="16" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">Embedded WorkerRunner (poll_interval = 1.0s)</text>
      <text x="16" y="66" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">&#10003; SELECT FOR UPDATE SKIP LOCKED</text>
      <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">&#10003; Generation Fencing Token &amp; Lease Renewal</text>
      <text x="16" y="98" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">&#10003; Max 3 Retries before DEAD status</text>
      <text x="16" y="114" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">&#10003; Zero-PHI Safe Logging Engine</text>

      <rect x="16" y="130" width="288" height="42" rx="8" fill="rgba(0,0,0,0.3)"/>
      <text x="28" y="148" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FBBF24">&#9888; Safety Principle</text>
      <text x="28" y="164" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">Upstream doubt never becomes downstream certainty</text>
    </g>
  </g>

  <!-- Connectors: Gateway -> Persistence -->
  <g stroke="#34D399" stroke-width="2" stroke-dasharray="6,4" opacity="0.8">
    <path d="M 870 380 L 930 380 L 930 280 L 980 280"/>
    <path d="M 870 500 L 980 500"/>
    <path d="M 870 700 L 930 700 L 930 740 L 980 740"/>
  </g>

  <!-- 3. PERSISTENCE & ML LAYER (RIGHT) -->
  <g transform="translate(980, 130)" filter="url(#shadow)">
    <rect width="540" height="800" rx="20" fill="url(#cardGrad)" stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
    <rect width="540" height="52" rx="20" fill="rgba(16,185,129,0.15)"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800" fill="#34D399" letter-spacing="1">3. PERSISTENCE &amp; RECOGNITION TIER</text>
    <text x="410" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">STORAGE &amp; MODELS</text>

    <!-- PostgreSQL / SQLite Database -->
    <g transform="translate(20, 75)">
      <rect width="500" height="210" rx="14" fill="rgba(0,0,0,0.3)" stroke="rgba(52,211,153,0.3)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle" fill="#34D399">&#128452;</text>
      <text x="60" y="34" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="#FFFFFF">Relational Database (PostgreSQL 16+ / SQLite)</text>
      <text x="60" y="50" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">ACID Transactions &amp; Strict Check Constraints</text>

      <g transform="translate(20, 68)" font-family="Consolas, monospace" font-size="10.5" fill="#E5E7EB">
        <rect width="220" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="10" y="17" fill="#6EE7B7">prescription_documents</text>

        <rect x="235" y="0" width="225" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="245" y="17" fill="#6EE7B7">analyses &amp; analysis_jobs</text>

        <rect y="34" width="220" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="10" y="51" fill="#6EE7B7">patients &amp; users</text>

        <rect x="235" y="34" width="225" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="245" y="51" fill="#6EE7B7">medication_audit_trail</text>

        <rect y="68" width="220" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="10" y="85" fill="#6EE7B7">medicine_reminders</text>

        <rect x="235" y="68" width="225" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="245" y="85" fill="#6EE7B7">risk_findings &amp; reviews</text>

        <rect y="102" width="460" height="26" rx="5" fill="rgba(255,255,255,0.06)"/>
        <text x="10" y="119" fill="#FBBF24">CDSCO Canonical Master + RxNorm CUIs (Immutable)</text>
      </g>
    </g>

    <!-- S3 / MinIO Object Storage -->
    <g transform="translate(20, 305)">
      <rect width="500" height="150" rx="14" fill="rgba(0,0,0,0.3)" stroke="rgba(245,158,11,0.3)"/>
      <circle cx="35" cy="35" r="15" fill="#F59E0B" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle" fill="#FBBF24">&#129699;</text>
      <text x="60" y="34" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="#FFFFFF">Object Storage (MinIO / S3)</text>
      <text x="60" y="50" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">60-Second Ephemeral Signed URLs · Local Directory Fallback</text>

      <g transform="translate(20, 68)" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">
        <rect width="460" height="32" rx="6" fill="rgba(255,255,255,0.06)"/>
        <text x="12" y="21" font-weight="600">&#128193; Bucket "prescripto":</text>
        <text x="145" y="21" fill="#9CA3AF" font-family="Consolas, monospace">/prescriptions/{id}/original.{ext} + line region crops</text>

        <rect y="38" width="460" height="32" rx="6" fill="rgba(255,255,255,0.06)"/>
        <text x="12" y="59" font-weight="600">&#128274; Bucket "retention-vault":</text>
        <text x="180" y="59" fill="#9CA3AF" font-family="Consolas, monospace">DPDPA deletion manifests (Separately permissioned)</text>
      </g>
    </g>

    <!-- Vision & Recognition Providers -->
    <g transform="translate(20, 475)">
      <rect width="500" height="300" rx="14" fill="rgba(0,0,0,0.3)" stroke="rgba(168,85,247,0.3)"/>
      <circle cx="35" cy="35" r="15" fill="#A855F7" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle" fill="#C084FC">&#128065;</text>
      <text x="60" y="34" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="#FFFFFF">Recognition &amp; Normalization Providers</text>
      <text x="60" y="50" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Hybrid Vision Architecture with Local Offline Fallback</text>

      <rect x="20" y="70" width="460" height="60" rx="10" fill="rgba(16,185,129,0.12)" stroke="rgba(52,211,153,0.3)"/>
      <text x="34" y="93" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#34D399">&#10024; PRIMARY: Gemini Vision Provider</text>
      <text x="34" y="112" font-family="Segoe UI, sans-serif" font-size="11" fill="#D1FAE5">gemini-3.5-flash (with gemini-3.6-flash fallback). Direct prescription image OCR.</text>

      <rect x="20" y="140" width="460" height="60" rx="10" fill="rgba(59,130,246,0.12)" stroke="rgba(96,165,250,0.3)"/>
      <text x="34" y="163" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#60A5FA">&#128421;&#65039; FALLBACK: Local RapidOCR / TrOCR</text>
      <text x="34" y="182" font-family="Segoe UI, sans-serif" font-size="11" fill="#DBEAFE">Offline inference for auth failure, timeout, or rate-limit. Zero external network dependency.</text>

      <rect x="20" y="210" width="460" height="70" rx="10" fill="rgba(245,158,11,0.12)" stroke="rgba(245,158,11,0.3)"/>
      <text x="34" y="233" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#FBBF24">&#9878;&#65039; DETERMINISTIC REGEX &amp; CDSCO NORMALIZATION</text>
      <text x="34" y="252" font-family="Segoe UI, sans-serif" font-size="11" fill="#FEF3C7">Deterministic parsing for dosage numbers &amp; timing (1-0-1, pc/ac, q6h).</text>
      <text x="34" y="268" font-family="Segoe UI, sans-serif" font-size="10" fill="#FDE68A">Uncertainty state: CLEAR &#183; AMBIGUOUS &#183; UNREADABLE &#183; NOT_PRESENT</text>
    </g>
  </g>

  <!-- Bottom Attribution Footer -->
  <g transform="translate(80, 955)" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">
    <text x="0" y="10">&#128737; DPDPA 2023 Compliant &#183; Zero-PHI in Operational Logs &#183; Human-In-The-Loop Review Mandatory</text>
    <text x="1440" y="10" text-anchor="end">Prescripto AI 2.0 &#183; Production Architecture Blueprint</text>
  </g>
</svg>"""

# -----------------------------------------------------------------------------
# 2. SYSTEM DESIGN & ML PIPELINE DIAGRAM
# -----------------------------------------------------------------------------
SVG_SYSTEM_DESIGN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <defs>
    <linearGradient id="bg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="60%" stop-color="#022C22"/>
      <stop offset="100%" stop-color="#064E3B"/>
    </linearGradient>
    <linearGradient id="pipelineGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#10B981"/>
      <stop offset="50%" stop-color="#06B6D4"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
    <filter id="shadow2" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <rect width="1600" height="1000" fill="url(#bg2)"/>

  <!-- Title Banner -->
  <g transform="translate(80, 50)">
    <rect x="0" y="0" width="48" height="48" rx="14" fill="#06B6D4"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="22" text-anchor="middle" fill="#0F172A">&#9881;</text>
    <text x="64" y="28" font-family="Segoe UI, sans-serif" font-size="28" font-weight="900" fill="#FFFFFF">PRESCRIPTO AI 2.0</text>
    <text x="64" y="46" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600" fill="#67E8F9" letter-spacing="1.5">7-STAGE DETERMINISTIC PROCESSING PIPELINE &amp; SAFETY ENGINE</text>
  </g>

  <!-- Flow Progress Track -->
  <rect x="120" y="160" width="1360" height="12" rx="6" fill="rgba(255,255,255,0.1)"/>
  <rect x="120" y="160" width="1360" height="12" rx="6" fill="url(#pipelineGrad)"/>

  <!-- 7 Stages Grid -->
  <!-- STAGE 1: INGESTION -->
  <g transform="translate(80, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(16,185,129,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(16,185,129,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#34D399" text-anchor="middle">STAGE 1: INGESTION</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Magic Byte Check</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">JPEG, PNG, TIFF only</text>
    <text x="16" y="98" font-family="Segoe UI, sans-serif" font-size="10" fill="#F87171">&#10007; PDF Active Content rejected</text>

    <text x="16" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; SHA-256 Checksum</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Cryptographic image hash</text>

    <text x="16" y="170" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Idempotency-Key</text>
    <text x="16" y="187" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Instant deduplication replay</text>

    <text x="16" y="215" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Decompression Bomb</text>
    <text x="16" y="232" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Pillow memory defense</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#34D399">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">PrescriptionDocument</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">HTTP 202 Accepted</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">MinIO S3 storage key</text>
  </g>

  <!-- STAGE 2: DETECTION -->
  <g transform="translate(290, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(6,182,212,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(6,182,212,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#67E8F9" text-anchor="middle">STAGE 2: DETECTION</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; DBNet / PP-OCRv6</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Text region localization</text>

    <text x="16" y="110" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Line-Level Slicing</text>
    <text x="16" y="127" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Separates 5-20 handwritten</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">outpatient prescription lines</text>

    <text x="16" y="170" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Bounding Boxes</text>
    <text x="16" y="187" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Normalized coordinates</text>
    <text x="16" y="202" font-family="Consolas, monospace" font-size="9" fill="#67E8F9">[ymin, xmin, ymax, xmax]</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#67E8F9">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">List[LineRegion]</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Cropped image buffers</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Polygon coordinates</text>
  </g>

  <!-- STAGE 3: RECOGNITION -->
  <g transform="translate(500, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(139,92,246,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(139,92,246,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#C4B5FD" text-anchor="middle">STAGE 3: RECOGNITION</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Gemini 3.5 Flash</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Direct high-accuracy OCR</text>
    <text x="16" y="97" font-family="Segoe UI, sans-serif" font-size="10" fill="#C4B5FD">gemini-3.6-flash fallback</text>

    <text x="16" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Offline RapidOCR</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Local TrOCR / RapidOCR</text>
    <text x="16" y="157" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">fallback on quota / timeout</text>

    <text x="16" y="185" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Token Confidences</text>
    <text x="16" y="202" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Character-level certainty</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#C4B5FD">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">ExtractedTextLines</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Confidence scores (0..1)</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Provider metadata</text>
  </g>

  <!-- STAGE 4: STRUCTURED EXTRACTION -->
  <g transform="translate(710, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(236,72,153,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(236,72,153,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#F472B6" text-anchor="middle">STAGE 4: EXTRACTION</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Indian Shorthand</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">OD (1-0-0), BD (1-0-1)</text>
    <text x="16" y="97" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">TDS (1-1-1), QID, SOS, PRN</text>

    <text x="16" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Intervals &amp; Food</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">q6h, q8h, q12h frequency</text>
    <text x="16" y="157" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">pc (after food), ac (before)</text>

    <text x="16" y="185" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; 4-State Field Model</text>
    <text x="16" y="202" font-family="Consolas, monospace" font-size="8.5" fill="#34D399">CLEAR &#183; AMBIGUOUS</text>
    <text x="16" y="217" font-family="Consolas, monospace" font-size="8.5" fill="#F87171">UNREADABLE &#183; NOT_PRESENT</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#F472B6">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">MedicationCandidates</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Morning / Noon / Night</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Form (Tablet/Syrup/Cap)</text>
  </g>

  <!-- STAGE 5: NORMALIZATION -->
  <g transform="translate(920, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(245,158,11,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(245,158,11,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#FBBF24" text-anchor="middle">STAGE 5: NORMALIZATION</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; CDSCO Master Data</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Approved Indian drugs</text>
    <text x="16" y="97" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">&amp; active salt formulations</text>

    <text x="16" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Alias Resolution</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Calpol/Dolo &#8594; Paracetamol</text>
    <text x="16" y="157" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Augmentin &#8594; Amox-Clav</text>

    <text x="16" y="185" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Non-Forced Match</text>
    <text x="16" y="202" font-family="Segoe UI, sans-serif" font-size="10" fill="#FBBF24">Never guess unlisted drugs</text>
    <text x="16" y="217" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">&#8594; Flags UNRESOLVED</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#FBBF24">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">PrescriptionMedications</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Canonical Product CUI</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Strength &amp; Ratio (250/5)</text>
  </g>

  <!-- STAGE 6: SAFETY SCREENING -->
  <g transform="translate(1130, 200)" filter="url(#shadow2)">
    <rect width="190" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(239,68,68,0.4)" stroke-width="1.5"/>
    <rect width="190" height="38" rx="14" fill="rgba(239,68,68,0.2)"/>
    <text x="95" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#FCA5A5" text-anchor="middle">STAGE 6: SAFETY CHECK</text>

    <text x="16" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Duplicate Ingredients</text>
    <text x="16" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Screens repeated salts</text>
    <text x="16" y="97" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">(e.g. Paracetamol in 2 tabs)</text>

    <text x="16" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Dosage Frequency</text>
    <text x="16" y="142" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Flags excessive daily doses</text>
    <text x="16" y="157" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Interval boundary checks</text>

    <text x="16" y="185" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Rule-Based Engine</text>
    <text x="16" y="202" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Independent of LLM</text>
    <text x="16" y="217" font-family="Segoe UI, sans-serif" font-size="10" fill="#A7F3D0">Deterministic &amp; auditable</text>

    <rect x="12" y="260" width="166" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="20" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#FCA5A5">OUTPUT:</text>
    <text x="20" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">List[RiskFinding]</text>
    <text x="20" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Severity: DANGER / WARN</text>
    <text x="20" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">review_required flag</text>
  </g>

  <!-- STAGE 7: COMMIT & GATING -->
  <g transform="translate(1340, 200)" filter="url(#shadow2)">
    <rect width="180" height="360" rx="14" fill="rgba(255,255,255,0.06)" stroke="rgba(16,185,129,0.4)" stroke-width="1.5"/>
    <rect width="180" height="38" rx="14" fill="rgba(16,185,129,0.2)"/>
    <text x="90" y="24" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#34D399" text-anchor="middle">STAGE 7: GATING</text>

    <text x="14" y="65" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Atomic Lease Commit</text>
    <text x="14" y="82" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Validates lease_token</text>
    <text x="14" y="97" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Guards expired workers</text>

    <text x="14" y="125" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#10003; Dual Status Fork</text>
    <text x="14" y="145" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#FBBF24">&#9654; REQUIRES_REVIEW</text>
    <text x="14" y="160" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">Routes to Doctor Queue</text>
    <text x="14" y="180" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#34D399">&#9654; COMPLETED</text>
    <text x="14" y="195" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">Direct patient release</text>

    <rect x="10" y="260" width="160" height="85" rx="8" fill="rgba(0,0,0,0.3)"/>
    <text x="18" y="280" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#34D399">OUTPUT:</text>
    <text x="18" y="296" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Final Analysis JSON</text>
    <text x="18" y="310" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Push Notifications</text>
    <text x="18" y="324" font-family="Consolas, monospace" font-size="9" fill="#E5E7EB">Audit Manifests</text>
  </g>

  <!-- LOWER SECTION: THE HUMAN-IN-THE-LOOP VERIFICATION CONSOLE -->
  <g transform="translate(80, 600)" filter="url(#shadow2)">
    <rect width="1440" height="340" rx="16" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.15)" stroke-width="1.5"/>
    <rect width="1440" height="42" rx="16" fill="rgba(52,211,153,0.15)"/>
    <text x="24" y="26" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399">HUMAN-IN-THE-LOOP SAFETY RECOVERY: CLINICAL REVIEW WORKSPACE</text>
    <text x="1200" y="26" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">DECISION SUPPORT ONLY &#183; ZERO AUTO-PRESCRIBING</text>

    <!-- Step A: Queue -->
    <g transform="translate(30, 60)">
      <rect width="320" height="250" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.1)"/>
      <text x="16" y="26" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#FBBF24">A. Triage Queue</text>
      <text x="16" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Prioritized by wait time &amp; critical flags</text>
      <rect x="16" y="60" width="288" height="46" rx="6" fill="rgba(245,158,11,0.1)"/>
      <text x="24" y="78" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">Rahul Verma (PAT-1001)</text>
      <text x="24" y="94" font-family="Segoe UI, sans-serif" font-size="10" fill="#FBBF24">&#9888; 1 Unclear Line &#183; Waiting 12m</text>

      <rect x="16" y="115" width="288" height="46" rx="6" fill="rgba(255,255,255,0.04)"/>
      <text x="24" y="133" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">Sunita Rao (PAT-1004)</text>
      <text x="24" y="149" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Duplicate Salt Check &#183; Waiting 25m</text>

      <rect x="16" y="170" width="288" height="46" rx="6" fill="rgba(255,255,255,0.04)"/>
      <text x="24" y="188" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">Bhushan Patil (PAT-1005)</text>
      <text x="24" y="204" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Unresolved Drug Name &#183; Waiting 40m</text>

      <text x="16" y="240" font-family="Segoe UI, sans-serif" font-size="10" fill="#6EE7B7">&#10003; 404-over-403 security privacy enforced</text>
    </g>

    <!-- Step B: Split Screen -->
    <g transform="translate(380, 60)">
      <rect width="680" height="250" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.1)"/>
      <text x="16" y="26" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#60A5FA">B. Side-by-Side Verification Console</text>
      <text x="16" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Original Image with Highlight Overlays vs Extracted Fields</text>

      <!-- Sub-panel Left: Image -->
      <g transform="translate(16, 56)">
        <rect width="310" height="175" rx="8" fill="#1E293B" stroke="rgba(255,255,255,0.1)"/>
        <text x="155" y="40" font-family="Segoe UI, sans-serif" font-size="12" text-anchor="middle" fill="#64748B">&#128196; Scanned Prescription</text>
        <rect x="30" y="60" width="250" height="30" rx="4" fill="rgba(245,158,11,0.2)" stroke="#F59E0B" stroke-width="1.5"/>
        <text x="40" y="80" font-family="Consolas, monospace" font-size="11" fill="#FBBF24">"Calpol 250/5 syp 5ml TDS"</text>
        <text x="155" y="125" font-family="Segoe UI, sans-serif" font-size="10" text-anchor="middle" fill="#94A3B8">Zoom: 150% &#183; Pan &#183; Rotate &#183; Invert</text>
        <text x="155" y="145" font-family="Segoe UI, sans-serif" font-size="9" fill="#10B981" text-anchor="middle">&#128274; 60s Temporary Presigned URL</text>
      </g>

      <!-- Sub-panel Right: Editable Fields -->
      <g transform="translate(345, 56)">
        <rect width="320" height="175" rx="8" fill="#0F172A" stroke="rgba(255,255,255,0.1)"/>
        <text x="16" y="24" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#E2E8F0">Clinical Field Review</text>

        <rect x="16" y="34" width="288" height="36" rx="6" fill="rgba(255,255,255,0.06)"/>
        <text x="24" y="48" font-family="Segoe UI, sans-serif" font-size="9" fill="#94A3B8">Drug &amp; Formulation</text>
        <text x="24" y="62" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#34D399">Paracetamol Oral Liquid (Syrup)</text>

        <rect x="16" y="76" width="288" height="36" rx="6" fill="rgba(255,255,255,0.06)"/>
        <text x="24" y="90" font-family="Segoe UI, sans-serif" font-size="9" fill="#94A3B8">Daily Dosage Timing</text>
        <text x="24" y="104" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">1-1-1 (Morning, Afternoon, Night)</text>

        <rect x="16" y="120" width="138" height="38" rx="6" fill="#10B981"/>
        <text x="85" y="144" font-family="Segoe UI, sans-serif" font-size="12" font-weight="800" fill="#0A3831" text-anchor="middle">&#10003; Confirm Sign-off</text>

        <rect x="166" y="120" width="138" height="38" rx="6" fill="rgba(239,68,68,0.2)" stroke="#EF4444"/>
        <text x="235" y="144" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FCA5A5" text-anchor="middle">&#10007; Reject / Escalate</text>
      </g>
    </g>

    <!-- Step C: Audit & Release -->
    <g transform="translate(1090, 60)">
      <rect width="320" height="250" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.1)"/>
      <text x="16" y="26" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#A78BFA">C. Immutable Audit Log</text>
      <text x="16" y="44" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Cryptographic sign-off stamp</text>

      <rect x="16" y="60" width="288" height="135" rx="6" fill="rgba(255,255,255,0.04)"/>
      <text x="24" y="80" font-family="Consolas, monospace" font-size="10" fill="#A78BFA">&#8226; reviewer_id: Dr. S. Sharma</text>
      <text x="24" y="98" font-family="Consolas, monospace" font-size="10" fill="#E2E8F0">&#8226; transition: REQUIRES_REVIEW &#8594; COMPLETED</text>
      <text x="24" y="116" font-family="Consolas, monospace" font-size="10" fill="#E2E8F0">&#8226; timestamp: 2026-11-05T05:15Z</text>
      <text x="24" y="134" font-family="Consolas, monospace" font-size="10" fill="#34D399">&#8226; integrity_hash: 7f8a3c...e9</text>
      <text x="24" y="152" font-family="Consolas, monospace" font-size="10" fill="#FBBF24">&#8226; field_overrides: 0</text>
      <text x="24" y="170" font-family="Consolas, monospace" font-size="10" fill="#6EE7B7">&#8226; patient_notification: DISPATCHED</text>

      <rect x="16" y="205" width="288" height="32" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="160" y="225" font-family="Segoe UI, sans-serif" font-size="10.5" font-weight="700" fill="#6EE7B7" text-anchor="middle">Ready for Patient Portal Spoken Audio</text>
    </g>
  </g>
</svg>"""

# -----------------------------------------------------------------------------
# 3. USER WORKFLOW JOURNEY (PATIENT & CLINICIAN)
# -----------------------------------------------------------------------------
SVG_USER_WORKFLOW = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <defs>
    <linearGradient id="bg3" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="50%" stop-color="#1E293B"/>
      <stop offset="100%" stop-color="#0F2D25"/>
    </linearGradient>
    <filter id="shadow3" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <rect width="1600" height="1000" fill="url(#bg3)"/>

  <!-- Title Banner -->
  <g transform="translate(80, 50)">
    <rect x="0" y="0" width="48" height="48" rx="14" fill="#10B981"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="20" text-anchor="middle" fill="#0A3831">&#128101;</text>
    <text x="64" y="28" font-family="Segoe UI, sans-serif" font-size="28" font-weight="900" fill="#FFFFFF">PRESCRIPTO AI 2.0</text>
    <text x="64" y="46" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600" fill="#34D399" letter-spacing="1.5">END-TO-END PATIENT &amp; CLINICIAN WORKFLOW JOURNEY</text>
  </g>

  <!-- PATIENT WORKFLOW (UPPER HALF) -->
  <g transform="translate(80, 130)" filter="url(#shadow3)">
    <rect width="1440" height="380" rx="16" fill="rgba(255,255,255,0.05)" stroke="rgba(52,211,153,0.3)" stroke-width="1.5"/>
    <rect width="1440" height="44" rx="16" fill="rgba(16,185,129,0.15)"/>
    <text x="24" y="28" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800" fill="#34D399">&#128104;&#8205;&#9877;&#65039; PATIENT &amp; CAREGIVER EXPERIENCE (MOBILE-FIRST &#183; MULTILINGUAL)</text>
    <text x="1220" y="28" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">CLASS 6 READING LEVEL &#183; 48px TARGETS</text>

    <!-- 5 Patient Steps -->
    <!-- Step 1 -->
    <g transform="translate(30, 65)">
      <rect width="250" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399" text-anchor="middle">1</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Native Script Login</text>
      <text x="20" y="75" font-family="Segoe UI, sans-serif" font-size="11" fill="#9CA3AF">Pick language with 1 tap:</text>

      <rect x="20" y="88" width="100" height="28" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="70" y="106" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#6EE7B7" text-anchor="middle">English</text>

      <rect x="130" y="88" width="100" height="28" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="180" y="106" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#6EE7B7" text-anchor="middle">&#2361;&#2367;&#2344;&#2381;&#2342;&#2368;</text>

      <rect x="20" y="122" width="100" height="28" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="70" y="140" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#6EE7B7" text-anchor="middle">&#2711;&#2753;&#2716;&#2736;&#2750;&#2724;&#2752;</text>

      <rect x="130" y="122" width="100" height="28" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="180" y="140" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#6EE7B7" text-anchor="middle">&#2350;&#2352;&#2368;&#2336;&#2368;</text>

      <text x="20" y="180" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; 10-Digit Mobile Number</text>
      <text x="20" y="200" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; 6 Auto-Advancing OTP boxes</text>
      <text x="20" y="220" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; 30s Resend countdown</text>

      <rect x="20" y="240" width="210" height="26" rx="6" fill="rgba(16,185,129,0.15)"/>
      <text x="125" y="257" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#A7F3D0" text-anchor="middle">No password needed</text>
    </g>

    <!-- Arrow -->
    <path d="M 320 205 L 345 205" stroke="#34D399" stroke-width="3" fill="none" marker-end="url(#arrow)"/>

    <!-- Step 2 -->
    <g transform="translate(320, 65)">
      <rect width="250" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399" text-anchor="middle">2</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Intake Prescription</text>

      <rect x="20" y="70" width="210" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="30" y="90" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">&#128247; Take a Photo</text>
      <text x="30" y="106" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Live camera preview + alignment frame</text>

      <rect x="20" y="130" width="210" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="30" y="150" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">&#128193; Choose from Gallery</text>
      <text x="30" y="166" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">JPEG / PNG / WebP &lt; 20 MB</text>

      <text x="20" y="205" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Client-side downscale &gt;2500px</text>
      <text x="20" y="225" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; DPDPA explicit privacy consent</text>

      <rect x="20" y="240" width="210" height="26" rx="6" fill="rgba(16,185,129,0.15)"/>
      <text x="125" y="257" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#A7F3D0" text-anchor="middle">Step 1 of 3 Progress Bar</text>
    </g>

    <!-- Step 3 -->
    <g transform="translate(610, 65)">
      <rect width="250" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399" text-anchor="middle">3</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Reading &amp; AI Analysis</text>

      <rect x="20" y="70" width="210" height="80" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="30" y="92" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#34D399">&#8987; Honest Waiting Screen</text>
      <text x="30" y="110" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">"Reading your prescription..."</text>
      <text x="30" y="126" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Honest time expectation: 5-10s</text>
      <text x="30" y="140" font-family="Segoe UI, sans-serif" font-size="9" fill="#6EE7B7">Exponential backoff poll (1s, 2s, 3s)</text>

      <text x="20" y="175" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Line-by-line OCR Detection</text>
      <text x="20" y="195" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; CDSCO Drug Master Verification</text>
      <text x="20" y="215" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Duplicate Safety Screening</text>

      <rect x="20" y="240" width="210" height="26" rx="6" fill="rgba(245,158,11,0.2)"/>
      <text x="125" y="257" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#FBBF24" text-anchor="middle">Zero Fake Progress Bars</text>
    </g>

    <!-- Step 4 -->
    <g transform="translate(900, 65)">
      <rect width="250" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399" text-anchor="middle">4</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Result Screen Hero</text>

      <rect x="20" y="70" width="210" height="42" rx="6" fill="rgba(255,255,255,0.05)"/>
      <text x="28" y="88" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">Human Doctor Header</text>
      <text x="28" y="102" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">Dr. Sharma &#183; City Clinic (No raw UUIDs)</text>

      <rect x="20" y="118" width="210" height="52" rx="6" fill="rgba(16,185,129,0.1)"/>
      <text x="28" y="136" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#34D399">&#127749; Sunrise / Sun / Moon</text>
      <text x="28" y="150" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">Morning 1 Tab &#183; Afternoon &#8212; &#183; Night 1</text>
      <text x="28" y="162" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">pc (After food) &#183; 5 Days countdown</text>

      <text x="20" y="192" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Amber border for unconfirmed items</text>
      <text x="20" y="210" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; "Show on photo" bounding overlay</text>
      <text x="20" y="228" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Severity-sorted safety findings</text>

      <rect x="20" y="240" width="210" height="26" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="125" y="257" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#6EE7B7" text-anchor="middle">&#128266; Listen Button per card</text>
    </g>

    <!-- Step 5 -->
    <g transform="translate(1190, 65)">
      <rect width="220" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#10B981" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399" text-anchor="middle">5</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Daily Routine</text>

      <rect x="16" y="70" width="188" height="65" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="24" y="90" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">&#128337; Today Timeline</text>
      <text x="24" y="106" font-family="Segoe UI, sans-serif" font-size="10" fill="#34D399">"Next dose in 45 mins"</text>
      <text x="24" y="122" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">Morning (8am), Lunch (1pm), Night (9pm)</text>

      <rect x="16" y="145" width="188" height="42" rx="6" fill="rgba(16,185,129,0.15)"/>
      <text x="24" y="163" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#6EE7B7">&#10003; Taken (audio chime)</text>
      <text x="24" y="177" font-family="Segoe UI, sans-serif" font-size="9" fill="#E5E7EB">Snooze (15m) &#183; Skip dose</text>

      <text x="16" y="208" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">&#8226; Share to family on WhatsApp</text>
      <text x="16" y="225" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">&#8226; Offline fallback cache</text>

      <rect x="16" y="240" width="188" height="26" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="110" y="257" font-family="Segoe UI, sans-serif" font-size="10" font-weight="700" fill="#A7F3D0" text-anchor="middle">VAPID Push Reminders</text>
    </g>
  </g>

  <!-- CLINICIAN WORKFLOW (LOWER HALF) -->
  <g transform="translate(80, 550)" filter="url(#shadow3)">
    <rect width="1440" height="380" rx="16" fill="rgba(255,255,255,0.05)" stroke="rgba(96,165,250,0.3)" stroke-width="1.5"/>
    <rect width="1440" height="44" rx="16" fill="rgba(59,130,246,0.15)"/>
    <text x="24" y="28" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800" fill="#60A5FA">&#129658; CLINICAL REVIEW WORKSPACE (DOCTOR &#183; PHARMACIST &#183; ADMIN)</text>
    <text x="1220" y="28" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#93C5FD">SAFETY DECISION SUPPORT ONLY</text>

    <!-- 4 Doctor Steps -->
    <!-- Step 1: Login -->
    <g transform="translate(30, 65)">
      <rect width="320" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#3B82F6" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#60A5FA" text-anchor="middle">1</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Clinical Authentication</text>

      <rect x="20" y="70" width="280" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="90" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">Staff Email &amp; Password</text>
      <text x="32" y="106" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">doctor@prescripto.local (PBKDF2 SHA-256)</text>

      <text x="20" y="145" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Role-Based Access Control (RBAC):</text>
      <text x="32" y="165" font-family="Segoe UI, sans-serif" font-size="10" fill="#60A5FA">&#9656; REVIEWER: Sign-off &amp; override authority</text>
      <text x="32" y="185" font-family="Segoe UI, sans-serif" font-size="10" fill="#34D399">&#9656; OPERATOR: Ingestion &amp; triage intake</text>
      <text x="32" y="205" font-family="Segoe UI, sans-serif" font-size="10" fill="#FBBF24">&#9656; ADMIN: Audit logs, deletion vault &amp; health</text>

      <rect x="20" y="235" width="280" height="30" rx="6" fill="#3B82F6" opacity="0.2"/>
      <text x="160" y="254" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#93C5FD" text-anchor="middle">RS256 Asymmetric JWT Session</text>
    </g>

    <!-- Step 2: Queue -->
    <g transform="translate(390, 65)">
      <rect width="320" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#3B82F6" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#60A5FA" text-anchor="middle">2</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Prioritized Review Queue</text>

      <rect x="20" y="70" width="280" height="50" rx="8" fill="rgba(245,158,11,0.15)"/>
      <text x="32" y="90" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FBBF24">Real Patient Names Displayed</text>
      <text x="32" y="106" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">Rahul Verma (PAT-1001) &#183; Waiting 15m</text>

      <text x="20" y="145" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Min-w-0 constrained responsive cards</text>
      <text x="20" y="165" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Eliminates horizontal overflow on 13" laptops</text>
      <text x="20" y="185" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Live badge count of pending scripts</text>
      <text x="20" y="205" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Filter by status: All / Urgent / Flagged</text>

      <rect x="20" y="235" width="280" height="30" rx="6" fill="rgba(255,255,255,0.06)"/>
      <text x="160" y="254" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#60A5FA" text-anchor="middle">Sorted by longest wait time</text>
    </g>

    <!-- Step 3: Split-View -->
    <g transform="translate(750, 65)">
      <rect width="320" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#3B82F6" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#60A5FA" text-anchor="middle">3</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Split-Screen Verification</text>

      <rect x="20" y="70" width="280" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="90" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">Left: High-Res Prescription Photo</text>
      <text x="32" y="106" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Pan, zoom, rotate, highlight bounding boxes</text>

      <rect x="20" y="130" width="280" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="150" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF">Right: Extracted Clinical Form</text>
      <text x="32" y="166" font-family="Segoe UI, sans-serif" font-size="10" fill="#9CA3AF">Inline dose stepper (- / +), frequency, timing</text>

      <text x="20" y="205" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Inline validation prevents malformed saves</text>
      <text x="20" y="222" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Pre-populates CDSCO canonical salt</text>

      <rect x="20" y="235" width="280" height="30" rx="6" fill="#10B981" opacity="0.2"/>
      <text x="160" y="254" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0" text-anchor="middle">Average review time &lt; 30 seconds</text>
    </g>

    <!-- Step 4: Sign-off -->
    <g transform="translate(1110, 65)">
      <rect width="300" height="280" rx="12" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <circle cx="35" cy="35" r="15" fill="#3B82F6" opacity="0.2"/>
      <text x="35" y="40" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#60A5FA" text-anchor="middle">4</text>
      <text x="60" y="38" font-family="Segoe UI, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Clinical Sign-Off &amp; Dossier</text>

      <rect x="20" y="70" width="260" height="60" rx="8" fill="rgba(16,185,129,0.15)"/>
      <text x="32" y="92" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" fill="#34D399">&#10003; Signs Off Record</text>
      <text x="32" y="108" font-family="Segoe UI, sans-serif" font-size="10" fill="#E5E7EB">Status &#8594; COMPLETED / REVIEWED</text>
      <text x="32" y="120" font-family="Segoe UI, sans-serif" font-size="9" fill="#A7F3D0">Instant update to patient mobile portal</text>

      <text x="20" y="150" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Appends to Patient History Timeline</text>
      <text x="20" y="170" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Tracks cumulative drug history</text>
      <text x="20" y="190" font-family="Segoe UI, sans-serif" font-size="11" fill="#E5E7EB">&#8226; Flags chronic medication interactions</text>

      <rect x="20" y="215" width="260" height="50" rx="8" fill="rgba(255,255,255,0.05)"/>
      <text x="32" y="235" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">Immutable Audit Stamp</text>
      <text x="32" y="251" font-family="Segoe UI, sans-serif" font-size="9" fill="#9CA3AF">Reviewer ID + Timestamp + Override diff</text>
    </g>
  </g>
</svg>"""

# -----------------------------------------------------------------------------
# 4. TECH STACK WORKFLOW DIAGRAM
# -----------------------------------------------------------------------------
SVG_TECH_STACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <defs>
    <linearGradient id="bg4" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#090D16"/>
      <stop offset="50%" stop-color="#0D1E1B"/>
      <stop offset="100%" stop-color="#063328"/>
    </linearGradient>
    <filter id="shadow4" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <rect width="1600" height="1000" fill="url(#bg4)"/>

  <!-- Title Banner -->
  <g transform="translate(80, 50)">
    <rect x="0" y="0" width="48" height="48" rx="14" fill="#F59E0B"/>
    <text x="24" y="32" font-family="Segoe UI, sans-serif" font-size="20" text-anchor="middle" fill="#000000">&#9889;</text>
    <text x="64" y="28" font-family="Segoe UI, sans-serif" font-size="28" font-weight="900" fill="#FFFFFF">PRESCRIPTO AI 2.0</text>
    <text x="64" y="46" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600" fill="#FBBF24" letter-spacing="1.5">COMPLETE PRODUCTION TECHNOLOGY STACK &amp; WORKFLOW</text>
  </g>

  <!-- 4 Pillars -->
  <!-- Pillar 1: Frontend -->
  <g transform="translate(80, 130)" filter="url(#shadow4)">
    <rect width="335" height="800" rx="18" fill="rgba(255,255,255,0.05)" stroke="rgba(56,189,248,0.3)" stroke-width="1.5"/>
    <rect width="335" height="50" rx="18" fill="rgba(56,189,248,0.15)"/>
    <text x="20" y="32" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#38BDF8">FRONTEND ARCHITECTURE</text>
    <text x="240" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#BAE6FD">WEB SPA</text>

    <!-- Stack Cards -->
    <g transform="translate(20, 70)" font-family="Segoe UI, sans-serif">
      <rect width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="26" font-size="14" font-weight="700" fill="#FFFFFF">React 19.3 + TypeScript 6</text>
      <text x="16" y="46" font-size="11" fill="#9CA3AF">Strict type checking &#183; Zero runtime errors</text>
      <text x="16" y="64" font-size="11" fill="#E2E8F0">React Router v7 (Patient vs Staff Shells)</text>
      <text x="16" y="80" font-size="10" fill="#38BDF8">Fast concurrent rendering &amp; responsive state</text>

      <rect y="105" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="131" font-size="14" font-weight="700" fill="#FFFFFF">Vite 8.3 + Tailwind CSS 4.3</text>
      <text x="16" y="151" font-size="11" fill="#9CA3AF">Bundled production bundle &lt; 500 kB</text>
      <text x="16" y="169" font-size="11" fill="#E2E8F0">Hot Module Replacement (HMR &lt; 50ms)</text>
      <text x="16" y="185" font-size="10" fill="#38BDF8">Custom clinic CSS design tokens in index.css</text>

      <rect y="210" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="236" font-size="14" font-weight="700" fill="#FFFFFF">Web Speech Synthesis API</text>
      <text x="16" y="256" font-size="11" fill="#9CA3AF">Spoken dosage audio in 4 Indian languages:</text>
      <text x="16" y="274" font-size="11" font-weight="600" fill="#6EE7B7">en-IN &#183; hi-IN (&#2361;&#2367;&#2344;&#2381;&#2342;&#2368;) &#183; gu-IN (&#2711;&#2753;&#2716;&#2736;&#2750;&#2724;&#2752;) &#183; mr-IN</text>
      <text x="16" y="290" font-size="10" fill="#9CA3AF">Elder-friendly rate: 0.9x speed for clear intake</text>

      <rect y="315" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="341" font-size="14" font-weight="700" fill="#FFFFFF">Custom Healthcare SVG Set</text>
      <text x="16" y="361" font-size="11" fill="#9CA3AF">1.75px bespoke medical line icons:</text>
      <text x="16" y="379" font-size="11" fill="#E2E8F0">&#8226; Tablet, Capsule, Syrup, Inhaler, Drops</text>
      <text x="16" y="395" font-size="10" fill="#38BDF8">&#8226; Sunrise, Midday Sun, Moon (3-slot daily schedule)</text>

      <rect y="420" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="446" font-size="14" font-weight="700" fill="#FFFFFF">Service Worker &amp; Web Push</text>
      <text x="16" y="466" font-size="11" fill="#9CA3AF">VAPID Push Notifications API</text>
      <text x="16" y="484" font-size="11" fill="#E2E8F0">Offline asset cache via public/sw.js</text>
      <text x="16" y="500" font-size="10" fill="#38BDF8">PWA manifest with clinic icons</text>

      <rect y="525" width="295" height="180" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="551" font-size="14" font-weight="700" fill="#FFFFFF">Client Utilities &amp; Tests</text>
      <text x="16" y="571" font-size="11" fill="#9CA3AF">&#8226; client-side image downscaling (&lt; 2500px)</text>
      <text x="16" y="589" font-size="11" fill="#9CA3AF">&#8226; Base64 VAPID key converter</text>
      <text x="16" y="607" font-size="11" fill="#9CA3AF">&#8226; Indian shorthand schedule parser</text>
      <text x="16" y="625" font-size="11" fill="#9CA3AF">&#8226; Prescription image highlight projector</text>
      <text x="16" y="650" font-size="12" font-weight="700" fill="#34D399">&#10003; 60/60 Unit Tests Green (Node Runner)</text>
      <text x="16" y="668" font-size="11" font-weight="700" fill="#38BDF8">&#10003; TypeScript 0 Errors Passed</text>
      <text x="16" y="686" font-size="10" fill="#E2E8F0">&#10003; Playwright E2E Accessible Selectors</text>
    </g>
  </g>

  <!-- Pillar 2: Backend -->
  <g transform="translate(445, 130)" filter="url(#shadow4)">
    <rect width="335" height="800" rx="18" fill="rgba(255,255,255,0.05)" stroke="rgba(52,211,153,0.3)" stroke-width="1.5"/>
    <rect width="335" height="50" rx="18" fill="rgba(16,185,129,0.15)"/>
    <text x="20" y="32" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#34D399">BACKEND &amp; API RUNTIME</text>
    <text x="220" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#A7F3D0">FASTAPI / PYTHON</text>

    <g transform="translate(20, 70)" font-family="Segoe UI, sans-serif">
      <rect width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="26" font-size="14" font-weight="700" fill="#FFFFFF">Python 3.12 + FastAPI 0.115</text>
      <text x="16" y="46" font-size="11" fill="#9CA3AF">Asynchronous ASGI Architecture</text>
      <text x="16" y="64" font-size="11" fill="#E2E8F0">Uvicorn 0.53 + Starlette</text>
      <text x="16" y="80" font-size="10" fill="#34D399">Auto OpenAPI documentation at /docs</text>

      <rect y="105" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="131" font-size="14" font-weight="700" fill="#FFFFFF">Pydantic v2 Schema Engine</text>
      <text x="16" y="151" font-size="11" fill="#9CA3AF">Strict input/output data validation</text>
      <text x="16" y="169" font-size="11" fill="#E2E8F0">Parity with OPENAPI.yaml spec</text>
      <text x="16" y="185" font-size="10" fill="#34D399">Custom serializers for patient metadata</text>

      <rect y="210" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="236" font-size="14" font-weight="700" fill="#FFFFFF">SQLAlchemy 2.0 ORM</text>
      <text x="16" y="256" font-size="11" fill="#9CA3AF">Declarative ORM models &amp; relationships</text>
      <text x="16" y="274" font-size="11" fill="#E2E8F0">Alembic schema versioning &amp; migrations</text>
      <text x="16" y="290" font-size="10" fill="#34D399">Connection pool size = 10, max overflow = 20</text>

      <rect y="315" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="341" font-size="14" font-weight="700" fill="#FFFFFF">Asymmetric Auth (RS256 JWT)</text>
      <text x="16" y="361" font-size="11" fill="#9CA3AF">2048-bit RSA Private/Public Keypair</text>
      <text x="16" y="379" font-size="11" fill="#E2E8F0">Access Token TTL = 900s (15 min)</text>
      <text x="16" y="395" font-size="10" fill="#34D399">Refresh Token TTL = 7 Days</text>

      <rect y="420" width="295" height="90" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="446" font-size="14" font-weight="700" fill="#FFFFFF">Storage Client (Boto3 S3)</text>
      <text x="16" y="466" font-size="11" fill="#9CA3AF">HMAC-SHA256 signature generation</text>
      <text x="16" y="484" font-size="11" fill="#E2E8F0">60-second expiring presigned URLs</text>
      <text x="16" y="500" font-size="10" fill="#34D399">Safe local directory path traversal guard</text>

      <rect y="525" width="295" height="180" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="551" font-size="14" font-weight="700" fill="#FFFFFF">WorkerRunner Daemon</text>
      <text x="16" y="571" font-size="11" fill="#9CA3AF">&#8226; Fenced queue engine with generation tokens</text>
      <text x="16" y="589" font-size="11" fill="#9CA3AF">&#8226; Lease heartbeat renewal every 10 seconds</text>
      <text x="16" y="607" font-size="11" fill="#9CA3AF">&#8226; Multi-stage pipeline execution manager</text>
      <text x="16" y="625" font-size="11" fill="#9CA3AF">&#8226; Zero-PHI logging processor (scrubs PII)</text>
      <text x="16" y="650" font-size="12" font-weight="700" fill="#34D399">&#10003; SQLite &amp; PostgreSQL Compatible</text>
      <text x="16" y="668" font-size="11" font-weight="700" fill="#38BDF8">&#10003; 404-over-403 Security Model Enforced</text>
      <text x="16" y="686" font-size="10" fill="#E2E8F0">&#10003; Full Alembic Migration Rollforward</text>
    </g>
  </g>

  <!-- Pillar 3: AI & Vision -->
  <g transform="translate(810, 130)" filter="url(#shadow4)">
    <rect width="335" height="800" rx="18" fill="rgba(255,255,255,0.05)" stroke="rgba(168,85,247,0.3)" stroke-width="1.5"/>
    <rect width="335" height="50" rx="18" fill="rgba(168,85,247,0.15)"/>
    <text x="20" y="32" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#C084FC">AI &amp; DOCUMENT VISION</text>
    <text x="235" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#E9D5FF">ML ENGINE</text>

    <g transform="translate(20, 70)" font-family="Segoe UI, sans-serif">
      <rect width="295" height="110" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="26" font-size="14" font-weight="700" fill="#FFFFFF">Gemini Vision Provider</text>
      <text x="16" y="46" font-size="11" fill="#9CA3AF">gemini-3.5-flash (primary vision model)</text>
      <text x="16" y="64" font-size="11" fill="#E2E8F0">Structured handwriting line OCR</text>
      <text x="16" y="82" font-size="11" fill="#C084FC">gemini-3.6-flash fallback provider</text>
      <text x="16" y="98" font-size="10" fill="#A78BFA">Zero unverified clinical claims made</text>

      <rect y="125" width="295" height="110" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="151" font-size="14" font-weight="700" fill="#FFFFFF">Local RapidOCR / TrOCR</text>
      <text x="16" y="171" font-size="11" fill="#9CA3AF">PyTorch + ONNX Runtime</text>
      <text x="16" y="189" font-size="11" fill="#E2E8F0">Runs locally when network is absent</text>
      <text x="16" y="207" font-size="11" fill="#C084FC">Automatic fallback on Gemini 429 quota</text>
      <text x="16" y="223" font-size="10" fill="#A78BFA">Complete air-gapped clinic resilience</text>

      <rect y="250" width="295" height="110" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="276" font-size="14" font-weight="700" fill="#FFFFFF">Deterministic Regex Engine</text>
      <text x="16" y="296" font-size="11" fill="#9CA3AF">Rule-based dosage and frequency extraction</text>
      <text x="16" y="314" font-size="11" fill="#E2E8F0">OD, BD, TDS, QID, 1-0-1, 1-1-1, pc/ac</text>
      <text x="16" y="332" font-size="11" fill="#C084FC">Interval timings: q4h, q6h, q8h, q12h</text>
      <text x="16" y="348" font-size="10" fill="#A78BFA">Identical repeatable results every run</text>

      <rect y="375" width="295" height="110" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="401" font-size="14" font-weight="700" fill="#FFFFFF">CDSCO Drug Master</text>
      <text x="16" y="421" font-size="11" fill="#9CA3AF">Official Indian regulatory medications</text>
      <text x="16" y="439" font-size="11" fill="#E2E8F0">Brand alias cross-reference dictionary</text>
      <text x="16" y="457" font-size="11" fill="#C084FC">RxNorm CUI mapping where available</text>
      <text x="16" y="473" font-size="10" fill="#A78BFA">Preserved permanently during data deletions</text>

      <rect y="500" width="295" height="205" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="526" font-size="14" font-weight="700" fill="#FFFFFF">Clinical Safety Engine</text>
      <text x="16" y="546" font-size="11" fill="#9CA3AF">&#8226; Independent of LLM (Zero hallucination)</text>
      <text x="16" y="564" font-size="11" fill="#9CA3AF">&#8226; Duplicate active ingredient detector</text>
      <text x="16" y="582" font-size="11" fill="#9CA3AF">&#8226; Maximum daily dosage safety thresholds</text>
      <text x="16" y="600" font-size="11" fill="#9CA3AF">&#8226; Unusual frequency warning banners</text>
      <text x="16" y="618" font-size="11" fill="#9CA3AF">&#8226; Uncertainty model propagates through layers</text>
      <text x="16" y="642" font-size="12" font-weight="700" fill="#34D399">&#10003; 4-State Field Uncertainty Model</text>
      <text x="16" y="660" font-size="11" font-weight="700" fill="#FBBF24">&#10003; NOT_EVALUATED != SAFE Standard</text>
      <text x="16" y="678" font-size="10" fill="#E2E8F0">&#10003; Mandatory Human Review for Ambiguities</text>
    </g>
  </g>

  <!-- Pillar 4: Storage & Infra -->
  <g transform="translate(1175, 130)" filter="url(#shadow4)">
    <rect width="345" height="800" rx="18" fill="rgba(255,255,255,0.05)" stroke="rgba(245,158,11,0.3)" stroke-width="1.5"/>
    <rect width="345" height="50" rx="18" fill="rgba(245,158,11,0.15)"/>
    <text x="20" y="32" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800" fill="#FBBF24">DATA &amp; INFRASTRUCTURE</text>
    <text x="235" y="32" font-family="Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#FDE68A">PERSISTENCE</text>

    <g transform="translate(20, 70)" font-family="Segoe UI, sans-serif">
      <rect width="305" height="120" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="26" font-size="14" font-weight="700" fill="#FFFFFF">PostgreSQL 16+ / SQLite</text>
      <text x="16" y="46" font-size="11" fill="#9CA3AF">ACID Relational Storage</text>
      <text x="16" y="64" font-size="11" fill="#E2E8F0">SELECT FOR UPDATE SKIP LOCKED</text>
      <text x="16" y="82" font-size="11" fill="#FBBF24">Indexed by uploaded_at, patient_ref, status</text>
      <text x="16" y="100" font-size="10" fill="#FDE68A">Strict foreign keys &amp; check constraints</text>

      <rect y="135" width="305" height="120" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="161" font-size="14" font-weight="700" fill="#FFFFFF">MinIO / S3 Object Store</text>
      <text x="16" y="181" font-size="11" fill="#9CA3AF">Encrypted at rest (AES-256)</text>
      <text x="16" y="199" font-size="11" fill="#E2E8F0">Bucket: prescripto</text>
      <text x="16" y="217" font-size="11" fill="#FBBF24">Bucket: prescripto-retention (Vault)</text>
      <text x="16" y="235" font-size="10" fill="#FDE68A">Local fallback: prescripto_storage/ directory</text>

      <rect y="270" width="305" height="120" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="296" font-size="14" font-weight="700" fill="#FFFFFF">DPDPA 2023 Compliance</text>
      <text x="16" y="316" font-size="11" fill="#9CA3AF">Digital Personal Data Protection Act</text>
      <text x="16" y="334" font-size="11" fill="#E2E8F0">Right to erasure &amp; deletion manifests</text>
      <text x="16" y="352" font-size="11" fill="#FBBF24">Explicit user consent before camera upload</text>
      <text x="16" y="370" font-size="10" fill="#FDE68A">Zero health data sharing with 3rd parties</text>

      <rect y="405" width="305" height="120" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="431" font-size="14" font-weight="700" fill="#FFFFFF">Docker Compose &amp; Deploy</text>
      <text x="16" y="451" font-size="11" fill="#9CA3AF">Multi-stage Alpine Dockerfile</text>
      <text x="16" y="469" font-size="11" fill="#E2E8F0">Zero-downtime single container deploy</text>
      <text x="16" y="487" font-size="11" fill="#FBBF24">Render / Vercel deployment presets</text>
      <text x="16" y="505" font-size="10" fill="#FDE68A">Environment variable security validation</text>

      <rect y="540" width="305" height="165" rx="10" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)"/>
      <text x="16" y="566" font-size="14" font-weight="700" fill="#FFFFFF">Security Safeguards</text>
      <text x="16" y="586" font-size="11" fill="#9CA3AF">&#8226; Constant-time HMAC comparison</text>
      <text x="16" y="604" font-size="11" fill="#9CA3AF">&#8226; Path traversal relative_to validation</text>
      <text x="16" y="622" font-size="11" fill="#9CA3AF">&#8226; Magic-byte file format verification</text>
      <text x="16" y="640" font-size="11" fill="#9CA3AF">&#8226; Maximum file upload capped at 20 MB</text>
      <text x="16" y="662" font-size="11" font-weight="700" fill="#34D399">&#10003; 100% Zero-PHI Operational Logs</text>
      <text x="16" y="680" font-size="10" fill="#E2E8F0">&#10003; Isolated Retention Vault Permissioning</text>
    </g>
  </g>
</svg>"""

DIAGRAMS = [
    ("01_system_architecture", SVG_SYSTEM_ARCHITECTURE, 1600, 1000),
    ("02_system_design_pipeline", SVG_SYSTEM_DESIGN, 1600, 1000),
    ("03_user_workflow", SVG_USER_WORKFLOW, 1600, 1000),
    ("04_tech_stack_workflow", SVG_TECH_STACK, 1600, 1000),
]

def main():
    print(f"[1/4] Saving high-resolution vector SVG files to {OUTPUT_DIR}...")
    for name, svg_content, width, height in DIAGRAMS:
        svg_file = OUTPUT_DIR / f"{name}.svg"
        with open(svg_file, "w", encoding="utf-8") as f:
            f.write(svg_content)
        # Also copy to web/public/diagrams for web access
        web_svg = WEB_PUBLIC_DIR / f"{name}.svg"
        with open(web_svg, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"  -> Generated {svg_file.name}")

    print("[2/4] Rendering crisp high-resolution PNG raster images via headless Edge...")
    for name, _, width, height in DIAGRAMS:
        svg_file = OUTPUT_DIR / f"{name}.svg"
        png_file = OUTPUT_DIR / f"{name}.png"
        web_png = WEB_PUBLIC_DIR / f"{name}.png"

        # Temporary HTML wrapper for headless Edge screenshot
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #000; overflow: hidden; width: {width}px; height: {height}px; }}
    svg {{ width: {width}px; height: {height}px; display: block; }}
  </style>
</head>
<body>
  {svg_file.read_text(encoding='utf-8')}
</body>
</html>"""
        temp_html = OUTPUT_DIR / f"temp_{name}.html"
        temp_html.write_text(html_content, encoding="utf-8")

        cmd = [
            EDGE_PATH,
            "--headless",
            "--disable-gpu",
            f"--screenshot={png_file}",
            f"--window-size={width},{height}",
            f"file:///{str(temp_html).replace(chr(92), '/')}",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if temp_html.exists():
            temp_html.unlink()

        if png_file.exists():
            # Copy to web public
            with open(png_file, "rb") as rf:
                with open(web_png, "wb") as wf:
                    wf.write(rf.read())
            print(f"  -> Rendered {png_file.name} ({width}x{height}, {png_file.stat().st_size // 1024} KB)")
        else:
            print(f"  ! Warning: could not render PNG for {name}: {res.stderr}")

    print("[3/4] All diagrams generated successfully!")

if __name__ == "__main__":
    main()


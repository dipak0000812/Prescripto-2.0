# Prescripto 2.0 — Production Changelog

All notable changes and architectural enhancements made during the productionization of Prescripto 2.0.

---

## [2.1.0] — Productionization & Reminders Engine (2026-11-05)

### Phase 1: Core Bug Fixes & Resilient Shorthand Engine
1. **Camera vs. Gallery Intake**:
   - Implemented native mobile camera capture (`capture="environment"`) vs. device gallery picker.
   - Built desktop `CameraCaptureDialog.tsx` using `navigator.mediaDevices.getUserMedia` with real-time video preview, viewfinder guides, snapshot inspection, and graceful permission fallbacks.
   - Added client-side image validation (JPEG, PNG, WebP under 20MB) and downscaling (~2500px long side, 0.85 JPEG) to eliminate upload latency.
2. **Medication Editing & Audit Trail**:
   - Added `PATCH /api/v1/analyses/{id}/medications` with full field validation.
   - Created Alembic migration `0004_medication_audit_trail.py` storing `original_*_raw`, `is_edited`, `edited_by_user_id`, and `edited_at`.
   - Clearing uncertainty flags upon user correction; triggers automatic re-screening of drug interactions and dosage recalculations.
3. **Visual Prescription Inspector ("Show on photo")**:
   - Implemented `PrescriptionImageModal.tsx` with high-resolution pan, pinch-zoom, 90° rotation, and keyboard navigation.
   - Displays animated bounding box highlights for OCR-detected coordinates; displays side-by-side verbatim quoted text when coordinates are absent without synthetic bounding boxes.
4. **Patient Timeline Linking**:
   - Auto-links logged-in patient uploads to their health timeline (`patient_id`).
   - Added staff patient picker at upload: real-time autocomplete search, inline patient registration modal, and walk-in toggle.
5. **Indian Prescription Shorthand & Ratio Formats**:
   - Liquid suspension/syrup auto-detection for ratio concentrations (`250/5`, `120/5`, `20/5`).
   - Unknown forms return `null` instead of erroneously defaulting to tablet.
   - Full parser support for intervals (`q6h`, `q4h`, `q8h`, `q12h`), standard timings (`1-0-1`, `1-1-1`, `1-0-0`, `0-0-1`), and food instructions (`ac`, `pc`, empty stomach).
   - WhatsApp share formatted text generation.
6. **Scan Error Recovery**:
   - Added `POST /api/v1/analyses/{id}/retry` endpoint to re-queue failed prescription analyses without re-uploading files.
   - Translates backend OCR failures into clear patient-facing guidance.

---

### Phase 2: User Journeys & Security Scoping
1. **Patient Data Scoping**:
   - Restricted patient prescription listings and analysis results so patient users can only view prescriptions they uploaded or records linked to their verified `Patient` profile.
   - Maintained doctor/clinician access across all patients within authorized care scopes.
2. **Doctor Review Queue Sign-Off**:
   - Verified clinical review sign-off workflow (`POST /analyses/{id}/review`).
   - Successfully transitions document status to `REVIEWED_COMPLETE` or `REVIEWED_ESCALATED` with reviewer audit notes.

---

### Phase 3: Medicine Reminders Engine & PWA Infrastructure
1. **Database Schema & Migrations**:
   - Added Alembic migration `0005_medicine_reminders.py` creating:
     - `reminder_plans`: Prescription medication plans, scheduled times, active/paused status, and date bounds.
     - `reminder_events`: Individual dose events with statuses (`PENDING`, `SENT`, `TAKEN`, `SNOOZED`, `SKIPPED`, `MISSED`) and timestamps.
     - `push_subscriptions`: Web Push endpoints, p256dh, and auth encryption keys.
2. **Schedule & Calendar Generator**:
   - Generates local reminder times from shorthand patterns (`1-0-1`, `1-1-1`, `q6h`, `HS`, `OD`, etc.).
   - Automatically offsets times (+30m for `pc`/after food, -30m for `ac`/before food).
   - Generates RFC 5545 compliant `.ics` calendar files with embedded `VALARM` alarms.
   - Windows tzdata fallback support for `Asia/Kolkata` (+05:30) and `UTC`.
3. **Web Push & VAPID Integration**:
   - Added `pywebpush` integration with uncompressed P-256 VAPID keypair.
   - Added key generator script `backend/scripts/generate_vapid_keys.py`.
   - Mounted 10 new API endpoints under `/api/v1/reminders/`.
4. **Worker Scheduler Loop**:
   - Integrated reminder dispatcher inside `WorkerRunner`: runs every 30 seconds, delivers Web Push payloads, marks 2-hour overdue doses as `MISSED`, and creates 10-minute follow-ups for `SNOOZE`.
5. **Frontend Reminders UI**:
   - `SetRemindersModal.tsx`: Opens on "Looks right", supports editing reminder times and durations, notification permission prompts, and honest limits disclosure.
   - `TodayRemindersPage.tsx`: Route `/today` displaying Overdue Doses, Upcoming Doses, Completed Doses, adherence metrics, gentle Web Audio chime, and action buttons (`Taken`, `Snooze 10m`, `Skip`).
   - PWA assets: `web/public/manifest.json` and `web/public/sw.js` with background notification actions.
   - Multilingual support for English, Hindi (हिन्दी), Gujarati (ગુજરાતી), and Marathi (मराठी).


# Prescripto 2.0 — Pending Help Article Updates (Phase 1 Changes)

This document tracks all user-facing changes made during Phase 1 that must be incorporated into the Assistant Knowledge Base (`backend/knowledge/app_help/`) during Phase 4 per the Change-Safety Protocol.

---

## 1. Uploading Prescriptions: Camera vs. Gallery & Compression

### User-Facing Behavior
- **"Take a photo" Option**:
  - **On Mobile Devices**: Directly launches the device's native rear camera (`capture="environment"`).
  - **On Desktop Devices**: Opens the **Interactive Camera Capture Dialog** (`CameraCaptureDialog.tsx`). Users can see a live video preview with an alignment guide viewfinder, click **Capture Photo**, inspect the snapshot, choose **Retake** or **Use Photo**, or cancel.
  - **Camera Permission Fallback**: If desktop camera access is denied, blocked, or no webcam exists, the application displays a friendly prompt explaining camera access and gracefully falls back to the native file picker.
- **"Choose from gallery" Option**: Opens the device file browser directly without requesting camera hardware permissions.
- **Client-Side File Validation**:
  - Allowed formats: JPEG, PNG, WebP under 20MB.
  - Unsupported files (e.g., PDF or raw documents) are blocked client-side with a clear instructional banner before consuming upload bandwidth.
- **Client-Side Photo Compression**:
  - Automatically downscales phone camera photos exceeding 2500px on the longest side to ~2500px while preserving aspect ratio.
  - Compresses to standard JPEG (~0.85 quality) in a browser canvas, reducing multi-megabyte camera photos to lightweight payloads for rapid scanning.

### Help Article Title & Topics
- **Article**: `how_to_upload_prescriptions.md`
- **Topics Covered**:
  - Taking a photo with smartphone camera vs. desktop webcam.
  - Troubleshooting camera permissions in browser settings.
  - Supported photo formats and resolution guidelines for clear OCR.

---

## 2. Correcting Extracted Medicines (Edit Medicine Flow)

### User-Facing Behavior
- **"Edit" Button on Medicine Cards**:
  - On the Analysis Detail page (`/analyses/:id`), every medicine card features an **Edit** button.
  - Clicking **Edit** opens the **Edit Medicine Modal** (`EditMedicineModal.tsx`).
- **Editable Fields & Validation**:
  - **Medicine Name**: Required text field. Cannot be left blank.
  - **Strength**: Formats like `500mg`, `650mg`, `250/5ml`.
  - **Frequency**: Quick-select buttons for standard Indian prescription regimens (`1-0-1`, `1-1-1`, `1-0-0`, `0-0-1`, `SOS`) plus a custom frequency text input.
  - **Food Timing**: Clear dropdown options (`before_food`, `after_food`, `with_food`, `anytime`).
  - **Duration**: Number of days as a positive integer (e.g., `5`), or flexible terms (`as needed`, `SOS`, `PRN`).
- **Audit Trail & Safety Re-evaluation**:
  - Changes are persisted via `PATCH /analyses/{id}/medications`.
  - The system preserves original extracted values (`original_*_raw`) and records who made the edit and when (`edited_at`).
  - When changes are saved, uncertainty flags ("Please check this") are cleared for corrected fields.
  - The analysis pipeline immediately re-runs safety screening (checking for drug-drug interactions, duplicate therapies, allergy contraindications, and dose warnings) and refreshes both the schedule and clinical summary.
- **Error Handling**: If the update fails, the modal remains open with an inline alert explaining the error, preventing loss of user input.

### Help Article Title & Topics
- **Article**: `reviewing_and_editing_prescriptions.md`
- **Topics Covered**:
  - How to fix misread medicine names, dosages, or durations.
  - What happens when a medicine is edited (audit history, safety recalculation).
  - Who is permitted to edit a prescription (patient owner, clinician, or reviewer).

---

## 3. "Show on Photo" Visual Inspector

### User-Facing Behavior
- **"Show on photo" Button**:
  - Located on each medicine card on the Analysis Detail page.
  - Clicking it opens the interactive full-screen **Prescription Image Modal** (`PrescriptionImageModal.tsx`).
- **Interactive Controls**:
  - **Zoom**: Zoom In (`+`), Zoom Out (`-`), and mouse scroll wheel.
  - **Pan**: Click and drag to pan across the high-resolution image, or use keyboard arrow keys.
  - **Rotate**: Rotate button or press `r` to rotate 90° clockwise to fix sideways prescription photos.
  - **Reset**: Reset zoom and pan to 100% or press `0`.
  - **Keyboard Accessibility**: `Esc` closes the viewer; arrow keys pan; `+`/`-` zoom.
- **Bounding Box Highlight vs. Verbatim Text**:
  - When OCR coordinates exist (RapidOCR bounding boxes), the image centers on the medicine with an animated cyan bounding box and a medicine name badge.
  - When coordinates do not exist (e.g. Gemini direct multimodal extraction), the viewer displays the full photo alongside a dedicated callout panel showing the exact verbatim extracted line (`original_text`) without generating misleading artificial highlights.

### Help Article Title & Topics
- **Article**: `verifying_prescription_scan.md`
- **Topics Covered**:
  - Inspecting original doctor handwriting against extracted results.
  - Using zoom, pan, and rotate controls.
  - Understanding highlighted regions vs. raw quoted text.

---

## 4. Patient Linking at Upload

### User-Facing Behavior
- **Logged-in Patients**:
  - Prescriptions uploaded by logged-in patient accounts are automatically linked to their profile (`patient_id`).
  - An informational badge ("Linking to your health timeline") confirms automatic linkage.
  - Patients immediately see the new prescription in their personal timeline and Prescriptions list.
- **Clinicians, Reviewers, and Operators**:
  - A tabbed patient selector is provided at upload:
    - **Select Patient**: Real-time searchable autocomplete dropdown of existing patient records.
    - **+ New Patient**: Inline modal to quickly register a new patient (Name, Phone Number, Age, Gender) without leaving the upload screen.
    - **Walk-in**: Checkbox/tab to mark as an unlinked walk-in prescription if patient identity is unknown.

### Help Article Title & Topics
- **Article**: `patient_profiles_and_linking.md`
- **Topics Covered**:
  - Linking prescriptions to patient health timelines.
  - Managing walk-in prescriptions vs. registered patient profiles.
  - Adding a new patient during upload.

---

## 5. Indian Prescription Shorthand & Medicine Form Guide

### User-Facing Behavior
- **Medicine Form Identification**:
  - Concentrations with ratios like `250/5` or `120/5` are accurately identified as syrup/suspension liquids.
  - Distinguishes tablets, capsules, syrups, suspensions, ointments, inhalers, eye/ear drops, and injections.
  - Unknown medicines are displayed without a form label rather than incorrectly defaulting to "TABLET".
- **Shorthand Frequency Interpretation**:
  - Interval timings (`q6h`, `q4h`, `q8h`, `q12h`) are recognized as standard intervals (e.g., `q6h` = every 6 hours / 4 times daily) and not flagged as "Unusual timing".
  - Standard Indian shorthand is supported:
    - `1-0-1`: Morning and Night
    - `1-1-1`: Morning, Afternoon, and Night
    - `1-0-0`: Morning only
    - `0-0-1`: Night only
    - `ac` / `before meals`: 30 minutes before food
    - `pc` / `after food`: after food
    - `SOS` / `PRN`: As needed for symptoms
- **WhatsApp Share**:
  - Formats daily medicine schedules with friendly timing summaries ready for patient copy or WhatsApp share.

### Help Article Title & Topics
- **Article**: `understanding_prescription_schedules.md`
- **Topics Covered**:
  - Common doctor abbreviations (`1-0-1`, `TDS`, `BD`, `q6h`, `SOS`).
  - Liquid medicine dosing (`250/5`, `tsp`, `ml`).
  - Food timings (empty stomach vs. after meals).

---

## 6. Scan Error Recovery & Retrying Scans

### User-Facing Behavior
- **Clear Error Explanations**:
  - When a prescription scan fails, technical backend messages are translated into actionable patient-facing explanations:
    - Low resolution / blur: "The photo is too blurry or low-resolution to read doctor handwriting. Please take a clearer photo with better lighting."
    - Unsupported file / corrupt image: "The uploaded file could not be decoded. Please upload a standard JPG or PNG photo."
    - Temporary server delay: "Processing timed out due to high demand. Please click 'Try again' to retry."
- **Actionable "Try again" / "Retry" Button**:
  - Available on both the **Analysis Detail** screen (`/analyses/:id`) and the **Prescriptions List** (`/prescriptions`) table for any prescription in `FAILED` status.
  - Retrying hits `POST /analyses/{id}/retry`, immediately requeuing the job for analysis without requiring the user to re-select or re-upload the image.

### Help Article Title & Topics
- **Article**: `troubleshooting_failed_scans.md`
- **Topics Covered**:
  - What to do when a prescription scan fails.
  - How to retry without re-uploading.
  - Tips for optimal photo capture (lighting, angle, flat surface).


---

## 7. Daily Medicine Reminders & "Today's Doses"

### User-Facing Behavior
- **"Looks Right" Triggers Reminder Setup**:
  - When a patient clicks **"Looks right"** on the Analysis Detail page, the **Set Daily Medicine Reminders** modal automatically opens (`SetRemindersModal.tsx`).
  - Extracted medicines are auto-mapped into suggested morning, afternoon, and night reminder times based on frequency and food instructions (e.g., 30 minutes before food or after meals).
  - Patients can toggle reminders on/off per medicine, adjust exact reminder times, and set duration days.
- **Web Push Notifications**:
  - Patients can opt in to browser / phone push notifications using standard Web Push (VAPID).
  - Works natively on Android and desktop browsers. On iPhones (iOS 16.4+), informs users to add Prescripto to their Home Screen.
  - Transparent "Honest Limits" disclaimer clarifies that phone battery optimization and Do Not Disturb modes may silence alerts, and digital alarms do not replace medical advice.
- **Calendar Download (.ics)**:
  - Patients can download standard iCalendar (`.ics`) files with pre-configured alarms (`VALARM`) to import directly into Google Calendar, Apple Calendar, or Outlook.
- **"Today's Doses" Dashboard (`/today`)**:
  - Displays today's scheduled doses grouped into:
    - **Overdue Doses**: Prominent alert cards with warning indicators for past-due doses.
    - **Upcoming Today**: Scheduled doses remaining for the day.
    - **Completed Today**: Doses marked as taken or skipped with timestamps.
  - Touch-friendly action buttons:
    - **Taken**: Records dose as taken, plays a gentle Web Audio confirmation chime, updates adherence score.
    - **Snooze 10m**: Postpones alarm by 10 minutes.
    - **Skip**: Records dose as skipped.
  - Overall adherence rate percentage calculated dynamically across completed doses.
- **Navigation Shortcuts**:
  - Added **"Today's Doses"** to the top navigation header and mobile bottom navigation bar with a bell icon.
  - Dedicated **"Today's Medicine Schedule"** banner on the Patient Portal (`/patient-portal`).

### Help Article Title & Topics
- **Article**: `setting_up_medicine_reminders.md`
- **Topics Covered**:
  - How to set reminder alarms after confirming a prescription.
  - Enabling push notifications on phone or browser.
  - Adding medicine schedules to Google/Apple Calendar.
  - Using the Today's Doses screen to track adherence, snooze, or mark doses taken.

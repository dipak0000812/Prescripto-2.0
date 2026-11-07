# Prescripto AI 2.0 — Screenshots, Figures & Visual Assets Dossier

**Document ID:** `DOC-13-FIG`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** Workspace Visual Inventory  
**Date of Extraction:** November 4, 2026  

---

## 1. Visual Asset Catalog

This inventory documents all verified visual assets, automated test screenshots, sample prescription images, and architectural diagrams available in the repository:

| Figure ID | Source File Path | Suggested Academic Report Figure Title | Report Chapter Placement | Content Description | Verified State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FIG-01** | *Mermaid Diagram in DOC-04* | System Component & Tier Architecture | Chapter 3: System Architecture | Block diagram showing Client Tier, API Gateway, Managed PostgreSQL, S3, Worker Engine, and AI Models | Reconstructed from verified code |
| **FIG-02** | *Mermaid Diagram in DOC-04* | End-to-End Processing Sequence & Worker Lease Fencing | Chapter 4: System Workflow & Concurrency | Sequence diagram showing upload, `SKIP LOCKED` job claim, heartbeat renewal, stage execution, and review sign-off | Reconstructed from verified code |
| **FIG-03** | *Mermaid Diagram in DOC-06* | Complete Entity-Relationship (ER) Schema | Chapter 5: Database Design | Schema diagram showing relationships between `users`, `patients`, `documents`, `analyses`, `medications`, and `findings` | Reconstructed from verified models |
| **FIG-04** | User Uploaded Screenshot | Doctor & Staff Multilingual Login Interface | Chapter 6: Authentication & User Interface | Browser view of the authentication portal showing language selector (English, Hindi, Gujarati, Marathi) and demo autofill | Verified in deployed Vercel UI |
| **FIG-05** | `docs/test_screenshots/desktop_1280x800.png` | Clinician Dual-Pane Verification & Sign-off Workspace | Chapter 6: User Interface Implementation | Desktop viewport ($1280 \times 800$) showing high-resolution scan on the left pane and structured confidence cards on the right | Verified in workspace repository |
| **FIG-06** | `docs/test_screenshots/mobile_360x640.png` | Patient Medication Portal with Voice Synthesis (Mobile View) | Chapter 6: Patient Accessibility & Voice UI | Mobile viewport ($360 \times 640$) showing Medicine Hero Cards grouped by morning/afternoon/night schedules and audio listen buttons | Verified in workspace repository |
| **FIG-07** | `docs/test_screenshots/tablet_768x1024.png` | Clinical Review Queue on Tablet Viewport | Chapter 6: Responsive UI & Review Queue | Tablet viewport ($768 \times 1024$) displaying review queue list, stage badges, and review requirement indicators | Verified in workspace repository |
| **FIG-08** | `sample_prescription.png` | Representative Handwritten Medical Prescription Scan | Chapter 7: Experimental Dataset & Perception | Sample handwritten medical prescription used for end-to-end integration testing and OCR verification | Verified in workspace root |
| **FIG-09** | `backend/tests/eval_set/synthetic_01_clean.png` | Baseline Clean Synthetic Prescription Benchmark | Chapter 8: Testing & Evaluation Benchmarks | Clean synthetic prescription with standardized typography used as ground-truth control benchmark | Verified in test suite |
| **FIG-10** | `backend/tests/eval_set/synthetic_02_blur.png` | Adversarial Blurry Prescription Benchmark | Chapter 8: Robustness & Adversarial Testing | Blurred synthetic prescription image used to evaluate the Stage 2 Laplacian variance quality gate | Verified in test suite |
| **FIG-11** | `backend/tests/eval_set/synthetic_07_diabetes_rot.png`| Rotated Prescription Scan Benchmark (90°) | Chapter 8: Robustness & Adversarial Testing | Rotated synthetic diabetic prescription evaluating EXIF orientation and angle invariance | Verified in test suite |
| **FIG-12** | `backend/tests/eval_set/synthetic_10_multidrug_clean.png`| Multi-Drug Polypharmacy Safety Trap Benchmark | Chapter 8: Clinical Safety Evaluation | Synthetic multi-drug prescription containing intentional duplicate active ingredients and dosage traps | Verified in test suite |

---

## 2. Textual Description of Core Visual Interfaces

### 2.1. The Clinician Dual-Pane Workspace (`FIG-05`)
The clinician review interface ([AnalysisDetailPage.tsx](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/pages/AnalysisDetailPage.tsx)) provides a split view designed for high-stress hospital environments:
* **Left Canvas Pane:** Displays the prescription document retrieved via an ephemeral 60-second HMAC signed storage URL. Medical officers can pan, zoom up to 400%, and rotate the image to inspect faded ink strokes.
* **Right Clinical Form Pane:** Each prescribed medication appears as an interactive card. Every field (`name`, `strength`, `dose`, `route`, `frequency`, `duration`, `instructions`) renders a color-coded status badge:
  * **Green Chip:** `CLEAR` (Calibrated confidence $\ge 0.85$)
  * **Amber Chip:** `AMBIGUOUS` (Moderate confidence $0.50\text{--}0.84$; clinician verification required)
  * **Red Chip:** `UNREADABLE` (Stroke illegible; value masked)
  * **Gray Chip:** `NOT_PRESENT` (Field absent from document)
* **Interactive Editing:** Clinicians can click any field to open [EditMedicineModal.tsx](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/components/EditMedicineModal.tsx), providing auto-complete suggestions from the local CDSCO formulary.
* **Action Drawer:** Clinicians choose an immutable sign-off action:
  * `APPROVE`: Confirms all extractions and safety findings.
  * `FLAG`: Flags medication order for physician clarification with mandatory notes.
  * `ESCALATE`: Routes prescription to senior clinical pharmacy committee.

### 2.2. The Patient Medication Schedule & Spoken Voice Portal (`FIG-06`)
Designed specifically for semi-literate or elderly patients:
* **Medicine Hero Cards:** Medicines are grouped visually by ingestion timing rather than alphabetical order:
  * 🌅 **Morning (सुबह / સવારે / सकाळी)**
  * ☀️ **Afternoon (दोपहर / બપોરે / दुपारी)**
  * 🌙 **Night (रात / રાત્રે / रात्री)**
  * ⚠️ **As Needed (SOS / जब ज़रूरत हो)**
* **Dietary Chips:** Large high-contrast chips indicating "After Food" (भोजन के बाद) or "Before Food" (भोजन से पहले).
* **Multilingual Web Speech Audio:** Patients tap the speaker icon (`Volume2`) to trigger browser-native speech synthesis in their preferred language (**English, Hindi, Gujarati, or Marathi**), converting complex medical text into natural vernacular instructions.


# 18. Open Questions and Confirmation Register — Prescripto AI 2.0

This document records all institutional, academic, organizational, and deployment variables that cannot be determined exclusively from the codebase or git history and must be confirmed by the human student developer, project team, or academic guide.

---

## 1. Academic and Institutional Metadata

| Item | Question / Detail | Default Placeholder in Dossier | Confirmed Value (To Be Filled by Student / Guide) |
| :--- | :--- | :--- | :--- |
| **Q-01** | What is the full official name of the university and affiliated engineering college? | `[REQUIRING CONFIRMATION: College Name]` | |
| **Q-02** | What is the exact academic degree being pursued (e.g., Bachelor of Technology in Computer Science & Engineering, Bachelor of Engineering in Information Technology)? | `[REQUIRING CONFIRMATION: Degree Name]` | |
| **Q-03** | What are the full names, roll numbers / student registration numbers, and email addresses of all contributing students? | `[REQUIRING CONFIRMATION: Student Names & Roll Numbers]` | |
| **Q-04** | What is the full academic title, designation, and department of the faculty project supervisor / guide (e.g., Dr. / Prof., Department of CSE)? | `[REQUIRING CONFIRMATION: Project Guide Name & Designation]` | |
| **Q-05** | What is the full name and designation of the Head of the Department (HOD)? | `[REQUIRING CONFIRMATION: Head of Department]` | |
| **Q-06** | What is the official date of project submission and semester examination (e.g., May 2026 / November 2026)? | `[REQUIRING CONFIRMATION: Submission Date]` | |
| **Q-07** | Does the institution require a specific certificate format (e.g., IEEE, institutional standard format with college crest/seal)? | `[REQUIRING CONFIRMATION: Institutional Certificate Format]` | |

---

## 2. Clinical and Regulatory Governance

| Item | Question / Detail | Technical Status in Codebase | Decision Required for Final Academic Defense |
| :--- | :--- | :--- | :--- |
| **Q-08** | Has this software been submitted to an Institutional Ethics Committee (IEC) or Institutional Review Board (IRB) for clinical trial evaluation? | The codebase includes an automated synthetic test suite (`tests/` and `scripts/run_phase*.py`) with 197 test cases, but no real-patient clinical trial data. | Clarify in the report whether the evaluation was conducted exclusively on de-identified synthetic benchmarks or if hospital data was used under an ethics waiver. |
| **Q-09** | What is the planned commercial regulatory classification under the Indian Medical Device Rules (MDR) / CDSCO? | Prescripto 2.0 is architected as a clinical decision support (CDS) perceptual assistant, with all clinical actions gated by human clinicians. | Confirm whether the project report should classify the system as Software as a Medical Device (SaMD) Class B or Non-Device Clinical Decision Support. |

---

## 3. Production Infrastructure and Live Services

| Item | Question / Detail | Implemented State in Codebase | Production Decision Required |
| :--- | :--- | :--- | :--- |
| **Q-10** | Which telecom SMS provider will be contracted for production patient OTP delivery? | In development and testing, mobile authentication accepts demo OTP `123456` (`backend/prescripto/api/v1/routers/auth.py`). | Select and provision production credentials for Twilio, MSG91, or AWS SNS when transitioning to live hospital pilot. |
| **Q-11** | Will production deployments utilize cloud object storage (AWS S3 / Google Cloud Storage) or Render persistent disk volumes? | Storage abstraction layer (`backend/prescripto/storage/client.py`) supports local filesystem and S3 buckets. Render currently deploys with local ephemeral filesystem storage for stateless execution. | Confirm whether production deployments will configure `AWS_S3_BUCKET` or Google Cloud Storage buckets for long-term document retention. |
| **Q-12** | Will the medical formulary be expanded to the complete 15,000+ CDSCO NLEM catalog prior to the academic viva defense? | The current seed script (`backend/scripts/seed_medications.py`) seeds 107 representative medications across all major therapeutic classes. | Decide whether the 107-drug prototype is sufficient for the academic semester defense or if the full NLEM SQL dump should be ingested. |


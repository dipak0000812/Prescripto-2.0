"""
Seed Patients in Prescripto AI 2.0.
Includes Rahul Verma (matching sample_prescription.png) and additional diverse patients.
"""
import uuid
from prescripto.db.session import SessionLocal
from prescripto.db.models.patient import Patient
from prescripto.db.base import utc_now

SAMPLE_PATIENTS = [
    {
        "patient_id": "PAT-1001",
        "name": "Rahul Verma",
        "phone_number": "9876543210",
        "age": 34,
        "gender": "Male",
        "blood_group": "B+",
        "address": "42 Indiranagar, Bengaluru, Karnataka 560038",
        "medical_history": "Seasonal allergies, mild asthma. Previous Upper Respiratory Infection in Oct 2026.",
        "allergies": "Sulfa drugs",
        "emergency_contact": "+91 98765 43219 (Spouse - Priya Verma)",
    },
    {
        "patient_id": "PAT-1002",
        "name": "Pooja Sharma",
        "phone_number": "9812345678",
        "age": 28,
        "gender": "Female",
        "blood_group": "O+",
        "address": "15 Koramangala 4th Block, Bengaluru, Karnataka",
        "medical_history": "History of migraine and acid reflux.",
        "allergies": "Penicillin",
        "emergency_contact": "+91 98123 45670 (Father - Rajesh Sharma)",
    },
    {
        "patient_id": "PAT-1003",
        "name": "Amit Patel",
        "phone_number": "9823456789",
        "age": 52,
        "gender": "Male",
        "blood_group": "A+",
        "address": "77 Whitefield Main Road, Bengaluru, Karnataka",
        "medical_history": "Type 2 Diabetes Mellitus (managed on Metformin), Hypertension.",
        "allergies": "None reported",
        "emergency_contact": "+91 98234 56780 (Son - Rohan Patel)",
    },
    {
        "patient_id": "PAT-1004",
        "name": "Sunita Rao",
        "phone_number": "9834567890",
        "age": 45,
        "gender": "Female",
        "blood_group": "AB+",
        "address": "22 Jayanagar 7th Block, Bengaluru, Karnataka",
        "medical_history": "Hypothyroidism (managed on Thyroxine 50mcg), Vitamin D deficiency.",
        "allergies": "Aspirin",
        "emergency_contact": "+91 98345 67891 (Brother - Vikram Rao)",
    },
]


def seed_patients():
    db = SessionLocal()
    try:
        inserted = 0
        for p_data in SAMPLE_PATIENTS:
            existing = db.query(Patient).filter(
                (Patient.phone_number == p_data["phone_number"]) |
                (Patient.patient_id == p_data["patient_id"])
            ).first()
            if not existing:
                patient = Patient(
                    id=uuid.uuid4(),
                    patient_id=p_data["patient_id"],
                    name=p_data["name"],
                    phone_number=p_data["phone_number"],
                    age=p_data["age"],
                    gender=p_data["gender"],
                    blood_group=p_data["blood_group"],
                    address=p_data["address"],
                    medical_history=p_data["medical_history"],
                    allergies=p_data["allergies"],
                    emergency_contact=p_data["emergency_contact"],
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                db.add(patient)
                inserted += 1
        db.commit()
        total = db.query(Patient).count()
        print(f"Seeded {inserted} new patients. Total patients: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_patients()

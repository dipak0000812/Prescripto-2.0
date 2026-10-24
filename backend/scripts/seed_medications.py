"""
Seed Medication Master with CDSCO-Approved Formulations.
Idempotent: skips already existing entries based on (brand_name, generic_name, strength, dosage_form, route).
"""
import uuid
import sys
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from prescripto.db.session import SessionLocal
from prescripto.db.models.medication import Medication
from prescripto.db.models.registry import KnowledgeSnapshot
from prescripto.db.base import utc_now
from prescripto.audit.logger import configure_logging, get_logger

configure_logging("INFO")
logger = get_logger("prescripto.scripts.seed_medications")

CDSCO_FORMULATIONS: List[Dict[str, Any]] = [
    {
        "brand_name": "Augmentin 625 Duo",
        "generic_name": "Amoxicillin and Potassium Clavulanate",
        "active_ingredients": ["Amoxicillin", "Potassium Clavulanate"],
        "strength": "625mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "214199",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Moxikind-CV 625",
        "generic_name": "Amoxicillin and Potassium Clavulanate",
        "active_ingredients": ["Amoxicillin", "Potassium Clavulanate"],
        "strength": "625mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "214199",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Calpol 650",
        "generic_name": "Paracetamol",
        "active_ingredients": ["Paracetamol"],
        "strength": "650mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "161",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "otc": False},
    },
    {
        "brand_name": "Dolo 650",
        "generic_name": "Paracetamol",
        "active_ingredients": ["Paracetamol"],
        "strength": "650mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "161",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "otc": False},
    },
    {
        "brand_name": "Crocin 500",
        "generic_name": "Paracetamol",
        "active_ingredients": ["Paracetamol"],
        "strength": "500mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "161",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "otc": False},
    },
    {
        "brand_name": "Pan 40",
        "generic_name": "Pantoprazole",
        "active_ingredients": ["Pantoprazole"],
        "strength": "40mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "40790",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Pantocid 40",
        "generic_name": "Pantoprazole",
        "active_ingredients": ["Pantoprazole"],
        "strength": "40mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "40790",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Glycomet 500",
        "generic_name": "Metformin Hydrochloride",
        "active_ingredients": ["Metformin"],
        "strength": "500mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "6809",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Azithral 500",
        "generic_name": "Azithromycin",
        "active_ingredients": ["Azithromycin"],
        "strength": "500mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "18631",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H1"},
    },
    {
        "brand_name": "Atorva 10",
        "generic_name": "Atorvastatin Calcium",
        "active_ingredients": ["Atorvastatin"],
        "strength": "10mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "83367",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Telma 40",
        "generic_name": "Telmisartan",
        "active_ingredients": ["Telmisartan"],
        "strength": "40mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "316049",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
    {
        "brand_name": "Amlong 5",
        "generic_name": "Amlodipine Besylate",
        "active_ingredients": ["Amlodipine"],
        "strength": "5mg",
        "dosage_form": "Tablet",
        "route": "Oral",
        "rxnorm_cui": "17767",
        "source_class": "CDSCO_REGULATORY",
        "source_version": "2024.1",
        "verification_status": "VERIFIED_AUTHORITY",
        "provenance_metadata": {"cdsco_list": "Formulation List 2024", "schedule": "H"},
    },
]


def seed_medications(db: Session) -> int:
    """Inserts CDSCO medications idempotently into the medications table."""
    # Ensure KnowledgeSnapshot exists for CDSCO
    snapshot = db.query(KnowledgeSnapshot).filter(
        KnowledgeSnapshot.source_name == "CDSCO",
        KnowledgeSnapshot.source_version == "2024.1",
    ).first()
    if not snapshot:
        snapshot = KnowledgeSnapshot(
            id=uuid.uuid4(),
            source_name="CDSCO",
            source_version="2024.1",
            license_mode="PUBLIC_DOMAIN",
            snapshot_date=utc_now(),
            record_count=len(CDSCO_FORMULATIONS),
        )
        db.add(snapshot)
        db.flush()

    inserted = 0
    for item in CDSCO_FORMULATIONS:
        existing = db.query(Medication).filter(
            Medication.brand_name == item["brand_name"],
            Medication.generic_name == item["generic_name"],
            Medication.strength == item["strength"],
            Medication.dosage_form == item["dosage_form"],
            Medication.route == item["route"],
        ).first()

        if not existing:
            med = Medication(
                id=uuid.uuid4(),
                brand_name=item["brand_name"],
                generic_name=item["generic_name"],
                active_ingredients=item["active_ingredients"],
                strength=item["strength"],
                dosage_form=item["dosage_form"],
                route=item["route"],
                rxnorm_cui=item["rxnorm_cui"],
                source_class=item["source_class"],
                source_version=item["source_version"],
                verification_status=item["verification_status"],
                provenance_metadata=item["provenance_metadata"],
            )
            db.add(med)
            inserted += 1

    db.commit()
    logger.info("medications_seeded", inserted_count=inserted, total_count=len(CDSCO_FORMULATIONS))
    return inserted


def main() -> None:
    db = SessionLocal()
    try:
        count = seed_medications(db)
        print(f"Successfully seeded {count} CDSCO medications.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Seed the medications table with 100+ commonly prescribed Indian and international medicines.
Run from project root:
    .venv/Scripts/python.exe backend/scripts/seed_medications.py
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = "prescripto.db"

MEDICATIONS = [
    # Antibiotics
    ("Augmentin 625 Duo", "Amoxicillin and Clavulanate Potassium", ["Amoxicillin", "Clavulanate Potassium"], "500mg+125mg", "Tablet", "Oral"),
    ("Amoxicillin 500", "Amoxicillin", ["Amoxicillin"], "500mg", "Capsule", "Oral"),
    ("Amoxicillin 250", "Amoxicillin", ["Amoxicillin"], "250mg", "Capsule", "Oral"),
    ("Azithromycin 500", "Azithromycin", ["Azithromycin"], "500mg", "Tablet", "Oral"),
    ("Azithromycin 250", "Azithromycin", ["Azithromycin"], "250mg", "Tablet", "Oral"),
    ("Ciprofloxacin 500", "Ciprofloxacin", ["Ciprofloxacin"], "500mg", "Tablet", "Oral"),
    ("Ciprofloxacin 250", "Ciprofloxacin", ["Ciprofloxacin"], "250mg", "Tablet", "Oral"),
    ("Levofloxacin 500", "Levofloxacin", ["Levofloxacin"], "500mg", "Tablet", "Oral"),
    ("Levofloxacin 250", "Levofloxacin", ["Levofloxacin"], "250mg", "Tablet", "Oral"),
    ("Metronidazole 400", "Metronidazole", ["Metronidazole"], "400mg", "Tablet", "Oral"),
    ("Cefixime 200", "Cefixime", ["Cefixime"], "200mg", "Tablet", "Oral"),
    ("Cefuroxime 500", "Cefuroxime", ["Cefuroxime"], "500mg", "Tablet", "Oral"),
    ("Cephalexin 500", "Cephalexin", ["Cephalexin"], "500mg", "Capsule", "Oral"),
    ("Doxycycline 100", "Doxycycline", ["Doxycycline"], "100mg", "Capsule", "Oral"),
    ("Ofloxacin 200", "Ofloxacin", ["Ofloxacin"], "200mg", "Tablet", "Oral"),
    ("Norfloxacin 400", "Norfloxacin", ["Norfloxacin"], "400mg", "Tablet", "Oral"),
    ("Clindamycin 300", "Clindamycin", ["Clindamycin"], "300mg", "Capsule", "Oral"),
    # Pain relievers / Analgesics / Antipyretics
    ("Dolo 650", "Paracetamol", ["Paracetamol"], "650mg", "Tablet", "Oral"),
    ("Paracetamol 500", "Paracetamol", ["Paracetamol"], "500mg", "Tablet", "Oral"),
    ("Ibuprofen 400", "Ibuprofen", ["Ibuprofen"], "400mg", "Tablet", "Oral"),
    ("Ibuprofen 200", "Ibuprofen", ["Ibuprofen"], "200mg", "Tablet", "Oral"),
    ("Diclofenac 50", "Diclofenac Sodium", ["Diclofenac Sodium"], "50mg", "Tablet", "Oral"),
    ("Aceclofenac 100", "Aceclofenac", ["Aceclofenac"], "100mg", "Tablet", "Oral"),
    ("Naproxen 500", "Naproxen", ["Naproxen"], "500mg", "Tablet", "Oral"),
    ("Tramadol 50", "Tramadol", ["Tramadol Hydrochloride"], "50mg", "Capsule", "Oral"),
    ("Combiflam", "Ibuprofen + Paracetamol", ["Ibuprofen", "Paracetamol"], "400mg+325mg", "Tablet", "Oral"),
    ("Meftal Spas", "Mefenamic Acid + Dicyclomine", ["Mefenamic Acid", "Dicyclomine"], "250mg+10mg", "Tablet", "Oral"),
    # Antacids / GI
    ("Pantoprazole 40", "Pantoprazole", ["Pantoprazole Sodium"], "40mg", "Tablet", "Oral"),
    ("Omeprazole 20", "Omeprazole", ["Omeprazole"], "20mg", "Capsule", "Oral"),
    ("Rabeprazole 20", "Rabeprazole", ["Rabeprazole Sodium"], "20mg", "Tablet", "Oral"),
    ("Esomeprazole 40", "Esomeprazole", ["Esomeprazole"], "40mg", "Tablet", "Oral"),
    ("Domperidone 10", "Domperidone", ["Domperidone"], "10mg", "Tablet", "Oral"),
    ("Ondansetron 4", "Ondansetron", ["Ondansetron"], "4mg", "Tablet", "Oral"),
    ("Ranitidine 150", "Ranitidine", ["Ranitidine"], "150mg", "Tablet", "Oral"),
    ("Sucralfate 1g", "Sucralfate", ["Sucralfate"], "1g", "Tablet", "Oral"),
    # Antihistamines / Allergy
    ("Cetirizine 10", "Cetirizine", ["Cetirizine Dihydrochloride"], "10mg", "Tablet", "Oral"),
    ("Cetirizine 5", "Cetirizine", ["Cetirizine Dihydrochloride"], "5mg", "Tablet", "Oral"),
    ("Levocetirizine 5", "Levocetirizine", ["Levocetirizine"], "5mg", "Tablet", "Oral"),
    ("Fexofenadine 120", "Fexofenadine", ["Fexofenadine"], "120mg", "Tablet", "Oral"),
    ("Fexofenadine 180", "Fexofenadine", ["Fexofenadine"], "180mg", "Tablet", "Oral"),
    ("Chlorpheniramine 4", "Chlorpheniramine", ["Chlorpheniramine Maleate"], "4mg", "Tablet", "Oral"),
    ("Montelukast 10", "Montelukast", ["Montelukast Sodium"], "10mg", "Tablet", "Oral"),
    # Cardiac / Blood Pressure
    ("Amlodipine 10", "Amlodipine", ["Amlodipine Besylate"], "10mg", "Tablet", "Oral"),
    ("Atenolol 50", "Atenolol", ["Atenolol"], "50mg", "Tablet", "Oral"),
    ("Metoprolol 50", "Metoprolol", ["Metoprolol Succinate"], "50mg", "Tablet", "Oral"),
    ("Losartan 50", "Losartan", ["Losartan Potassium"], "50mg", "Tablet", "Oral"),
    ("Telmisartan 80", "Telmisartan", ["Telmisartan"], "80mg", "Tablet", "Oral"),
    ("Ramipril 5", "Ramipril", ["Ramipril"], "5mg", "Capsule", "Oral"),
    ("Enalapril 5", "Enalapril", ["Enalapril Maleate"], "5mg", "Tablet", "Oral"),
    ("Aspirin 75", "Aspirin", ["Acetylsalicylic Acid"], "75mg", "Tablet", "Oral"),
    ("Clopidogrel 75", "Clopidogrel", ["Clopidogrel Bisulphate"], "75mg", "Tablet", "Oral"),
    ("Ecosprin 75", "Aspirin", ["Acetylsalicylic Acid"], "75mg", "Tablet", "Oral"),
    # Cholesterol
    ("Atorvastatin 20", "Atorvastatin", ["Atorvastatin Calcium"], "20mg", "Tablet", "Oral"),
    ("Rosuvastatin 10", "Rosuvastatin", ["Rosuvastatin Calcium"], "10mg", "Tablet", "Oral"),
    ("Rosuvastatin 20", "Rosuvastatin", ["Rosuvastatin Calcium"], "20mg", "Tablet", "Oral"),
    # Diabetes
    ("Metformin 500", "Metformin", ["Metformin Hydrochloride"], "500mg", "Tablet", "Oral"),
    ("Metformin 850", "Metformin", ["Metformin Hydrochloride"], "850mg", "Tablet", "Oral"),
    ("Metformin 1000", "Metformin", ["Metformin Hydrochloride"], "1000mg", "Tablet", "Oral"),
    ("Glimepiride 1", "Glimepiride", ["Glimepiride"], "1mg", "Tablet", "Oral"),
    ("Glimepiride 2", "Glimepiride", ["Glimepiride"], "2mg", "Tablet", "Oral"),
    ("Gliclazide 80", "Gliclazide", ["Gliclazide"], "80mg", "Tablet", "Oral"),
    ("Sitagliptin 100", "Sitagliptin", ["Sitagliptin Phosphate"], "100mg", "Tablet", "Oral"),
    ("Voglibose 0.3", "Voglibose", ["Voglibose"], "0.3mg", "Tablet", "Oral"),
    # Respiratory / Cough
    ("Salbutamol 4", "Salbutamol", ["Salbutamol Sulphate"], "4mg", "Tablet", "Oral"),
    ("Salbutamol Inhaler", "Salbutamol", ["Salbutamol"], "100mcg", "Inhaler", "Inhalation"),
    ("Budesonide Inhaler", "Budesonide", ["Budesonide"], "200mcg", "Inhaler", "Inhalation"),
    ("Ambroxol 30", "Ambroxol", ["Ambroxol Hydrochloride"], "30mg", "Tablet", "Oral"),
    ("Theophylline 300", "Theophylline", ["Theophylline"], "300mg", "Tablet", "Oral"),
    # Vitamins / Supplements
    ("Vitamin D3 60000 IU", "Cholecalciferol", ["Cholecalciferol"], "60000IU", "Sachet", "Oral"),
    ("Vitamin B Complex", "Vitamin B Complex", ["Thiamine", "Riboflavin", "Niacin", "Pyridoxine", "Cyanocobalamin"], "multivitamin", "Tablet", "Oral"),
    ("Iron + Folic Acid", "Ferrous Sulphate + Folic Acid", ["Ferrous Sulphate", "Folic Acid"], "100mg+0.5mg", "Tablet", "Oral"),
    ("Calcium + Vitamin D3", "Calcium Carbonate + Vitamin D3", ["Calcium Carbonate", "Cholecalciferol"], "500mg+250IU", "Tablet", "Oral"),
    ("Zinc 50", "Zinc Sulphate", ["Zinc Sulphate"], "50mg", "Tablet", "Oral"),
    ("Multivitamin", "Multivitamin", ["Multiple Vitamins and Minerals"], "multivitamin", "Tablet", "Oral"),
    # CNS
    ("Escitalopram 10", "Escitalopram", ["Escitalopram Oxalate"], "10mg", "Tablet", "Oral"),
    ("Sertraline 50", "Sertraline", ["Sertraline Hydrochloride"], "50mg", "Tablet", "Oral"),
    ("Fluoxetine 20", "Fluoxetine", ["Fluoxetine Hydrochloride"], "20mg", "Capsule", "Oral"),
    ("Alprazolam 0.5", "Alprazolam", ["Alprazolam"], "0.5mg", "Tablet", "Oral"),
    ("Clonazepam 0.5", "Clonazepam", ["Clonazepam"], "0.5mg", "Tablet", "Oral"),
    # Steroids
    ("Prednisolone 10", "Prednisolone", ["Prednisolone"], "10mg", "Tablet", "Oral"),
    ("Prednisolone 5", "Prednisolone", ["Prednisolone"], "5mg", "Tablet", "Oral"),
    ("Methylprednisolone 4", "Methylprednisolone", ["Methylprednisolone"], "4mg", "Tablet", "Oral"),
    ("Dexamethasone 0.5", "Dexamethasone", ["Dexamethasone"], "0.5mg", "Tablet", "Oral"),
    ("Deflazacort 6", "Deflazacort", ["Deflazacort"], "6mg", "Tablet", "Oral"),
    # Thyroid
    ("Thyroxine 50", "Levothyroxine", ["Levothyroxine Sodium"], "50mcg", "Tablet", "Oral"),
    ("Thyroxine 100", "Levothyroxine", ["Levothyroxine Sodium"], "100mcg", "Tablet", "Oral"),
    ("Thyroxine 25", "Levothyroxine", ["Levothyroxine Sodium"], "25mcg", "Tablet", "Oral"),
    # Antifungal
    ("Fluconazole 150", "Fluconazole", ["Fluconazole"], "150mg", "Capsule", "Oral"),
    ("Itraconazole 100", "Itraconazole", ["Itraconazole"], "100mg", "Capsule", "Oral"),
    ("Terbinafine 250", "Terbinafine", ["Terbinafine"], "250mg", "Tablet", "Oral"),
    # Muscle Relaxant
    ("Thiocolchicoside 4", "Thiocolchicoside", ["Thiocolchicoside"], "4mg", "Capsule", "Oral"),
    ("Chlorzoxazone 500", "Chlorzoxazone", ["Chlorzoxazone"], "500mg", "Tablet", "Oral"),
    # Topical
    ("Betamethasone Cream", "Betamethasone", ["Betamethasone Valerate"], "0.1%", "Cream", "Topical"),
    ("Mupirocin Ointment", "Mupirocin", ["Mupirocin"], "2%", "Ointment", "Topical"),
    ("Clotrimazole Cream", "Clotrimazole", ["Clotrimazole"], "1%", "Cream", "Topical"),
    # Eye / Ear
    ("Ciprofloxacin Eye Drops", "Ciprofloxacin", ["Ciprofloxacin"], "0.3%", "Eye Drops", "Ophthalmic"),
    ("Tobramycin Eye Drops", "Tobramycin", ["Tobramycin"], "0.3%", "Eye Drops", "Ophthalmic"),
    ("Ofloxacin Ear Drops", "Ofloxacin", ["Ofloxacin"], "0.3%", "Ear Drops", "Otic"),
    # Indian brands commonly seen
    ("Shelcal 500", "Calcium Carbonate + Vitamin D3", ["Calcium Carbonate", "Cholecalciferol"], "500mg+250IU", "Tablet", "Oral"),
    ("Becosules", "Vitamin B Complex + Vitamin C", ["B Vitamins", "Ascorbic Acid"], "multivitamin", "Capsule", "Oral"),
    ("Allegra 120", "Fexofenadine", ["Fexofenadine"], "120mg", "Tablet", "Oral"),
    ("Montair LC", "Montelukast + Levocetirizine", ["Montelukast Sodium", "Levocetirizine"], "10mg+5mg", "Tablet", "Oral"),
    ("Sinarest", "Paracetamol + Phenylephrine + CPM", ["Paracetamol", "Phenylephrine", "Chlorpheniramine Maleate"], "500mg+10mg+2mg", "Tablet", "Oral"),
    ("Voveran 50", "Diclofenac Sodium", ["Diclofenac Sodium"], "50mg", "Tablet", "Oral"),
    ("ORS Powder", "Oral Rehydration Salts", ["Sodium Chloride", "Potassium Chloride", "Sodium Citrate", "Dextrose"], "WHO formula", "Powder", "Oral"),
]


def seed_medications(db_session=None):
    if db_session is not None:
        from prescripto.db.models.medication import Medication
        existing = {m[0] for m in db_session.query(Medication.brand_name).all()}
        inserted = 0
        for brand, generic, ingredients, strength, form, route in MEDICATIONS:
            if brand in existing:
                continue
            med = Medication(
                id=uuid.uuid4(),
                brand_name=brand,
                generic_name=generic,
                active_ingredients=ingredients,
                strength=strength,
                dosage_form=form,
                route=route,
                rxnorm_cui=None,
                source_class="CDSCO_REGULATORY",
                source_version="2024.1",
                verification_status="VERIFIED_AUTHORITY",
                provenance_metadata={"source": "prescripto_seed", "version": "2.0"},
            )
            db_session.add(med)
            existing.add(brand)
            inserted += 1
        db_session.commit()
        return inserted

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT brand_name FROM medications")
    existing = {row[0] for row in cursor.fetchall()}

    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0

    for brand, generic, ingredients, strength, form, route in MEDICATIONS:
        if brand in existing:
            skipped += 1
            continue
        med_id = uuid.uuid4().hex
        cursor.execute(
            """INSERT INTO medications
               (id, brand_name, generic_name, active_ingredients, strength,
                dosage_form, route, rxnorm_cui, source_class, source_version,
                verification_status, provenance_metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'CDSCO_REGULATORY', '2024.1',
                       'VERIFIED_AUTHORITY', ?, ?)""",
            (
                med_id, brand, generic, json.dumps(ingredients), strength,
                form, route,
                json.dumps({"source": "prescripto_seed", "version": "2.0"}),
                now,
            ),
        )
        existing.add(brand)
        inserted += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM medications")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"Seeded {inserted} new medications, skipped {skipped} existing.")
    print(f"Total medications in database: {total}")
    return inserted


def seed():
    seed_medications()


if __name__ == "__main__":
    seed()

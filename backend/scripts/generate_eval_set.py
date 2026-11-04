"""
Generates the synthetic evaluation dataset in backend/tests/eval_set/.
Creates 10 diverse synthetic prescriptions with varying layouts, medications,
and realistic degradations (blur, rotation of 3-8 degrees, low brightness, JPEG compression).
Outputs ground_truth.json formatted as medicines[{name, strength, frequency, duration}].
"""
import os
import json
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
EVAL_DIR = os.path.join(BACKEND_DIR, "tests", "eval_set")
os.makedirs(EVAL_DIR, exist_ok=True)

EVAL_SPECS = [
    {
        "filename": "synthetic_01_clean.png",
        "doctor": "Dr. Ramesh Gupta, MD (Internal Medicine)",
        "clinic": "METRO SPECIALITY CLINIC",
        "patient": "Vikas Malhotra, 42 / M",
        "date": "12-Oct-2026",
        "diagnosis": "Bacterial Pharyngitis & Fever",
        "lines": [
            "1. Amoxicillin 500mg capsule - 1 cap three times daily for 7 days",
            "2. Paracetamol 650mg tablet - 1 tab three times daily for 3 days",
            "3. Cetirizine 10mg tablet - 1 tab once daily at bedtime for 5 days",
        ],
        "degradation": None,
        "medicines": [
            {"name": "Amoxicillin", "strength": "500mg", "frequency": "three times daily", "duration": "7 days"},
            {"name": "Paracetamol", "strength": "650mg", "frequency": "three times daily", "duration": "3 days"},
            {"name": "Cetirizine", "strength": "10mg", "frequency": "once daily at bedtime", "duration": "5 days"},
        ]
    },
    {
        "filename": "synthetic_02_blur.png",
        "doctor": "Dr. Sunita Deshmukh, MBBS, DNB",
        "clinic": "CAREWELL FAMILY HEALTHCARE",
        "patient": "Ananya Sen, 29 / F",
        "date": "15-Oct-2026",
        "diagnosis": "Acute Bronchitis",
        "lines": [
            "1. Azithromycin 500mg tablet - 1 tab once daily for 3 days",
            "2. Pantoprazole 40mg tablet - 1 tab once daily before food for 14 days",
            "3. Levocetirizine 5mg tablet - 1 tab at bedtime for 5 days",
        ],
        "degradation": "blur",
        "medicines": [
            {"name": "Azithromycin", "strength": "500mg", "frequency": "once daily", "duration": "3 days"},
            {"name": "Pantoprazole", "strength": "40mg", "frequency": "once daily", "duration": "14 days"},
            {"name": "Levocetirizine", "strength": "5mg", "frequency": "at bedtime", "duration": "5 days"},
        ]
    },
    {
        "filename": "synthetic_03_rot_pos.png",
        "doctor": "Dr. K. S. Venkatesh, MD (Endocrinology)",
        "clinic": "DIABETES & ENDOCRINE CARE CENTRE",
        "patient": "Mohan Lal, 58 / M",
        "date": "18-Oct-2026",
        "diagnosis": "Type 2 Diabetes Mellitus & Dyslipidemia",
        "lines": [
            "1. Metformin 500mg tablet - 1 tab twice daily with meals for 30 days",
            "2. Glimepiride 1mg tablet - 1 tab once daily before breakfast for 30 days",
            "3. Atorvastatin 20mg tablet - 1 tab once daily at night for 30 days",
        ],
        "degradation": "rot_pos",
        "medicines": [
            {"name": "Metformin", "strength": "500mg", "frequency": "twice daily", "duration": "30 days"},
            {"name": "Glimepiride", "strength": "1mg", "frequency": "once daily", "duration": "30 days"},
            {"name": "Atorvastatin", "strength": "20mg", "frequency": "once daily at night", "duration": "30 days"},
        ]
    },
    {
        "filename": "synthetic_04_rot_neg.png",
        "doctor": "Dr. Farhan Akhtar, MS (General Surgery)",
        "clinic": "CITY GASTRO & SURGICAL CLINIC",
        "patient": "Deepak Verma, 36 / M",
        "date": "20-Oct-2026",
        "diagnosis": "Acute Gastroenteritis & Infection",
        "lines": [
            "1. Ciprofloxacin 500mg tablet - 1 tab twice daily for 5 days",
            "2. Metronidazole 400mg tablet - 1 tab three times daily for 5 days",
            "3. Ondansetron 4mg tablet - 1 tab as needed for nausea for 3 days",
        ],
        "degradation": "rot_neg",
        "medicines": [
            {"name": "Ciprofloxacin", "strength": "500mg", "frequency": "twice daily", "duration": "5 days"},
            {"name": "Metronidazole", "strength": "400mg", "frequency": "three times daily", "duration": "5 days"},
            {"name": "Ondansetron", "strength": "4mg", "frequency": "as needed", "duration": "3 days"},
        ]
    },
    {
        "filename": "synthetic_05_low_brightness.png",
        "doctor": "Dr. Meera Nambiar, MD, DM (Cardiology)",
        "clinic": "HEART CARE & HYPERTENSION CLINIC",
        "patient": "Suresh Menon, 63 / M",
        "date": "22-Oct-2026",
        "diagnosis": "Essential Hypertension Stage II",
        "lines": [
            "1. Telmisartan 40mg tablet - 1 tab once daily in morning for 30 days",
            "2. Amlodipine 5mg tablet - 1 tab once daily in evening for 30 days",
            "3. Hydrochlorothiazide 12.5mg tablet - 1 tab once daily for 30 days",
        ],
        "degradation": "low_brightness",
        "medicines": [
            {"name": "Telmisartan", "strength": "40mg", "frequency": "once daily", "duration": "30 days"},
            {"name": "Amlodipine", "strength": "5mg", "frequency": "once daily", "duration": "30 days"},
            {"name": "Hydrochlorothiazide", "strength": "12.5mg", "frequency": "once daily", "duration": "30 days"},
        ]
    },
    {
        "filename": "synthetic_06_jpeg_compress.jpg",
        "doctor": "Dr. Rajesh Khanna, MBBS (General Physician)",
        "clinic": "COMMUNITY HEALTH DISPENSARY",
        "patient": "Pooja Hegde, 31 / F",
        "date": "24-Oct-2026",
        "diagnosis": "Musculoskeletal Pain & Gastric Irritation",
        "lines": [
            "1. Ibuprofen 400mg tablet - 1 tab three times daily after food for 3 days",
            "2. Paracetamol 500mg tablet - 1 tab as needed for fever for 3 days",
            "3. Domperidone 10mg tablet - 1 tab twice daily before food for 5 days",
        ],
        "degradation": "jpeg_compress",
        "medicines": [
            {"name": "Ibuprofen", "strength": "400mg", "frequency": "three times daily", "duration": "3 days"},
            {"name": "Paracetamol", "strength": "500mg", "frequency": "as needed for fever", "duration": "3 days"},
            {"name": "Domperidone", "strength": "10mg", "frequency": "twice daily", "duration": "5 days"},
        ]
    },
    {
        "filename": "synthetic_07_diabetes_rot.png",
        "doctor": "Dr. Arvind Swamy, MD (Diabetology)",
        "clinic": "APEX DIABETIC CARE",
        "patient": "Harish Chandra, 54 / M",
        "date": "25-Oct-2026",
        "diagnosis": "Uncontrolled Type 2 Diabetes",
        "lines": [
            "1. Dapagliflozin 10mg tablet - 1 tab once daily in morning for 30 days",
            "2. Sitagliptin 100mg tablet - 1 tab once daily after lunch for 30 days",
        ],
        "degradation": "rot_pos_small",
        "medicines": [
            {"name": "Dapagliflozin", "strength": "10mg", "frequency": "once daily", "duration": "30 days"},
            {"name": "Sitagliptin", "strength": "100mg", "frequency": "once daily", "duration": "30 days"},
        ]
    },
    {
        "filename": "synthetic_08_pediatric_blur.png",
        "doctor": "Dr. Neha Kapoor, MD (Pediatrics)",
        "clinic": "CHILD HEALTH & WELLNESS CLINIC",
        "patient": "Master Aarav Joshi, 7 / M",
        "date": "26-Oct-2026",
        "diagnosis": "Otitis Media & Mild Pyrexia",
        "lines": [
            "1. Augmentin 375mg tablet - 1 tab three times daily for 5 days",
            "2. Paracetamol 250mg suspension - 5ml as needed for fever for 3 days",
        ],
        "degradation": "blur",
        "medicines": [
            {"name": "Augmentin", "strength": "375mg", "frequency": "three times daily", "duration": "5 days"},
            {"name": "Paracetamol", "strength": "250mg", "frequency": "as needed for fever", "duration": "3 days"},
        ]
    },
    {
        "filename": "synthetic_09_cardio_rot_neg.png",
        "doctor": "Dr. S. K. Mukherjee, MBBS, MD (Cardiology)",
        "clinic": "EASTERN HEART INSTITUTE",
        "patient": "Bimal Roy, 67 / M",
        "date": "27-Oct-2026",
        "diagnosis": "Post-PTCA Stable CAD & Statin Therapy",
        "lines": [
            "1. Clopidogrel 75mg tablet - 1 tab once daily after breakfast for 30 days",
            "2. Rosuvastatin 10mg tablet - 1 tab once daily at bedtime for 30 days",
            "3. Ramipril 2.5mg tablet - 1 tab once daily in morning for 30 days",
        ],
        "degradation": "rot_neg_large",
        "medicines": [
            {"name": "Clopidogrel", "strength": "75mg", "frequency": "once daily", "duration": "30 days"},
            {"name": "Rosuvastatin", "strength": "10mg", "frequency": "once daily at bedtime", "duration": "30 days"},
            {"name": "Ramipril", "strength": "2.5mg", "frequency": "once daily", "duration": "30 days"},
        ]
    },
    {
        "filename": "synthetic_10_multidrug_clean.png",
        "doctor": "Dr. Ananya Roy, MD (Pulmonology)",
        "clinic": "ADVANCED PULMONARY & ALLERGY CENTRE",
        "patient": "Gitanjali Sen, 38 / F",
        "date": "28-Oct-2026",
        "diagnosis": "Allergic Rhinitis with Mild Persistent Asthma",
        "lines": [
            "1. Doxycycline 100mg capsule - 1 cap twice daily after meals for 7 days",
            "2. Cetirizine 10mg tablet - 1 tab once daily at night for 10 days",
            "3. Montelukast 10mg tablet - 1 tab once daily at night for 10 days",
            "4. Pantoprazole 40mg tablet - 1 tab once daily before breakfast for 7 days",
        ],
        "degradation": None,
        "medicines": [
            {"name": "Doxycycline", "strength": "100mg", "frequency": "twice daily", "duration": "7 days"},
            {"name": "Cetirizine", "strength": "10mg", "frequency": "once daily at night", "duration": "10 days"},
            {"name": "Montelukast", "strength": "10mg", "frequency": "once daily at night", "duration": "10 days"},
            {"name": "Pantoprazole", "strength": "40mg", "frequency": "once daily", "duration": "7 days"},
        ]
    }
]


def generate_eval_set():
    ground_truth = {}

    for spec in EVAL_SPECS:
        width, height = 900, 720
        img = Image.new("RGB", (width, height), color=(250, 250, 248))
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((50, 40), spec["clinic"], fill=(20, 40, 80))
        draw.text((50, 65), spec["doctor"], fill=(50, 50, 50))
        draw.line([(50, 100), (850, 100)], fill=(180, 180, 180), width=2)

        # Patient Info
        draw.text((50, 120), "Patient: " + spec["patient"], fill=(30, 30, 30))
        draw.text((500, 120), "Date: " + spec["date"], fill=(30, 30, 30))
        draw.text((50, 150), "Diagnosis: " + spec["diagnosis"], fill=(30, 30, 30))
        draw.line([(50, 180), (850, 180)], fill=(200, 200, 200), width=1)

        # Rx
        draw.text((50, 205), "Rx (Medicines):", fill=(20, 40, 80))
        y = 245
        for line in spec["lines"]:
            draw.text((70, y), line, fill=(20, 20, 20))
            y += 45

        draw.line([(50, 600), (850, 600)], fill=(180, 180, 180), width=1)
        doc_name = spec["doctor"].split(",")[0]
        draw.text((600, 625), doc_name, fill=(20, 40, 80))
        draw.text((630, 650), "[Signed]", fill=(120, 120, 120))

        # Apply degradation
        deg = spec["degradation"]
        if deg == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        elif deg == "rot_pos":
            img = img.rotate(4, expand=False, fillcolor=(250, 250, 248))
        elif deg == "rot_pos_small":
            img = img.rotate(3, expand=False, fillcolor=(250, 250, 248))
        elif deg == "rot_neg":
            img = img.rotate(-5, expand=False, fillcolor=(250, 250, 248))
        elif deg == "rot_neg_large":
            img = img.rotate(-7, expand=False, fillcolor=(250, 250, 248))
        elif deg == "low_brightness":
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.65)

        out_path = os.path.join(EVAL_DIR, spec["filename"])
        if spec["filename"].endswith(".jpg"):
            img.save(out_path, format="JPEG", quality=35)
        else:
            img.save(out_path, format="PNG")

        ground_truth[spec["filename"]] = {
            "synthetic": True,
            "medicines": spec["medicines"]
        }
        print(f"Generated {spec['filename']} ({len(spec['medicines'])} medicines)")

    gt_path = os.path.join(EVAL_DIR, "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"\nWrote ground_truth.json with {len(ground_truth)} entries to {gt_path}")


if __name__ == "__main__":
    generate_eval_set()


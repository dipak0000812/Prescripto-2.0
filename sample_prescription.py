"""
Generate a synthetic demo prescription image.
"""
from PIL import Image, ImageDraw

def generate_prescription(path: str = "sample_prescription.png"):
    width, height = 900, 700
    img = Image.new("RGB", (width, height), color=(250, 250, 248))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.text((50, 40), "CITY CLINIC & HEALTH CENTER", fill=(20, 40, 80))
    draw.text((50, 65), "Dr. Ananya Sharma, MBBS, MD (General Medicine)", fill=(50, 50, 50))
    draw.text((50, 85), "Reg. No: MED-KA-2018-9941 | Ph: +91 98765 43210", fill=(80, 80, 80))
    draw.line([(50, 110), (850, 110)], fill=(180, 180, 180), width=2)
    
    # Patient Info
    draw.text((50, 130), "Patient Name: Rahul Verma", fill=(30, 30, 30))
    draw.text((450, 130), "Age/Gender: 34 / M", fill=(30, 30, 30))
    draw.text((50, 155), "Date: 10-Oct-2026", fill=(30, 30, 30))
    draw.text((450, 155), "Diagnosis: Upper Respiratory Tract Infection", fill=(30, 30, 30))
    draw.line([(50, 185), (850, 185)], fill=(200, 200, 200), width=1)
    
    # Rx
    draw.text((50, 210), "Rx", fill=(20, 40, 80))
    
    lines = [
        "1. Amoxicillin 500mg capsule",
        "   Sig: 1 cap three times daily after food for 7 days",
        "",
        "2. Paracetamol 650mg tablet",
        "   Sig: 1 tab as needed for fever every 6 hours",
        "",
        "3. Cetirizine 10mg tablet",
        "   Sig: 1 tab at bedtime for 5 days",
    ]
    
    y = 250
    for line in lines:
        draw.text((80, y), line, fill=(20, 20, 20))
        y += 35
        
    draw.line([(50, 580), (850, 580)], fill=(180, 180, 180), width=1)
    draw.text((600, 610), "Dr. Ananya Sharma", fill=(20, 40, 80))
    draw.text((630, 635), "[Signature]", fill=(120, 120, 120))
    
    img.save(path, format="PNG")
    print(f"Generated prescription image at {path}")

if __name__ == "__main__":
    generate_prescription()

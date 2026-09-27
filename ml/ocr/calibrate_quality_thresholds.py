from quality_check import check_blur, check_exposure
import os

folder = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset"
sample_files = ["1.jpg", "10.jpg", "45.jpg", "90.jpg", "100.jpg"]  # mix of known-good prescriptions

for fname in sample_files:
    path = os.path.join(folder, fname)
    if not os.path.exists(path):
        print(f"Missing: {fname}")
        continue
    sharp_ok, blur = check_blur(path)
    exp_ok, brightness = check_exposure(path)
    print(f"{fname}: blur={blur:.1f} sharp_ok={sharp_ok} | brightness={brightness:.1f} exposure_ok={exp_ok}")
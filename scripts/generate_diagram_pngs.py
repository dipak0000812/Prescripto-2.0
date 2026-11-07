"""
Prescripto AI 2.0 — Publication-Grade Diagram Generator (Pure PIL).
Renders 4 standalone 1920x1080 PNG diagrams:
1. 01_system_architecture.png
2. 02_system_design_pipeline.png
3. 03_user_workflow.png
4. 04_tech_stack_workflow.png
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("docs/architecture_diagrams").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR = Path("web/public/diagrams").resolve()
WEB_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1920, 1080

# Color Palette (Prescripto Warm Forest & Slate)
BG_COLOR = (8, 30, 26)           # Deep forest background
CARD_BG = (16, 48, 42)          # Card background
CARD_BORDER = (34, 90, 80)      # Border
EMERALD = (16, 185, 129)        # Primary brand green
EMERALD_LIGHT = (110, 231, 183) # Light green
AMBER = (245, 158, 11)          # Accent warning/pending
AMBER_LIGHT = (252, 211, 77)
BLUE = (59, 130, 246)           # Technical highlight
BLUE_LIGHT = (147, 197, 253)
WHITE = (255, 255, 255)
TEXT_MUTED = (160, 180, 175)
TEXT_DIM = (120, 145, 140)
DARK_CARD = (11, 38, 33)

def get_font(size, bold=False):
    font_name = "segoeuib.ttf" if bold else "segoeui.ttf"
    try:
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

def draw_header(draw, title, subtitle, tag="LOCKED BASELINE v1.1"):
    # Header container
    draw.rounded_rectangle([60, 40, WIDTH - 60, 120], radius=16, fill=(12, 42, 37), outline=CARD_BORDER, width=2)
    
    # Shield icon badge
    draw.rounded_rectangle([80, 52, 136, 108], radius=12, fill=EMERALD)
    draw.text((108, 62), "+", fill=(6, 34, 29), font=get_font(32, bold=True), anchor="mm")
    
    # Title & Subtitle
    draw.text((155, 62), title, fill=WHITE, font=get_font(26, bold=True))
    draw.text((155, 92), subtitle, fill=EMERALD_LIGHT, font=get_font(15, bold=False))
    
    # Status Tag
    tag_font = get_font(13, bold=True)
    draw.rounded_rectangle([WIDTH - 280, 60, WIDTH - 80, 100], radius=20, fill=(20, 60, 52), outline=EMERALD, width=1)
    draw.ellipse([WIDTH - 265, 76, WIDTH - 253, 84], fill=EMERALD)
    draw.text((WIDTH - 170, 80), tag, fill=WHITE, font=tag_font, anchor="mm")

def draw_card(draw, box, title, subtitle=None, header_color=EMERALD, fill=CARD_BG, outline=CARD_BORDER):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=14, fill=fill, outline=outline, width=2)
    # Header banner
    draw.rounded_rectangle([x1, y1, x2, y1 + 42], radius=14, fill=(header_color[0]//4, header_color[1]//4, header_color[2]//4))
    draw.line([x1, y1 + 42, x2, y1 + 42], fill=outline, width=1)
    draw.text((x1 + 16, y1 + 21), title, fill=WHITE, font=get_font(15, bold=True), anchor="lm")
    if subtitle:
        draw.text((x2 - 16, y1 + 21), subtitle, fill=TEXT_MUTED, font=get_font(12), anchor="rm")

def draw_pill(draw, x, y, text, color=EMERALD, text_color=WHITE):
    font = get_font(12, bold=True)
    bbox = font.getbbox(text)
    pw = (bbox[2] - bbox[0]) + 18
    ph = 24
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=12, fill=(color[0]//3, color[1]//3, color[2]//3), outline=color, width=1)
    draw.text((x + pw // 2, y + ph // 2), text, fill=text_color, font=font, anchor="mm")
    return pw + 8

def draw_arrow(draw, start, end, color=EMERALD, width=3):
    x1, y1 = start
    x2, y2 = end
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    # Simple arrowhead
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 12
    arrow_angle = math.pi / 6
    xa1 = x2 - arrow_len * math.cos(angle - arrow_angle)
    ya1 = y2 - arrow_len * math.sin(angle - arrow_angle)
    xa2 = x2 - arrow_len * math.cos(angle + arrow_angle)
    ya2 = y2 - arrow_len * math.sin(angle + arrow_angle)
    draw.polygon([(x2, y2), (xa1, ya1), (xa2, ya2)], fill=color)

# =============================================================================
# 1. SYSTEM ARCHITECTURE
# =============================================================================
def generate_system_architecture():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "PRESCRIPTO AI 2.0 — END-TO-END SYSTEM ARCHITECTURE", "Modular Monolithic Architecture: Client, Gateway, Processing Engine, Storage & Cloud Services")

    col_w = 405
    col_gap = 25
    start_x = 60
    top_y = 150
    h = 880

    # Column 1: Presentation Tier
    c1_x = start_x
    draw_card(draw, [c1_x, top_y, c1_x + col_w, top_y + h], "1. PRESENTATION TIER", "SPA / PWA", EMERALD)
    
    # Sub-card 1: Patient App
    draw_card(draw, [c1_x + 15, top_y + 55, c1_x + col_w - 15, top_y + 440], "Patient Mobile Web Shell", "Mobile PWA", BLUE, fill=DARK_CARD)
    y = top_y + 115
    items_patient = [
        ("Camera / Gallery Upload", "HTML5 capture + frame guides, file picker"),
        ("Multilingual UI Shell", "EN, Hindi, Gujarati, Marathi switch"),
        ("3-Slot Visual Schedule", "Morning (Sunrise), Noon (Sun), Night (Moon)"),
        ("Audio Speech Player", "Local Web Speech API synthesis playback"),
        ("Scan Status Tracker", "Live polling + instant state updates"),
        ("Consent & Privacy Dialog", "DPDPA patient data handling disclosure")
    ]
    for title, desc in items_patient:
        draw.rounded_rectangle([c1_x + 25, y, c1_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c1_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c1_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Sub-card 2: Clinician Portal
    draw_card(draw, [c1_x + 15, top_y + 460, c1_x + col_w - 15, top_y + 850], "Doctor & Staff Review Console", "Desktop Pro", AMBER, fill=DARK_CARD)
    y = top_y + 520
    items_doctor = [
        ("Triage Review Queue", "Priority sorting by confidence & risk flags"),
        ("Side-by-Side Reviewer", "Split-screen: original image vs. extracted JSON"),
        ("Interactive Bounding Boxes", "Hoverable polygon coordinates on Rx slip"),
        ("One-Click Field Edit", "Correct dose, frequency, drug name with fuzzy search"),
        ("Audit Action Log", "Doctor ID, timestamp, diff trail recorded"),
        ("Instant Patient Notify", "Dispatches update event to patient schedule")
    ]
    for title, desc in items_doctor:
        draw.rounded_rectangle([c1_x + 25, y, c1_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c1_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c1_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Column 2: Application Gateway
    c2_x = c1_x + col_w + col_gap
    draw_card(draw, [c2_x, top_y, c2_x + col_w, top_y + h], "2. APPLICATION GATEWAY", "FastAPI / Python", BLUE)
    
    # Sub-card 1: Core API Routers
    draw_card(draw, [c2_x + 15, top_y + 55, c2_x + col_w - 15, top_y + 510], "REST API & Auth Routers", "FastAPI Monolith", EMERALD, fill=DARK_CARD)
    y = top_y + 115
    routers = [
        ("POST /prescriptions/upload", "Multi-part image stream, session binding"),
        ("GET /prescriptions/{id}", "Normalized prescription JSON & status"),
        ("GET /prescriptions/queue", "Triage list for human-in-the-loop review"),
        ("POST /prescriptions/review", "Doctor approval, edit diffs, verification"),
        ("GET /audio/synthesize", "Edge & server-side speech audio bytes"),
        ("POST /safety/verify", "Dosage ceiling, drug interaction validation"),
        ("POST /auth/login & /verify-otp", "JWT bearer token, role-based claims")
    ]
    for title, desc in routers:
        draw.rounded_rectangle([c2_x + 25, y, c2_x + col_w - 25, y + 46], radius=8, fill=(20, 56, 48))
        draw.text((c2_x + 35, y + 14), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c2_x + 35, y + 30), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 54

    # Sub-card 2: Middleware & Security
    draw_card(draw, [c2_x + 15, top_y + 530, c2_x + col_w - 15, top_y + 850], "Security & Middleware Layer", "Guardrails", AMBER, fill=DARK_CARD)
    y = top_y + 590
    security = [
        ("CORS & Origin Filtering", "Restricts origins to authorized PWA & portals"),
        ("Rate Limiter (Token Bucket)", "Prevents denial-of-service on inference APIs"),
        ("JWT Auth & Scopes", "Strict patient vs. reviewer vs. admin privileges"),
        ("Structured Logging (structlog)", "JSON logs with correlation IDs & audit trail")
    ]
    for title, desc in security:
        draw.rounded_rectangle([c2_x + 25, y, c2_x + col_w - 25, y + 50], radius=8, fill=(20, 56, 48))
        draw.text((c2_x + 35, y + 16), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c2_x + 35, y + 33), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 58

    # Column 3: Processing & AI Engine
    c3_x = c2_x + col_w + col_gap
    draw_card(draw, [c3_x, top_y, c3_x + col_w, top_y + h], "3. AI & VISION ENGINE", "Hybrid Pipeline", AMBER)
    
    # Sub-card 1: Async Worker Daemon
    draw_card(draw, [c3_x + 15, top_y + 55, c3_x + col_w - 15, top_y + 440], "Async Pipeline Daemon", "Worker Loop", EMERALD, fill=DARK_CARD)
    y = top_y + 115
    pipeline = [
        ("Image Orientation & Crop", "Auto EXIF transpose, perspective rectification"),
        ("Laplacian Blur Filter", "Rejects unreadable images before model call"),
        ("Primary: Gemini 2.5 Flash", "Multimodal vision handwriting extraction"),
        ("Fallback: RapidOCR ONNX", "Zero-cloud local inference if offline/quota"),
        ("Clinical Medical Normalizer", "Maps brand names to generic pharmacology"),
        ("Confidence Scorer", "Assigns word-level & overall certainty scores")
    ]
    for title, desc in pipeline:
        draw.rounded_rectangle([c3_x + 25, y, c3_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c3_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c3_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Sub-card 2: Clinical Decision Engine
    draw_card(draw, [c3_x + 15, top_y + 460, c3_x + col_w - 15, top_y + 850], "Safety & Schedule Normalizer", "Rules Engine", BLUE, fill=DARK_CARD)
    y = top_y + 520
    safety_items = [
        ("3-Slot Scheduler", "Converts '1-0-1' or 'TID' into Morning/Noon/Night"),
        ("Food Timing Normalizer", "Standardizes 'pc'/'ac' -> Before/After Meals"),
        ("Maximum Daily Dose Check", "Flags dangerous paracetamol > 4000mg/day"),
        ("Pediatric / Pregnancy Warning", "Identifies contraindicated drug combinations"),
        ("Audit Diff Engine", "Tracks AI-detected vs. human-confirmed edits"),
        ("Multilingual Translation", "Generates instructions in Hindi, Guj, Mar")
    ]
    for title, desc in safety_items:
        draw.rounded_rectangle([c3_x + 25, y, c3_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c3_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c3_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Column 4: Storage & Infrastructure
    c4_x = c3_x + col_w + col_gap
    draw_card(draw, [c4_x, top_y, c4_x + col_w, top_y + h], "4. STORAGE & INFRA", "State & Comms", EMERALD)
    
    # Sub-card 1: Relational Database
    draw_card(draw, [c4_x + 15, top_y + 55, c4_x + col_w - 15, top_y + 440], "Relational Database", "PostgreSQL / SQLite", BLUE, fill=DARK_CARD)
    y = top_y + 115
    db_items = [
        ("SQLAlchemy 2.0 Async ORM", "Declarative schema models with async engine"),
        ("Alembic Database Migrations", "Strict backward-compatible schema versioning"),
        ("Prescriptions & Medicines", "Normalized JSON fields, dose metadata"),
        ("Patients & Users Table", "Mobile numbers, hashed passwords, roles"),
        ("Audit Trail Logs", "Immutable records of every doctor review edit"),
        ("Full-Text Search Index", "Rapid drug lookup and fuzzy query support")
    ]
    for title, desc in db_items:
        draw.rounded_rectangle([c4_x + 25, y, c4_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c4_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c4_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Sub-card 2: Storage & Web Push
    draw_card(draw, [c4_x + 15, top_y + 460, c4_x + col_w - 15, top_y + 850], "Object Storage & Messaging", "S3 / VAPID", AMBER, fill=DARK_CARD)
    y = top_y + 520
    infra_items = [
        ("MinIO / AWS S3 Storage", "Encrypted prescription image slips & crops"),
        ("Presigned GET / PUT URLs", "Time-limited direct download tokens"),
        ("VAPID Web Push (pywebpush)", "Browser notification when review finishes"),
        ("Event Notification Bus", "Broadcasts status changes between services"),
        ("DPDPA Data Retention Policy", "Automatic scrub / anonymization triggers"),
        ("Health & Readiness Probes", "`/health` endpoints for zero-downtime deploy")
    ]
    for title, desc in infra_items:
        draw.rounded_rectangle([c4_x + 25, y, c4_x + col_w - 25, y + 44], radius=8, fill=(20, 56, 48))
        draw.text((c4_x + 35, y + 13), title, fill=WHITE, font=get_font(13, bold=True))
        draw.text((c4_x + 35, y + 29), desc, fill=TEXT_MUTED, font=get_font(11))
        y += 52

    # Draw Inter-Tier Flow Arrows
    draw_arrow(draw, (c1_x + col_w, top_y + 250), (c2_x, top_y + 250), EMERALD, width=3)
    draw_arrow(draw, (c2_x + col_w, top_y + 250), (c3_x, top_y + 250), AMBER, width=3)
    draw_arrow(draw, (c3_x + col_w, top_y + 250), (c4_x, top_y + 250), BLUE, width=3)
    # Return arrow for doctor review
    draw_arrow(draw, (c4_x, top_y + 650), (c3_x + col_w, top_y + 650), BLUE, width=2)
    draw_arrow(draw, (c3_x, top_y + 650), (c2_x + col_w, top_y + 650), AMBER, width=2)
    draw_arrow(draw, (c2_x, top_y + 650), (c1_x + col_w, top_y + 650), EMERALD, width=2)

    # Footer note
    draw.text((WIDTH // 2, HEIGHT - 25), "Prescripto AI 2.0 • Standard High-Reliability Architecture • Fully Local Fallback Ready", fill=TEXT_DIM, font=get_font(13), anchor="mm")

    path = OUTPUT_DIR / "01_system_architecture.png"
    img.save(path, quality=95)
    img.save(WEB_DIR / "01_system_architecture.png", quality=95)
    print(f"  -> Generated {path.name}")

# =============================================================================
# 2. SYSTEM DESIGN & PROCESSING PIPELINE
# =============================================================================
def generate_system_design_pipeline():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "PRESCRIPTO AI 2.0 — 7-STAGE INGESTION & SAFETY PIPELINE", "Deterministic Medical Pipeline: From Raw Handwritten Photo to Multilingual Verified Schedule")

    stages = [
        ("STAGE 1", "Image Ingestion", "Upload & Validation", [
            "Multipart upload stream",
            "EXIF orientation normalize",
            "Image format check (JPEG, PNG)",
            "Hash idempotency check",
            "Raw image saved to S3/MinIO"
        ], EMERALD),
        ("STAGE 2", "Quality Gate", "Blur & Glare Check", [
            "Laplacian variance metric",
            "Threshold: Variance >= 100",
            "Auto-reject motion blur",
            "Contrast & lighting check",
            "Immediate retry hint if failed"
        ], BLUE),
        ("STAGE 3", "Hybrid OCR", "Multimodal Vision", [
            "Primary: Gemini 2.5 Flash",
            "High-res handwriting OCR",
            "Fallback: RapidOCR ONNX",
            "Local zero-cloud offline mode",
            "Extracts raw tokens & bounds"
        ], AMBER),
        ("STAGE 4", "Medical NLP", "Entity Extraction", [
            "Drug name matching",
            "Dosage strength (mg, ml)",
            "Form (Tab, Syrup, Cap)",
            "Frequency parsing (1-0-1, q6h)",
            "Duration span (5 days, etc.)"
        ], BLUE),
        ("STAGE 5", "Schedule Engine", "3-Slot Mapping", [
            "Morning (Sunrise) slot",
            "Afternoon (Sun) slot",
            "Night (Moon) slot",
            "Meal relation (Before/After)",
            "Special timing instructions"
        ], EMERALD),
        ("STAGE 6", "Safety Gate", "Dosage & Conflict", [
            "Ceiling dose check",
            "Drug-drug interactions",
            "Contraindication lookup",
            "Confidence scoring (0-100%)",
            "Ambiguity flag trigger"
        ], AMBER),
        ("STAGE 7", "Dual Routing", "Delivery & Review", [
            "Score >= 80% -> Direct Publish",
            "Score < 80% -> Doctor Triage",
            "Side-by-side human review",
            "1-click doctor verification",
            "Multilingual audio generated"
        ], EMERALD)
    ]

    card_w = 230
    gap = 20
    start_x = (WIDTH - (len(stages) * card_w + (len(stages) - 1) * gap)) // 2
    top_y = 160
    card_h = 580

    for idx, (stage_num, title, sub, bullets, color) in enumerate(stages):
        x = start_x + idx * (card_w + gap)
        # Stage card
        draw_card(draw, [x, top_y, x + card_w, top_y + card_h], stage_num, sub, header_color=color, fill=DARK_CARD)
        
        # Big Title
        draw.text((x + card_w // 2, top_y + 70), title, fill=WHITE, font=get_font(18, bold=True), anchor="mm")
        draw.line([x + 20, top_y + 95, x + card_w - 20, top_y + 95], fill=CARD_BORDER, width=1)
        
        # Bullets
        by = top_y + 115
        for b in bullets:
            draw.ellipse([x + 20, by + 6, x + 26, by + 12], fill=color)
            draw.text((x + 35, by), b, fill=TEXT_MUTED, font=get_font(12))
            by += 44

        # Connector arrow to next stage
        if idx < len(stages) - 1:
            next_x = x + card_w + gap
            draw_arrow(draw, (x + card_w + 2, top_y + card_h // 2), (next_x - 4, top_y + card_h // 2), color=EMERALD, width=3)

    # Bottom Architecture Summary Cards (Dual Path Detail)
    bottom_y = top_y + card_h + 35
    bottom_h = 240
    path_w = (WIDTH - 120 - 30) // 2

    # Path A: Automated Fast-Path
    draw_card(draw, [60, bottom_y, 60 + path_w, bottom_y + bottom_h], "PATH A: HIGH-CONFIDENCE AUTOMATED RELEASE (>=80% Score)", "Latency < 2.5s", EMERALD)
    draw.text((85, bottom_y + 65), "• Bypasses manual review queue when handwriting clarity and dosage match CDSCO database strictly.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85, bottom_y + 98), "• Instantly renders 3-slot visual schedule cards on patient's smartphone with high-contrast pill forms.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85, bottom_y + 131), "• Generates multilingual speech synthesis audio (English, Hindi, Gujarati, Marathi) via Web Speech API.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85, bottom_y + 164), "• Triggers automated WhatsApp / SMS reminder notifications matching Morning, Noon, and Night slots.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85, bottom_y + 197), "• Stores full immutable cryptographic analysis audit log with raw AI confidence matrix.", fill=TEXT_MUTED, font=get_font(14))

    # Path B: Human-in-the-Loop Clinical Triage
    draw_card(draw, [60 + path_w + 30, bottom_y, WIDTH - 60, bottom_y + bottom_h], "PATH B: HUMAN-IN-THE-LOOP CLINICAL TRIAGE (<80% or Safety Flag)", "Guaranteed Zero-Guesswork", AMBER)
    draw.text((85 + path_w + 30, bottom_y + 65), "• Prescription instantly flagged into Doctor Review Queue with specific amber warning highlights.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85 + path_w + 30, bottom_y + 98), "• Doctor inspects original high-res slip with overlay bounding polygons side-by-side with parsed fields.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85 + path_w + 30, bottom_y + 131), "• One-click inline corrections for ambiguous drug names, frequency misalignments, or missing duration.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85 + path_w + 30, bottom_y + 164), "• Verified with licensed doctor digital stamp; audit log captures original vs corrected field diffs.", fill=TEXT_MUTED, font=get_font(14))
    draw.text((85 + path_w + 30, bottom_y + 197), "• Real-time WebSocket / push alert immediately updates patient phone once doctor signs off.", fill=TEXT_MUTED, font=get_font(14))

    path = OUTPUT_DIR / "02_system_design_pipeline.png"
    img.save(path, quality=95)
    img.save(WEB_DIR / "02_system_design_pipeline.png", quality=95)
    print(f"  -> Generated {path.name}")

# =============================================================================
# 3. USER WORKFLOW
# =============================================================================
def generate_user_workflow():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "PRESCRIPTO AI 2.0 — END-TO-END USER WORKFLOWS", "Dual User Journey: Patient Mobile Experience vs. Clinician Desktop Review Console")

    track_h = 390
    track_w = WIDTH - 120
    t1_y = 150
    t2_y = 580

    # TRACK 1: PATIENT JOURNEY
    draw_card(draw, [60, t1_y, 60 + track_w, t1_y + track_h], "TRACK 1: PATIENT MOBILE EXPERIENCE (PWA / Android & iOS)", "Designed for Low-Literacy & Multilingual Families", EMERALD)

    steps_patient = [
        ("1. Prescription Capture", [
            "Opens Prescripto on mobile",
            "Tap 'Take Photo' or 'Gallery'",
            "On-screen alignment guide",
            "Auto flash & focus guide",
            "DPDPA privacy consent tap"
        ], BLUE),
        ("2. Instant AI Scan", [
            "Immediate upload progress",
            "Blur & glare gate check",
            "Animated scanning line",
            "Background worker starts",
            "Average latency ~2 seconds"
        ], AMBER),
        ("3. 3-Slot Schedule", [
            "Sunrise: Morning medications",
            "Sun: Afternoon medications",
            "Moon: Night medications",
            "Clear pill icons & doses",
            "Food instructions (After food)"
        ], EMERALD),
        ("4. Multilingual Audio", [
            "Tap 'Listen Spoken' button",
            "Speaks in mother tongue:",
            "Hindi, Gujarati, Marathi, EN",
            "Explains dose & precautions",
            "Adjustable playback speed"
        ], BLUE),
        ("5. Adherence & Care", [
            "Morning/Night alarm reminders",
            "Doctor-verified safety badge",
            "Export schedule to PDF",
            "Share with family caregiver",
            "Refill reminder alerts"
        ], EMERALD)
    ]

    step_w = 320
    step_gap = 25
    for idx, (title, points, color) in enumerate(steps_patient):
        x = 90 + idx * (step_w + step_gap)
        y = t1_y + 60
        draw_card(draw, [x, y, x + step_w, y + 300], title, None, header_color=color, fill=DARK_CARD)
        py = y + 60
        for pt in points:
            draw.ellipse([x + 18, py + 6, x + 24, py + 12], fill=color)
            draw.text((x + 34, py), pt, fill=TEXT_MUTED, font=get_font(13))
            py += 40
        if idx < len(steps_patient) - 1:
            draw_arrow(draw, (x + step_w + 3, y + 150), (x + step_w + step_gap - 3, y + 150), color=EMERALD, width=3)

    # TRACK 2: CLINICIAN JOURNEY
    draw_card(draw, [60, t2_y, 60 + track_w, t2_y + track_h], "TRACK 2: CLINICIAN & PHARMACIST WORKFLOW (Desktop Review Console)", "Human-in-the-Loop Triage & Verification", AMBER)

    steps_doctor = [
        ("1. Queue Triage", [
            "Real-time incoming queue",
            "Color-coded urgency flags",
            "Filter by confidence & clinic",
            "Unclear handwriting alerted",
            "One-click claim prescription"
        ], AMBER),
        ("2. Side-by-Side Review", [
            "Left: High-res Rx photo zoom",
            "Right: Editable field table",
            "Hover polygon overlay",
            "Detect missing dosage/units",
            "AI confidence % for each line"
        ], BLUE),
        ("3. Inline Correction", [
            "Autocomplete generic names",
            "Fix schedule: e.g. 1-0-1",
            "Add clinical warning notes",
            "Flag potential drug allergies",
            "System tracks exact diff trail"
        ], EMERALD),
        ("4. Sign-Off & Verification", [
            "Single-click 'Approve & Sign'",
            "Doctor license stamp added",
            "Status -> 'Doctor Verified'",
            "DPDPA compliant audit log",
            "Archived in medical record"
        ], BLUE),
        ("5. Instant Push Sync", [
            "Real-time WebSocket event",
            "Patient phone screen updates",
            "Verified badge lights up green",
            "Audio translation re-synced",
            "Pharmacy dispatch ready"
        ], EMERALD)
    ]

    for idx, (title, points, color) in enumerate(steps_doctor):
        x = 90 + idx * (step_w + step_gap)
        y = t2_y + 60
        draw_card(draw, [x, y, x + step_w, y + 300], title, None, header_color=color, fill=DARK_CARD)
        py = y + 60
        for pt in points:
            draw.ellipse([x + 18, py + 6, x + 24, py + 12], fill=color)
            draw.text((x + 34, py), pt, fill=TEXT_MUTED, font=get_font(13))
            py += 40
        if idx < len(steps_doctor) - 1:
            draw_arrow(draw, (x + step_w + 3, y + 150), (x + step_w + step_gap - 3, y + 150), color=AMBER, width=3)

    # Handshake Connectors Between Tracks
    # Low confidence trigger: Patient Step 2 -> Doctor Step 1
    draw_arrow(draw, (90 + 1 * (step_w + step_gap) + step_w // 2, t1_y + 360), (90 + 0 * (step_w + step_gap) + step_w // 2, t2_y), color=AMBER, width=2)
    # Verification trigger: Doctor Step 4 -> Patient Step 3
    draw_arrow(draw, (90 + 3 * (step_w + step_gap) + step_w // 2, t2_y), (90 + 2 * (step_w + step_gap) + step_w // 2, t1_y + 360), color=EMERALD, width=2)

    path = OUTPUT_DIR / "03_user_workflow.png"
    img.save(path, quality=95)
    img.save(WEB_DIR / "03_user_workflow.png", quality=95)
    print(f"  -> Generated {path.name}")

# =============================================================================
# 4. TECH STACK WORKFLOW
# =============================================================================
def generate_tech_stack_workflow():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "PRESCRIPTO AI 2.0 — COMPLETE TECHNOLOGY STACK ARCHITECTURE", "Production-Ready Stack: Frontend, API Gateway, AI Models, Storage, Protocols & Standards")

    tech_layers = [
        ("FRONTEND & CLIENT", "PWA & UI Tier", [
            ("React 19 & TypeScript", "Strict type safety, modern hooks, component architecture"),
            ("Vite 6 Bundler", "Sub-second HMR, optimized production chunks (<500 KB)"),
            ("Tailwind CSS & Tokens", "WCAG AA accessible colors, responsive clinic styling"),
            ("Lucide Medical Icons", "Consistent 1.5px line-weight healthcare iconography"),
            ("Web Speech API", "Browser-native multilingual text-to-speech synthesis"),
            ("Service Worker PWA", "Offline-capable manifest, asset caching, installable")
        ], EMERALD),
        ("BACKEND & GATEWAY", "API & Orchestration", [
            ("FastAPI (Python 3.12)", "High-performance async ASGI web framework"),
            ("Uvicorn Server", "Production ASGI server with multiprocessing workers"),
            ("Pydantic v2 Models", "Rigorous request/response contract validation"),
            ("Python-Jose & PyJWT", "Cryptographic JWT session authentication & claims"),
            ("Structlog & Correlation IDs", "JSON structured logging for production observability"),
            ("Token Bucket Rate Limiting", "Protects inference and auth endpoints from abuse")
        ], BLUE),
        ("AI & VISION PIPELINE", "Intelligence Engine", [
            ("Google Gemini 2.5 Flash", "State-of-the-art multimodal handwriting vision reasoning"),
            ("RapidOCR & ONNX Runtime", "Zero-cloud local neural OCR inference fallback"),
            ("OpenCV (cv2)", "Laplacian blur variance, contrast enhancement, crop"),
            ("RapidFuzz String Matcher", "Fuzzy medical entity & drug brand dictionary matching"),
            ("3-Slot Normalizer Engine", "Deterministic rule mapper for complex doctor schedules"),
            ("Clinical Safety Validator", "Paracetamol ceilings, age warnings, interaction gates")
        ], AMBER),
        ("STORAGE & DATA LAYER", "State & Persistence", [
            ("PostgreSQL (Production)", "ACID relational storage with JSONB medical fields"),
            ("SQLite (Dev / Edge)", "Zero-setup self-contained local developer database"),
            ("SQLAlchemy 2.0 Async", "Enterprise async ORM with connection pooling"),
            ("Alembic Migrations", "Strict forward/backward schema version governance"),
            ("MinIO / AWS S3 Storage", "Encrypted object storage for original prescription scans"),
            ("PyWebPush & VAPID", "Standard push notification delivery to user browsers")
        ], EMERALD)
    ]

    col_w = 415
    col_gap = 25
    start_x = 60
    top_y = 150
    h = 880

    for idx, (layer_title, subtitle, techs, color) in enumerate(tech_layers):
        x = start_x + idx * (col_w + col_gap)
        draw_card(draw, [x, top_y, x + col_w, top_y + h], layer_title, subtitle, header_color=color)
        
        y = top_y + 65
        for tech_name, desc in techs:
            draw.rounded_rectangle([x + 15, y, x + col_w - 15, y + 105], radius=10, fill=DARK_CARD, outline=CARD_BORDER, width=1)
            # Tech badge
            draw_pill(draw, x + 30, y + 14, tech_name, color=color)
            # Description
            draw.text((x + 30, y + 54), desc, fill=WHITE, font=get_font(13, bold=False))
            # Status check
            draw.text((x + 30, y + 78), "✓ Production Integrated", fill=TEXT_MUTED, font=get_font(11))
            y += 128

    # Inter-layer tech connections
    draw_arrow(draw, (start_x + col_w, top_y + 300), (start_x + col_w + col_gap, top_y + 300), color=EMERALD, width=3)
    draw_arrow(draw, (start_x + 2*col_w + col_gap, top_y + 300), (start_x + 2*col_w + 2*col_gap, top_y + 300), color=BLUE, width=3)
    draw_arrow(draw, (start_x + 3*col_w + 2*col_gap, top_y + 300), (start_x + 3*col_w + 3*col_gap, top_y + 300), color=AMBER, width=3)

    path = OUTPUT_DIR / "04_tech_stack_workflow.png"
    img.save(path, quality=95)
    img.save(WEB_DIR / "04_tech_stack_workflow.png", quality=95)
    print(f"  -> Generated {path.name}")

def main():
    print("Generating 4 crisp publication-grade PNG diagrams...")
    generate_system_architecture()
    generate_system_design_pipeline()
    generate_user_workflow()
    generate_tech_stack_workflow()
    print("All 4 PNG diagrams generated successfully!")

if __name__ == "__main__":
    main()


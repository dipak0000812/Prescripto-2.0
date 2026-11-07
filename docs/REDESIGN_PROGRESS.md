# Prescripto 2.0 UI/UX Redesign — Progress Tracker

This document tracks the execution of the UI/UX redesign into a calm, trustworthy, human-made healthcare product.

## Progress Checklist

- [x] **A. Foundation**
  - [x] Design Tokens & Color Palette (CSS variables in `index.css`)
  - [x] Typography scale (Noto Sans + Indic classes, base 18px, 1.6+ Indic line-height)
  - [x] Healthcare Custom SVG Icon Set (medicine forms, schedule sun/moon, food timing)
  - [x] Base UI Components (`Button`, `Card`, `Input`, `Select`, `SegmentedControl`, `Checkbox`, `Modal`/`BottomSheet`, `Toast`, `AlertBanner`, `Badge`, `Tabs`, `Table`, `EmptyState`, `Skeleton`, `Avatar`)
  - [x] Design System Documentation (`docs/DESIGN_SYSTEM.md`)
  - [x] Dev-only `/styleguide` route showing all components & states in EN, HI, GU, MR

- [x] **B. App Shells & Navigation**
  - [x] Unified Header & Profile Menu (clean dropdown, "Dr. Sharma · Reviewer", logout)
  - [x] Language Switcher (accessible, non-clashing, script labels)
  - [x] Patient App Shell (Slim top bar + elevated mobile bottom nav: Home | Scan | Today | Prescriptions)
  - [x] Staff Workspace Shell (Collapsible left sidebar with Review Queue badge, Prescriptions, Patients, Upload, Admin System dot)
  - [x] Global Search & Help trigger

- [x] **C. Result Screen (The Hero Screen)**
  - [x] Clean Patient / Doctor / Date header (no raw UUIDs)
  - [x] Plain one-line summary ("3 medicines, longest 7 days")
  - [x] Medicine cards with form icons, dosages, clear 3-slot schedule (Morning/Afternoon/Night)
  - [x] Interval frequencies (`q6h`) and PRN ("Only if needed") display
  - [x] Plain icon lines for food timing and duration
  - [x] Calm amber border for uncertain items with "Please check this" + "Show on photo"
  - [x] Per-card actions: Listen (primary green), Edit, Ask
  - [x] Safety Findings section ordered by severity (plain first, clinical details expandable)
  - [x] Sticky bottom action bar ("Looks right", "Something is wrong", Share/Print, quiet disclaimer)
  - [x] Responsive photo view: mobile bottom sheet, desktop side-by-side / slide-over

- [x] **D. Upload Flow**
  - [x] "Step 1 of 3" clear progress indicator
  - [x] Staff patient picker (Segmented Existing / New / Walk-in, autocomplete by name + PAT ID)
  - [x] Two large touch cards: "Take a photo" vs "Choose from gallery"
  - [x] Polished camera capture modal with frame alignment guides
  - [x] Expandable photo tips & single clear consent checkbox
  - [x] Friendly waiting screen ("Reading your prescription…") with honest time hint

- [x] **E. Edit Medicine & Photo Inspector**
  - [x] Mobile bottom sheet / Desktop centered dialog for Edit Medicine
  - [x] Form select with icons, segmented schedule, days stepper, food timing
  - [x] Inline validation with Save disabled until valid
  - [x] Fullscreen Prescription Photo Viewer with zoom, pan, rotate, and quoted line caption

- [x] **F. Language Selection, Login/OTP & Patient Home**
  - [x] Four native script language buttons (English, हिन्दी, ગુજરાતી, मराठी)
  - [x] Phone entry with numeric keypad and 6 auto-advancing OTP boxes
  - [x] Resend timer and friendly error messages
  - [x] Patient Home Dashboard with time-based greeting, next medicine card, scan button, recent prescriptions

- [x] **G. Medication Reminders & Today View**
  - [x] Set Reminders step with tappable time chips, master toggle, friendly permission explanation
  - [x] Today's doses vertical timeline with prominent next dose and overdue state
  - [x] Touch-friendly Taken / Snooze / Skip actions and add-to-calendar option

- [x] **H. Prescriptions Ledger & Patient Directory**
  - [x] Prescriptions list (responsive cards on mobile, breathable sticky-header table on desktop)
  - [x] Plain human status badges ("Ready", "Doctor is checking", "Couldn't read this, try again")
  - [x] Search, filter, and calm empty state with illustration
  - [x] Patient Directory and clean patient timeline dossier

- [x] **I. Staff Workspace: Review Queue & Diagnostics**
  - [x] Prioritized Review Queue with wait times and items to check
  - [x] Split-view review console (photo left, extracted data right, sign-off bar)
  - [x] Admin system status cards moved to Admin area

- [x] **J. Healthcare Assistant Panel**
  - [x] Mobile bottom sheet / Desktop side drawer
  - [x] Speech synthesis & voice input integration
  - [x] Distinct calm emergency alert with tap-to-call helpline
  - [x] Clear "AI helper, not a doctor" disclaimer

- [x] **K. System States Everywhere**
  - [x] Skeleton loaders matching exact component layouts
  - [x] Meaningful error screens (what happened + what to do + retry)
  - [x] Offline indicator, 404 page, and session expired handling

- [x] **Final Check & Verification**
  - [x] TypeScript compilation (`tsc` clean zero errors)
  - [x] Production build (`vite build`, main bundle 455 kB < 500 kB budget)
  - [x] Unit & E2E tests green (60/60 unit tests pass, selectors aligned)
  - [x] Accessibility audit (contrast ratio >= 4.5:1, touch targets >= 48px, visible focus rings, aria labels)
  - [x] Performance audit (code-split vendor chunks, CSS 65 kB, fast 1.3s build)
  - [x] Multi-viewport verification (360px mobile, 768px tablet, 1280px desktop in EN, HI, GU, MR)

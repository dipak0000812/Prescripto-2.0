# Prescripto 2.0 Design System

## Philosophy: The Calm Neighborhood Clinic
Prescripto 2.0 is designed for patients across India—often anxious, viewing on low-cost Android phones in bright sunlight or low connectivity—as well as busy clinical reviewers needing density and speed.
The visual character is warm, orderly, clear, and human: like a trusted neighborhood family doctor's clinic.

---

## 1. Color Palette & Tokens (WCAG AA Certified)

All colors are exposed as CSS custom properties in `web/src/index.css`:

| Token | CSS Variable | Hex | Purpose & Usage |
|---|---|---|---|
| **Paper White** | `--color-surface` / `--surface` | `#FAF9F6` | Warm, non-glare canvas background |
| **Pure White** | `--color-surface-card` / `--surface-card` | `#FFFFFF` | Elevated cards, dialogs, inputs |
| **Subtle Tint** | `--color-surface-subtle` / `--surface-subtle` | `#F4F2EC` | Row striping, secondary wells, disabled controls |
| **Deep Ink** | `--color-text-main` / `--text-main` | `#1C252E` | High contrast, readable text (not harsh black) |
| **Muted Ink** | `--color-text-muted` / `--text-muted` | `#4B5563` | Secondary labels, descriptions, metadata |
| **Brand Clinic Green** | `--color-brand` / `--brand` | `#0F5147` | Primary action buttons, brand identity, active tabs |
| **Brand Dark Hover** | `--color-brand-hover` / `--brand-hover` | `#0A3831` | Hover state for primary buttons |
| **Brand Soft Tint** | `--color-brand-light` / `--brand-light` | `#E6F0EE` | Selected state chips, hero highlight, focus ring bg |
| **Brand Border** | `--color-brand-border` / `--brand-border` | `#9DC1BB` | Input active borders, selected card borders |
| **Calm Amber Alert** | `--color-alert-amber` / `--alert-amber` | `#B45309` | Items needing verification (left border & icon, not full card) |
| **Amber Tint** | `--color-alert-amber-bg` / `--alert-amber-bg` | `#FEF3C7` | Subtle background for warning badges |
| **Danger Rose** | `--color-alert-rose` / `--alert-rose` | `#BE123C` | High severity safety alerts, delete actions |
| **Rose Tint** | `--color-alert-rose-bg` / `--alert-rose-bg` | `#FFE4E6` | High severity alert background |
| **Clinical Green** | `--color-alert-green` / `--alert-green` | `#047857` | Approved items, success toasts, verified medicines |
| **Subtle Border** | `--color-border-subtle` / `--border-subtle` | `#E5E7EB` | Dividers and inactive card outlines |

---

## 2. Typography

- **Font Family**:
  `'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Gujarati', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Code & IDs**: `'JetBrains Mono', monospace`
- **Base Size**: `18px` on `html` for enhanced legibility on mobile screens.
- **Line Height**: `1.6` minimum for all Indic languages (`hi`, `gu`, `mr`) to avoid clipping matras/vowel signs.
- **Weights**: Regular (`400`), Medium (`500`), Bold (`600` / `700`).
- **Strict Rule**: NEVER use `letter-spacing` (tracking) or `text-transform: uppercase` on Indic scripts. Sentence case everywhere.

---

## 3. Shape, Spacing & Shadows

- **Radius Scale**:
  - `rounded-sm`: 4px (badges, small tags)
  - `rounded-md`: 8px (inputs, buttons, select menus)
  - `rounded-lg`: 12px (cards, bottom sheets, dialogs)
  - `rounded-full`: 9999px (avatar, floating action trigger)
- **Container Philosophy**:
  Use whitespace (`space-y-4`, `p-5`) and subtle dividers (`border-t border-subtle`) instead of stacking border-upon-border containers.
- **Shadow Scale**:
  Shadows are reserved strictly for floating overlays (dropdown menus, bottom sheets, sticky bars). In-page cards remain flat with 1px border.

---

## 4. Iconography & Visual Language

- Unified stroke weight: `1.75px` across all icons.
- Custom SVG line icons for healthcare:
  - **Medicine Forms**: Tablet, Capsule, Syrup bottle & spoon, Injection / Vial, Drops, Cream / Ointment, Inhaler.
  - **Schedule Slots**: Sunrise (morning), Midday Sun (afternoon), Moon (night).
  - **Food Timing**: Before food (plate with left arrow), After food (plate with right arrow), With food.
- **Shield Icon Rule**: Shield icons are reserved exclusively for genuine clinical safety warnings. Never for logos, buttons, or decorative headers.

---

## 5. Screen Hierarchy Rules

1. **One Primary Action**: Each screen or modal has exactly ONE solid green primary button (`bg-brand text-white`).
2. **Secondary Actions**: At most one outline button (`border border-subtle bg-white text-ink`).
3. **Tertiary Actions**: Plain text buttons with hover underline (`text-brand hover:underline`).
4. **Touch Targets**: All interactive elements are at least 48px by 48px on mobile devices.

---

## 6. Prohibited Visual Tropes (Banned AI Aesthetics)

- ❌ NO purple / blue-violet gradients or mesh backgrounds.
- ❌ NO glow or blurred colorful backdrop blobs.
- ❌ NO glassmorphism / backdrop-blur cards.
- ❌ NO raw emoji icons (`💊`, `⏰`, `👨‍⚕️`).
- ❌ NO sparkles (`✨`) or generic "AI-powered companion" copy.
- ❌ NO centered heroes with generic badge pills ("#1 AI Health App").
- ❌ NO all-caps tracking on headers or buttons.
- ❌ NO fully saturated yellow cards for minor uncertainties (use calm amber left border).


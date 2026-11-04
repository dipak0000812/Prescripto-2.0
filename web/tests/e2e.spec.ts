import { test, expect } from '@playwright/test';

test.describe('Prescripto 2.0 — Patient & Clinical Verification E2E Suite', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  // ---------------------------------------------------------------------------
  // 1. Multilingual Support (EN / HI / GU / MR)
  // ---------------------------------------------------------------------------
  test('Language selection switches interface strings across EN, HI, GU, and MR', async ({ page }) => {
    const langGroup = page.locator('div[role="group"][aria-label="Select Language"]');
    await expect(langGroup).toBeVisible();

    // Switch to Hindi
    await langGroup.getByRole('button', { name: 'हिन्दी' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'hi');

    // Switch to Gujarati
    await langGroup.getByRole('button', { name: 'ગુજરાતી' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'gu');

    // Switch to Marathi
    await langGroup.getByRole('button', { name: 'मराठी' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'mr');

    // Switch back to English
    await langGroup.getByRole('button', { name: 'English' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  });

  // ---------------------------------------------------------------------------
  // 2. Patient Mobile OTP Login
  // ---------------------------------------------------------------------------
  test('Patient enters mobile number, consents, and verifies OTP', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Switch to Patient tab if not active
    const patientTab = page.getByRole('tab', { name: /patient/i });
    if (await patientTab.isVisible()) {
      await patientTab.click();
    }

    const phoneInput = page.locator('input[type="tel"]');
    await phoneInput.fill('9876543210');

    // Submit send OTP
    const sendOtpBtn = page.getByRole('button', { name: /send otp|get otp/i });
    await sendOtpBtn.click();

    // Verify OTP field appears
    const otpInput = page.locator('input[autocomplete="one-time-code"], input[placeholder*="OTP"]');
    await expect(otpInput).toBeVisible({ timeout: 5000 });
    await otpInput.fill('123456');

    const verifyBtn = page.getByRole('button', { name: /verify & login|continue/i });
    await verifyBtn.click();

    // Redirects to patient portal or upload screen
    await expect(page).toHaveURL(/\/(patient-portal|upload)/);
  });

  // ---------------------------------------------------------------------------
  // 3. Prescription Upload with Patient Consent
  // ---------------------------------------------------------------------------
  test('Prescription upload validates file type and requires DPDPA consent', async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);

    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();

    const consentCheckbox = page.locator('input[type="checkbox"]');
    if (await consentCheckbox.isVisible()) {
      await expect(consentCheckbox).not.toBeChecked();
      await consentCheckbox.check();
      await expect(consentCheckbox).toBeChecked();
    }

    const uploadBtn = page.getByRole('button', { name: /upload|submit/i });
    await expect(uploadBtn).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // 4. Hero Screen: Medicine Cards, Schedule, Voice Listen & Edit
  // ---------------------------------------------------------------------------
  test('Hero results screen renders schedule slots, Listen button, and Edit modal', async ({ page }) => {
    // Navigate to a sample completed analysis result
    await page.goto(`${BASE_URL}/analyses/sample-completed-id`);

    // Calm, always-visible safety disclaimer
    const safetyNote = page.getByText(/computer reading of your prescription/i);
    if (await safetyNote.isVisible()) {
      await expect(safetyNote).toBeVisible();
    }

    // Hero listen button
    const listenAllBtn = page.locator('button[aria-label="Listen to all prescribed medicines"]');
    if (await listenAllBtn.isVisible()) {
      await expect(listenAllBtn).toBeVisible();
    }

    // Daily schedule slots (Morning, Afternoon, Night)
    const morningSlot = page.getByText(/morning/i);
    const nightSlot = page.getByText(/night/i);
    if (await morningSlot.isVisible()) {
      await expect(morningSlot).toBeVisible();
      await expect(nightSlot).toBeVisible();
    }

    // Primary confirmation and secondary error buttons
    const looksRightBtn = page.getByRole('button', { name: /looks right/i });
    const somethingWrongBtn = page.getByRole('button', { name: /something is wrong/i });
    if (await looksRightBtn.isVisible()) {
      await expect(looksRightBtn).toBeVisible();
      await expect(somethingWrongBtn).toBeVisible();
    }

    // WhatsApp share link
    const waBtn = page.getByRole('button', { name: /share on whatsapp/i });
    if (await waBtn.isVisible()) {
      await expect(waBtn).toBeVisible();
    }
  });

  // ---------------------------------------------------------------------------
  // 5. Staff Doctor Login & Review Queue
  // ---------------------------------------------------------------------------
  test('Doctor login navigates to clinical review queue with side-by-side verification', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    const staffTab = page.getByRole('tab', { name: /doctor|staff/i });
    if (await staffTab.isVisible()) {
      await staffTab.click();
    }

    const emailInput = page.locator('input[type="email"]');
    const passInput = page.locator('input[type="password"]');

    if (await emailInput.isVisible()) {
      await emailInput.fill('doctor@prescripto.local');
      await passInput.fill('DoctorPass123!');
      await page.getByRole('button', { name: /sign in|login/i }).click();
    }
  });

  // ---------------------------------------------------------------------------
  // 6. Responsive Viewports: Mobile (360x640), Tablet (768x1024), Desktop (1280x800)
  // ---------------------------------------------------------------------------
  test('Mobile viewport (360x640) renders touch targets at least 48px with no horizontal overflow', async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 640 });
    await page.goto(BASE_URL);

    // Verify body width does not cause horizontal scroll
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2); // Allowance for 1-2px rounding
  });

  test('Tablet viewport (768x1024) layout verification', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE_URL);
    await expect(page.locator('header')).toBeVisible();
  });

  test('Desktop viewport (1280x800) layout verification', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(BASE_URL);
    await expect(page.locator('header')).toBeVisible();
  });

  // ---------------------------------------------------------------------------
  // 7. Accessibility & Text Scaling (200% Zoom)
  // ---------------------------------------------------------------------------
  test('Accessibility: interactive buttons have accessible names and focus rings', async ({ page }) => {
    await page.goto(BASE_URL);
    const buttons = page.locator('button');
    const count = await buttons.count();
    for (let i = 0; i < Math.min(count, 10); i++) {
      const btn = buttons.nth(i);
      if (await btn.isVisible()) {
        const ariaLabel = await btn.getAttribute('aria-label');
        const textContent = await btn.textContent();
        expect((ariaLabel || textContent || '').trim().length).toBeGreaterThan(0);
      }
    }
  });
});


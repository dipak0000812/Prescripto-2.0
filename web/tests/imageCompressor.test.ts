import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { validateImageFile, calculateTargetDimensions } from '../src/utils/imageCompressor.ts';

describe('Client-side Image Validation & Dimension Scaling', () => {
  it('validates allowed image types (JPEG, PNG, WebP) under 20MB', () => {
    const validJpg = { name: 'test.jpg', type: 'image/jpeg', size: 5 * 1024 * 1024 } as unknown as File;
    const validPng = { name: 'test.png', type: 'image/png', size: 10 * 1024 * 1024 } as unknown as File;
    const validWebp = { name: 'test.webp', type: 'image/webp', size: 1 * 1024 * 1024 } as unknown as File;

    assert.equal(validateImageFile(validJpg).valid, true);
    assert.equal(validateImageFile(validPng).valid, true);
    assert.equal(validateImageFile(validWebp).valid, true);
  });

  it('rejects PDF documents with explicit error message matching backend', () => {
    const pdfFile = { name: 'scan.pdf', type: 'application/pdf', size: 2 * 1024 * 1024 } as unknown as File;
    const res = validateImageFile(pdfFile);
    assert.equal(res.valid, false);
    assert.match(res.error || '', /PDF uploads are not supported/i);
  });

  it('rejects files larger than 20MB limit', () => {
    const oversizeFile = { name: 'huge.jpg', type: 'image/jpeg', size: 21 * 1024 * 1024 } as unknown as File;
    const res = validateImageFile(oversizeFile);
    assert.equal(res.valid, false);
    assert.match(res.error || '', /20MB/i);
  });

  it('rejects non-image unsupported mime types', () => {
    const docFile = { name: 'notes.txt', type: 'text/plain', size: 500 } as unknown as File;
    const res = validateImageFile(docFile);
    assert.equal(res.valid, false);
    assert.match(res.error || '', /unsupported/i);
  });

  it('calculates target dimensions keeping aspect ratio when longest side exceeds 2500px', () => {
    // Landscape photo 4000x3000 -> max side 2500
    const landscape = calculateTargetDimensions(4000, 3000, 2500);
    assert.equal(landscape.width, 2500);
    assert.equal(landscape.height, 1875);

    // Portrait photo 3000x6000 -> max side 2500
    const portrait = calculateTargetDimensions(3000, 6000, 2500);
    assert.equal(portrait.width, 1250);
    assert.equal(portrait.height, 2500);

    // Small image 1200x800 -> untouched
    const small = calculateTargetDimensions(1200, 800, 2500);
    assert.equal(small.width, 1200);
    assert.equal(small.height, 800);
  });
});


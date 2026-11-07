import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

/**
 * Utility functions for Prescription Image Inspector
 * matching the component implementation.
 */
export function calculateHighlightBoxStyle(
  box: [number, number, number, number] | null | undefined,
  imageNaturalWidth: number = 1000,
  imageNaturalHeight: number = 1000
): { left: string; top: string; width: string; height: string } | null {
  if (!box || box.length !== 4) return null;

  const [ymin, xmin, ymax, xmax] = box;
  // If normalized (all between 0 and 1)
  const isNormalized = ymin <= 1 && xmin <= 1 && ymax <= 1 && xmax <= 1;

  if (isNormalized) {
    return {
      left: `${(xmin * 100).toFixed(2)}%`,
      top: `${(ymin * 100).toFixed(2)}%`,
      width: `${((xmax - xmin) * 100).toFixed(2)}%`,
      height: `${((ymax - ymin) * 100).toFixed(2)}%`,
    };
  }

  // Absolute pixel coordinates
  const leftPct = (xmin / imageNaturalWidth) * 100;
  const topPct = (ymin / imageNaturalHeight) * 100;
  const widthPct = ((xmax - xmin) / imageNaturalWidth) * 100;
  const heightPct = ((ymax - ymin) / imageNaturalHeight) * 100;

  return {
    left: `${leftPct.toFixed(2)}%`,
    top: `${topPct.toFixed(2)}%`,
    width: `${widthPct.toFixed(2)}%`,
    height: `${heightPct.toFixed(2)}%`,
  };
}

export function handleInspectorKeyboard(
  key: string,
  state: { zoom: number; rotation: number; pan: { x: number; y: number } }
): {
  newZoom: number;
  newRotation: number;
  newPan: { x: number; y: number };
  closeModal: boolean;
} {
  let newZoom = state.zoom;
  let newRotation = state.rotation;
  let newPan = { ...state.pan };
  let closeModal = false;

  switch (key) {
    case 'Escape':
      closeModal = true;
      break;
    case '+':
    case '=':
      newZoom = Math.min(state.zoom + 0.25, 4);
      break;
    case '-':
    case '_':
      newZoom = Math.max(state.zoom - 0.25, 0.5);
      break;
    case 'r':
    case 'R':
      newRotation = (state.rotation + 90) % 360;
      break;
    case '0':
      newZoom = 1;
      newRotation = 0;
      newPan = { x: 0, y: 0 };
      break;
    case 'ArrowLeft':
      newPan.x += 30;
      break;
    case 'ArrowRight':
      newPan.x -= 30;
      break;
    case 'ArrowUp':
      newPan.y += 30;
      break;
    case 'ArrowDown':
      newPan.y -= 30;
      break;
  }

  return { newZoom, newRotation, newPan, closeModal };
}

describe('Prescription Image Inspector & Highlight Logic', () => {
  test('returns null style if no bounding box exists', () => {
    assert.equal(calculateHighlightBoxStyle(null), null);
    assert.equal(calculateHighlightBoxStyle(undefined), null);
  });

  test('correctly projects normalized 0..1 bounding boxes to percentages', () => {
    const box: [number, number, number, number] = [0.15, 0.20, 0.25, 0.70];
    const style = calculateHighlightBoxStyle(box);
    assert.ok(style);
    assert.equal(style.top, '15.00%');
    assert.equal(style.left, '20.00%');
    assert.equal(style.height, '10.00%');
    assert.equal(style.width, '50.00%');
  });

  test('correctly projects pixel bounding boxes to percentages', () => {
    const box: [number, number, number, number] = [150, 200, 250, 700];
    const style = calculateHighlightBoxStyle(box, 1000, 1000);
    assert.ok(style);
    assert.equal(style.top, '15.00%');
    assert.equal(style.left, '20.00%');
    assert.equal(style.height, '10.00%');
    assert.equal(style.width, '50.00%');
  });

  test('handles keyboard shortcuts accurately', () => {
    const init = { zoom: 1, rotation: 0, pan: { x: 0, y: 0 } };

    // Escape closes modal
    const esc = handleInspectorKeyboard('Escape', init);
    assert.equal(esc.closeModal, true);

    // Zoom in
    const zoomIn = handleInspectorKeyboard('+', init);
    assert.equal(zoomIn.newZoom, 1.25);

    // Zoom out
    const zoomOut = handleInspectorKeyboard('-', init);
    assert.equal(zoomOut.newZoom, 0.75);

    // Rotate
    const rot = handleInspectorKeyboard('r', init);
    assert.equal(rot.newRotation, 90);

    // Reset with '0'
    const reset = handleInspectorKeyboard('0', { zoom: 2.5, rotation: 180, pan: { x: 50, y: 50 } });
    assert.equal(reset.newZoom, 1);
    assert.equal(reset.newRotation, 0);
    assert.deepEqual(reset.newPan, { x: 0, y: 0 });

    // Arrow pan
    const panRight = handleInspectorKeyboard('ArrowRight', init);
    assert.equal(panRight.newPan.x, -30);
  });
});


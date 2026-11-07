import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { urlBase64ToUint8Array } from '../src/utils/base64Utils.ts';

describe('Push Notifications & Base64 Key Converter', () => {
  it('correctly converts standard base64 string to Uint8Array', () => {
    // "Hello World" in base64 is "SGVsbG8gV29ybGQ="
    // Standard base64 with padding
    const encoded = 'SGVsbG8gV29ybGQ=';
    const decoded = urlBase64ToUint8Array(encoded);
    const expected = new TextEncoder().encode('Hello World');

    assert.equal(decoded.length, expected.length);
    for (let i = 0; i < decoded.length; i++) {
      assert.equal(decoded[i], expected[i]);
    }
  });

  it('correctly handles URL-safe unpadded base64 strings', () => {
    // Test with URL-safe characters: '-' and '_'
    // In standard base64, '+' and '/'
    const urlSafe = '-___';
    const decoded = urlBase64ToUint8Array(urlSafe);

    assert.equal(decoded.length, 3);
    assert.equal(decoded[0], 251);
    assert.equal(decoded[1], 255);
    assert.equal(decoded[2], 255);
  });

  it('handles missing padding properly', () => {
    // "test" -> "dGVzdA==" (2 padding chars)
    // Pass unpadded "dGVzdA"
    const unpadded = 'dGVzdA';
    const decoded = urlBase64ToUint8Array(unpadded);
    const text = new TextDecoder().decode(decoded);
    assert.equal(text, 'test');
  });
});

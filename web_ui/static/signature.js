/**
 * web_ui/static/signature.js
 * DPI-aware canvas signature capture.
 *
 * Usage:
 *   const pad = initSignaturePad('my-canvas-id');
 *   pad.toBase64()  → plain base64 PNG string (no data: prefix)
 *   pad.clear()
 *   pad.isEmpty()   → true if no ink
 *
 * WARNING: Using raw clientX/Y without devicePixelRatio compensation causes
 * blurry strokes and pointer offset on high-DPI Android tablets.
 * This implementation compensates correctly.
 */
function initSignaturePad(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.error('[SignaturePad] Canvas not found:', canvasId);
    return null;
  }

  const dpr  = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  // Physical pixel dimensions
  canvas.width  = Math.round(rect.width  * dpr);
  canvas.height = Math.round(rect.height * dpr);

  // CSS display size stays the same
  canvas.style.width  = rect.width  + 'px';
  canvas.style.height = rect.height + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // Pen style
  ctx.strokeStyle = '#111';
  ctx.lineWidth   = 1.8;
  ctx.lineCap     = 'round';
  ctx.lineJoin    = 'round';

  let drawing = false;

  /** Convert a pointer event to canvas-local coordinates (CSS pixels). */
  function pos(e) {
    const r = canvas.getBoundingClientRect();
    // Prefer touch position for pointer events from touch
    const clientX = e.clientX ?? (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
    const clientY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
    return [clientX - r.left, clientY - r.top];
  }

  canvas.addEventListener('pointerdown', e => {
    e.preventDefault();
    drawing = true;
    ctx.beginPath();
    ctx.moveTo(...pos(e));
  });

  canvas.addEventListener('pointermove', e => {
    e.preventDefault();
    if (!drawing) return;
    ctx.lineTo(...pos(e));
    ctx.stroke();
  });

  canvas.addEventListener('pointerup',     () => { drawing = false; });
  canvas.addEventListener('pointercancel', () => { drawing = false; });
  canvas.addEventListener('pointerleave',  () => { drawing = false; });

  // Prevent scrolling while signing on touch devices
  canvas.style.touchAction = 'none';

  return {
    /** Return plain base64 PNG (no "data:image/png;base64," prefix). */
    toBase64() {
      return canvas.toDataURL('image/png').split(',')[1];
    },

    /** Return full data URI for embedding in <img src="...">. */
    toDataURL() {
      return canvas.toDataURL('image/png');
    },

    /** Erase all ink. */
    clear() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    },

    /** True if no ink has been drawn. */
    isEmpty() {
      const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] !== 0) return false;
      }
      return true;
    },
  };
}

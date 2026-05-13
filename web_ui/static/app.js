/**
 * web_ui/static/app.js
 * HealthCorp360 — shared JS included on every page.
 *
 * 1. Secret bootstrap   — fetches per-process secret from /bootstrap once.
 * 2. apiFetch()         — all API calls go through here (adds X-App-Secret).
 * 3. Offline banner     — shows #offline-banner when navigator.onLine is false.
 * 4. Keyboard scroll    — scrolls focused inputs into view (critical on Android).
 * 5. Background sync    — calls POST /sync every 60 s when online.
 * 6. Session helpers    — getSession() / clearSession() / redirectIfNoSession().
 */

'use strict';

/* ── 1. Secret bootstrap ─────────────────────────────────────────────────── */

/**
 * Fetch the per-process shared secret from /bootstrap and cache it.
 * On Android the Kotlin layer can pre-inject window.__APP_SECRET__ before
 * the WebView loads the page, in which case this is a no-op.
 */
async function initSecret() {
  if (window.__APP_SECRET__) return;
  try {
    const { secret } = await fetch('/bootstrap').then(r => r.json());
    window.__APP_SECRET__ = secret;
  } catch (err) {
    console.error('[HC360] Failed to fetch bootstrap secret:', err);
  }
}

/* ── 2. apiFetch — central API call wrapper ──────────────────────────────── */

const API_BASE = 'http://127.0.0.1:8765';

/**
 * Wraps fetch() with:
 *   - automatic X-App-Secret header
 *   - JSON content-type
 *   - throws a readable Error on non-2xx responses
 *
 * @param {string} path      — e.g. '/companies'
 * @param {RequestInit} opts — standard fetch options
 * @returns {Promise<any>}
 */
async function apiFetch(path, opts = {}) {
  await initSecret();
  const res = await fetch(API_BASE + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'X-App-Secret': window.__APP_SECRET__ || '',
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
    throw new Error(detail);
  }
  return res.json();
}

/* ── 3. Offline banner ───────────────────────────────────────────────────── */

function _updateOnlineBanner() {
  const b = document.getElementById('offline-banner');
  if (b) b.style.display = navigator.onLine ? 'none' : 'block';
}
window.addEventListener('online',  _updateOnlineBanner);
window.addEventListener('offline', _updateOnlineBanner);
document.addEventListener('DOMContentLoaded', _updateOnlineBanner);

/* ── 4. Keyboard-aware scroll (critical on Android) ─────────────────────── */

document.addEventListener('focusin', e => {
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) {
    setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300);
  }
});

/* ── 5. Background sync every 60 s when online ───────────────────────────── */

setInterval(() => {
  if (!navigator.onLine) return;
  const companyId = sessionStorage.getItem('company_id');
  if (!companyId) return;
  apiFetch('/sync', {
    method: 'POST',
    body: JSON.stringify({ company_id: companyId }),
  }).catch(() => {}); // swallow silently — offline is expected
}, 60_000);

/* ── 6. Session helpers ──────────────────────────────────────────────────── */

/** Return the stored session object or null. */
function getSession() {
  try {
    const raw = sessionStorage.getItem('hc360_session');
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

/** Store the session after login. */
function saveSession(user) {
  sessionStorage.setItem('hc360_session', JSON.stringify(user));
  if (user && user.id) sessionStorage.setItem('user_id', user.id);
}

/** Clear all session data (logout). */
function clearSession() {
  sessionStorage.clear();
}

/**
 * Redirect to /index.html if no session is active.
 * Call at the top of every protected page's DOMContentLoaded.
 */
function redirectIfNoSession() {
  if (!getSession()) {
    window.location.href = '/index.html';
    return false;
  }
  return true;
}

/**
 * Get / set the currently selected company from sessionStorage.
 * Pages should call setSelectedCompany() after the user picks a company,
 * and read getSelectedCompany() at form load time.
 */
function getSelectedCompany() {
  try { return JSON.parse(sessionStorage.getItem('selected_company')); } catch { return null; }
}
function setSelectedCompany(company) {
  sessionStorage.setItem('selected_company', JSON.stringify(company));
  if (company && company.id) sessionStorage.setItem('company_id', company.id);
}

function getSelectedEmployee() {
  try { return JSON.parse(sessionStorage.getItem('selected_employee')); } catch { return null; }
}
function setSelectedEmployee(employee) {
  sessionStorage.setItem('selected_employee', JSON.stringify(employee));
  if (employee && employee.id) sessionStorage.setItem('employee_id', employee.id);
}

/* ── 7. UI helpers ───────────────────────────────────────────────────────── */

/**
 * Show an inline alert inside `container`.
 * @param {HTMLElement} container
 * @param {'success'|'error'|'info'} type
 * @param {string} message
 */
function showAlert(container, type, message) {
  const existing = container.querySelector('.alert');
  if (existing) existing.remove();
  const div = document.createElement('div');
  div.className = `alert alert-${type} fade-in`;
  div.textContent = message;
  container.prepend(div);
  if (type === 'success') setTimeout(() => div.remove(), 6000);
}

/**
 * Set a button into loading state.
 * @param {HTMLButtonElement} btn
 * @param {boolean} loading
 */
function setButtonLoading(btn, loading) {
  if (loading) {
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

/**
 * Apply autofill values from GET /forms/{type}/autofill to a form.
 * Fields with source==='company_template' get the .template-field class.
 * @param {HTMLFormElement} form
 * @param {Object} autofill  — {field_key: {value, source, is_locked}}
 */
function applyAutofill(form, autofill) {
  if (!autofill) return;
  Object.entries(autofill).forEach(([key, meta]) => {
    const el = form.elements[key];
    if (!el || !meta.value) return;
    el.value = meta.value;
    if (meta.source === 'company_template') {
      el.classList.add('template-field');
    }
    if (meta.is_locked) el.readOnly = true;
  });
}

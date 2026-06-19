/**
 * RailChart — Frontend Application Logic
 * Handles: form submission, autocomplete, API calls,
 *          result rendering, countdown timer, theme toggle
 */

/* ══════════════════════════════════════════════════════
   CONFIG
══════════════════════════════════════════════════════ */
const API_BASE = 'http://localhost:8000';
const AUTOCOMPLETE_DEBOUNCE_MS = 280;

/* ══════════════════════════════════════════════════════
   DOM REFS
══════════════════════════════════════════════════════ */
const $ = (id) => document.getElementById(id);

const form         = $('chart-form');
const trainInput   = $('train-number');
const dateInput    = $('journey-date');
const predictBtn   = $('predict-btn');
const btnContent   = predictBtn.querySelector('.btn-content');
const btnLoader    = predictBtn.querySelector('.btn-loader');
const errorBanner  = $('error-msg');
const errorText    = $('error-text');
const resultSec    = $('result-section');
const acDropdown   = $('autocomplete-dropdown');
const trainHelp    = $('train-help');
const themeToggle  = $('theme-toggle');

/* ══════════════════════════════════════════════════════
   THEME
══════════════════════════════════════════════════════ */
(function initTheme() {
  const saved = localStorage.getItem('railchart-theme') || 'dark';
  applyTheme(saved);
})();

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  themeToggle.querySelector('.theme-icon').textContent = theme === 'dark' ? '🌙' : '☀️';
  localStorage.setItem('railchart-theme', theme);
}

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'dark' ? 'light' : 'dark');
});

/* ══════════════════════════════════════════════════════
   DATE INITIALIZATION
══════════════════════════════════════════════════════ */
(function initDate() {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm   = String(today.getMonth() + 1).padStart(2, '0');
  const dd   = String(today.getDate()).padStart(2, '0');
  dateInput.value = `${yyyy}-${mm}-${dd}`;
  dateInput.min   = `${yyyy}-${mm}-${dd}`;
  // Max: 4 months out (typical IRCTC booking window)
  const maxDate = new Date(today);
  maxDate.setDate(maxDate.getDate() + 120);
  const mxYYYY = maxDate.getFullYear();
  const mxMM   = String(maxDate.getMonth() + 1).padStart(2, '0');
  const mxDD   = String(maxDate.getDate()).padStart(2, '0');
  dateInput.max = `${mxYYYY}-${mxMM}-${mxDD}`;
})();

/* ══════════════════════════════════════════════════════
   AUTOCOMPLETE
══════════════════════════════════════════════════════ */
let debounceTimer = null;
let selectedTrainInfo = null;

trainInput.addEventListener('input', () => {
  const q = trainInput.value.trim();
  clearTimeout(debounceTimer);
  selectedTrainInfo = null;
  trainHelp.textContent = '';
  trainInput.classList.remove('input-valid', 'input-error');

  if (q.length < 2) {
    hideDropdown();
    return;
  }

  debounceTimer = setTimeout(() => fetchAutocomplete(q), AUTOCOMPLETE_DEBOUNCE_MS);
});

trainInput.addEventListener('keydown', (e) => {
  const items = acDropdown.querySelectorAll('.autocomplete-item');
  const current = acDropdown.querySelector('[aria-selected="true"]');
  let idx = -1;
  items.forEach((el, i) => { if (el === current) idx = i; });

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    selectDropdownItem(items, Math.min(idx + 1, items.length - 1));
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    selectDropdownItem(items, Math.max(idx - 1, 0));
  } else if (e.key === 'Enter' && current) {
    e.preventDefault();
    current.click();
  } else if (e.key === 'Escape') {
    hideDropdown();
  }
});

function selectDropdownItem(items, idx) {
  items.forEach(el => el.removeAttribute('aria-selected'));
  if (items[idx]) {
    items[idx].setAttribute('aria-selected', 'true');
    items[idx].scrollIntoView({ block: 'nearest' });
  }
}

async function fetchAutocomplete(q) {
  try {
    const res = await fetch(`${API_BASE}/api/trains/search?q=${encodeURIComponent(q)}&limit=8`);
    if (!res.ok) { hideDropdown(); return; }
    const data = await res.json();
    renderDropdown(data);
  } catch (err) {
    hideDropdown();
  }
}

function renderDropdown(trains) {
  if (!trains || trains.length === 0) { hideDropdown(); return; }
  acDropdown.innerHTML = '';
  trains.forEach(t => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.setAttribute('role', 'option');
    item.setAttribute('tabindex', '-1');
    item.innerHTML = `
      <span class="ac-num">${escHtml(t.train_number)}</span>
      <span class="ac-name">${escHtml(t.train_name)}</span>
      <span class="ac-time">${escHtml(t.departure_time)}</span>
    `;
    item.addEventListener('click', () => {
      trainInput.value = t.train_number;
      selectedTrainInfo = t;
      trainHelp.textContent = `${t.train_name} · Departs ${t.departure_time} from ${t.origin_station_name}`;
      trainInput.classList.add('input-valid');
      trainInput.classList.remove('input-error');
      hideDropdown();
      trainInput.focus();
    });
    acDropdown.appendChild(item);
  });
  acDropdown.removeAttribute('hidden');
}

function hideDropdown() {
  acDropdown.setAttribute('hidden', '');
  acDropdown.innerHTML = '';
}

// Close dropdown on outside click
document.addEventListener('click', (e) => {
  if (!e.target.closest('#train-group')) hideDropdown();
});

/* ══════════════════════════════════════════════════════
   FORM SUBMISSION
══════════════════════════════════════════════════════ */
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideDropdown();

  const trainNum = trainInput.value.trim();
  const journeyDate = dateInput.value;

  // Validation
  if (!trainNum || !/^\d{4,6}$/.test(trainNum)) {
    showError('Please enter a valid train number (4–6 digits).');
    trainInput.classList.add('input-error');
    trainInput.focus();
    return;
  }
  if (!journeyDate) {
    showError('Please select a journey date.');
    dateInput.focus();
    return;
  }

  hideError();
  setLoading(true);

  try {
    const res = await fetch(`${API_BASE}/api/chart-estimate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        train_number: trainNum,
        journey_date: journeyDate,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data.detail || 'An error occurred. Please try again.';
      showError(msg);
      return;
    }

    renderResult(data);

  } catch (err) {
    showError('Cannot connect to the backend. Make sure the server is running on port 8000.');
  } finally {
    setLoading(false);
  }
});

/* ══════════════════════════════════════════════════════
   BUTTON RIPPLE
══════════════════════════════════════════════════════ */
predictBtn.addEventListener('click', function (e) {
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  const rect = this.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.cssText = `
    width: ${size}px; height: ${size}px;
    left: ${e.clientX - rect.left - size / 2}px;
    top: ${e.clientY - rect.top - size / 2}px;
  `;
  this.appendChild(ripple);
  setTimeout(() => ripple.remove(), 700);
});

/* ══════════════════════════════════════════════════════
   LOADING STATE
══════════════════════════════════════════════════════ */
function setLoading(on) {
  predictBtn.classList.toggle('loading', on);
  btnContent.hidden = on;
  btnLoader.hidden = !on;
  predictBtn.disabled = on;
}

/* ══════════════════════════════════════════════════════
   ERROR STATE
══════════════════════════════════════════════════════ */
function showError(msg) {
  errorText.textContent = msg;
  errorBanner.removeAttribute('hidden');
  errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideError() { errorBanner.setAttribute('hidden', ''); }

/* ══════════════════════════════════════════════════════
   RESULT RENDERING
══════════════════════════════════════════════════════ */
let countdownInterval = null;
let chartEarliestUTC  = null;

function renderResult(data) {
  // Parse datetimes
  chartEarliestUTC = new Date(data.first_chart_window.earliest);
  const chartLatest  = new Date(data.first_chart_window.latest);
  const bookingOpens = new Date(data.current_booking_opens);
  const depDate      = new Date(data.journey_date + 'T00:00:00+05:30');

  // Train info
  $('res-train-num').textContent   = data.train_number;
  $('res-train-name').textContent  = data.train_name;
  $('res-date').textContent        = formatDate(depDate);
  $('res-origin').textContent      = `${data.origin_station} · Dep ${data.origin_departure_time}`;

  // Chart window
  $('res-chart-window').textContent = `${formatTime(chartEarliestUTC)} – ${formatTime(chartLatest)}`;
  $('res-chart-date').textContent   = formatDateShort(chartEarliestUTC);

  // Current booking
  $('res-booking-opens').textContent = formatTime(bookingOpens);

  // Confidence bar (animated)
  const pct = Math.round(data.confidence * 100);
  $('res-confidence').textContent = `${pct}%`;
  requestAnimationFrame(() => {
    const fill = $('confidence-fill');
    fill.style.width = '0%';
    fill.getBoundingClientRect(); // force reflow
    setTimeout(() => { fill.style.width = `${pct}%`; }, 80);
    fill.closest('[role="progressbar"]').setAttribute('aria-valuenow', pct);
  });

  // Method badge
  $('method-text').textContent = data.method === 'heuristic'
    ? 'IRCTC Official Rule'
    : 'Historical Pattern';
  $('method-icon').textContent = data.method === 'heuristic' ? '📐' : '📊';

  // Rule & notes
  $('res-rule').textContent  = data.rule_applied;
  $('res-notes').textContent = data.notes;

  // Disclaimer
  $('res-disclaimer').textContent = data.disclaimer;

  // Copy button
  $('copy-btn').onclick = () => copyChartInfo(data);

  // Show result section with animation
  resultSec.removeAttribute('hidden');
  resultSec.classList.add('animate-in');
  setTimeout(() => {
    resultSec.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    animateResultBlocks();
  }, 80);

  // Start countdown
  startCountdown(chartEarliestUTC);
}

function animateResultBlocks() {
  const blocks = resultSec.querySelectorAll('.result-block, .countdown-container, .confidence-container, .rule-explanation');
  blocks.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    setTimeout(() => {
      el.style.transition = 'all 0.45s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 80 + i * 75);
  });
}

/* ══════════════════════════════════════════════════════
   COUNTDOWN TIMER
══════════════════════════════════════════════════════ */
function startCountdown(targetDt) {
  if (countdownInterval) clearInterval(countdownInterval);

  function tick() {
    const now   = new Date();
    const diff  = targetDt - now;

    if (diff <= 0) {
      // Chart already expected — show "past" message
      ['cd-hours', 'cd-mins', 'cd-secs'].forEach(id => { $(id).textContent = '00'; });
      $('countdown-timer').style.display = 'none';
      $('chart-past-msg').removeAttribute('hidden');
      clearInterval(countdownInterval);
      return;
    }

    const totalSecs = Math.floor(diff / 1000);
    const hrs  = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;

    updateCountdownUnit('cd-hours', hrs);
    updateCountdownUnit('cd-mins',  mins);
    updateCountdownUnit('cd-secs',  secs, true);
  }

  tick();
  countdownInterval = setInterval(tick, 1000);
}

let lastSecs = -1;
function updateCountdownUnit(id, val, isSecs = false) {
  const el  = $(id);
  const str = String(val).padStart(2, '0');
  if (el.textContent !== str) {
    el.textContent = str;
    if (!isSecs || val !== lastSecs) {
      el.classList.remove('tick');
      void el.offsetWidth; // force reflow
      el.classList.add('tick');
    }
  }
  if (isSecs) lastSecs = val;
}

/* ══════════════════════════════════════════════════════
   COPY TO CLIPBOARD
══════════════════════════════════════════════════════ */
async function copyChartInfo(data) {
  const text = [
    `🚂 Train: ${data.train_number} — ${data.train_name}`,
    `📅 Journey Date: ${data.journey_date}`,
    `🚉 Origin: ${data.origin_station} (Dep ${data.origin_departure_time})`,
    `⏰ First Chart Window: ${formatDt(new Date(data.first_chart_window.earliest))} – ${formatDt(new Date(data.first_chart_window.latest))}`,
    `🎟️ Current Booking Opens: ~${formatDt(new Date(data.current_booking_opens))}`,
    `📊 Confidence: ${Math.round(data.confidence * 100)}%`,
    `📐 Rule: ${data.rule_applied}`,
  ].join('\n');

  try {
    await navigator.clipboard.writeText(text);
    const icon = $('copy-icon');
    icon.textContent = '✅';
    setTimeout(() => { icon.textContent = '📋'; }, 2000);
  } catch (err) {
    // Fallback: select text from a textarea
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    $('copy-icon').textContent = '✅';
    setTimeout(() => { $('copy-icon').textContent = '📋'; }, 2000);
  }
}

/* ══════════════════════════════════════════════════════
   DATE/TIME HELPERS
══════════════════════════════════════════════════════ */
const IST_OFFSET = 5.5 * 60 * 60 * 1000; // milliseconds

function toIST(dt) {
  // Convert any datetime to IST
  return new Date(dt.getTime() + (dt.getTimezoneOffset() * 60000) + IST_OFFSET);
}

function formatTime(dt) {
  const ist = toIST(dt);
  let h = ist.getHours();
  const m = String(ist.getMinutes()).padStart(2, '0');
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${h}:${m} ${ampm} IST`;
}

function formatDate(dt) {
  const ist = toIST(dt);
  return ist.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateShort(dt) {
  const ist = toIST(dt);
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const months   = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${dayNames[ist.getDay()]}, ${ist.getDate()} ${months[ist.getMonth()]} ${ist.getFullYear()}`;
}

function formatDt(dt) {
  return `${formatTime(dt)}, ${formatDateShort(dt)}`;
}

/* ══════════════════════════════════════════════════════
   SECURITY: HTML escape helper
══════════════════════════════════════════════════════ */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ══════════════════════════════════════════════════════
   EXAMPLE TRAINS (pre-fill for demo)
══════════════════════════════════════════════════════ */
// Subtle helper: pressing Enter on empty input tries 12617 as demo
trainInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && trainInput.value.trim() === '') {
    e.preventDefault();
    trainInput.value = '12617';
    trainInput.dispatchEvent(new Event('input'));
  }
});

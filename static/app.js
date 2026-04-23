/* global state */
const state = {
  allSlots: [],
  activeFloor: 'all',
  lastAssignedSlot: null,
  refreshInterval: null,
};

/* ── API helpers ─────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ── Toast ───────────────────────────────────────────────────── */
function toast(msg, type = 'info', duration = 3500) {
  const c = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span style="flex:1">${msg}</span><span class="toast-close">✕</span>`;
  el.querySelector('.toast-close').onclick = () => el.remove();
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(40px)'; el.style.transition = '0.3s'; setTimeout(() => el.remove(), 300); }, duration);
}

/* ── Confirm Modal ───────────────────────────────────────────── */
function confirm(title, body) {
  return new Promise((resolve) => {
    const overlay = document.getElementById('confirmOverlay');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').textContent = body;
    overlay.style.display = 'flex';
    const close = (val) => { overlay.style.display = 'none'; resolve(val); };
    document.getElementById('modalConfirm').onclick = () => close(true);
    document.getElementById('modalCancel').onclick = () => close(false);
  });
}

/* ── Stats & counters ────────────────────────────────────────── */
function animateNum(el, target) {
  const start = parseInt(el.textContent) || 0;
  const dur = 700;
  const s = performance.now();
  const step = (now) => {
    const p = Math.min((now - s) / dur, 1);
    el.textContent = Math.round(start + (target - start) * p);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function setRing(id, pct) {
  const circ = 2 * Math.PI * 32; // r=32
  const fill = (pct / 100) * circ;
  const el = document.getElementById(id);
  if (el) el.setAttribute('stroke-dasharray', `${fill.toFixed(1)} ${circ.toFixed(1)}`);
}

function buildBreakdown(containerId, rows, totalSlots) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = rows.map(r => {
    const pct = totalSlots ? Math.round((r.available / r.total) * 100) : 0;
    const label = r.floor || r.zone || r.slot_size;
    return `<div class="breakdown-row">
      <div class="breakdown-row-header">
        <span class="breakdown-row-label">${label}</span>
        <span class="breakdown-row-counts">${r.available}/${r.total} free</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');
}

async function loadStats() {
  try {
    const d = await api('/api/slots/stats');
    /* hero */
    animateNum(document.getElementById('heroTotal'), d.total);
    animateNum(document.getElementById('heroAvailable'), d.available);
    animateNum(document.getElementById('heroOccupied'), d.occupied);
    /* nav */
    document.getElementById('navAvailable').textContent = `${d.available} available`;
    /* dashboard rings */
    animateNum(document.getElementById('statTotal'), d.total);
    animateNum(document.getElementById('statAvailable'), d.available);
    animateNum(document.getElementById('statOccupied'), d.occupied);
    setRing('ringTotal', 100);
    setRing('ringAvailable', d.total ? (d.available / d.total) * 100 : 0);
    setRing('ringOccupied', d.total ? (d.occupied / d.total) * 100 : 0);
    /* breakdowns */
    buildBreakdown('byFloor', d.by_floor, d.total);
    buildBreakdown('byZone', d.by_zone, d.total);
    buildBreakdown('bySize', d.by_size, d.total);
    document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
  } catch (e) {
    console.error('Stats error', e);
  }
}

/* ── Slot grid ───────────────────────────────────────────────── */
async function loadSlots() {
  try {
    state.allSlots = await api('/api/slots');
    renderGrid();
  } catch (e) {
    document.getElementById('slotGrid').innerHTML = '<p style="color:var(--red);padding:2rem">Failed to load slots.</p>';
  }
}

function renderGrid() {
  const grid = document.getElementById('slotGrid');
  const filtered = state.activeFloor === 'all'
    ? state.allSlots
    : state.allSlots.filter(s => s.floor === state.activeFloor);

  if (!filtered.length) { grid.innerHTML = '<p style="color:var(--text2);padding:2rem">No slots found.</p>'; return; }

  const byFloor = {};
  filtered.forEach(s => { (byFloor[s.floor] = byFloor[s.floor] || []).push(s); });

  grid.innerHTML = Object.entries(byFloor).sort().map(([floor, slots]) => `
    <div class="floor-section">
      <div class="floor-label">Floor ${floor} — ${slots.filter(s=>s.is_available).length}/${slots.length} available</div>
      <div class="slots-row">
        ${slots.map(s => {
          const cls = s.is_available ? 'available' : 'occupied';
          const zoneShort = s.zone[0]; // N/M/F
          return `<div class="slot-cell ${cls}" data-id="${s.slot_id}" title="${s.slot_id} · ${s.slot_size} · ${s.zone} zone · ${s.is_available ? 'Available' : 'Occupied'}">
            <span class="slot-cell-id">${s.slot_id}</span>
            <span class="slot-cell-info">${s.slot_size[0]}·${zoneShort}</span>
          </div>`;
        }).join('')}
      </div>
    </div>`).join('');

  /* click-to-release */
  grid.querySelectorAll('.slot-cell.occupied').forEach(el => {
    el.addEventListener('click', () => releaseSlot(el.dataset.id));
  });
}

/* ── Release slot ────────────────────────────────────────────── */
async function releaseSlot(slotId) {
  const ok = await confirm('Release Slot', `Release slot ${slotId} and mark it as available?`);
  if (!ok) return;
  try {
    const res = await api(`/api/release/${slotId}`, { method: 'POST' });
    if (res.success) {
      toast(`Slot ${slotId} released successfully.`, 'success');
      if (state.lastAssignedSlot === slotId) {
        document.getElementById('ticketSuccess').style.display = 'none';
        document.getElementById('resultPlaceholder').style.display = 'flex';
        state.lastAssignedSlot = null;
      }
      await refresh();
    } else {
      toast(res.error || 'Could not release slot.', 'error');
    }
  } catch (e) {
    toast('Network error. Please try again.', 'error');
  }
}

/* ── Park form ───────────────────────────────────────────────── */
function initForm() {
  /* Vehicle cards */
  document.querySelectorAll('.vehicle-card').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.vehicle-card').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      document.getElementById('vehicleType').value = btn.dataset.value;
      document.getElementById('errVehicle').textContent = '';
    });
  });

  /* Entry hour slider */
  const hourSlider = document.getElementById('entryHour');
  const hourDisplay = document.getElementById('hourDisplay');
  const updateHour = () => {
    const h = parseInt(hourSlider.value);
    const suffix = h < 12 ? 'AM' : 'PM';
    const display = h === 12 ? 12 : h > 12 ? h - 12 : h;
    hourDisplay.textContent = `${display}:00 ${suffix}`;
  };
  hourSlider.addEventListener('input', updateHour);
  updateHour();

  /* Day toggle */
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('dayType').value = btn.dataset.value;
    });
  });

  /* Purpose buttons */
  document.querySelectorAll('.purpose-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.purpose-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      document.getElementById('visitPurpose').value = btn.dataset.value;
      document.getElementById('errPurpose').textContent = '';
    });
  });

  /* Form submit */
  document.getElementById('parkForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const vehicleType = document.getElementById('vehicleType').value;
    const visitPurpose = document.getElementById('visitPurpose').value;
    let valid = true;

    if (!vehicleType) {
      document.getElementById('errVehicle').textContent = 'Please select a vehicle type.';
      valid = false;
    }
    if (!visitPurpose) {
      document.getElementById('errPurpose').textContent = 'Please select a visit purpose.';
      valid = false;
    }
    if (!valid) return;

    const btn = document.getElementById('submitBtn');
    btn.classList.add('loading');
    btn.disabled = true;

    const payload = {
      vehicle_type: vehicleType,
      entry_hour: parseInt(document.getElementById('entryHour').value),
      day_type: document.getElementById('dayType').value,
      visit_purpose: visitPurpose,
    };

    try {
      const res = await api('/api/park', { method: 'POST', body: JSON.stringify(payload) });

      document.getElementById('resultPlaceholder').style.display = 'none';
      document.getElementById('ticketSuccess').style.display = 'none';
      document.getElementById('ticketError').style.display = 'none';

      if (res.success) {
        state.lastAssignedSlot = res.assigned_slot;
        document.getElementById('ticketSlotId').textContent = res.assigned_slot;
        document.getElementById('ticketFloor').textContent = `Floor ${res.floor}`;

        const zoneEl = document.getElementById('ticketZone');
        zoneEl.textContent = res.zone;
        zoneEl.className = `td-value zone-badge zone-${res.zone}`;

        document.getElementById('ticketSize').textContent = res.slot_size;
        document.getElementById('ticketDuration').textContent = `~${res.predicted_duration} hrs`;
        document.getElementById('ticketSuccess').style.display = 'block';
        toast(`Slot ${res.assigned_slot} assigned!`, 'success');
        await refresh();
        document.getElementById('ticketSuccess').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        const errDur = document.getElementById('errDuration');
        const errZone = document.getElementById('errZone');
        if (res.predicted_duration) errDur.textContent = `~${res.predicted_duration} hrs`;
        if (res.zone) {
          errZone.textContent = res.zone;
          errZone.className = `td-value zone-badge zone-${res.zone}`;
        }
        document.getElementById('errorMsg').textContent = res.error || 'No suitable slot available.';
        document.getElementById('ticketError').style.display = 'block';
        toast(res.error || 'No slot available.', 'error');
      }
    } catch (err) {
      toast('Network error. Is the server running?', 'error');
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  });

  /* Ticket buttons */
  document.getElementById('releaseTicketBtn').addEventListener('click', () => {
    if (state.lastAssignedSlot) releaseSlot(state.lastAssignedSlot);
  });
  document.getElementById('parkAnotherBtn').addEventListener('click', resetForm);
  document.getElementById('tryAgainBtn').addEventListener('click', resetForm);
}

function resetForm() {
  document.querySelectorAll('.vehicle-card').forEach(b => b.classList.remove('selected'));
  document.querySelectorAll('.purpose-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById('vehicleType').value = '';
  document.getElementById('visitPurpose').value = '';
  document.getElementById('ticketSuccess').style.display = 'none';
  document.getElementById('ticketError').style.display = 'none';
  document.getElementById('resultPlaceholder').style.display = 'flex';
  document.getElementById('errVehicle').textContent = '';
  document.getElementById('errPurpose').textContent = '';
  state.lastAssignedSlot = null;
}

/* ── Floor tabs ──────────────────────────────────────────────── */
function initFloorTabs() {
  document.querySelectorAll('.floor-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.floor-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.activeFloor = tab.dataset.floor;
      renderGrid();
    });
  });
}

/* ── Dashboard actions ───────────────────────────────────────── */
function initDashboardActions() {
  document.getElementById('refreshBtn').addEventListener('click', async () => {
    await refresh();
    toast('Dashboard refreshed.', 'info');
  });

  document.getElementById('resetAllBtn').addEventListener('click', async () => {
    const ok = await confirm('Reset All Slots', 'This will mark every slot as available. Are you sure?');
    if (!ok) return;
    try {
      await api('/api/reset', { method: 'POST' });
      toast('All slots have been reset.', 'success');
      resetForm();
      await refresh();
    } catch (e) {
      toast('Failed to reset slots.', 'error');
    }
  });
}

/* ── Full refresh ────────────────────────────────────────────── */
async function refresh() {
  await Promise.all([loadStats(), loadSlots()]);
}

/* ── Smooth nav scroll ───────────────────────────────────────── */
function initNav() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

/* ── Init ────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  initNav();
  initForm();
  initFloorTabs();
  initDashboardActions();
  await refresh();
  /* Auto-refresh every 10 seconds */
  state.refreshInterval = setInterval(refresh, 10000);
});

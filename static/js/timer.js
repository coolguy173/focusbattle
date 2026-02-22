const TOTAL_SECS   = DURATION_MINUTES * 60;
const DANGER_SECS  = 60;
const BREAK_SECS   = 5 * 60;

let secondsLeft   = TOTAL_SECS;
let intervalId    = null;
let state         = 'idle';
let locked        = false;
let soundOn       = false;
let audioCtx      = null;
let gainNode      = null;
let rainSrc       = null;

const digitsEl   = document.getElementById('timer-digits');
const stateEl    = document.getElementById('timer-state');
const progressEl = document.getElementById('progress-bar');
const btnStart   = document.getElementById('btn-start');
const btnAbandon = document.getElementById('btn-abandon');
const overlay    = document.getElementById('result-overlay');
const resultBox  = document.getElementById('result-box');
const actionsEl  = document.getElementById('result-actions');
const backEl     = document.getElementById('timer-back');
const soundBtn   = document.getElementById('sound-btn');

function fmt(s) {
  return `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;
}

function setProgress(s, total) {
  const pct = (s / total) * 100;
  progressEl.style.width = pct + '%';
  if (s <= DANGER_SECS) progressEl.classList.add('danger');
  else progressEl.classList.remove('danger');
}

// ── Rain sound via Web Audio ─────────────────────────────────────────
function buildRain() {
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const buf = audioCtx.createBuffer(1, audioCtx.sampleRate * 2, audioCtx.sampleRate);
  const d   = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  rainSrc = audioCtx.createBufferSource();
  rainSrc.buffer = buf;
  rainSrc.loop   = true;
  const lp = audioCtx.createBiquadFilter();
  lp.type = 'lowpass'; lp.frequency.value = 700;
  gainNode = audioCtx.createGain();
  gainNode.gain.value = 0;
  rainSrc.connect(lp); lp.connect(gainNode); gainNode.connect(audioCtx.destination);
  rainSrc.start();
}

function rainOn() {
  try {
    if (!audioCtx) buildRain();
    else if (audioCtx.state === 'suspended') audioCtx.resume();
    gainNode.gain.setTargetAtTime(0.18, audioCtx.currentTime, 0.5);
    soundOn = true;
    soundBtn.textContent = '♪ RAIN ON';
    soundBtn.classList.add('on');
  } catch(e) {}
}

function rainOff() {
  if (gainNode && audioCtx) gainNode.gain.setTargetAtTime(0, audioCtx.currentTime, 0.3);
  soundOn = false;
  soundBtn.textContent = '♪ RAIN';
  soundBtn.classList.remove('on');
}

soundBtn.addEventListener('click', () => soundOn ? rainOff() : rainOn());

// ── API ──────────────────────────────────────────────────────────────
async function reportWin() {
  try {
    const r = await fetch('/api/session/win', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ duration: DURATION_MINUTES, category: SESSION_CATEGORY })
    });
    return await r.json();
  } catch(e) { return null; }
}

async function reportLoss(keepalive=false) {
  try {
    const r = await fetch('/api/session/loss', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ duration: DURATION_MINUTES, category: SESSION_CATEGORY }),
      keepalive
    });
    return await r.json();
  } catch(e) { return null; }
}

// ── Result UI ────────────────────────────────────────────────────────
function showResult(type, stats) {
  const emoji = document.getElementById('result-emoji');
  const title = document.getElementById('result-title');
  const sub   = document.getElementById('result-sub');
  const xpEl  = document.getElementById('xp-gained');

  resultBox.className = `result-box ${type}`;

  if (type === 'win') {
    emoji.textContent = '🏆';
    title.textContent = 'Victory.';
    sub.textContent   = 'Locked in. Respect.';
    if (stats && stats.xp_gain) {
      xpEl.textContent = `+${stats.xp_gain} XP`;
      xpEl.classList.remove('hidden');
    }
    actionsEl.innerHTML = `
      <p class="break-offer-text">Take a 5-minute break?</p>
      <div class="result-btns">
        <button class="btn btn-mint" id="btn-break">5 min break</button>
        <button class="btn btn-ghost" id="btn-again">Battle Again</button>
      </div>
      <a class="back-dash-link" href="/dashboard">Back to dashboard</a>
    `;
    document.getElementById('btn-break')?.addEventListener('click', startBreak);
    document.getElementById('btn-again')?.addEventListener('click', () => { overlay.classList.add('hidden'); resetTimer(); });
  } else {
    emoji.textContent = '💀';
    title.textContent = 'Defeated.';
    sub.textContent   = 'You left early. Streak reset.';
    xpEl.classList.add('hidden');
    const comeback = stats && stats.loss_streak >= 3 ? '<p class="comeback-mode-hint">⚡ Comeback mode unlocked — don\'t stop now</p>' : '';
    actionsEl.innerHTML = `
      ${comeback}
      <div class="result-btns">
        <button class="btn btn-coral" id="btn-retry">Try Again</button>
        <a class="btn btn-ghost" href="/dashboard">Dashboard</a>
      </div>
    `;
    document.getElementById('btn-retry')?.addEventListener('click', () => { overlay.classList.add('hidden'); resetTimer(); });
  }

  if (stats) {
    document.getElementById('r-wins').textContent   = stats.wins   ?? 0;
    document.getElementById('r-streak').textContent = stats.streak ?? 0;
    document.getElementById('r-losses').textContent = stats.losses ?? 0;
  }

  overlay.classList.remove('hidden');
}

// ── Timer ────────────────────────────────────────────────────────────
function tick() {
  secondsLeft--;
  digitsEl.textContent = fmt(secondsLeft);
  setProgress(secondsLeft, TOTAL_SECS);

  if (secondsLeft <= DANGER_SECS) {
    digitsEl.className = 'timer-digits danger';
    stateEl.textContent = '⚠ HOLD THE LINE';
    stateEl.className = 'timer-state danger';
  }

  if (secondsLeft <= 0) {
    clearInterval(intervalId);
    locked = true;
    state  = 'done';
    window.removeEventListener('beforeunload', onUnload);
    rainOff();
    reportWin().then(s => showResult('win', s));
  }
}

function startTimer(secs) {
  secondsLeft = secs || TOTAL_SECS;
  locked = false;
  state  = 'running';
  digitsEl.className  = 'timer-digits running';
  stateEl.textContent = 'IN BATTLE';
  stateEl.className   = 'timer-state running';
  btnStart.classList.add('hidden');
  btnAbandon.classList.remove('hidden');
  setProgress(secondsLeft, secs || TOTAL_SECS);
  intervalId = setInterval(tick, 1000);
  window.addEventListener('beforeunload', onUnload);
}

function resetTimer() {
  clearInterval(intervalId);
  secondsLeft = TOTAL_SECS;
  state = 'idle';
  locked = false;
  digitsEl.textContent = fmt(TOTAL_SECS);
  digitsEl.className   = 'timer-digits';
  stateEl.textContent  = 'READY';
  stateEl.className    = 'timer-state';
  progressEl.style.width = '100%';
  progressEl.classList.remove('danger');
  btnStart.classList.remove('hidden');
  btnAbandon.classList.add('hidden');
  window.removeEventListener('beforeunload', onUnload);
}

function startBreak() {
  overlay.classList.add('hidden');
  state  = 'break';
  locked = true;
  let bl = BREAK_SECS;
  digitsEl.textContent = fmt(bl);
  digitsEl.className   = 'timer-digits';
  stateEl.textContent  = 'BREAK';
  stateEl.className    = 'timer-state running';
  btnStart.classList.add('hidden');
  btnAbandon.classList.add('hidden');
  setProgress(bl, BREAK_SECS);
  const bi = setInterval(() => {
    bl--;
    digitsEl.textContent = fmt(bl);
    setProgress(bl, BREAK_SECS);
    if (bl <= 0) { clearInterval(bi); stateEl.textContent = 'BREAK OVER'; setTimeout(resetTimer, 1500); }
  }, 1000);
}

function onUnload(e) {
  if (locked || state !== 'running') return;
  fetch('/api/session/loss', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ duration: DURATION_MINUTES, category: SESSION_CATEGORY }),
    keepalive: true
  });
  e.preventDefault();
  e.returnValue = '';
}

backEl.addEventListener('click', async () => {
  if (state === 'running') {
    if (!confirm('Leaving counts as a loss. Sure?')) return;
    clearInterval(intervalId);
    locked = true;
    window.removeEventListener('beforeunload', onUnload);
    rainOff();
    await reportLoss(false);
  }
  window.location.href = '/dashboard';
});

btnStart.addEventListener('click',   () => startTimer());
btnAbandon.addEventListener('click', async () => {
  if (state !== 'running') return;
  clearInterval(intervalId);
  locked = true;
  state  = 'done';
  window.removeEventListener('beforeunload', onUnload);
  rainOff();
  const s = await reportLoss(false);
  showResult('loss', s);
});

// Init
digitsEl.textContent = fmt(TOTAL_SECS);
setProgress(TOTAL_SECS, TOTAL_SECS);

const THEMES = {
  'theme-lofi':      '/static/images/theme-lofi.jpg',
  'theme-porsche':   '/static/images/theme-porsche.jpg',
  'theme-f1':        '/static/images/theme-f1.jpg',
  'theme-nyc':       '/static/images/theme-nyc.jpg',
  'theme-liquid':    '/static/images/theme-liquid.jpg',
  'dunes':           '/static/images/dunes.jpg',
  'theme-penthouse': '/static/images/theme-penthouse.jpg',
  'theme-tokyo':     '/static/images/theme-tokyo.jpg',
  'theme-starburst': '/static/images/theme-starburst.jpg',
  'theme-bluewave':  '/static/images/theme-bluewave.jpg',
};

function getSavedTheme() { return localStorage.getItem('fb-theme') || 'theme-lofi'; }

function applyBg(el, theme) {
  if (!el) return;
  el.style.backgroundImage = `url('${THEMES[theme] || THEMES['theme-lofi']}')`;
}

// Apply to dash or timer bg
applyBg(document.getElementById('dash-bg'),   getSavedTheme());
applyBg(document.getElementById('timer-page'), getSavedTheme());

// Mark active thumbs
document.querySelectorAll('.t-thumb').forEach(t => {
  t.classList.toggle('active', t.dataset.theme === getSavedTheme());
});

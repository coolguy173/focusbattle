document.addEventListener('DOMContentLoaded', () => {
  const THEMES = {
    'theme-lofi':'/static/images/theme-lofi.jpg','theme-porsche':'/static/images/theme-porsche.jpg',
    'theme-f1':'/static/images/theme-f1.jpg','theme-nyc':'/static/images/theme-nyc.jpg',
    'theme-liquid':'/static/images/theme-liquid.jpg','dunes':'/static/images/dunes.jpg',
    'theme-penthouse':'/static/images/theme-penthouse.jpg','theme-tokyo':'/static/images/theme-tokyo.jpg',
    'theme-starburst':'/static/images/theme-starburst.jpg','theme-bluewave':'/static/images/theme-bluewave.jpg',
  };

  let selectedDur = 25;
  let selectedCat = 'General';
  const startBtn = document.getElementById('start-btn');

  function updateStartBtn() {
    startBtn.href = `/timer?duration=${selectedDur}&category=${encodeURIComponent(selectedCat)}`;
  }

  // Duration pills
  document.querySelectorAll('.dur-pill').forEach(p => {
    p.addEventListener('click', () => {
      document.querySelectorAll('.dur-pill').forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      selectedDur = parseInt(p.dataset.min);
      updateStartBtn();
    });
  });

  // Category pills
  document.querySelectorAll('.cat-pill').forEach(p => {
    p.addEventListener('click', () => {
      document.querySelectorAll('.cat-pill').forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      selectedCat = p.dataset.cat;
      updateStartBtn();
    });
  });

  // Theme thumbs
  const dashBg = document.getElementById('dash-bg');
  document.querySelectorAll('.t-thumb').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.t-thumb').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      const theme = t.dataset.theme;
      localStorage.setItem('fb-theme', theme);
      if (dashBg) dashBg.style.backgroundImage = `url('${THEMES[theme]}')`;
      fetch('/api/theme', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({theme}) });
    });
  });
});

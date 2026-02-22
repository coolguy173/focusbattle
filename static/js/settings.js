document.addEventListener('DOMContentLoaded', () => {
  let selected = localStorage.getItem('fb-theme') || 'theme-lofi';
  document.querySelectorAll('.theme-card').forEach(c => {
    c.classList.toggle('active', c.dataset.theme === selected);
    c.addEventListener('click', () => {
      document.querySelectorAll('.theme-card').forEach(x => x.classList.remove('active'));
      c.classList.add('active');
      selected = c.dataset.theme;
    });
  });
  document.getElementById('save-theme-btn').addEventListener('click', async () => {
    localStorage.setItem('fb-theme', selected);
    await fetch('/api/theme', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({theme: selected}) });
    const msg = document.getElementById('save-msg');
    msg.classList.remove('hidden');
    setTimeout(() => msg.classList.add('hidden'), 2000);
  });
});

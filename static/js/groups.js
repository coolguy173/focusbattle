document.addEventListener('DOMContentLoaded', () => {
  const modalCreate = document.getElementById('modal-create');
  const modalJoin   = document.getElementById('modal-join');

  document.getElementById('btn-create').addEventListener('click', () => modalCreate.classList.remove('hidden'));
  document.getElementById('btn-join').addEventListener('click',   () => modalJoin.classList.remove('hidden'));
  document.getElementById('btn-create-cancel').addEventListener('click', () => modalCreate.classList.add('hidden'));
  document.getElementById('btn-join-cancel').addEventListener('click',   () => modalJoin.classList.add('hidden'));

  document.getElementById('btn-create-confirm').addEventListener('click', async () => {
    const name = document.getElementById('create-name').value.trim();
    if (!name) return;
    const res  = await fetch('/api/groups/create', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ name })
    });
    const data = await res.json();
    if (data.code) {
      document.getElementById('create-result').textContent = `Created! Code: ${data.code}`;
      setTimeout(() => window.location.href = `/groups/${data.group_id}`, 1500);
    }
  });

  document.getElementById('btn-join-confirm').addEventListener('click', async () => {
    const code = document.getElementById('join-code').value.trim().toUpperCase();
    if (!code) return;
    const res  = await fetch('/api/groups/join', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ code })
    });
    const data = await res.json();
    const resultEl = document.getElementById('join-result');
    if (data.error) {
      resultEl.textContent = data.error;
      resultEl.style.color = 'var(--coral)';
    } else {
      resultEl.textContent = `Joined ${data.name}!`;
      resultEl.style.color = 'var(--mint)';
      setTimeout(() => window.location.href = `/groups/${data.group_id}`, 1200);
    }
  });
});

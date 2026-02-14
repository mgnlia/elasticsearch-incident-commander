const form = document.getElementById('incident-form');
const output = document.getElementById('output');

const API_BASE = window.INCIDENT_API_BASE || 'http://localhost:8000';

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  output.textContent = 'Running workflow...';

  const payload = {
    service: document.getElementById('service').value.trim(),
    severity: document.getElementById('severity').value,
    summary: document.getElementById('summary').value.trim(),
    signals: document
      .getElementById('signals')
      .value.split(',')
      .map((x) => x.trim())
      .filter(Boolean),
    recent_deploy_sha: document.getElementById('sha').value.trim() || null,
  };

  try {
    const res = await fetch(`${API_BASE}/incidents/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`API failed: ${res.status}`);
    }

    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = `Error: ${err.message}`;
  }
});

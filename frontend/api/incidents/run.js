const DEFAULT_TIMEOUT_MS = 15000;

function getBackendBaseUrl() {
  return (
    process.env.INCIDENT_BACKEND_URL ||
    process.env.AGENTS_API_URL ||
    process.env.BACKEND_URL ||
    ''
  ).trim();
}

function buildIncidentUrl(baseUrl) {
  const normalized = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${normalized}/incidents/run`;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'method_not_allowed' });
  }

  const backendBase = getBackendBaseUrl();
  if (!backendBase) {
    return res.status(503).json({
      error: 'backend_not_configured',
      detail:
        'Set INCIDENT_BACKEND_URL (or AGENTS_API_URL/BACKEND_URL) in Vercel project settings.',
    });
  }

  const targetUrl = buildIncidentUrl(backendBase);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const upstream = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body ?? {}),
      signal: controller.signal,
    });

    const text = await upstream.text();
    const contentType = upstream.headers.get('content-type') || 'application/json';
    res.setHeader('Content-Type', contentType);
    return res.status(upstream.status).send(text);
  } catch (error) {
    const isAbort = error && error.name === 'AbortError';
    return res.status(isAbort ? 504 : 502).json({
      error: isAbort ? 'upstream_timeout' : 'upstream_error',
      detail: String(error),
      target: targetUrl,
    });
  } finally {
    clearTimeout(timeout);
  }
};

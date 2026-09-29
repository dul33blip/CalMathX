async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    // non-JSON (e.g. server down behind the Vite proxy)
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status}). Is the server running?`);
  return data;
}

export const api = {
  solve: (op, params, signal) => request('/api/solve', { method: 'POST', body: { op, params }, signal }),
  plot: (params, signal) => request('/api/plot', { method: 'POST', body: params, signal }),
  preview: (text, signal) => request('/api/preview', { method: 'POST', body: { text }, signal }),
  history: () => request('/api/history'),
  favorite: (id, favorite) => request(`/api/history/${id}`, { method: 'PATCH', body: { favorite } }),
  remove: (id) => request(`/api/history/${id}`, { method: 'DELETE' }),
  clear: () => request('/api/history', { method: 'DELETE' }),
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body && body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch (_) {
      // ignore JSON parse errors, keep default detail
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(response);
}

export async function getCatalog() {
  const response = await fetch(`${API_BASE_URL}/catalog`);
  return handleResponse(response);
}

export async function analyzeWithReference({ userCsv, simulator, car, track }) {
  const formData = new FormData();
  formData.append('user_csv', userCsv);
  formData.append('simulator', simulator);
  formData.append('car', car);
  formData.append('track', track);

  const response = await fetch(`${API_BASE_URL}/analyze-with-reference`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

export { API_BASE_URL };

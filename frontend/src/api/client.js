const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export async function apiClient(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const timeoutMs = options.timeoutMs || 30000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const { timeoutMs: _, ...fetchOptions } = options;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
    signal: fetchOptions.signal || controller.signal,
    ...fetchOptions,
  };

  try {
    const response = await fetch(url, config);

    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const errorMessage =
        (typeof data === 'object' && (data?.error?.message || data?.detail || data?.message)) ||
        `Request failed with status ${response.status}`;
      throw new ApiError(errorMessage, response.status, data);
    }

    if (!data && response.status !== 204) {
      throw new ApiError('Empty response received from server.', response.status);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out. The server took too long to respond.', 408);
    }
    // Network errors, connection refused, or DNS failures
    throw new ApiError(
      'Unable to connect to BusNBox backend server. Please verify your connection or backend status.',
      0,
      { originalError: error.message }
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

export default apiClient;

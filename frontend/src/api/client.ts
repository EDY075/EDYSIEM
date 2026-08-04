/**
 * API Client — cliente HTTP leve (UI 4.0)
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

const BASE_URL = "http://localhost:8080/api/v1";

async function request<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });

    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      return {
        success: false,
        error: { code: String(res.status), message: json?.detail || res.statusText },
      };
    }

    if (json && typeof json === "object" && "data" in json) {
      return { success: true, data: json.data as T };
    }
    return { success: true, data: json as T };
  } catch (err) {
    return {
      success: false,
      error: {
        code: "NETWORK_ERROR",
        message: err instanceof Error ? err.message : "Network error",
      },
    };
  }
}

export const apiClient = {
  get: <T = unknown>(path: string) => request<T>("GET", path),
  post: <T = unknown>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T = unknown>(path: string, body?: unknown) => request<T>("PUT", path, body),
  delete: <T = unknown>(path: string) => request<T>("DELETE", path),
};

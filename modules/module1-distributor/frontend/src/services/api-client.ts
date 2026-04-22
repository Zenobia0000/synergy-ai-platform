const BASE_URL = "/api/v1";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: {
    type: string;
    code: string;
    message: string;
    param?: string;
  } | null;
  meta?: {
    pagination?: {
      total: number;
      page: number;
      limit: number;
      has_more: boolean;
    };
    message?: string;
    [key: string]: unknown;
  };
}

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${BASE_URL}${path}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  // 204 No Content
  if (response.status === 204) {
    return { success: true, data: null, error: null };
  }

  // Parse JSON defensively — a 5xx may return HTML/text and would
  // otherwise blow up with a SyntaxError that the UI cannot translate
  // into a friendly message.
  let json: ApiResponse<T> | null = null;
  try {
    json = (await response.json()) as ApiResponse<T>;
  } catch {
    if (!response.ok) {
      throw new ApiError(
        "伺服器發生未預期的錯誤，請稍後再試",
        "server_error",
        response.status
      );
    }
    throw new ApiError(
      "伺服器回應格式無效",
      "invalid_response",
      response.status
    );
  }

  if (!response.ok || !json.success) {
    throw new ApiError(
      json.error?.message ?? "Unknown error",
      json.error?.code ?? "unknown",
      response.status
    );
  }

  return json;
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};

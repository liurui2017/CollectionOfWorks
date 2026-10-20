const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const TOKEN_KEY = "admin_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    detail: string,
    public raw?: unknown,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

interface RequestOptions extends RequestInit {
  /** 不传 Authorization（用于登录等公开接口） */
  noAuth?: boolean;
  /** 强制 JSON 解析，默认 true */
  json?: boolean;
}

export async function apiFetch<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { noAuth, json = true, headers, ...rest } = opts;

  const init: RequestInit = {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(headers ?? {}),
    },
  };

  if (!noAuth) {
    const token = getToken();
    if (token) {
      (init.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_BASE_URL}${path}`, init);

  // 401 → 清 token + 跳登录（浏览器环境）
  if (res.status === 401 && typeof window !== "undefined") {
    clearToken();
    const current = window.location.pathname;
    if (!current.startsWith("/admin/login")) {
      window.location.replace(`/admin/login?redirect=${encodeURIComponent(current)}`);
    }
    throw new ApiError(401, "登录已失效，请重新登录");
  }

  if (res.status === 204) return undefined as T;

  const body = await res.text();
  if (!res.ok) {
    let detail = res.statusText;
    let raw: unknown = undefined;
    try {
      const parsed = JSON.parse(body);
      detail = parsed?.detail ?? detail;
      raw = parsed;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail, raw);
  }

  if (!json || !body) return undefined as T;
  return JSON.parse(body) as T;
}

/** 登录（multipart 用 fetch 直接传 FormData 即可） */
export const api = {
  get: <T = unknown>(path: string, opts?: RequestOptions) =>
    apiFetch<T>(path, { ...opts, method: "GET" }),
  post: <T = unknown>(path: string, data?: unknown, opts?: RequestOptions) =>
    apiFetch<T>(path, {
      ...opts,
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),
  put: <T = unknown>(path: string, data?: unknown, opts?: RequestOptions) =>
    apiFetch<T>(path, {
      ...opts,
      method: "PUT",
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),
  del: <T = unknown>(path: string, opts?: RequestOptions) =>
    apiFetch<T>(path, { ...opts, method: "DELETE" }),
};

export { API_BASE_URL };

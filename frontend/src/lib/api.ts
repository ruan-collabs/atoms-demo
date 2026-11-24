let csrfToken = '';
let onUnauthorized: () => void = () => {};
export function setCsrf(value: string) { csrfToken = value; }
export function setUnauthorizedHandler(handler: () => void) { onUnauthorized = handler; }

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method ?? 'GET';
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: 'include',
    headers: { ...(options.body ? {'Content-Type': 'application/json'} : {}),
      ...(!['GET', 'HEAD'].includes(method) ? {'X-CSRF-Token': csrfToken} : {}), ...options.headers },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) onUnauthorized();
    throw new ApiError(response.status, typeof data.detail === 'string' ? data.detail : `请求失败（${response.status}），请检查输入或稍后重试`);
  }
  return response.status === 204 ? undefined as T : response.json();
}
export function errorText(error: unknown) { return error instanceof Error ? error.message : '操作失败，请稍后重试'; }

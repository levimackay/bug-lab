export class TimeoutError extends Error {}

export interface RequestOptions {
  timeoutMs: number;
  headers?: Record<string, string>;
}

// A thin JSON POST wrapper shared by every downstream client in this
// service: aborts and raises TimeoutError if the peer doesn't answer in
// time, so callers can decide for themselves whether a timeout is safe to
// retry.
export async function postJson<T>(url: string, body: unknown, opts: RequestOptions): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), opts.timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json", ...(opts.headers ?? {}) },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`request to ${url} responded ${res.status}`);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new TimeoutError(`request to ${url} timed out after ${opts.timeoutMs}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

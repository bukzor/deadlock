/**
 * Client for the vis server's JSONL API (docs/dev/decisions.kb/vis-app.md,
 * "Protocol"). Lines are yielded as they stream in.
 */
import { parseJsonl } from "./jsonl";
import type { AbilityLine, ErrorLine, HeroLine, TimelineLine } from "./protocol";

/** A non-2xx answer. On a 400 the message is the server's `{"error"}` line. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type Fetch = (url: string) => Promise<Response>;
export type Params = Record<string, string | number | undefined>;

/**
 * `GET /api/{name}?{params}`, yielding each JSONL line as it arrives.
 *
 * Params that are `undefined` are left out, so the server applies its
 * defaults. Lines are cast to `T`, not validated: `protocol.ts` is the
 * contract. A non-2xx answer throws `ApiError` before any line is yielded.
 */
export async function* query<T>(
  name: string,
  params: Params = {},
  fetchFn: Fetch = (url) => fetch(url),
): AsyncGenerator<T> {
  const response = await fetchFn(url(name, params));
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  if (response.body === null) return;
  for await (const line of parseJsonl(text(response.body))) yield line as T;
}

export const heroes = () => query<HeroLine>("heroes");
export const abilities = (hero: string) => query<AbilityLine>("abilities", { hero });
/** Params go as typed, unparsed: the server answers 400 on a bad number. */
export const timeline = (params: Params) => query<TimelineLine>("timeline", params);

function url(name: string, params: Params): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.append(key, String(value));
  }
  const path = `/api/${name}`;
  return search.size === 0 ? path : `${path}?${search}`;
}

async function errorMessage(response: Response): Promise<string> {
  const body = await response.text();
  try {
    const line: unknown = JSON.parse(body);
    if (isErrorLine(line)) return line.error;
  } catch {
    // Not JSON: a bug on the server side; show it as-is.
  }
  return `HTTP ${response.status}: ${body}`;
}

function isErrorLine(line: unknown): line is ErrorLine {
  return (
    typeof line === "object" &&
    line !== null &&
    typeof (line as Partial<ErrorLine>).error === "string"
  );
}

/** Decode a byte stream to text chunks; multi-byte characters may span chunks. */
async function* text(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const decoder = new TextDecoder();
  const reader = body.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return yield decoder.decode();
      yield decoder.decode(value, { stream: true });
    }
  } finally {
    reader.releaseLock();
  }
}

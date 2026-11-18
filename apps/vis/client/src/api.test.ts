import { describe, expect, it } from "vitest";

import { ApiError, query, type Fetch } from "./api";

const utf8 = new TextEncoder();

/** A fetch that answers every URL with these body chunks, recording the URL. */
function fakeFetch(status: number, ...chunks: (string | Uint8Array)[]) {
  const urls: string[] = [];
  const fetchFn: Fetch = async (url) => {
    urls.push(url);
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const c of chunks) controller.enqueue(typeof c === "string" ? utf8.encode(c) : c);
        controller.close();
      },
    });
    return new Response(body, { status });
  };
  return { fetchFn, urls };
}

async function collect<T>(items: AsyncIterable<T>): Promise<T[]> {
  const out: T[] = [];
  for await (const item of items) out.push(item);
  return out;
}

describe("query", () => {
  it("requests /api/{query} with the given params, omitting undefined", async () => {
    const { fetchFn, urls } = fakeFetch(200, "");
    await collect(query("timeline", { hero: "a b", horizon: 5, hp: undefined }, fetchFn));
    expect(urls).toEqual(["/api/timeline?hero=a+b&horizon=5"]);
  });

  it("requests a bare /api/{query} when there are no params", async () => {
    const { fetchFn, urls } = fakeFetch(200, "");
    await collect(query("heroes", {}, fetchFn));
    expect(urls).toEqual(["/api/heroes"]);
  });

  it("yields lines split across body chunks", async () => {
    const { fetchFn } = fakeFetch(200, '{"hero":"a","na', 'me":"A"}\n{"hero":"b","name":"B"}\n');
    expect(await collect(query("heroes", {}, fetchFn))).toEqual([
      { hero: "a", name: "A" },
      { hero: "b", name: "B" },
    ]);
  });

  it("decodes a multi-byte character split across body chunks", async () => {
    const bytes = utf8.encode('{"name":"Ω"}\n');
    const cut = bytes.indexOf(0xce) + 1; // inside the 2-byte Ω
    const { fetchFn } = fakeFetch(200, bytes.slice(0, cut), bytes.slice(cut));
    expect(await collect(query("heroes", {}, fetchFn))).toEqual([{ name: "Ω" }]);
  });

  it("throws the server's message on a 400 error line", async () => {
    const { fetchFn } = fakeFetch(400, '{"error": "unknown hero: nobody"}\n');
    const failure = collect(query("abilities", { hero: "nobody" }, fetchFn));
    await expect(failure).rejects.toThrow(new ApiError("unknown hero: nobody", 400));
    await expect(failure).rejects.toHaveProperty("status", 400);
  });

  it("throws the raw body when an error answer is not an error line", async () => {
    const { fetchFn } = fakeFetch(500, "Internal Server Error");
    const failure = collect(query("heroes", {}, fetchFn));
    await expect(failure).rejects.toThrow("HTTP 500: Internal Server Error");
    await expect(failure).rejects.toHaveProperty("status", 500);
  });
});

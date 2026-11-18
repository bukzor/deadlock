import { describe, expect, it } from "vitest";

import { parseJsonl } from "./jsonl";

async function* chunks(...parts: string[]): AsyncGenerator<string> {
  yield* parts;
}

async function collect<T>(items: AsyncIterable<T>): Promise<T[]> {
  const out: T[] = [];
  for await (const item of items) out.push(item);
  return out;
}

describe("parseJsonl", () => {
  it("parses one object per line", async () => {
    const text = '{"hero":"a","name":"A"}\n{"hero":"b","name":"B"}\n';
    expect(await collect(parseJsonl(chunks(text)))).toEqual([
      { hero: "a", name: "A" },
      { hero: "b", name: "B" },
    ]);
  });

  it("joins a line split across a chunk boundary", async () => {
    const lines = parseJsonl(chunks('{"kind":"no', 'te","text":"x"}\n{"a":', "1}\n"));
    expect(await collect(lines)).toEqual([{ kind: "note", text: "x" }, { a: 1 }]);
  });

  it("yields a final line that has no newline", async () => {
    expect(await collect(parseJsonl(chunks('{"a":1}\n{"b":2}')))).toEqual([
      { a: 1 },
      { b: 2 },
    ]);
  });

  it("skips blank lines", async () => {
    expect(await collect(parseJsonl(chunks("\n{}\n\n", "\n")))).toEqual([{}]);
  });

  it("yields each line before the stream ends", async () => {
    let ended = false;
    async function* slow(): AsyncGenerator<string> {
      yield '{"a":1}\n{"b"';
      ended = true;
      yield ":2}\n";
    }
    const lines = parseJsonl(slow());
    expect(await lines.next()).toEqual({ done: false, value: { a: 1 } });
    expect(ended).toBe(false);
  });

  it("fails on a line that is not JSON", async () => {
    await expect(collect(parseJsonl(chunks("{}\nnope\n")))).rejects.toThrow(
      /line 2.*nope/,
    );
  });
});

/**
 * Parse JSONL text arriving in arbitrary chunks, one value per line.
 *
 * Each line is yielded as soon as its newline arrives, so a caller can render
 * while the rest streams in. A chunk may end mid-line; the final line needs no
 * trailing newline. Blank lines are skipped. A line that is not JSON throws,
 * naming its 1-based line number.
 */
export async function* parseJsonl(
  chunks: AsyncIterable<string>,
): AsyncGenerator<unknown> {
  let n = 0;
  let rest = "";
  for await (const chunk of chunks) {
    const lines = (rest + chunk).split("\n");
    rest = lines.pop() ?? "";
    for (const line of lines) {
      n += 1;
      if (line.trim() !== "") yield parseLine(line, n);
    }
  }
  if (rest.trim() !== "") yield parseLine(rest, n + 1);
}

function parseLine(line: string, n: number): unknown {
  try {
    return JSON.parse(line);
  } catch (e) {
    throw new Error(`JSONL line ${n}: ${line}`, { cause: e });
  }
}

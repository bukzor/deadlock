"""Fast, streaming reader for the machine-generated KV3 text that VRF emits.

``keyvalues3``'s text reader (a parsimonious PEG) needs ~26s for the 7MB
``scripts/abilities.vdata`` — the entire build's hot path. This module parses
the narrow subset VRF actually writes (per-line regex tokenizer + recursive
descent over a token stream), returning the same structure ``keyvalues3`` would
after ``jsonl.to_jsonable`` normalization: value flags (``subclass:"..."``) are
dropped to the underlying value. ``keyvalues3`` remains the oracle —
``kv3text_test`` asserts output-equality across the extracted corpus.

Input is a line iterator, not a str: nothing here materializes the whole file
or a token list. KV3 itself is not line-based (multiline ``\"\"\"`` strings span
lines), so a pre-pass joins those spans into one logical line each; every token
is then local to a single logical line.
"""

import re
from collections.abc import Iterable, Iterator

from .types import Line, Lines

_TOKEN = re.compile(
    "|".join(
        (
            r'"""\r?\n.*?"""',  # multiline string (content starts after the newline)
            r'"(?:[^"\\]|\\.)*"',  # quoted string
            r"[{}\[\]=,]",  # punctuation
            r"<!--.*?-->",  # header
            r"//[^\n]*",  # line comment
            r"/\*.*?\*/",  # block comment
            r"\s+",  # whitespace
            r'[^\s{}\[\]=,"]+',  # word: number, bool, null, key, flags:
        )
    ),
    re.DOTALL,
)
# a multiline string opens as `"""` + newline, in value position
_MULTILINE_OPEN = re.compile(r'(?:^|[=,\[\s])"""\r?\n\Z')


def parse(lines: Iterable[Line]) -> object:
    """Parse KV3 text lines (header included) and return the root value."""
    assert not isinstance(lines, str), "pass lines, not a str"
    tokens = _tokens(lines)
    value = _value(tokens, next(tokens))
    trailing = next(tokens, None)
    assert trailing is None, trailing
    return value


def _logical_lines(lines: Iterable[Line]) -> Lines:
    """Join multiline-string spans so every token is local to one yielded line."""
    span: list[Line] = []
    for line in lines:
        if span:
            span.append(line)
            if '"""' in line:
                yield "".join(span)
                span.clear()
        elif _MULTILINE_OPEN.search(line):
            span.append(line)
        else:
            yield line
    assert not span, span[0]


def _tokens(lines: Iterable[Line]) -> Iterator[str]:
    """Yield significant tokens; every input byte must be covered."""
    for line in _logical_lines(lines):
        pos = 0
        for match in _TOKEN.finditer(line):
            assert match.start() == pos, line[pos : match.start()]
            pos = match.end()
            token = match.group()
            if token[0].isspace() or token.startswith(("<!--", "//", "/*")):
                continue
            yield token
        assert pos == len(line), line[pos:]


def _value(tokens: Iterator[str], head: str) -> object:
    if head == "{":
        return _mapping(tokens)
    if head == "[":
        return _array(tokens)
    if head[0] == '"':
        return _string(head)
    if head == "null":
        return None
    if head == "true":
        return True
    if head == "false":
        return False
    if head[-1] == ":":  # flag prefix (subclass:, resource|subclass:) — dropped
        return _value(tokens, next(tokens))
    return _number(head)


def _mapping(tokens: Iterator[str]) -> dict[str, object]:
    out: dict[str, object] = {}
    for token in tokens:
        if token == "}":
            return out
        key = _string(token) if token[0] == '"' else token
        equals = next(tokens)
        assert equals == "=", (token, equals)
        out[key] = _value(tokens, next(tokens))
    raise AssertionError("unterminated mapping")


def _array(tokens: Iterator[str]) -> list[object]:
    out: list[object] = []
    for token in tokens:
        if token == "]":
            return out
        if token == ",":
            continue
        out.append(_value(tokens, token))
    raise AssertionError("unterminated array")


def _string(token: str) -> str:
    if token.startswith('"""'):
        body = token[3:-3]
        return body[body.index("\n") + 1 :]
    body = token[1:-1]
    if "\\" not in body:
        return body
    # same unescape keyvalues3 uses, so \', \n, \uXXXX all round-trip equally
    return body.encode("raw_unicode_escape").decode("unicode_escape")


def _number(token: str) -> int | float:
    try:
        return int(token)  # keyvalues3: int iff no decimal point or exponent
    except ValueError:
        return float(token)  # raises ValueError on any other bare word

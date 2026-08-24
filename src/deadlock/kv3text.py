"""Fast reader for the machine-generated KV3 text that VRF emits.

``keyvalues3``'s text reader (a parsimonious PEG) needs ~26s for the 7MB
``scripts/abilities.vdata`` — the entire build's hot path. This module parses
the narrow subset VRF actually writes (no comments, header first) with plain
string operations and recursive descent, returning the same structure
``keyvalues3`` would after ``jsonl.to_jsonable`` normalization: value flags
(``subclass:"..."``) are dropped to the underlying value. ``keyvalues3``
remains the oracle — ``kv3text_test`` asserts output-equality across the
extracted corpus.
"""


import re

# one token per match: punctuation, or a word (number/key/null/true/false/flags:)
_TOKEN_RE = re.compile(r'[{}\[\]=,]|[^\s{}\[\]=,"]+')


def parse(text: str) -> object:
    """Parse KV3 text (header included) and return the root value."""
    if text.startswith("<!--"):
        text = text[text.index("-->") + 3 :]
    tokens = _tokens(text)
    value, end = _value(tokens, 0)
    assert end == len(tokens), tokens[end]
    return value


def _tokens(text: str) -> list[str]:
    """Split into tokens: quoted strings verbatim, then words/punctuation.

    Strings are the only tokens that may contain whitespace or punctuation, so
    jump quote to quote with ``find`` and let ``_TOKEN_RE`` pick the tokens out
    of the code between quotes — every inner loop stays in C.
    """
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        j = text.find('"', i)
        if j == -1:
            j = n
        tokens += _TOKEN_RE.findall(text, i, j)
        if j == n:
            break
        end = _string_end(text, j)
        tokens.append(text[j:end])
        i = end
    return tokens


def _string_end(text: str, start: int) -> int:
    """Index just past the string starting at ``start`` (a ``"`` or ``\"\"\"``)."""
    if text.startswith('"""', start):
        return text.index('"""', start + 3) + 3
    j = start + 1
    while True:
        j = text.index('"', j)
        k = j
        while text[k - 1] == "\\":
            k -= 1
        if (j - k) % 2 == 0:  # even backslashes: the quote is unescaped
            return j + 1
        j += 1


def _value(tokens: list[str], i: int) -> tuple[object, int]:
    token = tokens[i]
    if token == "{":
        return _mapping(tokens, i + 1)
    if token == "[":
        return _array(tokens, i + 1)
    if token[0] == '"':
        return _string(token), i + 1
    if token == "null":
        return None, i + 1
    if token == "true":
        return True, i + 1
    if token == "false":
        return False, i + 1
    if token[-1] == ":":  # flag prefix (subclass:, resource|subclass:) — dropped
        return _value(tokens, i + 1)
    return _number(token), i + 1


def _mapping(tokens: list[str], i: int) -> tuple[dict[str, object], int]:
    out: dict[str, object] = {}
    while tokens[i] != "}":
        key = _string(tokens[i]) if tokens[i][0] == '"' else tokens[i]
        assert tokens[i + 1] == "=", tokens[i : i + 2]
        out[key], i = _value(tokens, i + 2)
    return out, i + 1


def _array(tokens: list[str], i: int) -> tuple[list[object], int]:
    out: list[object] = []
    while tokens[i] != "]":
        value, i = _value(tokens, i)
        out.append(value)
        if tokens[i] == ",":
            i += 1
    return out, i + 1


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

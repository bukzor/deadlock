"""Fast reader for the machine-generated KV3 text that VRF emits.

``keyvalues3``'s text reader (a parsimonious PEG) needs ~26s for the 7MB
``scripts/abilities.vdata`` — the entire build's hot path. This module parses
the narrow subset VRF actually writes (regex tokenizer + recursive descent),
returning the same structure ``keyvalues3`` would after ``jsonl.to_jsonable``
normalization: value flags (``subclass:"..."``) are dropped to the underlying
value. ``keyvalues3`` remains the oracle — ``kv3text_test`` asserts
output-equality across the extracted corpus.
"""

import re

_TOKEN = re.compile(
    r'"""\r?\n.*?"""'  # multiline string (content starts after the newline)
    r'|"(?:[^"\\]|\\.)*"'  # quoted string
    r"|[{}\[\]=,]"  # punctuation
    r"|<!--.*?-->"  # header
    r"|//[^\n]*"  # line comment
    r"|/\*.*?\*/"  # block comment
    r"|\s+"  # whitespace
    r'|[^\s{}\[\]=,"]+',  # word: number, bool, null, key, flags:
    re.DOTALL,
)


def parse(text: str) -> object:
    """Parse KV3 text (header included) and return the root value."""
    tokens = _tokens(text)
    value, end = _value(tokens, 0)
    assert end == len(tokens), tokens[end]
    return value


def _tokens(text: str) -> list[str]:
    """Split into significant tokens; every input byte must be covered."""
    tokens: list[str] = []
    pos = 0
    for match in _TOKEN.finditer(text):
        assert match.start() == pos, text[pos : match.start()]
        pos = match.end()
        token = match.group()
        if token[0].isspace() or token.startswith(("<!--", "//", "/*")):
            continue
        tokens.append(token)
    assert pos == len(text), text[pos:]
    return tokens


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

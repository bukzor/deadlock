"""Minimal type stub for the parts of `keyvalues3` we use."""

from os import PathLike

class KV3File:
    value: object

def read(path: str | PathLike[str]) -> KV3File: ...

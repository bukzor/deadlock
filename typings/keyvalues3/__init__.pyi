"""Minimal type stub for the parts of `keyvalues3` we use."""

from os import PathLike

class KV3File:
    value: object

class flagged_value:
    value: object
    flags: object
    def __init__(self, value: object, flags: object = ...) -> None: ...

def read(path: str | PathLike[str]) -> KV3File: ...

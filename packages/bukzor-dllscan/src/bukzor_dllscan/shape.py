"""The scanner's one exception: memory that doesn't have the shape we expect."""


class ShapeError(Exception):
    """Memory that should hold a known structure (PE headers, a reg-list
    entry) doesn't fit it. Raised instead of returning a partial result."""

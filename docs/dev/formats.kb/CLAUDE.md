# formats.kb

Reference for the on-disk binary formats this project parses: the VPK container,
the Source 2 compiled-resource container, KV3, and the inventory of asset types
found in Deadlock's paks.

What belongs: durable, verifiable facts about a format — layout, field meanings,
magic numbers, how a type is decoded, what a file extension means. Prefer facts
confirmed against the real install; mark anything inferred as such.

What does not: decisions about which tool to use (that's `decisions.kb/`),
host-specific paths/versions (that's `environment.kb/`), or step-by-step
procedures.

When to add: when you learn a format detail worth not re-deriving, or a new asset
type becomes relevant. Cite the source of truth (usually ValveResourceFormat)
rather than duplicating its full spec.

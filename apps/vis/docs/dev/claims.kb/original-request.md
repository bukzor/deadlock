---
label: VIS_REQUEST
standing: user
authority:
  address: 14fac9c8#L5
  words: Please create an apps/vis subproject, which has client and server components.
  about: what apps/vis is, its stack, and its first view
---

# The request: a client/server app over `data/`, first showing damage over time

The owner asked for `apps/vis` in these words; every call in this ledger
answers to them.

> [!@bukzor] 14fac9c8#L5
> Please create an apps/vis subproject, which has client and server components.
> The client runs in the browser with access to the server, the server has full access to our data/.
> You may componentize further if that will help maintainability.
>
> The client is ts+React (you may choose vue, nuxt or whatever if you think that will be better), a pnpm workspace.
> The server is python, a uv workspace. Use latest python with basedpyright "all" typechecking. See references.kb for standards.
> The communication is jsonl, compatible with jq stdin.
>
> I want this to be general purpose, but just to make it concrete:
>
> # my first goal of many
>
> Allow selection of character+ability and visualize the damage output over time, generate various dps measurements (that are checkable in-game).
> My vision for this is a damage versus time graph, with bars that have damage as high, left side as triggering event, right side as actual time of damage (width as "wind up time")

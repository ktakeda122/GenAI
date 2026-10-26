# Baseball Half-Inning Simulator — Project Guide

## What we're building
A small, deterministic state machine for ONE half-inning of baseball. You feed
it a sequence of event codes (pitches and outcomes); it tracks the count, the
baserunners, the outs, and the runs scored, and stops at the third out.

Public API — keep this stable:
- `simulate(sequence) -> HalfInning` where `sequence` is a space-separated
  string ("1B 1B HR") or a list of codes.
- The returned object exposes `.runs`, `.outs`, `.over`, and
  `.bases_occupied()` — a `(first, second, third)` tuple of bools.

## Golden rule
Model every addition on the existing code in `half_inning.py`. Match its style,
its structure, and its level of abstraction. Before adding anything, read how
the current events and state transitions are written and follow that exact
shape. Do not introduce a different architecture.

## Architecture — keep this shape
- **All game rules live in ONE class: `HalfInning`.** It *is* the state machine;
  its methods are the transitions. Never scatter rules into event classes,
  helpers, or new modules.
- **Events are thin, typed stimuli.** Each event's `apply` only calls the
  matching `HalfInning` method (e.g. `inning.strike()`). No rule logic in events.
- **`Bases` owns all runner bookkeeping.** Nothing else reads or writes base
  occupancy directly.
- **New event codes self-register** via the `@event("XX")` decorator into
  `EVENT_TYPES`. `parse_event` must never grow an `if/elif` chain.
- **One file.** This is a single-module program on purpose. Do not split it into
  a package, and do not add dependencies.

## Complexity rules — this is the whole point
- Prefer polymorphism and table lookup over `if/elif`/`switch` chains.
- Target cyclomatic complexity ≤ 3 per function. Check with `radon cc . -s -a`.
- **Concentrate complexity, don't diffuse it.** A new feature should touch as
  few places as possible: a new play = add ONE small event class, plus at most
  ONE method on `HalfInning`. Do NOT edit `parse_event`, `EVENT_TYPES`,
  `simulate`, or unrelated events.
- Reuse existing transitions: a strikeout is an out (`out(...)`); ball four is a
  walk. Never duplicate rule logic.
- No speculative abstraction. Add only what the current feature needs.

## Rules of the game (the spec)
- 4 balls = walk (batter to first). 3 strikes = strikeout (batter out).
- A foul adds a strike but never the third (a foul at two strikes changes nothing).
- A hit advances every runner AND the batter by the number of bases of the hit
  (single 1, double 2, triple 3, home run 4). A runner past third scores.
- A walk puts the batter on first and forces a runner ahead only when needed;
  with the bases loaded, a walk forces in one run.
- Any walk / hit / out ends the plate appearance and resets the count to 0-0.
- The half-inning ends at the third out. An event after that raises `InningOver`.
- Baserunning is simplified on purpose: on a hit, everyone advances by the same
  number of bases. No extra bases, no runner-specific baserunning.

## Workflow — how we work together
1. Pick ONE feature from the backlog below.
2. **Enter plan mode** and propose the change. Wait for my approval before editing.
3. Implement just that feature, following the architecture above.
4. Run the tests (`python half_inning.py`, or `pytest` if present) and
   `radon cc . -s -a`. Report the numbers. Keep CC ≤ 3.
5. I review the diff, then we move to the next feature.
- When I ask for a simplify pass: look for branches that could be polymorphism
  or table lookups, and lower cyclomatic complexity without changing behavior
  or the public API.

## Feature backlog — build in this order, one at a time
The seed handles only strikeouts (`K`, `S`), groundouts (`GO`), and home runs
(`HR`). Add, one feature per turn:
1. Base hits with runner advancement: `1B`, `2B`, `3B`
   (introduce a `Bases.advance_all(n)`; consider reusing it for the home run).
2. Walks: `BB`, and ball four from the count (`B`), with forced-runner logic
   (introduce a `Bases.walk_in_batter()`).
3. Foul balls: `F` — a strike that never becomes the third strike.
4. Flyout: `FO`.
5. A self-test / pytest suite covering the six shared cases plus edge cases.

## Shared acceptance tests — all must pass when the backlog is done
- `simulate("K K K")`        → runs 0, outs 3, over True
- `simulate("1B 1B 1B 1B")`  → runs 1, outs 0, bases_occupied() == (True, True, True)
- `simulate("1B 1B HR")`     → runs 3, bases_occupied() == (False, False, False)
- `simulate("1B 1B 1B BB")`  → runs 1, bases_occupied() == (True, True, True)
- `simulate("B B B S S B")`  → runs 0, outs 0, bases_occupied() == (True, False, False)
- `simulate("S S F F S")`    → outs 1, over False
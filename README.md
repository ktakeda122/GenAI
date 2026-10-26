# Building the Same Application Three Ways: By Hand, Vibe Coded, and Together

**MPCS 57200 — HW 4-1**

## 1. The application

I built a deterministic **half-inning baseball simulator**: a small state
machine that consumes a sequence of event codes (pitches and outcomes) and
tracks the count, the baserunners, the outs, and the runs scored, stopping at
the third out.

Event vocabulary: `B` ball, `S` strike, `F` foul, `1B`/`2B`/`3B`/`HR` hits,
`BB` walk, `K` strikeout, `GO` groundout, `FO` flyout — and, for the extension
experiment, `SB` stolen base.

All three implementations expose the **identical public API** —
`simulate(sequence)` returning `.runs`, `.outs`, `.over`, `.bases_occupied()` —
and pass the **identical 21-case shared acceptance suite** (`test_acceptance.py`).
Behaviourally the three programs are indistinguishable; the experiment is
entirely about *how* they are built and what that does to the code.

I chose this app deliberately. Unlike a CRUD web app, it has no framework to
lean on, and its rules are a genuine tangle of special cases — forced walks,
the two-strike foul that is not a strikeout, every runner advancing on a hit,
the third out ending everything. That is exactly the "no well-understood
pattern, few examples, no framework" kind of program the lecture argued would
expose the difference between the three approaches, rather than hiding it the
way a CRUD app would.

## 2. Method

- **By hand** — written manually with a deliberate object-oriented design: all
  rules concentrated in one `HalfInning` state machine, thin polymorphic
  `Event` classes, a `Bases` helper that owns runner movement, and a decorator
  registry so new event codes self-register.
- **Vibe coded** — I gave the agent (Claude Code) only the behavioural spec and
  the test cases, with no architectural guidance, and accepted its single-pass
  output. It chose to build a `baseball` package of eight modules using
  immutable dataclasses.
- **Together** — I seeded a minimal program that already carried the full
  architecture (handling only strikeouts, groundouts, home runs), wrote a
  `CLAUDE.md` of design rules ("model off the existing code," concentrate
  complexity, keep cyclomatic complexity ≤ 3), then added each remaining feature
  one at a time in plan mode, reviewed every diff, and ran one simplify pass.

All complexity numbers below come from `radon`, measured on production code only
(test harnesses excluded).

## 3. The three experiences

**By hand.** Slowest to write, but the most predictable. Because I fixed the
architecture up front, every rule had an obvious home and I never had to re-read
unrelated code to add the next one. The cost was time: getting the
runner-advancement and forced-walk logic correct by hand took real thought.

**Vibe coded.** Fastest to a working program by a wide margin — a complete,
tested implementation in a single pass, with 90 of its own generated tests
passing. Two things stood out. First, the agent reached for *more* structure
than the problem needed: eight modules, an enum-plus-dispatch-table, immutable
`Count` and `Rules` objects. Second, during its initial build it **rewrote one
of its own tests** to match its implementation, asserting the implementation was
the correct one — exactly the failure mode the lecture warns about, where an
agent iterates until the tests pass and can mask a real bug instead of fixing
it. I had to re-derive that case by hand from the spec to trust it.

**Together.** The most controlled of the three. Plan mode forced the agent to
propose a change before editing, so I could reject anything that drifted from
the architecture. Each feature landed as "one small event class plus at most one
method on `HalfInning`," and the simplify pass pulled the single function that
had crept to CC 5 (`advance_all`) back down to CC 2 by extracting two tiny
helpers. One recurring friction: the agent repeatedly **hand-estimated
cyclomatic complexity and was wrong** — it reported `advance_all` as "CC 3" when
`radon` measured 5 — a concrete reminder to measure rather than trust an agent's
self-report.

## 4. Quantitative comparison

### Table 1 — Code and complexity of the finished app (production only)

| Metric | by hand | vibe coded | together |
|---|---|---|---|
| Files / modules | **1** | **8** | **1** |
| SLOC (production) | 163 | 246 | ~165 |
| Mean cyclomatic complexity | 1.63 | **2.11** | 1.61 |
| Max CC (function) | 4 | **6** (`advance_all`) | 4 |
| Functions with CC > 3 | 2 | 3 | 1 |
| Total decision points, Σ(CC − 1) | 30 | **41** | 33 |
| Shared acceptance tests | 21/21 | 21/21 | 21/21 |

### Table 2 — Blast radius of adding one feature (stolen base)

| Metric | by hand | vibe coded | together |
|---|---|---|---|
| **Production files changed** | **1** | **3** | **1** |
| Total files changed (incl. tests) | 1 | 4 | 2 |
| Modules touched | `half_inning.py` | `bases.py`, `events.py`, `inning.py` | `half_inning.py` |
| Lines added / removed | +16 / −0 | +41 / −4 | +65 / −5 |
| Mean CC after | ~1.64 | 2.13 | 1.62 |
| Any existing test edited? | no | no (additive) | import fix only* |

\* The together test file needed a one-line import fixed, a leftover from
renaming the module — not a change to any assertion.

## 5. Discussion

**Low cyclomatic complexity is not the whole story.** The vibe-coded version's
per-function CC is still in radon's "A" band, yet the same behaviour is spread
across eight modules and carries ~50% more code and ~30% higher mean complexity
than the hand-written version. The lecture's "diffuse complexity" shows up here
less as tangled functions and more as *scattering*: the logic for one idea is
distributed across `events.py`, `count.py`, `outcomes.py`, `bases.py`, and
`inning.py` rather than concentrated in one state machine.

**Blast radius is where the difference bites.** Adding a stolen base — a play
that does not end the plate appearance and does not touch the count — landed in
a single file in the by-hand and together versions (add a `Bases` method, a
`HalfInning` transition, and a thin `SB` event; the parser, registry, and
`simulate` untouched). In the vibe-coded version the same play reached into
three production modules at once. The reason is structural: a steal is a *new
category* of event that does not fit the vibe design's `Pitch`/`Outcome` split,
so absorbing it forced edits to the dispatch, the bases, and the inning's
processing loop simultaneously. This is the lecture's central claim reproduced
in miniature.

**A human fixing the architecture recovers hand-written quality.** The together
version matched the by-hand version almost exactly — mean CC 1.61 vs 1.63, one
module, a one-file extension — while letting the agent do the typing. The value
the human added was not writing code but *owning the structure* and reviewing
each step.

**Goodhart's caveat.** "Together" optimized partly toward a metric (CC ≤ 3), and
a measure that becomes a target can be gamed — e.g. by replacing branches with a
brittle lookup table that lowers CC without truly simplifying. I watched the
simplify pass for this, and in this case the refactor genuinely concentrated the
logic rather than hiding it, but the risk is real and is the reason I reviewed
diffs instead of trusting the number alone.

**The gap compounds.** With a single extension the differences are modest. The
lecture's point is that they accumulate: each of dozens of future features would
widen the SLOC, complexity, and blast-radius gaps, and the vibe-coded code's
scattered diffs would make each review and merge progressively harder.

## 6. Conclusion

Vibe coding was dramatically faster and produced correct, working, well-tested
code — but more of it, more complex, and more scattered, on an application with
no framework to guide the agent. Building *together*, with a human-fixed
architecture and feature-by-feature review, recovered essentially hand-written
quality while keeping much of the speed. For this class of program the lecture's
thesis held up under measurement: the value of the human in the loop is not
typing the code but owning its structure.

## Appendix — reproduction

```powershell
# complexity and size (run per implementation)
uv run --with radon radon cc half_inning.py -s -a      # by hand / together
uv run --with radon radon cc baseball     -s -a        # vibe coded (package)
uv run --with radon radon raw <target>    -s

# shared behaviour (copy test_acceptance.py into each folder)
uv run --with pytest pytest test_acceptance.py -q      # 21/21 in all three

# blast radius of the stolen-base extension
git diff --stat HEAD~1 HEAD -- byhand
git diff --stat HEAD~1 HEAD -- vibecode
git diff --stat HEAD~1 HEAD -- together
```

# Half-Inning Baseball Simulator — Built Three Ways

One application, implemented three ways — **by hand**, **vibe coded**, and
**together** with an AI coding agent — then compared on code structure,
cyclomatic complexity, and the blast radius of adding a new feature.

## The application

A deterministic **half-inning baseball simulator**. You feed it a sequence of
event codes (pitches and outcomes); it tracks the count, the baserunners, the
outs, and the runs scored, and stops at the third out.

Event codes: `B` ball, `S` strike, `F` foul, `1B`/`2B`/`3B`/`HR` hits,
`BB` walk, `K` strikeout, `GO` groundout, `FO` flyout, `SB` stolen base.

All three versions expose the identical public API:

```python
simulate(sequence)   # sequence: "1B 1B HR" or ["1B", "1B", "HR"]
# -> an inning object with:
#    .runs, .outs, .over, .bases_occupied()  # (first, second, third) bools
```

## Repository layout

```
4_1/
├─ README.md               # this file
├─ pyproject.toml          # uv project (dev deps: pytest, radon)
├─ byhand/
│  ├─ half_inning.py       # single-file, hand-written design
│  └─ test_acceptance.py   # shared 21-case suite (run here)
├─ vibecode/
│  ├─ baseball/            # 8-module package the agent produced
│  │  ├─ bases.py  count.py  errors.py  events.py
│  │  └─ inning.py  outcomes.py  rules.py  __init__.py
│  ├─ tests/              # the vibecode version's own tests
│  └─ test_acceptance.py   # shared 21-case suite (run here)
└─ together/
   ├─ half_inning.py       # single-file, grown feature-by-feature with the agent
   ├─ CLAUDE.md            # design guide given to the agent
   ├─ test_half_inning.py  # the together version's own test suite
   └─ test_acceptance.py   # shared 21-case suite (run here)
```

## The three versions

- **by hand** — written manually with a deliberate object-oriented design: all
  rules in one `HalfInning` state machine, thin polymorphic `Event` classes, a
  `Bases` helper for runner movement, and a decorator registry for event codes.
- **vibe coded** — the agent was given only the behavioural spec and test cases,
  no architectural guidance, and its single-pass output was accepted as-is. It
  chose an eight-module package with immutable dataclasses.
- **together** — a minimal human-written seed (full architecture, minimal
  features) plus a `CLAUDE.md` of design rules; each remaining feature was added
  one at a time in plan mode, reviewed, then a single simplify pass was run.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Running and reproducing

```powershell
# run the shared acceptance suite in a version (copy test_acceptance.py into the folder first)
uv run --with pytest pytest test_acceptance.py -q        # 21/21 in all three

# cyclomatic complexity and size
uv run --with radon radon cc half_inning.py -s -a        # byhand / together
uv run --with radon radon cc baseball     -s -a          # vibecode (package)
uv run --with radon radon raw <target>    -s

# blast radius of the stolen-base extension (across the committed history)
git diff --stat HEAD~1 HEAD -- byhand vibecode together
```

The by-hand and together versions also carry an inline smoke test:
`uv run python half_inning.py` prints `self-tests passed`.

## Results at a glance

All three are behaviourally identical (21/21 shared acceptance tests), yet
differ in structure. Production-code figures (`radon`):

| | by hand | vibe coded | together |
|---|---|---|---|
| Modules | 1 | 8 | 1 |
| SLOC | 163 | 246 | ~165 |
| Mean cyclomatic complexity | 1.63 | 2.11 | 1.61 |
| Files touched to add a stolen base | 1 | 3 | 1 |


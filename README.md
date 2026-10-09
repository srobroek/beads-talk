# beads-talk

Reproducible Beads durable-agent orchestration demo: **lose the conversation, keep the project**.

A small log-analysis CLI (`logdemo`) is built through a Beads epic: live task
decomposition, subagents, independent review, a failed acceptance check, a
fresh-session continuation and real GitHub delivery. The ledger, not the chat,
carries the work across sessions.

## Tools and versions

| Tool | Version | Role |
|---|---|---|
| [Beads](https://github.com/gastownhall/beads/tree/v1.3.0) (`bd`) | 1.3.0 | Durable graph, claims, readiness, history, formulas, molecules, gates, wisps |
| [Mardi Gras](https://github.com/quietpublish/mardi-gras/tree/v0.33.0) (`mg`) | 0.33.0 | Terminal board that reads through `bd` |
| OMP coding agent | 18.8.0 | Lead and subagents |
| OMP Beads plugin | 4.1.3 | Guardrails on top of native Beads (below) |
| OMP SpecKit plugin | 0.10.2 | Source of the bundled SpecKit formulas |
| OMP Delivery plugin | 1.4.0 | PR landing receipt |
| Python | 3.12+ | Application and checks; standard library only |

### Native Beads versus OMP

- **Native Beads** owns the graph, atomic claims (`bd update ID --claim`), readiness
  (`bd ready`), history (`bd history`), formulas, molecules, human gates and wisps.
  Everything in this walkthrough runs with plain `bd`.
- **OMP Beads** adds actor attribution, serialization of writes to the embedded
  store, closure safeguards and pinning to the canonical store. It does not
  schedule work: `metadata.execution_agent_type` is input the lead reads when it
  dispatches.
- The workflow contract itself is [`AGENTS.md`](AGENTS.md) and is tool-portable.

## Repository layout

| Path | Purpose |
|---|---|
| `logdemo/` | CLI: `python3 -m logdemo dump FILE` (baseline) |
| `fixtures/` | JSON Lines inputs |
| `tests/`, `checks/acceptance.py` | Unit tests and CLI acceptance (`baseline`, `summary`, `filtered`) |
| `demo/epic.json` | Seed graph: nine nodes, eight parent-child links, two blockers |
| `demo/prepared-summary.patch` | Prepared summary commit with a disclosed defect |
| `demo/summary-acceptance.md`, `demo/filter-acceptance.md` | Written acceptance |
| `prompts/` | Ready-to-paste prompts |
| `.beads/formulas/` | `talk-delivery`, `demo-smoke` and seven bundled SpecKit formulas |
| `AGENTS.md` | Durable agent workflow contract |

## The disclosed defect

`demo/prepared-summary.patch` is a public teaching fixture. It adds a summary
command that counts an event as `ERROR` when its **message** contains `ERROR`,
even when its level is `INFO`. The default kit does not apply it. Ordinary
summary checks pass with the patch; `python3 checks/acceptance.py summary` fails
on `fixtures/message-error.jsonl` (expected `1/0/0`). Finding and fixing this in a
fresh session is the point of the demo.

## 1. Bind variables

Every later block uses these variables. Set them once per shell, in the
repository's canonical checkout. Choose a new run name for every run; runs are
never reset.

```sh
export RUN=rehearsal-01
export REPO=srobroek/beads-talk
export CANONICAL="$(git rev-parse --show-toplevel)"
export KIT_SHA="$(git rev-parse demo-kit-v1^{commit})"
export BEADS_DIR="$CANONICAL/.beads"
export GIT_TERMINAL_PROMPT=0 PAGER=cat GIT_PAGER=cat
unset BEADS_DOLT_SHARED_SERVER
```

Actors are fixed per run:

```sh
export ACTOR_PREPARE="demo/$RUN/prepare"
export ACTOR_LEAD_A="demo/$RUN/lead-a"
export ACTOR_LEAD_B="demo/$RUN/lead-b"
export SESSIONS='REPLACE: empty private directory for agent sessions, outside the repository'
```

Linked worktrees are created with [Worktrunk](https://worktrunk.dev) (`wt`). Its
JSON output names the created path; read it, do not construct it.

## 2. Check the baseline

```sh
python3 -m unittest discover -s tests
python3 checks/acceptance.py baseline
python3 -m logdemo dump fixtures/demo.jsonl
```

Expected: tests and baseline acceptance pass; `dump` prints the four records of
`fixtures/demo.jsonl` as a JSON array in input order. `summary` and `filtered`
acceptance fail because those features do not exist yet.

## 3. Create the run base branch

```sh
wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-base/$RUN"
```

In the returned path:

```sh
git push -u origin "demo-base/$RUN"
git ls-remote origin "refs/heads/demo-base/$RUN"
```

This branch is the run's PR destination, not the default branch.

## 4. Seed the epic

```sh
bd dolt pull
BEADS_ACTOR="$ACTOR_PREPARE" bd create --graph demo/epic.json --dry-run --json
BEADS_ACTOR="$ACTOR_PREPARE" bd create --graph demo/epic.json --json
```

The dry run reports `node_count: 9`, `parent_deps: 8` and `edge_count: 5`
(two `blocks`, three `related`). Read the created IDs from the live JSON output
and bind them; IDs are assigned at runtime:

```sh
export EPIC='REPLACE: epic id from the output'
export SUMMARY='REPLACE: summary id from the output'
export MERGE='REPLACE: merge id from the output'
```

Stamp the per-run merge anchors:

```sh
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$MERGE" --set-metadata "branch=demo-delivery/$RUN" --set-metadata "origin_actor=$ACTOR_LEAD_A" --set-metadata "demo_run=$RUN"
```

### Graph shape

```
epic: Deliver service-filtered log summaries
├── summary               implementer   prepared code
├── review-summary        researcher    read-only review
├── filter-feature        (feature)     decomposed live
├── integration           implementer   blocked by summary-accepted, filter-artifact
├── merge                 operator      labels pr:merge, agent:shepherd
├── summary-accepted      operator      label demo:milestone
├── filter-artifact       operator      label demo:milestone
└── integration-artifact  operator      label demo:milestone
```

Blockers point from dependent to prerequisite: `integration` needs both
`summary-accepted` and `filter-artifact`. Milestone carriers are `related` to the
code they certify. No blocker duplicates a parent-child link.

```sh
bd show "$EPIC"
bd graph "$EPIC"
bd ready --parent "$EPIC" --json
```

### Readiness versus dispatch

Raw readiness lists **7** descendants: `summary`, `review-summary`,
`filter-feature`, `merge` and the three milestones. Only `integration` is blocked.
Ready means unblocked, not "needs coding". The dispatch view excludes outcome
containers, milestones and the merge carrier:

```sh
bd ready --parent "$EPIC" --exclude-label demo:milestone,pr:merge --exclude-type epic,feature --json
```

That leaves `summary` and `review-summary`. Once preparation marks `summary`
`state=reported`, the lead discards it: reported code needs review, not more
coding. Dispatch therefore starts with `review-summary` alone, until the lead
decomposes `filter-feature`.

## 5. Prepare the summary commit

```sh
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$SUMMARY" --claim
wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-summary/$RUN"
```

In the returned summary tree:

```sh
git apply demo/prepared-summary.patch
git add -A
git commit -m "feat: add level summary"
python3 checks/acceptance.py summary
```

The last command fails on the message boundary, as disclosed. Record the anchors
and release the claim (the bead stays open):

```sh
export SUMMARY_SHA="$(git rev-parse HEAD)"
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$SUMMARY" --set-metadata state=reported --set-metadata "branch=demo-summary/$RUN" --set-metadata "artifact_sha=$SUMMARY_SHA" --set-metadata "demo_run=$RUN"
BEADS_ACTOR="$ACTOR_PREPARE" bd unclaim "$SUMMARY" --if-assignee="$ACTOR_PREPARE"
```

Create the epic-owned delivery tree after the lead claims the epic:

```sh
BEADS_ACTOR="$ACTOR_LEAD_A" bd update "$EPIC" --claim
wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-delivery/$RUN"
```

```sh
export DELIVERY_TREE='REPLACE: path field from the wt JSON output'
```

In the delivery tree, merge the prepared summary branch:

```sh
git merge --no-ff "demo-summary/$RUN" -m "merge prepared summary"
```

Release the epic claim before launching the lead so it claims it itself:

```sh
BEADS_ACTOR="$ACTOR_LEAD_A" bd unclaim "$EPIC" --if-assignee="$ACTOR_LEAD_A"
```

## 6. Lead A: decompose, dispatch, find the defect

Launch from the delivery tree with an empty session directory of your choice:

```sh
BEADS_ACTOR="$ACTOR_LEAD_A" omp --cwd "$DELIVERY_TREE" --session-dir "$SESSIONS/lead-a"
```

Paste [`prompts/start.md`](prompts/start.md) with `EPIC_ID` replaced by `$EPIC`.

Expected: the lead creates two children under `filter-feature`, dispatches the
filter implementer and the summary reviewer together, records the failed
boundary acceptance as a bug parented to the epic, and stops without fixing it.

While work runs, watch the board:

```sh
mg -no-animations
```

Use only `j`/`k` or arrows, `Enter`, `Esc`, `?` and `q`. If the TUI is
unavailable, `mg -status` prints the same state once.

## 7. Lead B: a fresh session

Exit lead A. Launch a new lead with a **different, empty** session directory and
no resume, continue, fork or import:

```sh
BEADS_ACTOR="$ACTOR_LEAD_B" omp --cwd "$DELIVERY_TREE" --session-dir "$SESSIONS/lead-b"
```

Paste exactly [`prompts/resume.md`](prompts/resume.md) with `EPIC_ID` replaced:

```
Continue epic EPIC_ID in this repository.
```

Everything else comes from the ledger and `AGENTS.md`. Expected: the new lead
finds the fix bug, the filter progress and the recorded worktrees, fixes the
defect, integrates and passes:

```sh
python3 -m logdemo summary fixtures/demo.jsonl --service api
python3 checks/acceptance.py filtered
```

This demonstrates lost conversational context, not crash recovery.

## 8. Delivery molecule

`bd mol pour` finds formulas in the resolved store's `formulas/` directory, so
run these from the canonical checkout once it contains `.beads/formulas/` at
`demo-kit-v1`.

```sh
bd mol pour talk-delivery --var "feature=log-summary-$RUN" --dry-run
BEADS_ACTOR="$ACTOR_LEAD_B" bd mol pour talk-delivery --var "feature=log-summary-$RUN" --json
```

Read `new_epic_id` and `id_mapping` from the JSON; never construct step IDs.
Formula steps carry no acceptance field in bd 1.3.0, so set each step's
acceptance with `bd update STEP --acceptance "..."` after pouring.

```sh
export MOL='REPLACE: new_epic_id from the pour output'
export GATE='REPLACE: gate issue id for the approve step, from bd mol show'
```

```sh
bd mol current "$MOL"
bd mol show "$MOL" --parallel
bd ready --mol "$MOL"
```

Steps: `verify` (researcher) → `approve` (operator, human gate) → `land`
(operator) → `record` (operator). `land` stays blocked until a human accepts
the current head and evidence and resolves the gate:

```sh
bd gate resolve "$GATE" --reason "<what was accepted, at which head SHA>"
```

### Transient wisp

```sh
bd mol wisp demo-smoke --var "run=$RUN" --json
bd mol wisp list
```

Wisps are local and ephemeral. Durable conclusions go on a regular bead.

## 9. Review and landing

Review uses [`prompts/review.md`](prompts/review.md) with `PR_NUMBER` and
`HEAD_SHA` replaced. The approval names one full 40-hex head SHA; any new commit
needs a new review. The agent review is posted as a PR comment from the author's
account and is disclosed as such; it is not a separate GitHub-user approval.
Landing is a squash merge into `demo-base/$RUN` and requires green `verify` CI
for that head and the resolved human gate. Code beads stay open until the
landing receipt; then the merge bead closes first, children before parents.

```sh
export PR='REPLACE: pull request number'
```

```sh
gh pr view "$PR" --json state,baseRefName,headRefOid,mergeCommit
bd history "$EPIC"
bd dolt push
git ls-remote origin refs/dolt/data
```

## SpecKit formula example

`.beads/formulas/` carries seven formulas copied byte-for-byte from the OMP
SpecKit plugin 0.10.2 (`formulas/` directory), names unchanged:
`speckit-basic`, `speckit-lean`, `speckit-feature`, `mol-speckit-bugfix`,
`mol-speckit-fix-findings`, `mol-speckit-iterate`, `mol-speckit-refine`.

The demo only instantiates the template; no specification phase runs, and no
`.specify/` scaffolding or `tasks.md` exists.

```sh
bd formula show speckit-basic
bd cook speckit-basic --var "feature=001-formula-only-$RUN" --var autonomous=no --dry-run
bd mol pour speckit-basic --var "feature=001-formula-only-$RUN" --var autonomous=no --dry-run
```

With `autonomous=no`, the human approval gates stay in the molecule. Unperformed
phases stay open. Label any instance `formula instantiated; specification phases
not executed`.

Real SpecKit work does not pour by hand. It uses the plugin's approval-aware
starter, which records the explicit approval answer and forces its working
directory and `BEADS_DIR` to `<workspace>/.beads`:

```sh
bun <speckit-plugin>/tools/spec-start.ts --spec NNN-slug --workspace <canonical-project> --profile speckit-basic --approvals yes --decision '<explicit answer>' --beads-plugin <beads-plugin>
```

This demo does not run the starter: it would read formulas from the canonical
store, while this kit's formulas live in a linked worktree.

## Workflow contract

See [`AGENTS.md`](AGENTS.md): entry, readiness versus dispatch, claims and
release, metadata conventions, findings, reporting line and landing policy.

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
| [Worktrunk](https://worktrunk.dev) (`wt`) | 0.80.0 | Linked git worktrees |
| OMP coding agent (`omp`) | 18.8.0 | Lead and subagents (`task` tool) |
| OMP Beads plugin | 4.1.3 | Guardrails on top of native Beads |
| OMP SpecKit plugin | 0.10.2 | Source of the bundled SpecKit formulas |
| OMP Delivery plugin | 1.4.0 | `delivery_land` PR landing receipt |
| GitHub CLI (`gh`), `jq`, Python | 3.12+ for Python | PRs, JSON capture, application and checks (standard library only) |

### What runs where

- **Native Beads (`bd`)** owns the graph, atomic claims (`bd update ID --claim`),
  readiness (`bd ready`), history (`bd history`), formulas, molecules, human
  gates and wisps. Every `bd` command below is plain Beads.
- **OMP** runs the agents. The lead dispatches subagents with its `task` tool and
  lands with the Delivery plugin's `delivery_land` tool. The OMP Beads plugin
  adds actor attribution, serialized writes to the embedded store, closure
  safeguards and pinning to the canonical store. Nothing schedules work:
  `metadata.execution_agent_type` is input the lead reads when it dispatches.
- **Git and GitHub** (`git`, `gh`) carry code; `bd dolt push` carries the ledger.
  Code and ledger sync are separate operations.
- The workflow contract is [`AGENTS.md`](AGENTS.md) and is tool-portable.

## Repository layout

| Path | Purpose |
|---|---|
| `logdemo/` | CLI: `python3 -m logdemo dump FILE` (baseline) |
| `fixtures/` | JSON Lines inputs |
| `tests/`, `checks/acceptance.py` | Unit tests and CLI acceptance (`baseline`, `summary`, `filtered`) |
| `demo/epic.json` | Seed graph: nine nodes, eight parent-child links, two blockers |
| `demo/prepared-summary.patch` | Prepared summary commit with a disclosed defect |
| `demo/summary-acceptance.md`, `demo/filter-acceptance.md` | Written acceptance contracts |
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

## 1. Bind the environment

This walkthrough has two entry points. Do not mix them:

- **Initial provisioning (this section).** The presenter runs it once per shell,
  from the canonical checkout: the clone of this repository whose `.beads/` is
  the run's ledger store. It is the only place `BEADS_DIR` is ever set, and only
  when the shell does not already supply it.
- **Already-provisioned agent entry.** Lead sessions launched in sections 6 and 7
  inherit `BEADS_DIR`, `BEADS_ACTOR` and the hardened variables from this shell.
  They skip this section and never rederive `BEADS_DIR`;
  [`AGENTS.md`](AGENTS.md) has them confirm the store with `bd where` and stop on
  a mismatch.

Choose a new `RUN` for every run; runs are never reset.

```sh
export RUN=rehearsal-01
export REPO=srobroek/beads-talk
export CANONICAL="$(git rev-parse --show-toplevel)"
export KIT_SHA="$(git rev-parse 'demo-kit-v1^{commit}')"
export BEADS_DIR="${BEADS_DIR:-$CANONICAL/.beads}"
[ "$BEADS_DIR" = "$CANONICAL/.beads" ] || echo "STOP: inherited BEADS_DIR=$BEADS_DIR is not $CANONICAL/.beads" >&2
export GIT_TERMINAL_PROMPT=0 SSH_ASKPASS=/usr/bin/false SSH_ASKPASS_REQUIRE=force PAGER=cat GIT_PAGER=cat
unset BEADS_DOLT_SHARED_SERVER
export ACTOR_PREPARE="demo/$RUN/prepare"
export ACTOR_LEAD_A="demo/$RUN/lead-a"
export ACTOR_LEAD_B="demo/$RUN/lead-b"
export BEADS_ACTOR="$ACTOR_PREPARE"
export SESSIONS="$(mktemp -d)"
export MG_BIN="$(command -v mg)"
beads_store() {
  [ "$BEADS_DIR" = "$CANONICAL/.beads" ] || { echo wrong-store; return 1; }
  bd where --json | jq -r --arg want "$(cd "$BEADS_DIR" && pwd -P)" \
    'if .path != $want then "wrong-store" elif has("database_path") then "ready" else "missing" end'
}
```

`BEADS_DIR` pins every `bd` call, from any worktree, to the canonical store. A
value the shell already supplies is kept, never replaced; if it names another
store, the check prints `STOP` and `beads_store` refuses every later step: fix
the launching environment and open a new shell.

`beads_store` asks `bd where` which store is active and prints one word: `ready`
(the pinned canonical store holds a database), `missing` (it holds only the
tracked setup files) or `wrong-store`. `bd where` exits 0 in all three cases
and falls back to the current directory when `BEADS_DIR` names no directory,
so its exit status alone proves nothing. Every ledger write below runs only
after `test "$(beads_store)" = ready` succeeds in this shell.

`SESSIONS` is a fresh system-temporary directory for private agent sessions.
`MG_BIN` must resolve to Mardi Gras. Some systems ship an unrelated `mg` editor,
for example `/usr/bin/mg` on macOS; put Mardi Gras first on `PATH` before binding.

Create the kit tree and the run base tree. Worktrunk prints JSON; the path is read
from it, never constructed:

```sh
export KIT_TREE="$(wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-kit/$RUN" | jq -r .path)"
export BASE_TREE="$(wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-base/$RUN" | jq -r .path)"
```

Source pushes in this walkthrough use `git push`; on the presenter's macOS host
the same commands run as `dgit push`.

### Ledger store on a fresh clone

A fresh clone of this repository carries only the tracked `.beads/` setup files
(`config.yaml`, `metadata.json`, formulas). The ledger itself lives on GitHub
under `refs/dolt/data`. Check the store from the kit tree, under the pinned
environment:

```sh
cd "$KIT_TREE"
beads_store
```

`ready`: continue with section 2. `wrong-store`: stop. `missing`: bootstrap the
existing remote ledger, still from the kit tree:

```sh
cd "$KIT_TREE"
git ls-remote origin refs/dolt/data
bd bootstrap --dry-run
test -n "$(git ls-remote origin refs/dolt/data)" && test "$(beads_store)" = missing && bd bootstrap --yes
test "$(beads_store)" = ready
bd dolt remote list
```

`git ls-remote` must print a ref; if it prints nothing, the remote holds no
ledger and this walkthrough stops. Per `bd bootstrap --help` (bd 1.3.0), with
`sync.remote` configured (the tracked `config.yaml` names this repository) it
verifies `refs/dolt/data` and clones the ledger from the remote. It never deletes
existing issues and exits non-zero when it cannot set up a database. If `bd` warns
that `.beads` permissions are too open, run `chmod 700 "$BEADS_DIR"`.
`bd dolt remote list` must show `origin` pointing at this repository.

Never run `bd init` in a clone of this existing repository, never start a Dolt
server, and never reset or re-create anything: the ledger already exists.

## 2. Check the baseline

```sh
cd "$KIT_TREE"
python3 -m unittest discover -s tests
python3 checks/acceptance.py baseline
python3 -m logdemo dump fixtures/demo.jsonl
```

Expected: tests and baseline acceptance pass; `dump` prints the four records of
`fixtures/demo.jsonl` as a JSON array in input order. `summary` and `filtered`
acceptance fail because those features do not exist yet.

## 3. Publish the run base branch

```sh
git -C "$BASE_TREE" push -u origin "demo-base/$RUN"
git ls-remote origin "refs/heads/demo-base/$RUN"
```

This branch is the run's PR destination, not the default branch.

## 4. Seed the epic

Confirm the pinned store before the first ledger write; continue only when this
exits 0:

```sh
cd "$KIT_TREE"
test "$(beads_store)" = ready
```

Then seed:

```sh
cd "$KIT_TREE"
bd dolt pull
BEADS_ACTOR="$ACTOR_PREPARE" bd create --graph demo/epic.json --dry-run --json
BEADS_ACTOR="$ACTOR_PREPARE" bd create --graph demo/epic.json --json > "$SESSIONS/seed.json"
jq . "$SESSIONS/seed.json"
```

The dry run reports `node_count: 9`, `parent_deps: 8` and `edge_count: 5`
(two `blocks`, three `related`). IDs are assigned at runtime; read them from the
live output's key-to-ID map:

```sh
export EPIC="$(jq -r .ids.epic "$SESSIONS/seed.json")"
export SUMMARY="$(jq -r .ids.summary "$SESSIONS/seed.json")"
export FILTER_FEATURE="$(jq -r '.ids["filter-feature"]' "$SESSIONS/seed.json")"
export FILTER_ARTIFACT="$(jq -r '.ids["filter-artifact"]' "$SESSIONS/seed.json")"
export INTEGRATION_ARTIFACT="$(jq -r '.ids["integration-artifact"]' "$SESSIONS/seed.json")"
export MERGE="$(jq -r .ids.merge "$SESSIONS/seed.json")"
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
`state=reported` (section 5), the lead discards it: reported code needs review,
not more coding. Dispatch starts with `review-summary` alone, until the lead
decomposes `filter-feature`.

## 5. Prepare the summary commit and delivery tree

```sh
bd dolt pull
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$SUMMARY" --claim
export SUMMARY_TREE="$(wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-summary/$RUN" | jq -r .path)"
cd "$SUMMARY_TREE"
git apply demo/prepared-summary.patch
git add -A
git commit -m "feat: add level summary"
export SUMMARY_SHA="$(git rev-parse HEAD)"
python3 checks/acceptance.py summary
```

The last command fails on the message boundary, as disclosed. Only now, after the
real commit, mark the bead reported and release the claim; it stays open:

```sh
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$SUMMARY" --set-metadata state=reported --set-metadata "branch=demo-summary/$RUN" --set-metadata "artifact_sha=$SUMMARY_SHA" --set-metadata "demo_run=$RUN"
BEADS_ACTOR="$ACTOR_PREPARE" bd unclaim "$SUMMARY" --if-assignee="$ACTOR_PREPARE"
```

The epic owns the delivery tree. Claim the epic, create the tree, merge the
prepared summary into it, then release so the lead claims the epic itself:

```sh
bd dolt pull
BEADS_ACTOR="$ACTOR_LEAD_A" bd update "$EPIC" --claim
export DELIVERY_TREE="$(wt switch -y --create --no-cd --base "$KIT_SHA" --format json "demo-delivery/$RUN" | jq -r .path)"
git -C "$DELIVERY_TREE" merge --no-ff "demo-summary/$RUN" -m "merge prepared summary"
relpath() { python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$1" "$CANONICAL"; }
BEADS_ACTOR="$ACTOR_PREPARE" bd update "$SUMMARY" --set-metadata "base_sha=$KIT_SHA" --set-metadata "worktree=$(relpath "$SUMMARY_TREE")"
BEADS_ACTOR="$ACTOR_LEAD_A" bd update "$EPIC" --set-metadata "demo_run=$RUN" --set-metadata "base_sha=$KIT_SHA" --set-metadata "branch=demo-delivery/$RUN" --set-metadata "worktree=$(relpath "$DELIVERY_TREE")" --set-metadata "head_sha=$(git -C "$DELIVERY_TREE" rev-parse HEAD)"
BEADS_ACTOR="$ACTOR_LEAD_A" bd unclaim "$EPIC" --if-assignee="$ACTOR_LEAD_A"
```

## 6. Lead A: decompose, dispatch, find the defect

Print the start prompt with the epic bound:

```sh
sed "s/EPIC_ID/$EPIC/g" "$KIT_TREE/prompts/start.md"
```

Launch the lead with an empty session directory and paste that output:

```sh
mkdir -p "$SESSIONS/lead-a"
BEADS_ACTOR="$ACTOR_LEAD_A" omp --cwd "$DELIVERY_TREE" --session-dir "$SESSIONS/lead-a"
```

The lead creates the two `filter-feature` children in one native graph
transaction, of this shape (`parent_id` and the carrier ID are the runtime IDs):

```json
{
  "nodes": [
    {"key": "filter-impl", "parent_id": "<FILTER_FEATURE>", "type": "task",
     "title": "Implement filter_service with tests",
     "acceptance_criteria": "logdemo/filtering.py and tests/test_filtering.py meet demo/filter-acceptance.md; python3 -m unittest tests.test_filtering passes",
     "metadata": {"execution_agent_type": "implementer"}},
    {"key": "filter-verify", "parent_id": "<FILTER_FEATURE>", "type": "task",
     "title": "Verify filter contract on the inspected artifact",
     "acceptance_criteria": "Read-only: records the artifact SHA and expected versus observed results for every case in demo/filter-acceptance.md",
     "metadata": {"execution_agent_type": "researcher"}}
  ],
  "edges": [
    {"from_key": "filter-verify", "to_id": "<FILTER_ARTIFACT>", "type": "blocks"}
  ]
}
```

Expected: the filter implementer works in its own worktree cut from `KIT_SHA`;
the summary reviewer reads the existing summary tree read-only and gets only the
acceptance and the artifact SHA. After the filter commit is inspected, the lead
closes `filter-artifact` and dispatches the verifier. The failed boundary
acceptance becomes a bug parented to the epic; the lead does not fix it,
checkpoints and releases its epic claim.

While work runs, watch the board:

```sh
"$MG_BIN" -no-animations
```

Use only `j`/`k` or arrows, `Enter`, `Esc`, `?` and `q`. If the TUI is
unavailable, `"$MG_BIN" -status` prints the state once.

### Optional: ask the ledger (read-only)

These queries are optional and read-only; nothing in later sections depends on
them. A live answer takes as long as the lead session and `bd` take. If that
would overrun the stage budget, show answers recorded during a rehearsal or skip
this part.

Rebind the epic from the seed output immediately before rendering, then paste
any printed line into a lead session:

```sh
EPIC="$(jq -er .ids.epic "$SESSIONS/seed.json")" &&
  sed "s/EPIC_ID/$EPIC/g" "$KIT_TREE/prompts/discover.md"
```

`jq -e` fails instead of printing `null` when the seed output lacks the epic, so
no prompt renders with a wrong ID.

The native equivalents, equally read-only:

```sh
bd list --status open --type task --json
bd list --parent "$EPIC" --all --json
export EPIC_SCOPE="$EPIC $(bd list --parent "$EPIC" --all --json | jq -r '.[].id' | tr '\n' ' ')"
bd dep list $EPIC_SCOPE --direction down --type related --json
bd dep list $EPIC_SCOPE --direction up --type related --json
bd dep list $EPIC_SCOPE --direction up --type discovered-from --json
bd dep list $EPIC_SCOPE --direction down --type discovered-from --json
bd ready --parent "$EPIC" --json
bd blocked --parent "$EPIC" --json
```

"All tasks related to the epic" is wider than its descendants: the `dep list`
calls add beads linked `related` or `discovered-from` to the epic or any
descendant, in both directions. The JSON shapes differ: `down` returns edge rows
(`issue_id`, `depends_on_id`), `up` returns issue rows (`id`, `dependency_type`).

"What's next" distinguishes ready, blocked, claimed (`assignee`) and
`metadata.state=reported` rows.

## 7. Lead B: a fresh session

Exit lead A. Launch a new lead with a **different, empty** session directory and
no resume, continue, fork or import:

```sh
sed "s/EPIC_ID/$EPIC/g" "$KIT_TREE/prompts/resume.md"
mkdir -p "$SESSIONS/lead-b"
BEADS_ACTOR="$ACTOR_LEAD_B" omp --cwd "$DELIVERY_TREE" --session-dir "$SESSIONS/lead-b"
```

Paste the single printed line, `Continue epic <id> in this repository.`, and
nothing else. Everything else comes from the ledger and `AGENTS.md`. Expected:
the new lead finds the fix bug, the filter progress and the recorded worktrees,
fixes the defect, integrates and passes:

```sh
cd "$DELIVERY_TREE"
python3 -m logdemo summary fixtures/demo.jsonl --service api
python3 checks/acceptance.py filtered
```

This demonstrates lost conversational context, not crash recovery.

## 8. Delivery molecule

`bd` finds formulas by name in the active store's `formulas/` and in the current
checkout's `.beads/formulas/`. Run these from the delivery tree, which carries
the kit formulas; nothing is copied into the canonical checkout.

```sh
cd "$DELIVERY_TREE"
bd formula show talk-delivery
bd mol pour talk-delivery --var "feature=log-summary-$RUN" --dry-run
BEADS_ACTOR="$ACTOR_LEAD_B" bd mol pour talk-delivery --var "feature=log-summary-$RUN" --json > "$SESSIONS/mol.json"
jq . "$SESSIONS/mol.json"
export MOL="$(jq -r .new_epic_id "$SESSIONS/mol.json")"
```

Read step IDs from `id_mapping` in that JSON; never construct them. Formula steps
carry no acceptance field in bd 1.3.0, so the lead sets each step's acceptance
with `bd update STEP --acceptance "..."` after pouring, then links the molecule:
`verify` blocked by `integration-artifact`, the root `related` to the epic, and
`land` `related` to the merge bead.

```sh
bd mol current "$MOL"
bd mol show "$MOL" --parallel
bd ready --mol "$MOL"
```

These molecule views follow only the molecule's internal edges. They still list
`verify` as ready even while the external `integration-artifact` blocker is
open. Before dispatching any step, check the real state:

```sh
bd show "$VERIFY_STEP" --json
bd dep list "$VERIFY_STEP" --json
bd blocked --json
```

`VERIFY_STEP` is the `verify` ID from `id_mapping`.

Steps: `verify` (researcher) → `approve` (operator, human gate) → `land`
(operator) → `record` (operator). `land` stays blocked until a human accepts the
current head and evidence and the gate is resolved with
`bd gate resolve <gate-id> --reason "<what was accepted, at which head SHA>"`.

### Transient wisp

```sh
cd "$DELIVERY_TREE"
bd mol wisp demo-smoke --var "run=$RUN" --json
bd mol wisp list
```

Wisps are local and ephemeral. Durable conclusions go on a regular bead.

## 9. Review and landing

```sh
cd "$DELIVERY_TREE"
git push -u origin "demo-delivery/$RUN"
cat > "$SESSIONS/pr-body.md" <<EOF
Adds \`python3 -m logdemo summary FILE [--service NAME]\`: level counts for all
events or one exact service.

Why: demo epic $EPIC, delivered through a durable Beads ledger.

Test plan:
- python3 -m unittest discover -s tests
- python3 checks/acceptance.py baseline
- python3 checks/acceptance.py summary
- python3 checks/acceptance.py filtered

Bead: $EPIC
EOF
printf 'Closes-Bead: %s\n' $IMPLEMENTED_IDS >> "$SESSIONS/pr-body.md"
gh pr create --repo "$REPO" --draft --base "demo-base/$RUN" --head "demo-delivery/$RUN" --title "feat: add service-filtered log summaries" --body-file "$SESSIONS/pr-body.md"
export PR="$(gh pr view "demo-delivery/$RUN" --repo "$REPO" --json number -q .number)"
export HEAD_SHA="$(gh pr view "$PR" --repo "$REPO" --json headRefOid -q .headRefOid)"
sed -e "s/PR_NUMBER/$PR/g" -e "s/HEAD_SHA/$HEAD_SHA/g" "$KIT_TREE/prompts/review.md"
```

`IMPLEMENTED_IDS` holds the space-separated IDs of the implementation beads that
land in this PR (summary, fix, filter implementation, integration), read from
`bd list --parent "$EPIC" --all --json`. A fresh independent reviewer gets the
printed review prompt. The lead writes the reviewer's actual result, never an
invented one, to `$SESSIONS/review-comment.md` in this shape and posts it from
the author's account with
`gh pr comment "$PR" --repo "$REPO" --body-file "$SESSIONS/review-comment.md"`:

```
VERDICT: APPROVE
Reviewed-Head: <full 40-hex headRefOid>
Checks: <commands and exit statuses>
Independent agent review posted by the PR author's account; not a separate GitHub-user approval.
```

```sh
gh pr view "$PR" --repo "$REPO" --json headRefOid,comments
gh pr checks "$PR" --repo "$REPO"
```

Landing requires `Reviewed-Head` equal to the current `headRefOid`, green
`verify` CI for that head and the resolved human gate. Any new commit needs a
new review. Then `gh pr ready "$PR" --repo "$REPO"`, and the lead calls the
Delivery plugin's `delivery_land` tool (an OMP tool, not a shell command) with
arguments of this shape:

```json
{"repo": "srobroek/beads-talk", "pr": 12, "merge_method": "squash",
 "expectHeadSha": "<reviewed 40-hex SHA>", "worktree": "<delivery tree>", "beadId": "<epic id>"}
```

`pr` is the literal PR number. The tool does not check the review; the lead does.

The receipt must show `MERGED`, the reviewed head, base `demo-base/$RUN` and the
merge SHA. Then the merge bead closes first, children before parents, and the
ledger syncs:

```sh
gh pr view "$PR" --repo "$REPO" --json state,baseRefName,headRefOid,mergeCommit
bd history "$EPIC" --events
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

Before the real pour, ask the presenter whether this sample keeps human
approval gates, and bind their actual answer. `autonomous=no` keeps the gates:

```sh
export APPROVAL_ANSWER='REPLACE with the presenter'"'"'s exact answer'
```

```sh
cd "$DELIVERY_TREE"
bd formula show speckit-basic
bd cook .beads/formulas/speckit-basic.formula.toml --var "feature=001-formula-only-$RUN" --var autonomous=no --dry-run
bd mol pour speckit-basic --var "feature=001-formula-only-$RUN" --var autonomous=no --dry-run
BEADS_ACTOR="$ACTOR_LEAD_B" bd mol pour speckit-basic --var "feature=001-formula-only-$RUN" --var autonomous=no --json > "$SESSIONS/speckit.json"
export SPEC_MOL="$(jq -r .new_epic_id "$SESSIONS/speckit.json")"
BEADS_ACTOR="$ACTOR_LEAD_B" bd update "$SPEC_MOL" --spec-id "001-formula-only-$RUN" --set-metadata human_approvals=yes --set-metadata autonomous=no --set-metadata demo_kind=formula-only --set-metadata "approval_choice=$APPROVAL_ANSWER"
bd mol current "$SPEC_MOL"
bd ready --mol "$SPEC_MOL"
```

With `autonomous=no`, the human approval gates stay in the molecule;
`id_mapping` in `$SESSIONS/speckit.json` names each step, and the lead stamps
the same `spec_id` on them. Unperformed
phases stay open. Label any instance `formula instantiated; specification phases
not executed`.

Real SpecKit work does not pour by hand. It uses the plugin's approval-aware
starter, which records the explicit approval answer and forces its working
directory and `BEADS_DIR` to `<workspace>/.beads`:

```sh
bun <speckit-plugin>/tools/spec-start.ts --spec NNN-slug --workspace <canonical-project> --profile speckit-basic --approvals yes --decision '<explicit answer>' --beads-plugin <beads-plugin>
```

This demo does not run the starter: forced to the canonical checkout, it would
not see the formulas that live in the linked worktrees.

## Workflow contract

See [`AGENTS.md`](AGENTS.md): entry, readiness versus dispatch, claims and
release, metadata conventions, findings, reporting line and landing policy.

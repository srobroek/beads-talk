# beads-talk

Companion repository for the talk **Durable agent orchestration with Beads: lose
the conversation, keep the project**.

This README is a quick start for **your own repository**. You plan one feature as a
Beads epic, let one or more coding agents work it, end the chat, and continue in a
fresh session from the ledger. The stage app and the presenter's reproduction kit
are separate; see [Try the stage app](#try-the-stage-app-optional).

## What Beads does, and what it does not

- `bd` stores a graph of work in your repository: epics, children, dependencies,
  acceptance criteria, claims, notes, metadata and history. The ledger is a Dolt
  database that syncs through your git remote under `refs/dolt/data`. Code
  branches are not touched.
- `bd` **does not run agents or schedule work**. Your harness (Claude Code, Codex,
  Cursor, …) or you read `bd ready` and decide who works on what. Metadata such as
  `execution_agent_type` is a routing hint for whoever dispatches.

Each step below says why it exists, gives the commands to run yourself, gives a
prompt that asks your agent to do the same, and says what you should see.
Use whichever you prefer.

**Placeholders.** `<epic-id>`, `<writer-id>`, `<owner>/<repo>` and similar are
yours to fill in. IDs are whatever `bd` prints for you (prefix = your directory
name by default); never type an ID from this page. Commands match `bd` 1.3.0.

The running example is "add CSV export to a report command". Replace it with a
small feature from your own project.

## 1. Install `bd` and connect your repository

Install once per machine with one of the methods from the
[v1.3.0 README](https://github.com/gastownhall/beads/blob/v1.3.0/README.md#-installation);
the [installation guide](https://github.com/gastownhall/beads/blob/v1.3.0/docs/getting-started/installation.md)
covers the install script, Windows and Linux packages.

```sh
brew install beads                              # macOS / Linux
npm install -g @beads/bd                        # or, with Node.js
bd version                                      # expect 1.3.0 or newer
```

Beads syncs through your repository's `origin`, so it must point at a repository
**you** own before you set Beads up:

```sh
cd <your-repo>
git remote -v                                   # origin must be your repository
git ls-remote origin refs/dolt/data             # does a ledger already exist?
```

### 1a. No output: create a new ledger

`bd init` commits its setup files on the current branch, so give it a branch.
`--skip-agents` and `--skip-hooks` keep it from writing agent instructions or git
hooks; you choose your harness integration in step 2.

```sh
git switch -c chore/beads-setup
BD_NON_INTERACTIVE=1 bd init --init-if-missing --skip-hooks --skip-agents
bd info                                         # database path and issue count
bd dolt remote list                             # expect: origin <your repo URL>
```

`bd init` wires your git `origin` as the ledger remote. If `bd dolt remote list`
prints `No remotes configured.`, add it once, in Dolt's URL form:

```sh
bd dolt remote add origin git+ssh://git@github.com/<owner>/<repo>.git
```

If `bd` refuses because the URL matches your git origin, that same-repository
layout is the documented default
([sync concepts](https://github.com/gastownhall/beads/blob/v1.3.0/docs/core-concepts/sync-concepts.md));
re-run with `--allow-git-origin` only if that is what you want. Never re-add a
remote name that already exists: it is replaced silently.

Merge the setup branch the way you merge anything else, then publish the ledger:

```sh
bd dolt push                                    # expect: Push complete.
git ls-remote origin refs/dolt/data             # expect: one ref
```

Exit status is not proof; the `refs/dolt/data` line is. The generated
`.beads/README.md` shows `bd update ID --status done`; prefer
`bd close ID --reason "<evidence>"`.

### 1b. A ref is printed: join the existing ledger

Someone already set Beads up. Clone it; never re-initialize over it.

```sh
bd bootstrap --dry-run                          # shows what it will do
bd bootstrap --yes
bd info
```

Do not use `bd init --force`, `--reinit-local` or `--discard-remote` on a project
that already has a ledger. No Dolt server is needed for normal use.

## 2. Connect your agent harness

`bd setup <recipe>` writes instruction files and, for some tools, session hooks
or a skill, so the agent runs `bd prime` and knows the workflow. **You** run it,
on your setup branch, and review the diff before committing. Recipes write a
managed section between `BEGIN/END BEADS` markers; your own text in
`AGENTS.md` or `CLAUDE.md` stays yours, re-running updates the section in place,
and `--remove` deletes only that section
([IDE setup, v1.3.0](https://github.com/gastownhall/beads/blob/v1.3.0/docs/getting-started/ide-setup.md)).

| Harness | Install (project) | Check | Notes |
|---|---|---|---|
| Claude Code | `bd setup claude` | `bd setup claude --check` | SessionStart hook + `CLAUDE.md` section; `--global` writes `~/.claude/settings.json` |
| Codex CLI | `bd setup codex` | `bd setup codex --check` | Skill + `AGENTS.md` guidance + hooks; `--global` targets your Codex home |
| Cursor | `bd setup cursor` | `bd setup cursor --check` | Rules file, session hooks and skill |
| Gemini CLI | `bd setup gemini --project` | `bd setup gemini --check` | Without `--project` it writes `~/.gemini/settings.json` |
| Copilot CLI | `bd setup copilot` | `bd setup copilot --check` | CLI plugin + `.github/copilot-instructions.md`; Copilot in VS Code uses the MCP server instead |
| OpenCode, Factory, Mux | `bd setup opencode` (or `factory`, `mux`) | `… --check` | Managed `AGENTS.md` section |

```sh
bd setup --list                                 # every recipe on your version
bd setup codex --print                          # preview the text, writes nothing
git diff                                        # review what setup changed
```

`--check` exits non-zero until the integration is installed. Restart the harness
after setup so it loads the new hooks or instructions. By default `bd prime`
gives agents conservative git authority: they propose commits and pushes rather
than doing them. That is a good default while you learn.

**OMP** has no `bd setup` recipe. Its optional Beads plugin adds actor
attribution, serialized ledger writes and closure safeguards; it schedules
nothing. Nothing in this guide requires it.

**Check it works.** In a new agent session:

> Run `bd prime` and `bd ready`. In three sentences, tell me how you will track work in this repository.

Expected: the agent describes claiming, ready work and closing with evidence.

## 3. Create the epic

An epic is the durable name of the feature. Its acceptance criteria are what
"done" means later, for you and for any reviewer.

```sh
bd create "Add CSV export to the report command" -t epic -p 1 \
  --description "Users can export the existing report as CSV." \
  --acceptance "report --format csv prints a header row and one row per record; default output unchanged; tests pass" \
  --silent
```

`--silent` prints only the new ID. Copy it; it is your `<epic-id>`.

Or ask the agent:

> Plan "CSV export for the report command" as one Beads epic. Read the relevant code first. Create only the epic, with a description and testable acceptance criteria, then print its ID. Do not create children or edit code.

## 4. Inspect: what is there, what is related, what is next

```sh
bd show <epic-id>                               # description, acceptance, notes, metadata
bd children <epic-id>                           # every child, including closed ones
bd graph <epic-id>                              # layers: same layer can run in parallel
bd ready --parent <epic-id>                     # open, unblocked, unclaimed
bd blocked --parent <epic-id>                   # and what blocks them
bd dep list <epic-id> --direction up            # what points at the epic
```

"Ready" means nothing blocks it, not "needs coding": a finished but unreviewed
bead can still be ready. Natural-language versions:

> What tasks are in epic `<epic-id>`, and which are done, claimed or blocked?

> What else in the ledger is related to, or was discovered from, `<epic-id>`?

> What can be worked on next in `<epic-id>`, and why is each blocked item blocked?

## 5. Split the work into children with real dependencies

Each child should have one owner, named files, and acceptance someone else can
check. Add a dependency only when a child needs another child's output or would
edit the same file; ordering preferences are not dependencies.

```sh
bd create "CSV formatter with unit tests" -t task --parent <epic-id> \
  --acceptance "to_csv(rows) writes header and rows; tests cover empty input and quoting" \
  --metadata '{"execution_agent_type":"implementer"}' --silent        # <writer-id>
bd create "Document CSV export" -t task --parent <epic-id> \
  --acceptance "user docs show report --format csv with sample output" \
  --metadata '{"execution_agent_type":"implementer"}' --silent        # <docs-id>
bd create "Wire --format csv into the report CLI" -t task --parent <epic-id> \
  --acceptance "report --format csv uses to_csv; CLI test passes; default output unchanged" \
  --metadata '{"execution_agent_type":"implementer"}' --silent        # <cli-id>
bd create "Review CSV export against the epic acceptance" -t task --parent <epic-id> \
  --acceptance "reviewer runs the named tests at one commit and reports PASS or FAIL with output" \
  --metadata '{"execution_agent_type":"researcher"}' --silent         # <review-id>

bd dep add <cli-id> <writer-id>                 # CLI depends on formatter
bd dep add <review-id> <cli-id>                 # review depends on CLI
bd dep add <review-id> <docs-id>                # review depends on docs
bd ready --parent <epic-id>                     # expect: formatter and docs
```

Read `bd dep add A B` as **A depends on B**. Careful: `bd create --deps blocks:B`
means the opposite (B depends on the new bead). `execution_agent_type`
(`implementer`, `researcher`, `operator`) tells the dispatcher what kind of
agent to use; if you leave it out, ask the agent to fill it in while planning.

Or ask the agent:

> Decompose epic `<epic-id>` into child beads. Each child gets one owner, the files it touches, testable acceptance criteria and `execution_agent_type` metadata. Add `blocks` dependencies only where a child needs another's output or edits the same file; use `related` otherwise. Create them in one `bd create --graph` transaction after a `--dry-run`. Show me `bd graph <epic-id>` and `bd ready --parent <epic-id>`. Do not start work.

## 6. Claim, work, test, report, review

A claim is atomic: a second claimant is refused. Claim before you edit or create
a branch. Claims are per actor (`--actor`, else `$BEADS_ACTOR`, else git
`user.name`), and re-claiming your own bead succeeds, so give each agent its own
actor name (for example `BEADS_ACTOR=<you>/csv-writer`) when several run as you.

```sh
bd update <writer-id> --claim
git worktree add -b csv-formatter ../<repo>-csv-formatter <base-sha>
# …edit, test, commit in that worktree…
bd update <writer-id> --set-metadata branch=csv-formatter --set-metadata head_sha=<commit-sha>
bd comment <writer-id> "<test command> -> <result>; commit <commit-sha>"
```

Concurrent writers each get their own worktree cut from the same base commit,
so they never share a checkout. The worker records evidence and reports; it
does not close its own bead. Code beads stay open until their change has landed.

Review is independent: a fresh agent (or a person) checks the commit against the
acceptance, without fixing anything. A defect becomes its own durable bead,
linked to where it was found:

```sh
bd create "CSV formatter drops quotes around names with commas" -t bug --parent <epic-id> \
  --deps discovered-from:<writer-id> \
  --acceptance "names containing commas are quoted; regression test added" \
  --metadata '{"execution_agent_type":"implementer"}' --silent
```

Prompts:

> Work epic `<epic-id>`. Take items from `bd ready --parent <epic-id>`. Claim each with `bd update ID --claim` before editing. Give each concurrent writer its own git worktree from one base commit. If you can run subagents, dispatch independent children in one parallel batch; otherwise do them one at a time. Each worker runs the tests its acceptance names, commits, records branch, commit and result on the bead, and reports. Do not close code beads.

> Review bead `<writer-id>` at commit `<commit-sha>` against its acceptance criteria. Read-only: run the named checks and report PASS or FAIL with the commands and output. For a defect, state expected versus observed behavior. Do not fix it.

## 7. Checkpoint, then continue in a fresh session

The conversation is disposable; the ledger is the handoff. Before ending a
session, commit, write what matters onto the beads, release claims and sync.

```sh
bd update <epic-id> --append-notes "Formatter at <commit-sha>, tests pass. Bug <bug-id> open. Next: fix bug, then CLI."
bd unclaim <writer-id>                          # only releases your own claim
bd dolt push
```

Start a new session with no history and give it only this:

> Continue epic `<epic-id>` in this repository.

Expected: the agent runs `bd prime` and `bd show`, finds the notes, the open bug,
the recorded branch and commit, and what is ready; it reuses existing branches
and worktrees instead of starting over. Anything only in the old transcript is
gone, which is why anchors go on the beads.

## 8. Deliver: pull request, checks, your decision, merge, then close

Close code beads after the change has actually merged. Code and ledger sync
separately: `git push` never moves the ledger, and `bd dolt push` never moves code.
These examples use GitHub's `gh`; use your host's equivalent.

```sh
git push -u origin <branch>
gh pr create --draft --title "feat: CSV export for reports" --body "Bead: <epic-id>"
gh pr view <pr-number> --json headRefOid       # the exact commit under review
gh pr checks <pr-number>                       # CI for that commit
```

You review the evidence for that head commit and decide. A new commit needs a
new review. After you merge under your normal policy:

```sh
gh pr view <pr-number> --json state,mergeCommit # expect: MERGED and a merge SHA
bd update <writer-id> --set-metadata pr=<pr-number> --set-metadata merge_sha=<merge-sha>
bd close <writer-id> --reason "Merged <pr-url> (<merge-sha>); tests: <command> -> pass"
bd close <epic-id> --reason "All children closed; acceptance verified at <merge-sha>"
bd dolt push
```

Close children before their parent, each with checkable evidence. Trying it
locally without a pull request is fine: close after your own review, with the
test command and commit as evidence.

## End-to-end orchestration prompt

Paste this into a lead session once steps 1–3 are done. It stops before merging.

```text
You are the lead for Beads epic <epic-id> in this repository.

Scope: only the feature the epic describes. No unrelated refactors, new
dependencies, servers or persistence.

1. Run bd prime, bd dolt pull, bd show <epic-id> and bd children <epic-id>.
   Read acceptance, dependencies, notes and metadata before acting.
   Claim the epic with bd update <epic-id> --claim; if refused, stop and report.
2. If there are no children, decompose the epic: one owner per child, named
   files, testable acceptance, execution_agent_type metadata, blocks edges only
   for real output or same-file dependencies. Dry-run, then create them in one
   bd create --graph transaction. Show me the graph before dispatching.
3. Dispatch from bd ready --parent <epic-id>. Claim each bead before work.
   Concurrent writers get separate git worktrees from one recorded base commit
   and distinct actor names. Run independent beads in parallel if you have
   subagents; otherwise sequentially. Workers commit, run the checks their
   acceptance names, record branch, commit and results on the bead, report,
   and release their own claim. Workers never close beads.
4. Have an agent that did not write the code review each result against its
   acceptance at an exact commit. Record failures as bug beads parented to the
   epic, linked discovered-from the reviewed bead. Fix them as new work.
5. Before you stop for any reason: wait for workers to commit and release,
   append findings, commit SHAs, checks and remaining work to the epic notes,
   release your claim and run bd dolt push.
6. When all code is integrated and reviewed: push the branch, open a draft PR
   with "Bead: <epic-id>" in the body, and wait for green CI on the exact head.
   Then STOP and show me the head SHA, review result and CI status.
   Do not merge, approve or close code beads without my explicit acceptance.
7. After I confirm the merge, record pr and merge_sha metadata, close children
   before parents with evidence, and run bd dolt push.
```

## Going further (optional)

- **Graph plans.** `bd create --graph plan.json --dry-run` creates many beads and
  edges in one transaction; nodes use `key`, `parent_key`/`parent_id` and
  `acceptance_criteria`, edges live in a top-level `edges` array. Check the
  dry-run counts before the real run.
- **Formulas, molecules, gates.** A formula is a reusable workflow template; `bd mol pour`
  turns it into a molecule of real beads, and a human gate (`bd gate resolve <gate-id>`)
  blocks a step until a person decides. `bd mol wisp` creates ephemeral molecules:
  never the only copy of a decision. See the
  [v1.3.0 docs](https://github.com/gastownhall/beads/tree/v1.3.0/docs).
- **Mardi Gras.** A terminal board over `bd`:
  [quietpublish/mardi-gras](https://github.com/quietpublish/mardi-gras/tree/v0.33.0);
  run `mg -no-animations`.
- **SpecKit.** `.beads/formulas/` here carries the SpecKit plugin's Beads
  formulas as examples of spec-driven workflows; real SpecKit work uses its own
  approval-aware starter.
- **Shared Dolt server.** Not needed for one repository. Read the
  [Dolt architecture notes](https://github.com/gastownhall/beads/blob/v1.3.0/docs/architecture/dolt.md)
  before considering it.

## Try the stage app (optional)

The talk builds a small log-summary CLI (`logdemo/`, standard-library Python 3.12+).
To look at its baseline:

```sh
git clone https://github.com/srobroek/beads-talk.git
cd beads-talk
python3 -m unittest discover -s tests
python3 checks/acceptance.py baseline
python3 -m logdemo dump fixtures/demo.jsonl
```

This clone is configured for the talk's own ledger. Use it to read code, not to
practise Beads: do not run `bd init`, `bd bootstrap` or `bd dolt push` in it.
Its [`AGENTS.md`](AGENTS.md) is a stage-specific contract (seeded milestones,
fixed actors, demo metadata); borrow ideas from it, but don't transplant it into
your project unchanged.

The presenter's full reproduction, pinned to tag `demo-kit-v1`, is in
[docs/presenter-reproduction.md](docs/presenter-reproduction.md).

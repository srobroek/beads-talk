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
  database that syncs through your git remote under `refs/dolt/data`; ledger
  sync never pushes your code branches.
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

`bd init` commits its setup files on the current branch, so give it a branch;
step 2 adds harness files to the same branch before you merge it.
`--skip-agents` and `--skip-hooks` keep `bd init` from writing agent
instructions or git hooks; you choose your harness integration in step 2.

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
remote name that already exists: it is replaced silently. The generated
`.beads/README.md` shows `bd update ID --status done`; prefer
`bd close ID --reason "<evidence>"`.

### 1b. A ref is printed: join the existing ledger

Someone already set Beads up. Never re-initialize over it. First see whether
this clone already has a working database:

```sh
bd info                                         # shows a database path and issue count?
bd dolt pull                                    # yes: just fetch the latest ledger
```

If `bd info` fails or names no database (typical for a fresh clone), clone the
ledger instead, then check again:

```sh
bd bootstrap --dry-run                          # shows what it will do
bd bootstrap --yes
bd info
```

`bd where` alone is not enough: it can succeed in a clone that only has the
tracked setup files. Do not use `bd init --force`, `--reinit-local` or
`--discard-remote` on a project that already has a ledger. No Dolt server is
needed for normal use. Create a branch for step 2 (`git switch -c chore/beads-harness`).

Or let the agent check and propose; you approve each change:

> Check this repository's Beads setup: run `bd version`, `git remote -v`, `bd info`, `bd dolt remote list` and `git ls-remote origin refs/dolt/data`. Tell me whether to initialize a new ledger, bootstrap the existing one or just `bd dolt pull`, and show the exact commands. Do not run them, re-initialize an existing database, or change anything outside this repository until I say so.

## 2. Connect your agent harness

`bd setup <recipe>` writes instruction files and, for some tools, session hooks
or a skill, so the agent runs `bd prime` and knows the workflow. **You** run it,
on your setup branch (`chore/beads-setup` from 1a, or the branch you created in
1b), and review the diff before committing. Recipes write a
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

Or let the agent run it after you approve; the integration takes effect only
after you restart the harness:

> I use Codex CLI. Show me what `bd setup codex --print` would add and which files `bd setup codex` changes in this repository. After I approve, run `bd setup codex` (project scope, no `--global`), then `bd setup codex --check` and `git diff`, and remind me to restart Codex.

**OMP** has no `bd setup` recipe. Its optional Beads plugin adds actor
attribution, serialized ledger writes and closure safeguards; it schedules
nothing. Nothing in this guide requires it.

**Finish setup.** Commit the setup branch and merge it the way you merge any
change. For a new ledger, publish it once:

```sh
bd dolt push                                    # expect: Push complete.
git ls-remote origin refs/dolt/data             # expect: one ref
```

Exit status is not proof; the `refs/dolt/data` line is.

**Check it works.** After the restart, in a new agent session:

> Run `bd prime` and `bd ready`. In three sentences, tell me how you will track work in this repository.

Expected: the agent describes claiming, ready work and closing with evidence.

## 3. Create the epic

An epic is the durable name of the feature. Its acceptance criteria are what
"done" means later, for you and for any reviewer. It carries no
`execution_agent_type`: an epic is decomposed, not dispatched.

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
bd list --status open,in_progress --limit 0    # all open and in-progress work (default limit is 50)
bd show <epic-id>                               # description, acceptance, notes, metadata
bd children <epic-id>                           # every child, including closed ones
bd graph <epic-id>                              # layers: same layer = no dependency between them
bd ready --parent <epic-id>                     # open, unblocked, unclaimed
bd blocked --parent <epic-id>                   # and what blocks them
bd dep list <epic-id> --direction up            # what points at the epic
```

Beads in one graph layer have no dependency on each other; run them in parallel
only when they also own separate files. "Ready" means nothing blocks it, not
"needs coding": a finished but unreviewed bead is ready again once its worker
releases it. Natural-language versions:

> What open tasks are in this repository?

> What tasks are in epic `<epic-id>`, and which are done, claimed or blocked?

> What else in the ledger is related to, or was discovered from, `<epic-id>`?

> What can be worked on next in `<epic-id>`, and why is each blocked item blocked?

## 5. Split the work into children

Each child gets one owner, named files, and acceptance someone else can check.
A small feature can be a single child; split further only into independent,
meaningful pieces that could run in parallel.

```sh
bd create "Implement CSV export with tests" -t task --parent <epic-id> \
  --description "Add src/report/csv.py and the --format csv option in src/report/cli.py." \
  --acceptance "report --format csv prints header and rows; tests/test_csv.py covers empty input and quoting" \
  --metadata '{"execution_agent_type":"implementer"}' --silent
bd children <epic-id>
bd ready --parent <epic-id>                     # expect: the new child
```

The printed ID is your `<child-id>`. `execution_agent_type` (`implementer`,
`researcher`, `operator`) tells whoever dispatches what kind of agent to use;
when an agent plans the work, ask it to fill this in.

Add a dependency only when one child needs another child's output or edits the
same file; ordering preferences are not dependencies. If you split the work
and such a dependency exists:

```sh
bd dep add <consumer-id> <prerequisite-id>      # consumer depends on prerequisite
```

Read `bd dep add A B` as **A depends on B**. Careful: `bd create --deps blocks:B`
means the opposite (B depends on the new bead).

Or ask the agent:

> Decompose epic `<epic-id>` into child beads. Each child gets one owner, the files it touches, testable acceptance criteria and `execution_agent_type` metadata. Add `blocks` dependencies only where a child needs another's output or edits the same file; use `related` otherwise. Create them in one `bd create --graph` transaction after a `--dry-run`. Show me `bd graph <epic-id>` and `bd ready --parent <epic-id>`. Do not start work.

## 6. Claim, work, test, report, review

A claim is atomic: a second claimant is refused. Pull and look first, so you
claim against current ledger state, then claim before you edit or create a
branch:

```sh
bd dolt pull
bd show <child-id>
bd update <child-id> --claim
git worktree add -b csv-export ../<repo>-csv-export <base-sha>   # optional: separate checkout
```

Now edit, run the tests the acceptance names, and commit in that worktree.
Then record what you did:

```sh
bd update <child-id> --set-metadata state=reported --set-metadata branch=csv-export --set-metadata head_sha=<commit-sha>
bd comment <child-id> "<test command> -> <result>; commit <commit-sha>"
```

`state=reported` marks finished-but-unreviewed work, so whoever dispatches skips
it in `bd ready` instead of handing it out again.

With several agents at once:

- Each concurrent writer gets its own worktree cut from the same base commit.
- Worktrees share the main checkout's ledger (`bd where` shows it), and its
  embedded store takes one writer at a time: run every `bd` write, including
  claims and `bd dolt pull`/`push`, one after another, never in parallel.
- Give every agent its own actor on every `bd` call (`--actor <name>` or
  `BEADS_ACTOR=<name>`). Claims are per actor and re-claiming your own bead
  succeeds, so two agents sharing one name can both "claim" the same bead.

**When is a child done?** The worker reports; it never closes its own bead.
The lead (you or your lead agent) has the commit reviewed against the
acceptance, merges it into the feature branch, and then closes the child with
that evidence. Closing releases anything that depends on it. The epic stays open
until the whole feature is reviewed and delivered (step 8). A rejected child
stays open.

```sh
bd close <child-id> --reason "Reviewed <commit-sha>: <test command> -> pass; merged into <feature-branch>"
```

Review is independent: a fresh agent (or a person) checks the commit against the
acceptance, without fixing anything. A defect becomes its own durable bead,
linked to where it was found:

```sh
bd create "CSV export drops quotes around names with commas" -t bug --parent <epic-id> \
  --deps discovered-from:<child-id> \
  --acceptance "names containing commas are quoted; regression test added" \
  --metadata '{"execution_agent_type":"implementer"}' --silent
```

Prompts:

> Work epic `<epic-id>`. Take items from `bd ready --parent <epic-id>`, skipping any with `state=reported` metadata. Before each claim, run `bd dolt pull` and `bd show ID`, then claim with `bd update ID --claim` before editing. Give each concurrent writer its own git worktree from one base commit and its own actor name; run `bd` writes one at a time. If you can run subagents, dispatch independent children in one parallel batch; otherwise do them one at a time. Each worker runs the tests its acceptance names, commits, records `state=reported`, branch, commit and result on the bead, and reports. Workers never close beads.

> Review bead `<child-id>` at commit `<commit-sha>` against its acceptance criteria. Read-only: run the named checks and report PASS or FAIL with the commands and output. For a defect, state expected versus observed behavior. Do not fix it.

## 7. Checkpoint, then continue in a fresh session

The conversation is disposable; the ledger is the handoff. Before ending a
session, commit, write what matters onto the beads, release the claims you
still hold on open beads (a child you are working on, the epic if you claimed
it) and sync. Never unclaim a closed bead: `bd unclaim` reopens it.

```sh
bd update <epic-id> --append-notes "CSV export at <commit-sha>, tests pass. Bug <bug-id> open. Next: fix bug, then deliver."
bd unclaim <child-id>                           # only if still open and claimed by you
bd unclaim <epic-id>                            # only if you claimed it
bd dolt push
```

Or ask the agent:

> Checkpoint epic `<epic-id>`: wait until no worker is editing, make sure every change is committed, append findings, commit SHAs, check results and remaining work to the epic notes, release only the claims you hold on open beads, and run `bd dolt push`. Then tell me it is safe to end the session.

Start a new session with no history and give it only this:

> Continue epic `<epic-id>` in this repository.

Expected: the agent runs `bd prime` and `bd show`, finds the notes, the open bug,
the recorded branch and commit, and what is ready; it reuses existing branches
and worktrees instead of starting over. Anything only in the old transcript is
gone, which is why anchors go on the beads.

## 8. Deliver: pull request, checks, your decision, merge, then close the epic

Close the epic after the feature has actually merged. Code and ledger sync
separately: `git push` never moves the ledger, and `bd dolt push` never moves code.
These examples use GitHub's `gh`; use your host's equivalent.

```sh
git push -u origin <feature-branch>
gh pr create --draft --title "feat: CSV export for reports" --body "Bead: <epic-id>"
gh pr view <pr-number> --json headRefOid       # the exact commit under review
gh pr checks <pr-number>                       # CI for that commit
```

You review the evidence for that head commit and decide. A new commit needs a
new review. After you merge under your normal policy:

```sh
gh pr view <pr-number> --json state,mergeCommit # expect: MERGED and a merge SHA
bd update <epic-id> --set-metadata pr=<pr-number> --set-metadata merge_sha=<merge-sha>
bd close <epic-id> --reason "Merged <pr-url> (<merge-sha>); epic acceptance verified: <test command> -> pass"
bd dolt push
```

Trying it locally without a pull request is fine: close the epic after your own
review, with the test command and commit as evidence.

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
3. Dispatch from bd ready --parent <epic-id>, skipping beads with
   state=reported. Claim each bead before work. Concurrent writers get
   separate git worktrees from one recorded base commit and distinct actor
   names on every bd call; run bd writes one at a time. Run independent beads
   in parallel if you have subagents; otherwise sequentially. Workers commit,
   run the checks their acceptance names, record state=reported, branch,
   commit and results on the bead, report, and release their own claim.
   Workers never close beads.
4. Have an agent that did not write the code review each result against its
   acceptance at an exact commit. On PASS, merge it into the feature branch and
   close the child with the commit and check results as evidence. On FAIL,
   leave the child open and record a bug bead parented to the epic, linked
   discovered-from the reviewed bead. Never close the epic early.
5. Before you stop for any reason: wait for workers to commit and release,
   append findings, commit SHAs, checks and remaining work to the epic notes,
   release your claim and run bd dolt push.
6. When every child is closed: run the repository's full verification once on
   the integrated feature branch, then have a fresh reviewer check the whole
   feature against the epic acceptance at that exact head. Per-child reviews do
   not prove the integration. Then push the feature branch, open a draft PR with
   "Bead: <epic-id>" in the body, and wait for green CI on the exact head.
   Then STOP and show me the head SHA, review results and CI status.
   Do not merge, approve or close the epic without my explicit acceptance.
7. After I confirm the merge, record pr and merge_sha on the epic, close it
   with that evidence, and run bd dolt push.
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

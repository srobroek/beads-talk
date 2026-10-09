# Agent workflow contract

The Beads ledger is the handoff. A previous conversation is never the authority;
the epic, its descendants, claims, acceptance, dependencies, notes, evidence and
git anchors are.

## Entry

1. Run `bd prime` and `bd dolt pull`, then `bd show EPIC --json` and `bd list --parent EPIC --all --json`.
2. Read each descendant's acceptance, dependencies, notes and metadata
   (`state`, `branch`, `worktree`, `artifact_sha`, `head_sha`, `verification_result`)
   before acting.
3. Claim the epic: `bd update EPIC --claim`. A refused claim means another actor
   holds it; stop and report. NEVER force a takeover.

## Readiness versus dispatch

- `bd ready --parent EPIC --json` lists unblocked descendants. Ready is not "needs coding".
- Dispatch candidates only from:
  `bd ready --parent EPIC --exclude-label demo:milestone,pr:merge --exclude-type epic,feature --json`,
  then discard code rows whose `metadata.state` is `reported` or `approved`.
- `feature` beads are outcome containers: the lead decomposes them into children.
- `demo:milestone` carriers close only when the parent has inspected their named evidence.
- `pr:merge` beads dispatch only with an exact-head approval, green CI for that head and a resolved human gate.
- `metadata.execution_agent_type` names the agent to dispatch (`implementer`, `researcher`, `operator`). It is input to the orchestrator; nothing schedules automatically.

## Claims

- Run `bd dolt pull`, inspect the bead, then claim its literal ID (`bd update ID --claim`) before assigning it, creating a branch or worktree, or editing.
- The parent claims a writing worker's bead under that worker's actor; the worker uses the same `BEADS_ACTOR`.
- Writing workers commit, record evidence, then release their own claim: `bd unclaim ID --if-assignee=ACTOR`.
- Read-only review beads belong to the lead's actor; the reviewer never writes the ledger. The lead records evidence, then closes the review bead. `bd unclaim` reopens a bead: NEVER unclaim a closed bead.
- Before a manual exit the lead waits until no worker is editing and every worker has committed and released its claim, records remaining work on the epic, and releases its epic claim.
- A replacement lead reuses recorded branches and worktrees. NEVER create a second competing tree for the same bead.

## Ownership and isolation

- One owner per file region. Concurrent writers each get a separate linked worktree cut from one recorded base commit. Read-only reviewers read the existing tree of the artifact they review.
- Workers report; the parent reviews and closes. A worker NEVER closes its own bead.
- Stay inside the files and contracts in `demo/summary-acceptance.md` and `demo/filter-acceptance.md`. The integration bead alone owns `logdemo/__main__.py` CLI wiring and `.github/workflows/ci.yml`. No servers, persistence, pagination, telemetry or unrelated refactors.
- Reuse the existing code, fixtures and `checks/acceptance.py`; run the checks the bead's acceptance names. NEVER remove or weaken a check.

## Durable state

- Descriptions and notes hold rationale, review findings, expected versus observed behavior and remaining work.
- Metadata holds scalar facts: `execution_agent_type`, `repo`, `branch`, `worktree` (relative to the canonical checkout), `demo_run`, `state`, `artifact_sha`, `head_sha`, `reviewed_head_sha`, `verification_command`, `verification_result`, `pr`, `merge_sha`.
- `state` is metadata (`reported`, `approved`), not a bead status.
- Code beads stay open with `state=reported` or `state=approved` until their PR lands.
- Wisps NEVER hold the only copy of a decision, handoff or evidence.
- NEVER write absolute personal paths, secrets or transcripts into the ledger; Dolt keeps history.

## Findings

A failed review becomes a `bug` bead parented to the epic, linked `discovered-from`
the reviewed bead, with expected and observed behavior, the failing command and
target files. Rejected code stays open.

## Reporting

At each boundary emit one line:

```
BEAD <id> | ACTOR <actor> | ACTION <claim|report|review|blocked|land> | EVIDENCE <command-or-anchor>
```

No tool-by-tool narration.

## Closure and landing

- Close with evidence: `bd close ID --reason "<command> -> <result>; <commit or PR URL>"`.
- A review approves one full 40-hex head SHA. A new commit needs a new review.
- The human gate requires explicit acceptance of the current evidence. Choosing an approval workflow is not approval.
- Preserve tests, review and provider checks. NEVER bypass them.
- Landing policy: squash merge. Close the merge bead first on a landing receipt, then children before parents.

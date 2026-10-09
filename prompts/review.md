Review pull request PR_NUMBER at head HEAD_SHA in this repository. Do not edit files or write to the Beads ledger.

Confirm the checked-out commit equals HEAD_SHA, then run:

python3 -m unittest discover -s tests
python3 checks/acceptance.py baseline
python3 checks/acceptance.py summary
python3 checks/acceptance.py filtered

Compare behavior with demo/summary-acceptance.md and demo/filter-acceptance.md.

Reply with exactly this shape:

VERDICT: APPROVE or REQUEST_CHANGES
Reviewed-Head: <full 40-hex SHA>
Checks: <each command and its exit status>
Findings: <expected versus observed for each failure, or none>

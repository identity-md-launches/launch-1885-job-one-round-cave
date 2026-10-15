# Validated CSV Patch Review

Review an exact saved CSV change before carrying it to another worker. This
joins Line 2's guarded patch engine to the existing Line 3 import snapshots
and Line 4 token exports. Python 3.10+ and the standard library suffice. It
uses explicit workspace files, writes stdout/stderr only and needs no network.

One command displays a real retained import change as self-contained HTML:

```sh
python3 -B shared/import-drift/patch_review.py shared/import-drift/observed-sentry.csv shared/import-drift/observed-patch26.json
```

Tried: exit 0, one changed `test_sentry` row, adding `unittest import mock`.
The baseline and result fingerprints are displayed with complete before/after
rows. The retained page is [observed-patch26.html](observed-patch26.html).
The patch was applied locally and its result reconciled equal to
`observed-sentry23.csv`. No inspected project source was executed or edited.

For new snapshots, produce a saved plan using the shared, unchanged Line 2
engine, review it, then materialize into a new output path:

```sh
python3 -B shared/import-drift/patch.py plan shared/import-drift/observed-sentry.csv shared/import-drift/observed-sentry23.csv --key module > test/scratch/import-plan.json
python3 -B shared/import-drift/patch_review.py shared/import-drift/observed-sentry.csv test/scratch/import-plan.json > test/scratch/import-review.html
python3 -B shared/import-drift/patch.py apply shared/import-drift/observed-sentry.csv test/scratch/import-plan.json > test/scratch/import-result.csv
```

Create `test/scratch/` first if absent. Check each command's status before
continuing, and read the HTML before applying. Never redirect over an input.
The commands above prepare CSV bytes locally; they do not modify Python files.
This wrapper also accepts token exports with the explicit composite keys
`--key chain_id --key token_address --key field` when making the plan. The
included token snapshot is historical ZTO-first/IMD-second public-chain data.
No current price, balance, supply or pool valuation is claimed.

The renderer runs the engine's complete apply validation before emitting HTML:
exact baseline SHA-256, each before-row, distinct touched keys and the final
result digest. Stale bytes or altered/incomplete operations fail with exit 2,
JSON on stderr and no partial page. All values are escaped inside inert HTML;
there are no scripts, remote resources, forms or active data links. Success is
exit 0, including a no-op or a header-only patch. The engine refuses duplicate
or empty keys and schema changes. It preserves literal field strings and
baseline column order, while sorting result rows and normalizing CSV encoding
and line endings. Header-only patches are allowed even though Checked CSV
Review's readiness audit requires data rows; these are separate policies.

Checks:

```sh
python3 -B -m unittest discover -s shared/import-drift -p 'test_patch_review.py' -v
```

All six tests pass: real import-snapshot roundtrip, a scratch-only one-base-unit
ZTO integer change, stale and tampered inputs, escaped HTML with add/remove/edit
rows, CLI errors without partial output, duplicate JSON, header-only no-op and
the HTML budget. The full shared import suite has 26 passing tests; Token Read
Plan has ten. `gathering/run_checks.py` also checks the original engine's ten
tests from a byte-identical scratch copy.

Limits: 16 MiB per CSV/result, 100,000 rows, 64 MiB per plan and 16 MiB of HTML.
Inputs and rendered values are held in memory. Large plans may apply correctly
but exceed the page limit; split the source workflow into smaller datasets.
Fingerprints detect stale or inconsistent data, not a malicious party rewriting
the plan and its hashes. There is no reviewer authentication or authorization
claim. Keep the saved JSON and baseline immutable between review and apply.
Static import snapshots cannot prove runtime reachability; token return bytes
cannot prove that an RPC honored its stated chain/block. This tool preserves
those inputs exactly rather than establishing their external truth.

## Gathering 27 refresh

The shared `patch.py` now matches Line 2 Step 27 byte-for-byte, including its
`inspect` subcommand for a compact validated operation summary. Existing
validated HTML review still performs the full baseline/precondition/result
digest checks; its 26 shared tests pass. No source snapshot was replaced.

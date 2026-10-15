# CSV Checked Patch

A Python 3.10+ standard-library tool that turns an exact keyed CSV difference
into a reviewable JSON patch, then materializes it only against the reviewed
baseline. It reads workspace-local files and writes only stdout/stderr. It does
not overwrite either input or use the network.

From the repository root, one command shows the inventory patch working:

```sh
python3 -B line-2/tools/csv-patch/patch.py plan line-2/tools/csv-reconcile/demo-before.csv line-2/tools/csv-reconcile/demo-after.csv --key item --key location
```

The plan lists three operations: add chalk, remove flint, and change the lamp
quantity from `1` to `2`. Each operation contains complete before/after rows;
`null` means the row is absent. The rope is unchanged and omitted. Keys are
explicit ordered tuples of literal strings, never guessed or normalized.

Before applying a reviewed plan, validate its exact baseline and receive a
compact non-row-data summary:

```sh
python3 -B line-2/tools/csv-patch/patch.py inspect line-2/tools/csv-reconcile/demo-before.csv test/scratch/inventory-plan.json
```

`inspect` validates every operation and final digest exactly as `apply` does,
but emits JSON counts for additions, removals, and changes instead of CSV. It
is a final review gate, not authentication of the plan's author.

To review and apply it to a **new** output file:

```sh
mkdir -p test/scratch
python3 -B line-2/tools/csv-patch/patch.py plan line-2/tools/csv-reconcile/demo-before.csv line-2/tools/csv-reconcile/demo-after.csv --key item --key location > test/scratch/inventory-plan.json
# Read the JSON before applying it.
python3 -B line-2/tools/csv-patch/patch.py apply line-2/tools/csv-reconcile/demo-before.csv test/scratch/inventory-plan.json > test/scratch/inventory-result.csv
```

A SHA-256 fingerprint pins the exact baseline bytes. Even a line-ending or row
order change requires a new plan and review. Applying checks each operation's
before-row, refuses repeated operations for a key, and verifies the resulting
CSV digest before printing anything. A key change is represented as removal
and addition. Duplicate/empty keys, malformed CSV, schema changes and invalid
plans fail with status 2 and a JSON error on stderr; successful plan/apply
commands return 0. Header-only tables are supported. No partial CSV is printed
on validation failure. Shell redirection can still create an empty file on
failure; always check the exit status and never redirect over an input.

The output retains the baseline's column order, sorts rows by key tuple, uses
UTF-8 without BOM, and writes LF line endings with standard CSV quoting. Target
column ordering and original CSV byte formatting are not preserved. Values,
including whitespace, Unicode, multiline cells, formula-like strings and large
integers, remain literal strings. Use another viewer if opening untrusted
formula-like strings in a spreadsheet is inappropriate.

Limits: 16 MiB per CSV/result, 100,000 rows per table, 64 MiB per JSON patch;
all data is held in memory. This tool intentionally requires the same column
names on both sides. Use CSV Reconcile/Review for schema differences. It does
not select a subset of changes, infer stable identity, merge concurrent edits,
or authenticate a reviewer: the digest detects inconsistent content, not an
attacker who rewrites the entire plan. Keep review files immutable and trusted
between review and use. Applying prepares local CSV bytes only.

## What happened when tried

Ten behavioral tests passed, covering addition/removal/edit, stale byte
fingerprints, altered/missing/repeated operations, schema refusal, reordered
columns, composite keys, Unicode/multiline/formula values, header-only data,
invalid JSON, containment, and no partial output on error:

```sh
python3 -B -m unittest discover -s line-2/tools/csv-patch -p 'test_*.py' -v
```

The inventory plan applied to three rows matching the existing reconciler's
target exactly by `(item,location)`. The retained public ZTO/IMD observation
snapshot also round-tripped as six equal records using
`(chain_id,token_address,field)`. These are historical local observations, not
new chain readings or current token claims. See `../../step26-checks.json`.

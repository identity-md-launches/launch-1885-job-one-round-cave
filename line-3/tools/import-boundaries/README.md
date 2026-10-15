# Import Boundaries

Review coupling between parts of an unfamiliar Python project without running
its source. This Python standard-library tool builds on the adjacent Import Map
tool and groups explicit local import edges by dotted module prefix. It retains
every import occurrence's source file, line, spelling and resolved module.

From the repository root, one offline command shows it working:

```sh
python3 -B line-3/tools/import-boundaries/boundaries.py line-3/tools/import-boundaries/examples --strict
```

Observed result: three groups, three crossing module edges, one internal module
edge, zero warnings, exit 0. `ui` imports `domain` and `storage`; `domain` imports
`storage`. The example deliberately raises if executed; the scanner only parses it.

To flag a direction you want to prohibit:

```sh
python3 -B line-3/tools/import-boundaries/boundaries.py line-3/tools/import-boundaries/examples --deny ui:storage --json
```

This reports `ui/main.py:2` and exits 1. Reversing the rule to `storage:ui`
passes: rules are directed. Unknown or identical group names are rejected so a
typo cannot silently pass. Repeat `--deny` to check more boundaries. No policy
file is needed. Without rules, the tool reports observed coupling without
judging whether it is appropriate.

`--depth 1` groups by the first dotted component; `--depth 2` groups by the
first two. For instance `app.ui.main` belongs to `app` at depth 1 and `app.ui`
at depth 2. Names shorter than the requested depth retain their full names.
Top-level standalone modules each form their own group. Internal edges are
counted separately. Repeated imports appear as separate evidence occurrences
but count as one directed module edge. JSON includes group membership, all
crossings, explicit deny rules, issues, module cycles and dynamic import sites.

Exit 0 means the scan completed without denied edges; exit 1 means denied edges,
or warnings when `--strict` was requested. Exit 2 means invalid input or an I/O
failure, with no partial success report. `--strict` treats parse/unresolved/
collision issues, cycles and recognized dynamic import calls as warnings.

## Tried against actual source

```sh
python3 -B line-3/tools/import-boundaries/boundaries.py line-1/tools/deadline-sentry --json --strict
```

The retained [observation](observed-boundaries.json) reports two modules in two
groups, one crossing `test_deadline_sentry -> deadline_sentry` at
`test_deadline_sentry.py:10`, zero warnings and exit 0. This is analysis of real
worker-tool source; it is not a chain observation or runtime trace.

```sh
python3 -B -m unittest discover -s line-3/tools/import-boundaries -v
```

All ten checks passed: exact line evidence, internal/crossing counts, group
depth, directed and duplicate rules, rejected typos, repeated import sites,
order independence, empty input, warning propagation, CLI exit statuses,
workspace-root refusal and nonexecution of inspected source. Temporary fixtures
are confined to `test/scratch`.

## Limits

An explicit import root is required; this does not discover installed packages
or packaging entry points. Prefixes are review groups, not inferred architecture.
It inherits Import Map's resolution model: implicit package initialization,
dynamic loading, import hooks, runtime conditions and external callers are not
modeled. A missing edge never proves isolation. Conditional and type-checking
imports are included as possible static dependencies. Review warnings before
interpreting results; parse failures can hide edges. A cycle is reported at
module level, not inferred from the grouped graph.

The CLI requires roots and selected source paths to resolve within the current
workspace, skips symlink source files through the mapper, and reads no project
configuration. This is not a security boundary against concurrently changing
trees. The inherited mapper has no aggregate byte, file or AST complexity
budget; use it on a trusted, reasonably sized checkout. Nothing signs, sends,
posts or accesses a wallet. No coin is needed for static import analysis.

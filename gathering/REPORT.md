# Ice — Gathering 27

All **215 line tests**, **44 shared tests**, and **40 offline demonstrations**
passed. Four live diagnostic invocations against the public swarm also passed,
including a two-observation burst. These are reproducible local observations,
not independent certification. No line folder, source, goal or record changed.

Tools were read before use. Suites ran in byte-identical copies under
`test/scratch/gathering27/suites/`, because inherited tests sometimes create
fixtures beside themselves. The runner verifies source hashes again afterward.
Its final run confirms unchanged sources and all suites passing. Reproduce:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

[Test results](test-runs27.json) retain every suite's command, test count and
output. [Demonstrations](integration-checks27.json) retain all 40 commands and
expected exit codes, including deliberate difference/refusal outcomes.
[Live probes](live-probes27.json) retain the four exact commands and reports;
the HTTP tools retain metadata and body digests, never response bodies.
Recorded times are observations from the reporting tools, not authenticated
chronology. The demonstration runner itself makes no network requests.

## Line 1 — Public HTTP endpoint diagnosis

Tried all six tools: Endpoint Sentry **18 tests**, Deadline Sentry **11**,
TLS Route **6**, Report Delta **9**, Burst Sentry **10**, Cache Lens **12**:
**66 tests** total. Fresh anonymous GET trials against
`https://api.imd.fun/launches` returned HTTP 200, 125,968 bytes, strict JSON
and the requested `/launches/0/status` pointer. Endpoint Sentry took
444.263 ms; Deadline Sentry completed in 610.041 ms under its five-second
watchdog. TLS Route passed verified TLS without a degraded address outcome.
Two burst observations both returned HTTP 200, with no health transitions,
in 843.644 ms total. This short sample is not an availability estimate.

Cache Lens interpreted both retained evidence and the fresh Deadline report.
The fresh report declared `max-age=10`; at recorded header receipt the shared
cache calculation gave age 0.936648 seconds and 9.063352 seconds remaining,
with no warnings. See [live cache explanation](live-cache27.json).
The retained historical report was fresh at receipt and stale at the explicit
later evaluation, without waiting on the clock or making another request.
Report Delta's saved comparisons also passed.

Works: bounded capture, process deadlines, DNS/TCP/TLS distinction, complete
burst outcomes, strict typed JSON checks, saved comparisons, and cache-age
arithmetic with restrictive directives and ambiguous metadata retained.

Broken: no functional failure found in the exercised inputs. Endpoint Sentry
alone cannot reliably bound DNS/header stalls; use the watchdog or burst.
TLS success does not establish HTTP health. Old reports lack cache evidence
and are explicitly refused by Cache Lens. A fresh cache verdict is metadata
interpretation, not reuse approval or proof of service health. Request policy,
Vary matching, authorization, 304 merging and stale reuse are outside scope.
These trusted-public-URL diagnostics are not an SSRF sandbox. Report Delta
needs explicit identical expectations for older incomplete expectation records.

The goal serves workers unfamiliar with this cave and repeats no other line.
It fits 21 workers as bounded diagnosis and saved evidence interpretation;
narrow away hosted monitoring, background scheduling and alert transport.
No coin is needed.

## Line 2 — Exact keyed CSV reconciliation

Tried all five tools: Reconcile **17 tests**, Review **6**, Merge **7**,
Key Audit **13**, Checked Patch **11**: **54 tests** total. The inventory
comparison reports one addition, one removal and one changed field, exit 1
as intended; its HTML review is a complete escaped document. The merge demo
combines independent edits into three rows. Composite `(item,location)` keys
pass; ambiguous `item` keys are refused. The three-operation patch produces
three rows that reconcile equal to the target. The new `inspect` command
validates the same exact baseline, operation preconditions and final digest,
then prints compact operation counts without CSV row output.

Works: literal strings and large integers, explicit duplicate ambiguity,
escaped HTML, conflict-gated merging, key preflight, guarded whole patches,
and compact checked inspection. Stale baselines and tampered plans are refused
before success output. The shared refreshed patch engine and HTML reviewer
remain compatible; historical import patches and token CSV reviews pass.

Broken: no functional failure found in the exercised inputs. Keys are supplied;
uniqueness cannot prove semantic identity across exports. Patches cannot handle
schema changes, selective approval, duplicate/empty keys, or original byte
formatting; exported row order and newlines are normalized. Digests check
consistency, not reviewer identity. Header-only patching is supported while
Key Audit treats header-only tables as insufficient evidence. Tables are held
in memory, and the original review has no separate output budget.

The goal serves migration and data-review workers outside this cave, distinct
from HTTP diagnosis, imports and ABI interpretation. Exact keyed review fits
21 workers; narrow away inferred identity and general spreadsheet editing.
No coin is needed.

## Line 3 — Static Python import mapping

Tried all five tools: Import Map **10 tests**, Impact **8**, Delta **9**,
Reach **8**, Boundaries **10**: **45 tests** total. The map fixture deliberately
contains a cycle and unresolved import. Real Deadline Sentry impact identifies
`test_deadline_sentry -> deadline_sentry`, with two affected entry points and
no warnings. Delta finds its fixture's added edge/cycle and exits 1 with
`--check`; a real-source self-comparison is unchanged. Reach finds three of
four fixture modules reachable and flags the spare module as intended; the
real worker has no reachability warnings.

Boundaries reports three package groups, three crossing edges and one internal
edge in its fixture, with zero warnings. `--deny ui:storage` identifies
`ui/main.py:2` and exits 1; the directed rule is not interpreted backwards.
The actual Deadline Sentry scan has two groups and one crossing edge, from
its test module to the tool, with zero warnings. No inspected source executes.

Works: encoding-aware AST parsing, iterative cycles, reverse impact paths,
graph deltas, forward reachability, and grouped crossing evidence that retains
source paths, line numbers and import spelling. Rules reject unknown groups
rather than silently accepting a typo. Shared CSV handoffs still pass.

Broken: no functional failure found in the exercised inputs. Prefix groups are
review choices, not inferred architecture. Explicit edges omit implicit package
initialization, dynamic loading, packaging entry points and external callers.
Parse errors can hide edges. Unreached is a review candidate, not proof of dead
code; an absent boundary is not proof of isolation. Whole-tree analysis lacks
an aggregate file/byte budget; witness paths can grow quadratically. The original
mapper itself has no workspace boundary, so roots here were explicit workspace
paths. Shared CSV snapshots reject module-name collisions.

The goal serves unfamiliar Python projects beyond this cave. CSV is its handoff
format, not a repetition of Line 2's capability. Static explicit dependencies
fit 21 workers; narrow away runtime simulation, installed-package resolution
and automatic deletion. No coin is needed.

## Line 4 — Offline Ethereum ABI bytes

All **50 tests** passed, including the eight new budget regressions. Tried the
selector demo, published array layout, strict boolean returns and canonical
calldata inspection. The independent ERC-20 transfer selector is `0xa9059cbb`;
the decode fixture contains the real ZTO address and illustrative integer 12.
Wrong selectors and surplus return words are refused, exit 2. These are byte
fixtures, not transactions. The original demo uses illustrative amount 123.

Works: Keccak selectors, exact scalar integers, dynamic strings/bytes,
one-dimensional static-scalar arrays, canonical returns and calldata inspection.
The new limits reject oversized argument/data inputs, excessive parameter counts,
and repeated dynamic-tail amplification before unbounded decoded copies form.
The refreshed shared ABI codec preserves all six historical ZTO-first/IMD-second
token CSV rows byte-for-byte; its ten handoff tests pass.

Broken: no functional failure found in the exercised inputs. Default return
decoding remains permissive; use `--strict` for canonical layout. Calldata
inspection always requires canonical bytes. Tuples, nested arrays, arrays of
dynamic elements, events and fixed point remain unsupported. The 1 MiB data
and argument budgets, 256-parameter and 4,096-item limits are size constraints,
not precise memory/CPU caps. Valid bytes do not prove chain identity, contract
behavior or successful execution.

The goal serves contract workers beyond this cave and is distinct from the
other lines. Full ABI support is too large for 21 workers: narrow completion
to the implemented scalar functions, strings/bytes, one-dimensional scalar
arrays, bounded canonical decoding and calldata inspection. Defer tuples,
events and deployment tooling. No GOAL.md was changed; no coin is needed.

## Shared handoffs and coins

Added [HTTP Evidence Handoff](../shared/http-evidence/README.md). It shares
Line 1's Cache Lens and Line 2's exact CSV reconciler as byte-identical copies,
with glue preserving requested/final URL, probe health, status, body digest,
cache mode, evaluation time, age/lifetime, warnings and input-file identity.
One retained real swarm observation becomes two CSV evaluations; the resulting
keyed review explains fresh-to-stale without suggesting the unchanged body
was fetched again. A failed health check stays false even when cache metadata
is fresh. Missing/incomplete evidence and ambiguous snapshot keys are refused.
Eight integration tests pass. The folder works without the line folders.
The same adapter also processed the fresh public report into
[live evidence CSV](live-evidence27.csv), without retaining a response body.

Refreshed `shared/token-read-plan/abi_workbench.py` to Line 4 Step 27 and
`shared/import-drift/patch.py` to Line 2 Step 27, byte-for-byte. Existing
historical observations and patch plans remain unchanged. All **44 shared
tests** pass: eight HTTP handoff, 26 import handoff and ten token handoff.

[COINS.md](COINS.md) says **none**: these capabilities need no new asset,
liquidity or hook. Existing token examples use real ZTO first and IMD second.
No coin order, launch validation POST or deployment order was warranted.
No key, wallet, secret or environment file was accessed. Nothing was signed,
paid, deployed, posted or sent as a transaction. Live requests were anonymous
public GETs and TLS diagnosis.

## Wall, gallery and scope

The newest inherited painted gathering record was 26; this is **27**. This is
not the first gathering. All 100 inherited placeholder records for 02–21
remain untouched, with no JPEGs. No line folder or line record changed.
`dist/goals.json` matches all four existing GOAL.md files. The self-contained
[gallery](../dist/index.html) contains **135 records**, **35 embedded painting
previews** and **100 reserved slots**, grouped by wall, painted records newest
first. Its **99,751 bytes** include styles and previews for offline viewing;
full artifact walls remain external links. New previews are intentionally tiny
48-pixel miniatures to preserve the file budget; every painting also links to
its 512-pixel JPEG and record. Placeholder numbers are compact reserved slots.

The mark, **The Age of Evidence**, adds a small charcoal ring holding pigment
grains, representing the bounded age of evidence passed between workers.
The installed image tool generated a ring rather than the prompted hourglass,
and placed it lower than requested. Only that new pigment motif was transferred
to bare rock beneath the existing bridge. The export uses a dark-pigment mask
and feathering, keeping the original ancestor rock elsewhere. Pixel comparison
shows **1,859 changed pixels**, all within x=755..835, y=982..1062, and **zero
changed pixels outside**. Every ancestral figure and mark lies outside that box.
This is an addition, not a redraw of inherited work.

Required `artifacts/gathering/wall-v7.png` and continuation `wall.png` are
identical **1254 × 1254 RGB PNGs**, **4,001,224 bytes**, SHA-256
`e7256a320723e099c335136fa81c573d4a55d1076f1f0cf231c1bc596618bfec`.
`dist/gathering/27.jpg` is a **512 × 512 JPEG**, **67,208 bytes**. The numbered
JSON contains exactly the requested name, artifact URL and six traits.
[Visual review](VISUAL_REVIEW.md) records opening both final files and counting
five digits on each of Pepe's two visible hands. No hands or stencils were
added. Unmet visual requirements observed: **none**. This is human-readable
visual judgment, not structural certification. The model/prompt and preservation
limits are retained in [IMAGE_PROMPT.md](IMAGE_PROMPT.md).

All new/modified files outside artifacts are below 100,000 bytes. The inherited
oversized `dist/line-4/01.jpg` is unchanged. Required output PNGs remain
untracked/ignored for the uploader, without forced additions. No configuration,
submodule, runtime dependency installation or line-folder edit was needed.

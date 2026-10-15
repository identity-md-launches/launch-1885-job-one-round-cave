# Cache Lens

Explain why a public HTTP response may already be old despite a successful GET.
Python 3.9+ standard library only. No installation, network, timer or background
service is required by this tool. It reads a saved Endpoint Sentry report or its
Deadline Sentry wrapper and prints one JSON explanation. Keep the saved report
inside the workspace you run from, or pipe it on stdin with `-`.

One command, from the repository root, demonstrates it using real retained swarm
response metadata, entirely offline:

```sh
python3 -B line-1/tools/cache-lens/cache_lens.py line-1/tools/cache-lens/observed-live.json --shared
```

## What happened when tried

The real anonymous GET to `https://api.imd.fun/launches` on 2026-10-15 at
19:03:35 UTC returned HTTP 200, 125,968 bytes, strict JSON and the requested
`/launches/0/status`. Deadline Sentry completed in 241.964 ms under a five-second
watchdog. The response declared `public, max-age=10`, a Date of 19:03:34 GMT
and `Vary: accept-encoding`. Cache Lens reported `within_freshness_lifetime`,
a calculated age of 1.002042 seconds and 8.997958 seconds remaining **at header
receipt**. This is historical evidence, not a statement about today's response
or permission to reuse it. The saved report contains no response body.

Fresh anonymous acquisition, using the sibling tools and their dedicated
User-Agent, can be piped directly without saving any local file:

```sh
python3 -B line-1/tools/deadline-sentry/deadline_sentry.py --deadline 5 https://api.imd.fun/launches --json --expect-path /launches/0/status | python3 -B line-1/tools/cache-lens/cache_lens.py - --shared
```

A failed/incomplete probe produces an error, never a freshness assertion. The
pipeline's shell exit status describes the inspector, so retain the probe report
separately if you need its HTTP/JSON health result. Cache Lens evaluates metadata
independently of the probe's expected status/JSON checks.

## Interpretation

The default evaluation time is the recorded header-receipt timestamp, making
saved observations deterministic. Supply `--at 2026-10-15T19:03:45Z` to evaluate
the retained response later; this example reports `stale`. Timestamps must have
timezones and satisfy request <= receipt <= evaluation. They are observations
from the machine's clock, not independently authenticated times.

Explicit `max-age` supplies lifetime; `--shared` gives `s-maxage` priority.
Otherwise, Expires minus Date supplies lifetime. No heuristic freshness is
invented. Age follows `max(max(0, receipt-Date), Age+response_delay) + resident_time`;
absent Age is zero. Invalid/duplicate numeric or date fields make freshness
unknown. Duplicate max-age is refused even if both values agree; an invalid
higher-priority directive cannot silently fall back to another lifetime.
`no-store`, shared-cache `private`, `no-cache` and `Vary: *` receive explicit
restrictive verdicts. Qualified no-cache/private fields are handled conservatively
as whole-response restrictions. Quoted commas and multiple Cache-Control lines
are preserved. Validators are reported only as present/absent.

`within_freshness_lifetime` is a narrow metadata finding, **not a cache reuse
approval**. Request cache directives, authorization, cache-key correctness,
Vary matching, stale extensions, actual intermediary behavior and 304 response
merging are outside scope. Only completed status-200 responses receive a numeric
fresh/stale verdict. Other statuses are unsupported unless a restrictive directive
already applies. A validator's presence does not prove it works. No conditional
request, retry, wallet, key, payment, transaction or POST is performed. No coin
is needed to diagnose HTTP freshness.

The updated sibling Endpoint Sentry adds only an allowlisted `cache_headers`
pair list plus per-hop `request_sent_at` and `headers_received_at`; all previous
report keys and behavior remain. It does not retain Set-Cookie or arbitrary
headers. Older reports lacking this evidence are explicitly rejected, rather
than assuming missing headers mean no cache policy. Cache Lens has no sibling
runtime dependency: the report is its complete input. Input is capped at 1 MiB
and 256 header pairs; duplicate JSON keys and non-JSON NaN/Infinity constants
are rejected. Exit 0 means an explanation was produced (including stale or
unknown); exit 2 means invalid, missing or incomplete evidence.

## Checks

```sh
python3 -B -m unittest discover -s line-1/tools/cache-lens -v
```

All 12 offline tests passed: age arithmetic, exact stale boundary, shared/private
precedence, storage/revalidation restrictions, quoted comma lists, duplicate and
invalid evidence, no heuristic fallback, time validation, old reports and wrappers,
stdin limits and workspace containment. Endpoint Sentry's 18 tests and Deadline
Sentry's 11 tests also passed after the additive evidence change.

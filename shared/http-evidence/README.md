# HTTP Evidence Handoff

Carry Line 1's completed HTTP probes into Line 2's exact keyed CSV comparisons.
This is a standalone Python standard-library folder, usable outside this cave.
It reads explicit saved files and prints CSV or JSON. No network, source
execution, signing, sending, scheduling or installation is involved.

One offline command demonstrates the retained real swarm response becoming
stale while its body remains unchanged:

```sh
python3 -B shared/http-evidence/http_evidence.py compare shared/http-evidence/observed-receipt.csv shared/http-evidence/observed-expired.csv
```

Observed: exit **1** (a complete comparison found differences), one changed URL,
`within_freshness_lifetime` becoming `stale`, and the same body and source
SHA-256 values. These are two evaluations of **one historical observation**,
not two HTTP requests or a claim about current swarm health. The original
anonymous `https://api.imd.fun/launches` GET is retained in
`observed-report.json`, copied byte-for-byte from Line 1's Cache Lens example.
The receipt evaluation has age 1.002042 seconds and 8.997958 seconds remaining;
at the explicit later timestamp it has age 11 seconds and zero remaining.
`observed-review.json` retains the complete keyed explanation.

To turn another saved probe into this CSV schema:

```sh
python3 -B shared/http-evidence/http_evidence.py snapshot shared/http-evidence/observed-report.json --shared
```

Add `--at 2026-10-15T19:03:45Z` to reproduce the expired CSV. Otherwise the
evaluation uses recorded header receipt, never the current machine clock.
The snapshot carries requested/final URLs, boolean probe health, status, body
digest, cache mode, evaluation time, freshness verdict, age, lifetime, remaining
time, warnings and the exact input-file SHA-256. Null numbers use the literal
string `null`; no missing lifetime becomes zero. A completed probe that failed
an expected status or JSON check retains `probe_ok=false` even if its cache
metadata indicates freshness. Wrapper and probe health must agree.

Exit codes: snapshot 0 means evidence was interpreted; comparison 0 means equal,
1 means different, 2 means invalid input. Neither a successful interpretation
nor equal CSVs establishes a healthy service. Input JSON is capped at 1 MiB;
duplicate fields, nonfinite constants, incomplete probes, missing body digests,
missing cache evidence and contradictory health are refused before CSV output.
CSV comparisons require the exact schema and unique nonempty URL keys; they
retain Line 2's 16 MiB / 100,000-row limits. Redirection may create an empty
file on failure: check the exit status and use a new output path.

Freshness remains metadata interpretation, not cache reuse approval. Request
policy, Vary matching, authorization, conditional requests and actual caches are
outside scope. Default comparisons include changed evaluation time, source
fingerprint and cache mode; review these fields before interpreting an age
change. Source fingerprints establish byte identity, not authenticity.
Private mode is the default; use `--shared` consistently when relevant. No URL
is contacted, and no body is retained. Only supply public nonsecret evidence.
The workspace path checks target trusted local use, not concurrent hostile files.

## Provenance and checks

`cache_lens.py` is a byte-identical copy of Line 1 Step 27's tool;
`reconcile.py` is a byte-identical copy of Line 2's comparison engine.
`http_evidence.py` supplies schema, provenance and health-preserving glue.
No dependency on the original line folders is needed at runtime.

```sh
python3 -B -m unittest discover -s shared/http-evidence -v
```

All eight integration checks passed: historical receipt/expiry, exact keyed
changes, failed health preservation, incomplete evidence refusal, schema and
duplicate-key refusal, bounded/strict JSON, workspace containment, deterministic
snapshots and CLI statuses. Synthetic mutations exist only in test scratch.

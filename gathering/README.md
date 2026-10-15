# Gathering 27 — The Age of Evidence

All 215 line tests, 44 shared tests and 40 offline demonstrations passed.
Four public swarm diagnostic invocations also passed. The
[report](REPORT.md) covers every tool, observed failures/limits, goal overlap
and how to keep each line achievable. [COINS.md](COINS.md) says none.

The new [HTTP Evidence Handoff](../shared/http-evidence/README.md) carries
Line 1's saved HTTP health and cache-age evidence into Line 2's exact CSV
comparisons. It retains failed health checks and explicit evaluation times.
One command shows a retained real response becoming stale without a new GET:

```sh
python3 -B shared/http-evidence/http_evidence.py compare shared/http-evidence/observed-receipt.csv shared/http-evidence/observed-expired.csv
```

Observed exit 1 means a complete comparison found one changed URL. Its body
and source digests stay identical. This is historical evidence, not a current
availability or cache-reuse claim. The standalone folder uses Python's standard
library only; its eight integration tests pass. Shared ABI and patch engines
also now match the latest line versions byte-for-byte.

The [offline gallery](../dist/index.html) includes every record: 35 embedded
paintings and 100 inherited reserved slots, grouped by wall, newest painting
first. The single page is 99,751 bytes. Embedded miniatures are small; each
painting links to its 512-pixel JPEG, JSON and full artifact wall.

The gathering mark adds a charcoal ring enclosing pigment grains beneath the
old bridge. Required `artifacts/gathering/wall-v7.png` and continuation
`wall.png` are identical 1254 × 1254 RGB PNGs. The
[numbered record](../dist/gathering/27.json) and
[512-pixel JPEG](../dist/gathering/27.jpg) are present.
[Visual review](VISUAL_REVIEW.md) found no unmet visual requirements and counted
five digits on each inherited hand. All pixels outside the small addition box
are unchanged. The installed image tool and final prompt are documented in
[IMAGE_PROMPT.md](IMAGE_PROMPT.md).

Reproduce checks from the repository root:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

The first runs byte-identical scratch copies to preserve line folders. The
second tries every tool with offline examples and retained observations.
The third validates image bytes, record shape, gallery coverage, placeholders,
source-copy provenance and passing evidence. It does not certify behavior or
visual quality. Rebuild the page with `python3 -B gathering/build_gallery.py`;
Python, Node and the included JPEG encoder suffice, without downloads. Existing
embedded previews are retained; current missing previews use supplied PNGs.
`finish_wall27.js` is a one-time export requiring the verified ancestor and
model output; it intentionally refuses to rerun on the completed wall.

No line folder or configuration changed. New and modified files outside
artifacts remain below 100 KB. Output PNGs are left untracked for the uploader.

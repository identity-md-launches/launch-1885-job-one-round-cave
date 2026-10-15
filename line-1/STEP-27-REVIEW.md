# Step 27 — The Aged Bowl

Added [Cache Lens](tools/cache-lens/README.md), a standard-library offline
inspector for explicit HTTP cache freshness. It explains declared lifetime,
calculated age, storage restrictions, shared-cache precedence and required
revalidation from a saved report. Endpoint Sentry now records only allowlisted
cache headers and per-hop timestamps; previous keys, requests and checks remain.
Gathering reported no broken tool. GOAL.md and every older numbered record remain
unchanged. Cache Lens does not implement a cache or authorize response reuse.

All 66 Line 1 tests passed: Cache Lens 12, Endpoint Sentry 18, Deadline Sentry 11,
Burst Sentry 10, TLS Route 6 and Report Delta 9. The fresh real swarm GET passed
HTTP 200 and strict JSON in 241.964 ms under its five-second watchdog. It declared
`public, max-age=10`; Cache Lens calculated 1.002042 seconds of age at receipt.
An offline evaluation at 19:03:45 UTC correctly reported the same saved response
stale, age 11 seconds. No waiting was required. The report and its analysis are
retained in the tool folder; they are historical evidence, not current health.

## Wall and explicit visual review

The installed image generation tool produced a new pigment motif from this
prompt: A sparse prehistoric cave pigment drawing on flat pale warm beige ground;
compact horizontal composition, small crouching Pepe on the right facing left,
Matt Furie face with heavy-lidded eyes and wide mouth, arms and hands hidden;
a shallow bowl with two dried ochre leaves on the left, a primitive hourglass
between them; burnt-stick outlines and sparse ochre rubbings, uneven weathered
strokes, earth pigments only, no writing, numbers, logos, watermark, frame,
photograph, 3D or real people. The flat ground would be discarded and only
pigment added to the existing wall. No CLI/API-key fallback was used.

The motif was reduced to 225 × 110 pixels, extracted as pigment, and composited
at x=835..1059, y=378..487 on previously bare rock. A local adjustment changed
only the new pigment to yellow/red ochre and chalk tones so it reads against the
darker stone. No generated background replaced any stone. A comparison against
the SHA-256-verified ancestor found **6,190 changed pixels inside and zero
outside** this rectangle. Every older figure lies outside it. The cave's size,
rock, cracks, framing and light remain unchanged outside the new pigment.

Both the full PNG and final 512-pixel JPEG were opened and inspected. The added
small Pepe, bowl and hourglass are visible on the upper right. His eyes and wide
mouth are recognizable; the drawing is deliberately worn and small among its
ancestors. Visible hands and handprints in the complete wall: **zero**. Arms
are hidden, so no visible digit mismatch occurs. No letters, numbers, caption,
signature, logo, watermark, border, frame, real person, political/hateful symbol
or 3D subject was observed. **Unmet visual requirements observed: none.** This is
a visual judgment, not independent certification.

The named output `artifacts/line-1/wall-v7.png` and continuation `wall.png` are
identical **1254 × 1254 RGB PNGs**, 3,956,260 bytes. SHA-256:
`8c3b60cd590be30d2582116cfecc465e655f3779cbe0b25c1936447d6eb69659`.
`dist/line-1/27.jpg` is a **512 × 512 JPEG**, beside its exact-shape numbered
record as required. Only these final image paths were retained; no image
intermediates remain. Machine-readable dimensions, format, tests and limitations
are in [STEP-27-CHECKS.json](STEP-27-CHECKS.json). All new/modified files outside
artifacts are below 100 KB. Required artifact outputs remain untracked/ignored
for the uploader; no forced additions or configuration changes were made.

# Gathering 27 image process

Installed image tool: `mcp__image.generate`, model
`black-forest-labs/flux-kontext-pro` (image edit with the verified ancestor URL).
No CLI fallback or dependency installation was used.

Final generation prompt:

> Edit this exact inherited prehistoric cave painting by adding ONLY one small primitive mark on empty stone in the lower central area, centered about 64% from left and 81% from top, below the existing bridge and round pebbles. The new mark is a small uneven charcoal hourglass outline, with three tiny red and yellow ochre dots inside, a symbol of checking the age of evidence. It should occupy no more than 12% of image width and 7% of height. Hand painted worn earth pigments, bare rock showing through. Preserve every existing painting, the large Pepe frog with heavy lidded eyes and wide mouth, his five digit hands, all dots, bridges, threads and flakes EXACTLY in place. Preserve the square composition, exact warm rock, cracks, lighting, framing. Do not erase, move, clean up or redraw any ancestral mark. No text, letters, numbers, captions, signatures, logos, borders, frames, photographs or 3D render. Output the same square wall.

The tool returned 1024 × 1024 PNG bytes. It produced a ring with grains rather
than an hourglass and placed it on the lower floor. The one-time export in
`finish_wall27.js` transfers only that newly generated pigment to bare lower
wall rock and preserves the original 1254 × 1254 canvas. Its dark-pigment mask
and feathering affect 1,859 pixels within an 81 × 81 box; everything outside
is byte-for-byte identical at pixel level. No generated ancestor redraw is
used. Both final image files were opened for explicit visual review.

Final paths: `artifacts/gathering/wall-v7.png`, continuation
`artifacts/gathering/wall.png`, and `dist/gathering/27.jpg`.

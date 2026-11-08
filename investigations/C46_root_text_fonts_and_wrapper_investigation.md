# C46 investigation record: sticky-bar clearance, fonts and wrapper designs

**Status: documentation only. No runtime, test, version or bootstrap change.** This file sits on exact `main` bd7d19bca6107780cedd4f7225c74081b716e38f (optbot v0.6.45) and records an investigation whose code candidates were all **rejected**. Nothing here is a general browser guarantee: every number below was measured in one environment (see section 2), on a synthetic demo page and a few hand-built synthetic states. Where an independent reviewer re-ran something, the outcome is stated as the reviewer reported it and with its limits. **Only one item has any independent reproduction: the resize-then-full-page-capture scroll jump of section 8 (M3), reproduced by the reviewer in one run each at two of three root sizes, in a different Chromium build; everything else here is measured in this environment only.**

Simulation only: no live orders, no activation, no funds, no provider or market-data calls. The repository is public: no credentials, account identifiers, private or licensed data, internal records or real provider responses are involved; every page is generated from the repo's own synthetic replay.

## 1. The question

v0.6.44 and v0.6.45 add keyboard-focus and fragment clearance below the three sticky warning bars (SIMULATION ONLY / DEMO DATA / mode) when the page's own root text size (`html{font-size:…}`, as set by a user style or a page) is larger than the browser's default. Two limits were disclosed in v0.6.45: (a) `#main`, the skip link's target, is not covered; (b) a 40 px root at 320 px wide is not covered. C46 asked whether a small, safe, presentation-only change could improve either, and what reading space is left under the bars at those sizes. **Outcome: no change is recommended.** The investigation did, however, produce measurements that change how the existing claims should be read (section 3).

## 2. Environment and method (everything below is from this setup)

| Item | Value |
|---|---|
| Browser | Chromium 153.0.8010.12 (Playwright 1.63.0, bundled build `chromium-1243`), headless |
| Automation | Node.js 22.23.4, Playwright `chromium.launch()` with no arguments unless stated |
| OS | Linux 6.18.44 |
| Python | 3.13.18 (repo tests and page generation) |
| `fc-match system-ui` | `Inter-Regular.otf` ("Inter Regular"); `fc-match sans-serif` is also Inter here |
| Installed families (all 29, `fc-list : family`) | Bitstream Charter, Caladea, Carlito, Courier 10 Pitch, DejaVu Sans / Sans Mono / Serif, FreeMono, FreeSans, FreeSerif, IPAGothic, IPAPGothic, Inter, Inter Display, JetBrains Mono, Liberation Mono / Sans / Serif, Loma, Noto Color Emoji, OpenSymbol, Unifont (several), WenQuanYi Zen Hei (three); **no** Segoe UI, Roboto, San Francisco, Helvetica, Arial or Noto Sans |

* **Pages.** The 24-day demo page: extract the v0.6.45 bootstrap (`python3 optbot_v0.6.45_bootstrap.py <dir>`), then `PYTHONPATH=<dir>/src python3 -c "import sys; from optbot import cli; sys.exit(cli.main(['demo-dashboard','--out','demo.html','--days','24']))"`. The sparse states (`no_points`, `one_point`, `partial_only`, `open0`–`open2`, …) are **hand-built** from the repo's own test helpers (journal health entries and ledger records written with invented values); that helper script is not reproduced here, so results for sparse pages are not exactly reproducible from this file. Unless a table says otherwise, "the demo page" means the 24-day demo.
* **Raised root text size** (what v0.6.44/45 address): `page.goto(file://…/demo.html)` then `page.addStyleTag({content: 'html{font-size:32px}'})`. This moves `rem` but not the media-query `em`, which is why it differs from the browser's own default-size setting.
* **Browser default text size** (a different thing): `chromium.launch({args:['--blink-settings=defaultFontSize=32']})`. Here `em` in media queries and `rem` move together.
* **Font override** (section 3): `page.addStyleTag({content: 'body{font-family:"DejaVu Sans"!important}'})` in addition to the root size.
* **"Bars end at"** is `document.querySelector('.banners').getBoundingClientRect().bottom` in CSS px (the bars are sticky at the top, so this is also their height at scroll offset 0).
* **Viewports** are Playwright contexts of the stated size; forced colours use `forcedColors:'active'`, dark uses `colorScheme:'dark'`.

## 3. Finding: the bars' height depends on the font, so the clearance bands are font-specific

The page's font stack is `system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif`. The clearance bands (v0.6.28 to v0.6.45) were measured with whatever `system-ui` resolved to on the development machine, which is Inter. The same page wraps the three warning texts into different numbers of lines in other fonts.

"Bars end at", px (and rem = px ÷ root), demo page, window width 320 or 390 px:

| Font | 16 px root, 320 | 16, 390 | 24, 320 | 32, 320 | **40, 320** | 32, 390 | 40, 390 |
|---|---|---|---|---|---|---|---|
| system-ui (= Inter here) | 183.25 (11.45) | 161.56 (10.10) | 317.36 (13.22) | 539.73 (16.87) | **716.50 (17.91)** | 406.45 (12.70) | 662.25 (16.56) |
| DejaVu Sans | 183.25 (11.45) | 183.25 (11.45) | 317.36 (13.22) | 539.73 (16.87) | **828.88 (20.72)** | 406.45 (12.70) | 662.25 (16.56) |
| Liberation Sans (Arial metrics) | 183.25 | 161.56 | 317.36 | 449.84 (14.06) | 662.25 (16.56) | 406.45 | 608.00 (15.20) |
| FreeSans (Helvetica-like) | 183.25 | 161.56 | 317.36 | 496.34 (15.51) | 662.25 | 406.45 | 608.00 |
| Carlito (Calibri metrics) | 161.56 (10.10) | 116.63 (7.29) | 282.48 (11.77) | 406.45 (12.70) | 662.25 | 359.95 (11.25) | 495.63 (12.39) |
| Loma | 183.25 | 161.56 | 282.48 | 449.84 | 662.25 | 406.45 | 608.00 |
| generic `sans-serif` | 183.25 | 161.56 | 317.36 | 449.84 | 662.25 | 406.45 | 608.00 |

* **The reviewer's figure was reproduced exactly in my environment with DejaVu Sans:** the demo's bars end at **828.875 px** at a 40 px root and 320 px wide, where Inter (what `system-ui` resolves to here) gives 716.5 px. That the reviewer's reported height matches my DejaVu Sans measurement to three decimals is strong evidence of a wrap difference between fonts, but **which font the reviewer's browser actually used was not verified** (no font binding was inspected there); it may be DejaVu Sans or another face with the same metrics.
* **Consequence for earlier claims:** the v0.6.45 "17.5 rem band" (and its 14 and 12.5 rem siblings) were tuned to Inter. In DejaVu Sans at a 20 px root and 320 px wide the bars are 13.6 rem against a 12.5 rem band, and at 11.5 to 12.2 em wide 14.3 rem against 14.0 rem. These are shortfalls in an environment that was never measured before. They should exist at the browser's own default text size too, because the same em-selected bands apply there; that was **not measured** with the browser's default-size setting in DejaVu Sans.
* **Worst case over seven font configurations** (Inter, DejaVu Sans, Liberation Sans, FreeSans, Carlito, Loma, generic sans-serif; demo page; windows 320 px and wider; root sizes 20, 24, 28, 32, 36, 40, 44, 48 px; bar height in rem against window width in the page's own em): 7.0 to 7.5 em: 20.6 to 23.2 rem; 8.0 to 8.6 em: 20.72 (DejaVu); 8.8 to 10.3 em: 16.6 to 16.7; 10.4 to 10.9 em: 16.87; 11.0 to 11.4 em: 14.06; 11.5 to 12.2 em: 14.28; 12.3 to 13.5 em: 12.93; 13.6 to 15.9 em: 13.22; 16.0 to 16.3 em: 13.64; 16.4 to 16.5 em: 12.19; 16.6 to 24 em: 10.83; 24.1 to 25.8 em: 9.47 to 9.5; 26 to 31.9 em: 9.52 to 10.81; 32.4 to 33 em: 9.31 to 9.38. These are steps, not a smooth curve, because a word moving to the next line changes the height by a whole line.
* **What this means.** Clearance expressed in rem cannot be exact across fonts, and CSS cannot read the bars' height. Any "covered" claim in READINESS for v0.6.44/45 should be read as "covered in Inter, at the sizes measured". Fonts that were not measured (Segoe UI, Roboto, San Francisco, Noto Sans, Cantarell, …) are unknown.

### Coverage grid on the held candidate (head 0420c5e of this PR's earlier version)

588 cells = 7 font configurations × roots 16, 20, 24, 32, 40, 48 px × windows 320, 360, 390, 430, 500, 640, 768 px × 2 pages (demo, never-run), direct `#money`, "hidden" = the section heading's top above the bottom of the sticky bars. That head had C45's bands plus one extra band (18.5 rem up to 8.3 em). **15 cells were hidden**: 13 at a 48 px root (outside every claim) and two in DejaVu Sans: root 20 at 320 px (bars 13.6 rem against 12.5) and root 40 at 320 px (20.7 against 18.5). The v0.6.45 tree itself was not run through this grid.

## 4. Finding: skip-link landing, C45 against a main-only wrapper (rejected candidate C)

`Tab` to the skip link, `Enter`, then measure the hero card's top (`#headline`) against the bars' bottom. Demo page, 2 fonts × roots 16/24/32/40 × windows 320x900, 390x844, 768x900 = 24 cells; 8 identical, 16 differ. "Gap" = hero top minus bars bottom (blank space above the landing).

| Font, root, window | C45 | candidate C |
|---|---|---|
| Inter 24, 320x900 | gap 19 px | gap 55 |
| Inter 24, 768x900 | gap 90 | gap 123 |
| Inter 32, 320x900 | **under the bars by 104** | gap 56 |
| Inter 32, 390x844 | gap 30 | gap 78 |
| Inter 32, 768x900 | gap 59 | gap 136 |
| Inter 40, 320x900 | **under by 181** | gap 19 |
| Inter 40, 390x844 | **under by 126** | gap 74 |
| Inter 40, 768x900 | gap 21 | gap 148 |
| DejaVu 24, 320x900 | gap 19 | gap 55 |
| DejaVu 24, 768x900 | gap 10 | gap 94 |
| DejaVu 32, 320x900 | **under by 104** | gap 56 |
| DejaVu 32, 390x844 | gap 30 | gap 78 |
| DejaVu 32, 768x900 | gap 59 | gap 136 |
| DejaVu 40, 320x900 | **under by 293** | **still under by 93** |
| DejaVu 40, 390x844 | **under by 126** | gap 74 |
| DejaVu 40, 768x900 | gap 21 | gap 148 |

Counts over 56 skip-link activations (demo + never-run page, 7 windows × roots 16/24/32/40): C45 10 under the bars, in both fonts; candidate C: Inter 2 (both at 320x700 with a 40 px root, where the window is shorter than the bars), DejaVu 3 (a 40 px root, 320 px wide). Direct fragments including `#main`, jump activation and history (demo; 408 + 102 + 136 interactions): problems C45 / candidate C: Inter 19 / 3 / 3 → 13 / 3 / 3; DejaVu 29 / 6 / 6 → 24 / 6 / 6 (all remaining cells are a 40 px root at 320 px wide). The jump list's forward and reverse Tab sweep (52 configurations, 1092 steps) is identical for C45 and candidate C. The candidate raises the blank space above the landing by up to about 127 px in windows C45 already cleared (for example 21 to 148 px at 768 px wide and a 40 px root), the same coarse step the sections already get.

## 5. Reading space (unresolved, no safe CSS-only change found)

Bars end at 540 px at a 32 px root and 320 px wide (60% of a 900 px window; Inter and DejaVu alike), at 716.5 px with a 40 px root in Inter (80%; 102% of a 700 px window) and 828.9 px in DejaVu (92% of 900 px). Releasing the pinning needs a size container above `.banners` (the same class of container as `body`/`html`, see section 7), because a container cannot style itself or its preceding siblings. A tighter-leading variant of the bars (about 25% shorter) was considered and not built: it would need every clearance step retuned for each band and font. **Reading space is not fixed by any candidate and the pinned bars keep covering most of a small window at large root sizes.**

## 6. The candidates that were tried and rejected

**A. `<div class="pg">` around the jump list and the main column, container on it, four steps (3.5, 1.5, 3.5, 1.0 rem), fourth band 18.5 rem (head 0420c5e, still readable in this PR's history).** Removed v0.6.45's two padding regimes (12 rules → 4) and covered `#main`. At 320 px and a 40 px root the extra band (18.5 rem) was too small for DejaVu Sans (20.7 rem), which is what the reviewer observed (main 89 px under the bars). Rejected because it was font-tuned and because of section 8.

**B. Band retune from the seven-font envelope (never committed; working tree only).** Bands 9 / 12.5 / 14.8 (11 to 16.4 em) / 17.5 / 21.5 rem (≤ 8.8 em), media-height limits 22.5 / 31.25 / 37 / 43.75 / 53.75 em, steps 3.5, 2.3, 2.7, 4.0. Coverage grid: hidden cells 15 → 3 (all 48 px root). Rejected because:
* **it changes ordinary states:** at browser default text 24 px, 390x844, all 48 fragment targets (4 pages × 12) land at different scroll positions (for example `#headline` 65 → 341 px), because the new 37 em height limit makes the bars static (unpinned) in an 844 px window, so a common phone window at 150% text loses its pinned bars. The identity matrix also found 24 persistent differences at 320x900 `#money` with browser text 24 px. At browser text 16 and 32 px there were none;
* **blank space above targets grows in narrower fonts** (Inter, up to about 144 px at a 40 px root and 320 px, 67 px at 32 px / 390, 80 px at 20 px / 320);
* **a landing moves below the fold:** at a 40 px root and 320x900 in Inter the hero lands below the fold (bars 717 px plus about 860 px of clearance against a 900 px window), where C45 and candidate C leave it visible with a 19 px gap;
* it still only protects the sampled fonts.

**C. `<div class="mw">` around `<main>` only, container on it, three rules for `main` with C45's own bands (no new threshold).** Results in sections 4 and 8. Rejected because of section 8.

## 7. The withdrawn pre-merge `body` container (v0.6.44's first candidate; it was never merged) and why "container on a wrapper" is treated with suspicion

The first v0.6.44 candidate put the size container on `body`; it changed the page layout in Chromium after a viewport resize or a full-page capture and was withdrawn before any merge (the merged v0.6.44 and v0.6.45 use containers on the jump list, the main column and the sections only). Since then every wrapper-container design has been run against a matrix that compares the layout of every element, three scroll-position screenshots, the layout after a resize cycle and after a full-page capture. **The known-positive control** (the withdrawn `body` version against its baseline) is detected, 2 of 2 pairs at 768 px. **The control is limited:** a `body` variant of candidate A's own rules was *not* detected (0 of 2 at default root, 24 and 32 px roots), so the trigger of the original failure is not understood and the control only shows that the detector sees that one known failure. No design here is claimed immune.

## 8. Capture-path scroll behaviour with an added wrapper container (measured here; partly reproduced by the reviewer, see below)

**What was seen.** With candidate C (container on a wrapper directly around `main`), a page scrolled to the middle that then goes through a viewport resize cycle and a full-page capture ends at the bottom of the document in this environment, where C45 keeps its position. The capture API used is Playwright's `page.screenshot({fullPage:true, path})`; how it is implemented inside Chromium was not inspected here, and no claim is made about any other capture tool. The resize cycle is Playwright's `page.setViewportSize`. Normal browsing actions (a window resize cycle, a rotation-like width change, a capture followed by a resize) did not show a difference.

Exact sequences, demo page, window 1280x900, root set with `addStyleTag`; `scrollTo` at "middle" = `(scrollHeight − innerHeight) / 2`; resize cycle = `setViewportSize({width:1080,height:900})`, wait 80 ms, `setViewportSize({width:1280,height:900})`, wait 100 ms; capture = `page.screenshot({fullPage:true, path})`, then wait 100 ms; the scroll offset is read with `window.scrollY`. Waits of 40 ms follow each `scrollTo`.

| Sequence | C45 | candidate C |
|---|---|---|
| M1 middle → resize cycle | kept | kept |
| M2 middle → capture only | kept | **moved to the bottom in 2 of 8 runs at root 16** (kept in the other 6, including 0 of 5 in a repeat); kept at roots 24 and 32 |
| **M3 middle → resize cycle → capture** | kept | **moved in 5 of 5 repeats at roots 16, 24 and 32** (2513 → 5027; 4970 → 9944 (once 4974); 7053 → 14111 px) |
| M4 middle → capture → resize cycle | kept | kept |
| M5 middle → two resize cycles (1080 and 900 wide) → capture | kept | moved at root 24 (4970 → 9944), +1 px at root 16 |
| M6 top → resize cycle → capture | stays at the top | stays at the top |
| M7 middle → window height 700 then 900 → capture | kept | moved (both roots) |

Isolation, M3 at 1280x900, 5 fresh contexts per cell: C45 moved 0 of 5 at root 16 and 0 of 5 at root 24; v0.6.43 (no wrapper, no `.jump`/`main` containers, sections only) 0 of 5 and 0 of 5; **the same wrapper `div` without `container-type`: 1 of 5 at root 16 and 0 of 5 at root 24** (so a plain wrapper is not strictly clean either, and some of this is timing-sensitive); **candidate C with `container-type`: 5 of 5 and 5 of 5.** Variants of the container wrapper, **one run per cell** (M2 and M3, roots 16 and 24): adding `overflow-anchor:none` kept the position in all four; `display:flow-root`, `position:relative`, `content-visibility:visible` and a `container-name` still moved in M3. Scroll anchoring inside the wrapper is therefore implicated, but the mechanism is not established and single runs are weak evidence.

**Why `overflow-anchor:none` is not an acceptable fix.** It turns scroll anchoring off for the whole main column. A live line in a main section (`#snap`, the inline script's "snapshot taken N ago", which gains a sentence when the page turns OLD) can change height above a reader; with anchoring off the reader's view would shift by that change.

**Reviewer's results (two separate checks).**
* **Simple capture, no resize.** The reviewing assistant ran middle-of-page full-page Playwright screenshots at 1280 px, roots 16, 24 and 32, with the main-only container and with `.pg`, **without a resize sequence**, and reports that offsets stay at the midpoint in both versions: no thousands-of-pixels jump. That is consistent with the table above (M2 intermittent, M1 and M4 identical).
* **Exact M3, run independently** with candidate C's CSS from the appendix, file URLs, root set with `addStyleTag`, the 80 ms and 100 ms resize waits, a full-page capture and a 100 ms wait, in **Chromium 156.0.8078.4** (a different build from mine, 153.0.8010.12), **one run per root**, scroll offset before → after the capture: root 16: C45 2597 → 2598, candidate C 2597 → **5195**; root 24: C45 5041 → 5045, candidate C 5041 → 5045 (**no jump**); root 32: C45 7273 → 7273, candidate C 7273 → **14552**. So the candidate's jump to the bottom was **independently reproduced at roots 16 and 32 and was not seen at root 24** in that run, with one run each. In the reviewer's runs C45 itself moved by 1 to 4 px at roots 16 and 24 (document growth during the capture), so the baseline is not exactly stable there; in my five runs per cell C45 moved 0 of 5. My own five runs at root 24 moved 5 of 5 (four to the bottom, once by 4 px), so the root-24 result differs between the two environments and between runs: **the behaviour is real in at least two environments but sensitive to the environment and timing, and it is not established at every root size.**

**Real-user impact, as far as it was assessed.** Not observed: normal resize, rotation-like width changes, capture-then-resize. Observed only through the capture path (Playwright here): the scroll position after a full-page capture can be lost. Not tested: the DevTools "Capture full size screenshot" UI itself, printing, find-in-page, other engines, any assistive technology. If real, the consequence would be that a user (or an automated audit) who captures the page from mid-scroll finds the view at the bottom afterwards: an annoyance, not a loss of data, but larger than the 3 to 6 px offset below. In the states checked, leaving the candidate out (C45) keeps the baseline position. Whether some other wrapper or target design would also keep it was not tested beyond the variants listed above (a plain wrapper moved 1 of 5 times at root 16), so nothing here says that a container above `main` is the only cause or that no other design could avoid it.

### The earlier "3 to 6 px" scroll-offset difference

Sequence A: scroll to the bottom (`scrollTo(0, 1e9)`), resize cycle (1280 → 1080 → 1280), full-page capture. The capture grows the document by 4 px (root 24), 6 px (root 32) or 3 px (root 40) in **both** versions; the container-wrapper versions end at the bottom edge (`scrollY` = max) and C45 ends that many pixels above it. It showed up as persistent differences in the identity matrix at 1280 px with a raised root (see section 9). It looks like the bottom-edge case of the behaviour above, but that link is an inference, not a demonstrated cause. The reviewer's first simple case (offset identical in both, document growth 4/6/3 px) did not reproduce the difference; the resize cycle is the necessary ingredient here. Capture-only at the bottom (no resize) was identical in both versions in the runs made (two per root).

## 9. The identity matrices, and the invalid comparator

Matrix procedure (all sequential, one process at a time): for each pair (page, window, with or without `#money`) in a fresh Playwright page, compare a hash of (a) `getBoundingClientRect` position and size (y plus `scrollY`) plus computed `display`, `flex-direction`, `grid-template-columns`, `font-size`, `color`, `background-color`, `position`, `visibility`, `opacity`, `border-top-width`, `outline-style` of every element (`html, body, body *`), (b) three viewport screenshots at scroll fractions 0, 0.5 and 1, (c) the same geometry after the resize cycle, (d) after a full-page capture. A pair that differs once and then matches on retry is **recorded as a first-pass mismatch and is not a pass**.

* **An invalid chain.** For candidate A the first comparator listed every element, including the added wrapper, so every pair differed: 120 of 120 at browser text 16 and 24 px, and the control reported the candidate as different at 768 px. That is an artefact of the extra element, not evidence about the design. It was stopped and replaced by a comparator that skips only the wrapper element (the wrapper's own box, role and neutrality were checked separately; its children's layout, text and painting stay in the comparison). With the wrapper excluded, a single 768 px pair matched on geometry, the three screenshots, the resize and the full-page capture. The invalid numbers are not used anywhere else in this record.
* **Candidate A, corrected comparator:** default text 16 and 24 px: 0 differences (120 pairs each); 32 px: 0 persistent and **1 first-pass mismatch** (`one_rejected` `#money` at 768, matched on retry); dark and forced colours (4 widths, text 16 and 32 px): 192 pairs, 0; raised root 24, 32 and 40 px: **24, 24 and 22 persistent differences, all at 1280 px**, all explained (in 72 pairs examined) as the post-capture scroll offset of section 8: layout and the three screenshots matched before the capture.
* **Candidate B (retune):** default text 16 and 32 px: 0; 24 px: 24 persistent (the height-limit change above); raised root 24, 32, 40: 24, 21 and 23 persistent at 1280, with **3 first-pass mismatches** at root 32 (`long_gap#money` at 768, `no_pos_trades#money` at 1280, `open1` at 1280), each matched on retry; dark and forced colours: 0.
* **Candidate C (main-only wrapper), small run only** (3 pages, 4 widths plus 568x320, with and without `#money`, 30 pairs each): default text 16 and 32 px: 0 and 0; raised root 24, 32 and 40 px: 6, 6 and 6 persistent (all 1280 px), plus 1 first-pass mismatch each at root 32 (`no_points` at 1280) and root 40 (`no_points#money` at 1280). Print (8 PDFs, 53 pages incl. text) and the accessibility tree (18 page/width combinations, about 509 nodes) were identical to C45; the wrapper was a plain, role-less, padding-less `div` whose box equalled `main`'s in 40 combinations; 720 fragment loads at browser text 16, 24 and 32 px had identical scroll positions.
* **What the matrices cannot show.** They scrolled to the bottom before capturing, so they could not see the mid-page behaviour of section 8; they were added to the investigation afterwards by hand-run sequences. An identity check proves nothing about states it does not visit.

## 10. Chromium history behaviour (baseline, not a dashboard issue)

Back or Forward to the **first** jumped fragment of a session leaves the page scrolled to the top in this Chromium, at default text too. A plain page reproduces it:

```js
// plain.html: <nav><a href="#s1">one</a> <a href="#s2">two</a> <a href="#s3">three</a></nav>
//             then five <h2 id="sN" style="margin-top:900px">…</h2><p>text</p> blocks
await page.goto('file://…/plain.html');
for (const id of ['s1','s2','s3']) { await page.focus(`a[href="#${id}"]`); await page.keyboard.press('Enter'); await page.waitForTimeout(250); }
for (const d of ['back','back','back','forward']) { await (d==='back'?page.goBack():page.goForward()); await page.waitForTimeout(250); console.log(d, await page.evaluate(()=>[location.hash, Math.round(scrollY)])); }
// observed: back → #s2 (scrollY 1891); back → #s1 (scrollY 0, not 926); back → ''; forward → #s1 (scrollY 0)
```

Landings of this kind are reported separately in all counts above and are the same before and after every candidate.

## 11. What is and is not claimed

* **Measured and recorded here:** the font dependence of the bars' height (7 configurations, one machine); which cells of the coverage grid were hidden for the held head; the skip-link table; the rejected designs' failure evidence; the capture-path sequences, with their intermittency.
* **Not claimed:** that any design is safe across fonts or browsers; that candidate C's capture-path behaviour is a defect (it reproduces in two Chromium builds, in the reviewer's case at two of three root sizes in one run each, and not with the reviewer's simpler no-resize capture; real use through DevTools' own capture or any other tool was not tested); that reading space is acceptable at large root sizes; accessibility conformance; anything about engines other than this Chromium build, any screen reader, DevTools' own capture UI, or the real clipboard.
* **Open limits of v0.6.45 that this investigation leaves in place:** `#main` (the skip link's target) can land under the bars with a root text size of 32 px or more at 320 px wide; a 40 px root at 320 px is not covered; clearance is Inter-tuned, so wider fonts can leave part of a target under the bars at the sizes in section 3; the bars still cover most of a small window at large root sizes.
* **Recommendation:** no runtime change. Alternative designs for the skip target (for example moving the target to an element that already has a container ancestor) and any change that lowers the bars' height were **not started**.

## Appendix: scripts (the ones the numbers above came from, trimmed to the essentials)

Bars' height by font (section 3):

```js
const { chromium } = require('playwright');
const FONTS = [['system-ui',null],['Inter','Inter'],['DejaVu Sans','DejaVu Sans'],['Liberation Sans','Liberation Sans'],['FreeSans','FreeSans'],['Carlito','Carlito'],['Loma','Loma'],['generic','sans-serif']];
(async () => { const b = await chromium.launch();
  for (const [label, fam] of FONTS) for (const [root, w] of [[16,320],[16,390],[24,320],[32,320],[40,320],[32,390],[40,390]]) {
    const ctx = await b.newContext({ viewport: { width: w, height: 900 } }); const p = await ctx.newPage();
    await p.goto('file://' + process.cwd() + '/demo.html');
    await p.addStyleTag({ content: `html{font-size:${root}px}` + (fam ? `body{font-family:"${fam}"!important}` : '') });
    await p.waitForTimeout(30);
    const bottom = await p.evaluate(() => document.querySelector('.banners').getBoundingClientRect().bottom);
    console.log(label, root, w, bottom.toFixed(3), (bottom / root).toFixed(2)); await ctx.close(); }
  await b.close(); })();
```

Skip-link landing (section 4; run it with the page directory of each version, optionally with a `body{font-family:…}` rule):

```js
// for each root in [16,24,32,40] and window in [[320,900],[390,844],[768,900]]:
await p.goto(url); await p.addStyleTag({ content: `html{font-size:${root}px}` });
await p.keyboard.press('Tab'); await p.keyboard.press('Enter');
await p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); await p.waitForTimeout(30);
const g = await p.evaluate(() => ({ hero: document.getElementById('headline').getBoundingClientRect().top,
                                    bar: document.querySelector('.banners').getBoundingClientRect().bottom, vh: innerHeight }));
// under the bars: g.hero < g.bar - 1;  below the fold: g.hero > g.vh - 20;  otherwise gap = g.hero - g.bar
```

Capture-path sequences (section 8; `base/` and `cand/` hold the two demo pages):

```js
const mid = p => p.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - innerHeight) / 2));
const cycle = async p => { await p.setViewportSize({width:1080,height:900}); await p.waitForTimeout(80);
                           await p.setViewportSize({width:1280,height:900}); await p.waitForTimeout(100); };
const capture = async p => { await p.screenshot({ fullPage: true, path: '_t.png' }); await p.waitForTimeout(100); };
// per run: new context {viewport:{width:1280,height:900}}; goto demo.html; addStyleTag html{font-size:<root>px}; wait 60;
//   await mid(p); wait 40; const before = Math.round(await p.evaluate(() => scrollY));
//   M2: await capture(p)          M3: await cycle(p); await capture(p)          M1: await cycle(p)
//   const after = Math.round(await p.evaluate(() => scrollY));   // "moved" = after !== before
```

Sequence A (bottom): `scrollTo(0, 1e9)`; wait 40; `cycle`; `capture`; compare `scrollY` with `scrollHeight - innerHeight` read after the capture.

Geometry used by the identity matrix (the wrapper element is the only one skipped):

```js
const geo = () => { const o = [];
  for (const e of document.querySelectorAll('html,body,body *')) {
    if (e.classList && (e.classList.contains('pg') || e.classList.contains('mw'))) continue;   // the added wrapper only
    const c = getComputedStyle(e), r = e.getBoundingClientRect();
    o.push([e.tagName, Math.round(r.x*10), Math.round((r.y+scrollY)*10), Math.round(r.width*10), Math.round(r.height*10),
            c.display, c.flexDirection, c.gridTemplateColumns, c.fontSize, c.color, c.backgroundColor, c.position,
            c.visibility, c.opacity, c.borderTopWidth, c.outlineStyle]); }
  return JSON.stringify(o) + '|' + document.documentElement.scrollHeight; };
```

The candidate-C page used in section 4 and 8 is the v0.6.45 page with `<main id="main" tabindex="-1">` replaced by `<div class="mw"><main id="main" tabindex="-1">`, the first `</main>` by `</main></div>`, and this CSS appended before `</style>`:

```css
@media screen{.mw{container-type:inline-size}}
main{scroll-margin-top:calc(var(--m1,0rem) + var(--m2,0rem) + var(--m3,0rem))}
@media (min-width:32.01em) and (max-width:880px) and (min-height:22.51em){
@container (max-width:32em){main{--m1:3.5rem}}}
@media (min-width:32.01em) and (max-width:880px) and (min-height:22.51em),(min-width:14.01em) and (max-width:32em) and (min-height:31.26em){
@container (max-width:14em){main{--m2:1.5rem}}}
@media (min-width:32.01em) and (max-width:880px) and (min-height:22.51em),(min-width:14.01em) and (max-width:32em) and (min-height:31.26em),(min-width:11.01em) and (max-width:14em) and (min-height:35.01em){
@container (max-width:11em){main{--m3:3.5rem}}}
```

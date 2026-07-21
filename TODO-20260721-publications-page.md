# TODO: Publications page with citation charts

**Goal:** An interactive HTML page of Georgia Tsambos's published papers, with
charts of how citations have grown over time, published live on GitHub Pages.

Started 2026-07-21 (Workshop Session 2).

## Facts established

- **ORCID:** `0000-0001-7001-2275` — confirmed against the paper list.
  (Note: `0000-0001-6225-7926` is a different Tsambos and must not be used.)
- **Live at:** https://gtsambos.github.io/MyPublications/
- **Repo:** `gtsambos/MyPublications`, public, SSH remote.
- **Data source:** OpenAlex. Reachable from the Harris cluster (HTTP 200).
  Citations are only broken out by year from ~2012 on; older citations still
  count in lifetime totals but have no per-year breakdown.
- **Environment:** work happens on the Harris SGE cluster, terminal-only. The
  page is reviewed by pushing and refreshing the live GitHub Pages URL, since
  there is no local browser here. Pages is enabled early for this reason.
- **Python:** `python3` (PyPy 3.9) has `requests` and `openpyxl`. No `pandas`.

## Plan — COMPLETE 2026-07-21

- [x] Create the repo and start this spec
- [x] Fetch works from OpenAlex by ORCID; save `papers.json` + a spreadsheet
- [x] **Check the list by eye** and drop anything not mine — 33 works to 7
- [x] Interview on design; fold answers into this spec; approve before building
- [x] Build `index.html`
- [x] Enable GitHub Pages (browser — the API token lacks admin scope)
- [x] Live and confirmed working
- [x] Package the workflow as a reusable skill (Session 2 stretch goal)
- [x] GitHub Action to refresh the data on a schedule

**Still open (cosmetic, for whenever):** the *link-ancestors* entry in the
software section points at the tskit repo, because `link_ancestors` is a tskit
method rather than a standalone package — so it duplicates the tskit entry
above it. Drop it or repoint it at `tspop`.

## The design (from the interview, 2026-07-21)

**Look — warm editorial.** Off-white paper tone, generous whitespace, one warm
accent. System sans throughout (no serif display face). Dark mode **follows the
reader's system setting**; no toggle.

**Colour.** Accent is the reference palette's slot-2 orange: `#eb6834` light /
`#d95926` dark. Surfaces `#fcfcfb` / `#1a1a19`, page plane `#f9f9f7` / `#0d0d0d`,
ink and gridlines per `palette.md`. *The palette validator could not be run — the
cluster has Node v12, which predates the `??=` syntax the script uses — so
documented values are used unchanged rather than substituted by eye.*

**Header.** Name, plus the one-line description "Population geneticist, Harris
lab, University of Washington" — confirmed 2026-07-21.

**No stat tiles.** The numbers are folded into the intro sentence instead —
"7 papers, cited 931 times since 2020" — which suits the editorial look better
than a dashboard row.

**Header links.** ORCID only (`orcid.org/0000-0001-7001-2275`), so a reader can
verify the record. No GitHub or Scholar link.

**Main chart — cumulative citations over time.** Single series, so no legend; the
title names it. 2px line, area wash at ~10%, end-dot with a surface ring, hairline
gridlines, endpoint label only. Hover crosshair + tooltip. **No annotations** on
the curve — the paper list carries the detail.
Data runs 2018–2026 (one stray 2018 citation predates the first paper).
**2026 is partial: its final segment is dashed and labelled "partial year"** —
the curve would otherwise read as flattening.

**Paper list.** Newest first. Each entry: **title linked to its DOI**, the
**venue**, and its **citation count**.

**Software section**, below the papers — a small block for the open-source work,
since 11 Zenodo release records were dropped from the paper list: **tskit,
msprime, stdpopsim, tspop, link-ancestors**, each linked to its repo.

**Footer.** "Data from OpenAlex, last updated 21 July 2026."

**Build constraints.** Single self-contained `index.html`, no external libraries
or CDN requests — the chart is hand-written inline SVG. Data is read from
`papers.json` at build time and inlined, so the page works as a static file.

## Notes as we go

*(kept current so the work can be re-run later)*

- OpenAlex indexes several of these papers twice; the duplicates are *within*
  the `article` type, so filtering by type alone does not catch them. See
  `exclusions.json`.
- OpenAlex reports venue "Open MIND" for the 2026 tskit ARG paper and for
  several Zenodo software records. Looks like mis-indexing; the paper may not be
  formally published yet.

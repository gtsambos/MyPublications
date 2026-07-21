# TODO: Publications page with citation charts

**Goal:** An interactive HTML page of Georgia Tsambos's published papers, with
charts of how citations have grown over time, published live on GitHub Pages.

Started 2026-07-21 (Workshop Session 2).

## Facts established

- **ORCID:** `0000-0001-7001-2275` — pending confirmation against the paper list.
  (Note: `0000-0001-6225-7926` is a different Tsambos and must not be used.)
- **Repo:** `gtsambos/MyPublications`, public, SSH remote.
- **Data source:** OpenAlex. Reachable from the Harris cluster (HTTP 200).
  Citations are only broken out by year from ~2012 on; older citations still
  count in lifetime totals but have no per-year breakdown.
- **Environment:** work happens on the Harris SGE cluster, terminal-only. The
  page is reviewed by pushing and refreshing the live GitHub Pages URL, since
  there is no local browser here. Pages is enabled early for this reason.
- **Python:** `python3` (PyPy 3.9) has `requests` and `openpyxl`. No `pandas`.

## Plan

- [x] Create the repo and start this spec
- [ ] Fetch works from OpenAlex by ORCID; save `papers.json` + a spreadsheet
- [ ] **Check the list by eye** and drop anything not mine
- [ ] Interview on design; fold answers into this spec; approve before building
- [ ] Build `index.html`
- [ ] Enable GitHub Pages (browser — the API token lacks admin scope)
- [ ] Refine the design against the live URL
- [ ] Mark complete; optionally copy to `ClaudeLab/todos/completed/`

## Notes as we go

*(kept current so the work can be re-run later)*

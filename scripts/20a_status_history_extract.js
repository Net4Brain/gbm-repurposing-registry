// Step 20a (browser part) - recruitment status on the index date from ClinicalTrials.gov version histories (D41).
//
// Why a browser: scripted requests (curl, Python) to the history endpoint return HTTP 403, so the extract was run on
// 2026-11-04 in the browser console of the public record-history page (https://clinicaltrials.gov/study/NCT04591431
// ?tab=history), using the same internal endpoint that page calls: /api/int/studies/{NCT}?history=true.
// It is reproduced here exactly as run, except that IDS must be filled with the 280 primary-cohort NCT IDs
// (outputs/main/cohort_D37.csv, primary_cohort == "yes", in ascending order).
//
// Output: one line per trial, "nct_id|status|date|version|next status|next date|n versions", lines joined by "\n"
// plus a final "\n". Save it as data/raw/ctgov_status_history_D41_<date>.txt and check its SHA-256 (the 2026-11-04
// extract: b48c8cc5b5e6cdc40f031d7c9729b106b9b2f3278e06b7b28e7d01ce2058e518). scripts/20a_status_history_from_raw.py
// then rebuilds data/reference/status_history_index_D41.csv. A rerun on a later date can differ if the registry
// revises a record's history.

const ids = [/* IDS: the 280 primary-cohort NCT IDs */];
const out = {}; const IDX = '2026-07-31';
for (const n of ids) {
  let tries = 0, j = null;
  while (tries < 3) {
    try { const r = await fetch(`/api/int/studies/${n}?history=true`); if (r.ok) { j = await r.json(); break; } } catch (e) {}
    tries++; await new Promise(s => setTimeout(s, 1500));
  }
  if (!j) { out[n] = ['FETCH_FAILED']; continue; }
  const ch = (j.history && j.history.changes) || [];
  const before = ch.filter(c => c.date <= IDX).sort((a, b) => a.date < b.date ? -1 : 1);
  const last = before[before.length - 1];
  const nxt = ch.filter(c => c.date > IDX).sort((a, b) => a.date < b.date ? -1 : 1)[0];
  out[n] = [last ? last.status : 'NO_VERSION_BEFORE_INDEX', last ? last.date : '', last ? last.version : '',
            nxt ? nxt.status : '', nxt ? nxt.date : '', ch.length];
  await new Promise(s => setTimeout(s, 250));
}
window.__statusOut = out;

// When all 280 are done (no FETCH_FAILED), the raw text and its checksum:
const raw = Object.entries(window.__statusOut).map(([k, v]) => [k, ...v].join('|')).join('\n') + '\n';
const sha = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw))))
  .map(x => x.toString(16).padStart(2, '0')).join('');
[raw.length, sha];

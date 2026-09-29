# Maldives Tourism Dataset (2007–2026)

A year-by-year tourism dataset for the Maldives, built for a Business Informatics
Master's thesis, combining two official government sources:

1. **Ministry of Tourism & Civil Aviation** — monthly statistical reports (PDF),
   2009–2026.
2. **Maldives Bureau of Statistics** — Statistical Yearbook of Maldives,
   annual, 2010–2026 editions (covering data back to 2007).

## Folder structure

```
raw/<year>/                       Raw yearbook source files as published (2010-2026)
raw/fetch_yearbook_tourism.py     Script that downloaded raw/
tourism_dataset_extracted/<year>/tourism.json   The combined, cleaned dataset (2007-2026)
```

**`raw/`** contains only the Bureau of Statistics yearbook's Tourism chapter
(chapter 10, a fixed convention across every edition regardless of how other
chapters are numbered) — PDF and Excel files as published, one folder per
publication year 2010–2026. Formats vary by era: HTML tables for 2010–2012
(the site had no downloadable files then, so the rendered table page itself
was saved), PDF + Excel pairs from 2013 onward. This is source material, not
itself part of the clean dataset.

The Ministry of Tourism's raw monthly PDFs (2009–2026, 211 reports) are
**not included in this repo** — only their already-extracted values, folded
into `tourism_dataset_extracted/`.

**`tourism_dataset_extracted/`** is the actual dataset: one `tourism.json`
per year, 2007–2026.

## `tourism.json` schema

Each file contains only the sections that exist for that year — nothing is
padded with nulls.

```json
{
  "year": 2015,
  "monthly": [
    {
      "month": 1,
      "total_arrivals": 97073,
      "arrivals_by_air": 97073,
      "arrivals_by_sea": 0,
      "arrivals_by_region": { "EUROPE": 52545, "ASIA & THE PACIFIC": 36311, "...": "..." },
      "arrivals_by_country": { "Russia": 5790, "United Kingdom": 7150, "...": "..." },
      "total_beds": 20992,
      "bed_nights": 645472,
      "occupancy_rate_pct": 91.1,
      "avg_stay_days": 6.2,
      "filled_from_yearbook": ["total_beds", "bed_nights"]
    }
  ],
  "annual_summary": {
    "total_arrivals": 1234567,
    "months_with_data": 12,
    "avg_occupancy_rate_pct": 88.4,
    "avg_stay_days": 6.5,
    "arrivals_by_country": { "...": "annual totals, summed from monthly" },
    "arrivals_by_region": { "...": "annual totals, summed from monthly" }
  },
  "atoll_bed_capacity": { "Kaafu": 15566, "Raa": 4548, "...": "19 of 20 atolls" }
}
```

- **`monthly`** — present for 2009–2026 (Ministry source). Each month keeps
  only the fields that were actually extracted; a field simply doesn't
  appear if neither source had it for that month, rather than being `null`.
  `filled_from_yearbook` lists any fields whose value came from the yearbook
  gap-fill (see below) instead of the Ministry report — present only on
  months where that happened.
- **`annual_summary`** — derived by aggregating `monthly`, not pulled from
  the yearbook's own annual arrivals table (which would just duplicate it).
- **`atoll_bed_capacity`** — present for 2007–2025 (yearbook source).
  Resort bed capacity per atoll, year-end snapshot. 19 of 20 atolls
  typically appear; Gnaviyani has zero registered resorts in this period,
  so it's correctly absent from a *resort* bed-capacity table.
- **2007–2008**: atoll data only (Ministry reports don't go back that far).
- **2026**: monthly data through the most recently published month only;
  no atoll figure yet (that table isn't published until the year closes).

## Field coverage

| Field | Coverage | Notes |
|---|---|---|
| `total_arrivals`, `arrivals_by_region`, `arrivals_by_country` | 211/211 months (2009–2026) | Ministry source, fully clean |
| `total_beds` | 211/211 months | See gap-fill below |
| `occupancy_rate_pct` | 211/211 months | See gap-fill below |
| `avg_stay_days` | 211/211 months | See gap-fill below |
| `bed_nights` | 206/211 months | Gap remains only in 2026 (still in progress; no yearbook edition covers it yet) |
| `atoll_bed_capacity` | 2007–2025 (19 years) | Yearbook source |

### The 2010–2020 gap-fill

The Ministry's monthly PDF reports switched to an infographic-style layout
for roughly 2010–2020, which made `total_beds`, `bed_nights`,
`occupancy_rate_pct`, and `avg_stay_days` unparseable as text for that
stretch (only ~47–50% of months had these fields from the Ministry source
alone). The yearbook publishes an equivalent "Bed Capacity and Utilization
by Month" table every year, so it was used to **fill only the missing
values** — it never overwrites a Ministry-sourced value that was already
present. This closed the gap to 98–100% coverage across the full
2009–2026 range. Any month where a value came from this fallback is marked
in that month's `filled_from_yearbook` list.

## What was deliberately excluded

- **Yearbook annual arrivals-by-nationality table** — a strict subset of
  what summing the monthly `arrivals_by_country` data already gives you.
- **Yearbook monthly bed-capacity/occupancy tables split by facility type**
  (resorts/hotels/guesthouses/safari vessels individually) — the combined
  total (used for the gap-fill above) already covers what's needed; the
  per-type breakdown wasn't judged worth the added complexity.
- **Tourism revenue vs. government budget table** — its position in the
  chapter's table numbering isn't stable across editions (e.g. "table 10.6"
  is a completely different table in the 2026 edition than in the 2010
  one), so it can't be safely auto-extracted by title/number without
  per-year manual verification, which hasn't been done.

## Known limitations

- **Atoll-level *arrivals*** (as opposed to bed *capacity*) only exist in
  the Ministry data from January 2025 onward — two months, at time of
  writing. Not enough history for atoll-level demand forecasting; treat any
  atoll-level arrivals figure as a recent snapshot, not a time series.
- **Gap-filled values are regex-parsed from PDF text**, including PDFs with
  mixed English/right-to-left Dhivehi text, which has non-obvious rendering
  quirks (e.g. reversed digit order in RTL title lines, single-facility-type
  sub-tables sharing near-identical titles with the combined table). The
  parsing logic was corrected for the specific issues found during
  construction, but individual gap-filled values have not been
  cross-checked one by one against the source PDFs.
- **Mislabelled Ministry source files**: a small number of the original
  Ministry PDFs were mislabelled by month/year on the Ministry's own
  website (see the scraping notes for `tourism_ministry_reports/`, not
  included in this repo); corrected filenames were used as authoritative
  over on-page labels where the two conflicted.

## Sources

- Ministry of Tourism & Civil Aviation: https://www.tourism.gov.mv/statistics/publications
- Maldives Bureau of Statistics, Statistical Yearbook: https://statisticsmaldives.gov.mv/yearbook/

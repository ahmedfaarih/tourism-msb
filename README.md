# Maldives Tourism Dataset (2007–2026)

Monthly + annual Maldives tourism data, combining:

1. **Ministry of Tourism & Civil Aviation** monthly reports (2009–2026)
2. **Maldives Bureau of Statistics** yearbooks (2010–2026 editions, data back to 2007)

## Structure

```
raw/<year>/                              yearbook source files as published, 2010-2026
raw/fetch_yearbook_tourism.py            script that downloaded raw/
tourism_dataset_extracted/<year>/tourism.json   the actual dataset, 2007-2026
```

`raw/` is the yearbook's Tourism chapter only — PDF/Excel as published (HTML for
2010–2012, no downloads existed yet then). Source material, not the clean data.

Ministry PDFs (211 reports, 2009–2026) aren't in this repo — only their extracted
values, in `tourism_dataset_extracted/`.

## `tourism.json` schema

```json
{
  "year": 2015,
  "monthly": [
    {
      "month": 1,
      "total_arrivals": 97073,
      "arrivals_by_air": 97073,
      "arrivals_by_sea": 0,
      "arrivals_by_region": { "EUROPE": 52545, "...": "..." },
      "arrivals_by_country": { "Russia": 5790, "...": "..." },
      "total_beds": 20992,
      "bed_nights": 645472,
      "occupancy_rate_pct": 91.1,
      "avg_stay_days": 6.2,
      "filled_from_yearbook": ["total_beds", "bed_nights"]
    }
  ],
  "annual_summary": {
    "total_arrivals": 1234567,
    "avg_occupancy_rate_pct": 88.4,
    "arrivals_by_country": { "...": "summed from monthly" }
  },
  "atoll_bed_capacity": { "Kaafu": 15566, "...": "19 of 20 atolls" }
}
```

Fields only appear when they have a value — nothing is null-padded.

- **`monthly`**: 2009–2026, from the Ministry. `filled_from_yearbook` lists any
  fields pulled from the yearbook instead, on months where that happened.
- **`annual_summary`**: computed by summing `monthly`, not from the yearbook's
  own annual table (same numbers, that table is redundant).
- **`atoll_bed_capacity`**: 2007–2025, from the yearbook. Resort beds per atoll,
  year-end. Gnaviyani is missing — it has zero resorts, correctly.
- **2007–2008**: atoll data only, no Ministry reports that far back.
- **2026**: partial year, no atoll figure yet (published after year-end).

## Coverage

| Field | Coverage |
|---|---|
| `total_arrivals`, `arrivals_by_region`, `arrivals_by_country` | 211/211 months |
| `total_beds`, `occupancy_rate_pct`, `avg_stay_days` | 211/211 months |
| `bed_nights` | 206/211 (gap is 2026 only, still in progress) |
| `atoll_bed_capacity` | 2007–2025 |

**Why it's not full 47% like the raw Ministry PDFs**: 2010–2020 Ministry reports
used an infographic layout that couldn't be parsed for bed/occupancy/stay figures.
The yearbook publishes the same numbers monthly, so those gaps are filled from
there — only where the Ministry value was missing, never overwriting it.

## Excluded on purpose

- Yearbook's annual arrivals-by-nationality table — same numbers as summing
  `arrivals_by_country`, no reason to duplicate it.
- Yearbook's per-facility-type monthly bed tables (resorts/hotels/guesthouses/
  vessels split out) — the combined total already used for the gap-fill covers it.
- Tourism revenue vs. government budget table — its table number moves between
  editions ("10.6" is a different table in 2010 vs 2026), not safe to grab by
  number without checking every year by hand, which wasn't done.

## Limitations

- **Atoll-level arrivals** (not bed capacity — actual visitor counts per atoll)
  only exist from January 2025. Two months of data. Don't forecast with it,
  treat it as a snapshot.
- Yearbook gap-fill values are regex-parsed from PDFs with mixed English/Dhivehi
  (right-to-left) text — known quirks like reversed year order and near-duplicate
  table titles were fixed, but individual values haven't been hand-checked
  against the source PDFs one by one.
- A few Ministry source files were originally mislabelled by month/year on the
  Ministry's own site; corrected filenames were used over the on-page labels.

## Sources

- https://www.tourism.gov.mv/statistics/publications
- https://statisticsmaldives.gov.mv/yearbook/

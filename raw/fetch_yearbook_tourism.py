#!/usr/bin/env python3
"""
Download the Tourism chapter (chapter 10, by fixed convention across all
editions) of the National Bureau of Statistics' Statistical Yearbook of
Maldives, 2010-2026.

The site has three generations of publishing platform, each with a
different URL scheme for the same chapter-10 file numbering:
  - 2010-2012: static tree-menu site, tables only exist as .htm pages
    (no separate PDF/Excel download) under <base>/yearbook/<TourismDir>/10.X.htm
  - 2013-2015: same static site generation, but chapter 10 has real
    downloadable .xls/.xlsx + .pdf files instead of .htm tables
  - 2016-2026: WordPress site, files under
    <base>/wp-content/uploads/sites/<N>/<YYYY>/<MM>/10.X.(pdf|xlsx)
    (N and MM vary by year and aren't predictable, so each year's page is
    fetched and scraped for the actual paths rather than guessed)

Usage: python3 fetch_yearbook_tourism.py
"""
import re
import time
import urllib.request
from pathlib import Path

OUT_ROOT = Path(__file__).parent

# (year, page_to_scrape, tourism_dir_name_for_rewriting_relative_links)
OLD_SITE_YEARS = {
    2010: ("https://statisticsmaldives.gov.mv/yearbook2010/yearbook.html",
           "https://statisticsmaldives.gov.mv/yearbook2010/"),
    2011: ("https://statisticsmaldives.gov.mv/YearBook2011/yearbook.html",
           "https://statisticsmaldives.gov.mv/YearBook2011/"),
    2012: ("https://statisticsmaldives.gov.mv/yearbook2012/yearbook.html",
           "https://statisticsmaldives.gov.mv/yearbook2012/"),
    2013: ("https://statisticsmaldives.gov.mv/yearbook2013/yearbook.html",
           "https://statisticsmaldives.gov.mv/yearbook2013/"),
    2014: ("https://statisticsmaldives.gov.mv/yearbook2014/yearbook.html",
           "https://statisticsmaldives.gov.mv/yearbook2014/"),
    2015: ("https://statisticsmaldives.gov.mv/yearbook2015/index.html",
           "https://statisticsmaldives.gov.mv/yearbook2015/"),
}

# newer WordPress-based site: try the dedicated /tourism/ page first
# (2016-2018, 2020-2021), fall back to the single all-chapters index page
# (2019, 2022-2026) since some editions inline every chapter on one page.
WP_SITE_YEARS = {
    2016: "https://statisticsmaldives.gov.mv/yearbook/2016/",
    2017: "https://statisticsmaldives.gov.mv/yearbook/2017/",
    2018: "https://statisticsmaldives.gov.mv/yearbook/2018/",
    2019: "https://statisticsmaldives.gov.mv/yearbook/2019/",
    2020: "https://statisticsmaldives.gov.mv/yearbook/2020/",
    2021: "https://statisticsmaldives.gov.mv/yearbook/2021/",
    2022: "https://statisticsmaldives.gov.mv/yearbook/2022/",
    2023: "https://statisticsmaldives.gov.mv/yearbook/2023/",
    2024: "https://statisticsmaldives.gov.mv/yearbook/2024/",
    2025: "https://statisticsmaldives.gov.mv/yearbook/2025/",
    2026: "https://statisticsmaldives.gov.mv/yearbook/2026/",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (research data collection)"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    try:
        data = fetch(url)
    except Exception as e:
        # the source site has a handful of broken .xls links where the real
        # file was actually uploaded as .xlsx (e.g. 2014) -- try that once
        # before giving up.
        if url.endswith(".xls"):
            try:
                data = fetch(url + "x")
                dest = dest.with_suffix(".xlsx")
            except Exception:
                return f"FAILED: {e}"
        else:
            return f"FAILED: {e}"
    dest.write_bytes(data)
    return f"{len(data)} bytes -> {dest.name}"


# 2010 and 2011 use a JS tree-menu (Chrome-confirmed via manual expand)
# whose sub-item links are injected by JS and never appear in the static
# HTML at all, so they can't be scraped with a regex -- hardcode the
# relative paths found by expanding the Tourism node in a real browser.
HARDCODED_OLD_YEARS = {
    2010: ("https://statisticsmaldives.gov.mv/yearbook2010/",
           [f"yearbook/10_tourism/10.{i}.htm" for i in range(1, 10)]),
    2011: ("https://statisticsmaldives.gov.mv/YearBook2011/",
           [f"yearbook/Tourism/10.{i}.htm" for i in range(1, 12)]),
}


def handle_old_site_year(year: int, page_url: str, base_url: str, report: list):
    if year in HARDCODED_OLD_YEARS:
        base, relpaths = HARDCODED_OLD_YEARS[year]
        out_dir = OUT_ROOT / str(year)
        for rel in relpaths:
            fname = rel.split("/")[-1]
            status = download_file(base + rel, out_dir / fname)
            report.append((year, fname, status))
        return

    try:
        html = fetch_text(page_url)
    except Exception as e:
        report.append((year, page_url, f"FAILED to fetch index: {e}"))
        return

    # chapter-10 links: .htm (2010-2012, table pages) or .xls/.xlsx/.pdf
    # (2013-2015, real downloadable files); relative paths vary in casing
    # ("Tourism" vs "10_tourism") so match loosely.
    hrefs = re.findall(r'href="([^"]*10\.\d+\.(?:htm|xls|xlsx|pdf))"', html, re.I)
    hrefs = sorted(set(hrefs))
    if not hrefs:
        report.append((year, page_url, "no chapter-10 files found on index page"))
        return

    out_dir = OUT_ROOT / str(year)
    for href in hrefs:
        file_url = href if href.startswith("http") else base_url + href
        fname = href.split("/")[-1]
        dest = out_dir / fname
        status = download_file(file_url, dest)
        report.append((year, fname, status))


def handle_wp_year(year: int, base_url: str, report: list):
    candidates = [base_url + "tourism/", base_url]
    hrefs = set()
    used_url = None
    for url in candidates:
        try:
            html = fetch_text(url)
        except Exception as e:
            report.append((year, url, f"FAILED to fetch: {e}"))
            continue
        found = re.findall(r'(https?://[^"\']*?/10\.\d+\.(?:pdf|xlsx))', html)
        if found:
            hrefs.update(found)
            used_url = url
            break  # dedicated tourism page worked; no need for the full index
        # some years' /tourism/ page 404s outright (caught above) or is
        # empty; try the next candidate (the full index page)

    if not hrefs:
        # last resort: full index page even if the dedicated page had 0 matches
        try:
            html = fetch_text(base_url)
            hrefs.update(re.findall(r'(https?://[^"\']*?/10\.\d+\.(?:pdf|xlsx))', html))
            used_url = base_url
        except Exception as e:
            report.append((year, base_url, f"FAILED to fetch fallback index: {e}"))

    if not hrefs:
        report.append((year, base_url, "no chapter-10 files found"))
        return

    out_dir = OUT_ROOT / str(year)
    for file_url in sorted(hrefs):
        fname = file_url.split("/")[-1]
        dest = out_dir / fname
        status = download_file(file_url, dest)
        report.append((year, fname, status))


def main():
    report = []

    for year, (page_url, base_url) in sorted(OLD_SITE_YEARS.items()):
        handle_old_site_year(year, page_url, base_url, report)
        time.sleep(0.3)

    for year, base_url in sorted(WP_SITE_YEARS.items()):
        handle_wp_year(year, base_url, report)
        time.sleep(0.3)

    report_path = OUT_ROOT / "download_report.txt"
    with report_path.open("w") as f:
        for year, name, status in report:
            f.write(f"{year}  {name:50s}  {status}\n")

    by_year = {}
    for year, name, status in report:
        by_year.setdefault(year, []).append(status)

    print(f"{'Year':6}{'Files found':14}{'Downloaded':12}{'Skipped':10}{'Failed':8}")
    for year in sorted(by_year):
        statuses = by_year[year]
        downloaded = sum(1 for s in statuses if s not in ("skip",) and not s.startswith("FAILED"))
        skipped = sum(1 for s in statuses if s == "skip")
        failed = sum(1 for s in statuses if s.startswith("FAILED"))
        print(f"{year:<6}{len(statuses):<14}{downloaded:<12}{skipped:<10}{failed:<8}")
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()

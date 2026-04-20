# Q1 Onion Scraper

Single-file Python solution for the Q1 web scraping assessment.

This repository intentionally keeps only implementation and documentation. It does **not** store solved output values or submission answers.

## What This Task Was

The assessment required solving 12 scraping tasks across 4 simulated `.onion` sections:

- E-commerce (tasks 1-3)
- News (tasks 4-6)
- Social feed/profiles (tasks 7-9)
- Forum users/threads (tasks 10-12)

Each task depended on extracting specific fields and computing aggregates such as totals, averages, counts, or top entries.

## What We Built

The script in [scraper.py](scraper.py):

- Crawls each section with pagination support
- Resolves relative links safely (including `<base href>` handling)
- Extracts data from visible text and hidden HTML attributes
- Reuses cached pages to avoid duplicate requests
- Computes all task results and prints a JSON object with `task1` to `task12`

Network access is done through Tor SOCKS (`127.0.0.1:9050`) using `curl`.

## Key Problems Faced and How We Solved Them

1. Unstable onion responses and slow pages
- Added retry logic with backoff in `fetch_html`.

2. Different pagination/link patterns in each section
- Implemented generic page traversal and URL normalization.

3. Relative URL issues due to base tags
- Added `resolve_href` to combine current page URL, `<base>`, and relative paths correctly.

4. Hidden values not always in visible text
- Read `data-*` attributes and embedded payloads where needed.

5. Number format inconsistencies
- Centralized parsing helpers (`to_int`, `to_float`) for robust cleanup and conversion.

6. Repeated fetches reducing speed
- Added in-memory soup cache to avoid refetching the same pages.

## Repository Contents

- [scraper.py](scraper.py): complete solver for tasks 1-12
- [README.md](README.md): task context + implementation notes

No per-question dumps, logs, snapshots, cache files, or answer artifacts are included in this clean version.

## Setup

Requirements:

- Python 3.10+
- `curl`
- Tor with SOCKS endpoint at `127.0.0.1:9050`
- `beautifulsoup4`

Install and run:

```bash
python3 -m venv .venv_wsl
source .venv_wsl/bin/activate
pip install beautifulsoup4
python q1/scraper.py
```

## Output Policy

The script prints a JSON object with keys `task1` to `task12`.

For academic integrity and clean publication, this repo does not publish solved values.

## Usage Boundaries

This project is only for the authorized educational simulation.

- Do not use on unauthorized targets.
- Respect site terms and applicable laws.

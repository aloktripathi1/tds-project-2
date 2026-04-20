# TDS Project 2

Clean submission repository for Project 2, organized into two parts:

- `p1`: Onion web scraping solution (Python)
- `p2`: Solana Devnet transfer helper (Node.js)

This repository intentionally keeps only source code and documentation.
It does not include answer dumps, logs, cache files, private keys, or local environment files.

## Repository Structure

- `p1/scraper.py`: full scraper implementation for tasks 1 to 12
- `p1/README.md`: context, approach, and usage notes for P1
- `p2/send-devnet-transfer.mjs`: transfer + memo validation script for Devnet
- `p2/README.md`: context, usage notes, and security guidance for P2

## Part 1 (P1) Summary

P1 solves a multi-section onion scraping assessment by:

- crawling paginated pages across sections
- resolving relative URLs (including base href handling)
- extracting visible and hidden fields from HTML
- computing required aggregates and task outputs

See `p1/README.md` for full implementation notes and run instructions.

## Part 2 (P2) Summary

P2 sends an exact Solana Devnet transfer with an exact memo and verifies both on finalized transaction data.

See `p2/README.md` for environment variables and run instructions.

## Security and Integrity

- No solved answer values are stored in this repo.
- No private key material is committed.
- This work is for authorized educational use only.
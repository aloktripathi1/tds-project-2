# TDS Project 2

Clean submission repository for Project 2, organized into two parts:

- `q1`: Onion web scraping solution (Python)
- `q2`: Solana Devnet transfer helper (Node.js)

This repository intentionally keeps only source code and documentation.
It does not include answer dumps, logs, cache files, private keys, or local environment files.

## Repository Structure

- `q1/scraper.py`: full scraper implementation for tasks 1 to 12
- `q1/README.md`: context, approach, and usage notes for Q1
- `q2/send-devnet-transfer.mjs`: transfer + memo validation script for Devnet
- `q2/README.md`: context, usage notes, and security guidance for Q2

## Q1 Summary

Q1 solves a multi-section onion scraping assessment by:

- crawling paginated pages across sections
- resolving relative URLs (including base href handling)
- extracting visible and hidden fields from HTML
- computing required aggregates and task outputs

See `q1/README.md` for full implementation notes and run instructions.

## Q1 Problem Statements (No Answers)

1. Compute total inventory value for Home category products.
2. Find the SKU with highest review count in Outdoors category.
3. Compute average rating of out-of-stock Electronics products.
4. Sum internal views across all Sports news articles.
5. Compute rounded average internal views across Politics articles.
6. Find Sports article id with highest internal views.
7. Find handle with highest followers among users in Catherinefurt.
8. Sum likes across posts containing hashtag `#coding`.
9. Count profiles with location equal to Traciefort.
10. Sum user reputation for accounts joined during 2025-09.
11. Find leaks thread id with the highest views.
12. Sum reputation of all users marked as Vendor.

## Q2 Summary

Q2 sends an exact Solana Devnet transfer with an exact memo and verifies both on finalized transaction data.

See `q2/README.md` for environment variables and run instructions.

## Security and Integrity

- No solved answer values are stored in this repo.
- No private key material is committed.
- This work is for authorized educational use only.
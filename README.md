# Project 2 - Tools in Data Science (Jan 2026)

This repo contains my end-to-end solutions for Project 2, organized by question with reproducible scripts.

## What's Inside

| Folder | Focus |
|---|---|
| q1 | Onion web scraping workflow (12 tasks) |
| q2 | Solana Devnet exact transfer plus memo |

## Tech Snapshot

- Languages: Python, JavaScript
- Runtime: Python 3.10+, Node.js 18+
- Key libraries: beautifulsoup4, @solana/web3.js, dotenv, bs58

## Quick Start

```bash
cd tds-project-2

# Q1 setup
python3 -m venv .venv_wsl
source .venv_wsl/bin/activate
pip install beautifulsoup4

# Q2 runtime deps
cd q2
npm install @solana/web3.js dotenv bs58
cd ..
```

## Runbook

- Q1: [q1/README.md](q1/README.md)
- Q2: [q2/README.md](q2/README.md)

Common commands:

```bash
# Q1
python q1/scraper.py

# Q2
TO_ADDRESS="<vault-address>" \
AMOUNT_SOL="<exact-sol-amount>" \
MEMO_TEXT="<exact-memo>" \
SECRET_KEY="<json-array-or-base58-private-key>" \
node q2/send-devnet-transfer.mjs
```

## Notes

- Keep secrets and private keys out of git.
- Use environment variables for credentials.
- Follow each question README for exact task-specific details.
- This repo intentionally does not publish solved answer values.
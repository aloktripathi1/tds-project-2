# Q2 Solana Devnet Transfer Script

Single-file JavaScript solution for the Q2 transfer task.

This folder intentionally keeps only implementation and documentation. It does not include private keys, `.env` files, dependency lockfiles, or generated output.

## What This Task Was

The task required sending an exact Solana Devnet transfer to a target vault and attaching an exact memo in the same transaction.

Validation depended on both:

- exact lamport amount
- exact memo text match

## What We Built

The script in [send-devnet-transfer.mjs](send-devnet-transfer.mjs):

- parses SOL amount safely into lamports (with precision checks)
- loads signer key from environment (`SECRET_KEY` or `KEYPAIR_PATH`)
- enforces Devnet RPC by checking genesis hash
- builds one transaction with transfer + Memo program instruction
- confirms at finalized commitment
- re-reads parsed transaction and verifies exact transfer and memo

## Repository Contents

- [send-devnet-transfer.mjs](send-devnet-transfer.mjs): complete task script
- [README.md](README.md): task context and run instructions

## Run Locally

Install runtime dependencies once in this folder:

```bash
cd q2
npm install @solana/web3.js dotenv bs58
```

Set required environment variables and run:

```bash
TO_ADDRESS="<vault-address>" \
AMOUNT_SOL="<exact-sol-amount>" \
MEMO_TEXT="<exact-memo>" \
SECRET_KEY="<json-array-or-base58-private-key>" \
node send-devnet-transfer.mjs
```

Optional variables:

- `RPC_URL` (defaults to `https://api.devnet.solana.com`)
- `KEYPAIR_PATH` (alternative to `SECRET_KEY`)

## Security Notes

- Never commit private keys.
- Use Devnet-only funds and credentials for this task.
- Do not reuse any assessment key material in mainnet wallets.

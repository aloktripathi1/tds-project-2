import fs from "node:fs";
import path from "node:path";
import process from "node:process";

import dotenv from "dotenv";
import bs58 from "bs58";
import {
  Connection,
  Keypair,
  LAMPORTS_PER_SOL,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionInstruction,
} from "@solana/web3.js";

dotenv.config();

const MEMO_PROGRAM_ID = new PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr");

const DEVNET_GENESIS_HASH = "EtWTRABZaYq6iMfeYKouRu166VU2xqa1";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function parseSolToLamports(solText) {
  const raw = String(solText || "").trim();
  if (!raw) {
    throw new Error("AMOUNT_SOL is required.");
  }
  if (!/^\d+(\.\d+)?$/.test(raw)) {
    throw new Error(`Invalid AMOUNT_SOL: ${raw}`);
  }

  const [whole, frac = ""] = raw.split(".");
  if (frac.length > 9) {
    throw new Error("AMOUNT_SOL has more than 9 decimal places.");
  }

  const fracPadded = frac.padEnd(9, "0");
  const lamportsBig = BigInt(whole) * BigInt(LAMPORTS_PER_SOL) + BigInt(fracPadded);

  if (lamportsBig <= 0n) {
    throw new Error("AMOUNT_SOL must be greater than 0.");
  }
  if (lamportsBig > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new Error("Lamport value is too large for web3.js number APIs.");
  }

  return Number(lamportsBig);
}

function loadSecretKeyBytes() {
  const inline = process.env.SECRET_KEY?.trim();
  const filePath = process.env.KEYPAIR_PATH?.trim();

  if (inline) {
    if (inline.startsWith("[")) {
      return Uint8Array.from(JSON.parse(inline));
    }
    return bs58.decode(inline);
  }

  if (filePath) {
    const resolved = path.resolve(filePath);
    const content = fs.readFileSync(resolved, "utf8").trim();
    if (content.startsWith("[")) {
      return Uint8Array.from(JSON.parse(content));
    }
    return bs58.decode(content);
  }

  return null;
}

async function ensureFunds(connection, from, requiredLamports) {
  const currentBalance = await connection.getBalance(from.publicKey, "confirmed");
  if (currentBalance >= requiredLamports) {
    return currentBalance;
  }

  const target = Math.max(requiredLamports + 1000000, 2000000);
  const needed = target - currentBalance;
  const airdrop = Math.min(needed, 2000000000);

  for (let attempt = 1; attempt <= 4; attempt += 1) {
    try {
      const airdropSig = await connection.requestAirdrop(from.publicKey, airdrop);
      await connection.confirmTransaction(airdropSig, "confirmed");
      const balanceAfter = await connection.getBalance(from.publicKey, "confirmed");
      if (balanceAfter >= requiredLamports) {
        return balanceAfter;
      }
    } catch (error) {
      if (attempt === 4) {
        throw error;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, attempt * 1200));
  }

  throw new Error("Unable to airdrop enough Devnet SOL for this transfer.");
}

async function assertDevnet(connection) {
  const genesisHash = await connection.getGenesisHash();
  if (genesisHash !== DEVNET_GENESIS_HASH) {
    throw new Error(
      `RPC endpoint is not Solana Devnet (genesis hash ${genesisHash}). Use a Devnet RPC URL.`
    );
  }
}

function normalizeMemoFromInstruction(ix) {
  if (!ix) {
    return "";
  }

  if (typeof ix.parsed === "string") {
    return ix.parsed;
  }

  if (ix.parsed && typeof ix.parsed.memo === "string") {
    return ix.parsed.memo;
  }

  if (typeof ix.data === "string") {
    try {
      return Buffer.from(bs58.decode(ix.data)).toString("utf8");
    } catch {
      return ix.data;
    }
  }

  return "";
}

async function waitForParsedTransaction(connection, signature, timeoutMs = 90000) {
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const parsed = await connection.getParsedTransaction(signature, {
      commitment: "finalized",
      maxSupportedTransactionVersion: 0,
    });

    if (parsed) {
      return parsed;
    }

    await sleep(1200);
  }

  throw new Error(
    "Timed out waiting for finalized transaction details from RPC. Retry submission in a few seconds."
  );
}

function verifyTransactionContent(parsedTx, expectedTo, expectedLamports, expectedMemo) {
  if (!parsedTx?.meta || parsedTx.meta.err) {
    throw new Error(`Transaction failed on-chain: ${JSON.stringify(parsedTx?.meta?.err ?? null)}`);
  }

  const instructions = parsedTx.transaction?.message?.instructions || [];

  let transferMatched = false;
  let memoMatched = false;

  for (const ix of instructions) {
    if (
      ix?.program === "system" &&
      ix?.parsed?.type === "transfer" &&
      ix?.parsed?.info?.destination === expectedTo &&
      Number(ix?.parsed?.info?.lamports) === expectedLamports
    ) {
      transferMatched = true;
    }

    const programId = ix?.programId?.toBase58?.() || ix?.programId;
    if (programId === MEMO_PROGRAM_ID.toBase58()) {
      const memo = normalizeMemoFromInstruction(ix);
      if (memo === expectedMemo) {
        memoMatched = true;
      }
    }
  }

  if (!transferMatched) {
    throw new Error("Finalized transaction does not include the exact transfer to the target vault.");
  }

  if (!memoMatched) {
    throw new Error("Finalized transaction does not include an exact memo match.");
  }
}

async function main() {
  const rpcUrl = process.env.RPC_URL?.trim() || "https://api.devnet.solana.com";
  const toAddress = process.env.TO_ADDRESS?.trim();
  const memoText = process.env.MEMO_TEXT ?? "";

  if (!toAddress) {
    throw new Error("TO_ADDRESS is required.");
  }
  if (!memoText.trim()) {
    throw new Error("MEMO_TEXT is required.");
  }

  const lamports = parseSolToLamports(process.env.AMOUNT_SOL);
  const loaded = loadSecretKeyBytes();
  const from = loaded ? Keypair.fromSecretKey(loaded) : Keypair.generate();
  const toPubkey = new PublicKey(toAddress);
  const connection = new Connection(rpcUrl, {
    commitment: "finalized",
    disableRetryOnRateLimit: true,
  });

  await assertDevnet(connection);

  await ensureFunds(connection, from, lamports + 1000000);

  const transferIx = SystemProgram.transfer({
    fromPubkey: from.publicKey,
    toPubkey,
    lamports,
  });

  const memoIx = new TransactionInstruction({
    programId: MEMO_PROGRAM_ID,
    keys: [],
    data: Buffer.from(memoText, "utf8"),
  });

  const tx = new Transaction().add(transferIx, memoIx);
  tx.feePayer = from.publicKey;

  const latest = await connection.getLatestBlockhash("finalized");
  tx.recentBlockhash = latest.blockhash;
  tx.sign(from);

  const signature = await connection.sendRawTransaction(tx.serialize(), {
    skipPreflight: false,
    preflightCommitment: "confirmed",
    maxRetries: 8,
  });

  await connection.confirmTransaction(
    {
      signature,
      blockhash: latest.blockhash,
      lastValidBlockHeight: latest.lastValidBlockHeight,
    },
    "finalized"
  );

  const parsedTx = await waitForParsedTransaction(connection, signature);
  verifyTransactionContent(parsedTx, toPubkey.toBase58(), lamports, memoText);

  console.log("Sender:", from.publicKey.toBase58());
  console.log("SignerSource:", loaded ? "provided-key" : "ephemeral-generated");
  console.log("Receiver:", toPubkey.toBase58());
  console.log("Lamports:", lamports);
  console.log("Memo:", memoText);
  console.log("Commitment:", "finalized");
  console.log("VerifiedExactTransfer:", "yes");
  console.log("VerifiedExactMemo:", "yes");
  console.log("TxID:", signature);
  console.log("Explorer:", `https://explorer.solana.com/tx/${signature}?cluster=devnet`);
}

main().catch((error) => {
  console.error("Failed:", error.message || error);
  process.exitCode = 1;
});

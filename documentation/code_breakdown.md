---

## `src/api_handler.py` — Claude integration

**What it does:** Calls Claude once to get a hex seed, builds S-box and P-box from it.

**Key lines to know:**
- The prompt to Claude asks for a 64-char hex string — not the boxes themselves
- `_make_permutation()` — takes the seed and runs Fisher-Yates shuffle
- `get_sbox_and_pbox()` — the only function called from outside this file
- Fixed point elimination loop — makes sure no byte maps to itself in the S-box

**If asked:** "Claude generates a random seed. Python uses that seed to build the tables using Fisher-Yates. Claude determines the outcome, Python does the construction."

---

## `src/engine.py` — the cipher itself

**What it does:** All the actual encryption and decryption logic.

**Key lines to know:**
- Line 8 `KeySchedule` — takes your password, runs SHA-256 to produce 17 subkeys
- Line 17 `AddRoundKey` — XORs the block with a round key, one line of code
- Line 21 `SubBytes` — one line, replaces every byte using the S-box lookup
- Line 25 `PermuteBits` — converts block to 128 bits, rearranges them using P-box, converts back
- Line 45 `encrypt` — the full encrypt loop, 16 rounds of SubBytes → PermuteBits → AddRoundKey
- Line 56 `decrypt` — runs the same 16 rounds in reverse with inverse tables

**If asked:** "Everything in this file is custom Python. No crypto libraries. The encrypt function runs 16 rounds and each round applies all three operations to every 128-bit block."

---

## `src/utils.py` — padding helpers

**What it does:** Handles PKCS#7 padding so any message length works with 16-byte blocks.

**Key lines to know:**
- `pkcs7_pad` — figures out how many bytes to add, appends that many bytes each with the padding value
- `pkcs7_unpad` — reads the last byte to know how much to strip, verifies it first
- `bytes_to_bits` — converts 16 bytes into a list of 128 individual 1s and 0s for the P-box
- `bits_to_bytes` — converts them back after the P-box rearranges them

**If asked:** "Padding makes sure the message is always a multiple of 16 bytes. If the message is 7 bytes, we add 9 bytes each with the value 9. On decrypt we read that value and strip it off."

---

## `src/main.py` — the web server

**What it does:** Flask server that serves the GUI and handles API routes.

**Key lines to know:**
- `_save_session` / `_load_session` — reads and writes `session_keys.json`
- `/api/encrypt` route — calls `get_sbox_and_pbox()`, saves session, runs the cipher
- `/api/decrypt` route — loads session from file, runs cipher in reverse
- `/api/session-keys` route — returns current S-box and P-box to the GUI for the grid display
- `main()` at the bottom — starts Flask and auto-opens the browser

**If asked:** "Main.py is just the web layer. It receives the message and key from the browser, calls the engine to encrypt or decrypt, and sends the result back. The cipher logic lives entirely in engine.py."

---

## `tests/test_obsidian.py` — test suite

**What it does:** 25 tests that verify the cipher works correctly without any API calls.

**If asked:** "All tests use hardcoded S-boxes and P-boxes so they run instantly without needing a Claude API key. They test encrypt/decrypt roundtrip, padding, key schedule, edge cases. GitHub Actions runs them on every push."

---

## Quick cheat sheet for the demo

| Someone asks about | Point to |
|---|---|
| How Claude is involved | `api_handler.py` — `get_sbox_and_pbox()` |
| Where encryption happens | `engine.py` — `encrypt()` line 45 |
| Where the S-box is applied | `engine.py` — `SubBytes()` line 21 |
| Where the P-box is applied | `engine.py` — `PermuteBits()` line 25 |
| How the key works | `engine.py` — `KeySchedule()` line 8 |
| How the GUI talks to the cipher | `main.py` — `/api/encrypt` route |
| Where session keys are stored | `session_keys.json` at project root |
| Why padding exists | `utils.py` — `pkcs7_pad()` line 4 |
# Project Obsidian

A custom 128-bit symmetric block cipher built on a **Substitution-Permutation Network (SPN)** architecture. Designed as a STEM demonstration of foundational symmetric cryptography, with Claude (Anthropic AI) as a live cryptographic entropy source and a dark tactical browser-based GUI.

## What It Does

Project Obsidian encrypts and decrypts text using a fully custom cipher — no AES, no PyCryptodome. Every encryption session is uniquely keyed by Claude, which generates a cryptographic seed that drives the construction of fresh S-box and P-box lookup tables. The same key + same session tables always reproduce the original plaintext.

---

## Features

- **16-round SPN** — SubBytes → PermuteBits → AddRoundKey per round, fully custom Python
- **Claude-keyed sessions** — Claude generates a unique hex seed each encrypt; Fisher-Yates builds the S-box and P-box locally from that seed
- **Minimal API usage** — exactly 1 API call per Encrypt click; Decrypt is always free
- **Local web GUI** — Flask serves a dark tactical single-page app at `http://localhost:5000`
- **Full reversibility** — inverse tables are auto-derived; `Decrypt(Encrypt(msg, key), key) == msg` guaranteed
- **PKCS#7 padding** — supports any message length
- **Zero external dependencies for crypto** — every primitive is hand-written

---

## How the Claude Integration Works

When you click **Encrypt**, the app makes a single API call asking Claude to return a random 64-character hex string. That string is converted to an integer seed, which is fed into Python's Fisher-Yates shuffle algorithm to generate the S-box (256 entries) and P-box (128 entries). The tables are saved locally to `session_keys.json` for free decryption.

This approach replaces an earlier design that asked Claude to enumerate all 256 values directly — which failed 30–40% of the time due to how language models generate tokens. The seed approach is faster (< 1 second vs 10–15 seconds), always valid, and mathematically stronger.

See [`docs/algorithm.md`](docs/algorithm.md) for the full technical breakdown.

## Project Structure

Obsidian-Cipher/
├── src/
│ ├── main.py # Flask web server — serves GUI and API routes
│ ├── engine.py # SPN cipher core (SubBytes, PermuteBits, KeySchedule)
│ ├── api_handler.py # Claude API integration — seed generation + box construction
│ ├── utils.py # PKCS#7 padding helpers
│ ├── init.py
│ └── templates/
│ └── index.html # Project Obsidian GUI — dark stone/gunmetal theme
├── docs/
│ ├── algorithm.md # Full algorithm and design documentation
│ ├── claude_keyed_generation.md # Deep dive on seed-driven S/P-box approach
│ └── presentation_assets/ # Diagrams and slides
├── tests/
│ └── test_obsidian.py # 25 pytest tests — no API key required
├── .github/
│ └── workflows/
│ └── ci.yml # GitHub Actions — runs tests on every push
├── .env # ANTHROPIC_API_KEY (never committed)
├── requirements.txt
└── README.md
---

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/GabeT3ch/Obsidian-Cipher.git
cd Obsidian-Cipher
pip install -r requirements.txt
```

### 2. Set your API key

Create a `.env` file in the project root:
Get your key from [console.anthropic.com](https://console.anthropic.com). A $5 credit is more than enough — each encrypt call costs a fraction of a cent.

### 3. Launch

```bash
python -m src.main
```

Browser opens automatically at **`http://localhost:5000`**.

---

## Using the GUI

### Encrypt

1. Type your message in **Plaintext Message**
2. Enter a **Secret Key** (any string)
3. Click **⚡ Encrypt**

Claude generates a session seed → S-box and P-box are built locally → message is encrypted → hex ciphertext is displayed and auto-filled into the Decrypt tab.

### Decrypt

1. Paste the hex ciphertext (auto-filled if you just encrypted)
2. Enter the **same Secret Key**
3. Click **🔍 Decrypt**

No API call. Session tables are loaded from `session_keys.json`.

### Session Badge

- **Red** — no session keys yet, encrypt first
- **Green** — session keys active, ready to decrypt

---

## API Usage

| Action | API Calls | What Happens |
| Click Encrypt | **1** | Claude returns hex seed → boxes built → saved to `session_keys.json` |
| Click Decrypt | **0** | Loads boxes from `session_keys.json` |
| Click Encrypt again | **1** | New seed → new boxes → overwrites previous session |

---

## Run Tests

```bash
python -m pytest tests/test_obsidian.py -v
```

All 25 tests use hardcoded deterministic fixtures — no API key or network required. Tests run automatically on every push via GitHub Actions.

## Algorithm Summary

Encrypt:
Plaintext → PKCS#7 Pad → AddRoundKey(K0) → 16×[SubBytes → PermuteBits → AddRoundKey(Ki)] → Ciphertext
Decrypt:
Ciphertext → 16×[AddRoundKey(Ki) → InvPermuteBits → InvSubBytes] → AddRoundKey(K0) → PKCS#7 Unpad → Plaintext

| Property | Value |
| Block size | 128 bits (16 bytes) |
| Rounds | 16 |
| Key schedule | SHA-256 derived — 17 independent 16-byte subkeys |
| S-box | 256-entry byte substitution, no fixed points |
| P-box | 128-entry bit permutation, high inter-byte diffusion |
| Claude model | `claude-sonnet-4-6` |
| Claude's role | Generates unique hex seed per session |
| Box construction | Fisher-Yates shuffle seeded by Claude's output |

---

## Security Notice

Project Obsidian is an **educational prototype**. It operates in ECB mode and is not suitable for production data protection. For real-world encryption use AES-GCM or ChaCha20-Poly1305 from a vetted library.

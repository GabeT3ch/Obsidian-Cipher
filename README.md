---
# Obsidian Cipher

A custom 128-bit symmetric block cipher built on a **Substitution-Permutation Network (SPN)** architecture. Designed for STEM Day demonstration of foundational symmetric cryptography 

---

## Features

- **16-round SPN** — SubBytes → PermuteBits → AddRoundKey per round
- **Dynamic S-box & P-box** — generated fresh each session via the Anthropic Claude API
- **Minimal API usage** — the API is called **exactly once** per Encrypt click; Decrypt reuses saved session keys at zero additional cost
- **Local web GUI** — Flask server opens automatically at `http://localhost:5000`
- **Full reversibility** — inverse S-box and P-box are auto-derived; `Decrypt(Encrypt(P)) == P` guaranteed
- **PKCS#7 padding** — supports arbitrary-length messages
- **No PyCryptodome** — all cryptographic primitives are custom Python

---

## Quick Start

### 1. Install dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Add your API key to `.env`
\`\`\`
ANTHROPIC_API_KEY=sk-ant-...
\`\`\`

### 3. Launch the GUI
\`\`\`bash
python -m src.main
\`\`\`

Browser opens automatically at **http://localhost:5000**

---

## API Usage

| Action | API calls |
|--------|-----------|
| Click ENCRYPT | **1** — generates & saves session keys |
| Click DECRYPT | **0** — loads from session_keys.json |

---

## Run Tests
\`\`\`bash
python -m pytest tests/test_obsidian.py -v
\`\`\`
25 tests, no API key required.

---
# Project Obsidian

A custom 128-bit symmetric block cipher built on a Substitution-Permutation Network (SPN) architecture. Demonstrates foundational symmetric cryptography with Claude (Anthropic AI) as a live cryptographic entropy source and a dark tactical browser-based GUI.

---

## Built With

| Layer | Technology |
| Backend | Python 3 |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Web Framework | Flask |
| AI Integration | Anthropic Claude API (claude-sonnet-4-6) |
| Key Generation | Python random.Random, Fisher-Yates shuffle |
| Key Schedule | Python hashlib (SHA-256) |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Config | python-dotenv |

---

## How It Works

Every encrypt operation makes one API call to Claude, which returns a random 64-character hex string. That seed is fed into Fisher-Yates to build a unique S-box (256 entries) and P-box (128 entries) for the session. The cipher then runs 16 rounds of SubBytes, PermuteBits, and AddRoundKey on each 128-bit block. Session tables are saved locally so decrypt costs zero additional API calls.

---

## Quick Start

    git clone https://github.com/GabeT3ch/Obsidian-Cipher.git
    cd Obsidian-Cipher
    pip install -r requirements.txt

Create a .env file in the project root:

    ANTHROPIC_API_KEY=sk-ant-api03-...

Launch:

    python -m src.main

Browser opens automatically at http://localhost:5000

---

## Project Structure

    src/
        main.py          Flask server and API routes
        engine.py        SPN cipher core
        api_handler.py   Claude API and box generation
        utils.py         PKCS#7 padding
        templates/
            index.html   GUI
    docs/
        algorithm.md     Full algorithm documentation
    tests/
        test_obsidian.py 25 deterministic pytest tests
    .github/workflows/
        ci.yml           Runs tests on every push

---

## Run Tests

    python -m pytest tests/test_obsidian.py -v

No API key required. All 25 tests use hardcoded fixtures.

---

## Security Notice

Educational prototype only. Operates in ECB mode. Not suitable for production data protection.


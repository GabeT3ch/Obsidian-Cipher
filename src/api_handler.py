import json
import os
import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

_PROMPT = """You are a cryptographic assistant. Generate two lookup tables for a block cipher.

1. S-Box: A permutation of integers 0 through 255 (exactly 256 distinct values, each appearing exactly once). No fixed points (S[i] != i for all i). Values must be non-linear with no obvious arithmetic pattern.
2. P-Box: A permutation of integers 0 through 127 (exactly 128 distinct values, each appearing exactly once). Designed for high diffusion: output bit i should draw from a different byte than input bit i wherever possible.

Return ONLY valid JSON with exactly this structure — no commentary, no markdown fences:
{"sbox": [<256 integers>], "pbox": [<128 integers>]}"""


def _validate_sbox(sbox: list) -> None:
    if not isinstance(sbox, list) or len(sbox) != 256:
        raise ValueError(f"sbox must be a 256-element list, got len={len(sbox) if isinstance(sbox, list) else 'N/A'}")
    if sorted(sbox) != list(range(256)):
        raise ValueError("sbox must be a permutation of 0-255")


def _validate_pbox(pbox: list) -> None:
    if not isinstance(pbox, list) or len(pbox) != 128:
        raise ValueError(f"pbox must be a 128-element list, got len={len(pbox) if isinstance(pbox, list) else 'N/A'}")
    if sorted(pbox) != list(range(128)):
        raise ValueError("pbox must be a permutation of 0-127")


def get_sbox_and_pbox() -> tuple:
    """
    Call the Anthropic API once to generate session S-box and P-box.
    Returns (sbox, pbox) as validated lists.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set — add it to your .env file")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": _PROMPT}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if model includes them despite instructions
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(ln for ln in lines if not ln.startswith("```")).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"API response is not valid JSON: {exc}\nRaw (first 300 chars): {raw[:300]}") from exc

    if "sbox" not in data or "pbox" not in data:
        raise ValueError(f"Response missing required keys. Got: {list(data.keys())}")

    _validate_sbox(data["sbox"])
    _validate_pbox(data["pbox"])

    return data["sbox"], data["pbox"]

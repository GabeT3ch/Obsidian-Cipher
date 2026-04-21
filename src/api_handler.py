import os
import random
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

_PROMPT = "Generate a random hexadecimal string of exactly 64 characters for cryptographic use. Return ONLY the hex string, nothing else."


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


def _make_permutation(n: int, seed: int, salt: str) -> list:
    perm = list(range(n))
    r = random.Random(seed ^ hash(salt))
    r.shuffle(perm)
    if n == 256:
        for i in range(n):
            if perm[i] == i:
                j = (i + 1) % n
                perm[i], perm[j] = perm[j], perm[i]
    return perm


def get_sbox_and_pbox() -> tuple:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set — add it to your .env file")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL,
        max_tokens=128,
        messages=[{"role": "user", "content": _PROMPT}],
    )

    raw = message.content[0].text.strip().lower()
    hex_chars = ''.join(c for c in raw if c in '0123456789abcdef')
    if len(hex_chars) < 16:
        hex_chars = hex_chars.ljust(16, '0')

    seed = int(hex_chars[:16], 16)

    sbox = _make_permutation(256, seed, "sbox")
    pbox = _make_permutation(128, seed, "pbox")

    _validate_sbox(sbox)
    _validate_pbox(pbox)

    return sbox, pbox


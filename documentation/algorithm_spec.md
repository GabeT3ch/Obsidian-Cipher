---
Plaintext Block (128 bits)
AddRoundKey(K0) ← initial whitening
|
┌─────▼──────────────────────────────┐
│ SubBytes (S-box, byte-wise) │
│ PermuteBits (P-box, bit-wise) │ × 16 rounds
│ AddRoundKey (Ki, i = 1..16) │
└────────────────────────────────────┘
|
Ciphertext Block (128 bits)


**Decryption** reverses every operation in reverse round order:


Ciphertext Block
|
for r = 16 down to 1:
AddRoundKey(Kr)
InvPermuteBits (inverse P-box)
InvSubBytes (inverse S-box)
|
AddRoundKey(K0)
|
Plaintext Block


---

## Primitives

### AddRoundKey
XOR each byte of the 128-bit state with the corresponding byte of the 128-bit round key. XOR is its own inverse, so encryption and decryption use the same operation.

### SubBytes
Replace each byte `b` in the state with `S[b]`, where `S` is the 256-entry S-box. This provides **confusion** — it destroys the linear relationship between the plaintext and ciphertext.

The S-box is a permutation of {0, …, 255} with no fixed points, generated to be non-linear by the Anthropic API at session initialization.

**InvSubBytes** uses the inverse S-box: `S_inv[S[b]] = b` for all `b`.

### PermuteBits
Treats the 128-bit state as a sequence of 128 individual bits and rearranges them according to the P-box array, where `P[i] = j` means output bit `i` is taken from input bit `j`.

This provides **diffusion** — a single flipped input bit spreads its effect across multiple output bytes after each round.

The P-box is a permutation of {0, …, 127}, generated for high inter-byte diffusion by the Anthropic API.

**InvPermuteBits** uses the inverse P-box: `P_inv[P[i]] = i` for all `i`.

---

## Key Schedule

Obsidian derives **17 independent 16-byte subkeys** (K0 through K16) from the user's key:


master = SHA-256(user_key) # 32 bytes

K_i = SHA-256(master || i.to_bytes(2, 'big'))[:16] # for i in 0..16


- SHA-256 normalises keys of any length to a consistent 32 bytes.
- Binding the round index `i` ensures all 17 subkeys are distinct.
- SHA-256 is one-way: knowledge of one subkey does not reveal others.

---

## Dynamic S-box and P-box

At the start of each encrypt session, Obsidian calls the Anthropic Claude API
(`claude-haiku-4-5-20251001`) to generate a fresh S-box and P-box. This makes
every session cryptographically unique — the same plaintext and key will produce
different ciphertext each session.

**API usage policy (minimal):**

| Action | API calls |
|--------|-----------|
| Encrypt | **1** — tables generated and saved to `session_keys.json` |
| Decrypt | **0** — tables loaded from `session_keys.json` |

---

## Padding

PKCS#7 padding is applied before encryption and stripped after decryption:

- Append `n` bytes each with value `n`, where `n = 16 - (len(msg) % 16)`.
- If the message is already a multiple of 16 bytes, append a full block of 16 bytes each with value `0x10`.
- On unpad, read the last byte as `n`, verify all last `n` bytes equal `n`, then strip.

This guarantees the pad value is always in the range [1, 16] and unpadding is unambiguous.

---

## Confusion and Diffusion

The two core goals of any block cipher are:

**Confusion** (S-box) — makes the relationship between the key and ciphertext as complex as possible. Each output byte depends non-linearly on the input byte and the S-box, which is secret per session.

**Diffusion** (P-box + multiple rounds) — spreading the influence of each plaintext bit across the entire ciphertext. After a single PermuteBits operation, each bit has moved to a position in a different byte. After several rounds, every ciphertext bit depends on every plaintext bit — this is the **avalanche effect**.

---

## Security Notes

Obsidian is an **educational prototype**, not a production cryptographic primitive.

- ECB mode means identical plaintext blocks produce identical ciphertext blocks.
- The S-box and P-box source (LLM output) is not a cryptographically vetted generator.
- No authentication tag is included (no AEAD / integrity protection).

For real-world use, employ **AES-GCM** or **ChaCha20-Poly1305** from a vetted library.
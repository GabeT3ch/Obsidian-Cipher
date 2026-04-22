---

**`docs/algorithm.md`**

```markdown
# Project Obsidian — Algorithm Documentation

## Cipher Overview

Obsidian is a custom 128-bit symmetric block cipher built on a **Substitution-Permutation Network (SPN)** architecture. Every component is implemented from scratch in Python — no cryptographic libraries are used for the cipher operations.

| Property | Value |
|---|---|
| Block size | 128 bits (16 bytes) |
| Key size | Variable (any string, normalized via SHA-256) |
| Rounds | 16 |
| S-box | 256-entry byte substitution table |
| P-box | 128-entry bit permutation table |
| Padding | PKCS#7 |
| Mode | ECB |

---

## High-Level Encryption Flow

User Message (any length)
|
PKCS#7 Pad → multiple 128-bit blocks
|
for each block:
|
AddRoundKey(K0) ← initial whitening
|
┌────▼────────────────────────────────┐
│ SubBytes (S-box, byte-wise) │
│ PermuteBits (P-box, bit-wise) │ × 16 rounds
│ AddRoundKey (K1 through K16) │
└─────────────────────────────────────┘
|
Ciphertext Block (128 bits / 16 bytes)
|
Output as hex string

---

## High-Level Decryption Flow

Hex Ciphertext
|
Parse bytes → 128-bit blocks
|
for each block:
|
┌────▼────────────────────────────────┐
│ AddRoundKey (K16 down to K1) │
│ InvPermuteBits (inverse P-box) │ × 16 rounds (reversed)
│ InvSubBytes (inverse S-box) │
└─────────────────────────────────────┘
|
AddRoundKey(K0)
|
PKCS#7 Unpad
|
Original Plaintext

---

## Cipher Primitives

### 1. AddRoundKey

XOR every byte of the 128-bit state with the corresponding byte of the round key.

state[i] = state[i] XOR key[i] for i in 0..15

XOR is its own inverse — the same operation is used in both encryption and decryption. This operation binds the key to the data at every round.

---

### 2. SubBytes (Substitution)

Replace every byte in the 16-byte state block with its S-box lookup value:

state[i] = S[state[i]] for i in 0..15

The S-box is a 256-entry array where `S[b]` gives the substituted value for byte `b`. It is a permutation of {0, …, 255} with no fixed points (S[i] ≠ i for all i).

**Purpose:** Provides **confusion** — destroys the linear relationship between the plaintext and the ciphertext.

**InvSubBytes** applies the inverse table:

inv_S[S[b]] = b for all b in 0..255

---

### 3. PermuteBits (Permutation)

Treats the entire 128-bit state as a sequence of 128 individual bits and rearranges them:

output_bit[P[i]] = input_bit[i] for i in 0..127

**Purpose:** Provides **diffusion** — spreads the influence of a single input bit across multiple output bytes. After several rounds, every output bit depends on many input bits.

**InvPermuteBits** applies the inverse permutation:

inv_P[P[i]] = i for all i in 0..127

---

## Key Schedule

Obsidian derives 17 independent 128-bit subkeys (K0 through K16) from the user's input:

master_key = SHA-256(user_string.encode('utf-8'))
K[i] = SHA-256(master_key + i.to_bytes(2, 'big'))[:16] for i in 0..16

- SHA-256 normalizes any key length to 32 bytes
- Appending the round index ensures every subkey is unique
- SHA-256 is one-way — knowing one subkey reveals nothing about others
- K0 is used for initial whitening; K1–K16 are used in the 16 cipher rounds

---

## PKCS#7 Padding

**Padding:**

n = 16 - (len(message) % 16)
append n bytes each with value n

If the message is already a multiple of 16 bytes, a full 16-byte block (n=16) is appended.

**Unpadding:**

n = last byte value
verify last n bytes all equal n
strip last n bytes

---

## Claude-Keyed Session Generation

### Step 1 — Claude generates a session seed

Prompt: "Generate a random hexadecimal string of exactly 64 characters
for cryptographic use. Return ONLY the hex string, nothing else."

Response: "a3f7c2d891e4b560f1a2b3c4d5e6f708..."

One API call, under one second, always succeeds.

### Step 2 — Seed conversion

```python
hex_chars = ''.join(c for c in raw if c in '0123456789abcdef')
seed = int(hex_chars[:16], 16)

Step 3 — Fisher-Yates shuffle

r = random.Random(seed ^ hash(salt))   # salt = "sbox" or "pbox"
r.shuffle(perm)

Guarantees a true permutation with uniform distribution. The salt ensures S-box and P-box always differ.
Step 4 — Fixed point elimination (S-box only)

for i in range(256):
    if perm[i] == i:
        j = (i + 1) % 256
        perm[i], perm[j] = perm[j], perm[i]

Step 5 — Save

Tables are written to session_keys.json. Decrypt reads from this file — zero additional API calls.
Why Not Enumerate Directly

Asking Claude to produce all 256 values failed 30–40% of the time — LLMs have no internal counter and produce duplicates or truncated lists. The seed approach cuts response time from 10–15 seconds to under 1 second and eliminates all validation failures.
Why SPN Architecture
Layer Cryptographic Property What It Breaks
SubBytes Confusion Linear key-ciphertext relationship
PermuteBits Diffusion Localized bit-flip effects
AddRoundKey Key binding Distinguishable output

After 16 rounds, each output bit depends on every input bit and every key bit — this is the avalanche effect.
Security Scope

Project Obsidian is an educational prototype.

Known limitations:

    ECB mode — identical plaintext blocks produce identical ciphertext blocks
    No authentication — no MAC or AEAD tag; modified ciphertext decrypts to garbage silently
    PRNG for tables — random.Random is not a cryptographically secure PRNG
    LLM entropy — Claude's output is not uniformly random in the cryptographic sense

For real data protection use AES-256-GCM or ChaCha20-Poly1305.

1 step

---
# Project Obsidian - Algorithm Documentation

## Cipher Properties

| Property | Value |
| Block size | 128 bits (16 bytes) |
| Key size | Variable, normalized via SHA-256 |
| Rounds | 16 |
| S-box | 256-entry byte substitution table |
| P-box | 128-entry bit permutation table |
| Padding | PKCS#7 |
| Mode | ECB |

---

## Encryption Flow

    Plaintext -> PKCS#7 Pad -> AddRoundKey(K0) -> 16x [ SubBytes -> PermuteBits -> AddRoundKey(Ki) ] -> Ciphertext

## Decryption Flow

    Ciphertext -> 16x [ AddRoundKey(Ki) -> InvPermuteBits -> InvSubBytes ] -> AddRoundKey(K0) -> PKCS#7 Unpad -> Plaintext

---

## Cipher Primitives

### AddRoundKey
XOR every byte of the 128-bit state with the corresponding round key byte. XOR is its own inverse so the same operation runs in both directions.

### SubBytes
Replace every byte in the state with its S-box lookup value. Provides confusion - breaks the linear relationship between plaintext and ciphertext. Inverse uses the inverted S-box.

### PermuteBits
Treat the 128-bit state as 128 individual bits and rearrange them according to the P-box. Provides diffusion - a single flipped input bit spreads across multiple output bytes. Inverse uses the inverted P-box.

---

## Key Schedule

    master = SHA-256(user_key)
    K[i]   = SHA-256(master + i.to_bytes(2, 'big'))[:16]    for i in 0..16

Produces 17 independent 16-byte subkeys. K0 is used for initial whitening. K1 through K16 are used in the 16 cipher rounds.

---

## PKCS#7 Padding

    n = 16 - (len(message) % 16)
    append n bytes each with value n

If message length is already a multiple of 16, append a full 16-byte block where every byte equals 16. Unpad by reading the last byte as n, verifying, and stripping.

---

## Claude-Keyed Session Generation

Claude is prompted to return a random 64-character hex string. That string is converted to an integer seed which drives Fisher-Yates to build the S-box and P-box locally.

    seed = int(hex_string[:16], 16)
    r = random.Random(seed ^ hash(salt))
    r.shuffle(perm)

Salt is "sbox" or "pbox" so the two tables always differ. Fixed points (S[i] == i) are eliminated by swapping with the neighbor. Both tables are validated then saved to session_keys.json.

Why not ask Claude to enumerate all 256 values directly: LLMs have no internal counter and produced duplicates or truncated lists 30-40% of the time at 10-15 second response times. The seed approach is under 1 second and never fails.

---

## SPN Architecture

| Layer | Property | Effect |
| SubBytes | Confusion | Breaks key-ciphertext linearity |
| PermuteBits | Diffusion | Spreads single-bit changes across bytes |
| AddRoundKey | Key binding | Makes output indistinguishable |

After 16 rounds every output bit depends on every input bit and every key bit. This is the avalanche effect.

---

## Known Limitations

- ECB mode - identical plaintext blocks produce identical ciphertext blocks
- No authentication tag - corrupted ciphertext decrypts silently to garbage
- random.Random is not a cryptographically secure PRNG
- For production use: AES-256-GCM or ChaCha20-Poly1305
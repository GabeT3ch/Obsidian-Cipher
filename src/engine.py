import hashlib
from .utils import bytes_to_bits, bits_to_bytes

BLOCK_SIZE = 16
NUM_ROUNDS = 16


def KeySchedule(key_bytes: bytes, num_rounds: int = NUM_ROUNDS) -> list:
    #Derive (num_rounds + 1) independent 16-byte subkeys via SHA-256.
    master = hashlib.sha256(key_bytes).digest()
    return [
        hashlib.sha256(master + i.to_bytes(2, "big")).digest()[:16]
        for i in range(num_rounds + 1)
    ]


def AddRoundKey(block: bytes, round_key: bytes) -> bytes:
    return bytes(b ^ k for b, k in zip(block, round_key))


def SubBytes(block: bytes, sbox: list) -> bytes:
    return bytes(sbox[b] for b in block)


def PermuteBits(block: bytes, pbox: list) -> bytes:
    bits_in = bytes_to_bits(block)
    bits_out = [bits_in[pbox[i]] for i in range(128)]
    return bits_to_bytes(bits_out)


def invert_sbox(sbox: list) -> list:
    inv = [0] * 256
    for i, v in enumerate(sbox):
        inv[v] = i
    return inv


def invert_pbox(pbox: list) -> list:
    inv = [0] * 128
    for i, v in enumerate(pbox):
        inv[v] = i
    return inv


def encrypt(plaintext_bytes: bytes, key_bytes: bytes, sbox: list, pbox: list) -> bytes:
    assert len(plaintext_bytes) == BLOCK_SIZE, "Block must be 16 bytes"
    subkeys = KeySchedule(key_bytes)
    state = AddRoundKey(plaintext_bytes, subkeys[0])
    for r in range(1, NUM_ROUNDS + 1):
        state = SubBytes(state, sbox)
        state = PermuteBits(state, pbox)
        state = AddRoundKey(state, subkeys[r])
    return state


def decrypt(ciphertext_bytes: bytes, key_bytes: bytes, inv_sbox: list, inv_pbox: list) -> bytes:
    assert len(ciphertext_bytes) == BLOCK_SIZE, "Block must be 16 bytes"
    subkeys = KeySchedule(key_bytes)
    state = ciphertext_bytes
    for r in range(NUM_ROUNDS, 0, -1):
        state = AddRoundKey(state, subkeys[r])
        state = PermuteBits(state, inv_pbox)
        state = SubBytes(state, inv_sbox)
    state = AddRoundKey(state, subkeys[0])
    return state

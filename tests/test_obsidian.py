import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import pkcs7_pad, pkcs7_unpad, bytes_to_bits, bits_to_bytes
from src.engine import (
    encrypt, decrypt, invert_sbox, invert_pbox, KeySchedule,
    BLOCK_SIZE, NUM_ROUNDS,
)

TEST_SBOX = [(i + 1) % 256 for i in range(256)]
TEST_PBOX = [(i + 1) % 128 for i in range(128)]
TEST_KEY  = b"test_key_obsidian"
TEST_PLAINTEXT = b"Hello, Obsidian!"


class TestPadding:
    def test_partial_block(self):
        padded = pkcs7_pad(b"Hello")
        assert len(padded) == 16
        assert padded[5:] == bytes([11] * 11)

    def test_exact_block_adds_full_padding_block(self):
        padded = pkcs7_pad(b"A" * 16)
        assert len(padded) == 32
        assert padded[16:] == bytes([16] * 16)

    def test_roundtrip_various_lengths(self):
        for msg in [b"a", b"A" * 15, b"B" * 16, b"C" * 17, b"D" * 32]:
            assert pkcs7_unpad(pkcs7_pad(msg)) == msg

    def test_invalid_padding_raises(self):
        with pytest.raises(ValueError):
            pkcs7_unpad(b"\x00" * 16)

    def test_mismatched_padding_raises(self):
        with pytest.raises(ValueError):
            pkcs7_unpad(b"\x00" * 15 + b"\x03")


class TestBitHelpers:
    def test_roundtrip_single_byte(self):
        for val in range(256):
            b = bytes([val])
            assert bits_to_bytes(bytes_to_bits(b)) == b

    def test_roundtrip_block(self):
        block = bytes(range(16))
        assert bits_to_bytes(bytes_to_bits(block)) == block

    def test_known_msb(self):
        assert bytes_to_bits(b"\x80") == [1, 0, 0, 0, 0, 0, 0, 0]

    def test_known_lsb(self):
        assert bytes_to_bits(b"\x01") == [0, 0, 0, 0, 0, 0, 0, 1]

    def test_non_multiple_of_8_raises(self):
        with pytest.raises(ValueError):
            bits_to_bytes([1, 0, 1])


class TestSBoxInvertibility:
    def test_full_roundtrip(self):
        inv = invert_sbox(TEST_SBOX)
        for i in range(256):
            assert inv[TEST_SBOX[i]] == i

    def test_is_permutation(self):
        assert sorted(TEST_SBOX) == list(range(256))

    def test_inverse_is_permutation(self):
        assert sorted(invert_sbox(TEST_SBOX)) == list(range(256))


class TestPBoxInvertibility:
    def test_full_roundtrip(self):
        inv = invert_pbox(TEST_PBOX)
        for i in range(128):
            assert inv[TEST_PBOX[i]] == i

    def test_is_permutation(self):
        assert sorted(TEST_PBOX) == list(range(128))


class TestKeySchedule:
    def test_produces_correct_count(self):
        assert len(KeySchedule(TEST_KEY)) == NUM_ROUNDS + 1

    def test_all_keys_are_16_bytes(self):
        assert all(len(k) == BLOCK_SIZE for k in KeySchedule(TEST_KEY))

    def test_all_keys_distinct(self):
        assert len(set(KeySchedule(TEST_KEY))) == NUM_ROUNDS + 1

    def test_different_input_keys_differ(self):
        assert KeySchedule(b"key_a") != KeySchedule(b"key_b")


class TestEncryptDecrypt:
    def test_single_block_roundtrip(self):
        inv_s = invert_sbox(TEST_SBOX)
        inv_p = invert_pbox(TEST_PBOX)
        ct = encrypt(TEST_PLAINTEXT, TEST_KEY, TEST_SBOX, TEST_PBOX)
        assert decrypt(ct, TEST_KEY, inv_s, inv_p) == TEST_PLAINTEXT

    def test_varied_plaintexts(self):
        inv_s = invert_sbox(TEST_SBOX)
        inv_p = invert_pbox(TEST_PBOX)
        for pt in [b"\x00"*16, b"\xff"*16, b"\xaa\x55"*8, b"0123456789abcdef"]:
            assert decrypt(encrypt(pt, TEST_KEY, TEST_SBOX, TEST_PBOX), TEST_KEY, inv_s, inv_p) == pt

    def test_different_keys_produce_different_ciphertext(self):
        assert encrypt(TEST_PLAINTEXT, b"key_one", TEST_SBOX, TEST_PBOX) != \
               encrypt(TEST_PLAINTEXT, b"key_two", TEST_SBOX, TEST_PBOX)

    def test_ciphertext_differs_from_plaintext(self):
        assert encrypt(TEST_PLAINTEXT, TEST_KEY, TEST_SBOX, TEST_PBOX) != TEST_PLAINTEXT

    def test_block_size_assertion(self):
        with pytest.raises(AssertionError):
            encrypt(b"short", TEST_KEY, TEST_SBOX, TEST_PBOX)

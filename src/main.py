
#Obsidian Cipher — Local Web GUI starts a Flask server at http://localhost:5000 and opens it automatically.

import json
import os
import threading
import webbrowser

from dotenv import load_dotenv
from flask import Flask, jsonify, request , send_file

from .api_handler import get_sbox_and_pbox
from .engine import BLOCK_SIZE, decrypt as spn_decrypt
from .engine import encrypt as spn_encrypt
from .engine import invert_pbox, invert_sbox
from .utils import pkcs7_pad, pkcs7_unpad

load_dotenv()

_HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_HERE, "templates"))

SESSION_FILE = os.path.join(_HERE, "..", "session_keys.json")


def _save_session(sbox: list, pbox: list) -> None:
    with open(SESSION_FILE, "w") as f:
        json.dump({"sbox": sbox, "pbox": pbox}, f)


def _load_session():
    if not os.path.exists(SESSION_FILE):
        return None, None
    with open(SESSION_FILE) as f:
        data = json.load(f)
    return data["sbox"], data["pbox"]


@app.route("/")
def index():
    return send_file(os.path.join(_HERE, "templates", "index.html"))


@app.route("/api/session-status")
def session_status():
    return jsonify({"has_session": os.path.exists(SESSION_FILE)})


@app.route("/api/encrypt", methods=["POST"])
def encrypt_route():
    body = request.get_json(force=True)
    message = (body.get("message") or "").strip()
    key = (body.get("key") or "").strip()

    if not message:
        return jsonify({"error": "Message is required."}), 400
    if not key:
        return jsonify({"error": "Key is required."}), 400

    try:
        sbox, pbox = get_sbox_and_pbox()
        _save_session(sbox, pbox)

        key_bytes = key.encode("utf-8")
        padded = pkcs7_pad(message.encode("utf-8"))

        ciphertext = b""
        for i in range(0, len(padded), BLOCK_SIZE):
            ciphertext += spn_encrypt(padded[i : i + BLOCK_SIZE], key_bytes, sbox, pbox)

        return jsonify({"ciphertext": ciphertext.hex(), "success": True})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/decrypt", methods=["POST"])
def decrypt_route():
    body = request.get_json(force=True)
    ciphertext_hex = (body.get("ciphertext") or "").strip()
    key = (body.get("key") or "").strip()

    if not ciphertext_hex:
        return jsonify({"error": "Ciphertext is required."}), 400
    if not key:
        return jsonify({"error": "Key is required."}), 400

    sbox, pbox = _load_session()
    if sbox is None:
        return jsonify({"error": "No session keys found. Run an Encrypt first to generate them."}), 400

    try:
        ct = bytes.fromhex(ciphertext_hex)
    except ValueError:
        return jsonify({"error": "Ciphertext must be a valid hex string."}), 400

    if len(ct) % BLOCK_SIZE != 0:
        return jsonify({"error": f"Ciphertext length must be a multiple of {BLOCK_SIZE} bytes."}), 400

    try:
        inv_s = invert_sbox(sbox)
        inv_p = invert_pbox(pbox)
        key_bytes = key.encode("utf-8")

        padded = b""
        for i in range(0, len(ct), BLOCK_SIZE):
            padded += spn_decrypt(ct[i : i + BLOCK_SIZE], key_bytes, inv_s, inv_p)

        plaintext = pkcs7_unpad(padded)
        return jsonify({"plaintext": plaintext.decode("utf-8"), "success": True})

    except ValueError as exc:
        return jsonify({"error": f"Decryption failed — wrong key or corrupted data. ({exc})"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def main():
    port = 5000
    url = f"http://localhost:{port}"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"Obsidian Cipher running at {url}  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()

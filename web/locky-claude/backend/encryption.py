from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from hashlib import sha256
from os import urandom, getenv
import base64


def _get_key() -> bytes:
    secret = getenv("SECRET_KEY", "").encode()
    return sha256(secret).digest()


def _encrypt_data(plaintext: str) -> str:
    key = _get_key()
    iv = urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def _decrypt_data(encrypted_data: str) -> str:
    key = _get_key()
    raw = base64.b64decode(encrypted_data)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode()

from cryptography.hazmat import backends
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from hashlib import sha256 
from os import urandom, getenv 
import base64
import generate_token  

def __encrypt_data(key=sha256(b'{getenv("SECRET_KEY")}').hexdigest(), plaintext=None) -> str:
    key = sha256(b'{key}').digest()
    iv = urandom(16)

    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

    return base64.b64encode(iv + ciphertext).decode('utf-8')

def __decrypt_data(key=sha256(b'{getenv("SECRET_KEY")}').hexdigest(), encrypted_data=None) -> str:
    key = sha256(b'{key}').digest()
    encrypted_data_bytes = base64.b64decode(encrypted_data)

    iv = encrypted_data_bytes[:16]
    ciphertext = encrypted_data_bytes[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

    return decrypted_data.decode()


def __insert_key(rand_key:None, locker_nr=None):
    encrypted_key = __encrypt_data(plaintext=rand_key)
    insert_query(f"INSERT INTO lockers WHERE locker_nr = {locker_nr} VALUES {encrypted_key};")
    return 


def generate_locker_key(email:str, locker_nr:str) -> str:

    rand_key = urandom(32)
    encrypted_key = __encrypt_data(plaintext = rand_key)
    __insert_key(encrypted_key,email, locker_nr)
    token = generate_jwt_token(key = encrypted_key, email = email)
    return token 


def get_key(email)
    key = select_query(f"SELECT key FROM keys WHERE user = {email}")
    
    token = generate_jwt_token(email, key)
    return token



def unpack_key(token):
    key = unpack_jwt_token(token)
    return key

key = sha256(b"superdupersecretkey").hexdigest()
test = __encrypt_data(key=key, plaintext="testing encryption")
print("Encrypted:", test)
print("Decrypted:", decrypt_data(key=key, encrypted_data=str(test)))

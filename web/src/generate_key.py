from cryptography.hazmat import backends
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom, getenv 
from dotenv import load_dotenv
import base64 



def encrypt_data(key=os.getenv("SECRET_KEY"), plaintext=None) -> str:
    iv = urandom(16)

    cipher = Cipher(algorithms.ASE(key), modes.CFB(iv), backends=default_backend())
    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

    return base64.b64encode(iv + ciphertext).decode('utf-8')

def decrypt_data(key=os.getenv("SECRET_KEY"), encrypted_data=None) -> str:
   encrypted_data_bytes = base64.b64decode(encrypted_data)

   iv = encrypted_data_bytes[:16]
   ciphertext = encrypted_data_bytes[16:]

   cipher = Cipher(algorithms.ASE(key), modes.CFB(iv), backend=default_backend())
   decryptor = cipher.decryptor()

   decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

   return decrypted_data


test = encrypt_data(key="test", plaintext="testing encryption")
print("Encrypted:", test)
print("Decrypted:", decrypt_data(key="test", encrypt_data=test))

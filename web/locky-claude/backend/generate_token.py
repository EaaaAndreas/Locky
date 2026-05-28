import jwt
import encryption
import datetime
from os import getenv


def generate_jwt_token(email=None, locker_nr=None):
    token = jwt.encode({
        "email": email,
        "locker_nr": locker_nr,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8),
    }, getenv("JWT_SECRET_KEY"), algorithm="HS256")
    return encryption._encrypt_data(plaintext=token)


def verify_jwt_token(token=None):
    if not token:
        return None
    try:
        decrypted = encryption._decrypt_data(encrypted_data=token)
        payload = jwt.decode(decrypted, getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return payload
    except Exception:
        return None

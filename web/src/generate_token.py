import jwt
import encryption 
import datetime
from os import getenv


def generate_jwt_token(email=None, key=None):
    token = jwt.encode({
        "key": key,
        "email": email,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1)
    }, getenv("JWT_SECRET_KEY"), algorithm="HS256")
    token = encryption._encrypt_data(plaintext=token)
    return token 

def verify_jwt_token(token=None):
    try:
        token = encryption._decrypt_data(encrypted_data=token)
        payload = jwt.decode(token, getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return True   
    except jwt.ExpiredSignatureError:
        return False
        #return jsonify({"message": "f off - token udløbet, opdater siden"}), 401
    except jwt.InvalidTokenError:
        return False 
        #return jsonify({"message": "f off - ugyldig token"}), 401


    
    
    

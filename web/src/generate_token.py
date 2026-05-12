import jwt
import generate_key
import datetime
from os import getenv


def generate_jwt_token(email=None, key=None):
    token = jwt.encode({
        "key": key,
        "email": email,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1)
    }, getenv("JWT_SECRET_KEY"), algorithm="HS256")

    return token 

def unpack_jwt_token(token=None):
	try:
        payload = jwt.decode(token, getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return payload["key"]
          

 

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "f off - token udløbet, opdater siden"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "f off - ugyldig token"}), 401


    
    
    

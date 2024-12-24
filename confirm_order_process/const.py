from datetime import datetime, timedelta
import hmac
import hashlib
import base64
import random
import string
import logging

_logger = logging.getLogger(__name__)

def get_date():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    return formatted_datetime

def get_timestamp():
    current_datetime = datetime.now()
    timestamp = current_datetime.timestamp()
    return timestamp

def hmac_encode(data, key):
    key = key.encode('utf-8') if isinstance(key, str) else key
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hmac.new(key, data, hashlib.sha256).digest()

def encode_token(data, secret_key):
    payload = data.encode('utf-8')
    hmac_data = hmac_encode(payload, secret_key)
    token = payload + hmac_data
    return base64.b64encode(token).decode('utf-8')

def decode_token(encoded_data, secret_key):
    try:
        decoded_data = base64.b64decode(encoded_data)
        if len(decoded_data) < 32:
            return False
        payload = decoded_data[:-32]
        expected_hmac = decoded_data[-32:]
        computed_hmac = hmac_encode(payload, secret_key)
        if hmac.compare_digest(computed_hmac, expected_hmac):
            return payload.decode('utf-8', errors='ignore')
        else:
            return False
    except Exception as e:
        return str(e)

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def generate_otp(length=6):
    characters = string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

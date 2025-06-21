import os
import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta

JWT_SECRET = os.environ.get("JWT_SECRET", "your_jwt_secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXP_DELTA_SECONDS = int(os.environ.get("JWT_EXP_DELTA_SECONDS", 3600))


def check_api_key(event):
    if os.environ.get("MOCK_AWS", "false").lower() == "true":
        return True
    headers = event.get("headers", {})
    return headers.get("x-api-key") == "your-secure-api-key"


# JWT encode function
def encode_jwt(payload):
    payload = payload.copy()
    payload["exp"] = datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# JWT decode/verify function
def decode_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except PyJWTError:
        return None


# JWT auth check for Lambda events
def check_jwt_auth(event):
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    payload = decode_jwt(token)
    return payload is not None


def get_user_roles(event):
    """Decodes the JWT from the event and returns the user's roles."""
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return []

    token = auth_header.split(" ", 1)[1]
    # In a real scenario, you'd use a library that can decode without verification
    # just to read claims, or verify it fully. We assume decode_jwt does this.
    payload = decode_jwt(token)

    if payload and "cognito:groups" in payload:
        return payload["cognito:groups"]
    return []


def is_admin(event):
    """A convenience function to check if the user has the 'admins' role."""
    roles = get_user_roles(event)
    return "admins" in roles

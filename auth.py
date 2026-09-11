"""
JWT-based authentication -- tokens issued on login, verified on protected
endpoints via the Authorization header (Bearer scheme).
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24 * 7  # 7 days


def create_token(farmer_id: int, username: str) -> str:
    payload = {
        "farmer_id": farmer_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired -- please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_farmer(authorization: str = Header(None)) -> dict:
    """FastAPI dependency -- extracts and verifies the farmer from the
    Authorization: Bearer <token> header. Use as: farmer = Depends(get_current_farmer)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    return payload

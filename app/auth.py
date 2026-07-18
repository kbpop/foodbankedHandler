import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = 24
COOKIE_NAME = "foodbanked_token"

DONOR = "donor"
EMPLOYEE = "employee"
PARTNER = "partner"
ADMIN = "admin"


# Prototype-only: passwords are stored and compared as plain text.
# Swap these two functions for real hashing (e.g. bcrypt) before this goes anywhere real.
def hash_password(password):
    return password


def verify_password(password, password_hash):
    return password == password_hash


def create_token(user):
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "account_type": user["account_type"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def set_auth_cookie(response, token):
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="Lax",
        max_age=JWT_EXP_HOURS * 3600,
    )


def clear_auth_cookie(response):
    response.delete_cookie(COOKIE_NAME)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get(COOKIE_NAME)
        payload = decode_token(token) if token else None
        if payload is None:
            return jsonify({"error": "authentication required"}), 401
        g.current_user = payload
        return f(*args, **kwargs)

    return wrapper


def role_required(*allowed_account_types):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if g.current_user["account_type"] not in allowed_account_types:
                return jsonify({"error": "forbidden"}), 403
            return f(*args, **kwargs)

        return login_required(wrapper)

    return decorator


# Any logged-in account (donor/employee/partner/admin) can read.
# Only employee/admin accounts can write, per the current permission model.
write_required = role_required(EMPLOYEE, ADMIN)

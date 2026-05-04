from functools import wraps

import jwt
from flask import g, jsonify, request

from services.auth_service import decode_token


def _extract_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[7:].strip() or None


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        g.current_user = payload
        return view(*args, **kwargs)

    return wrapper


def require_role(*allowed_roles):
    def decorator(view):
        @wraps(view)
        @require_auth
        def wrapper(*args, **kwargs):
            chuc_vu = g.current_user.get("chuc_vu")
            if chuc_vu not in allowed_roles:
                return jsonify({"error": "Forbidden", "required_roles": list(allowed_roles)}), 403
            return view(*args, **kwargs)

        return wrapper

    return decorator

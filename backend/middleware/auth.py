from functools import wraps

import jwt
from flask import g, jsonify, request

from services.auth_service import decode_token


def _extract_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[7:].strip() or None


def _normalize_branch_code(branch_code):
    return (branch_code or "").strip().upper()


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
                return (
                    jsonify(
                        {"error": "Forbidden", "required_roles": list(allowed_roles)}
                    ),
                    403,
                )
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_branch_access(view):
    @wraps(view)
    @require_auth
    def wrapper(*args, **kwargs):
        requested_branch_code = _normalize_branch_code(kwargs.get("ma_chi_nhanh"))
        current_scope = g.current_user.get("scope", "central")
        current_branch_code = _normalize_branch_code(g.current_user.get("branch_code"))

        if current_scope == "branch" and current_branch_code != requested_branch_code:
            return jsonify({"error": "Forbidden for this branch"}), 403

        return view(*args, **kwargs)

    return wrapper

from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from services.auth_service import decode_token


def _extract_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[7:].strip() or None


def _normalize_branch_code(branch_code):
    return (branch_code or "").strip().upper()


def _token_matches_app_role(payload):
    app_role = (current_app.config.get("APP_ROLE") or "all").lower()
    token_scope = payload.get("scope", "central")

    if app_role == "central":
        return token_scope in ("central", "branch")

    if app_role == "branch":
        configured_branch_code = _normalize_branch_code(
            current_app.config.get("BRANCH_CODE")
        )
        token_branch_code = _normalize_branch_code(payload.get("branch_code"))
        return token_scope == "branch" and token_branch_code == configured_branch_code

    return True


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

        if not _token_matches_app_role(payload):
            return jsonify({"error": "Token is not valid for this API instance"}), 403

        g.current_user = payload
        return view(*args, **kwargs)

    return wrapper


def require_role(*allowed_roles):
    def decorator(view):
        @wraps(view)
        @require_auth
        def wrapper(*args, **kwargs):
            app_role = (current_app.config.get("APP_ROLE") or "all").lower()
            if app_role == "central" and g.current_user.get("scope") != "central":
                return jsonify({"error": "Central access required"}), 403

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


def require_central_scope(view):
    @wraps(view)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.current_user.get("scope") != "central":
            return jsonify({"error": "Central access required"}), 403
        return view(*args, **kwargs)

    return wrapper


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

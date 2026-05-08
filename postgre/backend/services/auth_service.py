from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from db import (
    get_branch_db_engine,
    password_hash_sql,
    query_branch_db,
    query_db,
)


def verify_credentials(ma_nhan_vien, mat_khau):
    if not ma_nhan_vien or not mat_khau:
        raise ValueError("ma_nhan_vien va mat_khau la bat buoc")

    row = query_db(
        """
        SELECT ma_nhan_vien, ho_ten, chuc_vu, ma_phong_ban, trang_thai
        FROM NHAN_VIEN
        WHERE ma_nhan_vien = ?
          AND mat_khau = {password_hash}
        """.format(password_hash=password_hash_sql()),
        (ma_nhan_vien, mat_khau),
        fetchone=True,
    )

    if not row:
        return None
    if row["trang_thai"] != 1:
        raise ValueError("Tai khoan da bi vo hieu hoa")
    return row


def verify_branch_credentials(branch_code, ma_nhan_vien, mat_khau):
    if not ma_nhan_vien or not mat_khau:
        raise ValueError("ma_nhan_vien va mat_khau la bat buoc")

    engine = get_branch_db_engine(branch_code)
    row = query_branch_db(
        branch_code,
        """
        SELECT ma_nhan_vien, ho_ten, chuc_vu, ma_phong_ban, trang_thai
        FROM NHAN_VIEN
        WHERE ma_nhan_vien = ?
          AND mat_khau = {password_hash}
        """.format(password_hash=password_hash_sql(engine)),
        (ma_nhan_vien, mat_khau),
        fetchone=True,
    )

    if not row:
        return None
    if row["trang_thai"] != 1:
        raise ValueError("Tai khoan da bi vo hieu hoa")
    return row


def create_token(user, scope="central", branch_code=None, source_engine=None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["ma_nhan_vien"],
        "ho_ten": user["ho_ten"],
        "chuc_vu": user["chuc_vu"],
        "ma_phong_ban": user["ma_phong_ban"],
        "scope": scope,
        "branch_code": branch_code,
        "source_engine": source_engine,
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"]),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )


def login(ma_nhan_vien, mat_khau):
    user = verify_credentials(ma_nhan_vien, mat_khau)
    if not user:
        return None

    token = create_token(
        user,
        scope="central",
        branch_code=None,
        source_engine=current_app.config["DB_ENGINE"],
    )
    return {
        "token": token,
        "expires_in_hours": current_app.config["JWT_EXPIRES_HOURS"],
        "user": {
            "ma_nhan_vien": user["ma_nhan_vien"],
            "ho_ten": user["ho_ten"],
            "chuc_vu": user["chuc_vu"],
            "ma_phong_ban": user["ma_phong_ban"],
            "scope": "central",
            "branch_code": None,
            "source_engine": current_app.config["DB_ENGINE"],
        },
    }


def login_branch(branch_code, ma_nhan_vien, mat_khau):
    user = verify_branch_credentials(branch_code, ma_nhan_vien, mat_khau)
    if not user:
        return None

    normalized_branch_code = branch_code.upper()
    engine = get_branch_db_engine(branch_code)
    token = create_token(
        user,
        scope="branch",
        branch_code=normalized_branch_code,
        source_engine=engine,
    )
    return {
        "token": token,
        "expires_in_hours": current_app.config["JWT_EXPIRES_HOURS"],
        "user": {
            "ma_nhan_vien": user["ma_nhan_vien"],
            "ho_ten": user["ho_ten"],
            "chuc_vu": user["chuc_vu"],
            "ma_phong_ban": user["ma_phong_ban"],
            "scope": "branch",
            "branch_code": normalized_branch_code,
            "source_engine": engine,
        },
    }

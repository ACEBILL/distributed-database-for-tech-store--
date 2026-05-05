from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from db import password_hash_sql, query_db


def verify_credentials(ma_nhan_vien, mat_khau):
    if not ma_nhan_vien or not mat_khau:
        raise ValueError("ma_nhan_vien và mat_khau là bắt buộc")

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
        raise ValueError("Tài khoản đã bị vô hiệu hóa")
    return row


def create_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["ma_nhan_vien"],
        "ho_ten": user["ho_ten"],
        "chuc_vu": user["chuc_vu"],
        "ma_phong_ban": user["ma_phong_ban"],
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
    token = create_token(user)
    return {
        "token": token,
        "expires_in_hours": current_app.config["JWT_EXPIRES_HOURS"],
        "user": {
            "ma_nhan_vien": user["ma_nhan_vien"],
            "ho_ten": user["ho_ten"],
            "chuc_vu": user["chuc_vu"],
            "ma_phong_ban": user["ma_phong_ban"],
        },
    }

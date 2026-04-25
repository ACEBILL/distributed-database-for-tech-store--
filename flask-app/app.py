import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import query_db, execute_db, get_redis

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"


# ─── TRANG CHỦ ───
@app.route("/")
def index():
    total_sp = query_db("SELECT COUNT(*) AS total FROM SAN_PHAM WHERE trang_thai = 1", fetchone=True)["total"]
    total_nv = query_db("SELECT COUNT(*) AS total FROM NHAN_VIEN WHERE trang_thai = 1", fetchone=True)["total"]
    total_cn = query_db("SELECT COUNT(*) AS total FROM chi_nhanh", fetchone=True)["total"]
    total_ncc = query_db("SELECT COUNT(*) AS total FROM NCC", fetchone=True)["total"]

    return render_template("index.html",
        total_sp=total_sp, total_nv=total_nv,
        total_cn=total_cn, total_ncc=total_ncc)


# ─── SẢN PHẨM ───
@app.route("/san-pham")
def san_pham_list():
    products = query_db("""
        SELECT sp.*, lsp.ten_loai_sp, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        ORDER BY sp.tao_vao DESC
    """)
    return render_template("san_pham.html", products=products)


@app.route("/san-pham/them", methods=["GET", "POST"])
def san_pham_them():
    if request.method == "POST":
        execute_db("""
            INSERT INTO SAN_PHAM (ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia, mo_ta, ma_loai_sp, ma_ncc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["ma_sp"],
            request.form["ten_sp"],
            request.form["gia"],
            request.form.get("ti_le_loi_nhuan", 0),
            request.form.get("ti_le_giam_gia", 0),
            request.form.get("mo_ta", ""),
            request.form["ma_loai_sp"],
            request.form["ma_ncc"],
        ))

        r = get_redis()
        r.delete("cache:san_pham_list")

        flash("Thêm sản phẩm thành công!", "success")
        return redirect(url_for("san_pham_list"))

    loai_sp = query_db("SELECT * FROM loai_sp")
    ncc_list = query_db("SELECT * FROM NCC")
    return render_template("san_pham_them.html", loai_sp=loai_sp, ncc_list=ncc_list)


# ─── NHÂN VIÊN ───
@app.route("/nhan-vien")
def nhan_vien_list():
    employees = query_db("""
        SELECT nv.*, pb.ten_pb
        FROM NHAN_VIEN nv
        JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb
        ORDER BY pb.ma_pb, nv.chuc_vu DESC
    """)
    return render_template("nhan_vien.html", employees=employees)


# ─── CHI NHÁNH ───
@app.route("/chi-nhanh")
def chi_nhanh_list():
    branches = query_db("SELECT * FROM v_thong_ke_chi_nhanh")
    return render_template("chi_nhanh.html", branches=branches)


# ─── API ───
@app.route("/api/san-pham")
def api_san_pham():
    r = get_redis()
    cached = r.get("cache:san_pham_list")
    if cached:
        return jsonify({"source": "cache", "data": json.loads(cached)})

    products = query_db("""
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_giam_gia,
               lsp.ten_loai_sp, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        WHERE sp.trang_thai = 1
    """)

    for p in products:
        p["gia"] = float(p["gia"]) if p["gia"] else 0
        p["ti_le_giam_gia"] = float(p["ti_le_giam_gia"]) if p["ti_le_giam_gia"] else 0

    r.setex("cache:san_pham_list", 300, json.dumps(products, ensure_ascii=False))
    return jsonify({"source": "database", "data": products})


@app.route("/api/thong-ke")
def api_thong_ke():
    stats = query_db("SELECT * FROM v_thong_ke_chi_nhanh")
    for s in stats:
        s["gia_trung_binh"] = float(s["gia_trung_binh"]) if s["gia_trung_binh"] else 0
    return jsonify(stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

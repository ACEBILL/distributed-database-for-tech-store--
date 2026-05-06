-- PostgreSQL init for branch CN02 (Chi nhanh TP.HCM)
-- Schema mirrors init/mysql/01-schema-and-data.sql so backend code can run unchanged.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS chi_nhanh (
    ma_chi_nhanh VARCHAR(20) PRIMARY KEY,
    ten_chi_nhanh VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS loai_sp (
    ma_loai_sp VARCHAR(20) PRIMARY KEY,
    ten_loai_sp VARCHAR(100) NOT NULL,
    ma_chi_nhanh VARCHAR(20) NOT NULL REFERENCES chi_nhanh(ma_chi_nhanh)
);

CREATE TABLE IF NOT EXISTS NCC (
    ma_NCC SERIAL PRIMARY KEY,
    ten_NCC VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS SAN_PHAM (
    ma_sp VARCHAR(20) PRIMARY KEY,
    ten_sp VARCHAR(200) NOT NULL,
    gia NUMERIC(15, 2) NOT NULL,
    ti_le_loi_nhuan NUMERIC(5, 2) DEFAULT 0.00,
    ti_le_giam_gia NUMERIC(5, 2) DEFAULT 0.00,
    mo_ta TEXT,
    ma_loai_sp VARCHAR(20) NOT NULL REFERENCES loai_sp(ma_loai_sp),
    ma_ncc INT NOT NULL REFERENCES NCC(ma_NCC),
    trang_thai INT DEFAULT 1,
    tao_vao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cap_nhat_vao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phong_ban (
    ma_pb SERIAL PRIMARY KEY,
    ten_pb VARCHAR(100) NOT NULL,
    ma_nv INT NULL
);

CREATE TABLE IF NOT EXISTS NHAN_VIEN (
    ma_nhan_vien VARCHAR(20) PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    cccd VARCHAR(20),
    sdt VARCHAR(15),
    luong NUMERIC(15, 2) DEFAULT 0,
    mat_khau VARCHAR(255) NOT NULL,
    trang_thai INT DEFAULT 1,
    ma_phong_ban INT REFERENCES phong_ban(ma_pb),
    ma_ngay_lam INT DEFAULT 0,
    chuc_vu VARCHAR(20) DEFAULT 'nhan_vien',
    ngay_bat_dau TIMESTAMP,
    ngay_ket_thuc TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sp_loai ON SAN_PHAM(ma_loai_sp);
CREATE INDEX IF NOT EXISTS idx_sp_ncc ON SAN_PHAM(ma_ncc);
CREATE INDEX IF NOT EXISTS idx_sp_trangthai ON SAN_PHAM(trang_thai);
CREATE INDEX IF NOT EXISTS idx_nv_pb ON NHAN_VIEN(ma_phong_ban);
CREATE INDEX IF NOT EXISTS idx_nv_chucvu ON NHAN_VIEN(chuc_vu);

-- Trigger to mimic MySQL's "ON UPDATE CURRENT_TIMESTAMP" for cap_nhat_vao
CREATE OR REPLACE FUNCTION trg_san_pham_touch_cap_nhat()
RETURNS TRIGGER AS $$
BEGIN
    NEW.cap_nhat_vao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS san_pham_touch_cap_nhat ON SAN_PHAM;
CREATE TRIGGER san_pham_touch_cap_nhat
BEFORE UPDATE ON SAN_PHAM
FOR EACH ROW EXECUTE FUNCTION trg_san_pham_touch_cap_nhat();

-- Seed data (CN02-focused but keeping shared lookup data)
INSERT INTO chi_nhanh (ma_chi_nhanh, ten_chi_nhanh) VALUES
('CN01', 'Chi nhánh Hà Nội'),
('CN02', 'Chi nhánh TP.HCM')
ON CONFLICT (ma_chi_nhanh) DO NOTHING;

INSERT INTO loai_sp (ma_loai_sp, ten_loai_sp, ma_chi_nhanh) VALUES
('LSP01', 'Laptop', 'CN01'),
('LSP02', 'Điện thoại', 'CN01'),
('LSP03', 'Phụ kiện', 'CN02'),
('LSP04', 'Màn hình', 'CN02'),
('LSP05', 'Linh kiện PC', 'CN01'),
('LSP06', 'Thiết bị mạng', 'CN01'),
('LSP07', 'Máy tính bảng', 'CN02'),
('LSP08', 'Thiết bị âm thanh', 'CN02'),
('LSP09', 'Camera và Webcam', 'CN01'),
('LSP10', 'Thiết bị đeo', 'CN02')
ON CONFLICT (ma_loai_sp) DO NOTHING;

INSERT INTO NCC (ma_NCC, ten_NCC) VALUES
(1, 'Apple Việt Nam'),
(2, 'Samsung Việt Nam'),
(3, 'Dell Technologies'),
(4, 'Logitech Distribution'),
(5, 'LG Electronics'),
(6, 'Kingston Technology'),
(7, 'JBL / Harman'),
(8, 'TP-Link Việt Nam')
ON CONFLICT (ma_NCC) DO NOTHING;

-- Reset SERIAL so next inserts continue after seeded ids
SELECT setval(pg_get_serial_sequence('ncc', 'ma_ncc'), (SELECT COALESCE(MAX(ma_NCC), 0) FROM NCC));

INSERT INTO SAN_PHAM (
    ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia,
    mo_ta, ma_loai_sp, ma_ncc, trang_thai, tao_vao
) VALUES
('SP001', 'Laptop Dell XPS 15',         32000000, 15.00, 0.00,  'Laptop cao cấp, màn 15.6 inch OLED', 'LSP01', 3, 1, '2025-01-10'),
('SP002', 'MacBook Air M3',              28000000, 12.00, 5.00,  'MacBook Air chip M3, 16GB RAM',       'LSP01', 1, 1, '2025-01-10'),
('SP003', 'Laptop Dell Inspiron 14',    18000000, 18.00, 10.00, 'Laptop văn phòng, i5 thế hệ 13',     'LSP01', 3, 1, '2025-01-15'),
('SP004', 'iPhone 15 Pro Max',          29000000, 10.00, 0.00,  'iPhone 15 Pro Max 256GB',             'LSP02', 1, 1, '2025-01-12'),
('SP005', 'Samsung Galaxy S24 Ultra',   26000000, 12.00, 8.00,  'Samsung flagship, camera 200MP',     'LSP02', 2, 1, '2025-01-12'),
('SP006', 'AirPods Pro 2',                5500000, 20.00, 0.00,  'Tai nghe không dây chống ồn',         'LSP03', 1, 1, '2025-01-20'),
('SP007', 'Chuột Logitech MX Master 3S',  2200000, 25.00, 5.00,  'Chuột không dây cao cấp',             'LSP03', 4, 1, '2025-01-20'),
('SP008', 'Màn hình LG 27 inch 4K',       8000000, 15.00, 10.00, 'IPS 4K, 60Hz, HDR400',                'LSP04', 5, 1, '2025-01-25'),
('SP009', 'SSD Samsung 990 Pro 1TB',      3200000, 20.00, 5.00,  'NVMe Gen4, đọc 7450MB/s',             'LSP05', 2, 1, '2025-02-01'),
('SP010', 'Router TP-Link Archer AX73',   2800000, 22.00, 0.00,  'WiFi 6, AX5400, MU-MIMO',             'LSP06', 8, 1, '2025-02-15')
ON CONFLICT (ma_sp) DO NOTHING;

INSERT INTO phong_ban (ma_pb, ten_pb, ma_nv) VALUES
(1, 'Ban Giám đốc', NULL),
(2, 'Phòng Kinh doanh', NULL),
(3, 'Phòng Kỹ thuật', NULL),
(4, 'Phòng Kho vận', NULL),
(5, 'Phòng Nhân sự', NULL),
(6, 'Phòng Kế toán', NULL)
ON CONFLICT (ma_pb) DO NOTHING;

SELECT setval(pg_get_serial_sequence('phong_ban', 'ma_pb'), (SELECT COALESCE(MAX(ma_pb), 0) FROM phong_ban));

INSERT INTO NHAN_VIEN (
    ma_nhan_vien, ho_ten, cccd, sdt, luong, mat_khau, trang_thai,
    ma_phong_ban, ma_ngay_lam, chuc_vu, ngay_bat_dau, ngay_ket_thuc
) VALUES
('NV001', 'Nguyễn Văn Hùng',  '001099001001', '0901000001', 50000000, UPPER(ENCODE(DIGEST('pass123', 'sha256'), 'hex')), 1, 1, 250, 'giam_doc',     '2020-01-01', NULL),
('NV002', 'Trần Thị Mai',     '001099002002', '0901000002', 25000000, UPPER(ENCODE(DIGEST('pass123', 'sha256'), 'hex')), 1, 2, 200, 'truong_phong', '2020-06-01', NULL),
('NV003', 'Lê Hoàng Nam',     '001099003003', '0901000003', 18000000, UPPER(ENCODE(DIGEST('pass123', 'sha256'), 'hex')), 1, 2, 180, 'pho_phong',    '2021-01-15', NULL),
('NV004', 'Phạm Thị Hương',   '001099004004', '0901000004', 12000000, UPPER(ENCODE(DIGEST('pass123', 'sha256'), 'hex')), 1, 2, 150, 'nhan_vien',    '2022-03-01', NULL),
('NV005', 'Hoàng Đức Anh',    '001099005005', '0901000005', 12000000, UPPER(ENCODE(DIGEST('pass123', 'sha256'), 'hex')), 1, 3, 140, 'nhan_vien',    '2022-06-15', NULL)
ON CONFLICT (ma_nhan_vien) DO NOTHING;

UPDATE phong_ban SET ma_nv = 2 WHERE ma_pb = 2;
UPDATE phong_ban SET ma_nv = 3 WHERE ma_pb = 3;

CREATE OR REPLACE VIEW v_san_pham_theo_chi_nhanh AS
SELECT
    cn.ma_chi_nhanh,
    cn.ten_chi_nhanh,
    lsp.ten_loai_sp,
    sp.ma_sp,
    sp.ten_sp,
    sp.gia,
    sp.ti_le_loi_nhuan,
    sp.ti_le_giam_gia,
    ROUND(sp.gia * (1 + sp.ti_le_loi_nhuan / 100) * (1 - sp.ti_le_giam_gia / 100), 0) AS gia_ban_thuc_te,
    sp.trang_thai
FROM SAN_PHAM sp
JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
JOIN chi_nhanh cn ON lsp.ma_chi_nhanh = cn.ma_chi_nhanh;

CREATE OR REPLACE VIEW v_thong_ke_chi_nhanh AS
SELECT
    cn.ma_chi_nhanh,
    cn.ten_chi_nhanh,
    COUNT(sp.ma_sp) AS so_san_pham,
    AVG(sp.gia) AS gia_trung_binh,
    SUM(CASE WHEN sp.trang_thai = 1 THEN 1 ELSE 0 END) AS sp_dang_ban,
    SUM(CASE WHEN sp.trang_thai = 0 THEN 1 ELSE 0 END) AS sp_ngung_ban
FROM chi_nhanh cn
LEFT JOIN loai_sp lsp ON cn.ma_chi_nhanh = lsp.ma_chi_nhanh
LEFT JOIN SAN_PHAM sp ON lsp.ma_loai_sp = sp.ma_loai_sp
GROUP BY cn.ma_chi_nhanh, cn.ten_chi_nhanh;

CREATE OR REPLACE VIEW v_nhan_vien_phong_ban AS
SELECT
    pb.ten_pb,
    nv.ma_nhan_vien,
    nv.ho_ten,
    nv.chuc_vu,
    nv.luong,
    nv.ma_ngay_lam,
    nv.trang_thai,
    CASE WHEN nv.trang_thai = 1 THEN 'Đang làm' ELSE 'Đã nghỉ' END AS tinh_trang
FROM NHAN_VIEN nv
JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb;

CREATE OR REPLACE VIEW v_luong_phong_ban AS
SELECT
    pb.ten_pb,
    COUNT(*) AS so_nhan_vien,
    SUM(nv.luong) AS tong_luong,
    AVG(nv.luong) AS luong_trung_binh,
    MIN(nv.luong) AS luong_thap_nhat,
    MAX(nv.luong) AS luong_cao_nhat
FROM NHAN_VIEN nv
JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb
WHERE nv.trang_thai = 1
GROUP BY pb.ma_pb, pb.ten_pb;

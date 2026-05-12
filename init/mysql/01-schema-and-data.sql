SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS chi_nhanh (
    ma_chi_nhanh VARCHAR(20) PRIMARY KEY,
    ten_chi_nhanh VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS loai_sp (
    ma_loai_sp VARCHAR(20) PRIMARY KEY,
    ten_loai_sp VARCHAR(100) NOT NULL,
    ma_chi_nhanh VARCHAR(20) NOT NULL,
    CONSTRAINT fk_loai_sp_chi_nhanh
        FOREIGN KEY (ma_chi_nhanh) REFERENCES chi_nhanh(ma_chi_nhanh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NCC (
    ma_NCC INT AUTO_INCREMENT PRIMARY KEY,
    ten_NCC VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS SAN_PHAM (
    ma_sp VARCHAR(20) PRIMARY KEY,
    ten_sp VARCHAR(200) NOT NULL,
    gia DECIMAL(15, 2) NOT NULL,
    ti_le_loi_nhuan DECIMAL(5, 2) DEFAULT 0.00,
    ti_le_giam_gia DECIMAL(5, 2) DEFAULT 0.00,
    mo_ta TEXT,
    ma_loai_sp VARCHAR(20) NOT NULL,
    ma_ncc INT NOT NULL,
    trang_thai INT DEFAULT 1,
    tao_vao DATETIME DEFAULT CURRENT_TIMESTAMP,
    cap_nhat_vao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_san_pham_loai_sp
        FOREIGN KEY (ma_loai_sp) REFERENCES loai_sp(ma_loai_sp),
    CONSTRAINT fk_san_pham_ncc
        FOREIGN KEY (ma_ncc) REFERENCES NCC(ma_NCC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phong_ban (
    ma_pb INT AUTO_INCREMENT PRIMARY KEY,
    ten_pb VARCHAR(100) NOT NULL,
    ma_nv INT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NHAN_VIEN (
    ma_nhan_vien VARCHAR(20) PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    cccd VARCHAR(20),
    sdt VARCHAR(15),
    luong DECIMAL(15, 2) DEFAULT 0,
    mat_khau VARCHAR(255) NOT NULL,
    trang_thai INT DEFAULT 1,
    ma_phong_ban INT,
    ma_ngay_lam INT DEFAULT 0,
    chuc_vu VARCHAR(20) DEFAULT 'nhan_vien',
    ngay_bat_dau DATETIME,
    ngay_ket_thuc DATETIME,
    CONSTRAINT fk_nhan_vien_phong_ban
        FOREIGN KEY (ma_phong_ban) REFERENCES phong_ban(ma_pb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_sp_loai ON SAN_PHAM(ma_loai_sp);
CREATE INDEX idx_sp_ncc ON SAN_PHAM(ma_ncc);
CREATE INDEX idx_sp_trangthai ON SAN_PHAM(trang_thai);
CREATE INDEX idx_nv_pb ON NHAN_VIEN(ma_phong_ban);
CREATE INDEX idx_nv_chucvu ON NHAN_VIEN(chuc_vu);

CREATE TABLE IF NOT EXISTS sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL UNIQUE,
    event_type VARCHAR(50) NOT NULL,
    ma_sp VARCHAR(50),
    version INT NOT NULL,
    source VARCHAR(50),
    target_branch VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    message TEXT,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    applied_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_sync_log_version ON sync_log(version);
CREATE INDEX idx_sync_log_status ON sync_log(status);
CREATE INDEX idx_sync_log_ma_sp ON sync_log(ma_sp);

CREATE TABLE IF NOT EXISTS HOA_DON (
    ma_hd VARCHAR(20) PRIMARY KEY,
    ngay_lap DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ma_nhan_vien VARCHAR(20) NOT NULL,
    ten_nhan_vien VARCHAR(100) NULL,
    ten_kh VARCHAR(100) NULL,
    sdt_kh VARCHAR(15) NULL,
    tong_tien DECIMAL(15, 2) NOT NULL DEFAULT 0,
    ghi_chu TEXT NULL,
    CONSTRAINT fk_hoa_don_nhan_vien
        FOREIGN KEY (ma_nhan_vien) REFERENCES NHAN_VIEN(ma_nhan_vien)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS CT_HOA_DON (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_hd VARCHAR(20) NOT NULL,
    ma_sp VARCHAR(20) NOT NULL,
    so_luong INT NOT NULL,
    don_gia DECIMAL(15, 2) NOT NULL,
    thanh_tien DECIMAL(15, 2) NOT NULL,
    CONSTRAINT fk_ct_hd_hoa_don
        FOREIGN KEY (ma_hd) REFERENCES HOA_DON(ma_hd) ON DELETE CASCADE,
    CONSTRAINT fk_ct_hd_san_pham
        FOREIGN KEY (ma_sp) REFERENCES SAN_PHAM(ma_sp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_hd_ngay ON HOA_DON(ngay_lap);
CREATE INDEX idx_hd_nv ON HOA_DON(ma_nhan_vien);
CREATE INDEX idx_cthd_hd ON CT_HOA_DON(ma_hd);
CREATE INDEX idx_cthd_sp ON CT_HOA_DON(ma_sp);

INSERT IGNORE INTO chi_nhanh (ma_chi_nhanh, ten_chi_nhanh) VALUES
('CN01', 'Chi nhánh Hà Nội'),
('CN02', 'Chi nhánh TP.HCM');

INSERT IGNORE INTO loai_sp (ma_loai_sp, ten_loai_sp, ma_chi_nhanh) VALUES
('LSP01', 'Laptop', 'CN01'),
('LSP02', 'Điện thoại', 'CN01'),
('LSP03', 'Phụ kiện', 'CN02'),
('LSP04', 'Màn hình', 'CN02'),
('LSP05', 'Linh kiện PC', 'CN01'),
('LSP06', 'Thiết bị mạng', 'CN01'),
('LSP07', 'Máy tính bảng', 'CN02'),
('LSP08', 'Thiết bị âm thanh', 'CN02'),
('LSP09', 'Camera và Webcam', 'CN01'),
('LSP10', 'Thiết bị đeo', 'CN02');

INSERT IGNORE INTO NCC (ma_NCC, ten_NCC) VALUES
(1,  'Apple Việt Nam'),
(2,  'Samsung Việt Nam'),
(3,  'Dell Technologies'),
(4,  'Logitech Distribution'),
(5,  'LG Electronics'),
(6,  'Kingston Technology'),
(7,  'JBL / Harman'),
(8,  'TP-Link Việt Nam'),
(9,  'ASUS Việt Nam'),
(10, 'Lenovo Việt Nam'),
(11, 'HP Việt Nam'),
(12, 'Acer Việt Nam'),
(13, 'MSI Gaming'),
(14, 'Xiaomi Việt Nam'),
(15, 'Sony Vietnam'),
(16, 'Microsoft Vietnam'),
(17, 'Western Digital'),
(18, 'Seagate Technology'),
(19, 'Anker Innovations'),
(20, 'Bose Audio Vietnam');

INSERT IGNORE INTO SAN_PHAM (
    ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia,
    mo_ta, ma_loai_sp, ma_ncc, trang_thai, tao_vao
) VALUES
('SP001', 'Laptop Dell XPS 15', 32000000, 15.00, 0.00, 'Laptop cao cấp, màn 15.6 inch OLED', 'LSP01', 3, 1, '2025-01-10'),
('SP002', 'MacBook Air M3', 28000000, 12.00, 5.00, 'MacBook Air chip M3, 16GB RAM', 'LSP01', 1, 1, '2025-01-10'),
('SP003', 'Laptop Dell Inspiron 14', 18000000, 18.00, 10.00, 'Laptop văn phòng, i5 thế hệ 13', 'LSP01', 3, 1, '2025-01-15'),
('SP004', 'iPhone 15 Pro Max', 29000000, 10.00, 0.00, 'iPhone 15 Pro Max 256GB', 'LSP02', 1, 1, '2025-01-12'),
('SP005', 'Samsung Galaxy S24 Ultra', 26000000, 12.00, 8.00, 'Samsung flagship, camera 200MP', 'LSP02', 2, 1, '2025-01-12'),
('SP006', 'AirPods Pro 2', 5500000, 20.00, 0.00, 'Tai nghe không dây chống ồn', 'LSP03', 1, 1, '2025-01-20'),
('SP007', 'Chuột Logitech MX Master 3S', 2200000, 25.00, 5.00, 'Chuột không dây cao cấp', 'LSP03', 4, 1, '2025-01-20'),
('SP008', 'Màn hình LG 27 inch 4K', 8000000, 15.00, 10.00, 'IPS 4K, 60Hz, HDR400', 'LSP04', 5, 1, '2025-01-25'),
('SP009', 'SSD Samsung 990 Pro 1TB', 3200000, 20.00, 5.00, 'NVMe Gen4, đọc 7450MB/s', 'LSP05', 2, 1, '2025-02-01'),
('SP010', 'Router TP-Link Archer AX73', 2800000, 22.00, 0.00, 'WiFi 6, AX5400, MU-MIMO', 'LSP06', 8, 1, '2025-02-15');

INSERT IGNORE INTO phong_ban (ma_pb, ten_pb, ma_nv) VALUES
(1, 'Ban Giám đốc', NULL),
(2, 'Phòng Kinh doanh', NULL),
(3, 'Phòng Kỹ thuật', NULL),
(4, 'Phòng Kho vận', NULL),
(5, 'Phòng Nhân sự', NULL),
(6, 'Phòng Kế toán', NULL);

INSERT IGNORE INTO NHAN_VIEN (
    ma_nhan_vien, ho_ten, cccd, sdt, luong, mat_khau, trang_thai,
    ma_phong_ban, ma_ngay_lam, chuc_vu, ngay_bat_dau, ngay_ket_thuc
) VALUES
('NV001', 'Nguyễn Văn Hùng', '001099001001', '0901000001', 50000000, UPPER(SHA2('pass123', 256)), 1, 1, 250, 'giam_doc', '2020-01-01', NULL),
('NV002', 'Trần Thị Mai', '001099002002', '0901000002', 25000000, UPPER(SHA2('pass123', 256)), 1, 2, 200, 'truong_phong', '2020-06-01', NULL),
('NV003', 'Lê Hoàng Nam', '001099003003', '0901000003', 18000000, UPPER(SHA2('pass123', 256)), 1, 2, 180, 'pho_phong', '2021-01-15', NULL),
('NV004', 'Phạm Thị Hương', '001099004004', '0901000004', 12000000, UPPER(SHA2('pass123', 256)), 1, 2, 150, 'nhan_vien', '2022-03-01', NULL),
('NV005', 'Hoàng Đức Anh', '001099005005', '0901000005', 12000000, UPPER(SHA2('pass123', 256)), 1, 3, 140, 'nhan_vien', '2022-06-15', NULL),
('CN001', 'Tai khoan demo CN001', '000000000001', '0900000001', 50000000, UPPER(SHA2('pass123', 256)), 1, 1, 250, 'giam_doc', '2020-01-01', NULL);

UPDATE phong_ban SET ma_nv = 2 WHERE ma_pb = 2;
UPDATE phong_ban SET ma_nv = 3 WHERE ma_pb = 3;

INSERT IGNORE INTO HOA_DON (ma_hd, ngay_lap, ma_nhan_vien, ten_nhan_vien, ten_kh, sdt_kh, tong_tien, ghi_chu) VALUES
('HD001', '2026-04-12 09:15:00', 'NV004', 'Phạm Thị Hương', 'Nguyễn Văn A', '0911000111', 32000000, 'Mua trả góp'),
('HD002', '2026-04-22 14:40:00', 'NV004', 'Phạm Thị Hương', 'Trần Thị B',   '0911000222', 28000000, NULL),
('HD003', '2026-05-03 10:05:00', 'NV005', 'Hoàng Đức Anh',  'Lê Văn C',     '0911000333', 31200000, 'Khách quen');

INSERT IGNORE INTO CT_HOA_DON (ma_hd, ma_sp, so_luong, don_gia, thanh_tien) VALUES
('HD001', 'SP001', 1, 32000000, 32000000),
('HD002', 'SP002', 1, 28000000, 28000000),
('HD003', 'SP004', 1, 29000000, 29000000),
('HD003', 'SP007', 1,  2200000,  2200000);

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

CREATE OR REPLACE VIEW v_doanh_thu_theo_ngay AS
SELECT
    DATE(hd.ngay_lap) AS ngay,
    COUNT(DISTINCT hd.ma_hd) AS so_hoa_don,
    SUM(hd.tong_tien)        AS tong_doanh_thu
FROM HOA_DON hd
GROUP BY DATE(hd.ngay_lap);

CREATE OR REPLACE VIEW v_doanh_thu_theo_san_pham AS
SELECT
    sp.ma_sp,
    sp.ten_sp,
    SUM(ct.so_luong)   AS tong_so_luong,
    SUM(ct.thanh_tien) AS tong_doanh_thu
FROM CT_HOA_DON ct
JOIN SAN_PHAM sp ON ct.ma_sp = sp.ma_sp
GROUP BY sp.ma_sp, sp.ten_sp;

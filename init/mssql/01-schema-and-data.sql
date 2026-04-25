-- ============================================================
--  SCHEMA + DỮ LIỆU DUMMY (T-SQL cho SQL Server)
-- ============================================================

-- Tạo database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'quan_ly_chi_nhanh')
    CREATE DATABASE quan_ly_chi_nhanh;
GO

USE quan_ly_chi_nhanh;
GO

-- ─────────────────────────────────────
--  1. TẠO BẢNG
-- ─────────────────────────────────────

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'chi_nhanh')
CREATE TABLE chi_nhanh (
    ma_chi_nhanh NVARCHAR(20) PRIMARY KEY,
    ten_chi_nhanh NVARCHAR(100) NOT NULL
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'loai_sp')
CREATE TABLE loai_sp (
    ma_loai_sp NVARCHAR(20) PRIMARY KEY,
    ten_loai_sp NVARCHAR(100) NOT NULL,
    ma_chi_nhanh NVARCHAR(20) NOT NULL,
    FOREIGN KEY (ma_chi_nhanh) REFERENCES chi_nhanh(ma_chi_nhanh)
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NCC')
CREATE TABLE NCC (
    ma_NCC INT IDENTITY(1,1) PRIMARY KEY,
    ten_NCC NVARCHAR(150) NOT NULL
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SAN_PHAM')
CREATE TABLE SAN_PHAM (
    ma_sp NVARCHAR(20) PRIMARY KEY,
    ten_sp NVARCHAR(200) NOT NULL,
    gia DECIMAL(15, 2) NOT NULL,
    ti_le_loi_nhuan DECIMAL(5, 2) DEFAULT 0.00,
    ti_le_giam_gia DECIMAL(5, 2) DEFAULT 0.00,  -- Quản lý bởi chi nhánh
    mo_ta NVARCHAR(MAX),
    ma_loai_sp NVARCHAR(20) NOT NULL,
    ma_ncc INT NOT NULL,
    trang_thai INT DEFAULT 1,  -- 1=active, 0=inactive
    tao_vao DATETIME DEFAULT GETDATE(),
    cap_nhat_vao DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ma_loai_sp) REFERENCES loai_sp(ma_loai_sp),
    FOREIGN KEY (ma_ncc) REFERENCES NCC(ma_NCC)
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'phong_ban')
CREATE TABLE phong_ban (
    ma_pb INT IDENTITY(1,1) PRIMARY KEY,
    ten_pb NVARCHAR(100) NOT NULL,
    ma_nv INT NULL
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NHAN_VIEN')
CREATE TABLE NHAN_VIEN (
    ma_nhan_vien NVARCHAR(20) PRIMARY KEY,
    ho_ten NVARCHAR(100) NOT NULL,
    cccd NVARCHAR(20),
    sdt NVARCHAR(15),
    luong DECIMAL(15, 2) DEFAULT 0,
    mat_khau NVARCHAR(255) NOT NULL,
    trang_thai INT DEFAULT 1,  -- 1=đang làm, 0=nghỉ
    ma_phong_ban INT,
    ma_ngay_lam INT DEFAULT 0,
    chuc_vu NVARCHAR(20) DEFAULT 'nhan_vien',  -- nhan_vien, truong_phong, pho_phong, giam_doc, admin
    ngay_bat_dau DATETIME,
    ngay_ket_thuc DATETIME,
    FOREIGN KEY (ma_phong_ban) REFERENCES phong_ban(ma_pb)
);
GO

-- Index
CREATE NONCLUSTERED INDEX idx_sp_loai ON SAN_PHAM(ma_loai_sp);
CREATE NONCLUSTERED INDEX idx_sp_ncc ON SAN_PHAM(ma_ncc);
CREATE NONCLUSTERED INDEX idx_sp_trangthai ON SAN_PHAM(trang_thai);
CREATE NONCLUSTERED INDEX idx_nv_pb ON NHAN_VIEN(ma_phong_ban);
CREATE NONCLUSTERED INDEX idx_nv_chucvu ON NHAN_VIEN(chuc_vu);
GO


-- ─────────────────────────────────────
--  2. DỮ LIỆU DUMMY
-- ─────────────────────────────────────

-- Chi nhánh
INSERT INTO chi_nhanh VALUES
(N'CN01', N'Chi nhánh Hà Nội'),
(N'CN02', N'Chi nhánh TP.HCM'),
(N'CN03', N'Chi nhánh Đà Nẵng'),
(N'CN04', N'Chi nhánh Cần Thơ'),
(N'CN05', N'Chi nhánh Hải Phòng');

-- Loại sản phẩm
INSERT INTO loai_sp VALUES
(N'LSP01', N'Laptop',            N'CN01'),
(N'LSP02', N'Điện thoại',        N'CN01'),
(N'LSP03', N'Phụ kiện',          N'CN02'),
(N'LSP04', N'Màn hình',          N'CN02'),
(N'LSP05', N'Linh kiện PC',      N'CN03'),
(N'LSP06', N'Thiết bị mạng',     N'CN03'),
(N'LSP07', N'Máy tính bảng',     N'CN04'),
(N'LSP08', N'Thiết bị âm thanh', N'CN04'),
(N'LSP09', N'Camera & Webcam',   N'CN05'),
(N'LSP10', N'Thiết bị đeo',      N'CN05');

-- Nhà cung cấp
SET IDENTITY_INSERT NCC ON;
INSERT INTO NCC (ma_NCC, ten_NCC) VALUES
(1, N'Apple Việt Nam'),
(2, N'Samsung Việt Nam'),
(3, N'Dell Technologies'),
(4, N'Logitech Distribution'),
(5, N'LG Electronics'),
(6, N'Kingston Technology'),
(7, N'JBL / Harman'),
(8, N'TP-Link Việt Nam');
SET IDENTITY_INSERT NCC OFF;

-- Sản phẩm (25 SP)
INSERT INTO SAN_PHAM (ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia, mo_ta, ma_loai_sp, ma_ncc, trang_thai, tao_vao) VALUES
(N'SP001', N'Laptop Dell XPS 15',           32000000, 15.00, 0.00,  N'Laptop cao cấp, màn 15.6 inch OLED',            N'LSP01', 3, 1, '2025-01-10'),
(N'SP002', N'MacBook Air M3',               28000000, 12.00, 5.00,  N'MacBook Air chip M3, 16GB RAM',                  N'LSP01', 1, 1, '2025-01-10'),
(N'SP003', N'Laptop Dell Inspiron 14',      18000000, 18.00, 10.00, N'Laptop văn phòng, i5 thế hệ 13',                N'LSP01', 3, 1, '2025-01-15'),
(N'SP004', N'iPhone 15 Pro Max',            29000000, 10.00, 0.00,  N'iPhone 15 Pro Max 256GB',                        N'LSP02', 1, 1, '2025-01-12'),
(N'SP005', N'Samsung Galaxy S24 Ultra',     26000000, 12.00, 8.00,  N'Samsung flagship, camera 200MP',                 N'LSP02', 2, 1, '2025-01-12'),
(N'SP006', N'iPhone 15',                    22000000, 10.00, 3.00,  N'iPhone 15 128GB',                                N'LSP02', 1, 1, '2025-02-01'),
(N'SP007', N'AirPods Pro 2',                5500000,  20.00, 0.00,  N'Tai nghe không dây chống ồn',                    N'LSP03', 1, 1, '2025-01-20'),
(N'SP008', N'Chuột Logitech MX Master 3S',  2200000, 25.00, 5.00,  N'Chuột không dây cao cấp',                       N'LSP03', 4, 1, '2025-01-20'),
(N'SP009', N'Bàn phím Logitech MX Keys',    2800000, 22.00, 0.00,  N'Bàn phím không dây, backlit',                   N'LSP03', 4, 1, '2025-02-05'),
(N'SP010', N'Màn hình LG 27" 4K',           8000000, 15.00, 10.00, N'IPS 4K, 60Hz, HDR400',                           N'LSP04', 5, 1, '2025-01-25'),
(N'SP011', N'Màn hình Dell 24" FHD',         5000000, 18.00, 0.00,  N'IPS FHD, 75Hz, chống lóa',                      N'LSP04', 3, 1, '2025-01-25'),
(N'SP012', N'SSD Samsung 990 Pro 1TB',       3200000, 20.00, 5.00,  N'NVMe Gen4, đọc 7450MB/s',                       N'LSP05', 2, 1, '2025-02-01'),
(N'SP013', N'RAM Kingston Fury 16GB DDR5',   1500000, 25.00, 0.00,  N'5600MHz, tản nhiệt',                            N'LSP05', 6, 1, '2025-02-01'),
(N'SP014', N'SSD Kingston A2000 512GB',      1200000, 28.00, 10.00, N'NVMe Gen3, đọc 2200MB/s',                       N'LSP05', 6, 1, '2025-02-10'),
(N'SP015', N'Router TP-Link Archer AX73',    2800000, 22.00, 0.00,  N'WiFi 6, AX5400, MU-MIMO',                       N'LSP06', 8, 1, '2025-02-15'),
(N'SP016', N'Switch TP-Link 8 Port Gigabit',   600000, 30.00, 0.00, N'Switch không quản lý, vỏ kim loại',             N'LSP06', 8, 1, '2025-02-15'),
(N'SP017', N'iPad Air M2',                  16000000, 12.00, 0.00,  N'iPad Air 11 inch, chip M2',                      N'LSP07', 1, 1, '2025-01-18'),
(N'SP018', N'Samsung Galaxy Tab S9',        14000000, 14.00, 5.00,  N'Tab S9 128GB, S Pen đi kèm',                    N'LSP07', 2, 1, '2025-01-18'),
(N'SP019', N'Loa JBL Flip 6',               2600000, 20.00, 8.00,  N'Loa bluetooth chống nước IP67',                  N'LSP08', 7, 1, '2025-02-20'),
(N'SP020', N'Loa JBL Charge 5',             3800000, 18.00, 0.00,  N'Loa bluetooth, pin 20 giờ',                      N'LSP08', 7, 1, '2025-02-20'),
(N'SP021', N'Webcam Logitech C920',          1800000, 25.00, 5.00,  N'Full HD 1080p, tự động lấy nét',                N'LSP09', 4, 1, '2025-03-01'),
(N'SP022', N'Webcam Logitech Brio 4K',       4500000, 20.00, 0.00,  N'4K Ultra HD, HDR, Windows Hello',               N'LSP09', 4, 1, '2025-03-01'),
(N'SP023', N'Apple Watch Series 9',          9500000, 12.00, 0.00,  N'GPS, viền nhôm, dây sport',                     N'LSP10', 1, 1, '2025-02-10'),
(N'SP024', N'Samsung Galaxy Watch 6',        6500000, 15.00, 10.00, N'Bluetooth, đo SpO2, ECG',                       N'LSP10', 2, 1, '2025-02-10'),
(N'SP025', N'Apple Watch SE 2',              6000000, 14.00, 5.00,  N'GPS, chip S8, phát hiện tai nạn',               N'LSP10', 1, 0, '2025-03-05');

-- Phòng ban
SET IDENTITY_INSERT phong_ban ON;
INSERT INTO phong_ban (ma_pb, ten_pb, ma_nv) VALUES
(1, N'Ban Giám đốc',     NULL),
(2, N'Phòng Kinh doanh',  NULL),
(3, N'Phòng Kỹ thuật',    NULL),
(4, N'Phòng Kho vận',     NULL),
(5, N'Phòng Nhân sự',     NULL),
(6, N'Phòng Kế toán',     NULL);
SET IDENTITY_INSERT phong_ban OFF;

-- Nhân viên (20 người)
INSERT INTO NHAN_VIEN VALUES
(N'NV001', N'Nguyễn Văn Hùng',    N'001099001001', N'0901000001', 50000000, HASHBYTES('SHA2_256', 'pass123'), 1, 1, 250, N'giam_doc',    '2020-01-01', NULL),
(N'NV002', N'Trần Thị Mai',       N'001099002002', N'0901000002', 25000000, HASHBYTES('SHA2_256', 'pass123'), 1, 2, 200, N'truong_phong','2020-06-01', NULL),
(N'NV003', N'Lê Hoàng Nam',       N'001099003003', N'0901000003', 18000000, HASHBYTES('SHA2_256', 'pass123'), 1, 2, 180, N'pho_phong',   '2021-01-15', NULL),
(N'NV004', N'Phạm Thị Hương',     N'001099004004', N'0901000004', 12000000, HASHBYTES('SHA2_256', 'pass123'), 1, 2, 150, N'nhan_vien',   '2022-03-01', NULL),
(N'NV005', N'Hoàng Đức Anh',      N'001099005005', N'0901000005', 12000000, HASHBYTES('SHA2_256', 'pass123'), 1, 2, 140, N'nhan_vien',   '2022-06-15', NULL),
(N'NV006', N'Vũ Thị Lan',         N'001099006006', N'0901000006', 11000000, HASHBYTES('SHA2_256', 'pass123'), 1, 2, 120, N'nhan_vien',   '2023-01-10', NULL),
(N'NV007', N'Đặng Minh Tuấn',     N'001099007007', N'0901000007', 28000000, HASHBYTES('SHA2_256', 'pass123'), 1, 3, 220, N'truong_phong','2020-03-01', NULL),
(N'NV008', N'Bùi Thị Ngọc',       N'001099008008', N'0901000008', 20000000, HASHBYTES('SHA2_256', 'pass123'), 1, 3, 190, N'pho_phong',   '2021-02-01', NULL),
(N'NV009', N'Ngô Quốc Bảo',       N'001099009009', N'0901000009', 15000000, HASHBYTES('SHA2_256', 'pass123'), 1, 3, 160, N'nhan_vien',   '2022-01-10', NULL),
(N'NV010', N'Đỗ Thị Phương',      N'001099010010', N'0901000010', 14000000, HASHBYTES('SHA2_256', 'pass123'), 1, 3, 140, N'nhan_vien',   '2022-08-01', NULL),
(N'NV011', N'Lý Văn Thành',       N'001099011011', N'0901000011', 22000000, HASHBYTES('SHA2_256', 'pass123'), 1, 4, 200, N'truong_phong','2020-04-01', NULL),
(N'NV012', N'Trịnh Thị Hà',       N'001099012012', N'0901000012', 13000000, HASHBYTES('SHA2_256', 'pass123'), 1, 4, 130, N'nhan_vien',   '2022-05-01', NULL),
(N'NV013', N'Cao Đức Mạnh',       N'001099013013', N'0901000013', 12000000, HASHBYTES('SHA2_256', 'pass123'), 1, 4, 110, N'nhan_vien',   '2023-02-15', NULL),
(N'NV014', N'Hồ Thị Yến',         N'001099014014', N'0901000014', 24000000, HASHBYTES('SHA2_256', 'pass123'), 1, 5, 210, N'truong_phong','2020-05-01', NULL),
(N'NV015', N'Dương Văn Khoa',     N'001099015015', N'0901000015', 13000000, HASHBYTES('SHA2_256', 'pass123'), 1, 5, 145, N'nhan_vien',   '2022-04-01', NULL),
(N'NV016', N'Phan Thị Trang',     N'001099016016', N'0901000016', 12000000, HASHBYTES('SHA2_256', 'pass123'), 1, 5, 120, N'nhan_vien',   '2023-03-01', NULL),
(N'NV017', N'Mai Văn Đức',        N'001099017017', N'0901000017', 23000000, HASHBYTES('SHA2_256', 'pass123'), 1, 6, 205, N'truong_phong','2020-07-01', NULL),
(N'NV018', N'Tạ Thị Linh',       N'001099018018', N'0901000018', 15000000, HASHBYTES('SHA2_256', 'pass123'), 1, 6, 160, N'pho_phong',   '2021-06-01', NULL),
(N'NV019', N'Châu Minh Quân',    N'001099019019', N'0901000019', 12000000, HASHBYTES('SHA2_256', 'pass123'), 1, 6, 130, N'nhan_vien',   '2022-09-01', NULL),
(N'NV020', N'Lương Thị Vân',      N'001099020020', N'0901000020', 11000000, HASHBYTES('SHA2_256', 'pass123'), 0, 2, 90,  N'nhan_vien',   '2023-01-01', '2024-12-31');

-- Cập nhật trưởng phòng
UPDATE phong_ban SET ma_nv = 2  WHERE ma_pb = 2;
UPDATE phong_ban SET ma_nv = 7  WHERE ma_pb = 3;
UPDATE phong_ban SET ma_nv = 11 WHERE ma_pb = 4;
UPDATE phong_ban SET ma_nv = 14 WHERE ma_pb = 5;
UPDATE phong_ban SET ma_nv = 17 WHERE ma_pb = 6;
GO


-- ─────────────────────────────────────
--  3. VIEW PHÂN TÍCH
-- ─────────────────────────────────────

CREATE OR ALTER VIEW v_san_pham_theo_chi_nhanh AS
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
GO

CREATE OR ALTER VIEW v_thong_ke_chi_nhanh AS
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
GO

CREATE OR ALTER VIEW v_nhan_vien_phong_ban AS
SELECT
    pb.ten_pb,
    nv.ma_nhan_vien,
    nv.ho_ten,
    nv.chuc_vu,
    nv.luong,
    nv.ma_ngay_lam,
    nv.trang_thai,
    CASE WHEN nv.trang_thai = 1 THEN N'Đang làm' ELSE N'Đã nghỉ' END AS tinh_trang
FROM NHAN_VIEN nv
JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb;
GO

CREATE OR ALTER VIEW v_luong_phong_ban AS
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
GO

PRINT N'✅ Database quan_ly_chi_nhanh đã sẵn sàng!';
GO

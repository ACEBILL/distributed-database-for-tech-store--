-- 1. Tạo bảng DANH_MUC
CREATE TABLE DANH_MUC (
  danh_muc_id VARCHAR(50) PRIMARY KEY,
  ten_danh_muc VARCHAR(255),
  status INT
);

-- 2. Tạo bảng NCC (Nhà Cung Cấp)
CREATE TABLE NCC (
  ma_NCC INT PRIMARY KEY,
  ten_NCC VARCHAR(255)
);

-- 3. Tạo bảng NHAN_VIEN
CREATE TABLE NHAN_VIEN (
  ma_nhan_vien VARCHAR(50) PRIMARY KEY,
  ho_ten VARCHAR(255),
  cccd VARCHAR(20),
  sdt VARCHAR(15),
  luong DECIMAL(15, 2),
  trang_thai INT,
  mat_khau VARCHAR(255)
);

-- 4. Tạo bảng KHACH_HANG
CREATE TABLE KHACH_HANG (
  ma_kh VARCHAR(50) PRIMARY KEY,
  ten_kh VARCHAR(255),
  sdt VARCHAR(15)
);

-- 5. Tạo bảng SAN_PHAM
CREATE TABLE SAN_PHAM (
  ma_sp VARCHAR(50) PRIMARY KEY,
  ten_sp VARCHAR(255),
  sl_ton_kho INT,
  gia DECIMAL(15, 2),
  ti_le_loi_nhuan DECIMAL(5, 2),
  ti_le_giam_gia DECIMAL(5, 2),
  mo_ta TEXT,
  danh_muc_id VARCHAR(50),
  ma_ncc INT,
  trang_thai INT,
  da_tao_vao DATETIME DEFAULT CURRENT_TIMESTAMP,
  da_cap_nhat_vao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_sp_danhmuc FOREIGN KEY (danh_muc_id) REFERENCES DANH_MUC(danh_muc_id),
  CONSTRAINT fk_sp_ncc FOREIGN KEY (ma_ncc) REFERENCES NCC(ma_NCC)
);

-- 6. Tạo bảng DON_HANG
CREATE TABLE DON_HANG (
  ma_donhang VARCHAR(50) PRIMARY KEY,
  trang_thai VARCHAR(50),
  thoi_gian_dat DATETIME,
  thoi_gian_hoan_thanh DATETIME,
  phuong_thuc_thanh_toan VARCHAR(50), -- 'Tiền mặt', 'Chuyển khoản', 'Ví điện tử'
  ma_kh VARCHAR(50),
  ma_nhan_vien VARCHAR(50),
  CONSTRAINT fk_dh_khachhang FOREIGN KEY (ma_kh) REFERENCES KHACH_HANG(ma_kh),
  CONSTRAINT fk_dh_nhanvien FOREIGN KEY (ma_nhan_vien) REFERENCES NHAN_VIEN(ma_nhan_vien)
);

-- 7. Tạo bảng CT_DON_HANG (Chi tiết đơn hàng)
CREATE TABLE CT_DON_HANG (
  ma_donhang VARCHAR(50),
  ma_sp VARCHAR(50),
  so_luong INT,
  don_gia INT,
  PRIMARY KEY (ma_donhang, ma_sp),
  CONSTRAINT fk_ctdh_donhang FOREIGN KEY (ma_donhang) REFERENCES DON_HANG(ma_donhang),
  CONSTRAINT fk_ctdh_sanpham FOREIGN KEY (ma_sp) REFERENCES SAN_PHAM(ma_sp)
);
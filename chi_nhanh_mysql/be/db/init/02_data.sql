-- 1. Thêm danh mục sản phẩm công nghệ
INSERT INTO DANH_MUC (danh_muc_id, ten_danh_muc, status) VALUES 
('DM01', 'Laptop & PC', 1),
('DM02', 'Điện thoại & Tablet', 1),
('DM03', 'Linh kiện (CPU, RAM, VGA)', 1),
('DM04', 'Phụ kiện (Chuột, Phím)', 1);

-- 2. Thêm nhà cung cấp thiết bị
INSERT INTO NCC (ma_NCC, ten_NCC) VALUES 
(1, 'Thế Giới Linh Kiện Apple'),
(2, 'Nhà phân phối Samsung VN'),
(3, 'Xưởng công nghệ ASUS');

-- 3. Thêm nhân viên cửa hàng
INSERT INTO NHAN_VIEN (ma_nhan_vien, ho_ten, cccd, sdt, luong, trang_thai, mat_khau) VALUES 
('NV01', 'Trần Văn Kỹ Thuật', '012345678910', '0912345678', 18000000, 1, '123456'),
('NV02', 'Nguyễn Thị Sale', '012345678911', '0987654321', 10000000, 1, '123456');

-- 4. Thêm khách hàng yêu công nghệ
INSERT INTO KHACH_HANG (ma_kh, ten_kh, sdt) VALUES 
('KH01', 'Anh Minh Tech', '0911223344'),
('KH02', 'Chị Hạnh Dev', '0988776655'),
('KH03', 'Khách mua lẻ', '0000000000');

-- 5. Thêm sản phẩm công nghệ
INSERT INTO SAN_PHAM (ma_sp, ten_sp, sl_ton_kho, gia, ti_le_loi_nhuan, ti_le_giam_gia, mo_ta, danh_muc_id, ma_ncc, trang_thai) VALUES 
('SP01', 'MacBook Pro M3', 15, 45000000, 0.2, 0.05, 'Màu Space Black, 16GB RAM', 'DM01', 1, 1),
('SP02', 'iPhone 15 Pro Max', 30, 32000000, 0.15, 0, 'Titan tự nhiên, 256GB', 'DM02', 2, 1),
('SP03', 'Chuột Logitech G502', 100, 1500000, 0.4, 0.1, 'Chuột gaming cao cấp', 'DM04', 3, 1),
('SP04', 'RAM Corsair 16GB', 50, 1200000, 0.3, 0, 'Bus 3200MHz DDR4', 'DM03', 3, 1);

-- 6. Thêm đơn hàng thiết bị
INSERT INTO DON_HANG (ma_donhang, trang_thai, thoi_gian_dat, thoi_gian_hoan_thanh, phuong_thuc_thanh_toan, ma_kh, ma_nhan_vien) VALUES 
('DH01', 'Đã hoàn thành', '2026-04-27 14:00:00', '2026-04-27 14:30:00', 'Tiền mặt', 'KH01', 'NV02'),
('DH02', 'Đang xử lý', '2026-04-27 15:00:00', NULL, 'Chuyển khoản', 'KH02', 'NV02');

-- 7. Chi tiết đơn hàng công nghệ
INSERT INTO CT_DON_HANG (ma_donhang, ma_sp, so_luong, don_gia) VALUES 
('DH01', 'SP01', 1, 45000000),
('DH01', 'SP03', 1, 1500000),
('DH02', 'SP02', 1, 32000000);
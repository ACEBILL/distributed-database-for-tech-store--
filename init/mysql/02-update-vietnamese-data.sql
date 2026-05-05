SET NAMES utf8mb4;
USE quan_ly_chi_nhanh;

UPDATE chi_nhanh SET ten_chi_nhanh = 'Chi nhánh Hà Nội' WHERE ma_chi_nhanh = 'CN01';
UPDATE chi_nhanh SET ten_chi_nhanh = 'Chi nhánh TP.HCM' WHERE ma_chi_nhanh = 'CN02';

UPDATE loai_sp SET ten_loai_sp = 'Điện thoại' WHERE ma_loai_sp = 'LSP02';
UPDATE loai_sp SET ten_loai_sp = 'Phụ kiện' WHERE ma_loai_sp = 'LSP03';
UPDATE loai_sp SET ten_loai_sp = 'Màn hình' WHERE ma_loai_sp = 'LSP04';
UPDATE loai_sp SET ten_loai_sp = 'Linh kiện PC' WHERE ma_loai_sp = 'LSP05';
UPDATE loai_sp SET ten_loai_sp = 'Thiết bị mạng' WHERE ma_loai_sp = 'LSP06';
UPDATE loai_sp SET ten_loai_sp = 'Máy tính bảng' WHERE ma_loai_sp = 'LSP07';
UPDATE loai_sp SET ten_loai_sp = 'Thiết bị âm thanh' WHERE ma_loai_sp = 'LSP08';
UPDATE loai_sp SET ten_loai_sp = 'Camera và Webcam' WHERE ma_loai_sp = 'LSP09';
UPDATE loai_sp SET ten_loai_sp = 'Thiết bị đeo' WHERE ma_loai_sp = 'LSP10';

UPDATE NCC SET ten_NCC = 'Apple Việt Nam' WHERE ma_NCC = 1;
UPDATE NCC SET ten_NCC = 'Samsung Việt Nam' WHERE ma_NCC = 2;
UPDATE NCC SET ten_NCC = 'TP-Link Việt Nam' WHERE ma_NCC = 8;

UPDATE SAN_PHAM SET mo_ta = 'Laptop cao cấp, màn 15.6 inch OLED' WHERE ma_sp = 'SP001';
UPDATE SAN_PHAM SET mo_ta = 'Laptop văn phòng, i5 thế hệ 13' WHERE ma_sp = 'SP003';
UPDATE SAN_PHAM SET mo_ta = 'Tai nghe không dây chống ồn' WHERE ma_sp = 'SP006';
UPDATE SAN_PHAM SET ten_sp = 'Chuột Logitech MX Master 3S', mo_ta = 'Chuột không dây cao cấp' WHERE ma_sp = 'SP007';
UPDATE SAN_PHAM SET ten_sp = 'Màn hình LG 27 inch 4K' WHERE ma_sp = 'SP008';
UPDATE SAN_PHAM SET mo_ta = 'NVMe Gen4, đọc 7450MB/s' WHERE ma_sp = 'SP009';

UPDATE phong_ban SET ten_pb = 'Ban Giám đốc' WHERE ma_pb = 1;
UPDATE phong_ban SET ten_pb = 'Phòng Kinh doanh' WHERE ma_pb = 2;
UPDATE phong_ban SET ten_pb = 'Phòng Kỹ thuật' WHERE ma_pb = 3;
UPDATE phong_ban SET ten_pb = 'Phòng Kho vận' WHERE ma_pb = 4;
UPDATE phong_ban SET ten_pb = 'Phòng Nhân sự' WHERE ma_pb = 5;
UPDATE phong_ban SET ten_pb = 'Phòng Kế toán' WHERE ma_pb = 6;

UPDATE NHAN_VIEN SET ho_ten = 'Nguyễn Văn Hùng' WHERE ma_nhan_vien = 'NV001';
UPDATE NHAN_VIEN SET ho_ten = 'Trần Thị Mai' WHERE ma_nhan_vien = 'NV002';
UPDATE NHAN_VIEN SET ho_ten = 'Lê Hoàng Nam' WHERE ma_nhan_vien = 'NV003';
UPDATE NHAN_VIEN SET ho_ten = 'Phạm Thị Hương' WHERE ma_nhan_vien = 'NV004';
UPDATE NHAN_VIEN SET ho_ten = 'Hoàng Đức Anh' WHERE ma_nhan_vien = 'NV005';

from sqlalchemy.orm import Session
from api.models.donhang import DonHang
from api.models.khachhang import KhachHang
from api.schemas.donhang_schemas import TaoDonHangRequest


class DonHangService:

    @staticmethod
    def get_all(db: Session):
        return db.query(DonHang).all()

    @staticmethod
    def get_by_id(db: Session, ma_donhang):
        return db.query(DonHang).filter(DonHang.ma_donhang == ma_donhang).first()

    @staticmethod
    def create_donhang(db: Session, donhang: TaoDonHangRequest):
        khach_hang = db.query(KhachHang).filter(
            KhachHang.sdt == donhang.sdt_khachhang,
            KhachHang.ten_kh == donhang.ten_khachhang
        ).first()

        if not khach_hang:
            khach_hang = KhachHang(
                ma_kh=donhang.ma_kh,
                ten_kh=donhang.ten_kh,
                sdt=donhang.sdt
            )
            db.add(khach_hang)
            db.flush() # Chưa commit nhưng đã thay đổi trong db session.

        new_donhang = DonHang(
            ma_donhang=donhang.ma_donhang,
            trang_thai=donhang.trang_thai,
            thoi_gian_dat=donhang.thoi_gian_dat,
            thoi_gian_hoan_thanh=donhang.thoi_gian_hoan_thanh,
            phuong_thuc_thanh_toan=donhang.phuong_thuc_thanh_toan,
            ma_kh=khach_hang.ma_kh,
            ma_nhan_vien=donhang.ma_nhan_vien
        )
        db.add(new_donhang)
        db.commit()
        db.refresh(new_donhang)
        return new_donhang
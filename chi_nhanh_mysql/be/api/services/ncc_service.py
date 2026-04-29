from sqlalchemy.orm import Session
from api.models.ncc import NCC
from api.schemas.ncc_schemas import NCCCreate, NCCUpdate

class NCCService:

    @staticmethod
    def get_all(db: Session):
        return db.query(NCC).all()
    
    @staticmethod # Hàm static
    def get_by_id(db: Session, ma_ncc):
        return db.query(NCC).filter(NCC.ma_ncc == ma_ncc).first() # Them 
    

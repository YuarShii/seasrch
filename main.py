from typing import List, Optional
from enum import IntEnum
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, text
from database import get_session
from models import SanPhamResponse

app = FastAPI()

# ====================== CẤU HÌNH CORS (BẮT BUỘC CHO FRONTEND) ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi nguồn (Frontend) gọi vào
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== ĐỊNH NGHĨA ENUM ======================
class SortOrder(IntEnum):
    MOI_NHAT = 0
    GIA_TANG_DAN = 1
    GIA_GIAM_DAN = 2
    DANH_GIA_CAO = 3

class StarRating(IntEnum):
    BA_SAO = 3
    BON_SAO = 4
    NAM_SAO = 5

# ====================== API ENDPOINTS ======================

@app.get("/")
def home():
    return {"message": "Backend Shop Demo đang chạy ngon lành!"}

# 1. API Lấy danh sách Danh mục (Cho Dropdown/Checkbox)
@app.get("/api/danh-muc") # URL khớp với Frontend
def lay_danh_sach_danh_muc(session: Session = Depends(get_session)):
    try:
        # Lấy danh sách tên danh mục, sắp xếp A-Z
        statement = text("SELECT DISTINCT tenDanhMuc FROM DANHMUC ORDER BY tenDanhMuc ASC")
        result = session.execute(statement)
        
        # Chuyển kết quả Tuple thành List String
        categories = [row[0] for row in result.fetchall()]
        return {"data": categories}
        
    except Exception as e:
        print(f"Lỗi lấy danh mục: {e}") # In lỗi ra terminal để debug
        raise HTTPException(status_code=500, detail="Lỗi không lấy được danh mục")

# API Tìm kiếm - Phiên bản "Hardcore" (Chắc chắn lấy được dữ liệu)
@app.get("/api/san-pham/tim-kiem", response_model=List[SanPhamResponse])
def tim_kiem_san_pham(
    tu_khoa: Optional[str] = None,
    gia_min: Optional[float] = Query(None, ge=0),
    gia_max: Optional[float] = Query(None, ge=0),
    danh_muc: Optional[str] = None,
    sao_toi_thieu: Optional[StarRating] = None,
    sap_xep: SortOrder = SortOrder.MOI_NHAT,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session)
):
    try:
        # 1. Xử lý tham số
        if danh_muc == "null" or danh_muc == "": danh_muc = None
        sao_val = sao_toi_thieu.value if sao_toi_thieu else None
        
        # 2. Dùng Cursor THÔ (Raw Cursor) của Driver
        # Đây là cách duy nhất để bypass mọi lỗi của ORM khi gọi Procedure
        raw_connection = session.connection().connection
        cursor = raw_connection.cursor(dictionary=True) # dictionary=True để lấy về JSON

        # 3. Gọi thủ tục
        args = [
            tu_khoa, gia_min, gia_max, danh_muc, sao_val, 
            sap_xep.value, page, page_size
        ]
        cursor.callproc('sp_TimKiemSanPhamNangCao', args)

        # 4. QUAN TRỌNG: Lặp qua stored_results để lấy bảng dữ liệu
        san_phams = []
        for result in cursor.stored_results():
            rows = result.fetchall()
            if rows:
                san_phams = rows
                # Debug: In ra xem lấy được bao nhiêu dòng
                print(f"--> [DEBUG] Đã lấy được: {len(rows)} sản phẩm") 
                break 
        
        cursor.close()
        
        # Nếu vẫn rỗng, thử in ra thông báo để check
        if not san_phams:
            print("--> [DEBUG] Procedure trả về danh sách rỗng!")

        return san_phams

    except Exception as e:
        print(f"--> [LỖI PYTHON]: {e}")
        return []
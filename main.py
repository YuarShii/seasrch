from typing import List, Optional
from enum import IntEnum
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, text
from database import get_session
from models import SanPhamResponse
import csv
import io
from fastapi.responses import StreamingResponse
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
    
@app.get("/api/products/export")
def export_products_csv(
    # Nhận tham số lọc từ URL (giống hệt API tìm kiếm)
    keyword: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    category: str = Query(None),
    min_rating: float = Query(None),
    sort_by: int = Query(0),
    session: Session = Depends(get_session)
):
    cursor = None
    try:
        # 1. LẤY RAW CONNECTION TỪ SESSION (Theo cách của bạn)
        # Ép kiểu .connection (lần 2) để lấy cái lõi mysql-connector ra
        raw_connection = session.connection().connection
        
        # 2. TẠO CURSOR
        # LƯU Ý: Để dictionary=False (mặc định) để nó trả về Tuple
        # Tuple viết vào CSV dễ hơn Dictionary
        cursor = raw_connection.cursor(dictionary=False)

        # 2. GỌI PROCEDURE
        # Lấy số lượng cực lớn (100,000 dòng) để đảm bảo lấy hết dữ liệu
        args = [keyword, min_price, max_price, category, min_rating, sort_by, 1, 100000]
        cursor.callproc('sp_TimKiemSanPhamNangCao', args)

        # Lấy dữ liệu trả về
        stored_results = [r.fetchall() for r in cursor.stored_results()]
        rows = stored_results[0] if stored_results else []

        # 3. VIẾT RA FILE CSV (Trong bộ nhớ RAM)
        stream = io.StringIO()
        csv_writer = csv.writer(stream)

        # Ghi tiêu đề cột (Header)
        headers = ['Mã SP', 'Tên Sản Phẩm', 'Giá Bán', 'Số Lượng', 'Giảm Giá', 'Danh Mục', 'Cửa Hàng', 'Điểm TB', 'Số Đánh Giá']
        csv_writer.writerow(headers)

        # Ghi dữ liệu
        csv_writer.writerows(rows)

        # 4. TRẢ VỀ FILE CHO NGƯỜI DÙNG TẢI
        # Thêm BOM (u'\ufeff') để Excel hiển thị tiếng Việt không bị lỗi font
        response_content = io.BytesIO((u'\ufeff' + stream.getvalue()).encode('utf-8'))

        return StreamingResponse(
            response_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=danh_sach_san_pham.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    except Exception as e:
        print(f"Lỗi xuất CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Luôn đóng kết nối dù có lỗi hay không
        if 'cursor' in locals() and cursor: cursor.close()

@app.get("/analytics/revenue")
def thong_ke_doanh_thu_frontend(
    month: int = Query(..., ge=1, le=12, description="Tháng cần thống kê"),
    year: int = Query(..., ge=2000, le=2100, description="Năm cần thống kê"),
    store_id: int = Query(1, description="Mã cửa hàng (default = 1)"),
    session: Session = Depends(get_session)
):
    try:
        raw_conn = session.connection().connection
        cursor = raw_conn.cursor(dictionary=True)

        # Gọi đúng stored procedure cũ
        cursor.callproc("sp_ThongKeDoanhThuTheoDanhMuc", [store_id, month, year])

        rows = []
        for result in cursor.stored_results():
            rows = result.fetchall() or []
            break

        cursor.close()

        # Chuyển dữ liệu sang format mà Chart.js cần
        labels = [item["tenDanhMuc"] for item in rows]
        values = [float(item["TongDoanhThu"] or 0) / 1_000_000 for item in rows]
 
        # chia 1 triệu để ra đơn vị "triệu VNĐ"

        return {
            "labels": labels,
            "values": values,
        }

    except Exception as e:
        print(f"[LỖI] /analytics/revenue: {e}")
        raise HTTPException(status_code=500, detail="Không thể lấy dữ liệu thống kê doanh thu")
    
@app.get("/orders/{order_id}")
def check_order_status(
    order_id: int,
    session: Session = Depends(get_session)
):
    try:
        raw_conn = session.connection().connection
        cursor = raw_conn.cursor(dictionary=True)

        # 1. Gọi function để lấy tổng tiền cuối (logic trạng thái nằm trong function)
        cursor.execute("SELECT f_TinhTongTienSauGiam(%s) AS final_total", (order_id,))
        final_row = cursor.fetchone()

        if not final_row:
            cursor.close()
            return {
                "success": False,
                "status": "Không tìm thấy đơn hàng",
                "subtotal": 0,
                "discount": 0,
                "final": 0
            }

        final_total = float(final_row["final_total"] or 0)

        # 2. SUCCESS = true nếu function trả > 0 (đúng logic function)
        success = (final_total > 0)

        # 3. Lấy trạng thái gốc từ bảng
        cursor.execute("""
            SELECT trangThaiDonHang 
            FROM DONHANG 
            WHERE maDonHang = %s
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            return {
                "success": False,
                "status": "Không tìm thấy đơn hàng",
                "subtotal": 0,
                "discount": 0,
                "final": 0
            }

        raw_status = order["trangThaiDonHang"]

        # 4. Tính subtotal
        cursor.execute("""
            SELECT SUM(soLuongMua * giaLucMua) AS subtotal
            FROM CHI_TIET_DONHANG
            WHERE maDonHang = %s
        """, (order_id,))
        subtotal_row = cursor.fetchone()
        subtotal = float(subtotal_row["subtotal"]) if subtotal_row else 0

        # 5. Tính tổng giảm giá
        cursor.execute("""
            SELECT COALESCE(SUM(soTienGiamThucTe), 0) AS discount
            FROM AP_DUNG_KHUYENMAI
            WHERE maDonHang = %s
        """, (order_id,))
        discount_row = cursor.fetchone()
        discount = float(discount_row["discount"] ) if discount_row else 0

        cursor.close()

        # 6. Hiển thị cho front-end
        status_text = "Đã Giao Hàng" if success else "Đơn chưa giao"

        return {
            "success": success,
            "status": status_text,
            "subtotal": subtotal,
            "discount": discount,
            "final": final_total
        }

    except Exception as e:
        print(f"[Lỗi] /orders/{order_id}: {e}")
        raise HTTPException(status_code=500, detail="Không thể kiểm tra đơn hàng")

@app.get("/shippers")
def get_all_shippers(session: Session = Depends(get_session)):
    query = text("""
        SELECT 
            s.maShipper AS id,
            nd.hoTen AS name,
            f_TinhDiemTBShipper(s.maShipper) AS score
        FROM SHIPPER s
        JOIN NGUOIDUNG nd ON s.maShipper = nd.maNguoiDung;
    """)
    
    rows = session.execute(query).fetchall()

    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "name": r.name,
            "score": float(r.score or 0)
        })

    return result

# API mới: Lấy danh sách cửa hàng để đổ vào Dropdown
@app.get("/stores")
def get_list_stores(session: Session = Depends(get_session)):
    try:
        raw_conn = session.connection().connection
        cursor = raw_conn.cursor(dictionary=True)
        
        # Lấy ID và Tên cửa hàng từ bảng CUAHANG
        cursor.execute("SELECT maCuaHang, tenCuaHang FROM CUAHANG")
        rows = cursor.fetchall()
        cursor.close()
        
        # Trả về danh sách dạng JSON
        return rows 
    except Exception as e:
        print(f"Error: {e}")
        return []
from sqlmodel import SQLModel

# Model hứng kết quả từ thủ tục sp_TimKiemSanPhamNangCao
class SanPhamResponse(SQLModel):
    maSanPham: int
    tenSanPham: str
    giaBan: float
    soLuongCon: int
    tenDanhMuc: str
    tenCuaHang: str
    phanTramGiamGia: float
    diemDanhGiaTB: float 
    soLuotDanhGia: int    
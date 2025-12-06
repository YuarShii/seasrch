# 🚀 Hướng Dẫn Cài Đặt Dự Án

**Trước khi chạy dự án, hãy đảm bảo máy của bạn đã cài đặt:**

1.  **Python** (phiên bản 3.8 trở lên)\
2.  **XAMPP** hoặc **MySQL Server** (đã bật module **MySQL**)\
    \> _Lưu ý:_ Database mặc định là **testdbbk**. Nếu bạn dùng tên khác, hãy chỉnh lại trong file `database.py`.

---

## 📥 Installation

### **Bước 1: Tải dự án**

Clone dự án hoặc tải file zip và mở bằng VS Code.

### **Bước 2: Mở Terminal**

Vào **Terminal → New Terminal**, và đảm bảo thư mục hiện tại là thư mục
dự án.

### **Bước 3: Tạo môi trường ảo**

python -m venv venv

### **Bước 4: Kích hoạt môi trường ảo và cài thư viện**

Kích hoạt môi trường ảo (nếu chưa thấy `(venv)`):

.venv\Scripts\activate

Cài thư viện:

pip install -r requirements.txt

### **Bước 5: Chạy server Backend**

uvicorn main:app --reload

---

## 🎨 Chạy Frontend

1.  Cài extension **Live Server** trong VS Code\
2.  Mở file giao diện HTML và nhấn **Go Live** ở góc phải dưới

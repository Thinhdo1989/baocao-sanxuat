# Ứng Dụng Báo Cáo Sản Xuất Tự Động - Nhà Máy Viên Nén Gỗ

Hệ thống theo dõi, tính toán chỉ số sản xuất (KPI), suất tiêu hao điện năng, năng suất thiết bị và hiển thị Dashboard tự động kết nối trực tiếp từ Google Sheets.

---

## 📁 Cấu Trúc Dữ Liệu Kết Nối

Hệ thống kết nối tự động tới **2 bảng tính Google Sheets**:
1. **Bảng Báo Cáo Sản Xuất & Thiết Bị:**
   - Spreadsheet ID: `1HH1r7O_eL_iW6spNruAKCM947G79rCyJRFHRVVb9apU` (2026 BVN QB Nhật kí sản xuất)
   - Chức năng: Thống kê chi tiết từng ca, giờ máy chạy 16 thiết bị (Nghiền búa Andritz/SHT, Trống sấy, 8 máy ép PE), độ ẩm, độ tro, dầu diezen.
2. **Bảng Đánh Giá & Thi Đua KPI Ca Trưởng:**
   - Spreadsheet ID: `1M75tg_kZNxItv3VOlAjNi-RF63S_2NtxBMXSAxCRe14` (2026 Nhat ky KPI)
   - Chức năng: Bảng vinh danh 🥇🥈🥉, xếp hạng điểm KPI tuần/tháng (thang 100 điểm), phân tích 4 trọng số: Sản lượng (/40đ), Độ ẩm (/22đ), Tiết kiệm điện (/20đ), Năng suất (/18đ).


---

## ⚙️ Thiết Lập Môi Trường & Cài Đặt

### 1. Kích hoạt môi trường ảo (Virtual Environment)
Nếu chưa kích hoạt môi trường ảo, bạn có thể kích hoạt bằng lệnh:
```powershell
# Trên Windows PowerShell
.\.venv\Scripts\activate
```

### 2. Cài đặt các thư viện (đã được cài đặt sẵn vào `.venv`)
```bash
pip install -r requirements.txt
```

---

## 🚀 Hướng Dẫn Chạy Ứng Dụng

### Bước 1: Kiểm tra kết nối Google Sheets đầu tiên
Chạy script kiểm tra để xác nhận Service Account kết nối thành công và đọc được số liệu ngày mới nhất:
```bash
python test_connection.py
```
*Kết quả sẽ hiển thị chi tiết: sản lượng thực tế, giờ chạy các máy nghiền/sấy/ép, suất điện năng (kWh/tấn) kèm đánh giá cảnh báo, năng suất ép (tấn/h).*

### Bước 2: Khởi chạy giao diện Dashboard trực quan
Chạy lệnh sau trên terminal:
```bash
streamlit run app.py
```
Hệ thống sẽ tự động mở trình duyệt tại địa chỉ: `http://localhost:8501`.

---

## 📊 Các Nghiệp Vụ & Chỉ Số Đo Lường Chính (KPI)

1. **Sản lượng thực tế (Tấn):**
   - Theo dõi theo từng ca (Ca Sắc, Ca Long, Ca Tài, Ca Thành, Ca Lâm...), theo ngày, tuần, tháng.
2. **Suất tiêu hao điện năng (kWh/tấn):**
   - **Định mức chuẩn:** `170.0 - 175.0 kWh/tấn`.
   - **Cảnh báo vượt mức:** Tô màu đỏ và gửi cảnh báo khi `> 175.0 kWh/tấn`.
   - **Hiệu quả cao:** Gắn nhãn xanh khi `< 170.0 kWh/tấn`.
3. **Năng suất ép trung bình (tấn/h):**
   - **Chỉ tiêu:** `≥ 4.0 tấn/h`.
   - Cảnh báo vàng/cam khi `< 4.0 tấn/h`.
4. **Giờ hoạt động cụm thiết bị:**
   - **Máy nghiền búa thô:** Andritz HM118, HM218; SHT HM318.
   - **Trống sấy:** DR124, DR224.
   - **Máy nghiền búa tinh:** SHT HM147; Andritz HM247, HM347.
   - **Cụm 8 máy ép viên:** PE1 đến PE8.
5. **Chỉ tiêu chất lượng (KCS) & Nhiên liệu:**
   - Độ ẩm viên nén (chuẩn: 8.0 - 9.5%).
   - Độ tro viên nén (chuẩn: ≤ 1.5%).
   - Tỷ lệ chế biến nguyên liệu (tấn nguyên liệu / tấn thành phẩm).
   - Dầu Diezen tiêu thụ theo xe/thiết bị (xe xúc SEM, máy đào DX, Toyota, xe ben, máy phát điện).

# NHẬT KÝ & LỊCH SỬ LÀM VIỆC DỰ ÁN
## HỆ THỐNG BÁO CÁO SẢN XUẤT TỰ ĐỘNG - NHÀ MÁY VIÊN NÉN GỖ
*(Dự án hợp tác phát triển cùng AI Coding Assistant trên Antigravity IDE)*

---

### 📌 THÔNG TIN TỔNG QUAN
- **Dự án:** Ứng dụng Báo cáo Sản xuất, Giám sát Thiết bị & Đánh giá KPI Thi đua Ca
- **Đơn vị vận hành:** Nhà máy Viên Nén Gỗ (BVN Quảng Bình)
- **Công nghệ nền tảng:** Python 3.11, Streamlit, Pandas, Plotly, Google Sheets API (gspread), UV package manager, Git/GitHub.
- **Kho mã nguồn GitHub:** `https://github.com/Thinhdo1989/baocao-sanxuat.git`
- **Địa chỉ ứng dụng Web:** `https://baocao-sanxua-pr32vanq35zuxh6zngmmly.streamlit.app/`
- **Thời gian triển khai:** Từ **11/09/2026** đến hiện tại (**Tháng 10/2026**).

---

## 🕒 I. TIẾN TRÌNH LỊCH SỬ LÀM VIỆC & CÁC CỘT MỐC PHÁT TRIỂN

### Giai đoạn 1: Khởi tạo dự án & Kết nối Google Sheets (11/09/2026 - 14/09/2026)
- **Yêu cầu ban đầu:** Xây dựng hệ thống tự động hóa thay thế việc xem báo cáo thủ công trên bảng tính Excel/Google Sheets.
- **Thực hiện:**
  - Thiết lập kiến trúc dự án với Streamlit và cấu trúc thư mục chuẩn.
  - Tích hợp xác thực Google Cloud Service Account qua file `credentials.json` và phân quyền truy cập Google Sheets.
  - Xây dựng mô-đun kết nối dữ liệu `data_loader.py` kết nối trực tiếp đến Spreadsheet *2026 BVN QB Nhật kí sản xuất* (ID: `1HH1r7O_eL_iW6spNruAKCM947G79rCyJRFHRVVb9apU`).
  - Viết script `test_connection.py` kiểm tra tự động kết nối và trích xuất dữ liệu ngày gần nhất.

---

### Giai đoạn 2: Theo dõi Suất tiêu hao điện năng & Giờ máy chạy (15/09/2026 - 19/09/2026)
- **Nghiệp vụ kỹ thuật:**
  - Tính toán suất tiêu hao điện năng tiêu chuẩn: `170.0 - 175.0 kWh/tấn`.
  - Thiết lập hệ thống cảnh báo màu trực quan:
    - 🟢 Màu xanh: Dưới 170 kWh/tấn (Vận hành tối ưu).
    - 🟡 Màu vàng: 170 - 175 kWh/tấn (Đạt định mức).
    - 🔴 Màu đỏ: Trên 175 kWh/tấn (Vượt định mức - cảnh báo kiểm tra).
  - Quản lý giờ chạy chi tiết của 16 cụm thiết bị trọng yếu:
    - Cụm nghiền thô: Andritz HM118, HM218; SHT HM318.
    - Cụm sấy: Trống sấy DR124, DR224.
    - Cụm nghiền tinh: SHT HM147; Andritz HM247, HM347.
    - Cụm ép viên: 8 máy ép PE1 đến PE8.
  - Phân tích năng suất ép trung bình: Chuẩn $\ge 4.0$ tấn/h.

---

### Giai đoạn 3: Xây dựng Hệ thống Thi đua & Chấm điểm KPI Ca Trưởng (20/09/2026 - 25/09/2026)
- **Thực hiện:**
  - Kết nối bảng tính thi đua KPI ca trưởng (Spreadsheet ID: `1M75tg_kZNxItv3VOlAjNi-RF63S_2NtxBMXSAxCRe14`).
  - Xây dựng mô-đun `kpi_calculator.py` tính điểm theo thang 100 điểm với 4 nhóm chỉ số:
    1. Sản lượng đạt kế hoạch (Trọng số 40 điểm).
    2. Độ ẩm viên nén thành phẩm 8.0 - 9.5% (Trọng số 22 điểm).
    3. Tiết kiệm điện năng $\le 175$ kWh/tấn (Trọng số 20 điểm).
    4. Năng suất ép $\ge 4.0$ tấn/h (Trọng số 18 điểm).
  - Thiết kế bảng vinh danh với huy chương 🥇 Vàng, 🥈 Bạc, 🥉 Đồng và bảng xếp hạng ca trưởng theo Tuần/Tháng.
  - Chuẩn hóa tên ca trưởng và nhân sự vận hành: Ca A (Lê Chiến Sắc), Ca B, Ca C...

---

### Giai đoạn 4: Chu kỳ Bảo trì, Thay dầu Máy ép & Nhập liệu KCS (26/09/2026 - 28/09/2026)
- **Thực hiện:**
  - Tính toán lũy kế giờ chạy máy ép PE sau mốc bảo trì 18/09/2026 để cảnh báo chu kỳ thay dầu lần 2.
  - Bổ sung ánh xạ mã máy `PE_510`.
  - Tích hợp giao diện sơ đồ công nghệ nhà máy và sơ đồ tổ chức nhân sự (`process_and_org_chart.py`).
  - Nâng cấp bộ lọc đa từ khóa, tìm kiếm linh hoạt mã bảo trì không gạch nối (ví dụ: `BT1892`, `SC2210`).
  - Xử lý tương thích định dạng số giữa chuẩn Việt Nam (dấu phẩy thập phân `,`) và chuẩn quốc tế (`clean_numeric`).

---

### Giai đoạn 5: Đưa lên Streamlit Cloud & Tự động hóa Vận hành (29/09/2026 - 01/10/2026)
- **Thực hiện:**
  - Tạo cơ chế tự động đồng bộ mã nguồn lên GitHub và Streamlit Cloud qua [Cap_Nhat_Len_Web.bat](file:///e:/1.Antigravity/1.Báo%20cáo%20sản%20xuất/Cap_Nhat_Len_Web.bat).
  - Viết file `secrets_for_streamlit_cloud.txt` hướng dẫn cấu hình bảo mật trên đám mây.
  - Xử lý các lỗi ngoại lệ khi tải lại mô-đun động trên Cloud.
  - Tối ưu hóa file [Khoi_Dong_Bao_Cao.bat](file:///e:/1.Antigravity/1.Báo%20cáo%20sản%20xuất/Khoi_Dong_Bao_Cao.bat) và [Chay_Ung_Dung.bat](file:///e:/1.Antigravity/1.Báo%20cáo%20sản%20xuất/Chay_Ung_Dung.bat) để người vận hành chỉ cần 1 nhấp đúp là khởi chạy mạng nội bộ cho điện thoại/máy tính bảng (`http://192.168.1.7:8501`).

---

### Giai đoạn 6: Đóng gói An toàn & Tự Phục hồi khi Thay Ổ Đĩa (02/10/2026)
- **Yêu cầu:** Đóng gói toàn bộ dự án để thay ổ đĩa mới, bảo đảm khi mở Antigravity vẫn hoạt động hoàn hảo.
- **Thực hiện:**
  - Viết công cụ đóng gói tự động `dong_goi_du_lieu.py` và [DONG_GOI_SAO_LUU.bat](file:///e:/1.Antigravity/DONG_GOI_SAO_LUU.bat).
  - Nén file an toàn `Sao_Luu_Antigravity_Day_Du.zip` (15.2 MB) và lưu đồng bộ sang Desktop, ổ D, ổ E.
  - Tích hợp cơ chế **tự phục hồi môi trường ảo (Self-healing)** vào [Khoi_Dong_Bao_Cao.bat](file:///e:/1.Antigravity/1.Báo%20cáo%20sản%20xuất/Khoi_Dong_Bao_Cao.bat).
  - Tạo file [Khoi_Phuc_Moi_Truong.bat](file:///e:/1.Antigravity/1.Báo%20cáo%20sản%20xuất/Khoi_Phuc_Moi_Truong.bat) dùng công cụ UV tốc độ cao để dựng lại môi trường trong 5-10 giây bất cứ khi nào đổi ổ đĩa.
  - **Mở khóa toàn diện Lịch Tháng 10 & Năm 2026:** Gỡ bỏ giới hạn chặn trên, cho phép chọn và xem mọi ngày trong tháng 10 và cả năm 2026.
  - **Chuẩn hóa hiển thị Ngày Không Sản Xuất / Bảo trì (01/10/2026):** Loại bỏ cơ chế lấy số liệu quá khứ hoặc gán mặc định. Khi ngày có sản lượng = 0 (như ca bảo trì BT_VS), các thẻ Độ ẩm, Tỷ trọng, Tỷ lệ chế biến, Dầu diezen hiển thị rõ `--` và nhãn `⚪ Không sản xuất`.
  - **Nâng cấp Dashboard Online Thời Gian Thực (Hôm nay 02/10/2026):** Chuyển Vị trí 1 sang chế độ Live Online: hiển thị trực tiếp ca sản xuất vừa nhập chiều nay (Ca B: 78.6 tấn, 20 giờ máy ép, tồn kho 13,795.8 tấn).
  - **Đóng gói toàn diện phiên bản hoàn chỉnh:** Cập nhật lại gói sao lưu đầy đủ sang Desktop, D:\, E:\ sẵn sàng cho việc thay ổ đĩa mới.

---

## 📁 II. DANH MỤC CẤU TRÚC TỆP TIN DỰ ÁN

| Tên Tệp / Thư Mục | Phân Loại | Chức Năng Chính |
| :--- | :--- | :--- |
| `app.py` | Mã nguồn chính | Giao diện Dashboard chính (KPI, Biểu đồ sản xuất, Giờ máy, KCS, Bảo trì) |
| `data_loader.py` | Mô-đun dữ liệu | Kết nối Google Sheets, xử lý làm sạch dữ liệu, tính toán định mức |
| `kpi_calculator.py` | Mô-đun nghiệp vụ | Thuật toán chấm điểm thi đua ca, bảng vinh danh và xếp hạng |
| `data_entry.py` | Giao diện nhập liệu | Form nhập nhật ký sản xuất, số liệu ca, KCS |
| `process_and_org_chart.py`| Trực quan hóa | Sơ đồ quy trình sản xuất và sơ đồ tổ chức nhà máy |
| `i18n.py` | Đa ngôn ngữ | Từ điển song ngữ Việt - Anh cho toàn bộ giao diện |
| `logo_data.py` | Giao diện đồ họa | Dữ liệu logo nhà máy dạng Base64 |
| `schematic_diagram.py` | Đồ họa kỹ thuật | Sơ đồ dây chuyền thiết bị nhà máy |
| `test_connection.py` | Kiểm thử | Script kiểm tra kết nối Google Sheets nhanh |
| `credentials.json` | Bảo mật | Khóa Service Account truy cập Google Sheets |
| `Khoi_Dong_Bao_Cao.bat`| Vận hành | Khởi động Streamlit nội bộ, tự phát hiện & sửa lỗi môi trường |
| `Chay_Ung_Dung.bat` | Lối tắt | File nhấp đúp nhanh ngoài màn hình |
| `Khoi_Phuc_Moi_Truong.bat`| Tiện ích | Tự tạo lại `.venv` và cài thư viện bằng UV trong 5 giây |
| `Cap_Nhat_Len_Web.bat` | Vận hành | Đẩy code mới lên GitHub và Streamlit Cloud |
| `DONG_GOI_SAO_LUU.bat` | Sao lưu | Đóng gói toàn bộ dự án thành file zip chỉ với 1 click |
| `requirements.txt` | Cấu hình thư viện | Danh sách các thư viện Python cần thiết |

---

## 🔒 III. CÁCH LƯU TRỮ VÀ XEM LẠI LỊCH SỬ HỘI THOẠI TRONG ANTIGRAVITY

1. **Cơ chế lưu tự động của Antigravity IDE:**
   - Mọi câu hỏi, trao đổi, dòng mã và kết quả trao đổi đều được Antigravity tự động ghi nhận vào cơ sở dữ liệu SQLite tại:
     `C:\Users\HP-PC\.gemini\antigravity\conversations\`
   - Hiện đã có hơn 30 phiên hội thoại từ ngày bắt đầu dự án đến nay được bảo vệ an toàn.

2. **Cách mở lại lịch sử trực tiếp trên Antigravity:**
   - Tại thanh công cụ bên trái của Antigravity, bấm vào mục **Chat History** (hoặc biểu tượng đồng hồ / danh sách cuộc trò chuyện).
   - Chọn bất kỳ phiên trò chuyện nào theo ngày giờ để xem lại từng đoạn hội thoại chi tiết.

3. **Bảo toàn khi thay ổ đĩa:**
   - Thư mục lịch sử trò chuyện nằm tại ổ **C:** (`C:\Users\HP-PC\...`).
   - Do đó khi bạn thay ổ đĩa **E:**, toàn bộ lịch sử hội thoại trên Antigravity **không bị ảnh hưởng và vẫn hiển thị đầy đủ 100%**.

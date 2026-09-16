"""
Mô-đun hiển thị:
Sơ Đồ Nguyên Lý Công Nghệ & Tự Động Hóa Toàn Nhà Máy (P&ID / SCADA Process Flow Schematic)
Trích xuất và phân tích toàn diện từ Bản vẽ kỹ thuật BVN Quảng Bình (PDF & Ultra HD 3168x2448).
"""

import os
import streamlit as st
import pandas as pd
from PIL import Image

def render_factory_schematic_diagram():
    """Hiển thị Sơ đồ nguyên lý công nghệ, P&ID và tự động hóa toàn nhà máy BVN Quảng Bình"""
    st.markdown("""
    <style>
    .schematic-zone-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 16px;
    }
    .schematic-tag {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .tag-plc { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .tag-rtu { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .tag-kw { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .tag-sensor { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    </style>
    """, unsafe_allow_html=True)

    # 1. Tiêu đề mục
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border-left: 6px solid #3b82f6; padding: 16px 22px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.12);">
        <div style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: 0.3px;">
            📐 SƠ ĐỒ NGUYÊN LÝ CÔNG NGHỆ & TỰ ĐỘNG HÓA NHÀ MÁY (P&ID / SCADA SCHEMATIC)
        </div>
        <div style="font-size: 13px; font-weight: 500; color: #94a3b8; margin-top: 4px;">
            Bản vẽ nguyên lý công nghệ dây chuyền sản xuất viên nén sinh khối BVN Quảng Bình (Chi tiết mã thiết bị, công suất động cơ, hệ thống cảm biến & tủ điều khiển PLC/RTU)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Đường dẫn tệp
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_hd_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn_hd.png")
    img_std_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn.png")
    pdf_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn.pdf")

    # 2. Thanh thao tác nhanh (Quick Action Bar)
    col_act1, col_act2, col_act3 = st.columns([4, 4, 4])
    
    with col_act1:
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Tải Bản Vẽ PDF Gốc (Full Vector)",
                data=pdf_bytes,
                file_name="So_Do_Nguyen_Ly_BVN_Quang_Binh.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Tải tệp PDF kỹ thuật chất lượng cao nhất để xem trên phần mềm CAD / Acrobat Reader"
            )
        else:
            st.info("Bản vẽ PDF đang được đồng bộ...")

    with col_act2:
        zoom_mode = st.radio("Độ phân giải hiển thị:", ["Siêu nét Ultra HD (3.168 x 2.448)", "Tiêu chuẩn (1.980 x 1.530)"], horizontal=True, index=0)

    with col_act3:
        st.caption("💡 *Gợi ý: Nhấp chuột phải vào bản vẽ chọn 'Mở hình ảnh trong thẻ mới' để phóng to từng cảm biến và số hiệu động cơ.*")

    # 3. Hiển thị hình ảnh bản vẽ
    display_img_path = img_hd_path if (zoom_mode == "Siêu nét Ultra HD (3.168 x 2.448)" and os.path.exists(img_hd_path)) else img_std_path
    if os.path.exists(display_img_path):
        st.image(
            display_img_path,
            caption="Bản vẽ sơ đồ nguyên lý P&ID & Tự động hóa nhà máy viên nén gỗ BVN Quảng Bình (Bao gồm Line 1 & Line 2, Trống sấy, 4 Máy nghiền, 8 Máy ép Andritz PM30-6)",
            use_container_width=True
        )
    else:
        st.warning("Đang tải dữ liệu hình ảnh bản vẽ kỹ thuật...")

    st.markdown("---")

    # 4. Phân tích chi tiết 6 phân vùng công nghệ (Zone Deep-Dive)
    st.markdown("### 🔍 PHÂN TÍCH CHI TIẾT 6 PHÂN VÙNG CÔNG NGHỆ & TỰ ĐỘNG HÓA")
    
    tab_z1, tab_z2, tab_z3, tab_z4, tab_z5, tab_z6, tab_legend, tab_rev = st.tabs([
        "1️⃣ Băm Dăm & Cấp Liệu (PLC#01)",
        "2️⃣ Nghiền Thô (RTU#05)",
        "3️⃣ Sấy Dăm & Lò Đốt (RTU#02)",
        "4️⃣ Nghiền Tinh & Lọc Bụi (RTU#03)",
        "5️⃣ Ép Viên 8 Máy PM30-6 (RTU#01)",
        "6️⃣ Làm Mát & Đóng Bao (RTU#04)",
        "📖 Bảng Tra Cứu Ký Hiệu P&ID",
        "📝 Lịch Sử Cập Nhật Bản Vẽ"
    ])

    # ----------------- PHÂN VÙNG 1: BĂM DĂM & CẤP LIỆU -----------------
    with tab_z1:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">🚜 KHU VỰC BĂM DĂM & NẠP LIỆU (MÃ KHU VỰC 0 - LINE 1: 1, LINE 2: 2)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-plc">TỦ ĐIỀU KHIỂN: PLC#01</span>
                <span class="schematic-tag tag-kw">CẤP ĐIỆN: 380V / 3 PHA</span>
                <span class="schematic-tag tag-sensor">CẢM BIẾN: AUTONICS PR 18-8DN</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Khu vực tiếp nhận nguyên liệu gỗ cây, cành ngọn từ bãi dăm, nạp vào phễu tiếp liệu qua hệ thống gắp gỗ và xúc lật. 
                Hai dây chuyền băm dăm độc lập (Line 1 và Line 2) hoạt động song song để cấp dăm về bãi chứa dăm thô và cấp dăm đốt cho 2 lò sấy.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z1_l, col_z1_r = st.columns(2)
        with col_z1_l:
            st.markdown("##### ⚙️ Danh mục thiết bị động lực chính:")
            df_z1_eq = pd.DataFrame([
                {"Mã thiết bị": "CM108 - CM1011", "Tên thiết bị": "Cụm máy băm dăm Line 1 (Chipper)", "Công suất": "Động cơ chính 450kW + phụ", "Chức năng": "Băm gỗ cây thành dăm kích thước 20-30mm"},
                {"Mã thiết bị": "CM208 - CM2011", "Tên thiết bị": "Cụm máy băm dăm Line 2 (Chipper)", "Công suất": "Động cơ chính 450kW + phụ", "Chức năng": "Dây chuyền băm dăm phụ trợ Line 2"},
                {"Mã thiết bị": "DC103, DC104, DC106", "Tên thiết bị": "Xích tải nạp dăm Line 1 (Drag Conveyor)", "Công suất": "11 kW / 9.2 kW / 15 kW", "Chức năng": "Tải dăm từ phễu băm về băng tải chính"},
                {"Mã thiết bị": "DC203, DC204, DC206", "Tên thiết bị": "Xích tải nạp dăm Line 2 (Drag Conveyor)", "Công suất": "11 kW / 9.2 kW / 15 kW", "Chức năng": "Tải dăm Line 2"},
                {"Mã thiết bị": "BE107, BE207", "Tên thiết bị": "Băng tải trung chuyển (Belt Conveyor)", "Công suất": "15 kW (có thắng cơ)", "Chức năng": "Chuyển dăm lên kho dăm thô"},
                {"Mã thiết bị": "BE1012, BE1013, BE1014", "Tên thiết bị": "Băng tải phân phối bãi dăm Line 1", "Công suất": "30 kW + 1.5 kW thắng", "Chức năng": "Rải dăm vào các khoang chứa"},
                {"Mã thiết bị": "AL1112, AL2112", "Tên thiết bị": "Cụm nam châm tách sắt vĩnh cửu (Magnet)", "Công suất": "Cơ khí nam châm", "Chức năng": "Hút đinh, vụn sắt trước khi vào máy nghiền"}
            ])
            st.dataframe(df_z1_eq, use_container_width=True, hide_index=True)

        with col_z1_r:
            st.markdown("##### 📡 Hệ thống cảm biến tự động hóa PLC#01:")
            df_z1_sn = pd.DataFrame([
                {"Ký hiệu": "SP103.1, SP103.2", "Loại cảm biến": "Cảm biến tốc độ (Speed Sensor)", "Model": "Autonics PR 18-8DN", "Chức năng": "Giám sát tốc độ quay trục xích tải DC103"},
                {"Ký hiệu": "SP104, SP106, SP107", "Loại cảm biến": "Cảm biến tốc độ trục", "Model": "Autonics PR 18-8DN", "Chức năng": "Báo trượt băng tải / đứt xích cấp liệu"},
                {"Ký hiệu": "OV103, OV104", "Loại cảm biến": "Cảm biến quá tải (Overload)", "Model": "Bảo vệ dòng điện", "Chức năng": "Ngắt khẩn cấp khi kẹt gỗ trong máng cào"},
                {"Ký hiệu": "OT108.1, OT108.2", "Loại cảm biến": "Cảm biến quá nhiệt ổ bi (Over Temp)", "Model": "PT100 / Thermocouple", "Chức năng": "Giám sát nhiệt ổ bi gối đỡ máy băm CM108"},
                {"Ký hiệu": "C113 / O113", "Loại cảm biến": "Công tắc hành trình cửa (Close/Open)", "Model": "Micro-switch", "Chức năng": "Xác nhận vị trí mở/đóng nắp bảo trì an toàn"}
            ])
            st.dataframe(df_z1_sn, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG 2: NGHIỀN THÔ -----------------
    with tab_z2:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">🔨 KHU VỰC NGHIỀN THÔ (HAMMER MILL LINE 1, 2, 3, 4)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-rtu">TỦ ĐIỀU KHIỂN: RTU#05</span>
                <span class="schematic-tag tag-kw">CÔNG SUẤT: 400kW - 450kW / MÁY</span>
                <span class="schematic-tag tag-sensor">BẢO VỆ: RUNG (VB), QUÁ NHIỆT (OT), DỪNG KHẨN (E)</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Khu vực nghiền dăm thô từ kích thước 20-30mm xuống hạt mùn dăm nhỏ < 15mm để chuẩn bị cấp vào lò sấy. 
                Gồm 3 line đang vận hành (HM118 - 400kW Andritz, HM218 - 400kW Andritz, HM318 - 450kW SHT) và 1 line dự phòng tương lai (HM418).
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z2_l, col_z2_r = st.columns(2)
        with col_z2_l:
            st.markdown("##### ⚙️ Cụm 4 Line máy nghiền thô:")
            df_z2_eq = pd.DataFrame([
                {"Line": "Line 1", "Máy nghiền chính": "HM118 (400 kW ANDRITZ)", "Cấp liệu": "Vít tải FD114 (11 kW có thắng) + SC111 (2x5.5kW)", "Quạt hút": "FA1113 (45 kW)", "Van sao xả": "AL1110 (4 kW), AL1111, AL1112"},
                {"Line": "Line 2", "Máy nghiền chính": "HM218 (400 kW ANDRITZ)", "Cấp liệu": "Vít tải FD214 (11 kW có thắng) + SC211 (2x5.5kW)", "Quạt hút": "FA2113 (55 kW)", "Van sao xả": "AL2110 (4 kW), AL2111, AL2112"},
                {"Line": "Line 3", "Máy nghiền chính": "HM318 (450 kW SHT)", "Cấp liệu": "Vít tải FD314 (11 kW có thắng) + SC311 (2x5.5kW)", "Quạt hút": "FA3113 (55 kW)", "Van sao xả": "AL3110 (4 kW), AL3111, AL3112"},
                {"Line": "Line 4 (Dự phòng)", "Máy nghiền chính": "HM418 (450 kW Tương lai)", "Cấp liệu": "Vít tải FD414 (11 kW) + SC411", "Quạt hút": "FA4113", "Van sao xả": "AL4110, AL4111, AL4112"}
            ])
            st.dataframe(df_z2_eq, use_container_width=True, hide_index=True)

        with col_z2_r:
            st.markdown("##### 🛡️ Cảm biến an toàn & Khí nén máy nghiền thô:")
            df_z2_sn = pd.DataFrame([
                {"Mã cảm biến": "VB118, VB218, VB318", "Tên": "Cảm biến báo rung (Vibration Sensor)", "Chức năng": "Phát hiện mất cân bằng rotor, gãy búa nghiền để dừng máy ngay lập tức"},
                {"Mã cảm biến": "OT118-1, OT118-2", "Tên": "Quá nhiệt ổ bi gần / xa motor", "Chức năng": "Bảo vệ gối đỡ vòng bi chính máy nghiền HM118"},
                {"Mã cảm biến": "SP118, SP218, SP318", "Tên": "Cảm biến tốc độ trục chính (Main Shaft)", "Chức năng": "Xác nhận máy nghiền đã đạt đủ tốc độ đồng bộ trước khi cho phép cấp liệu"},
                {"Mã cảm biến": "CW / CCW", "Tên": "Cảm biến chiều quay thuận / ngược", "Chức năng": "Điều khiển đảo chiều quay định kỳ để mòn đều 2 cạnh búa nghiền"},
                {"Mã cảm biến": "DR / DL", "Tên": "Door Switch Right / Left", "Chức năng": "Cảm biến an toàn khóa nắp buồng nghiền, cấm khởi động khi cửa mở"},
                {"Mã cảm biến": "S118-1, S118-2", "Tên": "Solenoid van 5/2 & 3/2", "Chức năng": "Điều khiển cơ cấu lật tấm hướng dòng búa nghiền"}
            ])
            st.dataframe(df_z2_sn, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG 3: SẤY DĂM & LÒ ĐỐT -----------------
    with tab_z3:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">🔥 KHU VỰC SẤY DĂM QUAY & LÒ ĐỐT SINH KHỐI (LINE 1 & LINE 2)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-rtu">TỦ ĐIỀU KHIỂN: RTU#02</span>
                <span class="schematic-tag tag-kw">TRỐNG SẤY: 2 x 315kW (DR124 & DR224)</span>
                <span class="schematic-tag tag-sensor">THỦY LỰC: 3 x 30kW SÀN TRƯỢT (HP137, HP138, HP139)</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Hệ thống sấy gồm 2 lò đốt sinh khối tự động (Burner 1 & 2) sử dụng dăm đốt khô để sinh khí nóng. 
                Hai trống sấy quay DR124 và DR224 bốc hơi ẩm của dăm tươi từ 45-50% xuống 10-12%. Dăm khô sau sấy được chuyển ra sàn trượt thủy lực 6 xy lanh tiếp liệu.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z3_l, col_z3_r = st.columns(2)
        with col_z3_l:
            st.markdown("##### ⚙️ Thiết bị hệ thống sấy & quạt gió:")
            df_z3_eq = pd.DataFrame([
                {"Mã thiết bị": "DR124, DR224", "Tên thiết bị": "Trống sấy quay Line 1 & Line 2 (Drum Dryer)", "Công suất": "315 kW mỗi trống", "Chức năng": "Đảo trộn dăm với khí nóng để bay hơi nước"},
                {"Mã thiết bị": "BURNER 1, BURNER 2", "Tên thiết bị": "Lò đốt nhiên liệu sinh khối", "Cấp liệu": "Vít nạp dăm đốt tự động", "Chức năng": "Cấp nhiệt sấy, kiểm soát nhiệt gió vào 280-350°C"},
                {"Mã thiết bị": "FA127, FA227", "Tên thiết bị": "Quạt hút khí nóng lò sấy (Main Fan)", "Công suất": "30 kW mỗi quạt", "Chức năng": "Tạo áp suất âm hút khí nóng qua thân trống"},
                {"Mã thiết bị": "FA1211, FA2211", "Tên thiết bị": "Quạt hút bụi sấy phụ", "Công suất": "9.2 kW mỗi quạt", "Chức năng": "Hút bụi mịn qua cyclone lắng"},
                {"Mã thiết bị": "DP1212 - DP1217", "Tên thiết bị": "Hệ thống van lật damper điều tiết gió", "Công suất": "Động cơ chấp hành 0.4kW", "Chức năng": "Cân bằng lưu lượng gió nóng và gió hồi"},
                {"Mã thiết bị": "HP137, HP138, HP139", "Tên thiết bị": "3 Trạm bơm thủy lực sàn trượt", "Công suất": "3 x 30 kW", "Chức năng": "Đẩy dăm khô đáy bunke sàn trượt vào xích tải"},
                {"Mã thiết bị": "DC1115", "Tên thiết bị": "Xích tải dăm khô thu hồi sau sấy", "Công suất": "18.5 kW", "Chức năng": "Gom dăm khô cấp sang khu vực nghiền tinh"}
            ])
            st.dataframe(df_z3_eq, use_container_width=True, hide_index=True)

        with col_z3_r:
            st.markdown("##### 📡 Cảm biến nhiệt độ, áp suất & sàn trượt:")
            df_z3_sn = pd.DataFrame([
                {"Ký hiệu": "T121, T122, T123, T124", "Loại cảm biến": "Cảm biến nhiệt độ khí sấy (Temp Sensor)", "Chức năng": "Đo nhiệt độ buồng đốt, nhiệt đầu vào và nhiệt đầu ra trống sấy"},
                {"Ký hiệu": "BV1 / BV2 (CBV / OBV)", "Loại van": "Burner Valve Close / Open", "Chức năng": "Van an toàn ngắt gió nóng khẩn cấp khi nhiệt độ vượt ngưỡng an toàn"},
                {"Ký hiệu": "1U137 - 6D139", "Loại cảm biến": "Cảm biến vị trí hành trình xy lanh sàn trượt", "Chức năng": "U: Pittong lên (Up), D: Pittong xuống (Down), đồng bộ nhịp đẩy dăm"},
                {"Ký hiệu": "1SU137 - 6SD139", "Loại cơ cấu": "Cuộn hút Solenoid van thủy lực", "Chức năng": "Đóng mở dầu thủy lực điều khiển từng xylanh sàn trượt"},
                {"Ký hiệu": "HL128 / LL128", "Loại cảm biến": "Cảm biến báo mức High / Low level bunke", "Chức năng": "Báo đầy/cạn bunke đệm dăm khô trước khi nghiền tinh"}
            ])
            st.dataframe(df_z3_sn, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG 4: NGHIỀN TINH & LỌC BỤI -----------------
    with tab_z4:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">⚙️ KHU VỰC NGHIỀN TINH & LỌC BỤI TÚI KHÍ NÉN (LINE 1 -> 4)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-rtu">TỦ ĐIỀU KHIỂN: RTU#03</span>
                <span class="schematic-tag tag-kw">CÔNG SUẤT: 450kW / MÁY NGHIỀN TINH</span>
                <span class="schematic-tag tag-sensor">CHỐNG CHÁY NỔ: HỆ THỐNG GRECON (G147, G247, G347)</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Dăm khô được nghiền thành bột mùn cưa mịn kích thước 4 - 6mm đạt tiêu chuẩn đồng nhất trước khi nạp vào máy ép viên. 
                Đặc biệt tích hợp hệ thống túi lọc bụi giũ khí nén (FI) và hệ thống dò tia lửa điện tử Grecon tự động dập tắt tàn lửa trong đường ống hút.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z4_l, col_z4_r = st.columns(2)
        with col_z4_l:
            st.markdown("##### ⚙️ Máy nghiền tinh & quạt hút công suất lớn:")
            df_z4_eq = pd.DataFrame([
                {"Mã thiết bị": "HM147", "Loại": "Máy nghiền tinh Line 1 (ANDRITZ)", "Công suất": "450 kW", "Quạt hút chính": "FA1410 (90 kW)", "Cấp liệu": "FD143 + SC141"},
                {"Mã thiết bị": "HM247", "Loại": "Máy nghiền tinh Line 2 (ANDRITZ)", "Công suất": "450 kW", "Quạt hút chính": "FA2410 (110 kW)", "Cấp liệu": "FD243 + SC241"},
                {"Mã thiết bị": "HM347", "Loại": "Máy nghiền tinh Line 3 (SHT)", "Công suất": "450 kW", "Quạt hút chính": "FA3410 (110 kW)", "Cấp liệu": "FD343 + SC341"},
                {"Mã thiết bị": "HM447", "Loại": "Máy nghiền tinh Line 4 (Tương lai)", "Công suất": "450 kW", "Quạt hút chính": "FA4410 (90 kW)", "Cấp liệu": "FD443 + SC441"},
                {"Mã thiết bị": "FI1410 - FI4410", "Loại": "Hệ thống túi lọc bụi giũ khí nén (Bag Filter)", "Công nghệ": "Pulse-jet", "Chức năng": "Tách 99.9% bụi mùn cưa khỏi luồng khí quạt hút"}
            ])
            st.dataframe(df_z4_eq, use_container_width=True, hide_index=True)

        with col_z4_r:
            st.markdown("##### 🚨 Hệ thống bảo vệ phòng nổ & dập tia lửa:")
            df_z4_sn = pd.DataFrame([
                {"Ký hiệu": "G147, G247, G347", "Hệ thống": "GRECON Spark Detection", "Chức năng": "Phát hiện tia lửa siêu nhạy trong đường gió quạt hút, dừng máy khẩn cấp và kích hoạt phun sương cao áp dập tắt cháy"},
                {"Ký hiệu": "VB147, VB247, VB347", "Cảm biến": "Cảm biến rung rotor", "Chức năng": "Giám sát rung động ổ bi máy nghiền tinh cao tốc"},
                {"Ký hiệu": "OT147-1 / OT147-2", "Cảm biến": "Cảm biến nhiệt ổ bi", "Chức năng": "Báo động khi nhiệt gối đỡ vượt 75°C, tự động ngắt tải"},
                {"Ký hiệu": "AL148, AL149, SC1411", "Thiết bị": "Van sao & vít tải gom bột", "Chức năng": "Xả kín mùn cưa từ đáy cyclone và túi lọc bụi vào vít tải chính"}
            ])
            st.dataframe(df_z4_sn, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG 5: CỤM 8 MÁY ÉP PM30-6 -----------------
    with tab_z5:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">🏭 KHU VỰC ÉP VIÊN SINH KHỐI: CỤM 8 MÁY ÉP ANDRITZ PM30-6 (LINE 1 -> LINE 8)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-rtu">TỦ ĐIỀU KHIỂN: RTU#01 & PELLETING CONTROL PANEL</span>
                <span class="schematic-tag tag-kw">CÔNG SUẤT ĐỘNG CƠ CHÍNH: 8 x 355 kW</span>
                <span class="schematic-tag tag-sensor">BÔI TRƠN: BƠM MỠ XUNG ÁP (PULSE LUB) & CHILLER LÀM MÁT DẦU</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Trái tim của nhà máy gồm 8 máy ép viên công nghiệp ANDRITZ PM30-6 bố trí song song. 
                Mỗi máy ép là một tổ hợp cơ điện tinh vi gồm: Vít cấp liệu biến tần, Bộ trộn nhão điều hòa ẩm, Vít ép lực cưỡng bức (Force Screw), 
                Động cơ chính 355kW dẫn động khuôn vòng Ø850mm, Cảm biến cắt chốt an toàn (Shear Pin), Cảm biến nhiệt rulo trái/phải và hệ thống bơm mỡ tự động.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z5_top1, col_z5_top2 = st.columns(2)
        with col_z5_top1:
            st.markdown("##### ⚙️ Tổ hợp thiết bị trên mỗi máy ép PM30-6 (Ví dụ Máy 1: PE1510):")
            df_pe_single = pd.DataFrame([
                {"Mã thiết bị": "PE1510", "Tên": "Động cơ chính máy ép (Pellet Mill)", "Công suất": "355 kW", "Thông số": "Dẫn động hộp số bánh răng nghiêng, khuôn vòng Ø850mm"},
                {"Mã thiết bị": "FD155", "Tên": "Vít cấp liệu biến tần (Feeder)", "Công suất": "4 kW", "Thông số": "Điều chỉnh lưu lượng bột gỗ nạp vào buồng ép theo dòng tải"},
                {"Mã thiết bị": "CD156", "Tên": "Bộ trộn nhão (Conditioner)", "Công suất": "11 kW", "Thông số": "Phối trộn bột dăm với nước vi lượng, hóa dẻo lignin tự nhiên"},
                {"Mã thiết bị": "FS158, FS159", "Tên": "Vít nhồi lực cưỡng bức (Force Screw)", "Công suất": "2 x 1.5 kW", "Thông số": "Ép chặt bột mùn vào góc ép giữa rulo và bề mặt khuôn"},
                {"Mã thiết bị": "WP1511", "Tên": "Bơm nước vi lượng (Water Pump)", "Công suất": "0.55 kW", "Thông số": "Cấp nước tạo ẩm chuẩn vào bộ Conditioner"},
                {"Mã thiết bị": "HP1512", "Tên": "Bơm thủy lực ép rulo (Hydraulic Pump)", "Công suất": "2.2 kW", "Thông số": "Tạo áp lực ép rulo tự động điều khiển khe hở"},
                {"Mã thiết bị": "CR157", "Tên": "Tời nâng cẩu khuôn (Crane)", "Công suất": "0.18 kW", "Thông số": "Hỗ trợ tháo lắp thay thế khuôn vòng Ø850mm"}
            ])
            st.dataframe(df_pe_single, use_container_width=True, hide_index=True)

        with col_z5_top2:
            st.markdown("##### 📡 Cảm biến bảo vệ & bôi trơn tự động PM30-6:")
            df_pe_sensor = pd.DataFrame([
                {"Ký hiệu": "1LS / 1RS", "Tên": "Chốt an toàn cơ khí (Shear Pin Left / Right)", "Chức năng": "Bảo vệ quá tải kẹt dị vật kim loại; chốt gãy lập tức ngắt động cơ 355kW"},
                {"Ký hiệu": "1LT / 1RT", "Tên": "Cảm biến nhiệt độ rulo (Roller Temp L/R)", "Chức năng": "Đo nhiệt độ ma sát ổ bi rulo ép, cảnh báo quá nhiệt > 105°C"},
                {"Ký hiệu": "1PS", "Tên": "Cảm biến xung mỡ (Pulse Switch Lubrication)", "Chức năng": "Xác nhận mỡ bôi trơn áp suất cao đã được bơm vào từng ổ bi rulo"},
                {"Ký hiệu": "1EL", "Tên": "Cảm biến báo cạn mỡ (Empty Lubrication)", "Chức năng": "Báo động thùng mỡ trung tâm cạn, yêu cầu bổ sung mỡ đặc chủng"},
                {"Ký hiệu": "1OOL", "Tên": "Van điện từ bơm mỡ (On/Off Lubrication)", "Chức năng": "Mở chu trình bơm mỡ định kỳ theo số giờ vận hành"},
                {"Ký hiệu": "MC1511 / MG1512", "Tên": "Hệ thống Chiller làm mát dầu hộp số", "Chức năng": "Bơm tuần hoàn và gas lạnh làm mát dầu bôi trơn hộp số 355kW"}
            ])
            st.dataframe(df_pe_sensor, use_container_width=True, hide_index=True)

        st.markdown("##### 📋 Ma trận 8 Line máy ép viên (Line 1 đến Line 8):")
        df_8_pe = pd.DataFrame([
            {"Line": f"Line {i}", "Mã máy ép": f"PE{i}510", "Động cơ chính": "355 kW", "Cấp liệu FD": f"FD{i}55 (4kW)", "Bộ trộn CD": f"CD{i}56 (11kW)", "Vít ép FS": f"FS{i}58/59 (2x1.5kW)", "Cảm biến rulo": f"{i}LT / {i}RT", "Chốt an toàn": f"{i}LS / {i}RS"}
            for i in range(1, 9)
        ])
        st.dataframe(df_8_pe, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG 6: LÀM MÁT & ĐÓNG BAO -----------------
    with tab_z6:
        st.markdown("""
        <div class="schematic-zone-card">
            <h4 style="color: #1e40af; margin-bottom: 8px;">❄️ KHU VỰC LÀM MÁT, SÀNG PHÂN LOẠI & ĐÓNG BAO JUMBO (PACKING STORE)</h4>
            <div style="margin-bottom: 12px;">
                <span class="schematic-tag tag-rtu">TỦ ĐIỀU KHIỂN: RTU#04</span>
                <span class="schematic-tag tag-kw">THÁP MÁT: QUẠT HÚT 90 kW (FA1612)</span>
                <span class="schematic-tag tag-sensor">CÂN BAO: 4 HỆ CÂN LOADCELL TỰ ĐỘNG (LC169 - LC469)</span>
            </div>
            <p style="font-size: 13px; color: #334155; line-height: 1.6;">
                Viên nén sau khi ép ở nhiệt độ 80-90°C được chuyển vào tháp làm nguội ngược dòng Counter-flow Cooler để hạ nhiệt về < 35°C. 
                Sau đó qua sàng rung tách cám 2 tầng, nam châm quay tách kim loại và được nạp vào 4 hệ thống cân tự động đóng bao Jumbo 650kg / 1000kg hoặc xilo xuất hàng rời.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_z6_l, col_z6_r = st.columns(2)
        with col_z6_l:
            st.markdown("##### ⚙️ Thiết bị làm nguội & sàng tách cám:")
            df_z6_eq = pd.DataFrame([
                {"Mã thiết bị": "CO161", "Tên": "Tháp làm mát ngược dòng (Counter-flow Cooler)", "Thông số": "Hạ nhiệt viên nén từ 85°C xuống < 35°C"},
                {"Mã thiết bị": "FA1612", "Tên": "Quạt hút làm mát tháp", "Công suất": "90 kW", "Thông số": "Hút gió đối lưu cưỡng bức làm nguội viên"},
                {"Mã thiết bị": "MD162, MD1611", "Tên": "Mô tơ rải liệu đỉnh tháp mát (Distribution)", "Công suất": "0.5 kW", "Thông số": "Phân bổ đều viên nén trên bề mặt tháp"},
                {"Mã thiết bị": "HP163", "Tên": "Bơm thủy lực xả đáy tháp mát", "Công suất": "5.5 kW", "Thông số": "Xả viên theo mẻ đã làm nguội đạt chuẩn"},
                {"Mã thiết bị": "ST167, ST267", "Tên": "Sàng rung 2 tầng phân loại (Shifter)", "Công suất": "2 x 2.88 kW", "Thông số": "Tách 100% cám vụn và viên gãy vỡ"},
                {"Mã thiết bị": "RMN 1, RMN 2", "Tên": "Nam châm quay tách kim loại (Rotary Magnet)", "Công suất": "2 x 2.2 kW", "Thông số": "Hút sạch tạp chất từ tính trước khi vào bao"},
                {"Mã thiết bị": "SC1616, SC1617", "Tên": "Vít tải hoàn lưu cám vụn", "Công suất": "2 x 4 kW", "Thông số": "Gom cám vụn quay ngược về phễu ép viên"}
            ])
            st.dataframe(df_z6_eq, use_container_width=True, hide_index=True)

        with col_z6_r:
            st.markdown("##### 📦 Hệ thống 4 Cân tự động đóng bao Jumbo:")
            df_z6_pack = pd.DataFrame([
                {"Hệ cân": "Hệ cân Jumbo 1", "Loadcell": "LC169", "Xylanh cửa nạp": "SL169 (Solenoid S169)", "Cảm biến báo mức hopper": "HL166 (High level)"},
                {"Hệ cân": "Hệ cân Jumbo 2", "Loadcell": "LC269", "Xylanh cửa nạp": "SL269 (Solenoid S1610)", "Cảm biến báo mức hopper": "HL266 (High level)"},
                {"Hệ cân": "Hệ cân Jumbo 3 (Cải tiến)", "Loadcell": "LC369", "Xylanh cửa nạp": "SL369 (Solenoid S369)", "Cảm biến báo mức hopper": "HL366 (High level)"},
                {"Hệ cân": "Hệ cân Jumbo 4 (Cải tiến)", "Loadcell": "LC469", "Xylanh cửa nạp": "SL469 (Solenoid S469)", "Cảm biến báo mức hopper": "HL466 (High level)"},
                {"Băng tải xuất": "BE171, BE172, BE173", "Công suất": "15kW / 30kW có thắng", "Chức năng": "Vận chuyển bao Jumbo ra kho thành phẩm / cân xe"}
            ])
            st.dataframe(df_z6_pack, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG: BẢNG KÝ HIỆU P&ID -----------------
    with tab_legend:
        st.markdown("#### 📖 BẢNG TRA CỨU KÝ HIỆU & MÃ THIẾT BỊ THEO CHUẨN P&ID BẢN VẼ")
        st.caption("Quy ước đánh số thiết bị: Chữ số đầu biểu thị Line; Chữ số giữa biểu thị Công đoạn; Chữ số cuối biểu thị Vị trí máy (Ví dụ: PE1510 = Pellet Mill 1 - Công đoạn 5 Ép viên - Vị trí 10)")

        col_leg1, col_leg2 = st.columns(2)
        with col_leg1:
            st.markdown("##### 🏭 Ký hiệu Thiết Bị Cơ Điện (Equipment Codes):")
            df_leg_eq = pd.DataFrame([
                {"Ký hiệu": "DC", "Tên tiếng Anh": "Drag Conveyor", "Tên tiếng Việt": "Xích tải cào liệu"},
                {"Ký hiệu": "BE", "Tên tiếng Anh": "Belt Conveyor", "Tên tiếng Việt": "Băng tải cao su"},
                {"Ký hiệu": "SC", "Tên tiếng Anh": "Screw Conveyor", "Tên tiếng Việt": "Vít tải xoắn"},
                {"Ký hiệu": "AL", "Tên tiếng Anh": "Airlock", "Tên tiếng Việt": "Van sao quay xả kín gió"},
                {"Ký hiệu": "CM", "Tên tiếng Anh": "Chipper", "Tên tiếng Việt": "Máy băm dăm gỗ"},
                {"Ký hiệu": "HM", "Tên tiếng Anh": "Hammer Mill", "Tên tiếng Việt": "Máy nghiền búa"},
                {"Ký hiệu": "PE", "Tên tiếng Anh": "Pellet Mill", "Tên tiếng Việt": "Máy ép viên nén"},
                {"Ký hiệu": "BN", "Tên tiếng Anh": "Burner", "Tên tiếng Việt": "Lò đốt sinh khối"},
                {"Ký hiệu": "DR", "Tên tiếng Anh": "Drum Dryer", "Tên tiếng Việt": "Trống sấy quay"},
                {"Ký hiệu": "CO", "Tên tiếng Anh": "Cooler", "Tên tiếng Việt": "Tháp làm nguội ngược dòng"},
                {"Ký hiệu": "ST", "Tên tiếng Anh": "Shifting Screen", "Tên tiếng Việt": "Sàng rung phân loại"},
                {"Ký hiệu": "FA", "Tên tiếng Anh": "Fan", "Tên tiếng Việt": "Quạt hút / Quạt thổi khí"},
                {"Ký hiệu": "HP", "Tên tiếng Anh": "Hydraulic Pump", "Tên tiếng Việt": "Trạm bơm dầu thủy lực"},
                {"Ký hiệu": "BC", "Tên tiếng Anh": "Bucket Conveyor", "Tên tiếng Việt": "Gàu tải múc nâng cao"},
                {"Ký hiệu": "CY", "Tên tiếng Anh": "Cyclone", "Tên tiếng Việt": "Xyclon lắng tách bụi"},
                {"Ký hiệu": "FD", "Tên tiếng Anh": "Feeder", "Tên tiếng Việt": "Vít cấp liệu biến tần"},
                {"Ký hiệu": "CD", "Tên tiếng Anh": "Conditioner", "Tên tiếng Việt": "Bộ trộn nhão điều hòa ẩm"},
                {"Ký hiệu": "FS", "Tên tiếng Anh": "Force Screw", "Tên tiếng Việt": "Vít nhồi lực ép vào khuôn"},
                {"Ký hiệu": "FI", "Tên tiếng Anh": "Bag Filter", "Tên tiếng Việt": "Bộ lọc bụi giũ khí nén"},
                {"Ký hiệu": "RMN", "Tên tiếng Anh": "Rotary Magnet", "Tên tiếng Việt": "Nam châm quay tách kim loại"}
            ])
            st.dataframe(df_leg_eq, use_container_width=True, hide_index=True)

        with col_leg2:
            st.markdown("##### 📡 Ký hiệu Cảm Biến & Tự Động Hóa (Instrumentation & Sensors):")
            df_leg_sn = pd.DataFrame([
                {"Ký hiệu": "SP...", "Tên tiếng Anh": "Speed Sensor", "Ý nghĩa": "Cảm biến đo tốc độ quay trục (Autonics PR 18-8DN)"},
                {"Ký hiệu": "OV...", "Tên tiếng Anh": "Over Load", "Ý nghĩa": "Cảm biến / Rơ le phát hiện quá tải động cơ"},
                {"Ký hiệu": "HL...", "Tên tiếng Anh": "High Level", "Ý nghĩa": "Cảm biến báo mức cao (chống tràn phễu/xilo)"},
                {"Ký hiệu": "LL...", "Tên tiếng Anh": "Low Level", "Ý nghĩa": "Cảm biến báo mức thấp (chống cạn liệu)"},
                {"Ký hiệu": "OT...", "Tên tiếng Anh": "Over Temperature", "Ý nghĩa": "Cảm biến giám sát quá nhiệt ổ bi / rulo"},
                {"Ký hiệu": "VB...", "Tên tiếng Anh": "Vibration Sensor", "Ý nghĩa": "Cảm biến báo rung chấn máy nghiền búa"},
                {"Ký hiệu": "G...", "Tên tiếng Anh": "Grecon Spark Detection", "Ý nghĩa": "Cảm biến dò tia lửa và dập cháy tự động"},
                {"Ký hiệu": "DP...", "Tên tiếng Anh": "Damper Valve", "Ý nghĩa": "Van lật điều tiết gió nóng lò sấy"},
                {"Ký hiệu": "TW...", "Tên tiếng Anh": "Two-Way Damper", "Ý nghĩa": "Van lật chia 2 ngã dòng nguyên liệu"},
                {"Ký hiệu": "SL...", "Tên tiếng Anh": "Slide Gate", "Ý nghĩa": "Cửa trượt đóng mở khí nén"},
                {"Ký hiệu": "LC...", "Tên tiếng Anh": "Load Cell", "Ý nghĩa": "Cảm biến lực cân đóng bao Jumbo"},
                {"Ký hiệu": "U / D", "Tên tiếng Anh": "Up / Down", "Ý nghĩa": "Công tắc hành trình xylanh Lên / Xuống"},
                {"Ký hiệu": "C / O", "Tên tiếng Anh": "Close / Open", "Ý nghĩa": "Cảm biến vị trí nắp cửa Đóng / Mở an toàn"}
            ])
            st.dataframe(df_leg_sn, use_container_width=True, hide_index=True)

    # ----------------- PHÂN VÙNG: LỊCH SỬ CẬP NHẬT -----------------
    with tab_rev:
        st.markdown("#### 📝 NHẬT KÝ CẬP NHẬT & CẢI TIẾN CÔNG NGHỆ BẢN VẼ")
        st.caption("Tổng hợp các mốc sửa đổi kỹ thuật thực tế được kỹ sư nhà máy BVN Quảng Bình ghi chú trực tiếp trên bản vẽ P&ID:")

        df_revisions = pd.DataFrame([
            {
                "Ngày cập nhật": "17/01/2026",
                "Nội dung cải tiến": "Bổ sung hệ thống nam châm quay RMN 2 (2.2 kW) và 2 hệ cân đóng bao Jumbo số 3 & số 4 (Loadcell LC369, LC469, Solenoid S369, S3611)",
                "Mục đích & Hiệu quả": "Tăng gấp đôi công suất đóng bao Jumbo lên 4 line, chống nghẽn xilo thành phẩm khi 8 máy ép chạy đồng thời."
            },
            {
                "Ngày cập nhật": "07/05/2025 (REV 5.5)",
                "Nội dung cải tiến": "Hủy bỏ không lắp đặt Line nghiền thô số 4 cũ; tối ưu đường hồi dăm và bố trí lại cụm van xả.",
                "Mục đích & Hiệu quả": "Thu gọn mặt bằng nhà xưởng, tập trung công suất vào 3 máy nghiền thô chính HM118, HM218, HM318."
            },
            {
                "Ngày cập nhật": "07/02/2025",
                "Nội dung cải tiến": "Thêm 2 cảm biến báo mức cao HL tại hopper trước cân thành phẩm; đổi tên công tắc hành trình U/D173 thành U/D172; đánh số van 2 ngã TW1517 & TW167; chuẩn hóa mã túi lọc bụi khí nén.",
                "Mục đích & Hiệu quả": "Chống tràn hopper cân bao Jumbo và chuẩn hóa mã hiệu thiết bị trên màn hình SCADA."
            },
            {
                "Ngày cập nhật": "15/01/2025",
                "Nội dung cải tiến": "Bổ sung motor nam châm quay RMN; 1 hệ cân bao Jumbo; cảm biến nhiệt độ áp suất lò sấy; bổ sung động cơ rải liệu MD1520 (2.2 kW) & MD2520 (2.2 kW); kết nối tín hiệu máy nén khí và máy sấy về SCADA.",
                "Mục đích & Hiệu quả": "Giám sát tập trung toàn bộ thông số máy nén khí và lò sấy tại phòng điều khiển trung tâm (Control Room)."
            },
            {
                "Ngày cập nhật": "02/01/2025",
                "Nội dung cải tiến": "Cập nhật hệ thống máy băm dăm Line 1 & Line 2 (PM101, PM201); nâng cấp biến tần vít tải cấp liệu FD.",
                "Mục đích & Hiệu quả": "Ổn định lưu lượng dăm băm vào phễu chứa, giảm xung tải điện lưới."
            }
        ])
        st.dataframe(df_revisions, use_container_width=True, hide_index=True)

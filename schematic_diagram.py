"""
Mô-đun hiển thị:
Tổ Hợp Các Khối Module Công Nghệ, P&ID & Tự Động Hóa Dây Chuyền Sản Xuất
Nhà Máy Viên Nén Gỗ Sinh Khối BVN Quảng Bình.
Số hóa toàn diện từ Bản vẽ Kỹ thuật P&ID AutoCAD & SCADA Schematic (Rev 5.5).
"""

import os
import streamlit as st
import pandas as pd
from PIL import Image
from i18n import t, is_en, translate_eval

def render_html_block(html_content: str):
    """Chuẩn hóa và hiển thị HTML sạch, tránh hiện tượng markdown code block."""
    clean_lines = [line.strip() for line in html_content.strip().split("\n") if line.strip()]
    cleaned_html = "".join(clean_lines)
    if hasattr(st, "html"):
        st.html(cleaned_html)
    else:
        st.markdown(cleaned_html, unsafe_allow_html=True)


def render_factory_schematic_diagram():
    """Hiển thị Tổ hợp các khối module công nghệ sản xuất, P&ID và tự động hóa nhà máy BVN Quảng Bình"""
    
    # CSS Thiết Kế Giao Diện Khối Module Hiện Đại
    st.markdown("""
    <style>
    .mod-header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-left: 6px solid #3b82f6;
        padding: 16px 22px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    }
    .mod-banner-title {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
        margin: 2px 0 4px 0;
    }
    .mod-banner-sub {
        font-size: 13px;
        color: #94a3b8;
    }
    .mod-grid-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        align-items: stretch;
        margin-bottom: 12px;
    }
    .mod-grid-arrow-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin: -4px 0 12px 0;
    }
    .mod-grid-arrow-row > div {
        text-align: center;
        font-size: 16px;
        font-weight: 900;
        color: #94a3b8;
    }
    .mod-box-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        height: 100%;
        min-height: 260px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
    }
    .mod-box-card:hover {
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    .mod-box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1.5px solid #f1f5f9;
        min-height: 32px;
    }
    .mod-box-tags {
        margin-bottom: 8px;
        min-height: 26px;
    }
    .mod-box-process {
        font-size: 12px;
        color: #334155;
        line-height: 1.55;
        margin-bottom: 10px;
        flex: 1 1 auto;
    }
    .mod-box-footer {
        margin-top: auto;
        padding-top: 8px;
        border-top: 1px dashed #e2e8f0;
        font-size: 11px;
        color: #475569;
        line-height: 1.45;
    }
    .mod-tag-pill {
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .mod-tag-rtu { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .mod-tag-kw { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .mod-tag-sensor { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .mod-tag-safety { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

    .mod-flow-arrow {
        text-align: center;
        font-size: 18px;
        font-weight: 900;
        color: #94a3b8;
        padding: 6px 0;
    }
    .mod-equipment-chip {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        background: #f8fafc;
        color: #334155;
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        margin: 2px;
    }
    /* Tối ưu hiển thị Responsive trên Điện thoại và Tablet */
    @media (max-width: 900px) {
        .mod-grid-row {
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .mod-grid-arrow-row {
            display: none;
        }
    }
    @media (max-width: 768px) {
        .mod-header-banner {
            padding: 12px 14px !important;
        }
        .mod-banner-title {
            font-size: 15px !important;
        }
        .mod-banner-sub {
            font-size: 11px !important;
            line-height: 1.4 !important;
        }
        .mod-box-card {
            padding: 10px 12px !important;
            min-height: auto !important;
        }
        .mod-tag-pill {
            font-size: 10px !important;
            padding: 1.5px 6px !important;
        }
        .mod-equipment-chip {
            font-size: 10px !important;
            padding: 1.5px 5px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Header Banner
    render_html_block(f"""
    <div class="mod-header-banner">
        <div style="font-size: 11px; font-weight: 800; color: #60a5fa; text-transform: uppercase; letter-spacing: 1px;">
            {t("HỆ THỐNG P&ID & ĐIỀU KHIỂN TỰ ĐỘNG HÓA SCADA • NHÀ MÁY BVN QUẢNG BÌNH", "P&ID SYSTEM & SCADA AUTOMATION CONTROL • BVN QUANG BINH PLANT")}
        </div>
        <div class="mod-banner-title">{t("📐 TỔ HỢP CÁC KHỐI MODULE QUY TRÌNH SẢN XUẤT", "📐 INTEGRATED PRODUCTION PROCESS MODULES")}</div>
        <div class="mod-banner-sub">
            {t("Số hóa toàn diện 9 phân vùng công nghệ: Bãi dăm ➔ Nghiền thô ➔ Sấy dăm ➔ Nghiền tinh ➔ 8 Máy ép ANDRITZ PM30-6 ➔ Làm mát ➔ Đóng bao Jumbo", "Digitized 9 technological zones: Wood chips ➔ Wet grinding ➔ Drying ➔ Fine grinding ➔ 8 ANDRITZ PM30-6 Mills ➔ Cooling ➔ Jumbo Bagging")}
        </div>
    </div>
    """)

    # Đường dẫn bản vẽ gốc
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_hd_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn_hd.png")
    img_std_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn.png")
    pdf_path = os.path.join(base_dir, "assets", "so_do_nguyen_ly_bvn.pdf")
    mag_pdf_path = os.path.join(base_dir, "assets", "20250220R5.10-So_do_Nam_cham-Model.pdf")
    mag_img_path = os.path.join(base_dir, "assets", "so_do_nam_cham.png")

    # 2. 4 Metric Cards Thống Kê Năng Lực Tổ Hợp
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(t("Tổng Công Suất Động Lực", "Total Electrical Load"), "≈ 4.850 kW", t("Cấp nguồn từ trạm biến áp 8.000 kVA", "Powered by 8,000 kVA substation"))
    with m2:
        st.metric(t("Tổ Hợp Module Công Nghệ", "Process Module Complex"), t("9 Khối Module", "9 Process Modules"), t("Liên động liên tục từ Khối 0 đến Khối 8", "Interlocked from Module 0 to 8"))
    with m3:
        st.metric(t("Hệ Thống Điều Khiển", "Control Systems"), "1 PLC + 5 RTU", t("PLC#01 băm dăm, RTU#01 đến RTU#05", "PLC#01 chipping, RTU#01 to RTU#05"))
    with m4:
        st.metric(t("Hệ Thống An Toàn & Tách Từ", "Safety & Magnets"), t("32 Điểm Nam Châm", "32 Magnet Stations"), t("GreCon dập tia lửa t = 0.25s • 6 Phân vùng", "GreCon spark sup. t = 0.25s • 6 Zones"))

    st.markdown("---")

    # 3. Phân Tab Chức Năng Chính (4 Tab chuyên sâu)
    tab_overview, tab_explorer, tab_magnet, tab_raw = st.tabs([
        t("🧩 Tổ Hợp 9 Module Quy Trình (Dây Chuyền Khép Kín)", "🧩 9 Integrated Process Modules (Closed Line)"),
        t("🔍 Khảo Sát Chi Tiết Từng Module (Thiết Bị & Cảm Biến)", "🔍 Module Explorer (Equipment & Sensors)"),
        t("🧲 Sơ Đồ 32 Điểm Nam Châm (Bản Vẽ Rev 5.10)", "🧲 32-Point Magnet Diagram (Rev 5.10)"),
        t("🗺️ Bản Vẽ Kỹ Thuật P&ID Gốc (AutoCAD / PDF Ultra HD)", "🗺️ Original P&ID Engineering Drawing (AutoCAD / PDF)")
    ])

    # ================= TAB 1: TỔ HỢP 9 KHỐI MODULE =================
    with tab_overview:
        st.markdown(f"#### {t('🧩 Tổ Hợp Các Khối Module Công Nghệ & Dòng Chảy Vật Liệu Dây Chuyền', '🧩 Integrated Process Modules & Material Flow Sequence')}")
        st.caption(t("Các khối module được số hóa từ bản vẽ P&ID kỹ thuật theo đúng thứ tự vận hành thực tế tại Nhà máy BVN Quảng Bình:", "Modules digitized from technical P&ID drawings reflecting real-world operation at BVN Quang Binh Plant:"))

        # Dòng 1: Module 0 ➔ Module 1 ➔ Module 2
        st.markdown(f"##### {t('📍 GIAI ĐOẠN 1: NGUYÊN LIỆU ĐẦU VÀO, NGHIỀN THÔ & SẤY KHÍ NÓNG', '📍 PHASE 1: RAW MATERIAL INFEED, WET GRINDING & ROTARY DRYING')}")
        render_html_block(f"""
        <div class="mod-grid-row">
            <!-- MODULE 0 -->
            <div class="mod-box-card" style="border-top: 4px solid #0284c7;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">🪵</span>
                        <b style="font-size: 13.5px; color: #0284c7;">{t("MODULE 0: BÃM DĂM & BÃI LIỆU", "MODULE 0: CHIPPING & WOOD YARD")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">PLC#01</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">2 x 450 kW</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("4 Điểm Nam Châm (1-4)", "4 Magnets (1-4)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình:</b> Gỗ cây từ bãi chứa được cẩu gắp nạp vào cụm máy băm dăm Line 1 & Line 2. Dăm băm qua xích tải và băng tải rải vào sàn trượt kho dăm tươi.", "<b>Process:</b> Round logs from storage are fed into Chipper Line 1 & Line 2. Chips travel via drag & belt conveyors to green walking-floor storage.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> CM108–CM2011, Băng tải BE107/BE207, Xích tải DC203/204, Sàn trượt HP137-139.<br><b>Cảm biến:</b> Autonics PR 18-8DN đo tốc độ trục, Rơ le quá tải OV103/104.", "<b>Core Equipment:</b> CM108–CM2011, Belt Conveyors BE107/BE207, Drag Conveyors DC203/204, Walking Floor HP137-139.<br><b>Sensors:</b> Shaft speed sensors PR 18-8DN, Overload relay OV103/104.")}
                </div>
            </div>

            <!-- MODULE 1 -->
            <div class="mod-box-card" style="border-top: 4px solid #ea580c;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">🔨</span>
                        <b style="font-size: 13.5px; color: #ea580c;">{t("MODULE 1: NGHIỀN THÔ DĂM ƯỚT", "MODULE 1: WET WOOD GRINDING")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#05</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">4 x 400-450 kW</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("10 Điểm Nam Châm (5-14)", "10 Magnets (5-14)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình (TRƯỚC SẤY):</b> Dăm tươi được nghiền thô bằng máy nghiền búa thành hạt nhỏ xốp để <b>tăng gấp đôi diện tích tiếp xúc nhiệt</b> trước khi đưa vào sấy.", "<b>Process (BEFORE DRYING):</b> Green wood chips are crushed by hammer mills into fine porous particles to <b>double thermal contact area</b> before drying.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> 4 Cụm máy nghiền HM118, HM218 (Andritz 400kW), HM318 (SHT 450kW), HM418, Vít tải SC111/211.<br><b>Cảm biến:</b> Rung rotor VB118, Quá nhiệt gối đỡ OT118, Đảo chiều quay CW/CCW.", "<b>Core Equipment:</b> 4 Hammer Mills HM118, HM218 (Andritz 400kW), HM318 (SHT 450kW), HM418, Screws SC111/211.<br><b>Sensors:</b> Rotor vibration VB118, Bearing overtemp OT118, CW/CCW rotation.")}
                </div>
            </div>

            <!-- MODULE 2 -->
            <div class="mod-box-card" style="border-top: 4px solid #dc2626;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">🔥</span>
                        <b style="font-size: 13.5px; color: #dc2626;">{t("MODULE 2: SẤY DĂM & LÒ ĐỐT PDI", "MODULE 2: DRYING & PDI BURNER")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#02</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">{t("2 x 315 kW Trống", "2 x 315 kW Drums")}</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("3 Điểm Nam Châm (15-17)", "3 Magnets (15-17)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình:</b> 2 Lò đốt PDI Burner cấp khí nóng trực tiếp vào 2 trống sấy quay DR124 & DR224. Độ ẩm dăm được hạ từ <b>~45% xuống chuẩn 12% - 15%</b>.", "<b>Process:</b> Twin PDI Burners feed hot flue gas into dual rotary dryers DR124 & DR224. Moisture is lowered from <b>~45% to standard 12% - 15%</b>.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> Trống quay DR124/224, Lò PDI Burner 1 & 2, Quạt thổi FA1211, Quạt hút FA127/227.<br><b>Cảm biến:</b> Nhiệt độ đỉnh lò T121/122, Van PID DP1217, Cảm biến đo ẩm online HU301.", "<b>Core Equipment:</b> Rotary Drum DR124/224, PDI Burners 1 & 2, Blower FA1211, Exhaust Fan FA127/227.<br><b>Sensors:</b> Furnace peak temp T121/122, PID valve DP1217, Online moisture sensor HU301.")}
                </div>
            </div>
        </div>
        """)

        render_html_block("""
        <div class="mod-grid-arrow-row">
            <div>▼</div>
            <div>▼</div>
            <div>▼</div>
        </div>
        """)

        # Dòng 2: Module 3 ➔ Module 4 ➔ Module 5
        st.markdown(f"##### {t('📍 GIAI ĐOẠN 2: CHUYỂN TIẾP SAU SẤY, NGHIỀN TINH & TRÁI TIM ÉP VIÊN PM30-6', '📍 PHASE 2: POST-DRYING TRANSFER, FINE GRINDING & PELLET MILLS PM30-6')}")
        render_html_block(f"""
        <div class="mod-grid-row">
            <!-- MODULE 3 -->
            <div class="mod-box-card" style="border-top: 4px solid #f59e0b;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">🔄</span>
                        <b style="font-size: 13.5px; color: #b45309;">{t("MODULE 3: TRUNG CHUYỂN & SÀN TRƯỢT", "MODULE 3: POST-DRYING TRANSFER")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#02/03</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">{t("3 x 30 kW Thủy lực", "3 x 30 kW Hydraulic")}</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("3 Nam Châm Tuyến", "3 Line Magnets")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình:</b> Dăm khô sau sấy xả vào bunke sàn trượt thủy lực 6 xylanh để ổn định lưu lượng, sau đó xích tải gom dăm cấp sang phân xưởng nghiền tinh.", "<b>Process:</b> Dried wood chips discharge into 6-cylinder hydraulic walking-floor bins to buffer flow, then drag conveyors convey them to fine grinding.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> 3 Trạm bơm thủy lực HP137, HP138, HP139 (30kW), Xích tải thu hồi DC1115 (18.5kW).<br><b>Cảm biến:</b> Hành trình xylanh Up/Down 1U137-6D139, Báo mức đầy/cạn hopper HL/LL128.", "<b>Core Equipment:</b> 3 Hydraulic pump skids HP137-139 (30kW), Reclaim conveyor DC1115 (18.5kW).<br><b>Sensors:</b> Cylinder Up/Down limit switches, Hopper level switches HL/LL128.")}
                </div>
            </div>

            <!-- MODULE 4 -->
            <div class="mod-box-card" style="border-top: 4px solid #7c3aed;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">⚙️</span>
                        <b style="font-size: 13.5px; color: #7c3aed;">{t("MODULE 4: NGHIỀN TINH & LỌC BỤI", "MODULE 4: FINE GRINDING & DUST")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#03</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">3 x 450 kW</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("3 Điểm Nam Châm (18-20)", "3 Magnets (18-20)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình (SAU SẤY):</b> Dăm khô được 3 máy nghiền tinh ANDRITZ nghiền thành bột gỗ mịn đồng đều (< 4-6mm). Quạt hút và lọc bụi túi Pulse-jet thu hồi 100% bột.", "<b>Process (AFTER DRYING):</b> Dried chips pulverized by 3 ANDRITZ fine hammer mills into uniform fine wood flour (< 4-6mm). Pulse-jet filters recover 100% flour.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> HM147, HM247, HM347 (450kW), Quạt hút FA1410-3410 (110kW), Túi lọc bụi FI1410-3410.<br><b>An toàn GreCon:</b> Cảm biến FM 1/8 phát hiện tia lửa, van ngắt G147-G347, dập nước trong 0.25s.", "<b>Core Equipment:</b> HM147-347 (450kW), Fans FA1410-3410 (110kW), Bag filters FI1410-3410.<br><b>GreCon Safety:</b> FM 1/8 spark sensors, emergency trip G147-G347, 0.25s water mist.")}
                </div>
            </div>

            <!-- MODULE 5 -->
            <div class="mod-box-card" style="border-top: 4px solid #059669;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">🏭</span>
                        <b style="font-size: 13.5px; color: #059669;">{t("MODULE 5: 8 MÁY ÉP ANDRITZ PM30-6", "MODULE 5: 8 ANDRITZ PM30-6 MILLS")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#01</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">8 x 355 kW</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("9 Điểm Nam Châm (21-29)", "9 Magnets (21-29)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Trái tim nhà máy:</b> Bột qua bộ trộn Conditioner CD phun sương ẩm (9-11%), vít ép lực Force Screw FS nén vào cụm 8 máy ép ANDRITZ PM30-6 định hình viên 6-8mm.", "<b>Plant Heart:</b> Wood flour conditioned with water mist (9-11%), force screws charge mash into 8 ANDRITZ PM30-6 mills extruding 6-8mm pellets.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> PE1510-8510 (355kW), Conditioner CD156-856 (11kW), Chiller dầu CH137-139, Bơm mỡ 1LP-8LP.<br><b>Bảo vệ:</b> Chốt an toàn Shear Pin 1LS/1RS, Cảm biến nhiệt rulo 1LT/1RT (< 60°C), Cảm biến xung mỡ 1PS.", "<b>Core Equipment:</b> PE1510-8510 (355kW), Conditioners CD156-856 (11kW), Oil Chillers CH137-139, Auto grease pumps 1LP-8LP.<br><b>Protection:</b> Mechanical shear pins 1LS/1RS, roller temp sensors (< 60°C), grease pulse switches 1PS.")}
                </div>
            </div>
        </div>
        """)

        render_html_block("""
        <div class="mod-grid-arrow-row">
            <div>▼</div>
            <div>▼</div>
            <div>▼</div>
        </div>
        """)

        # Dòng 3: Module 6 ➔ Module 7 ➔ Module 8
        st.markdown(f"##### {t('📍 GIAI ĐOẠN 3: LÀM MÁT, SÀNG PHÂN LOẠI, ĐÓNG BAO JUMBO & HỆ THỐNG PHỤ TRỢ', '📍 PHASE 3: COOLING, SCREENING, JUMBO BAGGING & UTILITY AUXILIARIES')}")
        render_html_block(f"""
        <div class="mod-grid-row">
            <!-- MODULE 6 -->
            <div class="mod-box-card" style="border-top: 4px solid #0284c7;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">❄️</span>
                        <b style="font-size: 13.5px; color: #0284c7;">{t("MODULE 6: LÀM MÁT & SÀNG TÁCH CÁM", "MODULE 6: COOLING & SCREENING")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#04</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">{t("Quạt hút 90 kW", "90 kW Exhaust Fan")}</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("3 Điểm Nam Châm (30-32)", "3 Magnets (30-32)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình:</b> Viên nén nóng 80-90°C được đưa lên tháp làm mát ngược dòng hạ nhiệt về < 35°C để đông đặc lignin tự nhiên. Sàng rung ST167/267 tách cám vụn tuần hoàn về ép.", "<b>Process:</b> Fresh hot pellets (80-90°C) cooled counterflow to < 35°C solidifying natural lignin. Vibrating screens ST167/267 recycle all fines to pellet mills.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> Gàu tải BC1514/2514, Tháp Cooler MD1520/2520, Quạt FA1612 (90kW), Sàng rung ST167/267 (2 x 2.88kW).<br><b>Chỉ tiêu:</b> Độ bền cơ học DU ≥ 97.5%, Tỷ trọng ≥ 600 kg/m³, Độ tro ≤ 1.5%.", "<b>Core Equipment:</b> Elevators BC1514/2514, Coolers MD1520/2520, Fan FA1612 (90kW), Screens ST167/267.<br><b>Quality:</b> Durability DU ≥ 97.5%, Density ≥ 600 kg/m³, Ash ≤ 1.5%.")}
                </div>
            </div>

            <!-- MODULE 7 -->
            <div class="mod-box-card" style="border-top: 4px solid #16a34a;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">📦</span>
                        <b style="font-size: 13.5px; color: #16a34a;">{t("MODULE 7: CÂN ĐÓNG BAO & XUẤT HÀNG", "MODULE 7: JUMBO BAGGING & SHIPPING")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">RTU#04</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">{t("4 Line Cân Jumbo", "4 Jumbo Packing Lines")}</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("Dò Kim Loại RMN (Điểm 30-32)", "Metal Detector RMN (Points 30-32)")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Quy trình:</b> Viên sạch qua nam châm quay RMN và máy dò kim loại chuyên dụng, sau đó nạp vào 4 hệ cân tự động đóng bao Jumbo 1.000kg hoặc bốc xếp xuất Cảng Vũng Áng.", "<b>Process:</b> Clean pellets pass Rotary Magnet RMN and metal detector, then fill automated 1,000kg Jumbo scales or transfer to Vung Ang Port.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> Nam châm quay RMN 1 & 2 (2.2kW), Máy dò kim loại, Cân Load cell LC169-469, Băng tải xuất BE171-173.<br><b>Kiểm soát:</b> Cảm biến báo mức HL166/266, Van 2 ngả TW1517/167, Nam châm treo cảng.", "<b>Core Equipment:</b> Rotary Magnets RMN 1 & 2 (2.2kW), Metal Detector, Scales LC169-469, Outfeed conveyors BE171-173.<br><b>Control:</b> Level switches HL166/266, Two-way valves, Port cross-belt magnets.")}
                </div>
            </div>

            <!-- MODULE 8 -->
            <div class="mod-box-card" style="border-top: 4px solid #475569;">
                <div class="mod-box-header">
                    <div>
                        <span style="font-size: 16px;">⚡</span>
                        <b style="font-size: 13.5px; color: #334155;">{t("MODULE 8: KHÍ NÉN, ĐIỆN & PCCC", "MODULE 8: COMPRESSED AIR, POWER & FIRE")}</b>
                    </div>
                    <span class="mod-tag-pill mod-tag-rtu">{t("HỆ PHỤ TRỢ", "AUXILIARY")}</span>
                </div>
                <div class="mod-box-tags">
                    <span class="mod-tag-pill mod-tag-kw">{t("TBA 8.000 + 1.800 kVA", "Substation 8,000 + 1,800 kVA")}</span>
                    <span class="mod-tag-pill mod-tag-safety">{t("GreCon Dập Lửa 0.25s", "GreCon Fire Ext. 0.25s")}</span>
                </div>
                <div class="mod-box-process">
                    {t("<b>Hệ phụ trợ toàn nhà máy:</b> Cung cấp nguồn điện ổn định, khí nén công nghiệp áp suất cao điều khiển van/giũ bụi và hệ thống an toàn phòng nổ GreCon (Đức).", "<b>Plant-wide Auxiliaries:</b> Stable power, high-pressure instrument air for valves/pulse cleaning, and German GreCon explosion prevention.")}
                </div>
                <div class="mod-box-footer">
                    {t("<b>Thiết bị chính:</b> 2 Máy nén khí trục vít Air Compressor + Bình tích áp, Tủ phân phối MSB/MDB, Trạm biến áp 9.800 kVA.<br><b>An toàn:</b> Tủ trung tâm GreCon CC7016, 2 bình tích áp 500L, vòi phun sương 120° (S ≥ 7.5m).", "<b>Core Equipment:</b> 2 Screw Air Compressors + Pressure Tanks, Switchgear MSB/MDB, Substation 9,800 kVA.<br><b>Safety:</b> GreCon CC7016 Console, twin 500L accumulators, 120° mist nozzles (S ≥ 7.5m).")}
                </div>
            </div>
        </div>
        """)

    # ================= TAB 2: KHẢO SÁT CHI TIẾT TỪNG MODULE =================
    with tab_explorer:
        st.markdown(f"#### {t('🔍 Bảng Điều Khiển Chi Tiết Thiết Bị & Tự Động Hóa Từng Module', '🔍 Module Equipment & Automation Detail Control Panel')}")
        st.caption(t("Chọn một module để xem toàn bộ danh mục động cơ, công suất (kW), cảm biến đo lường và logic liên động SCADA:", "Select a module to view complete motor list, power (kW), measurement sensors, and SCADA interlocking logic:"))

        module_options = [
            f"Module 0: {t('Băm Dăm & Bãi Chứa Liệu (PLC#01)', 'Wood Chipping & Storage Yard (PLC#01)')}",
            f"Module 1: {t('Phân Xưởng Nghiền Thô Dăm Ướt (RTU#05)', 'Wet Wood Coarse Grinding Workshop (RTU#05)')}",
            f"Module 2: {t('Cụm Trống Sấy Quay DR124/224 & Lò Đốt PDI (RTU#02)', 'Rotary Drum Dryers DR124/224 & PDI Burners (RTU#02)')}",
            f"Module 3: {t('Cụm Trung Chuyển Sau Sấy & Sàn Trượt Thủy Lực (RTU#02/03)', 'Post-Drying Transfer & Hydraulic Walking Floor (RTU#02/03)')}",
            f"Module 4: {t('Phân Xưởng Nghiền Tinh & Lọc Bụi Túi Khí Nén (RTU#03)', 'Fine Grinding Workshop & Pulse-jet Bag Filter (RTU#03)')}",
            f"Module 5: {t('Cụm 8 Máy Ép Viên ANDRITZ PM30-6 (RTU#01)', '8x ANDRITZ PM30-6 Pellet Mills (RTU#01)')}",
            f"Module 6: {t('Tháp Làm Mát Cooler & Sàng Rung Phân Loại Tách Cám (RTU#04)', 'Cooler Tower & Vibrating Screen Classifier (RTU#04)')}",
            f"Module 7: {t('Dò Kim Loại, Cân Đóng Bao Jumbo & Xuất Hàng (RTU#04)', 'Metal Detection, Jumbo Bag Scale & Dispatch (RTU#04)')}",
            f"Module 8: {t('Trạm Khí Nén, Điện Động Lực & Hệ Thống PCCC GreCon', 'Air Compressor, Power Substation & GreCon Fire System')}"
        ]

        sel_module = st.selectbox(
            t("Chọn Module Công Nghệ Cần Tra Cứu:", "Select Process Module to Query:"),
            module_options
        )

        st.markdown("---")

        if "Module 0" in sel_module:
            st.markdown(f"##### {t('🪵 MODULE 0: TIẾP NHẬN NGUYÊN LIỆU, BĂM DĂM & CẤP LIỆU (TỦ PLC#01)', '🪵 MODULE 0: RAW MATERIAL RECEPTION, CHIPPING & FEEDING (PLC#01)')}")
            c_m0_l, c_m0_r = st.columns(2)
            with c_m0_l:
                st.markdown(f"**{t('⚙️ Danh Mục Thiết Bị Động Lực:', '⚙️ Power Equipment Inventory:')}**")
                if is_en():
                    df_m0_eq = pd.DataFrame([
                        {"P&ID Tag": "CM108 - CM1011", "Equipment Name": "Chipper Line 1 Assembly", "Power": "Main Motor 450 kW + auxiliary", "Function": "Chip logs into 20-30mm chips"},
                        {"P&ID Tag": "CM208 - CM2011", "Equipment Name": "Chipper Line 2 Assembly", "Power": "Main Motor 450 kW + auxiliary", "Function": "Parallel Chipper Line 2"},
                        {"P&ID Tag": "DC103, DC104, DC106", "Equipment Name": "Drag Conveyor Line 1", "Power": "11 kW / 9.2 kW / 15 kW", "Function": "Transfer chips from hopper to main belt"},
                        {"P&ID Tag": "DC203, DC204, DC206", "Equipment Name": "Drag Conveyor Line 2", "Power": "11 kW / 9.2 kW / 15 kW", "Function": "Transfer chips Line 2"},
                        {"P&ID Tag": "BE107, BE207", "Equipment Name": "Belt Conveyor", "Power": "15 kW (with mechanical brake)", "Function": "Transfer chips to raw storage"},
                        {"P&ID Tag": "BE1012 - BE1014", "Equipment Name": "Line 1 Chip Yard Distribution Belt", "Power": "30 kW + 1.5 kW brake", "Function": "Distribute chips into storage bins"},
                        {"P&ID Tag": "AL1112, AL2112", "Equipment Name": "Permanent Magnetic Separators (4 sets)", "Power": "Mechanical Magnet", "Function": "Extract nails and tramp iron before hammer mill"}
                    ])
                else:
                    df_m0_eq = pd.DataFrame([
                        {"Mã P&ID": "CM108 - CM1011", "Tên thiết bị": "Cụm máy băm dăm Line 1 (Chipper)", "Công suất": "Động cơ chính 450 kW + phụ", "Chức năng": "Băm gỗ cây thành dăm kích thước 20-30mm"},
                        {"Mã P&ID": "CM208 - CM2011", "Tên thiết bị": "Cụm máy băm dăm Line 2 (Chipper)", "Công suất": "Động cơ chính 450 kW + phụ", "Chức năng": "Dây chuyền băm dăm Line 2 song song"},
                        {"Mã P&ID": "DC103, DC104, DC106", "Tên thiết bị": "Xích tải nạp dăm Line 1 (Drag Conveyor)", "Công suất": "11 kW / 9.2 kW / 15 kW", "Chức năng": "Tải dăm từ phễu băm về băng tải chính"},
                        {"Mã P&ID": "DC203, DC204, DC206", "Tên thiết bị": "Xích tải nạp dăm Line 2 (Drag Conveyor)", "Công suất": "11 kW / 9.2 kW / 15 kW", "Chức năng": "Tải dăm Line 2"},
                        {"Mã P&ID": "BE107, BE207", "Tên thiết bị": "Băng tải trung chuyển (Belt Conveyor)", "Công suất": "15 kW (có thắng cơ)", "Chức năng": "Chuyển dăm lên kho dăm thô"},
                        {"Mã P&ID": "BE1012 - BE1014", "Tên thiết bị": "Băng tải phân phối bãi dăm Line 1", "Công suất": "30 kW + 1.5 kW thắng", "Chức năng": "Rải dăm vào các khoang chứa"},
                        {"Mã P&ID": "AL1112, AL2112", "Tên thiết bị": "Cụm nam châm tách từ vĩnh cửu (4 cụm)", "Công suất": "Cơ khí nam châm", "Chức năng": "Hút đinh, vụn sắt trước khi vào máy nghiền"}
                    ])
                st.dataframe(df_m0_eq, use_container_width=True, hide_index=True)
            with c_m0_r:
                st.markdown(f"**{t('📡 Hệ Thống Cảm Biến & SCADA PLC#01:', '📡 Sensor System & SCADA PLC#01:')}**")
                if is_en():
                    df_m0_sn = pd.DataFrame([
                        {"Tag": "SP103.1, SP103.2", "Sensor Type": "Speed Sensor", "Model": "Autonics PR 18-8DN", "Function": "Monitor DC103 drag conveyor shaft speed"},
                        {"Tag": "SP104, SP106, SP107", "Sensor Type": "Shaft Speed Sensor", "Model": "Autonics PR 18-8DN", "Function": "Belt slippage / feed chain break alert"},
                        {"Tag": "OV103, OV104", "Sensor Type": "Overload Sensor", "Model": "Current protection", "Function": "Emergency trip on wood jam in trough"},
                        {"Tag": "OT108.1, OT108.2", "Sensor Type": "Bearing Overtemp Sensor", "Model": "PT100 / Thermocouple", "Function": "Monitor CM108 chipper bearing temperature"},
                        {"Tag": "C113 / O113", "Sensor Type": "Door Limit Switch (Close/Open)", "Model": "Micro-switch", "Function": "Safety maintenance door close confirmation"}
                    ])
                else:
                    df_m0_sn = pd.DataFrame([
                        {"Ký hiệu": "SP103.1, SP103.2", "Loại cảm biến": "Cảm biến tốc độ (Speed Sensor)", "Model": "Autonics PR 18-8DN", "Chức năng": "Giám sát tốc độ quay trục xích tải DC103"},
                        {"Ký hiệu": "SP104, SP106, SP107", "Loại cảm biến": "Cảm biến tốc độ trục", "Model": "Autonics PR 18-8DN", "Chức năng": "Báo trượt băng tải / đứt xích cấp liệu"},
                        {"Ký hiệu": "OV103, OV104", "Loại cảm biến": "Cảm biến quá tải (Overload)", "Model": "Bảo vệ dòng điện", "Chức năng": "Ngắt khẩn cấp khi kẹt gỗ trong máng cào"},
                        {"Ký hiệu": "OT108.1, OT108.2", "Loại cảm biến": "Cảm biến quá nhiệt ổ bi", "Model": "PT100 / Thermocouple", "Chức năng": "Giám sát nhiệt ổ bi gối đỡ máy băm CM108"},
                        {"Ký hiệu": "C113 / O113", "Loại cảm biến": "Công tắc hành trình cửa (Close/Open)", "Model": "Micro-switch", "Chức năng": "Xác nhận đóng nắp bảo trì an toàn"}
                    ])
                st.dataframe(df_m0_sn, use_container_width=True, hide_index=True)

        elif "Module 1" in sel_module:
            st.markdown(f"##### {t('🔨 MODULE 1: PHÂN XƯỞNG NGHIỀN THÔ DĂM ƯỚT (TỦ RTU#05)', '🔨 MODULE 1: WET WOOD COARSE GRINDING WORKSHOP (RTU#05)')}")
            c_m1_l, c_m1_r = st.columns(2)
            with c_m1_l:
                st.markdown(f"**{t('⚙️ Cụm 4 Line Máy Nghiền Thô (Diễn Ra TRƯỚC SẤY):', '⚙️ 4x Coarse Grinding Lines (Operates BEFORE DRYING):')}**")
                if is_en():
                    df_m1_eq = pd.DataFrame([
                        {"Line": "Line 1", "Main Hammer Mill": "HM118 (400 kW ANDRITZ)", "Feeder": "Screw Feeder FD114 (11 kW with brake) + SC111 (2x5.5kW)", "Exhaust Fan": "FA1113 (45 kW)", "Rotary Airlock": "AL1110 (4 kW), AL1111, AL1112"},
                        {"Line": "Line 2", "Main Hammer Mill": "HM218 (400 kW ANDRITZ)", "Feeder": "Screw Feeder FD214 (11 kW with brake) + SC211 (2x5.5kW)", "Exhaust Fan": "FA2113 (55 kW)", "Rotary Airlock": "AL2110 (4 kW), AL2111, AL2112"},
                        {"Line": "Line 3", "Main Hammer Mill": "HM318 (450 kW SHT)", "Feeder": "Screw Feeder FD314 (11 kW with brake) + SC311 (2x5.5kW)", "Exhaust Fan": "FA3113 (55 kW)", "Rotary Airlock": "AL3110 (4 kW), AL3111, AL3112"},
                        {"Line": "Line 4 (Standby)", "Main Hammer Mill": "HM418 (450 kW Future)", "Feeder": "Screw Feeder FD414 (11 kW) + SC411", "Exhaust Fan": "FA4113", "Rotary Airlock": "AL4110, AL4111, AL4112"}
                    ])
                else:
                    df_m1_eq = pd.DataFrame([
                        {"Line": "Line 1", "Máy nghiền chính": "HM118 (400 kW ANDRITZ)", "Cấp liệu": "Vít tải FD114 (11 kW có thắng) + SC111 (2x5.5kW)", "Quạt hút": "FA1113 (45 kW)", "Van sao xả": "AL1110 (4 kW), AL1111, AL1112"},
                        {"Line": "Line 2", "Máy nghiền chính": "HM218 (400 kW ANDRITZ)", "Cấp liệu": "Vít tải FD214 (11 kW có thắng) + SC211 (2x5.5kW)", "Quạt hút": "FA2113 (55 kW)", "Van sao xả": "AL2110 (4 kW), AL2111, AL2112"},
                        {"Line": "Line 3", "Máy nghiền chính": "HM318 (450 kW SHT)", "Cấp liệu": "Vít tải FD314 (11 kW có thắng) + SC311 (2x5.5kW)", "Quạt hút": "FA3113 (55 kW)", "Van sao xả": "AL3110 (4 kW), AL3111, AL3112"},
                        {"Line": "Line 4 (Dự phòng)", "Máy nghiền chính": "HM418 (450 kW Tương lai)", "Cấp liệu": "Vít tải FD414 (11 kW) + SC411", "Quạt hút": "FA4113", "Van sao xả": "AL4110, AL4111, AL4112"}
                    ])
                st.dataframe(df_m1_eq, use_container_width=True, hide_index=True)
            with c_m1_r:
                st.markdown(f"**{t('🛡️ Cảm Biến Bảo Vệ & 10 Điểm Nam Châm Tách Từ (Điểm 5 đến 14):', '🛡️ Protection Sensors & 10 Magnetic Separators (Points 5 to 14):')}**")
                if is_en():
                    df_m1_sn = pd.DataFrame([
                        {"Sensor Tag": "VB118, VB218, VB318", "Name": "Vibration Sensor", "Function": "Detect rotor imbalance or broken hammers for instant shutdown"},
                        {"Sensor Tag": "OT118-1, OT118-2", "Name": "Drive/Non-drive Bearing Overtemp", "Function": "Protect main bearings of HM118 hammer mill"},
                        {"Sensor Tag": "SP118, SP218, SP318", "Name": "Main Shaft Speed Sensor", "Function": "Confirm hammer mill reached nominal speed before opening feeder"},
                        {"Sensor Tag": "CW / CCW", "Name": "Rotation Direction Sensor", "Function": "Periodic direction reversal for symmetrical hammer wear"},
                        {"Sensor Tag": "DR / DL", "Name": "Door Switch Right / Left", "Function": "Safety interlock, inhibit start when door is open"}
                    ])
                else:
                    df_m1_sn = pd.DataFrame([
                        {"Mã cảm biến": "VB118, VB218, VB318", "Tên": "Cảm biến báo rung (Vibration Sensor)", "Chức năng": "Phát hiện mất cân bằng rotor, gãy búa nghiền để dừng máy ngay lập tức"},
                        {"Mã cảm biến": "OT118-1, OT118-2", "Tên": "Quá nhiệt ổ bi gần / xa motor", "Chức năng": "Bảo vệ gối đỡ vòng bi chính máy nghiền HM118"},
                        {"Mã cảm biến": "SP118, SP218, SP318", "Tên": "Cảm biến tốc độ trục chính", "Chức năng": "Xác nhận máy nghiền đã đạt đủ tốc độ trước khi mở vít cấp liệu"},
                        {"Mã cảm biến": "CW / CCW", "Tên": "Cảm biến chiều quay thuận / ngược", "Chức năng": "Điều khiển đảo chiều định kỳ để mòn đều 2 cạnh búa nghiền"},
                        {"Mã cảm biến": "DR / DL", "Tên": "Door Switch Right / Left", "Chức năng": "Khóa liên động an toàn, cấm khởi động khi cửa mở"}
                    ])
                st.dataframe(df_m1_sn, use_container_width=True, hide_index=True)

        elif "Module 2" in sel_module:
            st.markdown(f"##### {t('🔥 MODULE 2: CỤM TRỐNG SẤY QUAY & LÒ ĐỐT PDI MỸ (TỦ RTU#02)', '🔥 MODULE 2: ROTARY DRUM DRYERS & USA PDI BURNERS (RTU#02)')}")
            c_m2_l, c_m2_r = st.columns(2)
            with c_m2_l:
                st.markdown(f"**{t('⚙️ Thiết Bị Hệ Thống Sấy DR124/224 & Lò Đốt PDI:', '⚙️ DR124/224 Drying System & PDI Burner Equipment:')}**")
                if is_en():
                    df_m2_eq = pd.DataFrame([
                        {"Equipment Tag": "DR124, DR224", "Equipment Name": "2x Rotary Drum Dryers", "Power": "315 kW each", "Function": "Tumble wet chips with hot flue gas to evaporate moisture"},
                        {"Equipment Tag": "BURNER 1, BURNER 2", "Equipment Name": "PDI Biomass Furnace Burners", "Feeder": "Automatic biomass fuel screw", "Function": "Supply drying heat, inlet temp controlled at 280-350°C"},
                        {"Equipment Tag": "FA127, FA227", "Equipment Name": "Hot Gas Induced Draft Fans", "Power": "30 kW each", "Function": "Create negative draft pulling hot flue gas through drum"},
                        {"Equipment Tag": "FA1211, FA2211", "Equipment Name": "Auxiliary Drying Air Fans", "Power": "9.2 kW each", "Function": "Evacuate fine dust through settling cyclones"},
                        {"Equipment Tag": "DP1212 - DP1217", "Equipment Name": "Damper Flap System", "Power": "0.4 kW Actuators", "Function": "Balance hot gas flow and recirculation loop"}
                    ])
                else:
                    df_m2_eq = pd.DataFrame([
                        {"Mã thiết bị": "DR124, DR224", "Tên thiết bị": "2 Trống sấy quay (Drum Dryer)", "Công suất": "315 kW mỗi trống", "Chức năng": "Đảo trộn dăm với khí nóng để bay hơi nước"},
                        {"Mã thiết bị": "BURNER 1, BURNER 2", "Tên thiết bị": "Lò đốt sinh khối PDI", "Cấp liệu": "Vít nạp dăm đốt tự động", "Chức năng": "Cấp nhiệt sấy, kiểm soát nhiệt vào 280-350°C"},
                        {"Mã thiết bị": "FA127, FA227", "Tên thiết bị": "Quạt hút khí nóng (Main Fan)", "Công suất": "30 kW mỗi quạt", "Chức năng": "Tạo áp suất âm hút khí nóng qua thân trống"},
                        {"Mã thiết bị": "FA1211, FA2211", "Tên thiết bị": "Quạt thổi khí sấy phụ", "Công suất": "9.2 kW mỗi quạt", "Chức năng": "Hút bụi mịn qua cyclone lắng"},
                        {"Mã thiết bị": "DP1212 - DP1217", "Tên thiết bị": "Hệ thống van lật damper", "Công suất": "Động cơ chấp hành 0.4kW", "Chức năng": "Cân bằng lưu lượng gió nóng và gió hồi"}
                    ])
                st.dataframe(df_m2_eq, use_container_width=True, hide_index=True)
            with c_m2_r:
                st.markdown(f"**{t('📡 Cảm Biến Nhiệt Độ, Áp Suất & Độ Ẩm SCADA:', '📡 Temperature, Pressure & SCADA Moisture Sensors:')}**")
                if is_en():
                    df_m2_sn = pd.DataFrame([
                        {"Tag": "T121, T122, T123, T124", "Type": "Hot Gas Temperature Sensors", "Function": "Measure combustion chamber, drum inlet and outlet temperatures"},
                        {"Tag": "BV1 / BV2 (CBV / OBV)", "Type": "Burner Valve Close / Open", "Function": "Safety shutoff valve isolating hot flue gas if T exceeds 1200°C"},
                        {"Tag": "HU301", "Type": "Online Moisture Sensor", "Function": "Measure dried chip moisture (target 12 - 15%) reporting to SCADA"},
                        {"Tag": "P121, P124", "Type": "Differential Pressure Sensors", "Function": "Maintain dryer negative pressure P121 = 9-10 mbar, P124 = 10 mbar"}
                    ])
                else:
                    df_m2_sn = pd.DataFrame([
                        {"Ký hiệu": "T121, T122, T123, T124", "Loại": "Cảm biến nhiệt độ khí sấy (Temp)", "Chức năng": "Đo nhiệt buồng đốt, nhiệt đầu vào và nhiệt ra trống sấy"},
                        {"Ký hiệu": "BV1 / BV2 (CBV / OBV)", "Loại": "Burner Valve Close / Open", "Chức năng": "Van an toàn ngắt gió nóng khẩn cấp khi T vượt 1200°C"},
                        {"Ký hiệu": "HU301", "Loại": "Cảm biến đo độ ẩm Online", "Chức năng": "Đo độ ẩm dăm ra khỏi trống sấy (chuẩn 12 - 15%) về SCADA"},
                        {"Ký hiệu": "P121, P124", "Loại": "Cảm biến chênh áp (Differential Pressure)", "Chức năng": "Duy trì áp suất âm lò sấy P121 = 9-10 mbar, P124 = 10 mbar"}
                    ])
                st.dataframe(df_m2_sn, use_container_width=True, hide_index=True)

        elif "Module 3" in sel_module:
            st.markdown(f"##### {t('🔄 MODULE 3: CỤM TRUNG CHUYỂN SAU SẤY & SÀN TRƯỢT THỦY LỰC', '🔄 MODULE 3: POST-DRYING TRANSFER & HYDRAULIC WALKING FLOOR')}")
            c_m3_l, c_m3_r = st.columns(2)
            with c_m3_l:
                st.markdown(f"**{t('⚙️ Thiết Bị Thủy Lực & Xích Tải Thu Hồi:', '⚙️ Hydraulic Units & Reclamation Drag Conveyors:')}**")
                if is_en():
                    df_m3_eq = pd.DataFrame([
                        {"Equipment Tag": "HP137, HP138, HP139", "Equipment Name": "3x Walking Floor Hydraulic Stations", "Power": "3 x 30 kW", "Function": "Push dry chips from bunker bottom into drag conveyor"},
                        {"Equipment Tag": "DC1115", "Equipment Name": "Post-Drying Dry Chip Drag Conveyor", "Power": "18.5 kW", "Function": "Collect dried chips and convey to fine grinding area"},
                        {"Equipment Tag": "AL133", "Equipment Name": "Cyclone Bottom Rotary Airlock", "Power": "4 kW", "Function": "Reclaim fine wood powder from dryer flue exhaust"}
                    ])
                else:
                    df_m3_eq = pd.DataFrame([
                        {"Mã thiết bị": "HP137, HP138, HP139", "Tên thiết bị": "3 Trạm bơm thủy lực sàn trượt", "Công suất": "3 x 30 kW", "Chức năng": "Đẩy dăm khô đáy bunke sàn trượt vào xích tải"},
                        {"Mã thiết bị": "DC1115", "Tên thiết bị": "Xích tải dăm khô sau sấy", "Công suất": "18.5 kW", "Chức năng": "Gom dăm khô cấp sang khu vực nghiền tinh"},
                        {"Mã thiết bị": "AL133", "Tên thiết bị": "Van sao xả kín gió đáy cyclone sấy", "Công suất": "4 kW", "Chức năng": "Thu hồi bột mịn từ khí thải sấy"}
                    ])
                st.dataframe(df_m3_eq, use_container_width=True, hide_index=True)
            with c_m3_r:
                st.markdown(f"**{t('📡 Cảm Biến Hành Trình Xylanh & Báo Mức Bunke:', '📡 Cylinder Stroke Sensors & Bunker Level Switches:')}**")
                if is_en():
                    df_m3_sn = pd.DataFrame([
                        {"Tag": "1U137 - 6D139", "Type": "Cylinder Stroke Position Sensors", "Function": "U: Piston Up, D: Piston Down, synchronize walking floor strokes"},
                        {"Tag": "1SU137 - 6SD139", "Type": "Hydraulic Valve Solenoid Coils", "Function": "Actuate hydraulic oil to control each walking floor cylinder"},
                        {"Tag": "HL128 / LL128", "Type": "High / Low Level Switches", "Function": "Buffer bunker full/empty alert before fine grinding"}
                    ])
                else:
                    df_m3_sn = pd.DataFrame([
                        {"Ký hiệu": "1U137 - 6D139", "Loại": "Cảm biến vị trí hành trình xylanh", "Chức năng": "U: Pittong lên, D: Pittong xuống, đồng bộ nhịp đẩy dăm"},
                        {"Ký hiệu": "1SU137 - 6SD139", "Loại": "Cuộn hút Solenoid van thủy lực", "Chức năng": "Đóng mở dầu thủy lực điều khiển từng xylanh sàn trượt"},
                        {"Ký hiệu": "HL128 / LL128", "Loại": "Cảm biến báo mức High / Low level", "Chức năng": "Báo đầy/cạn bunke đệm dăm khô trước khi nghiền tinh"}
                    ])
                st.dataframe(df_m3_sn, use_container_width=True, hide_index=True)

        elif "Module 4" in sel_module:
            st.markdown(f"##### {t('⚙️ MODULE 4: PHÂN XƯỞNG NGHIỀN TINH & LỌC BỤI TÚI KHÍ NÉN (TỦ RTU#03)', '⚙️ MODULE 4: FINE GRINDING WORKSHOP & PULSE-JET BAG FILTER (RTU#03)')}")
            c_m4_l, c_m4_r = st.columns(2)
            with c_m4_l:
                st.markdown(f"**{t('⚙️ Máy Nghiền Tinh & Quạt Hút Công Suất Lớn:', '⚙️ Fine Hammer Mills & High-Power Exhaust Fans:')}**")
                if is_en():
                    df_m4_eq = pd.DataFrame([
                        {"Equipment Tag": "HM147", "Type": "Fine Hammer Mill Line 1 (ANDRITZ)", "Power": "450 kW", "Main Exhaust Fan": "FA1410 (90 kW)", "Feeder": "FD143 + SC141"},
                        {"Equipment Tag": "HM247", "Type": "Fine Hammer Mill Line 2 (ANDRITZ)", "Power": "450 kW", "Main Exhaust Fan": "FA2410 (110 kW)", "Feeder": "FD243 + SC241"},
                        {"Equipment Tag": "HM347", "Type": "Fine Hammer Mill Line 3 (SHT)", "Power": "450 kW", "Main Exhaust Fan": "FA3410 (110 kW)", "Feeder": "FD343 + SC341"},
                        {"Equipment Tag": "FI1410 - FI3410", "Type": "Pulse-Jet Bag Filter Unit", "Technology": "Pulse-jet", "Function": "Separate 99.9% sawdust particulate from exhaust airstream"}
                    ])
                else:
                    df_m4_eq = pd.DataFrame([
                        {"Mã thiết bị": "HM147", "Loại": "Máy nghiền tinh Line 1 (ANDRITZ)", "Công suất": "450 kW", "Quạt hút chính": "FA1410 (90 kW)", "Cấp liệu": "FD143 + SC141"},
                        {"Mã thiết bị": "HM247", "Loại": "Máy nghiền tinh Line 2 (ANDRITZ)", "Công suất": "450 kW", "Quạt hút chính": "FA2410 (110 kW)", "Cấp liệu": "FD243 + SC241"},
                        {"Mã thiết bị": "HM347", "Loại": "Máy nghiền tinh Line 3 (SHT)", "Công suất": "450 kW", "Quạt hút chính": "FA3410 (110 kW)", "Cấp liệu": "FD343 + SC341"},
                        {"Mã thiết bị": "FI1410 - FI3410", "Loại": "Bộ lọc bụi túi giũ khí nén (Bag Filter)", "Công nghệ": "Pulse-jet", "Chức năng": "Tách 99.9% bụi mùn cưa khỏi luồng khí thải"}
                    ])
                st.dataframe(df_m4_eq, use_container_width=True, hide_index=True)
            with c_m4_r:
                st.markdown(f"**{t('🚨 Hệ Thống Bảo Vệ Phòng Nổ & Dập Tia Lửa GreCon (Đức):', '🚨 GreCon Explosion Protection & Spark Extinguishing (Germany):')}**")
                if is_en():
                    df_m4_sn = pd.DataFrame([
                        {"Tag": "G147, G247, G347", "System": "GRECON Spark Detection", "Function": "Ultra-fast infrared spark detection, emergency trip & 0.25s mist suppression"},
                        {"Tag": "VB147, VB247, VB347", "Sensor": "Rotor Vibration Sensor", "Function": "Monitor high-speed fine grinding rotor bearing vibration"},
                        {"Tag": "OT147-1 / OT147-2", "Sensor": "Bearing Overtemp Sensor", "Function": "Alarm when bearing exceeds 75°C, auto-unload motor"},
                        {"Tag": "AL148, AL149, SC1411", "Equipment": "Rotary Airlock & Powder Screw", "Function": "Discharge dust from cyclone base into main collection screw"}
                    ])
                else:
                    df_m4_sn = pd.DataFrame([
                        {"Ký hiệu": "G147, G247, G347", "Hệ thống": "GRECON Spark Detection", "Chức năng": "Phát hiện tia lửa siêu nhạy, ngắt khẩn cấp và dập tắt bằng sương cao áp trong 0.25s"},
                        {"Ký hiệu": "VB147, VB247, VB347", "Cảm biến": "Cảm biến rung rotor", "Chức năng": "Giám sát rung động ổ bi máy nghiền tinh cao tốc"},
                        {"Ký hiệu": "OT147-1 / OT147-2", "Cảm biến": "Cảm biến nhiệt ổ bi", "Chức năng": "Báo động khi nhiệt gối đỡ vượt 75°C, tự động ngắt tải"},
                        {"Ký hiệu": "AL148, AL149, SC1411", "Thiết bị": "Van sao & vít tải gom bột", "Chức năng": "Xả kín mùn cưa từ đáy cyclone vào vít tải chính"}
                    ])
                st.dataframe(df_m4_sn, use_container_width=True, hide_index=True)

        elif "Module 5" in sel_module:
            st.markdown(f"##### {t('🏭 MODULE 5: TRÁI TIM ÉP VIÊN — CỤM 8 MÁY ANDRITZ PM30-6 (TỦ RTU#01)', '🏭 MODULE 5: PELLETING HEART — 8x ANDRITZ PM30-6 PELLET MILLS (RTU#01)')}")
            c_m5_l, c_m5_r = st.columns(2)
            with c_m5_l:
                st.markdown(f"**{t('⚙️ Tổ Hợp Cơ Điện Trên Mỗi Máy Ép PM30-6 (8 Máy x 355 kW):', '⚙️ Electromechanical Assembly on Each PM30-6 (8x 355 kW):')}**")
                if is_en():
                    df_m5_eq = pd.DataFrame([
                        {"Tag": "PE1510", "Name": "Pellet Mill Main Motor", "Power": "355 kW", "Specification": "Double helical gearbox 10:1, ring die Ø850mm"},
                        {"Tag": "FD155", "Name": "VFD Feeder Screw", "Power": "4 kW", "Specification": "Modulates wood meal feed rate according to motor load amperage"},
                        {"Tag": "CD156", "Name": "Conditioner Mixer", "Power": "11 kW", "Specification": "WP water mist injection to 9-11% moisture, plasticizing lignin"},
                        {"Tag": "FS158, FS159", "Name": "Force Feed Screws", "Power": "2 x 1.5 kW", "Specification": "Forcibly packs sawdust into roller-die compression wedge"},
                        {"Tag": "CH137 - CH139", "Name": "Chiller Oil Cooling System", "Power": "Refrigerant unit", "Specification": "Circulating oil cooling for 355 kW main drive gearboxes"}
                    ])
                else:
                    df_m5_eq = pd.DataFrame([
                        {"Mã thiết bị": "PE1510", "Tên": "Động cơ chính máy ép (Pellet Mill)", "Công suất": "355 kW", "Thông số": "Hộp số bánh răng nghiêng kép 10:1, khuôn vòng Ø850mm"},
                        {"Mã thiết bị": "FD155", "Tên": "Vít cấp liệu biến tần (Feeder)", "Công suất": "4 kW", "Thông số": "Điều chỉnh lưu lượng bột gỗ nạp theo dòng ampe tải"},
                        {"Mã thiết bị": "CD156", "Tên": "Bộ trộn nhão (Conditioner)", "Công suất": "11 kW", "Thông số": "Phun sương nước WP đưa ẩm về 9-11%, hóa dẻo lignin"},
                        {"Mã thiết bị": "FS158, FS159", "Tên": "Vít nhồi lực cưỡng bức (Force Screw)", "Công suất": "2 x 1.5 kW", "Thông số": "Nén chặt bột mùn vào góc ép rulo - khuôn"},
                        {"Mã thiết bị": "CH137 - CH139", "Tên": "Hệ thống Chiller giải nhiệt dầu", "Công suất": "Cụm lạnh gas", "Thông số": "Làm mát tuần hoàn dầu hộp số 355kW"}
                    ])
                st.dataframe(df_m5_eq, use_container_width=True, hide_index=True)
            with c_m5_r:
                st.markdown(f"**{t('📡 Cảm Biến Bảo Vệ & Bôi Trơn Tự Động PM30-6 (9 Nam Châm):', '📡 Protection Sensors & Auto Lubrication PM30-6 (9 Magnets):')}**")
                if is_en():
                    df_m5_sn = pd.DataFrame([
                        {"Tag": "1LS / 1RS", "Name": "Shear Pin L/R Safety Switches", "Function": "Mechanical tramp metal overload trip; shears pin and stops 355kW motor instantly"},
                        {"Tag": "1LT / 1RT", "Name": "Roller Temperature Sensor", "Function": "Measures roller bearing friction heat, trips alarm if > 105°C"},
                        {"Tag": "1PS", "Name": "Grease Pulse Switch", "Function": "Verifies high-pressure lubricating grease shot delivered to roller bearings"},
                        {"Tag": "1EL", "Name": "Empty Grease Level Sensor", "Function": "Triggers alert when central lubrication reservoir runs dry"},
                        {"Tag": "1OOL", "Name": "Auto Grease Solenoid Valve", "Function": "Automates periodic greasing cycle based on operating running hours"}
                    ])
                else:
                    df_m5_sn = pd.DataFrame([
                        {"Ký hiệu": "1LS / 1RS", "Tên": "Chốt an toàn cơ khí (Shear Pin L/R)", "Chức năng": "Bảo vệ kẹt dị vật kim loại; gãy chốt ngắt ngay motor 355kW"},
                        {"Ký hiệu": "1LT / 1RT", "Tên": "Cảm biến nhiệt rulo (Roller Temp)", "Chức năng": "Đo nhiệt độ ma sát ổ bi rulo ép, cảnh báo quá nhiệt > 105°C"},
                        {"Ký hiệu": "1PS", "Tên": "Cảm biến xung mỡ (Pulse Switch)", "Chức năng": "Xác nhận mỡ bôi trơn áp suất cao đã nạp vào ổ bi rulo"},
                        {"Ký hiệu": "1EL", "Tên": "Cảm biến báo cạn mỡ (Empty Lub)", "Chức năng": "Báo động thùng mỡ trung tâm cạn, yêu cầu bổ sung mỡ"},
                        {"Ký hiệu": "1OOL", "Tên": "Van điện từ bơm mỡ tự động", "Chức năng": "Mở chu trình bơm mỡ định kỳ tự động theo giờ chạy máy"}
                    ])
                st.dataframe(df_m5_sn, use_container_width=True, hide_index=True)

        elif "Module 6" in sel_module:
            st.markdown(f"##### {t('❄️ MODULE 6: THÁP LÀM MÁT COOLER & SÀNG RUNG TÁCH CÁM (TỦ RTU#04)', '❄️ MODULE 6: COOLER TOWER & VIBRATING FINES SCREEN (RTU#04)')}")
            c_m6_l, c_m6_r = st.columns(2)
            with c_m6_l:
                st.markdown(f"**{t('⚙️ Thiết Bị Làm Nguội & Sàng Lọc Bụi Vụn:', '⚙️ Cooling & Fines Classification Equipment:')}**")
                if is_en():
                    df_m6_eq = pd.DataFrame([
                        {"Tag": "CO161", "Name": "Counter-flow Cooler Tower", "Specification": "Cools pellets from 85°C down to < 35°C"},
                        {"Tag": "FA1612", "Name": "Cooler Exhaust Fan", "Power": "90 kW", "Specification": "Forced convective airflow for counter-current cooling"},
                        {"Tag": "MD162, MD1611", "Name": "Cooler Inlet Material Spreader", "Power": "0.5 kW", "Specification": "Evenly spreads warm pellets across cooler bed area"},
                        {"Tag": "HP163", "Name": "Cooler Hydraulic Discharge Pump", "Power": "5.5 kW", "Specification": "Discharges batches of properly cooled pellets"},
                        {"Tag": "ST167, ST267", "Name": "Double-deck Vibrating Shifter", "Power": "2 x 2.88 kW", "Specification": "Screens out 100% of fines and fractured pellet dust"},
                        {"Tag": "SC1616, SC1617", "Name": "Fines Recycling Screw Conveyor", "Power": "2 x 4 kW", "Specification": "Recycles screened fines back to pelleting feed bins"}
                    ])
                else:
                    df_m6_eq = pd.DataFrame([
                        {"Mã thiết bị": "CO161", "Tên": "Tháp làm mát ngược dòng (Counter-flow Cooler)", "Thông số": "Hạ nhiệt viên nén từ 85°C xuống < 35°C"},
                        {"Mã thiết bị": "FA1612", "Tên": "Quạt hút làm mát tháp", "Công suất": "90 kW", "Thông số": "Hút gió đối lưu cưỡng bức làm nguội viên"},
                        {"Mã thiết bị": "MD162, MD1611", "Tên": "Mô tơ rải liệu đỉnh tháp mát", "Công suất": "0.5 kW", "Thông số": "Phân bổ đều viên nén trên bề mặt tháp"},
                        {"Mã thiết bị": "HP163", "Tên": "Bơm thủy lực xả đáy tháp mát", "Công suất": "5.5 kW", "Thông số": "Xả viên theo mẻ đã làm nguội đạt chuẩn"},
                        {"Mã thiết bị": "ST167, ST267", "Tên": "Sàng rung 2 tầng phân loại (Shifter)", "Công suất": "2 x 2.88 kW", "Thông số": "Tách 100% cám vụn và viên gãy vỡ"},
                        {"Mã thiết bị": "SC1616, SC1617", "Tên": "Vít tải hoàn lưu cám vụn", "Công suất": "2 x 4 kW", "Thông số": "Gom cám vụn quay ngược về phễu ép viên"}
                    ])
                st.dataframe(df_m6_eq, use_container_width=True, hide_index=True)
            with c_m6_r:
                st.markdown(f"**{t('🎯 Tiêu Chuẩn Cơ Tính Sau Khâu Làm Mát:', '🎯 Mechanical Properties Standard After Cooling:')}**")
                st.markdown(t("""
                - ❄️ **Nhiệt độ viên sau làm mát:** `< 35°C` (chênh lệch ≤ 5°C so với nhiệt độ môi trường).
                - 💎 **Độ bền cơ học (DU):** `≥ 97.5%` (chống vỡ nát khi vận chuyển đường biển dài ngày).
                - ⚖️ **Tỷ trọng viên nén:** `≥ 600 kg/m³` (tiêu chuẩn xuất khẩu Nhật Bản / Châu Âu).
                - 💧 **Độ ẩm thành phẩm:** `8.0 - 9.5%` (tối ưu hóa nhiệt trị ≥ 4.000 kcal/kg).
                - 💨 **Tách bụi vụn:** Tỷ lệ bụi cám lọt qua sàng rung `< 1.0%`.
                """, """
                - ❄️ **Pellet temp after cooling:** `< 35°C` (differential ≤ 5°C vs ambient temp).
                - 💎 **Mechanical Durability (DU):** `≥ 97.5%` (anti-degradation for long ocean transit).
                - ⚖️ **Pellet bulk density:** `≥ 600 kg/m³` (export standard for Japan / Europe).
                - 💧 **Finished product moisture:** `8.0 - 9.5%` (optimizes calorific value ≥ 4,000 kcal/kg).
                - 💨 **Fines separation:** Fines fraction passing vibrating screen `< 1.0%`.
                """))

        elif "Module 7" in sel_module:
            st.markdown(f"##### {t('📦 MODULE 7: DÒ KIM LOẠI, CÂN ĐÓNG BAO JUMBO & XUẤT HÀNG (TỦ RTU#04)', '📦 MODULE 7: METAL DETECTION, JUMBO BAGGING SCALE & DISPATCH (RTU#04)')}")
            c_m7_l, c_m7_r = st.columns(2)
            with c_m7_l:
                st.markdown(f"**{t('⚙️ Hệ Thống 4 Cân Tự Động Đóng Bao Jumbo:', '⚙️ 4-Line Automated Jumbo Bag Packing Scale System:')}**")
                if is_en():
                    df_m7_eq = pd.DataFrame([
                        {"Scale Line": "Jumbo Scale 1", "Loadcell": "LC169", "Filling Gate Cylinder": "SL169 (Solenoid S169)", "Level Switch": "HL166 (High level)"},
                        {"Scale Line": "Jumbo Scale 2", "Loadcell": "LC269", "Filling Gate Cylinder": "SL269 (Solenoid S1610)", "Level Switch": "HL266 (High level)"},
                        {"Scale Line": "Jumbo Scale 3", "Loadcell": "LC369", "Filling Gate Cylinder": "SL369 (Solenoid S369)", "Level Switch": "HL366 (High level)"},
                        {"Scale Line": "Jumbo Scale 4", "Loadcell": "LC469", "Filling Gate Cylinder": "SL469 (Solenoid S469)", "Level Switch": "HL466 (High level)"},
                        {"Outfeed Conveyors": "BE171, BE172, BE173", "Power": "15kW / 30kW with brake", "Function": "Convey filled Jumbo bags to warehouse / truck scales"}
                    ])
                else:
                    df_m7_eq = pd.DataFrame([
                        {"Hệ cân": "Hệ cân Jumbo 1", "Loadcell": "LC169", "Xylanh cửa nạp": "SL169 (Solenoid S169)", "Báo mức": "HL166 (High level)"},
                        {"Hệ cân": "Hệ cân Jumbo 2", "Loadcell": "LC269", "Xylanh cửa nạp": "SL269 (Solenoid S1610)", "Báo mức": "HL266 (High level)"},
                        {"Hệ cân": "Hệ cân Jumbo 3", "Loadcell": "LC369", "Xylanh cửa nạp": "SL369 (Solenoid S369)", "Báo mức": "HL366 (High level)"},
                        {"Hệ cân": "Hệ cân Jumbo 4", "Loadcell": "LC469", "Xylanh cửa nạp": "SL469 (Solenoid S469)", "Báo mức": "HL466 (High level)"},
                        {"Băng tải xuất": "BE171, BE172, BE173", "Công suất": "15kW / 30kW có thắng", "Chức năng": "Vận chuyển bao Jumbo ra kho thành phẩm / cân xe"}
                    ])
                st.dataframe(df_m7_eq, use_container_width=True, hide_index=True)
            with c_m7_r:
                st.markdown(f"**{t('🛡️ Kiểm Soát Tạp Chất Kim Loại & Cảng Vũng Áng:', '🛡️ Metal Contaminant Control & Vung Ang Port:')}**")
                st.markdown(t("""
                - 🧲 **Nam châm quay Rotary Magnet RMN 1 & 2:** Công suất `2 x 2.2 kW`, quay liên tục quét sạch mạt sắt mịn trước khi viên vào phễu cân.
                - 📡 **Máy dò kim loại chuyên dụng (Magnetic Testing):** Phát hiện tạp chất kim loại đen và kim loại màu sót lại, tự động phát còi báo động và kích hoạt van xả thải.
                - 🚢 **Nam châm treo băng tải Cảng Vũng Áng:** Lọc từ tính lần cuối cùng trước khi đưa viên nén xuống hầm tàu hàng xuất khẩu.
                """, """
                - 🧲 **Rotary Magnet RMN 1 & 2:** Power `2 x 2.2 kW`, continuously rotating to remove fine iron particles before weighing hopper.
                - 📡 **Dedicated Metal Detector (Magnetic Testing):** Detects residual ferrous and non-ferrous metals, auto-triggers alarm buzzer and diverter gate.
                - 🚢 **Suspended Overband Magnet at Vung Ang Port:** Final magnetic filtration stage before discharging pellets into bulk ship cargo holds.
                """))

        elif "Module 8" in sel_module:
            st.markdown(f"##### {t('⚡ MODULE 8: HỆ THỐNG AN TOÀN PCCC GRECON, TRẠM KHÍ NÉN & ĐIỆN ĐỘNG LỰC', '⚡ MODULE 8: GRECON FIRE SAFETY, CENTRAL AIR COMPRESSOR & ELECTRICAL SUBSTATION')}")
            c_m8_l, c_m8_r = st.columns(2)
            with c_m8_l:
                st.markdown(f"**{t('🚨 Hệ Thống Chữa Cháy Siêu Tốc GreCon (Đức):', '🚨 GreCon High-Speed Fire Suppression System (Germany):')}**")
                st.markdown(t("""
                - 📡 **Đầu dò hồng ngoại:** `FM 1/8` và `DLD 1/9` lắp đặt trên toàn bộ các tuyến ống bột gỗ (Line L01 - L07).
                - 💧 **Thời gian dập lửa:** `t = 0.25 giây` bằng sương cao áp góc mở 120° từ 2 bình tích áp 500L.
                - 📐 **Khoảng cách an toàn:** $S = v \times t = 30\text{ m/s} \times 0.25\text{ s} = 7.5\text{ mét}$.
                - 🛑 **Ngắt khẩn cấp:** Tự động phát lệnh ngắt `G147, G247, G347` dừng máy nghiền và lò đốt khi có trên 20 tia lửa/lần.
                """, """
                - 📡 **Infrared Detectors:** `FM 1/8` and `DLD 1/9` installed across all wood dust duct lines (Line L01 - L07).
                - 💧 **Extinguishing Time:** `t = 0.25 seconds` via 120° high-pressure water mist from dual 500L accumulator tanks.
                - 📐 **Safe Extinguishing Distance:** $S = v \times t = 30\text{ m/s} \times 0.25\text{ s} = 7.5\text{ meters}$.
                - 🛑 **Emergency Trip:** Automatically fires trip signals `G147, G247, G347` to shut down mills and burners if spark count > 20 sparks/event.
                """))
            with c_m8_r:
                st.markdown(f"**{t('⚡ Nguồn Điện & Hệ Thống Khí Nén Trung Tâm:', '⚡ Power Supply & Central Compressed Air System:')}**")
                st.markdown(t("""
                - ⚡ **2 Trạm biến áp tổng:** Trạm 1.800 kVA (cấp khối phụ trợ & văn phòng) và Trạm 8.000 kVA (cấp điện động lực 8 máy ép 355kW và 7 máy nghiền 450kW).
                - 🌬️ **Trạm khí nén trung tâm:** 2 Máy nén khí trục vít công nghiệp + Bình tích áp khép kín cấp khí giũ bụi Pulse-jet Filter và bơm mỡ khí nén.
                - 🔒 **Lockout / Tagout (LOTO):** Quy định cô lập nguồn điện tuyệt đối trước khi bảo dưỡng cơ khí.
                """, """
                - ⚡ **2 Main Transformer Substations:** 1,800 kVA (auxiliary & office) and 8,000 kVA (motor power for 8x 355kW pellet mills & 7x 450kW hammer mills).
                - 🌬️ **Central Compressed Air Station:** 2 industrial rotary screw compressors + receiver tank supplying Pulse-jet filters and pneumatic grease pumps.
                - 🔒 **Lockout / Tagout (LOTO):** Mandatory electrical isolation protocols prior to mechanical maintenance.
                """))

    # ================= TAB 3: SƠ ĐỒ BỐ TRÍ 32 ĐIỂM NAM CHÂM =================
    with tab_magnet:
        st.markdown(f"#### {t('🧲 SƠ ĐỒ BỐ TRÍ 32 ĐIỂM GẮN NAM CHÂM TÁCH TỪ (MAGNETIC SEPARATOR)', '🧲 32-POINT MAGNETIC SEPARATOR LAYOUT DIAGRAM')}")
        st.caption(t("Bản vẽ thiết kế kỹ thuật bố trí nam châm từ tính hai cực (N-S) toàn nhà máy BVN Quảng Bình (Bản vẽ CAD Rev 5.10 — Ngày 20/02/2025):", "Engineering design drawing for dipolar (N-S) magnetic separators across BVN Quang Binh plant (CAD Rev 5.10 — Feb 20, 2025):"))

        c_top1, c_top2 = st.columns([3, 1.4])
        with c_top1:
            st.markdown(t("""
            Hệ thống tách từ tính được thiết kế theo tiêu chuẩn kỹ thuật nghiêm ngặt nhằm bảo vệ tối đa máy băm, máy nghiền, máy ép và đáp ứng chất lượng xuất khẩu sang Nhật Bản & Châu Âu:
            - **Tổng số điểm lắp đặt:** `32 điểm gắn nam châm` (Magnetic Separator: 32 mounting points).
            - **Ký hiệu kỹ thuật trên bản vẽ:** Khối nam châm hai cực `[N | S]` lắp trên phễu, máng cấp và băng tải.
            - **Phân bổ 6 phân vùng công nghệ:** Băm dăm (4 điểm) ➔ Nghiền thô (10 điểm) ➔ Sấy dăm (3 điểm) ➔ Nghiền tinh (3 điểm) ➔ Ép viên (9 điểm) ➔ Sàng & Đóng bao (3 điểm).
            """, """
            Magnetic separation system is engineered to strict standards to protect chippers, hammer mills, and pellet dies, meeting export quality requirements for Japan & Europe:
            - **Total installation points:** `32 magnet mounting points` (Magnetic Separator: 32 mounting points).
            - **Drawing symbol:** Dipolar magnet blocks `[N | S]` mounted on hoppers, feed chutes, and conveyor transfer points.
            - **6 Process Zone Distribution:** Chipping (4 points) ➔ Wet Grinding (10 points) ➔ Drying (3 points) ➔ Fine Grinding (3 points) ➔ Pelleting (9 points) ➔ Screening & Bagging (3 points).
            """))
        with c_top2:
            if os.path.exists(mag_pdf_path):
                with open(mag_pdf_path, "rb") as f_pdf:
                    st.download_button(
                        label=t("📥 Tải Sơ Đồ Nam Châm (PDF Rev 5.10)", "📥 Download Magnet Diagram (PDF Rev 5.10)"),
                        data=f_pdf.read(),
                        file_name="20250220R5.10-So_do_Nam_cham-Model.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

        # Bảng dữ liệu ma trận 32 điểm
        st.markdown(f"##### {t('📋 Bảng Chi Tiết Phân Bổ 32 Điểm Nam Châm Theo 6 Phân Vùng Công Nghệ:', '📋 Detailed Allocation Matrix of 32 Magnet Points Across 6 Process Zones:')}")
        if is_en():
            df_mag_matrix = pd.DataFrame([
                {"No.": 1, "Process Zone": "Raw Wood Chipping (Zone 0)", "Drawing Area": "Wood chip processing area", "Points Count": "4 points", "Point Tags": "Points 1, 2, 3, 4", "Location & Equipment": "BE207/1013 chip conveyors combined with Stone Drawer trap"},
                {"No.": 2, "Process Zone": "Wet Wood Coarse Grinding (Zone 1)", "Drawing Area": "Wet grinding area", "Points Count": "10 points", "Point Tags": "Points 5 to 14", "Location & Equipment": "HM418 hammer mill feed inlet & HP110, HP210, HP310 feeder chutes"},
                {"No.": 3, "Process Zone": "Wet Chip / Dust Drying (Zone 2)", "Drawing Area": "Dryer area", "Points Count": "3 points", "Point Tags": "Points 15, 16, 17", "Location & Equipment": "Post-drying material handling lines from DR124 & DR224 rotary drums"},
                {"No.": 4, "Process Zone": "Dry Dust Fine Grinding (Zone 4)", "Drawing Area": "Dry grinding area", "Points Count": "3 points", "Point Tags": "Points 18, 19, 20", "Location & Equipment": "Inlets to ANDRITZ HM147, HM247, HM347 fine hammer mills"},
                {"No.": 5, "Process Zone": "PM30-6 Pellet Pressing (Zone 5)", "Drawing Area": "Pelleting area", "Points Count": "9 points", "Point Tags": "Points 21 to 29", "Location & Equipment": "Point 21 main header + Points 22–29 inlets of 8x ANDRITZ PM30-6 presses"},
                {"No.": 6, "Process Zone": "Screening & Jumbo Bagging (Zone 6-7)", "Drawing Area": "Screening area", "Points Count": "3 points", "Point Tags": "Points 30, 31, 32", "Location & Equipment": "ST167/267 vibrating screens, RMN rotary magnets & bagging scales"}
            ])
        else:
            df_mag_matrix = pd.DataFrame([
                {"STT": 1, "Khu Vực Công Nghệ": "Băm dăm nguyên liệu (Mã 0)", "Vùng Bản Vẽ (Drawing Area)": "Wood chip processing area", "Số Điểm": "4 điểm", "Danh Sách Điểm": "Điểm 1, 2, 3, 4", "Vị Trí & Thiết Bị": "Băng tải dăm băm BE207/1013 kết hợp Bẫy đá Stone Drawer"},
                {"STT": 2, "Khu Vực Công Nghệ": "Nghiền thô dăm ướt (Mã 1)", "Vùng Bản Vẽ (Drawing Area)": "Wet grinding area", "Số Điểm": "10 điểm", "Danh Sách Điểm": "Điểm 5 đến Điểm 14", "Vị Trí & Thiết Bị": "Cửa buồng nghiền búa HM418 & Vít nạp cấp liệu HP110, HP210, HP310"},
                {"STT": 3, "Khu Vực Công Nghệ": "Sấy dăm/bột ướt (Mã 2)", "Vùng Bản Vẽ (Drawing Area)": "Dryer area", "Số Điểm": "3 điểm", "Danh Sách Điểm": "Điểm 15, 16, 17", "Vị Trí & Thiết Bị": "Đường vận chuyển vật liệu sau trống sấy quay DR124 & DR224"},
                {"STT": 4, "Khu Vực Công Nghệ": "Nghiền tinh bột khô (Mã 4)", "Vùng Bản Vẽ (Drawing Area)": "Dry grinding area", "Số Điểm": "3 điểm", "Danh Sách Điểm": "Điểm 18, 19, 20", "Vị Trí & Thiết Bị": "Trước cửa vào buồng nghiền tinh ANDRITZ HM147, HM247, HM347"},
                {"STT": 5, "Khu Vực Công Nghệ": "Ép viên nén PM30-6 (Mã 5)", "Vùng Bản Vẽ (Drawing Area)": "Pelleting area", "Số Điểm": "9 điểm", "Danh Sách Điểm": "Điểm 21 đến Điểm 29", "Vị Trí & Thiết Bị": "Điểm 21 cấp liệu tổng + Điểm 22–29 cửa buồng ép của 8 máy ANDRITZ PM30-6"},
                {"STT": 6, "Khu Vực Công Nghệ": "Sàng & Đóng bao Jumbo (Mã 6-7)", "Vùng Bản Vẽ (Drawing Area)": "Screening area", "Số Điểm": "3 điểm", "Danh Sách Điểm": "Điểm 30, 31, 32", "Vị Trí & Thiết Bị": "Sàng rung phân loại ST167/267, Nam châm quay RMN & Cân đóng bao"}
            ])
        st.dataframe(df_mag_matrix, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(f"##### {t('🗺️ Bản Vẽ Kỹ Thuật Bố Trí 32 Điểm Nam Châm (Rev 5.10):', '🗺️ 32-Point Magnet Layout Engineering Drawing (Rev 5.10):')}")
        if os.path.exists(mag_img_path):
            st.image(
                mag_img_path,
                caption=t("Bản vẽ sơ đồ bố trí 32 điểm gắn nam châm (Rev 5.10) - Nhà máy sản xuất viên nén gỗ BVN Quảng Bình", "32-Point Magnet Layout Drawing (Rev 5.10) - BVN Quang Binh Wood Pellet Plant"),
                use_container_width=True
            )

    # ================= TAB 4: BẢN VẼ KỸ THUẬT P&ID GỐC =================
    with tab_raw:
        st.markdown(f"#### {t('🗺️ Bản Vẽ Kỹ Thuật P&ID AutoCAD & Tài Liệu Thiết Kế Gốc', '🗺️ AutoCAD P&ID Engineering Drawings & Original Design Docs')}")
        st.caption(t("Bản vẽ nguyên lý sơ đồ công nghệ & tự động hóa nhà máy viên nén sinh khối BVN Quảng Bình (Rev 5.5):", "Process flow & automation P&ID schematic of BVN Quang Binh biomass pellet plant (Rev 5.5):"))

        # Nút tải PDF
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label=t("📥 Tải Bản Vẽ PDF Gốc (Full Vector CAD Quality)", "📥 Download Original PDF Drawing (Full Vector CAD Quality)"),
                data=pdf_bytes,
                file_name="So_Do_Nguyen_Ly_BVN_Quang_Binh.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # Hiển thị ảnh bản vẽ gốc
        zoom_opt = [
            t("Siêu nét Ultra HD (3.168 x 2.448)", "Ultra HD (3,168 x 2,448)"),
            t("Tiêu chuẩn (1.980 x 1.530)", "Standard (1,980 x 1,530)")
        ]
        zoom_mode = st.radio(t("Độ phân giải hiển thị ảnh CAD:", "CAD Image Display Resolution:"), zoom_opt, horizontal=True, index=0)
        display_img_path = img_hd_path if ("Ultra HD" in zoom_mode or "Siêu nét" in zoom_mode) and os.path.exists(img_hd_path) else img_std_path
        if os.path.exists(display_img_path):
            st.image(
                display_img_path,
                caption=t("Bản vẽ sơ đồ nguyên lý P&ID & Tự động hóa nhà máy viên nén gỗ BVN Quảng Bình (Bao gồm Line 1 & Line 2, Trống sấy, 4 Máy nghiền, 8 Máy ép Andritz PM30-6)", "P&ID Schematic & Automation Drawing of BVN Quang Binh Wood Pellet Plant (Line 1 & 2, Drum Dryers, 4 Hammer Mills, 8 Andritz PM30-6 Pellet Mills)"),
                use_container_width=True
            )

        st.markdown("---")
        st.markdown(f"##### {t('📖 Bảng Tra Cứu Ký Hiệu Thiết Bị P&ID Toàn Nhà Máy:', '📖 Plant-wide P&ID Equipment & Sensor Symbol Legend:')}")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if is_en():
                df_leg_eq = pd.DataFrame([
                    {"Tag": "DC", "Equipment Name": "Drag Conveyor", "Type": "Scraper Flight Conveyor"},
                    {"Tag": "BE", "Equipment Name": "Belt Conveyor", "Type": "Rubber Belt Conveyor"},
                    {"Tag": "SC", "Equipment Name": "Screw Conveyor", "Type": "Auger Screw Feeder"},
                    {"Tag": "AL", "Equipment Name": "Airlock", "Type": "Rotary Air-sealed Star Valve"},
                    {"Tag": "CM", "Equipment Name": "Chipper", "Type": "Drum Wood Chipper"},
                    {"Tag": "HM", "Equipment Name": "Hammer Mill", "Type": "High-speed Hammer Mill"},
                    {"Tag": "PE", "Equipment Name": "Pellet Mill", "Type": "ANDRITZ PM30-6 Pellet Mill"},
                    {"Tag": "BN", "Equipment Name": "Burner", "Type": "PDI Biomass Furnace Burner"},
                    {"Tag": "DR", "Equipment Name": "Drum Dryer", "Type": "Triple-pass Rotary Drum Dryer"},
                    {"Tag": "CO", "Equipment Name": "Cooler", "Type": "Counter-flow Pellet Cooler"}
                ])
            else:
                df_leg_eq = pd.DataFrame([
                    {"Ký hiệu": "DC", "Tên thiết bị": "Drag Conveyor", "Tên tiếng Việt": "Xích tải cào liệu"},
                    {"Ký hiệu": "BE", "Tên thiết bị": "Belt Conveyor", "Tên tiếng Việt": "Băng tải cao su"},
                    {"Ký hiệu": "SC", "Tên thiết bị": "Screw Conveyor", "Tên tiếng Việt": "Vít tải xoắn"},
                    {"Ký hiệu": "AL", "Tên thiết bị": "Airlock", "Tên tiếng Việt": "Van sao quay xả kín gió"},
                    {"Ký hiệu": "CM", "Tên thiết bị": "Chipper", "Tên tiếng Việt": "Máy băm dăm gỗ"},
                    {"Ký hiệu": "HM", "Tên thiết bị": "Hammer Mill", "Tên tiếng Việt": "Máy nghiền búa"},
                    {"Ký hiệu": "PE", "Tên thiết bị": "Pellet Mill", "Tên tiếng Việt": "Máy ép viên nén ANDRITZ PM30-6"},
                    {"Ký hiệu": "BN", "Tên thiết bị": "Burner", "Tên tiếng Việt": "Lò đốt sinh khối PDI"},
                    {"Ký hiệu": "DR", "Tên thiết bị": "Drum Dryer", "Tên tiếng Việt": "Trống sấy quay"},
                    {"Ký hiệu": "CO", "Tên thiết bị": "Cooler", "Tên tiếng Việt": "Tháp làm nguội ngược dòng"}
                ])
            st.dataframe(df_leg_eq, use_container_width=True, hide_index=True)
        with c_p2:
            if is_en():
                df_leg_sn = pd.DataFrame([
                    {"Tag": "SP...", "Description": "Shaft Speed Sensor (Autonics PR 18-8DN)"},
                    {"Tag": "OV...", "Description": "Motor Overload Protection Relay"},
                    {"Tag": "HL / LL", "Description": "High / Low Level Switch anti-overflow/dry run"},
                    {"Tag": "OT...", "Description": "Bearing / Roller Overtemperature Sensor"},
                    {"Tag": "VB...", "Description": "Hammer Mill Vibration Sensor"},
                    {"Tag": "G...", "Description": "GreCon Automatic Spark Detection & Extinguishing"},
                    {"Tag": "DP...", "Description": "Hot Gas Balancing Damper Flap Actuator"},
                    {"Tag": "LC...", "Description": "1,000kg Jumbo Bag Scale Load Cell Sensor"}
                ])
            else:
                df_leg_sn = pd.DataFrame([
                    {"Ký hiệu": "SP...", "Ý nghĩa": "Cảm biến đo tốc độ quay trục (Autonics PR 18-8DN)"},
                    {"Ký hiệu": "OV...", "Ý nghĩa": "Rơ le phát hiện quá tải động cơ"},
                    {"Ký hiệu": "HL / LL", "Ý nghĩa": "Cảm biến báo mức cao / thấp chống tràn/cạn bunke"},
                    {"Ký hiệu": "OT...", "Ý nghĩa": "Cảm biến giám sát quá nhiệt ổ bi / rulo"},
                    {"Ký hiệu": "VB...", "Ý nghĩa": "Cảm biến báo rung chấn máy nghiền búa"},
                    {"Ký hiệu": "G...", "Ý nghĩa": "Hệ thống dò tia lửa và dập cháy tự động GreCon"},
                    {"Ký hiệu": "DP...", "Ý nghĩa": "Van lật damper điều tiết gió nóng lò sấy"},
                    {"Ký hiệu": "LC...", "Ý nghĩa": "Cảm biến lực Load cell cân đóng bao Jumbo 1000kg"}
                ])
            st.dataframe(df_leg_sn, use_container_width=True, hide_index=True)

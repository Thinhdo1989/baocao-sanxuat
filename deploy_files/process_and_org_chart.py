"""
Mô-đun hiển thị:
1. Sơ Đồ Cơ Cấu Nhân Sự Nhà Máy Viên Nén Gỗ BVN Quảng Bình (Org Chart & Roster).
2. Quy Trình Công Nghệ Chế Biến Viên Nén Sinh Khối (9 công đoạn khép kín).
3. Quy Trình Kỹ Thuật Tráng Khuôn Máy Ép Viên ANDRITZ PM30-6 (Trích xuất từ tài liệu PDF BVN Quảng Bình).
4. Tích hợp liên kết Google Sheets Quy trình chế biến (ID: 1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw).
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from typing import Dict, Any, Optional

def render_html_block(html_content: str):
    """
    Chuẩn hóa và hiển thị HTML sạch, loại bỏ khoảng trắng thụt đầu dòng và dòng trống,
    tránh hiện tượng Markdown tự động chuyển đổi thành khối mã nguồn (code block).
    """
    clean_lines = [line.strip() for line in html_content.strip().split("\n") if line.strip()]
    cleaned_html = "".join(clean_lines)
    if hasattr(st, "html"):
        st.html(cleaned_html)
    else:
        st.markdown(cleaned_html, unsafe_allow_html=True)


def render_organization_chart():
    """Hiển thị Sơ đồ cơ cấu tổ chức & Định biên nhân sự nhà máy BVN Quảng Bình"""
    st.markdown("""
    <style>
    .org-card-director {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.25);
        border: 2px solid #3b82f6;
        margin-bottom: 12px;
    }
    .org-card-dept {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .org-card-dept:hover {
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    .org-role-title {
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .org-person-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 12px;
        margin-top: 4px;
    }
    .org-sub-item {
        font-size: 12px;
        color: #475569;
        padding: 4px 0;
        border-bottom: 1px dashed #f1f5f9;
        display: flex;
        justify-content: space-between;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Thống kê tổng quan định biên
    st.markdown("### 👥 TỔNG QUAN ĐỊNH BIÊN NHÂN SỰ NHÀ MÁY")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tổng Định Biên Nhân Sự", "48 Người", "100% Khối vận hành")
    with c2:
        st.metric("Khối Sản Xuất Trực Tiếp", "36 Người", "3 Ca luân phiên 24/7")
    with c3:
        st.metric("Khối Kỹ Thuật & Bảo Trì", "6 Người", "Cơ điện & Tự động hóa")
    with c4:
        st.metric("Khối QA/QC - Kho - HSE", "6 Người", "KCS, Bãi dăm & An toàn")

    st.markdown("---")

    # 2. Sơ đồ cây phân cấp lãnh đạo
    render_html_block("""
    <div style="max-width: 540px; margin: 0 auto 20px auto;">
        <div class="org-card-director">
            <div style="font-size: 12px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 1px;">BAN LÃNH ĐẠO ĐIỀU HÀNH</div>
            <div style="font-size: 18px; font-weight: 900; margin: 4px 0;">🏢 GIÁM ĐỐC NHÀ MÁY (PLANT DIRECTOR)</div>
            <div style="font-size: 13px; color: #e2e8f0;">Phụ trách toàn diện Vận hành, An toàn, Chất lượng & Hiệu quả sản xuất</div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 13px; font-weight: 700;">
                👨‍💼 QUẢN ĐỐC PHÂN XƯỞNG SẢN XUẤT (PRODUCTION MANAGER)
            </div>
        </div>
        <div style="text-align: center; color: #94a3b8; font-size: 20px; margin-top: -8px;">▼</div>
    </div>
    """)

    # 3. Khối 4 nhánh chức năng
    col_sx, col_cd, col_qc, col_hse = st.columns(4)

    with col_sx:
        render_html_block("""
        <div class="org-card-dept" style="background: #ffffff; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; border-top: 4px solid #2563eb; display: flex; flex-direction: column; min-height: 480px;">
            <div class="org-role-title" style="font-size: 14px; font-weight: 800; color: #1e40af; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span>🏭</span> KHỐI SẢN XUẤT 3 CA
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">Vận hành dây chuyền 24/7 (36 NS)</div>
            <div style="background: #eff6ff; padding: 8px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #bfdbfe;">
                <div style="font-size: 12px; font-weight: 800; color: #1d4ed8;">🔵 CA 1: CA TRƯỞNG LONG</div>
                <div style="font-size: 11px; color: #475569;">12 KTV/công nhân • KPI: 88.5đ 🥇</div>
            </div>
            <div style="background: #f0fdf4; padding: 8px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #bbf7d0;">
                <div style="font-size: 12px; font-weight: 800; color: #15803d;">🟢 CA 2: CA TRƯỞNG SẮC</div>
                <div style="font-size: 11px; color: #475569;">12 KTV/công nhân • KPI: 86.0đ 🥈</div>
            </div>
            <div style="background: #fff7ed; padding: 8px; border-radius: 6px; margin-bottom: 10px; border: 1px solid #fed7aa;">
                <div style="font-size: 12px; font-weight: 800; color: #c2410c;">🟠 CA 3: CA TRƯỞNG TÀI</div>
                <div style="font-size: 11px; color: #475569;">12 KTV/công nhân • KPI: 82.0đ 🥉</div>
            </div>
            <div style="font-size: 11px; font-weight: 700; color: #334155; margin-top: auto; padding-top: 8px; border-top: 1px dashed #e2e8f0;">
                Vị trí trong mỗi ca:
                <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Vận hành Sấy DR124/224</span> <b>2 người</b></div>
                <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Vận hành Nghiền HM</span> <b>2 người</b></div>
                <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Vận hành Ép PM30-6</span> <b>4 người</b></div>
                <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Đóng bao & Xilo</span> <b>4 người</b></div>
            </div>
        </div>
        """)

    with col_cd:
        render_html_block("""
        <div class="org-card-dept" style="background: #ffffff; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; border-top: 4px solid #f59e0b; display: flex; flex-direction: column; min-height: 480px;">
            <div class="org-role-title" style="font-size: 14px; font-weight: 800; color: #b45309; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span>🔧</span> CƠ ĐIỆN & BẢO TRÌ
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">Kỹ thuật, PM & Quản trị 4M (6 NS)</div>
            <div style="background: #fffbeb; padding: 8px; border-radius: 6px; margin-bottom: 10px; border: 1px solid #fde68a;">
                <div style="font-size: 12px; font-weight: 800; color: #92400e;">TRƯỞNG BỘ PHẬN CƠ ĐIỆN</div>
                <div style="font-size: 11px; color: #475569;">Chỉ huy bảo trì định kỳ & phòng ngừa</div>
            </div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Tổ Cơ Khí Ép Viên</span> <b>2 KTV</b></div>
            <div style="font-size: 10px; color: #64748b; padding-left: 6px; margin-bottom: 6px;">Cân rulo, thay khuôn PM30-6, bôi trơn</div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Tổ Cơ Khí Búa & Sấy</span> <b>2 KTV</b></div>
            <div style="font-size: 10px; color: #64748b; padding-left: 6px; margin-bottom: 6px;">Đảo búa nghiền, xích tải, quạt hút</div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Tổ Điện & Tự Động Hóa</span> <b>2 KTV</b></div>
            <div style="font-size: 10px; color: #64748b; padding-left: 6px;">Tủ điện 355kW, Biến tần, PLC/SCADA</div>
        </div>
        """)

    with col_qc:
        render_html_block("""
        <div class="org-card-dept" style="background: #ffffff; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; border-top: 4px solid #10b981; display: flex; flex-direction: column; min-height: 480px;">
            <div class="org-role-title" style="font-size: 14px; font-weight: 800; color: #047857; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span>🔬</span> CHẤT LƯỢNG (KCS / QA-QC)
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">Chuẩn ISO 17225-2 / ENplus (3 NS)</div>
            <div style="background: #ecfdf5; padding: 8px; border-radius: 6px; margin-bottom: 10px; border: 1px solid #a7f3d0;">
                <div style="font-size: 12px; font-weight: 800; color: #065f46;">TRƯỞNG PHÒNG QA/QC - KCS</div>
                <div style="font-size: 11px; color: #475569;">Phụ trách chứng chỉ xuất khẩu</div>
            </div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>KTV Phòng Thí Nghiệm</span> <b>2 KTV</b></div>
            <div style="font-size: 10px; color: #64748b; padding-left: 6px; margin-bottom: 8px;">Lấy mẫu test theo ca 2 giờ/lần</div>
            <div style="margin-top: auto; font-size: 11px; background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <b style="color: #0f172a;">Chỉ tiêu kiểm soát:</b><br>
                • Độ ẩm viên: 8.0 - 9.5%<br>
                • Tỷ trọng: ≥ 600 kg/m³<br>
                • Độ tro: ≤ 1.5%<br>
                • Độ bền cơ học: ≥ 97.5%
            </div>
        </div>
        """)

    with col_hse:
        render_html_block("""
        <div class="org-card-dept" style="background: #ffffff; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; border-top: 4px solid #ef4444; display: flex; flex-direction: column; min-height: 480px;">
            <div class="org-role-title" style="font-size: 14px; font-weight: 800; color: #b91c1c; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span>🚛</span> KHO VẬN & AN TOÀN HSE
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">Bãi dăm, Cân xe & ATEX (7 NS)</div>
            <div style="background: #fef2f2; padding: 8px; border-radius: 6px; margin-bottom: 10px; border: 1px solid #fecaca;">
                <div style="font-size: 12px; font-weight: 800; color: #991b1b;">CÁN BỘ AN TOÀN LAO ĐỘNG (HSE)</div>
                <div style="font-size: 11px; color: #475569;">Kiểm soát cháy nổ bụi ATEX Zone 22</div>
            </div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Quản lý Bãi dăm & Trạm cân</span> <b>2 người</b></div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Tổ Lái Xe Xúc Lật</span> <b>3 người</b></div>
            <div class="org-sub-item" style="font-size: 12px; color: #475569; padding: 4px 0; border-bottom: 1px dashed #f1f5f9; display: flex; justify-content: space-between;"><span>Lái Xe Nâng & Xuất hàng</span> <b>2 người</b></div>
            <div style="margin-top: auto; font-size: 11px; background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <b style="color: #0f172a;">Nhiệm vụ trọng tâm:</b><br>
                • Đảo bãi chống tự bốc cháy<br>
                • Giám sát độ ẩm nguyên liệu vào<br>
                • Kiểm soát quy trình Lockout/Tagout
            </div>
        </div>
        """)

    st.markdown("---")

    # 4. Bảng Định Biên Chi Tiết & Roster Phân Ca
    with st.expander("📋 Xem Bảng Định Biên Chi Tiết Các Vị Trí & Chế Độ Trực Ca (3 Ca 4 Kíp 24/7)", expanded=False):
        df_roster = pd.DataFrame([
            {"STT": 1, "Vị trí chức danh": "Giám Đốc Nhà Máy", "Khối": "Ban Điều Hành", "Định biên": 1, "Chế độ làm việc": "Giờ hành chính (Trực 24/7)", "Nhiệm vụ chính": "Chỉ đạo toàn diện hoạt động nhà máy"},
            {"STT": 2, "Vị trí chức danh": "Quản Đốc Phân Xưởng", "Khối": "Ban Điều Hành", "Định biên": 1, "Chế độ làm việc": "Giờ hành chính (Trực ca)", "Nhiệm vụ chính": "Điều phối kế hoạch sản xuất 3 ca"},
            {"STT": 3, "Vị trí chức danh": "Ca Trưởng Sản Xuất", "Khối": "Sản Xuất", "Định biên": 3, "Chế độ làm việc": "3 ca luân phiên (8h/ca)", "Nhiệm vụ chính": "Chịu trách nhiệm toàn ca về sản lượng, điện, OEE"},
            {"STT": 4, "Vị trí chức danh": "Vận Hành Hệ Thống Sấy (DR124/224)", "Khối": "Sản Xuất", "Định biên": 6, "Chế độ làm việc": "2 người/ca x 3 ca", "Nhiệm vụ chính": "Điều khiển nhiệt gió lò sấy, kiểm soát ẩm dăm 10-12%"},
            {"STT": 5, "Vị trí chức danh": "Vận Hành Nghiền Thô & Tinh (HM)", "Khối": "Sản Xuất", "Định biên": 6, "Chế độ làm việc": "2 người/ca x 3 ca", "Nhiệm vụ chính": "Cấp liệu, kiểm soát tải dòng điện máy nghiền búa"},
            {"STT": 6, "Vị trí chức danh": "Vận Hành Cụm Ép Viên ANDRITZ PM30-6", "Khối": "Sản Xuất", "Định biên": 12, "Chế độ làm việc": "4 người/ca x 3 ca", "Nhiệm vụ chính": "Cân rulo, vận hành 8 máy ép, tráng khuôn xả dừng máy"},
            {"STT": 7, "Vị trí chức danh": "Đóng Bao Jumbo & Hệ Thống Xilo", "Khối": "Sản Xuất", "Định biên": 12, "Chế độ làm việc": "4 người/ca x 3 ca", "Nhiệm vụ chính": "Đóng bao 650kg/1000kg, cân xuất hàng, sàng tách cám"},
            {"STT": 8, "Vị trí chức danh": "Kỹ Thuật Viên Bảo Trì Cơ Khí", "Khối": "Cơ Điện", "Định biên": 4, "Chế độ làm việc": "2 ca trực + HC", "Nhiệm vụ chính": "Bảo dưỡng máy ép PM30-6, thay khuôn, cân chỉnh rulo"},
            {"STT": 9, "Vị trí chức danh": "Kỹ Thuật Viên Điện & Tự Động Hóa", "Khối": "Cơ Điện", "Định biên": 2, "Chế độ làm việc": "Hành chính & Trực sự cố", "Nhiệm vụ chính": "Xử lý biến tần, tủ điện phân phối 355kW, PLC"},
            {"STT": 10, "Vị trí chức danh": "Kỹ Thuật Viên QA/QC - KCS", "Khối": "Chất Lượng", "Định biên": 3, "Chế độ làm việc": "1 người/ca x 3 ca", "Nhiệm vụ chính": "Test độ ẩm, độ tro, tỷ trọng, độ bền cơ học DU"},
            {"STT": 11, "Vị trí chức danh": "Quản Lý Bãi Dăm & Cân Xe", "Khối": "Kho Vận", "Định biên": 2, "Chế độ làm việc": "2 ca", "Nhiệm vụ chính": "Cân nguyên liệu vào, kiểm tra chất lượng ban đầu"},
            {"STT": 12, "Vị trí chức danh": "Lái Xe Xúc Lật & Xe Nâng", "Khối": "Kho Vận", "Định biên": 5, "Chế độ làm việc": "3 ca luân phiên", "Nhiệm vụ chính": "Cấp dăm lò sấy, dăm thô phễu nạp, nâng pallet bao"},
            {"STT": 13, "Vị trí chức danh": "Cán Bộ An Toàn Lao Động (HSE)", "Khối": "An Toàn", "Định biên": 1, "Chế độ làm việc": "Giờ hành chính", "Nhiệm vụ chính": "Kiểm soát an toàn PCCC, ATEX Zone 22, Lockout/Tagout"}
        ])
        st.dataframe(df_roster, use_container_width=True, hide_index=True)


def render_wood_pellet_process_and_die_conditioning(dl, process_data: Optional[Dict[str, Any]] = None):
    """
    Hiển thị:
    1. Bảng tính & Dữ liệu Quy trình chế biến viên nén gỗ (Google Sheets ID: 1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw).
       - Khung nhúng trực tiếp tương tác Google Sheets Live qua iframe.
       - Chế độ nạp dữ liệu bảng tính phân tích (DataFrame) qua API hoặc Tệp tải lên.
       - Hướng dẫn cấp quyền Viewer 2 bước tinh gọn.
    2. Quy trình công nghệ chế biến viên nén gỗ khép kín (9 công đoạn).
    3. Quy trình kỹ thuật vận hành & tráng khuôn máy ép viên.
    """
    if 'process_data' in st.session_state and st.session_state['process_data'] is not None:
        process_data = st.session_state['process_data']
    elif process_data is None:
        process_data = dl.load_wood_pellet_process_data()
        st.session_state['process_data'] = process_data

    sheet_url = process_data.get('sheet_url', "https://docs.google.com/spreadsheets/d/1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw/edit?gid=0#gid=0")
    sheet_id = process_data.get('sheet_id', "1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw")
    service_email = process_data.get('service_email', 'bvn-reporter@boxwood-dynamo-508304-t4.iam.gserviceaccount.com')
    status = process_data.get('status', 'PENDING')
    sheets_dict = process_data.get('sheets_data', {})

    # ================= 1. KHỐI BẢNG TÍNH QUY TRÌNH CHẾ BIẾN =================
    st.markdown("### 🌲 QUY TRÌNH CHẾ BIẾN VIÊN NÉN GỖ & BẢNG TÍNH VẬN HÀNH")
    st.caption(f"Dữ liệu quy trình công nghệ kết nối Google Sheets (`{sheet_id}`) và phân tích kỹ thuật xưởng BVN Quảng Bình")

    # Thanh trạng thái & điều khiển nhanh
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2.5, 1.2, 1.3])
    with col_ctrl1:
        if status == 'CONNECTED':
            st.markdown(
                '<div style="background: rgba(34, 197, 94, 0.12); border: 1px solid #22c55e; border-radius: 8px; padding: 7px 12px; color: #15803d; font-size: 12px; font-weight: 700;">'
                '🟢 Đã đồng bộ dữ liệu thời gian thực từ Google Sheets'
                '</div>', unsafe_allow_html=True
            )
        elif status == 'LOCAL_CACHE':
            st.markdown(
                '<div style="background: rgba(59, 130, 246, 0.12); border: 1px solid #3b82f6; border-radius: 8px; padding: 7px 12px; color: #1d4ed8; font-size: 12px; font-weight: 700;">'
                '💾 Đang nạp từ tệp bảng tính lưu trữ cục bộ'
                '</div>', unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; border-radius: 8px; padding: 7px 12px; color: #b45309; font-size: 12px; font-weight: 700;">'
                '🔒 Bảng tính riêng tư trên Drive • Xem khung nhúng hoặc cấp quyền Viewer'
                '</div>', unsafe_allow_html=True
            )

    with col_ctrl2:
        if hasattr(st, "link_button"):
            st.link_button("🌐 Mở Google Sheets ↗", sheet_url, use_container_width=True)
        else:
            st.markdown(f'<a href="{sheet_url}" target="_blank" style="display: block; text-align: center; background: #2563eb; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 12px;">🌐 Mở Google Sheets ↗</a>', unsafe_allow_html=True)

    with col_ctrl3:
        if st.button("🔄 Đồng Bộ Lại API", use_container_width=True):
            new_data = dl.load_wood_pellet_process_data(force_reload=True)
            st.session_state['process_data'] = new_data
            st.rerun()

    # Các chế độ hiển thị Bảng Tính
    tab_view_embed, tab_view_table, tab_view_guide = st.tabs([
        "🖥️ Khung Nhúng Trực Tiếp (Live Preview)",
        "📊 Bảng Dữ Liệu Tương Tác (Data Table)",
        "🔑 Hướng Dẫn Cấp Quyền & Nạp Tệp Dự Phòng"
    ])

    with tab_view_embed:
        embed_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing&rm=minimal"
        components.html(f"""
        <div style="border-radius: 10px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 4px 16px rgba(0,0,0,0.12); margin-top: 6px;">
            <iframe src="{embed_url}" width="100%" height="700" style="border: none; background: #ffffff;" allowfullscreen></iframe>
        </div>
        """, height=710)
        st.caption("💡 *Ghi chú: Khung nhúng tương tác trực tiếp qua tài khoản Google trên trình duyệt của bạn. Bạn có thể xem, cuộn dữ liệu và duyệt các trang tính ngay tại đây mà không phụ thuộc vào quyền truy cập API.*")

    with tab_view_table:
        if sheets_dict:
            sheet_names = list(sheets_dict.keys())
            c_sel1, c_sel2 = st.columns([3, 1])
            with c_sel1:
                chosen_sheet = st.selectbox("📑 Chọn trang tính dữ liệu quy trình:", sheet_names, key="sb_proc_sheet")
            df_cur = sheets_dict[chosen_sheet]
            with c_sel2:
                st.metric("Tổng Dòng / Cột", f"{len(df_cur)} dòng", f"{len(df_cur.columns)} cột")
            st.dataframe(df_cur, use_container_width=True, hide_index=True)
        else:
            st.info(
                "ℹ️ **Chưa có dữ liệu phân tích dạng bảng API:** Bảng tính Google Sheets đang ở trạng thái bảo mật riêng tư trên Drive. "
                "Bạn có thể xem trực tiếp qua tab **'🖥️ Khung Nhúng Trực Tiếp'** ở trên, hoặc tải tệp Excel (.xlsx)/CSV quy trình lên bên dưới để hiển thị dạng bảng tương tác ngay lập tức."
            )
            up_f = st.file_uploader("📁 Nạp tệp Quy trình (.xlsx, .xls, .csv) từ máy tính:", type=["xlsx", "xls", "csv"], key="uploader_process_table")
            if up_f is not None:
                try:
                    excel_sheets = pd.read_excel(up_f, sheet_name=None)
                    cache_p = os.path.join(os.path.dirname(__file__), "assets", "cache_process_sheets.xlsx")
                    os.makedirs(os.path.dirname(cache_p), exist_ok=True)
                    with open(cache_p, "wb") as f_out:
                        f_out.write(up_f.getbuffer())
                    st.session_state['process_data'] = {
                        'status': 'LOCAL_CACHE',
                        'sheet_id': sheet_id,
                        'sheet_url': sheet_url,
                        'title': up_f.name,
                        'sheets_data': excel_sheets
                    }
                    st.success("✅ Nạp tệp thành công! Đang làm mới dữ liệu...")
                    st.rerun()
                except Exception as ex_load:
                    st.error(f"Lỗi nạp tệp: {ex_load}")

    with tab_view_guide:
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            st.markdown(f"""
            #### 🔑 2 Bước Cấp Quyền Đồng Bộ Nền Tự Động (API Sync):
            1. **Bước 1:** Bấm nút **[🌐 Mở Google Sheets ↗]** ở trên và nhấn nút **Chia sẻ (Share)** màu xanh tại góc trên bên phải trang tính.
            2. **Bước 2:** Chọn 1 trong 2 phương thức:
               - **Cách 1 (Nhanh nhất):** Tại mục *Quyền truy cập chung (General access)*, chuyển từ *Bị hạn chế* sang **Bất kỳ ai có đường liên kết (Anyone with the link)** với vai trò **Người xem (Viewer)**.
               - **Cách 2:** Thêm trực tiếp email tài khoản dịch vụ hệ thống bên dưới với vai trò **Người xem (Viewer)**:
            """)
            st.code(service_email, language="text")
            st.markdown("Sau khi cấp quyền xong, chỉ cần nhấn nút **[🔄 Đồng Bộ Lại API]** để hệ thống tự động nạp dữ liệu vào Dashboard.")
        with col_g2:
            st.markdown("#### 📁 Tải Tệp Dự Phòng Lên Máy Chủ:")
            st.caption("Nếu quy trình nội bộ không thể chia sẻ công khai trên Google Drive, bạn có thể tải tệp trực tiếp:")
            up_f2 = st.file_uploader("Chọn file .xlsx / .csv:", type=["xlsx", "xls", "csv"], key="uploader_process_guide")
            if up_f2 is not None:
                try:
                    excel_sheets = pd.read_excel(up_f2, sheet_name=None)
                    cache_p = os.path.join(os.path.dirname(__file__), "assets", "cache_process_sheets.xlsx")
                    os.makedirs(os.path.dirname(cache_p), exist_ok=True)
                    with open(cache_p, "wb") as f_out:
                        f_out.write(up_f2.getbuffer())
                    st.session_state['process_data'] = {
                        'status': 'LOCAL_CACHE',
                        'sheet_id': sheet_id,
                        'sheet_url': sheet_url,
                        'title': up_f2.name,
                        'sheets_data': excel_sheets
                    }
                    st.success("✅ Nạp tệp thành công! Đang làm mới dữ liệu...")
                    st.rerun()
                except Exception as ex_load:
                    st.error(f"Lỗi nạp tệp: {ex_load}")

    # 2. Quy trình công nghệ chế biến viên nén gỗ tổng thể
    st.markdown("### 🌲 QUY TRÌNH CÔNG NGHỆ CHẾ BIẾN VIÊN NÉN GỖ KHÉP KÍN (9 CÔNG ĐOẠN)")
    st.caption("Chuỗi công nghệ từ nguyên liệu dăm sinh khối đầu vào đến viên nén xuất khẩu đạt chuẩn ENplus A1 / ISO 17225-2")

    stages = [
        {"step": "01", "name": "Tiếp Nhận & Sàng Tạp Chất", "icon": "🚛", "desc": "Nguyên liệu dăm gỗ, mùn cưa qua cân xe điện tử, kiểm tra ẩm độ (40-50%). Sàng rung tách rác và nam châm vĩnh cửu hút kim loại."},
        {"step": "02", "name": "Nghiền Búa Thô (HM118 - 318)", "icon": "🔨", "desc": "Giảm kích thước dăm thô về hạt < 15mm. Kiểm soát dòng điện động cơ chính tránh quá tải, cấp liệu đều vào phễu sấy."},
        {"step": "03", "name": "Hệ Thống Sấy Quay (DR124 - 224)", "icon": "🔥", "desc": "Lò đốt tầng sôi cấp nhiệt gián tiếp/trực tiếp. Kiểm soát nhiệt gió vào (280-350°C), gió ra (80-90°C), đưa độ ẩm dăm về mức tối ưu 10.0 - 12.0%."},
        {"step": "04", "name": "Nghiền Búa Tinh (HM147 - 347)", "icon": "⚙️", "desc": "Hạt dăm khô qua sàng tinh kích thước 4 - 6mm. Tạo độ đồng nhất tối đa cho bột mùn trước khi đưa vào buồng ép."},
        {"step": "05", "name": "Điều Hòa Ẩm & Phối Trộn", "icon": "💧", "desc": "Bộ hòa trộn trục vít (Cascade Mixer / Conditioner) bổ sung hơi ẩm vi lượng hoặc nước nếu dăm quá khô, giúp hóa dẻo tự nhiên lignin ở nhiệt độ cao."},
        {"step": "06", "name": "Ép Viên Cao Áp (ANDRITZ PM30-6)", "icon": "🏭", "desc": "Cụm 8 máy ép công suất 355 kW, khuôn vòng Ø850mm. Lực nén rulo ép bột gỗ qua lỗ khuôn ở áp suất cực cao, tự sinh nhiệt >80°C liên kết viên vững chắc."},
        {"step": "07", "name": "Làm Nguội Ngược Dòng (Cooler)", "icon": "❄️", "desc": "Tháp làm nguội ngược dòng đưa nhiệt độ viên nén từ 80-90°C xuống < 35°C (gần nhiệt độ môi trường). Lignin đóng rắn hoàn toàn, tăng độ cứng vững."},
        {"step": "08", "name": "Sàng Rung Phân Loại & Tách Vụn", "icon": "🔍", "desc": "Sàng rung loại bỏ 100% cám vụn và viên gãy vỡ. Cám vụn (tỷ lệ < 1.0%) được hút hoàn lưu về phễu ép viên để tái chế biến."},
        {"step": "09", "name": "Cân Đóng Bao Jumbo & Xuất Hàng", "icon": "📦", "desc": "Đóng bao Jumbo 650kg / 1000kg có lót PE chống ẩm hoặc cấp xilo xuất hàng rời. Kiểm soát chất lượng cuối: Độ bền cơ học DU ≥ 97.5%, tỷ trọng ≥ 600 kg/m³."}
    ]

    col_st1, col_st2, col_st3 = st.columns(3)
    cols = [col_st1, col_st2, col_st3]
    for idx, stg in enumerate(stages):
        target_col = cols[idx % 3]
        with target_col:
            render_html_block(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 16px;">{stg['icon']} <b>{stg['name']}</b></span>
                    <span style="font-size: 11px; font-weight: 800; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 10px;">BƯỚC {stg['step']}</span>
                </div>
                <div style="font-size: 12px; color: #475569; line-height: 1.5;">{stg['desc']}</div>
            </div>
            """)

    st.markdown("---")

    # 3. QUY TRÌNH KỸ THUẬT VẬN HÀNH & TRÁNG KHUÔN MÁY ÉP VIÊN
    render_html_block("""
    <div style="background: linear-gradient(90deg, #1e3a8a 0%, #172554 100%); color: #ffffff; padding: 14px 20px; border-radius: 10px; margin-bottom: 16px; border-left: 6px solid #60a5fa;">
        <div style="font-size: 18px; font-weight: 900; letter-spacing: 0.5px;">🛠️ QUY TRÌNH KỸ THUẬT VẬN HÀNH & TRÁNG KHUÔN MÁY ÉP VIÊN</div>
        <div style="font-size: 12px; color: #93c5fd; margin-top: 2px;">Cụm 8 máy ép viên công suất 355 kW (PE1 - PE8) | Nhà máy Viên Nén Gỗ BVN Quảng Bình (Huyện Bố Trạch, Tỉnh Quảng Bình)</div>
    </div>
    """)

    tab_tk1, tab_tk2, tab_tk3, tab_tk4, tab_tk5 = st.tabs([
        "✨ Quy Trình 1: Tráng Mài Bóng Khuôn Mới",
        "🛑 Quy Trình 2: Tráng Xả Dừng Máy",
        "📊 Bảng Dữ Liệu Kiểm Soát Kỹ Thuật",
        "⚠️ Sự Cố Thường GẶP & Xử Lý",
        "🦺 An Toàn Lao Động (ATEX Zone 22)"
    ])

    with tab_tk1:
        st.markdown("#### I. QUY TRÌNH TRÁNG / MÀI BÓNG KHUÔN MỚI (DIE RUNNING-IN)")
        st.caption("Áp dụng: Khi thay mới khuôn hoặc sau khi tiện/mài phẳng lại bề mặt làm việc của khuôn")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("""
            ##### 1. Công thức phối trộn hỗn hợp mài bóng (Abrasive Mixture):
            - 🪵 **Bột nền mang hạt mài:** `50 kg` bột gỗ mùn cưa tinh nghiền qua sàng mịn (< 1mm) hoặc cám gạo mịn thực vật.
            - 🏖️ **Chất mài mòn (Abrasive agent):** `24 kg` cát mài kỹ thuật tiêu chuẩn (carborundum).
            - 🛢️ **Chất lỏng dẫn hướng:** `3 lít` dầu bôi trơn công nghiệp sạch (kết dính và bôi trơn thành lỗ nén).
            - 💡 *Phương án thay thế:* Dùng chính viên nén thành phẩm ngâm dầu khoáng rồi trộn đều với cát mài.
            """)
        with col_m2:
            st.markdown("""
            ##### 2. Kiểm tra lắp ráp cơ khí trước khi chạy rà:
            - 🔧 **Lực siết bu-lông khuôn:** 24 bu-lông gá khuôn M30 phải siết chéo đối xứng bằng cờ lê lực đạt **1000 Nm**.
            - 📏 **Khe hở vành mòn (Wear ring):** Kiểm tra khe hở X giữa khuôn và gờ trục chính bằng thước lá 0.2mm. Tiêu chuẩn: **0.3 mm ≤ X ≤ 1.8 mm**.
            - 🔄 **Cân chỉnh rulo (Roll adjustment):** Cân chỉnh khe hở rulo và khuôn vừa chạm nhẹ (**0.0 - 0.2 mm**) khi quay tay. Tuyệt đối không để rulo tì quá chặt vào khuôn gây mẻ kim loại.
            """)

        st.markdown("""
        ##### 3. Trình tự 5 bước vận hành mài bóng khuôn:
        1. **Bước 1: Khởi động bôi trơn & làm mát:** Kích hoạt bơm bôi trơn hộp số (áp suất dầu nguội ≥ 5 bar), mở hệ thống nước làm mát trục rulo (duy trì nhiệt độ rulo < 60°C).
        2. **Bước 2: Chạy không tải:** Khởi động động cơ chính 355kW chạy không tải trong 3 - 5 phút để kiểm tra độ đảo và độ êm của truyền động đai V (Optibelt).
        3. **Bước 3: Cấp liệu mài bóng từ từ:** Nạp hỗn hợp mài bóng từ từ qua phễu nạp liệu ở tốc độ tối thiểu (0 - 10%). Quan sát dòng điện động cơ chính (Amperage).
        4. **Bước 4: Tuần hoàn hỗn hợp:** Thu hồi hỗn hợp ép đùn ra ở cửa xả và tuần hoàn nạp lại liên tục trong **0.5 - 1 giờ**.
        5. **Bước 5: Đánh giá nghiệm thu:** Quá trình kết thúc khi 100% các lỗ nén trên bề mặt khuôn đùn viên đồng đều, bề mặt lòng lỗ đạt độ bóng nhẵn và dòng tải Ampe ổn định.
        """)

    with tab_tk2:
        st.markdown("#### II. QUY TRÌNH TRÁNG KHUÔN XẢ KHI DỪNG MÁY (SHUTDOWN FLUSHING)")
        st.warning("⚠️ **BẮT BUỘC THỰC HIỆN:** Phải tiến hành trước mỗi ca kết thúc sản xuất hoặc dừng máy nghỉ ca dài ngày. Mục đích: Đẩy toàn bộ mùn cưa thô ra khỏi lỗ nén, lấp đầy bằng viên ngâm dầu mềm để ngăn chặn nướng cứng (baking >80°C) và chống gỉ sét kẹt khuôn.")
        
        col_x1, col_x2 = st.columns(2)
        with col_x1:
            st.markdown("""
            ##### 1. Chuẩn bị nguyên liệu tráng dừng máy:
            - **Thành phần:** Viên nén thành phẩm đã ngâm dầu/nhớt công nghiệp sạch (oil-soaked pellets) hoặc hỗn hợp ngô/cám ngâm dầu.
            - ⚠️ **Lưu ý kỹ thuật sống còn:** Viên phải ngấm đều dầu nhưng **KHÔNG ĐƯỢC NGÂM QUÁ MỀM/NHÃO**. Nếu viên quá mềm sẽ mất ma sát ép, rulo sẽ bị trượt và không tạo đủ áp lực để tống xuất vật liệu thô ra ngoài.
            """)
        with col_x2:
            st.markdown("""
            ##### 2. Trình tự 5 bước dừng máy & tráng xả:
            - **Bước 1: Ngắt cấp liệu chính:** Giảm tốc độ vít định lượng về 0%, ngắt nguồn cấp nguyên liệu thô vào máy. Dừng lập tức các van cấp hơi (steam), nước và phụ gia lỏng.
            - **Bước 2: Xả sạch bộ điều hòa:** Để bộ điều hòa (cascade mixer) chạy không tải cho đến khi xả sạch hoàn toàn lượng nguyên liệu tồn dư trong máng trộn.
            - **Bước 3: Nạp viên ngâm dầu:** Đổ trực tiếp hỗn hợp viên ngâm dầu xuống máng nạp qua trục vít đôi vào buồng ép. Rulo ép sẽ nén viên dầu đẩy toàn bộ mùn thô đang nằm trong lỗ khuôn ra ngoài.
            - **Bước 4: Kiểm tra trực quan:** Quan sát cửa xả viên nén. Khi các thỏi viên đùn ra chuyển sang màu sẫm bóng đồng nhất của dầu trên toàn bộ bề mặt khuôn, xác nhận **100% các lỗ khuôn đã được điền đầy viên dầu**.
            - **Bước 5: Trình tự dừng động cơ:** Dừng trục vít cấp liệu đôi ➔ Kiểm tra cơ cấu rulo ➔ Dừng động cơ chính 355kW ➔ Dừng bơm dầu hộp số ➔ Tắt làm mát hộp số ➔ Tắt làm mát rulo.
            """)

    with tab_tk3:
        st.markdown("#### III. BẢNG THÔNG SỐ VÀ DỮ LIỆU KIỂM SOÁT KỸ THUẬT (PM30-6)")
        df_specs = pd.DataFrame([
            {"Hạng mục kiểm soát": "Mô-men siết bu-lông khuôn", "Giá trị tiêu chuẩn": "1000 Nm", "Phương pháp kiểm tra": "Cờ lê lực (24 đai ốc M30)", "Ý nghĩa kỹ thuật": "Chống lỏng bu-lông, gãy vỡ, định vị vững chắc khuôn"},
            {"Hạng mục kiểm soát": "Khe hở vành mòn (Wear ring)", "Giá trị tiêu chuẩn": "0.3 mm ≤ X ≤ 1.8 mm", "Phương pháp kiểm tra": "Thước lá căn phẳng 0.2 mm", "Ý nghĩa kỹ thuật": "Đảm bảo độ ép côn, bảo vệ trục chính"},
            {"Hạng mục kiểm soát": "Khoảng cách rulo - khuôn", "Giá trị tiêu chuẩn": "0.0 - 0.2 mm (vừa chạm nhẹ)", "Phương pháp kiểm tra": "Quay tay kiểm tra âm học", "Ý nghĩa kỹ thuật": "Tránh ma sát kim loại gây nứt mẻ khuôn/rulo"},
            {"Hạng mục kiểm soát": "Nhiệt độ trục rulo khi chạy", "Giá trị tiêu chuẩn": "< 60°C", "Phương pháp kiểm tra": "Cảm biến nhiệt độ PT100", "Ý nghĩa kỹ thuật": "Bảo vệ vòng bi rulo không bị cháy hỏng"},
            {"Hạng mục kiểm soát": "Nhiệt độ buồng ép khi dừng", "Giá trị tiêu chuẩn": "≥ 80°C", "Phương pháp kiểm tra": "Cảm biến / Đồng hồ đo", "Ý nghĩa kỹ thuật": "Cảnh báo nguy cơ nướng cứng vật liệu nếu không tráng xả"},
            {"Hạng mục kiểm soát": "Áp suất dầu bôi trơn hộp số", "Giá trị tiêu chuẩn": "≥ 5 bar (nguội) / 1.5 bar (nóng)", "Phương pháp kiểm tra": "Đồng hồ đo áp suất bơm dầu", "Ý nghĩa kỹ thuật": "Đảm bảo bôi trơn cưỡng bức bánh răng và vòng bi"},
            {"Hạng mục kiểm soát": "Mô-men bu-lông cùm tay đòn", "Giá trị tiêu chuẩn": "900 Nm (Bu-lông F)", "Phương pháp kiểm tra": "Cờ lê lực", "Ý nghĩa kỹ thuật": "Cố định trục eccentric chỉnh rulo vững chắc"},
            {"Hạng mục kiểm soát": "Tỷ lệ điền đầy lỗ khuôn khi tráng", "Giá trị tiêu chuẩn": "100% diện tích lỗ", "Phương pháp kiểm tra": "Quan sát màu viên sẫm bóng cửa xả", "Ý nghĩa kỹ thuật": "Chống gỉ sét lòng lỗ và chống kẹt máy khi tái khởi động ca sau"}
        ])
        st.dataframe(df_specs, use_container_width=True, hide_index=True)

    with tab_tk4:
        st.markdown("#### IV. CÁC LỖI THƯỜNG GẶP VÀ BIỆN PHÁP KHẮC PHỤC")
        col_err1, col_err2, col_err3 = st.columns(3)
        with col_err1:
            st.error("❌ 1. Rulo Bị Trượt Mất Tải (Roll Slippage)")
            st.markdown("""
            - **Nguyên nhân:** Viên ngâm dầu quá nhão, hoặc đổ lượng dầu quá nhiều làm rulo mất ma sát kéo quay.
            - **Biện pháp khắc phục:** Bổ sung ngay nguyên liệu thô khô hoặc cám khô có độ ẩm chuẩn để tăng ma sát kéo rulo quay lại bình thường.
            """)
        with col_err2:
            st.warning("⚠️ 2. Quá Tải Động Cơ Chính (Overload / Tripping)")
            st.markdown("""
            - **Nguyên nhân:** Hỗn hợp mài bóng quá đặc, độ ẩm không đồng đều hoặc nạp liệu vào buồng ép quá nhanh.
            - **Biện pháp khắc phục:** Lập tức giảm tốc độ cấp liệu về 0%, xả bớt liệu tồn dư và kiểm tra dòng ampe trước khi tăng tốc lại từ từ.
            """)
        with col_err3:
            st.error("🚫 3. Nghẹt Khuôn Khởi Động Ca Sau (Plugging)")
            st.markdown("""
            - **Nguyên nhân:** Tráng xả dừng máy không đạt 100% diện tích lỗ, mùn cưa thô bị nhiệt dư (>80°C) nung cứng thành đá.
            - **Biện pháp khắc phục:** Tháo buồng ép, dùng dụng cụ khoan thông lỗ chuyên dụng. **Tuyệt đối không dùng búa sắt đục phá làm hỏng gờ nén**.
            """)

    with tab_tk5:
        st.markdown("#### V. QUY ĐỊNH AN TOÀN LAO ĐỘNG (SAFETY & ATEX)")
        st.markdown("""
        - 🔥 **Cảnh báo bỏng nhiệt:** Nhiệt độ các bộ phận bên trong buồng ép và bề mặt khuôn khi dừng máy luôn vượt quá **80°C**. Bắt buộc trang bị găng tay chịu nhiệt, kính bảo hộ và trang phục bảo hộ đầy đủ khi thao tác.
        - 🏗️ **Nâng hạ vật nặng (> 1 tấn):** Khuôn và rulo có trọng lượng rất lớn (trên 1 tấn). Mọi thao tác nâng hạ, tháo lắp phải sử dụng xe treo/tời nâng chuyên dụng (Travelling Trolley / Die Crane), nghiêm cấm thao tác thủ công.
        - 💥 **An toàn chống cháy nổ bụi sinh khối (ATEX Zone 22):** Môi trường ép mùn cưa có nguy cơ cháy nổ bụi cao. Tuyệt đối không dùng dụng cụ phát sinh tia lửa điện gần khu vực buồng ép khi máy đang mở cửa.
        - 🔒 **Khóa nguồn năng lượng (Lockout / Tagout):** Bắt buộc ngắt cầu dao điện chính và treo biển cảnh báo trước khi mở cửa buồng ép bảo dưỡng cơ khí.
        """)

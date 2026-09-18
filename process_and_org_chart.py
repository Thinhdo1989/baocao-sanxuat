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


def render_organization_chart(dl: Optional[Any] = None):
    """
    Hiển thị Sơ Đồ Cơ Cấu Tổ Chức & Định Biên Nhân Sự Toàn Công Ty Cổ Phần Đầu Tư BVN Quảng Bình.
    Đồng bộ dữ liệu thời gian thực từ Google Sheets ID: 1enwVBuwwFK7k6r4i_xcg_7oJgckLaOfzNUkHPRZfY6s (gid=987654321 & 1942073054).
    """
    import plotly.express as px
    import plotly.graph_objects as go

    # 1. Nạp dữ liệu (Session state hoặc DataLoader)
    if 'hr_data' not in st.session_state or st.session_state.get('hr_data') is None:
        if dl is not None:
            hr_data = dl.load_organization_hr_data()
        else:
            try:
                from data_loader import DataLoader
                _dl = DataLoader()
                hr_data = _dl.load_organization_hr_data()
            except Exception:
                hr_data = {}
        st.session_state['hr_data'] = hr_data
    else:
        hr_data = st.session_state['hr_data']

    # Thông số cơ bản
    sheet_id = hr_data.get('sheet_id', '1enwVBuwwFK7k6r4i_xcg_7oJgckLaOfzNUkHPRZfY6s')
    sheet_url = hr_data.get('sheet_url', f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=987654321#gid=987654321")
    status = hr_data.get('status', 'LOCAL_CACHE')
    summary = hr_data.get('total_summary', {'plan': 104, 'actual': 92, 'missing': 12, 'rate': '88,46%', 'rate_num': 88.46})
    departments = hr_data.get('departments', [])
    all_roster = hr_data.get('all_roster', [])

    # CSS Giao diện hiện đại, bóng mượt, hiển thị sắc nét trên cả nền sáng và tối
    st.markdown("""
    <style>
    .org-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e2e8f0;
    }
    .org-hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
        color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 18px rgba(30, 58, 138, 0.28);
        border: 2px solid #3b82f6;
        margin: 0 auto 10px auto;
        max-width: 620px;
    }
    .org-supervisor-card {
        background: linear-gradient(135deg, #78350f 0%, #92400e 50%, #b45309 100%);
        color: #ffffff;
        border-radius: 10px;
        padding: 14px 16px;
        text-align: center;
        border: 1.5px solid #f59e0b;
        box-shadow: 0 4px 14px rgba(180, 83, 9, 0.25);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .org-director-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #2563eb 100%);
        color: #ffffff;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
        border: 1.5px solid #60a5fa;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .org-pillar-box {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .org-pillar-box:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        border-color: #3b82f6;
    }
    .org-pillar-title {
        font-size: 13.5px;
        font-weight: 800;
        padding-bottom: 6px;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .org-subcard {
        background: #f8fafc;
        border-radius: 8px;
        padding: 9px 11px;
        margin-bottom: 8px;
        border: 1px solid #e2e8f0;
    }
    .org-subcard-title {
        font-size: 12.5px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .org-subcard-lead {
        font-size: 11.5px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .org-person-item {
        font-size: 11.5px;
        color: #334155;
        padding: 3px 0;
        border-bottom: 1px dashed #f1f5f9;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .org-badge-success {
        background: #dcfce7;
        color: #15803d;
        font-size: 10.5px;
        font-weight: 700;
        padding: 1.5px 7px;
        border-radius: 12px;
        border: 1px solid #86efac;
    }
    .org-badge-warning {
        background: #fef3c7;
        color: #b45309;
        font-size: 10.5px;
        font-weight: 700;
        padding: 1.5px 7px;
        border-radius: 12px;
        border: 1px solid #fde68a;
    }
    .org-badge-danger {
        background: #fee2e2;
        color: #b91c1c;
        font-size: 10.5px;
        font-weight: 700;
        padding: 1.5px 7px;
        border-radius: 12px;
        border: 1px solid #fca5a5;
    }
    /* Tối ưu hiển thị Responsive trên Điện thoại và Tablet */
    @media (max-width: 768px) {
        .org-header-container {
            flex-direction: column !important;
            align-items: flex-start !important;
        }
        .org-hero-card, .org-supervisor-card, .org-director-card {
            padding: 12px 14px !important;
            max-width: 100% !important;
            margin-bottom: 8px !important;
            font-size: 92% !important;
        }
        .org-pillar-box {
            padding: 10px 12px !important;
            margin-bottom: 12px !important;
            font-size: 92% !important;
        }
        .org-subcard {
            padding: 7px 9px !important;
            margin-bottom: 6px !important;
        }
        .org-person-item {
            font-size: 11px !important;
        }
    }
    @media (max-width: 1024px) {
        .org-pillar-box {
            margin-bottom: 12px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # 2. Thanh tiêu đề và công cụ điều khiển
    c_title, c_act = st.columns([3, 1.2])
    with c_title:
        st.markdown("### 👥 SƠ ĐỒ CƠ CẤU TỔ CHỨC & ĐỊNH BIÊN NHÂN SỰ TOÀN CÔNG TY")
        st.caption("CÔNG TY CỔ PHẦN ĐẦU TƯ BVN QUẢNG BÌNH • NHÀ MÁY SẢN XUẤT VIÊN NÉN GỖ SINH KHỐI")
    with c_act:
        status_badge = "🟢 Google Sheets Live" if status == "CONNECTED" else "🔵 Dữ liệu Cache Offline"
        st.markdown(f"**Trạng thái:** `{status_badge}`")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("🔄 Đồng Bộ", help="Nạp lại dữ liệu trực tiếp từ Google Sheets", use_container_width=True):
                with st.spinner("Đang đồng bộ Google Sheets..."):
                    if dl is not None:
                        st.session_state['hr_data'] = dl.load_organization_hr_data(force_reload=True)
                    else:
                        from data_loader import DataLoader
                        _dl = DataLoader()
                        st.session_state['hr_data'] = _dl.load_organization_hr_data(force_reload=True)
                    st.success("Đã đồng bộ thành công!")
                    st.rerun()
        with c_b2:
            st.markdown(f'<a href="{sheet_url}" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:7px 4px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;text-decoration:none;color:#0f172a;font-weight:600;">↗️ Mở Sheet</a>', unsafe_allow_html=True)

    # 3. Thống kê 5 Chỉ số KPI Tổng quan
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Tổng Định Biên Kế Hoạch", f"{summary.get('plan', 104)} Vị trí", "11 Bộ phận toàn công ty")
    with m2:
        st.metric("Nhân Sự Đã Tiếp Nhận", f"{summary.get('actual', 92)} Người", f"Lấp đầy {summary.get('rate', '88,46%')}")
    with m3:
        st.metric("Chỉ Tiêu Còn Thiếu", f"{summary.get('missing', 12)} Vị trí", "Cần tuyển dụng bổ sung", delta_color="inverse")
    with m4:
        st.metric("Khối Sản Xuất Trực Tiếp", "51 / 57 Người", "Đạt 89.5% (Băm & Ép 3 ca)")
    with m5:
        st.metric("Khối Gián Tiếp & Nghiệp Vụ", "33 / 34 Người", "Đạt 97.1% (FSC, KD, KT, HC)")

    st.markdown("---")

    # 4. Phân tab điều hướng chức năng
    t_tree, t_kpi, t_roster, t_sheet = st.tabs([
        "🏛️ Sơ Đồ Cây Phân Cấp",
        "📊 Thống Kê & Phân Tích Định Biên",
        "📋 Danh Sách Nhân Sự & Tìm Kiếm",
        "📑 Bảng Tính Trực Tiếp (Live Google Sheets)"
    ])

    # ================= TAB 1: SƠ ĐỒ CÂY PHÂN CẤP =================
    with t_tree:
        # Cấp 1: HĐQT
        render_html_block("""
        <div class="org-hero-card">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 1px;">CƠ QUAN QUẢN TRỊ TỐI CAO</div>
            <div style="font-size: 18px; font-weight: 900; margin: 4px 0;">🏢 HỘI ĐỒNG QUẢN TRỊ (HĐQT)</div>
            <div style="font-size: 12.5px; color: #e2e8f0;">Định hướng chiến lược phát triển, nguồn vốn, công nghệ & phê duyệt mục tiêu kinh doanh</div>
        </div>
        <div style="text-align: center; color: #94a3b8; font-size: 18px; margin: -6px 0 4px 0;">▼</div>
        """)

        # Cấp 2: Ban Giám Sát & Giám Đốc Nhà Máy
        c_sup, c_dir = st.columns([1, 2.3])
        with c_sup:
            render_html_block("""
            <div class="org-supervisor-card">
                <div style="font-size: 11px; font-weight: 700; color: #fde68a; text-transform: uppercase; letter-spacing: 0.5px;">CƠ QUAN GIÁM SÁT ĐỘC LẬP</div>
                <div style="font-size: 15px; font-weight: 900; margin: 4px 0;">⚖️ BAN GIÁM SÁT / KIỂM SOÁT</div>
                <div style="font-size: 12px; color: #fef3c7;">Giám sát tuân thủ điều lệ, quy chế tài chính, định mức tiêu hao & kiểm soát rủi ro</div>
                <div style="margin-top: 8px; font-size: 11px; font-weight: 700; background: rgba(0,0,0,0.2); padding: 3px 8px; border-radius: 6px;">Trực thuộc HĐQT</div>
            </div>
            """)
        with c_dir:
            render_html_block("""
            <div class="org-director-card">
                <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px;">CƠ QUAN ĐIỀU HÀNH CAO NHẤT NHÀ MÁY</div>
                <div style="font-size: 17px; font-weight: 900; margin: 3px 0;">🏢 GIÁM ĐỐC NHÀ MÁY: ÔNG VŨ QUANG SÁNG</div>
                <div style="font-size: 12.5px; color: #e2e8f0;">Chỉ đạo & điều hành toàn diện Vận hành 24/7, An toàn, Chất lượng, Kỹ thuật & Hiệu quả sản xuất kinh doanh</div>
                <div style="margin-top: 8px; font-size: 11.5px; font-weight: 700; background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 6px; display: inline-block;">
                    Chỉ đạo trực tiếp: Phó GĐ Kinh Doanh • Kế Toán Trưởng • Trưởng Phòng HC-NS • Phó GĐ Sản Xuất
                </div>
            </div>
            """)

        render_html_block("""<div style="text-align: center; color: #94a3b8; font-size: 18px; margin: 6px 0;">▼</div>""")

        # Cấp 3: 4 Cánh tay chức năng (4 Trụ Cột)
        col_kd, col_kt, col_hc, col_sx = st.columns(4)

        # 1. KHỐI KINH DOANH & FSC
        with col_kd:
            render_html_block("""
            <div class="org-pillar-box" style="border-top: 4px solid #2563eb;">
                <div class="org-pillar-title" style="color: #1e40af;">
                    <span>💼 KHỐI KINH DOANH & FSC</span>
                    <span class="org-badge-warning">11 / 12 NS</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">Quản lý: <b>Phó Giám Đốc Kinh Doanh</b></div>

                <!-- Ban FSC -->
                <div class="org-subcard" style="border-left: 3px solid #059669;">
                    <div class="org-subcard-title" style="color: #065f46;">
                        <span>🌲 Ban Quản Lý FSC</span>
                        <span class="org-badge-success">7/7 • 100% 🥇</span>
                    </div>
                    <div class="org-subcard-lead">Trưởng ban: Trần Đặng Hiếu</div>
                    <div class="org-person-item"><span>NV FSC 1</span> <b>Lê Hữu Hoàn</b></div>
                    <div class="org-person-item"><span>NV FSC 2</span> <b>Nguyễn Văn Long</b></div>
                    <div class="org-person-item"><span>NV FSC 3</span> <b>Phan Văn Hùng</b></div>
                    <div class="org-person-item"><span>NV FSC 4</span> <b>Lê Thuận Trung</b></div>
                    <div class="org-person-item"><span>NV FSC 5</span> <b>Lê Công Tình</b></div>
                    <div class="org-person-item"><span>NV Quản lý COC</span> <b>Nguyễn Thị Diệu Thu</b></div>
                </div>

                <!-- Phòng Kinh doanh -->
                <div class="org-subcard" style="border-left: 3px solid #2563eb;">
                    <div class="org-subcard-title" style="color: #1d4ed8;">
                        <span>📈 Phòng Kinh Doanh</span>
                        <span class="org-badge-warning">4/5 • 80%</span>
                    </div>
                    <div class="org-subcard-lead">Trưởng phòng: Nguyễn Trọng Đại</div>
                    <div class="org-person-item"><span>Logistics & Thu mua</span> <b>Nguyễn Anh Tuấn</b></div>
                    <div class="org-person-item"><span>NV Thu mua 1</span> <b>Lê Minh Hiển</b></div>
                    <div class="org-person-item"><span>NV Thu mua 2</span> <b>Lê Thanh</b></div>
                    <div class="org-person-item" style="color:#b91c1c;"><span>Vị trí khuyết</span> <i>Cần tuyển 1 NS</i></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #eff6ff; padding: 7px 9px; border-radius: 6px; border: 1px solid #bfdbfe;">
                    <b>Nhiệm vụ trọng tâm:</b><br>
                    • Chứng chỉ rừng bền vững FSC & CoC<br>
                    • Thu mua nguyên liệu dăm & bao tiêu đầu ra
                </div>
            </div>
            """)

        # 2. KHỐI TÀI CHÍNH - KẾ TOÁN & CÂN XE
        with col_kt:
            render_html_block("""
            <div class="org-pillar-box" style="border-top: 4px solid #d97706;">
                <div class="org-pillar-title" style="color: #b45309;">
                    <span>💰 KHỐI TÀI CHÍNH - KẾ TOÁN</span>
                    <span class="org-badge-success">8 / 8 NS • 100% 🥇</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">Kế toán trưởng: <b>Phan Văn Tuấn</b></div>

                <!-- Bộ phận kế toán -->
                <div class="org-subcard" style="border-left: 3px solid #d97706;">
                    <div class="org-subcard-title" style="color: #92400e;">
                        <span>🏢 Nghiệp Vụ Kế Toán</span>
                        <span class="org-badge-success">5 NS</span>
                    </div>
                    <div class="org-person-item"><span>Kế toán tổng hợp 1</span> <b>Nguyễn Thị Lệ Thuần</b></div>
                    <div class="org-person-item"><span>Kế toán tổng hợp 2</span> <b>Phan Hải Yến</b></div>
                    <div class="org-person-item"><span>Kế toán LNLT</span> <b>Hồ Thị Huyền Trang</b></div>
                    <div class="org-person-item"><span>Kế toán LNBT</span> <b>Dương Thị Ánh Tuyết</b></div>
                </div>

                <!-- Trạm cân xe -->
                <div class="org-subcard" style="border-left: 3px solid #f59e0b;">
                    <div class="org-subcard-title" style="color: #b45309;">
                        <span>⚖️ Tổ Trạm Cân Xe (3 Ca)</span>
                        <span class="org-badge-success">3 NS</span>
                    </div>
                    <div class="org-person-item"><span>NV Trạm cân 1</span> <b>Trần Thị Hòa</b></div>
                    <div class="org-person-item"><span>NV Trạm cân 2</span> <b>Trương Quang Sinh</b></div>
                    <div class="org-person-item"><span>NV Trạm cân 3</span> <b>Dương Hoàng</b></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #fffbeb; padding: 7px 9px; border-radius: 6px; border: 1px solid #fde68a;">
                    <b>Nhiệm vụ trọng tâm:</b><br>
                    • Kiểm soát phiếu cân nguyên liệu & xuất hàng<br>
                    • Quản trị giá thành viên nén, chi phí điện & vật tư
                </div>
            </div>
            """)

        # 3. KHỐI HÀNH CHÍNH - NHÂN SỰ & HẬU CẦN
        with col_hc:
            render_html_block("""
            <div class="org-pillar-box" style="border-top: 4px solid #7c3aed;">
                <div class="org-pillar-title" style="color: #6d28d9;">
                    <span>👥 HÀNH CHÍNH - NHÂN SỰ</span>
                    <span class="org-badge-success">11 / 11 NS • 100% 🥇</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">Trưởng phòng: <b>Hoàng Thanh Bình</b></div>

                <!-- HC-NS -->
                <div class="org-subcard" style="border-left: 3px solid #7c3aed;">
                    <div class="org-subcard-title" style="color: #5b21b6;">
                        <span>🏢 Quản Trị Nhân Lực</span>
                        <span class="org-badge-success">2 NS</span>
                    </div>
                    <div class="org-person-item"><span>Nhân viên HC-NS</span> <b>Phan Thị Linh Hằng</b></div>
                </div>

                <!-- Bảo vệ -->
                <div class="org-subcard" style="border-left: 3px solid #8b5cf6;">
                    <div class="org-subcard-title" style="color: #6d28d9;">
                        <span>🛡️ Tổ Bảo Vệ (Trực 24/7)</span>
                        <span class="org-badge-success">3 NS</span>
                    </div>
                    <div class="org-person-item"><span>Bảo vệ 1</span> <b>Phạm Huy Bình</b></div>
                    <div class="org-person-item"><span>Bảo vệ 2</span> <b>Trần Tiến Dũng</b></div>
                    <div class="org-person-item"><span>Bảo vệ 3</span> <b>Hoàng Xuân Khương</b></div>
                </div>

                <!-- Bếp ăn & Hậu cần -->
                <div class="org-subcard" style="border-left: 3px solid #a855f7;">
                    <div class="org-subcard-title" style="color: #7e22ce;">
                        <span>🍳 Hậu Cần & Đời Sống</span>
                        <span class="org-badge-success">6 NS</span>
                    </div>
                    <div class="org-person-item"><span>Cấp dưỡng (3 NS)</span> <b>V.Hiếu, N.Hiện, T.Minh</b></div>
                    <div class="org-person-item"><span>Tạp vụ & Vệ sinh</span> <b>H.Nhung, T.Hần</b></div>
                    <div class="org-person-item"><span>Lái xe đưa đón</span> <b>Võ Chí Thanh</b></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #faf5ff; padding: 7px 9px; border-radius: 6px; border: 1px solid #e9d5ff;">
                    <b>Nhiệm vụ trọng tâm:</b><br>
                    • Đảm bảo đời sống, bữa ăn ca an toàn vệ sinh<br>
                    • An ninh trật tự, tuyển dụng bù đắp định biên
                </div>
            </div>
            """)

        # 4. KHỐI SẢN XUẤT TRỰC TIẾP & KỸ THUẬT CƠ KHÍ
        with col_sx:
            render_html_block("""
            <div class="org-pillar-box" style="border-top: 4px solid #059669;">
                <div class="org-pillar-title" style="color: #047857;">
                    <span>🏭 SẢN XUẤT & KỸ THUẬT</span>
                    <span class="org-badge-warning">62 / 70 NS • 88.6%</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">PGĐSX: <b>Đỗ Công Thịnh</b> (Chỉ huy 4 cụm)</div>

                <!-- Đội băm -->
                <div class="org-subcard" style="border-left: 3px solid #ea580c;">
                    <div class="org-subcard-title" style="color: #c2410c;">
                        <span>🪵 Đội Băm Dăm (2 Ca)</span>
                        <span class="org-badge-warning">22/24 NS</span>
                    </div>
                    <div class="org-subcard-lead">Quản lý: Phạm Văn Cường</div>
                    <div class="org-person-item"><span>Ca 1 (Tổ trưởng)</span> <b>Trần Văn Quảng (11/12)</b></div>
                    <div class="org-person-item"><span>Ca 2 (Tổ trưởng)</span> <b>Trần Mạnh Hà (11/12)</b></div>
                    <div style="font-size:10.5px; color:#64748b; padding-top:2px;">Robot, Xe cạp, Xe gắp, Máy băm, LĐPT</div>
                </div>

                <!-- Thành phẩm 3 ca -->
                <div class="org-subcard" style="border-left: 3px solid #0284c7;">
                    <div class="org-subcard-title" style="color: #0369a1;">
                        <span>⚙️ Xưởng Ép Viên (3 Ca)</span>
                        <span class="org-badge-warning">29/33 NS</span>
                    </div>
                    <div class="org-person-item"><span>Ca 1 (Trưởng ca)</span> <b>Lê Chiến Sắc (9/11)</b></div>
                    <div class="org-person-item"><span>Ca 2 (Trưởng ca)</span> <b>Hoàng Phúc Tài (10/11)</b></div>
                    <div class="org-person-item"><span>Ca 3 (Trưởng ca)</span> <b>Nguyễn Long (10/11)</b></div>
                    <div style="font-size:10.5px; color:#64748b; padding-top:2px;">VHTT, Máy ép PM30-6, Cơ khí ca, Xe xúc</div>
                </div>

                <!-- Kỹ thuật vật tư -->
                <div class="org-subcard" style="border-left: 3px solid #4f46e5;">
                    <div class="org-subcard-title" style="color: #4338ca;">
                        <span>🛠️ Kỹ Thuật - Vật Tư - KCS</span>
                        <span class="org-badge-warning">5/7 NS</span>
                    </div>
                    <div class="org-person-item"><span>Phó phòng KT</span> <b>Nguyễn Đăng Thành</b></div>
                    <div class="org-person-item"><span>Vật tư & PCCC</span> <b>Cái Viết Thanh Lâm</b></div>
                    <div class="org-person-item"><span>Kỹ sư CME / KCS</span> <b>X.Dương, K.Dung</b></div>
                </div>

                <!-- Cơ khí -->
                <div class="org-subcard" style="border-left: 3px solid #e11d48;">
                    <div class="org-subcard-title" style="color: #be123c;">
                        <span>🔩 Cơ Khí Bảo Dưỡng</span>
                        <span class="org-badge-danger">3/6 NS (50%)</span>
                    </div>
                    <div class="org-person-item"><span>Tổ trưởng cơ khí</span> <b>Phan Nhớ</b></div>
                    <div class="org-person-item"><span>Thợ cơ khí chính</span> <b>M.Tuấn, V.Huy</b></div>
                    <div class="org-person-item" style="color:#b91c1c;"><span>Còn khuyết</span> <i>Thiếu 3 thợ cơ khí</i></div>
                </div>
            </div>
            """)

    # ================= TAB 2: THỐNG KÊ & PHÂN TÍCH ĐỊNH BIÊN =================
    with t_kpi:
        st.markdown("#### 📊 Ma Trận Định Biên Kế Hoạch vs Nhân Sự Thực Tế Theo Bộ Phận")
        
        # Chuẩn bị DataFrame thống kê
        chart_rows = []
        for d in departments:
            chart_rows.append({
                'Bộ Phận': d['department'],
                'Kế Hoạch': d['plan'],
                'Thực Tế': d['actual'],
                'Còn Thiếu': d['missing'],
                'Tỉ Lệ (%)': d.get('rate_num', round(d['actual']/d['plan']*100, 1) if d['plan'] > 0 else 0),
                'Người Phụ Trách': d.get('manager', ''),
                'Khối Trực Thuộc': d.get('parent', 'PGĐSX')
            })
        df_chart = pd.DataFrame(chart_rows)

        col_g1, col_g2 = st.columns([1.6, 1.4])

        with col_g1:
            fig_bar = px.bar(
                df_chart,
                x='Bộ Phận',
                y=['Thực Tế', 'Còn Thiếu'],
                title="So Sánh Định Biên: Nhân Sự Thực Tế vs Còn Thiếu (Người)",
                color_discrete_map={'Thực Tế': '#10b981', 'Còn Thiếu': '#ef4444'},
                barmode='stack',
                text_auto=True
            )
            fig_bar.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=80), xaxis_tickangle=-35)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            fig_rate = px.bar(
                df_chart.sort_values(by='Tỉ Lệ (%)', ascending=True),
                x='Tỉ Lệ (%)',
                y='Bộ Phận',
                orientation='h',
                title="Tỉ Lệ Hoàn Thành Định Biên (%)",
                color='Tỉ Lệ (%)',
                color_continuous_scale='RdYlGn',
                text='Tỉ Lệ (%)'
            )
            fig_rate.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_rate.add_vline(x=100, line_dash="dash", line_color="green", annotation_text="100% Đủ định biên")
            fig_rate.update_layout(height=400, margin=dict(l=10, r=20, t=40, b=20))
            st.plotly_chart(fig_rate, use_container_width=True)

        # Bảng chi tiết
        st.markdown("##### 📋 Bảng Định Biên Toàn Bộ 11 Đơn Vị Công Ty")
        st.dataframe(
            df_chart[['Bộ Phận', 'Khối Trực Thuộc', 'Người Phụ Trách', 'Kế Hoạch', 'Thực Tế', 'Còn Thiếu', 'Tỉ Lệ (%)']],
            use_container_width=True,
            hide_index=True
        )

    # ================= TAB 3: DANH SÁCH NHÂN SỰ & TÌM KIẾM =================
    with t_roster:
        st.markdown("#### 📋 Tra Cứu Danh Sách Cán Bộ Nhân Viên Toàn Nhà Máy")
        
        # Bộ lọc
        cf1, cf2, cf3 = st.columns([1.5, 1.2, 2])
        dept_list = ["Tất cả"] + [d['department'] for d in departments]
        with cf1:
            sel_dept = st.selectbox("Lọc theo Bộ phận / Phân xưởng:", dept_list)
        with cf2:
            sel_status = st.selectbox("Lọc theo Trạng thái:", ["Tất cả", "Đã có nhân sự", "Vị trí còn trống (Cần tuyển)"])
        with cf3:
            kw = st.text_input("🔍 Tìm kiếm theo Họ Tên hoặc Vị Trí:", placeholder="VD: Sắc, Long, Cơ khí, Robot...")

        # Lọc danh sách
        filtered_roster = []
        for idx, item in enumerate(all_roster, 1):
            d_match = (sel_dept == "Tất cả" or item['department'] == sel_dept)
            
            s_match = True
            if sel_status == "Đã có nhân sự":
                s_match = (item['status'] == 'Đã có')
            elif sel_status == "Vị trí còn trống (Cần tuyển)":
                s_match = (item['status'] == 'Còn trống')
                
            k_match = True
            if kw.strip():
                k_lower = kw.strip().lower()
                target_str = f"{item['department']} {item['position']} {item['name']}".lower()
                k_match = (k_lower in target_str)

            if d_match and s_match and k_match:
                filtered_roster.append({
                    "STT": len(filtered_roster) + 1,
                    "Bộ Phận / Đội": item['department'],
                    "Vị Trí Chức Danh": item['position'],
                    "Họ Và Tên": item['name'],
                    "Trạng Thái": item['status'],
                    "Ghi Chú Vận Hành": item.get('raw', '')
                })

        st.caption(f"Tìm thấy **{len(filtered_roster)}** vị trí / nhân sự phù hợp.")
        if filtered_roster:
            df_display = pd.DataFrame(filtered_roster)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Tải về CSV
            csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Tải Danh Sách Nhân Sự (CSV)",
                data=csv_data,
                file_name="Danh_sach_nhan_su_BVN_Quang_Binh.csv",
                mime="text/csv"
            )
        else:
            st.info("Không tìm thấy nhân sự phù hợp với tiêu chí lọc.")

    # ================= TAB 4: BẢNG TÍNH TRỰC TIẾP =================
    with t_sheet:
        st.markdown("#### 📑 Bảng Tính Nhân Sự & Cơ Cấu Trực Tiếp (Google Sheets Live)")
        st.caption("Xem hoặc chỉnh sửa trực tiếp dữ liệu nhân sự trên trang tính `Gốc Dữ liệu Sơ đồ khối` (gid=987654321) và `Định biên nhân sự` (gid=1942073054)")

        c_link1, c_link2, c_link3 = st.columns(3)
        with c_link1:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=987654321#gid=987654321" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;font-size:12.5px;font-weight:700;color:#1d4ed8;text-decoration:none;">↗️ Tab Gốc Sơ Đồ Khối (gid=987654321)</a>', unsafe_allow_html=True)
        with c_link2:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=1942073054#gid=1942073054" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;font-size:12.5px;font-weight:700;color:#15803d;text-decoration:none;">↗️ Tab Định Biên Nhân Sự (gid=1942073054)</a>', unsafe_allow_html=True)
        with c_link3:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=1408180321#gid=1408180321" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:6px;font-size:12.5px;font-weight:700;color:#7e22ce;text-decoration:none;">↗️ Tab Hằng - Sơ Đồ Nhân Sự (gid=1408180321)</a>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        embed_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=987654321&rm=minimal"
        components.iframe(embed_url, height=650, scrolling=True)


def render_wood_pellet_process_and_die_conditioning(dl, process_data: Optional[Dict[str, Any]] = None):
    """
    Hiển thị Quy trình công nghệ sản xuất viên nén gỗ khép kín tại Nhà máy BVN Quảng Bình.
    Định chuẩn theo Tài liệu Kỹ thuật Vận hành Chuẩn (SOP) — Mã hóa công đoạn 0 đến 7:
    Google Docs: https://docs.google.com/document/d/1WpwcIaK0o8oX0sQHuYsHtSKPQnVeCRb5Qnca8mi5b9M/edit?tab=t.0
    Cơ sở Thiết bị: ANDRITZ (Đan Mạch/Áo) • PDI (Mỹ) • GreCon (Đức).
    """
    doc_id = "1WpwcIaK0o8oX0sQHuYsHtSKPQnVeCRb5Qnca8mi5b9M"
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit?tab=t.0"
    doc_preview_url = f"https://docs.google.com/document/d/{doc_id}/preview"

    # CSS Chuyên biệt cho Quy Trình Kỹ Thuật
    st.markdown("""
    <style>
    .proc-header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
        color: #ffffff;
        border-radius: 12px;
        padding: 16px 22px;
        border: 2px solid #3b82f6;
        box-shadow: 0 4px 18px rgba(30, 58, 138, 0.25);
        margin-bottom: 14px;
    }
    .proc-banner-title {
        font-size: 19px;
        font-weight: 900;
        letter-spacing: 0.5px;
        margin: 2px 0 4px 0;
    }
    .proc-banner-sub {
        font-size: 12.5px;
        color: #bfdbfe;
    }
    .proc-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .proc-card:hover {
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border-color: #3b82f6;
    }
    .proc-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1.5px solid #f1f5f9;
    }
    .proc-badge-code {
        font-size: 11px;
        font-weight: 800;
        background: #eff6ff;
        color: #1d4ed8;
        padding: 2px 9px;
        border-radius: 12px;
        border: 1px solid #bfdbfe;
    }
    .proc-equip-badge {
        font-size: 11px;
        font-weight: 700;
        background: #f8fafc;
        color: #334155;
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    /* Tối ưu hiển thị Responsive trên Điện thoại và Tablet */
    @media (max-width: 768px) {
        .proc-header-banner {
            padding: 12px 14px !important;
        }
        .proc-banner-title {
            font-size: 15px !important;
        }
        .proc-banner-sub {
            font-size: 11px !important;
            line-height: 1.4 !important;
        }
        .proc-card {
            padding: 10px 12px !important;
            margin-bottom: 10px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Header Banner
    render_html_block(f"""
    <div class="proc-header-banner">
        <div style="font-size: 11px; font-weight: 800; color: #93c5fd; text-transform: uppercase; letter-spacing: 1px;">
            TÀI LIỆU KỸ THUẬT VẬN HÀNH CHUẨN (SOP) • NHÀ MÁY BVN QUẢNG BÌNH
        </div>
        <div class="proc-banner-title">🌲 QUY TRÌNH CÔNG NGHỆ SẢN XUẤT VIÊN NÉN GỖ SINH KHỐI</div>
        <div class="proc-banner-sub">
            Cơ sở Thiết bị: <b>ANDRITZ</b> (Đan Mạch/Áo) • <b>PDI</b> (Mỹ) • <b>GreCon</b> (Đức) | Định chuẩn theo Sơ đồ Mã hóa Công đoạn 0 đến 7
        </div>
    </div>
    """)

    # Nút liên kết và trạng thái
    c_btn1, c_btn2 = st.columns([3.5, 1.5])
    with c_btn1:
        st.markdown(
            '<div style="background: #eff6ff; border-left: 5px solid #2563eb; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #1e293b;">'
            '<b style="color: #1d4ed8; font-size: 12.5px;">💡 ĐÍNH CHÍNH QUAN TRỌNG VỀ TRÌNH TỰ CÔNG NGHỆ:</b> '
            'Tại BVN Quảng Bình, khâu <b>NGHIỀN THÔ (Mã 1)</b> diễn ra <b>TRƯỚC SẤY</b> đối với dăm tươi/ướt (nhân đôi hiệu suất bốc hơi), và '
            '<b>NGHIỀN TINH (Mã 4)</b> diễn ra <b>SAU SẤY</b> đối với vật liệu khô trước khi ép viên.'
            '</div>', unsafe_allow_html=True
        )
    with c_btn2:
        st.markdown(
            f'<a href="{doc_url}" target="_blank" style="display:block; text-align:center; padding:10px 12px; background:#1e40af; color:#ffffff; font-weight:700; font-size:12.5px; border-radius:8px; text-decoration:none; box-shadow: 0 2px 6px rgba(30,58,138,0.3);">'
            '📄 Mở Tài Liệu SOP (Google Docs) ↗</a>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tổng Công Suất Nhà Máy", "150.000 Tấn/Năm", "Thực tế vận hành: 100.000 tấn")
    with c2:
        st.metric("Cụm Máy Nghiền Sinh Khối", "7 Tuyến Máy Lớn", "4 Nghiền thô HM418 + 3 Nghiền tinh HM147-347")
    with c3:
        st.metric("Cụm 8 Máy Ép ANDRITZ", "8 × 355 kW", "Model PM30-6 • Hộp số kép 10:1")
    with c4:
        st.metric("An Toàn & Tách Từ", "32 Cụm Nam Châm", "GreCon dập lửa t = 0.25s • 5 Lớp tách từ")

    st.markdown("---")

    # 4 Sub-Tabs Chức Năng
    tab_flow, tab_safety, tab_mold, tab_doc = st.tabs([
        "🔄 Chuỗi 7 Bước Công Nghệ (Mã 0 ➔ Mã 7)",
        "🛡️ Hệ Thống An Toàn Phòng Nổ & Tách Từ Tính",
        "🛠️ Kỹ Thuật Vận Hành & Tráng Khuôn ANDRITZ PM30-6",
        "📑 Tra Cứu Toàn Văn Tài Liệu SOP (Google Docs Live)"
    ])

    # ================= TAB 1: CHUỖI 7 BƯỚC CÔNG NGHỆ =================
    with tab_flow:
        st.markdown("#### 🔄 Trình Tự Vật Lý Dòng Nguyên Liệu Khép Kín (Mã Vùng 0 Đến Mã Vùng 7)")

        # Bảng tóm tắt phân vùng
        df_zones = pd.DataFrame([
            {"Mã Vùng": "Mã 0", "Tên Công Đoạn": "Băm Dăm Nguyên Liệu", "Thiết Bị Cốt Lõi": "Máy băm CM108-CM2011, Băng tải BE, Xích tải DC", "Mục Tiêu Công Nghệ": "Chuyển gỗ cây/gỗ khúc thành dăm gỗ kích thước chuẩn"},
            {"Mã Vùng": "Mã 1", "Tên Công Đoạn": "Nghiền Thô Dăm Ướt", "Thiết Bị Cốt Lõi": "Máy nghiền búa HM118-HM418 (400-450kW), Feeder FD", "Mục Tiêu Công Nghệ": "Hạ kích thước dăm tươi/ướt trước khi đưa vào sấy"},
            {"Mã Vùng": "Mã 2", "Tên Công Đoạn": "Sấy Dăm/Bột Ướt", "Thiết Bị Cốt Lõi": "Trống sấy quay DR124/DR224, Lò đốt PDI Burner, Quạt FA", "Mục Tiêu Công Nghệ": "Giảm độ ẩm vật liệu từ ~45% xuống còn 12-15%"},
            {"Mã Vùng": "Mã 4", "Tên Công Đoạn": "Nghiền Tinh Bột Khô", "Thiết Bị Cốt Lõi": "Máy nghiền tinh HM147-HM347 (450kW), Lọc bụi FI", "Mục Tiêu Công Nghệ": "Nghiền bột gỗ khô đạt độ mịn đều chuẩn bị ép viên"},
            {"Mã Vùng": "Mã 5", "Tên Công Đoạn": "Ép Viên & Phụ Trợ", "Thiết Bị Cốt Lõi": "8 máy ép ANDRITZ PM30-6 (PE1510-8510), Condition CD", "Mục Tiêu Công Nghệ": "Ép định hình viên nén sinh khối, làm mát dầu/bôi trơn"},
            {"Mã Vùng": "Mã 6", "Tên Công Đoạn": "Làm Mát & Sàng", "Thiết Bị Cốt Lõi": "Tháp làm mát Cooler MD1520/2520, Sàng rung ST167/267", "Mục Tiêu Công Nghệ": "Hạ nhiệt viên nén, ổn định độ cứng và tách bụi vụn"},
            {"Mã Vùng": "Mã 7", "Tên Công Đoạn": "Đóng Bao & Xuất Hàng", "Thiết Bị Cốt Lõi": "Nam châm RMN, Máy dò kim loại, Cân Jumbo LC169-469", "Mục Tiêu Công Nghệ": "Kiểm soát tạp chất kim loại cuối, đóng bao & xuất bến"}
        ])
        st.dataframe(df_zones, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 7 Process Cards chi tiết theo Sơ đồ Bố trí 32 Điểm Nam châm Rev 5.10
        steps_data = [
            {
                "step": "BƯỚC 1", "code": "MÃ VÙNG 0", "icon": "🪵", "color": "#0284c7",
                "title": "Tiếp Nhận Nguyên Liệu, Băm Dăm & Tách Tạp Chất Sơ Cấp",
                "equip": ["Cẩu gắp nạp gỗ", "Máy băm CM108–CM2011", "Xích tải DC203/204/206", "Băng tải BE207/1013", "Sàn trượt thủy lực HP137-139", "4 Điểm nam châm (Điểm 1-4)", "Bẫy đá Stone Drawer"],
                "content": """
                • <b>Nguồn nguyên liệu đầu vào:</b> Cây gỗ và phế phụ phẩm lâm nghiệp có chứng chỉ FSC, kiểm soát chặt bởi KCS từ khâu thu mua, hạ tải đến phân loại.<br>
                • <b>Công đoạn băm dăm:</b> Cẩu gắp nạp gỗ vào tuyến máy băm CM108–CM1011 (Line 1) và CM208–CM2011 (Line 2). Hệ thống dao băm quay tốc độ cao cắt gỗ thành lát dăm đồng đều.<br>
                • <b>Chứa liệu & Kiểm soát tạp chất:</b> Dăm đưa về kho dăm tươi trang bị sàn trượt thủy lực HP137-HP139. Tuyến băng tải bố trí <b>4 điểm nam châm tách từ (Điểm 1 đến Điểm 4)</b> kết hợp <b>Bẫy đá (Stone Drawer)</b> loại bỏ mạt sắt lớn, đinh rác và sỏi đá, bảo vệ an toàn cho máy nghiền phía sau.
                """
            },
            {
                "step": "BƯỚC 2", "code": "MÃ VÙNG 1", "icon": "🔨", "color": "#ea580c",
                "title": "Nghiền Thô Dăm Ướt (Wet Grinding Area — Diễn Ra TRƯỚC Sấy)",
                "equip": ["Sàn trượt thủy lực", "Vít tải SC112, SC211, SC212", "Vít cấp liệu FD115-FD217", "Cụm máy nghiền búa HM418 (400-450kW)", "10 Điểm nam châm (Điểm 5-14)"],
                "content": """
                • <b>Cấp liệu dăm ướt:</b> Dăm gỗ tươi từ kho được sàn trượt thủy lực đẩy sang vít tải và vít cấp liệu nạp vào cụm máy nghiền thô.<br>
                • <b>Công nghệ nghiền dăm ướt:</b> Sử dụng cụm máy nghiền búa ANDRITZ HM418 công suất lớn <b>400kW - 450kW</b> đánh tan lát dăm gỗ ẩm thành hạt nhỏ xốp. Việc nghiền thô dăm ướt trước khi sấy giúp làm <b>tăng diện tích bề mặt tiếp xúc nhiệt, tăng gấp đôi hiệu suất bốc hơi nước</b> khi đi vào trống sấy.<br>
                • <b>Mật độ tách từ dày đặc:</b> Bố trí tới <b>10 điểm nam châm lọc sắt (Điểm 5 đến Điểm 14)</b> tại các vị trí cửa buồng nghiền búa HM418 & các phễu nạp/vít cấp liệu HP110, HP210... triệt hạ tối đa dị vật kim loại từ khâu băm trước khi vào sấy.
                """
            },
            {
                "step": "BƯỚC 3", "code": "MÃ VÙNG 2", "icon": "🔥", "color": "#dc2626",
                "title": "Sấy Dăm/Bột Ướt (Dryer Area — Công Nghệ Lò Đốt PDI Mỹ)",
                "equip": ["Trống sấy quay DR124 & DR224 (315kW)", "Lò đốt PDI Burner 1 & 2", "Quạt thổi FA1211", "Quạt hút quăng FA127/227", "Van làm nguội DP1214", "Van PID DP1217", "3 Điểm nam châm tuyến sấy (Điểm 15-17)"],
                "content": """
                • <b>Nạp liệu trống sấy:</b> Vật liệu xốp ẩm sau nghiền thô được xích tải đưa vào 2 trống sấy quay DR124 & DR224 (công suất 315kW).<br>
                • <b>Cung cấp nhiệt & Kiểm soát áp suất:</b> Lò đốt PDI Burner 1 & 2 cấp khí nóng. Nhiệt độ đỉnh lò T122 được kiểm soát qua van làm nguội DP1214 (ngưỡng ngắt an toàn T121 ≤ 1200°C). Quạt thổi FA1211 duy trì áp suất lò P121 = 9–10 mbar; Quạt hút quăng FA127/227 duy trì chênh áp P124 = 10 mbar.<br>
                • <b>Điều khiển nhiệt & Độ ẩm ngõ ra:</b> Nhiệt độ ngõ ra tự động khống chế dưới 149°C qua van PID DP1217; Tuần hoàn khí nóng hồi tiếp qua van DP1216 tiết kiệm nhiên liệu. <b>Độ ẩm nguyên liệu hạ từ ~45% xuống đạt chuẩn 12% - 15%</b>. Bố trí <b>3 điểm nam châm (Điểm 15, 16, 17)</b> trên tuyến vận chuyển sau sấy.
                """
            },
            {
                "step": "BƯỚC 4", "code": "MÃ VÙNG 4", "icon": "⚙️", "color": "#7c3aed",
                "title": "Nghiền Tinh Bột Khô (Dry Grinding Area — Diễn Ra SAU Sấy)",
                "equip": ["Xích tải phân phối SC141", "Van sao cách gió Airlock AL", "Vít cấp liệu FD143-FD343", "3 Máy nghiền tinh ANDRITZ HM147-347 (450kW)", "3 Điểm nam châm nghiền tinh (Điểm 18-20)", "Quạt hút FA1410-3410 (110kW)", "Lọc bụi Pulse-jet Filter FI1410-3410"],
                "content": """
                • <b>Phân phối liệu khô:</b> Vật liệu khô sau sấy đi qua xích tải phân phối, van sao cách gió và vít cấp liệu nạp vào 3 tuyến máy nghiền tinh.<br>
                • <b>Nghiền mịn bột gỗ:</b> Hệ thống gồm 3 máy nghiền tinh ANDRITZ HM147, HM247, HM347 (công suất <b>450kW/máy</b>). Rô-to quay tốc độ cao nghiền hạt gỗ khô thành bột gỗ mịn đồng đều, đạt kích thước nhỏ hơn đường kính lỗ khuôn ép viên.<br>
                • <b>Bảo vệ chống tia lửa & Tách từ:</b> Bố trí <b>3 điểm nam châm tách từ (Điểm 18, 19, 20)</b> trước các buồng máy nghiền tinh HM147, HM247, HM347 để ngăn chặn tuyệt đối mạt sắt ma sát sinh nhiệt gây cháy nổ bụi.<br>
                • <b>Thu hồi bột & Lọc bụi môi trường:</b> Mỗi máy nghiền đi kèm quạt hút 110kW và bộ lọc túi khí nén Pulse-jet Filter FI1410-3410 thu hồi 100% bột gỗ mịn, khí thải ra môi trường sạch hoàn toàn.
                """
            },
            {
                "step": "BƯỚC 5", "code": "MÃ VÙNG 5", "icon": "🏭", "color": "#059669",
                "title": "Trộn Nhão, Ép Viên Nén & Phụ Trợ (Pelleting Area — ANDRITZ PM30-6)",
                "equip": ["Vít cấp liệu SC151", "Bộ trộn nhão Conditioner CD156-856 (11kW)", "Bơm phun sương WP", "8 Máy ép ANDRITZ PM30-6 (355kW)", "Chiller giải nhiệt dầu CH137-139", "Bơm mỡ tự động 1LP-8LP", "9 Điểm nam châm ép viên (Điểm 21-29)"],
                "content": """
                • <b>Điều hòa ẩm (Conditioning):</b> Bột gỗ qua máy trộn nhão Conditioner (11kW) kết hợp hệ thống bơm nước WP phun sương bổ sung độ ẩm tối ưu (đạt <b>9-11% khi vào khuôn</b>). Vít ép lực Force Screw FS nạp bột nhão đều vào buồng ép.<br>
                • <b>Cụm 8 máy ép ANDRITZ PM30-6:</b> Động cơ <b>355kW/máy</b> trang bị hộp số giảm tốc kép tỷ số 10:1 hiệu suất cao. Rulo ép chặt bột gỗ qua lỗ khuôn Die định hình viên nén đường kính 6mm - 8mm. Dao cắt điều chỉnh chiều dài viên.<br>
                • <b>Phụ trợ tự động & Lọc từ:</b> Bố trí <b>9 điểm nam châm (Điểm 21 nạp liệu tổng + Điểm 22 đến 29 tại cửa buồng 8 máy ép PM30-6)</b>. Hệ thống Chiller giải nhiệt dầu hộp số; Bơm mỡ tự động khí nén 1LP-8LP kết hợp cảm biến xung 1PS-8PS tự động bôi trơn liên tục.
                """
            },
            {
                "step": "BƯỚC 6", "code": "MÃ VÙNG 6", "icon": "❄️", "color": "#0284c7",
                "title": "Làm Mát & Sàng Phân Loại Viên Nén (Cooling & Screening Area)",
                "equip": ["Gàu tải đứng BC1514, BC2514", "Tháp làm mát Cooler MD1520, MD2520", "Quạt hút ngược chiều FA132, FA153", "Sàng rung phân loại ST167, ST267", "3 Điểm nam châm sàng & đóng bao (Điểm 30-32)"],
                "content": """
                • <b>Vận chuyển viên nóng:</b> Viên nén bước ra khỏi máy ép có nhiệt độ cao (80°C - 90°C) được gàu tải vận chuyển đưa lên đỉnh tháp làm mát Cooler.<br>
                • <b>Làm mát hạ nhiệt & Đóng rắn lignin:</b> Không khí mát được quạt hút thổi ngược chiều qua lớp viên nén, hạ nhiệt độ viên xuống gần nhiệt độ môi trường (< 35°C), giúp nhựa gỗ lignin tự nhiên đông đặc, tạo độ cứng rắn và độ bền cơ học DU ≥ 97.5%.<br>
                • <b>Sàng rung tách vụn:</b> Viên nén xả xuống sàng rung ST167/267 loại bỏ 100% cám vụn và viên gãy. Cám vụn được quạt hút hút tuần hoàn quay trở lại khâu ép viên. Trang bị <b>3 điểm nam châm tách từ (Điểm 30, 31, 32)</b> tại khu vực sàng và cân xuất.
                """
            },
            {
                "step": "BƯỚC 7", "code": "MÃ VÙNG 7", "icon": "📦", "color": "#16a34a",
                "title": "Dò Kim Loại, Cân Đóng Bao Jumbo & Xuất Bến (Packaging & Shipping)",
                "equip": ["Băng tải chuyển liệu BE171, BE173", "Nam châm quay Rotary Magnet RMN", "Máy dò kim loại Magnetic Testing Machine", "Cảm biến báo mức HL166/266", "Van 2 ngả TW1517/167", "Hệ thống cân Jumbo Load cell LC169-469", "Nam châm treo Cảng Vũng Áng"],
                "content": """
                • <b>Kiểm soát kim loại tinh 100%:</b> Trước khi vào phễu đóng bao, viên nén đi qua Nam châm quay Rotary Magnet RMN (Điểm 30-32) và Máy dò kim loại chuyên dụng để đảm bảo tuyệt đối không còn bất kỳ mạt kim loại nào sót lại.<br>
                • <b>Cân đóng bao Jumbo tự động:</b> Viên nén nạp vào phễu chứa có cảm biến báo đầy. Van 2 ngả và cửa trượt điều tiết liệu xuống hệ thống cân điện tử Load cell thực hiện đóng bao Jumbo <b>1.000 kg/bao</b> tự động.<br>
                • <b>Xuất hàng & Lọc sắt Cảng Vũng Áng:</b> Bao Jumbo thành phẩm được cẩu gắp xếp kho hoặc vận chuyển xuất Cảng Vũng Áng. Băng tải bốc xếp lên tàu tiếp tục trang bị nam châm treo trên băng tải để lọc từ tính lần cuối trước khi xuống hầm tàu xuất khẩu.
                """
            }
        ]

        for s in steps_data:
            render_html_block(f"""
            <div class="proc-card" style="border-left: 5px solid {s['color']};">
                <div class="proc-card-header">
                    <div>
                        <span style="font-size: 16px; margin-right: 6px;">{s['icon']}</span>
                        <b style="font-size: 14px; color: #0f172a;">{s['title']}</b>
                    </div>
                    <div>
                        <span class="proc-badge-code" style="color: {s['color']}; border-color: {s['color']};">{s['code']}</span>
                        <span style="font-size: 11px; font-weight: 800; background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 10px; margin-left: 4px;">{s['step']}</span>
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 11px; font-weight: 700; color: #64748b;">Thiết bị trọng yếu: </span>
                    {' '.join([f'<span class="proc-equip-badge">{eq}</span>' for eq in s['equip']])}
                </div>
                <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
                    {s['content']}
                </div>
            </div>
            """)

    # ================= TAB 2: HỆ THỐNG AN TOÀN & TÁCH TỪ TÍNH =================
    with tab_safety:
        st.markdown("#### 🛡️ Các Hệ Thống An Toàn, Phòng Nổ & Kiểm Soát Chất Lượng Đạt Chuẩn Xuất Khẩu")

        c_g1, c_g2 = st.columns([1.5, 1.2])
        with c_g1:
            st.markdown("##### 1. Hệ Thống Phòng Chống Cháy Nổ Tự Động GreCon (Đức)")
            st.markdown("""
            Đặc thù sản xuất bột gỗ khô có nguy cơ cháy nổ bụi rất cao. Nhà máy BVN Quảng Bình đầu tư toàn bộ hệ thống phát hiện và dập tắt tia lửa **GreCon** trên các tuyến ống vận chuyển bột gỗ (Line L01 đến L07):
            - 📡 **Đầu dò hồng ngoại siêu nhạy:** Cảm biến `FM 1/8` và `DLD 1/9` phát hiện tia lửa ma sát nhỏ nhất trong ống dẫn.
            - 💧 **Dập lửa tức thì trong 0.25 giây:** Tủ trung tâm `Control Console CC7016` kích hoạt cụm dập lửa gồm bơm tăng áp, 2 bình tích áp màng 500L và vòi phun sương góc mở 120° dập tắt tia lửa trong thời gian cực ngắn **t = 0.25 giây**.
            - 📐 **Khoảng cách an toàn tối thiểu:**
            """)
            st.latex(r"S = v 	imes t = 30	ext{ m/s} 	imes 0.25	ext{ s} = 7.5	ext{ mét}")
            st.markdown("""
            - 🛑 **Cơ chế ngắt dừng máy khẩn cấp:** Nếu cảm biến đếm số tia lửa **> 20 tia/lần** hoặc tần suất báo cháy **> 10 lần/30 phút**, hệ thống tự động phát lệnh ngắt `G147, G247, G347` dừng ngay lập tức máy nghiền tinh và lò đốt để ngăn ngừa thảm họa.
            """)

        with c_g2:
            st.markdown("##### 2. Ma Trận 32 Điểm Gắn Nam Châm Tách Từ (Bản Vẽ Rev 5.10)")
            st.caption("Chi tiết phân bổ 32 điểm tách từ tính bảo vệ thiết bị và kiểm soát chất lượng xuất khẩu:")
            df_magnets = pd.DataFrame([
                {"Khu Vực Công Nghệ": "Băm dăm nguyên liệu (Mã 0)", "Vùng Bản Vẽ": "Wood chip processing", "Số Điểm": "4 điểm", "Điểm Đánh Số": "Điểm 1, 2, 3, 4", "Vị Trí Lắp Đặt": "Băng tải dăm băm & Bẫy đá Stone Drawer"},
                {"Khu Vực Công Nghệ": "Nghiền thô dăm ướt (Mã 1)", "Vùng Bản Vẽ": "Wet grinding area", "Số Điểm": "10 điểm", "Điểm Đánh Số": "Điểm 5 đến 14", "Vị Trí Lắp Đặt": "Cửa buồng nghiền búa HM418 & Vít nạp HP110-310"},
                {"Khu Vực Công Nghệ": "Sấy dăm/bột ướt (Mã 2)", "Vùng Bản Vẽ": "Dryer area", "Số Điểm": "3 điểm", "Điểm Đánh Số": "Điểm 15, 16, 17", "Vị Trí Lắp Đặt": "Tuyến vận chuyển liệu sau trống sấy quay PDI"},
                {"Khu Vực Công Nghệ": "Nghiền tinh bột khô (Mã 4)", "Vùng Bản Vẽ": "Dry grinding area", "Số Điểm": "3 điểm", "Điểm Đánh Số": "Điểm 18, 19, 20", "Vị Trí Lắp Đặt": "Trước cửa vào 3 buồng nghiền tinh HM147-347"},
                {"Khu Vực Công Nghệ": "Ép viên nén ANDRITZ (Mã 5)", "Vùng Bản Vẽ": "Pelleting area", "Số Điểm": "9 điểm", "Điểm Đánh Số": "Điểm 21 đến 29", "Vị Trí Lắp Đặt": "Điểm 21 (cấp tổng) + Điểm 22–29 (cửa 8 máy ép PM30-6)"},
                {"Khu Vực Công Nghệ": "Sàng & Đóng bao Jumbo (Mã 6-7)", "Vùng Bản Vẽ": "Screening area", "Số Điểm": "3 điểm", "Điểm Đánh Số": "Điểm 30, 31, 32", "Vị Trí Lắp Đặt": "Sàng rung ST167/267, Nam châm quay RMN & Cân xuất"}
            ])
            st.dataframe(df_magnets, use_container_width=True, hide_index=True)

            # Nút tải và xem bản vẽ sơ đồ nam châm
            mag_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "20250220R5.10-So_do_Nam_cham-Model.pdf")
            if os.path.exists(mag_pdf_path):
                with open(mag_pdf_path, "rb") as f_pdf:
                    st.download_button(
                        label="📥 Tải Bản Vẽ Sơ Đồ Nam Châm Gốc (PDF Rev 5.10)",
                        data=f_pdf.read(),
                        file_name="20250220R5.10-So_do_Nam_cham-Model.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            mag_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "so_do_nam_cham.png")
            if os.path.exists(mag_img_path):
                with st.expander("🔍 **Xem Bản Vẽ Bố Trí 32 Điểm Nam Châm Trực Quan**", expanded=False):
                    st.image(mag_img_path, caption="Sơ đồ bố trí 32 điểm nam châm (Rev 5.10) - Nhà máy viên nén gỗ BVN Quảng Bình", use_container_width=True)


        st.markdown("---")
        st.markdown("##### 3. Kiểm Soát Chất Lượng KCS & Giám Sát Độ Ẩm SCADA Online")
        col_qc1, col_qc2 = st.columns(2)
        with col_qc1:
            st.markdown("""
            - 📟 **Cảm biến đo ẩm Online HU301:** Gắn trực tiếp trên dây chuyền sấy và vận chuyển bột gỗ. Đồ thị độ ẩm truyền về trung tâm điều khiển SCADA và đồng bộ thời gian thực.
            - 🔬 **Phòng Thí Nghiệm KCS Nội Bộ:** Trang bị máy đo ẩm quét phổ hồng ngoại, lò nung độ tro, máy đo tỷ trọng viên nén và cân tiểu ly phân tích lấy mẫu 2 giờ/lần.
            """)
        with col_qc2:
            st.markdown("""
            - 🏢 **Kiểm Định Độc Lập VinaControl:** Định kỳ hàng tháng gửi mẫu viên nén thành phẩm kiểm tra độc lập tại Trung tâm Kiểm định VinaControl các chỉ tiêu:
              - *Độ ẩm:* `8.0 - 9.5%`
              - *Tỷ trọng:* `≥ 600 kg/m³`
              - *Độ bền cơ học (DU):* `≥ 97.5%`
              - *Độ tro:* `≤ 1.5%`
              - *Nhiệt lượng:* `≥ 4.000 kcal/kg`
            """)

    # ================= TAB 3: KỸ THUẬT VẬN HÀNH & TRÁNG KHUÔN ANDRITZ PM30-6 =================
    with tab_mold:
        st.markdown("#### 🛠️ Hướng Dẫn Vận Hành Kỹ Thuật & Quy Trình Tráng Khuôn ANDRITZ PM30-6")
        st.caption("Trích xuất từ hồ sơ kỹ thuật vận hành máy ép viên 355kW — Nhà máy BVN Quảng Bình")

        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "✨ Tráng Mài Bóng Khuôn Mới",
            "🛑 Tráng Xả Dừng Máy Bắt Buộc",
            "📊 Bảng Thông Số Kiểm Soát",
            "⚠️ Xử Lý Sự Cố & ATEX Zone 22"
        ])

        with sub_tab1:
            st.markdown("##### I. QUY TRÌNH TRÁNG / MÀI BÓNG KHUÔN MỚI (DIE RUNNING-IN)")
            st.caption("Áp dụng khi thay mới khuôn hoặc sau khi mài phẳng lại bề mặt khuôn:")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("""
                **1. Công thức hỗn hợp mài bóng (Abrasive Mixture):**
                - 🪵 `50 kg` bột gỗ mùn cưa tinh nghiền qua sàng mịn (< 1mm) hoặc cám gạo mịn.
                - 🏖️ `24 kg` cát mài kỹ thuật tiêu chuẩn (carborundum).
                - 🛢️ `3 lít` dầu bôi trơn công nghiệp sạch (kết dính và bôi trơn thành lỗ nén).
                """)
            with col_m2:
                st.markdown("""
                **2. Kiểm tra lắp ráp cơ khí trước khi chạy rà:**
                - 🔧 **Lực siết bu-lông khuôn:** 24 bu-lông M30 siết chéo đối xứng đạt **1000 Nm**.
                - 📏 **Khe hở vành mòn (Wear ring):** Tiêu chuẩn **0.3 mm ≤ X ≤ 1.8 mm**.
                - 🔄 **Cân chỉnh rulo:** Chỉnh khe hở rulo và khuôn vừa chạm nhẹ (**0.0 - 0.2 mm**).
                """)
            st.markdown("""
            **3. Trình tự 5 bước vận hành mài bóng:**
            1. Khởi động bôi trơn hộp số (áp suất ≥ 5 bar), mở nước làm mát rulo (< 60°C).
            2. Chạy không tải động cơ chính 355kW trong 3 - 5 phút kiểm tra truyền động đai V.
            3. Cấp liệu mài bóng từ từ qua phễu ở tốc độ tối thiểu (0 - 10%), theo dõi dòng Ampe.
            4. Tuần hoàn hỗn hợp ép đùn nạp lại liên tục trong **0.5 - 1 giờ**.
            5. Nghiệm thu khi 100% lỗ nén đùn viên đồng đều, lòng lỗ bóng nhẵn và Ampe ổn định.
            """)

        with sub_tab2:
            st.markdown("##### II. QUY TRÌNH TRÁNG KHUÔN XẢ KHI DỪNG MÁY (SHUTDOWN FLUSHING)")
            st.warning("⚠️ **BẮT BUỘC THỰC HIỆN:** Phải tiến hành trước khi dừng máy kết thúc ca hoặc dừng máy dài ngày để ngăn chặn bột gỗ nướng cứng (>80°C) gây nghẹt đá khuôn.")
            col_x1, col_x2 = st.columns(2)
            with col_x1:
                st.markdown("""
                **1. Chuẩn bị nguyên liệu tráng:**
                - Viên nén thành phẩm ngâm dầu công nghiệp sạch.
                - ⚠️ **Lưu ý kỹ thuật:** Viên phải ngấm đều dầu nhưng **KHÔNG ĐƯỢC NGÂM QUÁ MỀM/NHÃO**. Viên nhão sẽ làm trượt rulo, mất lực đẩy tống mùn thô ra ngoài.
                """)
            with col_x2:
                st.markdown("""
                **2. Trình tự 5 bước dừng máy:**
                - Giảm vít định lượng về 0%, ngắt cấp liệu, tắt bơm nước phun sương.
                - Cho bộ điều hòa (Conditioner) chạy không tải xả sạch tồn dư.
                - Đổ hỗn hợp viên dầu nén đẩy toàn bộ mùn cưa trong lỗ khuôn ra ngoài.
                - Xác nhận **100% lỗ khuôn đùn viên màu sẫm bóng đồng nhất của dầu**.
                - Dừng vít cấp liệu ➔ Dừng động cơ 355kW ➔ Dừng bơm dầu & làm mát.
                """)

        with sub_tab3:
            st.markdown("##### III. BẢNG THÔNG SỐ VÀ DỮ LIỆU KIỂM SOÁT KỸ THUẬT (PM30-6)")
            df_specs = pd.DataFrame([
                {"Hạng mục": "Mô-men siết bu-lông khuôn", "Tiêu chuẩn": "1000 Nm", "Kiểm tra": "Cờ lê lực (24 đai ốc M30)", "Mục đích": "Chống lỏng, gãy bu-lông, định vị khuôn"},
                {"Hạng mục": "Khe hở vành mòn (Wear ring)", "Tiêu chuẩn": "0.3 mm ≤ X ≤ 1.8 mm", "Kiểm tra": "Thước lá căn phẳng 0.2 mm", "Mục đích": "Đảm bảo độ ép côn, bảo vệ trục chính"},
                {"Hạng mục": "Khoảng cách rulo - khuôn", "Tiêu chuẩn": "0.0 - 0.2 mm (chạm nhẹ)", "Kiểm tra": "Quay tay kiểm tra âm học", "Mục đích": "Tránh ma sát kim loại gây mẻ khuôn/rulo"},
                {"Hạng mục": "Nhiệt độ trục rulo khi chạy", "Tiêu chuẩn": "< 60°C", "Kiểm tra": "Cảm biến PT100", "Mục đích": "Bảo vệ vòng bi rulo không cháy hỏng"},
                {"Hạng mục": "Nhiệt độ buồng ép khi dừng", "Tiêu chuẩn": "≥ 80°C", "Kiểm tra": "Đồng hồ nhiệt", "Mục đích": "Cảnh báo nguy cơ nung cứng nếu không tráng dầu"},
                {"Hạng mục": "Áp suất dầu bôi trơn", "Tiêu chuẩn": "≥ 5 bar (nguội) / 1.5 bar (nóng)", "Kiểm tra": "Đồng hồ bơm dầu", "Mục đích": "Bôi trơn cưỡng bức bánh răng và vòng bi"},
                {"Hạng mục": "Điền đầy lỗ khuôn khi tráng", "Tiêu chuẩn": "100% diện tích lỗ", "Kiểm tra": "Viên sẫm bóng cửa xả", "Mục đích": "Chống rỉ sét lòng lỗ và chống kẹt máy ca sau"}
            ])
            st.dataframe(df_specs, use_container_width=True, hide_index=True)

        with sub_tab4:
            st.markdown("##### IV. XỬ LÝ SỰ CỐ & AN TOÀN LAO ĐỘNG (ATEX ZONE 22)")
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.error("❌ Rulo Trượt Mất Tải")
                st.markdown("• *Nguyên nhân:* Viên dầu quá nhão.<br>• *Khắc phục:* Nạp ngay bột khô/cám khô tăng ma sát kéo rulo quay lại.", unsafe_allow_html=True)
            with col_e2:
                st.warning("⚠️ Quá Tải Động Cơ Chính")
                st.markdown("• *Nguyên nhân:* Hỗn hợp mài quá đặc, nạp quá nhanh.<br>• *Khắc phục:* Giảm cấp liệu về 0%, xả tồn dư và tăng tải từ từ.", unsafe_allow_html=True)
            with col_e3:
                st.error("🚫 Nghẹt Khuôn Ca Sau")
                st.markdown("• *Nguyên nhân:* Tráng xả chưa đủ 100% lỗ.<br>• *Khắc phục:* Khoan thông lỗ chuyên dụng. Cấm dùng búa đục phá.", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("""
            **Quy định an toàn lao động & Chống cháy nổ:**
            - 🔥 **Bỏng nhiệt:** Nhiệt độ buồng ép khi dừng luôn **≥ 80°C**. Bắt buộc đeo găng tay chịu nhiệt và bảo hộ.
            - 🏗️ **Nâng hạ vật nặng:** Khuôn và rulo nặng trên 1 tấn, bắt buộc dùng tời nâng chuyên dụng (Die Crane).
            - 💥 **ATEX Zone 22:** Môi trường bụi sinh khối, tuyệt đối không tạo tia lửa điện khi mở cửa máy.
            - 🔒 **Lockout / Tagout:** Cắt cầu dao tổng và khóa thẻ cảnh báo trước khi thao tác bảo dưỡng.
            """)

    # ================= TAB 4: TRA CỨU TOÀN VĂN GOOGLE DOCS =================
    with tab_doc:
        st.markdown("#### 📑 Tra Cứu Toàn Văn Tài Liệu SOP (Google Docs Live)")
        st.caption("Xem toàn văn tài liệu Kỹ thuật Vận hành Chuẩn (SOP) được cập nhật đồng bộ từ Google Docs:")
        st.markdown(
            f'<div style="margin-bottom: 10px;">'
            f'<a href="{doc_url}" target="_blank" style="display:inline-block; padding:8px 16px; background:#2563eb; color:#ffffff; font-weight:700; font-size:13px; border-radius:6px; text-decoration:none;">'
            f'🌐 Mở Trong Tab Mới (Google Docs Full View) ↗</a>'
            f'</div>', unsafe_allow_html=True
        )
        components.iframe(doc_preview_url, height=750, scrolling=True)

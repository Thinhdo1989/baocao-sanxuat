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
from i18n import t, is_en, translate_eval, strip_accents, format_person_name

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


# Mapping Từ điển Phòng ban / Đơn vị sang tiếng Anh
DEPT_MAP_EN = {
    'Ban FSC': 'FSC Board',
    'Ban Quản Lý FSC': 'FSC Management Board',
    'Phòng Kinh doanh': 'Commercial & Sales Dept',
    'Phòng Kinh Doanh': 'Commercial & Sales Dept',
    'P.Tài Chính -Kế Toán': 'Finance & Accounting Dept',
    'Phòng Tài Chính Kế Toán': 'Finance & Accounting Dept',
    'P. Hành Chính-Nhân Sự': 'HR & Admin Dept',
    'Phòng Hành Chính Nhân Sự': 'HR & Admin Dept',
    'Đội băm 1': 'Wood Chipping Team 1',
    'Đội băm 2': 'Wood Chipping Team 2',
    'Đội Băm Dăm': 'Wood Chipping Team',
    'Thành Phẩm 1': 'Pelletizing Shift 1',
    'Thành Phẩm 2': 'Pelletizing Shift 2',
    'Thành Phẩm 3': 'Pelletizing Shift 3',
    'Xưởng Ép Viên': 'Pelletizing Workshop',
    'Kỹ thuật - Vật tư': 'Engineering & Materials',
    'Phòng Kỹ Thuật & Cơ Điện': 'Engineering & Maintenance',
    'Cơ khí': 'Mechanical Maintenance',
    'Ban Giám Đốc': 'Executive Board',
    'Tổ Trạm Cân': 'Weighbridge Team',
    'Tổ Bảo Vệ': 'Security Team',
    'Tổ Bếp Ăn & Tạp Vụ': 'Catering & Janitor Team'
}

DIV_MAP_EN = {
    'Phó giám đốc kinh doanh': 'Deputy Commercial Director',
    'Giám đốc': 'Plant Director',
    'Quản lí Đội băm': 'Chipping Team Manager',
    'PGĐSX': 'Deputy Production Director',
    'HĐQT': 'Board of Directors',
    'Ban Giám Đốc': 'Executive Board'
}

POS_MAP_EN = {
    'Trưởng ban FSC': 'FSC Board Head',
    'Nhân viên FSC 1': 'FSC Specialist 1',
    'Nhân viên FSC 2': 'FSC Specialist 2',
    'Nhân viên FSC 3': 'FSC Specialist 3',
    'Nhân viên FSC 4': 'FSC Specialist 4',
    'Nhân viên FSC 5': 'FSC Specialist 5',
    'Nhân viên COC': 'CoC Specialist',
    'PGĐ Kinh Doanh': 'Deputy Commercial Director',
    'TP kinh doanh': 'Sales Manager',
    'Logistics': 'Logistics Specialist',
    'Nhân viên thu mua 1': 'Procurement Specialist 1',
    'Nhân viên thu mua 2': 'Procurement Specialist 2',
    'Thu mua + thủ kho': 'Procurement & Warehouse Keeper',
    'Kế toán trưởng': 'Chief Accountant',
    'Kế toán tổng hợp 1': 'General Accountant 1',
    'Kế toán tổng hợp 2': 'General Accountant 2',
    'Kế toán LNLT': 'Inventory / Material Accountant',
    'Kế toán LNBT': 'Operations & Payroll Accountant',
    'NV trạm cân': 'Weighbridge Operator',
    'NV trạm cân 1': 'Weighbridge Operator 1',
    'NV trạm cân 2': 'Weighbridge Operator 2',
    'Trưởng phòng': 'Department Head',
    'Nhân viên HC-NS': 'HR & Admin Specialist',
    'Bảo vệ 1': 'Security Guard 1',
    'Bảo vệ 2': 'Security Guard 2',
    'Bảo vệ 3': 'Security Guard 3',
    'Cấp dưỡng 1': 'Canteen Cook 1',
    'Cấp dưỡng 2': 'Canteen Cook 2',
    'Cấp dưỡng 3': 'Canteen Cook 3',
    'Tạp vụ': 'Janitor',
    'Lao công': 'Cleaner',
    'Lái xe': 'Driver',
    'Tổ trưởng băm ca 1': 'Shift 1 Chipping Lead',
    'Tổ trưởng băm ca 2': 'Shift 2 Chipping Lead',
    'Robot 1': 'Robot Operator 1',
    'Robot 2': 'Robot Operator 2',
    'Xe cạp 1': 'Scraper Operator 1',
    'Xe cạp 2': 'Scraper Operator 2',
    'Xe gắp 1': 'Log Grabber Operator 1',
    'Xe gắp 2': 'Log Grabber Operator 2',
    'Vận hành 1': 'Chipper Operator 1',
    'Vận hành 2': 'Chipper Operator 2',
    'LĐPT': 'General Laborer',
    'LĐPT 1': 'General Laborer 1',
    'LĐPT 2': 'General Laborer 2',
    'LĐPT3': 'General Laborer 3',
    'Trưởng ca 1': 'Shift 1 Leader',
    'Trưởng ca 2': 'Shift 2 Leader',
    'Trưởng ca 3': 'Shift 3 Leader',
    'Vận hành trung tâm 1': 'Central Control Operator 1',
    'Vận hành trung tâm 2': 'Central Control Operator 2',
    'Vận hành ép 1': 'Pellet Mill Operator 1',
    'Vận hành ép 2': 'Pellet Mill Operator 2',
    'Vận hành ép 3': 'Pellet Mill Operator 3',
    'Cơ khí 1': 'Mechanical Technician 1',
    'Cơ khí 2': 'Mechanical Technician 2',
    'Cơ khí 3': 'Mechanical Technician 3',
    'Cơ khí 4': 'Mechanical Technician 4',
    'Cơ khí 5': 'Mechanical Technician 5',
    'Bảo trì điện': 'Electrical Maintenance',
    'Xe xúc': 'Wheel Loader Operator',
    'Phó phòng kỹ thuật': 'Deputy Technical Head',
    'Quản lí vật tư+pccc': 'Materials & Fire Safety Manager',
    'Kỹ sư CME': 'CME Engineer',
    'KCS thành phẩm': 'Finished Product QC',
    'Quản lí xe cơ giới': 'Fleet / Vehicle Manager',
    'ATLĐ': 'HSE / Safety Officer',
    'Tổ trưởng': 'Mechanical Team Lead',
}

def translate_manager(mgr: str) -> str:
    """Chuyển đổi chức danh người phụ trách bộ phận sang tiếng Anh."""
    if not mgr or not is_en():
        return mgr
    replacements = {
        '(Trưởng ban)': '(Board Head)',
        '(TP Kinh doanh)': '(Sales Manager)',
        '(Kế toán trưởng)': '(Chief Accountant)',
        '(Trưởng phòng)': '(Dept Head)',
        '(Tổ trưởng ca 1)': '(Shift 1 Lead)',
        '(Tổ trưởng ca 2)': '(Shift 2 Lead)',
        '(Trưởng ca 1)': '(Shift 1 Leader)',
        '(Trưởng ca 2)': '(Shift 2 Leader)',
        '(Trưởng ca 3)': '(Shift 3 Leader)',
        '(Phó phòng)': '(Deputy Head)',
        '(Tổ trưởng)': '(Team Lead)',
    }
    res = mgr
    for k, v in replacements.items():
        res = res.replace(k, v)
    return strip_accents(res)


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
        st.markdown(f"### {t('👥 SƠ ĐỒ CƠ CẤU TỔ CHỨC & ĐỊNH BIÊN NHÂN SỰ TOÀN CÔNG TY', '👥 COMPANY-WIDE ORGANIZATION CHART & STAFFING STRUCTURE')}")
        st.caption(t("CÔNG TY CỔ PHẦN ĐẦU TƯ BVN QUẢNG BÌNH • NHÀ MÁY SẢN XUẤT VIÊN NÉN GỖ SINH KHỐI", "BVN QUANG BINH INVESTMENT JSC • BIOMASS WOOD PELLET PLANT"))
    with c_act:
        status_badge = t("🟢 Google Sheets Live", "🟢 Google Sheets Live") if status == "CONNECTED" else t("🔵 Dữ liệu Cache Offline", "🔵 Offline Cached Data")
        st.markdown(f"**{t('Trạng thái:', 'Status:')}** `{status_badge}`")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button(t("🔄 Đồng Bộ", "🔄 Sync Data"), help=t("Nạp lại dữ liệu trực tiếp từ Google Sheets", "Reload live data from Google Sheets"), use_container_width=True):
                with st.spinner(t("Đang đồng bộ Google Sheets...", "Syncing Google Sheets...")):
                    if dl is not None:
                        st.session_state['hr_data'] = dl.load_organization_hr_data(force_reload=True)
                    else:
                        from data_loader import DataLoader
                        _dl = DataLoader()
                        st.session_state['hr_data'] = _dl.load_organization_hr_data(force_reload=True)
                    st.success(t("Đã đồng bộ thành công!", "Sync completed successfully!"))
                    st.rerun()
        with c_b2:
            st.markdown(f'<a href="{sheet_url}" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:7px 4px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;text-decoration:none;color:#0f172a;font-weight:600;">{t("↗️ Mở Sheet", "↗️ Open Sheet")}</a>', unsafe_allow_html=True)

    # 3. Thống kê 5 Chỉ số KPI Tổng quan
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(t("Tổng Định Biên Kế Hoạch", "Total Planned Headcount"), f"{summary.get('plan', 104)} {t('Vị trí', 'Positions')}", t("11 Bộ phận toàn công ty", "11 Plant Departments"))
    with m2:
        st.metric(t("Nhân Sự Đã Tiếp Nhận", "Onboarded Personnel"), f"{summary.get('actual', 92)} {t('Người', 'Staff')}", f"{t('Lấp đầy', 'Filled')} {summary.get('rate', '88,46%')}")
    with m3:
        st.metric(t("Chỉ Tiêu Còn Thiếu", "Vacant Positions"), f"{summary.get('missing', 12)} {t('Vị trí', 'Positions')}", t("Cần tuyển dụng bổ sung", "To be recruited"), delta_color="inverse")
    with m4:
        st.metric(t("Khối Sản Xuất Trực Tiếp", "Direct Production Division"), f"51 / 57 {t('Người', 'Staff')}", t("Đạt 89.5% (Băm & Ép 3 ca)", "89.5% (Chipping & Pelleting 3 shifts)"))
    with m5:
        st.metric(t("Khối Gián Tiếp & Nghiệp Vụ", "Indirect & Office Staff"), f"33 / 34 {t('Người', 'Staff')}", t("Đạt 97.1% (FSC, KD, KT, HC)", "97.1% (FSC, Sales, Acc, Admin)"))

    st.markdown("---")

    # 4. Phân tab điều hướng chức năng
    t_tree, t_kpi, t_roster, t_sheet = st.tabs([
        t("🏛️ Sơ Đồ Cây Phân Cấp", "🏛️ Hierarchical Org Tree"),
        t("📊 Thống Kê & Phân Tích Định Biên", "📊 Headcount Analysis & Stats"),
        t("📋 Danh Sách Nhân Sự & Tìm Kiếm", "📋 Employee Roster & Search"),
        t("📑 Bảng Tính Trực Tiếp (Live Google Sheets)", "📑 Live Google Sheets")
    ])

    # ================= TAB 1: SƠ ĐỒ CÂY PHÂN CẤP =================
    with t_tree:
        # Cấp 1: HĐQT
        render_html_block(f"""
        <div class="org-hero-card">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 1px;">{t("CƠ QUAN QUẢN TRỊ TỐI CAO", "SUPREME GOVERNING BODY")}</div>
            <div style="font-size: 18px; font-weight: 900; margin: 4px 0;">🏢 {t("HỘI ĐỒNG QUẢN TRỊ (HĐQT)", "BOARD OF DIRECTORS (BOD)")}</div>
            <div style="font-size: 12.5px; color: #e2e8f0;">{t("Định hướng chiến lược phát triển, nguồn vốn, công nghệ & phê duyệt mục tiêu kinh doanh", "Strategic direction, capital financing, technology & business target approvals")}</div>
        </div>
        <div style="text-align: center; color: #94a3b8; font-size: 18px; margin: -6px 0 4px 0;">▼</div>
        """)

        # Cấp 2: Ban Giám Sát & Giám Đốc Nhà Máy
        c_sup, c_dir = st.columns([1, 2.3])
        with c_sup:
            render_html_block(f"""
            <div class="org-supervisor-card">
                <div style="font-size: 11px; font-weight: 700; color: #fde68a; text-transform: uppercase; letter-spacing: 0.5px;">{t("CƠ QUAN GIÁM SÁT ĐỘC LẬP", "INDEPENDENT SUPERVISORY BODY")}</div>
                <div style="font-size: 15px; font-weight: 900; margin: 4px 0;">⚖️ {t("BAN GIÁM SÁT / KIỂM SOÁT", "SUPERVISORY BOARD / INTERNAL AUDIT")}</div>
                <div style="font-size: 12px; color: #fef3c7;">{t("Giám sát tuân thủ điều lệ, quy chế tài chính, định mức tiêu hao & kiểm soát rủi ro", "Supervising compliance, financial regulations, consumption quotas & risk control")}</div>
                <div style="margin-top: 8px; font-size: 11px; font-weight: 700; background: rgba(0,0,0,0.2); padding: 3px 8px; border-radius: 6px;">{t("Trực thuộc HĐQT", "Under BOD Authority")}</div>
            </div>
            """)
        with c_dir:
            render_html_block(f"""
            <div class="org-director-card">
                <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px;">{t("CƠ QUAN ĐIỀU HÀNH CAO NHẤT NHÀ MÁY", "HIGHEST PLANT EXECUTIVE BODY")}</div>
                <div style="font-size: 17px; font-weight: 900; margin: 3px 0;">🏢 {t("GIÁM ĐỐC NHÀ MÁY: ÔNG VŨ QUANG SÁNG", "PLANT DIRECTOR: MR. VU QUANG SANG")}</div>
                <div style="font-size: 12.5px; color: #e2e8f0;">{t("Chỉ đạo & điều hành toàn diện Vận hành 24/7, An toàn, Chất lượng, Kỹ thuật & Hiệu quả sản xuất kinh doanh", "Directing 24/7 operations, plant safety, product quality, engineering & business efficiency")}</div>
                <div style="margin-top: 8px; font-size: 11.5px; font-weight: 700; background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 6px; display: inline-block;">
                    {t("Chỉ đạo trực tiếp: Phó GĐ Kinh Doanh • Kế Toán Trưởng • Trưởng Phòng HC-NS • Phó GĐ Sản Xuất", "Direct oversight: Deputy Sales Dir • Chief Accountant • HR-Admin Head • Deputy Production Dir")}
                </div>
            </div>
            """)

        render_html_block("""<div style="text-align: center; color: #94a3b8; font-size: 18px; margin: 6px 0;">▼</div>""")

        # Cấp 3: 4 Cánh tay chức năng (4 Trụ Cột)
        col_kd, col_kt, col_hc, col_sx = st.columns(4)

        # 1. KHỐI KINH DOANH & FSC
        with col_kd:
            render_html_block(f"""
            <div class="org-pillar-box" style="border-top: 4px solid #2563eb;">
                <div class="org-pillar-title" style="color: #1e40af;">
                    <span>{t("💼 KHỐI KINH DOANH & FSC", "💼 SALES & FSC DIVISION")}</span>
                    <span class="org-badge-warning">{t("11 / 12 NS", "11 / 12 Staff")}</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">{t("Quản lý: <b>Phó Giám Đốc Kinh Doanh</b>", "Managed by: <b>Deputy Sales Director</b>")}</div>

                <!-- Ban FSC -->
                <div class="org-subcard" style="border-left: 3px solid #059669;">
                    <div class="org-subcard-title" style="color: #065f46;">
                        <span>{t("🌲 Ban Quản Lý FSC", "🌲 FSC Management Board")}</span>
                        <span class="org-badge-success">7/7 • 100% 🥇</span>
                    </div>
                    <div class="org-subcard-lead">{t("Trưởng ban: Trần Đặng Hiếu", "Board Head: Tran Dang Hieu")}</div>
                    <div class="org-person-item"><span>{t("NV FSC 1", "FSC Staff 1")}</span> <b>{format_person_name("Lê Hữu Hoàn")}</b></div>
                    <div class="org-person-item"><span>{t("NV FSC 2", "FSC Staff 2")}</span> <b>{format_person_name("Nguyễn Văn Long")}</b></div>
                    <div class="org-person-item"><span>{t("NV FSC 3", "FSC Staff 3")}</span> <b>{format_person_name("Phan Văn Hùng")}</b></div>
                    <div class="org-person-item"><span>{t("NV FSC 4", "FSC Staff 4")}</span> <b>{format_person_name("Lê Thuận Trung")}</b></div>
                    <div class="org-person-item"><span>{t("NV FSC 5", "FSC Staff 5")}</span> <b>{format_person_name("Lê Công Tình")}</b></div>
                    <div class="org-person-item"><span>{t("NV Quản lý COC", "CoC Manager")}</span> <b>{format_person_name("Nguyễn Thị Diệu Thu")}</b></div>
                </div>

                <!-- Phòng Kinh doanh -->
                <div class="org-subcard" style="border-left: 3px solid #2563eb;">
                    <div class="org-subcard-title" style="color: #1d4ed8;">
                        <span>{t("📈 Phòng Kinh Doanh", "📈 Sales & Commercial Dept")}</span>
                        <span class="org-badge-warning">4/5 • 80%</span>
                    </div>
                    <div class="org-subcard-lead">{t("Trưởng phòng: Nguyễn Trọng Đại", "Dept Head: Nguyen Trong Dai")}</div>
                    <div class="org-person-item"><span>{t("Logistics & Thu mua", "Logistics & Procurement")}</span> <b>{format_person_name("Nguyễn Anh Tuấn")}</b></div>
                    <div class="org-person-item"><span>{t("NV Thu mua 1", "Procurement Staff 1")}</span> <b>{format_person_name("Lê Minh Hiển")}</b></div>
                    <div class="org-person-item"><span>{t("NV Thu mua 2", "Procurement Staff 2")}</span> <b>{format_person_name("Lê Thanh")}</b></div>
                    <div class="org-person-item" style="color:#b91c1c;"><span>{t("Vị trí khuyết", "Vacant position")}</span> <i>{t("Cần tuyển 1 NS", "1 recruit needed")}</i></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #eff6ff; padding: 7px 9px; border-radius: 6px; border: 1px solid #bfdbfe;">
                    {t("<b>Nhiệm vụ trọng tâm:</b><br>• Chứng chỉ rừng bền vững FSC & CoC<br>• Thu mua nguyên liệu dăm & bao tiêu đầu ra", "<b>Core Responsibilities:</b><br>• Sustainable Forest Management FSC & CoC<br>• Wood chip procurement & product sales contract")}
                </div>
            </div>
            """)

        # 2. KHỐI TÀI CHÍNH - KẾ TOÁN & CÂN XE
        with col_kt:
            render_html_block(f"""
            <div class="org-pillar-box" style="border-top: 4px solid #d97706;">
                <div class="org-pillar-title" style="color: #b45309;">
                    <span>{t("💰 KHỐI TÀI CHÍNH - KẾ TOÁN", "💰 FINANCE & ACCOUNTING DIVISION")}</span>
                    <span class="org-badge-success">{t("8 / 8 NS • 100% 🥇", "8 / 8 Staff • 100% 🥇")}</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">{t("Kế toán trưởng: <b>Phan Văn Tuấn</b>", "Chief Accountant: <b>Phan Van Tuan</b>")}</div>

                <!-- Bộ phận kế toán -->
                <div class="org-subcard" style="border-left: 3px solid #d97706;">
                    <div class="org-subcard-title" style="color: #92400e;">
                        <span>{t("🏢 Nghiệp Vụ Kế Toán", "🏢 Accounting Department")}</span>
                        <span class="org-badge-success">{t("5 NS", "5 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Kế toán tổng hợp 1", "General Accountant 1")}</span> <b>{format_person_name("Nguyễn Thị Lệ Thuần")}</b></div>
                    <div class="org-person-item"><span>{t("Kế toán tổng hợp 2", "General Accountant 2")}</span> <b>{format_person_name("Phan Hải Yến")}</b></div>
                    <div class="org-person-item"><span>{t("Kế toán LNLT", "Material / Inventory Acc")}</span> <b>{format_person_name("Hồ Thị Huyền Trang")}</b></div>
                    <div class="org-person-item"><span>{t("Kế toán LNBT", "Payroll & Operations Acc")}</span> <b>{format_person_name("Dương Thị Ánh Tuyết")}</b></div>
                </div>

                <!-- Trạm cân xe -->
                <div class="org-subcard" style="border-left: 3px solid #f59e0b;">
                    <div class="org-subcard-title" style="color: #b45309;">
                        <span>{t("⚖️ Tổ Trạm Cân Xe (3 Ca)", "⚖️ Weighbridge Team (3 Shifts)")}</span>
                        <span class="org-badge-success">{t("3 NS", "3 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("NV Trạm cân 1", "Weighbridge Operator 1")}</span> <b>{format_person_name("Trần Thị Hòa")}</b></div>
                    <div class="org-person-item"><span>{t("NV Trạm cân 2", "Weighbridge Operator 2")}</span> <b>{format_person_name("Trương Quang Sinh")}</b></div>
                    <div class="org-person-item"><span>{t("NV Trạm cân 3", "Weighbridge Operator 3")}</span> <b>{format_person_name("Dương Hoàng")}</b></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #fffbeb; padding: 7px 9px; border-radius: 6px; border: 1px solid #fde68a;">
                    {t("<b>Nhiệm vụ trọng tâm:</b><br>• Kiểm soát phiếu cân nguyên liệu & xuất hàng<br>• Quản trị giá thành viên nén, chi phí điện & vật tư", "<b>Core Responsibilities:</b><br>• Weighbridge tickets for raw material & shipping<br>• Cost accounting for pellets, electricity & consumables")}
                </div>
            </div>
            """)

        # 3. KHỐI HÀNH CHÍNH - NHÂN SỰ & HẬU CẦN
        with col_hc:
            render_html_block(f"""
            <div class="org-pillar-box" style="border-top: 4px solid #7c3aed;">
                <div class="org-pillar-title" style="color: #6d28d9;">
                    <span>{t("👥 HÀNH CHÍNH - NHÂN SỰ", "👥 ADMINISTRATION & HR DIVISION")}</span>
                    <span class="org-badge-success">{t("11 / 11 NS • 100% 🥇", "11 / 11 Staff • 100% 🥇")}</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">{t("Trưởng phòng: <b>Hoàng Thanh Bình</b>", "Dept Head: <b>Hoang Thanh Binh</b>")}</div>

                <!-- HC-NS -->
                <div class="org-subcard" style="border-left: 3px solid #7c3aed;">
                    <div class="org-subcard-title" style="color: #5b21b6;">
                        <span>{t("🏢 Quản Trị Nhân Lực", "🏢 Human Resource Management")}</span>
                        <span class="org-badge-success">{t("2 NS", "2 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Nhân viên HC-NS", "HR-Admin Specialist")}</span> <b>{format_person_name("Phan Thị Linh Hằng")}</b></div>
                </div>

                <!-- Bảo vệ -->
                <div class="org-subcard" style="border-left: 3px solid #8b5cf6;">
                    <div class="org-subcard-title" style="color: #6d28d9;">
                        <span>{t("🛡️ Tổ Bảo Vệ (Trực 24/7)", "🛡️ Security Team (24/7)")}</span>
                        <span class="org-badge-success">{t("3 NS", "3 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Bảo vệ 1", "Security Officer 1")}</span> <b>{format_person_name("Phạm Huy Bình")}</b></div>
                    <div class="org-person-item"><span>{t("Bảo vệ 2", "Security Officer 2")}</span> <b>{format_person_name("Trần Tiến Dũng")}</b></div>
                    <div class="org-person-item"><span>{t("Bảo vệ 3", "Security Officer 3")}</span> <b>{format_person_name("Hoàng Xuân Khương")}</b></div>
                </div>

                <!-- Bếp ăn & Hậu cần -->
                <div class="org-subcard" style="border-left: 3px solid #a855f7;">
                    <div class="org-subcard-title" style="color: #7e22ce;">
                        <span>{t("🍳 Hậu Cần & Đời Sống", "🍳 Catering & Logistics Support")}</span>
                        <span class="org-badge-success">{t("6 NS", "6 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Cấp dưỡng (3 NS)", "Canteen Cooks (3 Staff)")}</span> <b>{format_person_name("V.Hiếu, N.Hiện, T.Minh")}</b></div>
                    <div class="org-person-item"><span>{t("Tạp vụ & Vệ sinh", "Housekeeping & Janitor")}</span> <b>{format_person_name("H.Nhung, T.Hần")}</b></div>
                    <div class="org-person-item"><span>{t("Lái xe đưa đón", "Shuttle Bus Driver")}</span> <b>{format_person_name("Võ Chí Thanh")}</b></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #faf5ff; padding: 7px 9px; border-radius: 6px; border: 1px solid #e9d5ff;">
                    {t("<b>Nhiệm vụ trọng tâm:</b><br>• Đảm bảo đời sống, bữa ăn ca an toàn vệ sinh<br>• An ninh trật tự, tuyển dụng bù đắp định biên", "<b>Core Responsibilities:</b><br>• Welfare, sanitary shift catering & employee living<br>• Plant security, recruitment & headcount fulfillment")}
                </div>
            </div>
            """)

        # 4. KHỐI SẢN XUẤT TRỰC TIẾP & KỸ THUẬT CƠ KHÍ
        with col_sx:
            render_html_block(f"""
            <div class="org-pillar-box" style="border-top: 4px solid #059669;">
                <div class="org-pillar-title" style="color: #047857;">
                    <span>{t("🏭 SẢN XUẤT & KỸ THUẬT", "🏭 PRODUCTION & ENGINEERING DIVISION")}</span>
                    <span class="org-badge-warning">{t("62 / 70 NS • 88.6%", "62 / 70 Staff • 88.6%")}</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">{t("PGĐSX: <b>Đỗ Công Thịnh</b> (Chỉ huy 4 cụm)", "Deputy Production Dir: <b>Do Cong Thinh</b> (4 units)")}</div>

                <!-- Đội băm -->
                <div class="org-subcard" style="border-left: 3px solid #ea580c;">
                    <div class="org-subcard-title" style="color: #c2410c;">
                        <span>{t("🪵 Đội Băm Dăm (2 Ca)", "🪵 Wood Chipping Team (2 Shifts)")}</span>
                        <span class="org-badge-warning">{t("22/24 NS", "22/24 Staff")}</span>
                    </div>
                    <div class="org-subcard-lead">{t("Quản lý: Phạm Văn Cường", "Team Manager: Pham Van Cuong")}</div>
                    <div class="org-person-item"><span>{t("Ca 1 (Tổ trưởng)", "Shift 1 (Team Leader)")}</span> <b>{format_person_name("Trần Văn Quảng")} (11/12)</b></div>
                    <div class="org-person-item"><span>{t("Ca 2 (Tổ trưởng)", "Shift 2 (Team Leader)")}</span> <b>{format_person_name("Trần Mạnh Hà")} (11/12)</b></div>
                    <div style="font-size:10.5px; color:#64748b; padding-top:2px;">{t("Robot, Xe cạp, Xe gắp, Máy băm, LĐPT", "Robots, Scrapers, Wheel Loaders, Chippers, General Labors")}</div>
                </div>

                <!-- Thành phẩm 3 ca -->
                <div class="org-subcard" style="border-left: 3px solid #0284c7;">
                    <div class="org-subcard-title" style="color: #0369a1;">
                        <span>{t("⚙️ Xưởng Ép Viên (3 Ca)", "⚙️ Pelletizing Workshop (3 Shifts)")}</span>
                        <span class="org-badge-warning">{t("29/33 NS", "29/33 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Ca 1 (Trưởng ca)", "Shift 1 (Shift Leader)")}</span> <b>{format_person_name("Lê Chiến Sắc")} (9/11)</b></div>
                    <div class="org-person-item"><span>{t("Ca 2 (Trưởng ca)", "Shift 2 (Shift Leader)")}</span> <b>{format_person_name("Hoàng Phúc Tài")} (10/11)</b></div>
                    <div class="org-person-item"><span>{t("Ca 3 (Trưởng ca)", "Shift 3 (Shift Leader)")}</span> <b>{format_person_name("Nguyễn Long")} (10/11)</b></div>
                    <div style="font-size:10.5px; color:#64748b; padding-top:2px;">{t("VHTT, Máy ép PM30-6, Cơ khí ca, Xe xúc", "Central Control, ANDRITZ PM30-6, Shift Mechanics, Wheel Loaders")}</div>
                </div>

                <!-- Kỹ thuật vật tư -->
                <div class="org-subcard" style="border-left: 3px solid #4f46e5;">
                    <div class="org-subcard-title" style="color: #4338ca;">
                        <span>{t("🛠️ Kỹ Thuật - Vật Tư - KCS", "🛠️ Engineering, Materials & QC")}</span>
                        <span class="org-badge-warning">{t("5/7 NS", "5/7 Staff")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Phó phòng KT", "Deputy Technical Head")}</span> <b>{format_person_name("Nguyễn Đăng Thành")}</b></div>
                    <div class="org-person-item"><span>{t("Vật tư & PCCC", "Inventory & Fire Fighting")}</span> <b>{format_person_name("Cái Viết Thanh Lâm")}</b></div>
                    <div class="org-person-item"><span>{t("Kỹ sư CME / KCS", "CME / QC Engineers")}</span> <b>{format_person_name("X.Dương, K.Dung")}</b></div>
                </div>

                <!-- Cơ khí -->
                <div class="org-subcard" style="border-left: 3px solid #e11d48;">
                    <div class="org-subcard-title" style="color: #be123c;">
                        <span>{t("🔩 Cơ Khí Bảo Dưỡng", "🔩 Mechanical Maintenance")}</span>
                        <span class="org-badge-danger">{t("3/6 NS (50%)", "3/6 Staff (50%)")}</span>
                    </div>
                    <div class="org-person-item"><span>{t("Tổ trưởng cơ khí", "Mechanical Team Lead")}</span> <b>{format_person_name("Phan Nhớ")}</b></div>
                    <div class="org-person-item"><span>{t("Thợ cơ khí chính", "Senior Mechanics")}</span> <b>{format_person_name("M.Tuấn, V.Huy")}</b></div>
                    <div class="org-person-item" style="color:#b91c1c;"><span>{t("Còn khuyết", "Vacant")}</span> <i>{t("Thiếu 3 thợ cơ khí", "3 mechanics needed")}</i></div>
                </div>

                <div style="margin-top: auto; font-size: 11px; background: #f0fdf4; padding: 7px 9px; border-radius: 6px; border: 1px solid #bbf7d0;">
                    {t("<b>Nhiệm vụ trọng tâm:</b><br>• Vận hành liên tục 24/7 băm dăm và ép viên<br>• Bảo dưỡng định kỳ, giảm suất điện & tăng năng suất", "<b>Core Responsibilities:</b><br>• 24/7 continuous chipping & pelletizing operation<br>• Scheduled PM, reducing power rate & boosting output")}
                </div>
            </div>
            """)

    # ================= TAB 2: THỐNG KÊ & PHÂN TÍCH ĐỊNH BIÊN =================
    with t_kpi:
        st.markdown(f"#### {t('📊 Ma Trận Định Biên Kế Hoạch vs Nhân Sự Thực Tế Theo Bộ Phận', '📊 Headcount Matrix: Planned vs Actual Staffing by Department')}")

        # Chuẩn bị DataFrame thống kê
        chart_rows = []
        for d in departments:
            dept_display = DEPT_MAP_EN.get(d['department'], d['department']) if is_en() else d['department']
            div_display = DIV_MAP_EN.get(d.get('parent', ''), d.get('parent', '')) if is_en() else d.get('parent', '')
            mgr_display = translate_manager(d.get('manager', '')) if is_en() else d.get('manager', '')
            chart_rows.append({
                t('Bộ Phận', 'Department'): dept_display,
                t('Kế Hoạch', 'Plan'): d['plan'],
                t('Thực Tế', 'Actual'): d['actual'],
                t('Còn Thiếu', 'Vacant'): d['missing'],
                t('Tỉ Lệ (%)', 'Rate (%)'): d.get('rate_num', round(d['actual']/d['plan']*100, 1) if d['plan'] > 0 else 0),
                t('Người Phụ Trách', 'Manager'): mgr_display,
                t('Khối Trực Thuộc', 'Division'): div_display
            })
        df_chart = pd.DataFrame(chart_rows)

        col_g1, col_g2 = st.columns([1.6, 1.4])
        col_dept_key = t('Bộ Phận', 'Department')
        col_act_key = t('Thực Tế', 'Actual')
        col_miss_key = t('Còn Thiếu', 'Vacant')
        col_rate_key = t('Tỉ Lệ (%)', 'Rate (%)')

        with col_g1:
            fig_bar = px.bar(
                df_chart,
                x=col_dept_key,
                y=[col_act_key, col_miss_key],
                title=t("So Sánh Định Biên: Nhân Sự Thực Tế vs Còn Thiếu (Người)", "Headcount Comparison: Actual vs Vacant Staff (Persons)"),
                color_discrete_map={col_act_key: '#10b981', col_miss_key: '#ef4444'},
                barmode='stack',
                text_auto=True
            )
            fig_bar.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=40, b=80),
                xaxis_tickangle=-35,
                xaxis_title=t("Bộ Phận", "Department"),
                yaxis_title=t("Số người", "Persons"),
                legend_title_text=t("Chỉ tiêu", "Metric")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            fig_rate = px.bar(
                df_chart.sort_values(by=col_rate_key, ascending=True),
                x=col_rate_key,
                y=col_dept_key,
                orientation='h',
                title=t("Tỉ Lệ Hoàn Thành Định Biên (%)", "Headcount Fulfillment Rate (%)"),
                color=col_rate_key,
                color_continuous_scale='RdYlGn',
                text=col_rate_key
            )
            fig_rate.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_rate.add_vline(x=100, line_dash="dash", line_color="green", annotation_text=t("100% Đủ định biên", "100% Full Staff"))
            fig_rate.update_layout(
                height=400,
                margin=dict(l=10, r=20, t=40, b=20),
                xaxis_title=t("Tỉ Lệ (%)", "Rate (%)"),
                yaxis_title=t("Bộ Phận", "Department")
            )
            st.plotly_chart(fig_rate, use_container_width=True)

        # Bảng chi tiết
        st.markdown(f"##### {t('📋 Bảng Định Biên Toàn Bộ 11 Đơn Vị Công Ty', '📋 Staffing Table for All 11 Company Departments')}")
        st.dataframe(
            df_chart[[col_dept_key, t('Khối Trực Thuộc', 'Division'), t('Người Phụ Trách', 'Manager'), t('Kế Hoạch', 'Plan'), col_act_key, col_miss_key, col_rate_key]],
            use_container_width=True,
            hide_index=True
        )

    # ================= TAB 3: DANH SÁCH NHÂN SỰ & TÌM KIẾM =================
    with t_roster:
        st.markdown(f"#### {t('📋 Tra Cứu Danh Sách Cán Bộ Nhân Viên Toàn Nhà Máy', '📋 Factory-wide Personnel & Employee Directory')}")
        
        # Bộ lọc
        cf1, cf2, cf3 = st.columns([1.5, 1.2, 2])
        dept_raw_list = [d['department'] for d in departments]
        dept_options = [t("Tất cả", "All")] + [DEPT_MAP_EN.get(dept, dept) if is_en() else dept for dept in dept_raw_list]
        with cf1:
            sel_dept_idx = st.selectbox(t("Lọc theo Bộ phận / Phân xưởng:", "Filter by Department / Workshop:"), options=range(len(dept_options)), format_func=lambda i: dept_options[i])
            sel_dept_val = "Tất cả" if sel_dept_idx == 0 else dept_raw_list[sel_dept_idx - 1]
        with cf2:
            status_opts = [t("Tất cả", "All"), t("Đã có nhân sự", "Occupied Positions"), t("Vị trí còn trống (Cần tuyển)", "Vacant Positions (Recruiting)")]
            sel_status_idx = st.selectbox(t("Lọc theo Trạng thái:", "Filter by Status:"), options=range(len(status_opts)), format_func=lambda i: status_opts[i])
        with cf3:
            kw = st.text_input(t("🔍 Tìm kiếm theo Họ Tên hoặc Vị Trí:", "🔍 Search by Name or Position:"), placeholder=t("VD: Sắc, Long, Cơ khí, Robot...", "e.g.: Sac, Long, Mechanic, Robot..."))

        # Lọc danh sách
        filtered_roster = []
        for idx, item in enumerate(all_roster, 1):
            d_match = (sel_dept_val == "Tất cả" or item['department'] == sel_dept_val)
            
            s_match = True
            if sel_status_idx == 1:
                s_match = (item['status'] == 'Đã có')
            elif sel_status_idx == 2:
                s_match = (item['status'] == 'Còn trống')
                
            dept_show = DEPT_MAP_EN.get(item['department'], item['department']) if is_en() else item['department']
            pos_show = POS_MAP_EN.get(item['position'], item['position']) if is_en() else item['position']
            
            is_vacant = (item['status'] == 'Còn trống' or 'trống' in item['name'].lower() or 'tuyển' in item['name'].lower())
            if is_vacant:
                name_show = t(item['name'], "Vacant (To be recruited)")
                status_show = t("Còn trống", "Vacant")
                raw_show = f"{pos_show} | Vacant (To be recruited)" if is_en() else item.get('raw', f"{item['position']} (Cần tuyển)")
            else:
                name_show = format_person_name(item['name'])
                status_show = t("Đã có", "Occupied")
                raw_show = f'{pos_show} | "{name_show}"' if is_en() else item.get('raw', f'{item["position"]} | "{item["name"]}"')

            k_match = True
            if kw.strip():
                k_lower = kw.strip().lower()
                target_str = f"{item['department']} {dept_show} {item['position']} {pos_show} {item['name']} {name_show} {raw_show}".lower()
                k_match = (k_lower in target_str)

            if d_match and s_match and k_match:
                filtered_roster.append({
                    t("STT", "No."): len(filtered_roster) + 1,
                    t("Bộ Phận / Đội", "Department / Team"): dept_show,
                    t("Vị Trí Chức Danh", "Position / Title"): pos_show,
                    t("Họ Và Tên", "Full Name"): name_show,
                    t("Trạng Thái", "Status"): status_show,
                    t("Ghi Chú Vận Hành", "Operational Notes"): raw_show
                })

        st.caption(f"{t('Tìm thấy', 'Found')} **{len(filtered_roster)}** {t('vị trí / nhân sự phù hợp.', 'matching positions / staff.')}")
        if filtered_roster:
            df_display = pd.DataFrame(filtered_roster)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Tải về CSV
            csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=t("📥 Tải Danh Sách Nhân Sự (CSV)", "📥 Download Personnel Roster (CSV)"),
                data=csv_data,
                file_name=t("Danh_sach_nhan_su_BVN_Quang_Binh.csv", "BVN_Quang_Binh_Personnel_Roster.csv"),
                mime="text/csv"
            )
        else:
            st.info(t("Không tìm thấy nhân sự phù hợp với tiêu chí lọc.", "No personnel found matching filter criteria."))

    # ================= TAB 4: BẢNG TÍNH TRỰC TIẾP =================
    with t_sheet:
        st.markdown(f"#### {t('📑 Bảng Tính Nhân Sự & Cơ Cấu Trực Tiếp (Google Sheets Live)', '📑 Live Personnel & Org Google Sheets')}")
        st.caption(t("Xem hoặc chỉnh sửa trực tiếp dữ liệu nhân sự trên trang tính `Gốc Dữ liệu Sơ đồ khối` (gid=987654321) và `Định biên nhân sự` (gid=1942073054)", "Directly view or edit live personnel data on Google Sheets tab `Block Diagram Raw` (gid=987654321) and `Headcount Plan` (gid=1942073054)"))

        c_link1, c_link2, c_link3 = st.columns(3)
        with c_link1:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=987654321#gid=987654321" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;font-size:12.5px;font-weight:700;color:#1d4ed8;text-decoration:none;">{t("↗️ Tab Gốc Sơ Đồ Khối (gid=987654321)", "↗️ Live Diagram Raw Tab (gid=987654321)")}</a>', unsafe_allow_html=True)
        with c_link2:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=1942073054#gid=1942073054" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;font-size:12.5px;font-weight:700;color:#15803d;text-decoration:none;">{t("↗️ Tab Định Biên Nhân Sự (gid=1942073054)", "↗️ Headcount Plan Tab (gid=1942073054)")}</a>', unsafe_allow_html=True)
        with c_link3:
            st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid=1408180321#gid=1408180321" target="_blank" style="display:inline-block;width:100%;text-align:center;padding:8px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:6px;font-size:12.5px;font-weight:700;color:#7e22ce;text-decoration:none;">{t("↗️ Tab Hằng - Sơ Đồ Nhân Sự (gid=1408180321)", "↗️ HR Structure Tab (gid=1408180321)")}</a>', unsafe_allow_html=True)

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
            {t("TÀI LIỆU KỸ THUẬT VẬN HÀNH CHUẨN (SOP) • NHÀ MÁY BVN QUẢNG BÌNH", "STANDARD OPERATING PROCEDURES (SOP) • BVN QUANG BINH PLANT")}
        </div>
        <div class="proc-banner-title">{t("🌲 QUY TRÌNH CÔNG NGHỆ SẢN XUẤT VIÊN NÉN GỖ SINH KHỐI", "🌲 BIOMASS WOOD PELLET MANUFACTURING PROCESS FLOW")}</div>
        <div class="proc-banner-sub">
            {t("Cơ sở Thiết bị: <b>ANDRITZ</b> (Đan Mạch/Áo) • <b>PDI</b> (Mỹ) • <b>GreCon</b> (Đức) | Định chuẩn theo Sơ đồ Mã hóa Công đoạn 0 đến 7", "Equipment Base: <b>ANDRITZ</b> (Denmark/Austria) • <b>PDI</b> (USA) • <b>GreCon</b> (Germany) | Standardized Stages 0 to 7")}
        </div>
    </div>
    """)

    # Nút liên kết và trạng thái
    c_btn1, c_btn2 = st.columns([3.5, 1.5])
    with c_btn1:
        st.markdown(
            f'<div style="background: #eff6ff; border-left: 5px solid #2563eb; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #1e293b;">'
            f'<b style="color: #1d4ed8; font-size: 12.5px;">{t("💡 ĐÍNH CHÍNH QUAN TRỌNG VỀ TRÌNH TỰ CÔNG NGHỆ:", "💡 CRITICAL PROCESS SEQUENCE NOTE:")}</b> '
            f'{t("Tại BVN Quảng Bình, khâu <b>NGHIỀN THÔ (Mã 1)</b> diễn ra <b>TRƯỚC SẤY</b> đối với dăm tươi/ướt (nhân đôi hiệu suất bốc hơi), và <b>NGHIỀN TINH (Mã 4)</b> diễn ra <b>SAU SẤY</b> đối với vật liệu khô trước khi ép viên.", "At BVN Quang Binh, <b>WET GRINDING (Zone 1)</b> occurs <b>BEFORE DRYING</b> for green wood chips (doubling moisture evaporation efficiency), while <b>DRY GRINDING (Zone 4)</b> occurs <b>AFTER DRYING</b> for dry materials prior to pelletizing.")}'
            f'</div>', unsafe_allow_html=True
        )
    with c_btn2:
        st.markdown(
            f'<a href="{doc_url}" target="_blank" style="display:block; text-align:center; padding:10px 12px; background:#1e40af; color:#ffffff; font-weight:700; font-size:12.5px; border-radius:8px; text-decoration:none; box-shadow: 0 2px 6px rgba(30,58,138,0.3);">'
            f'{t("📄 Mở Tài Liệu SOP (Google Docs) ↗", "📄 Open SOP Document (Google Docs) ↗")}</a>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("Tổng Công Suất Nhà Máy", "Total Plant Capacity"), t("150.000 Tấn/Năm", "150,000 Tons/Yr"), t("Thực tế vận hành: 100.000 tấn", "Actual run rate: 100,000 tons"))
    with c2:
        st.metric(t("Cụm Máy Nghiền Sinh Khối", "Biomass Grinding Lines"), t("7 Tuyến Máy Lớn", "7 Major Lines"), t("4 Nghiền thô HM418 + 3 Nghiền tinh HM147-347", "4 Wet Grinders + 3 Dry Grinders"))
    with c3:
        st.metric(t("Cụm 8 Máy Ép ANDRITZ", "8 ANDRITZ Pellet Mills"), "8 × 355 kW", t("Model PM30-6 • Hộp số kép 10:1", "Model PM30-6 • 10:1 Dual Gearbox"))
    with c4:
        st.metric(t("An Toàn & Tách Từ", "Safety & Magnet Systems"), t("32 Cụm Nam Châm", "32 Magnet Stations"), t("GreCon dập lửa t = 0.25s • 5 Lớp tách từ", "GreCon spark sup. t = 0.25s • 5 Traps"))

    st.markdown("---")

    # 4 Sub-Tabs Chức Năng
    tab_flow, tab_safety, tab_mold, tab_doc = st.tabs([
        t("🔄 Chuỗi 7 Bước Công Nghệ (Mã 0 ➔ Mã 7)", "🔄 7-Step Technological Process (Zone 0 ➔ Zone 7)"),
        t("🛡️ Hệ Thống An Toàn Phòng Nổ & Tách Từ Tính", "🛡️ Explosion Safety & Magnetic Separation Systems"),
        t("🛠️ Kỹ Thuật Vận Hành & Tráng Khuôn ANDRITZ PM30-6", "🛠️ ANDRITZ PM30-6 Operation & Die Conditioning"),
        t("📑 Tra Cứu Toàn Văn Tài Liệu SOP (Google Docs Live)", "📑 SOP Full Documentation (Google Docs Live)")
    ])

    # ================= TAB 1: CHUỖI 7 BƯỚC CÔNG NGHỆ =================
    with tab_flow:
        st.markdown(f"#### {t('🔄 Trình Tự Vật Lý Dòng Nguyên Liệu Khép Kín (Mã Vùng 0 Đến Mã Vùng 7)', '🔄 Closed Physical Material Flow Sequence (Zone 0 to Zone 7)')}")

        # Bảng tóm tắt phân vùng
        if is_en():
            df_zones = pd.DataFrame([
                {"Zone Code": "Zone 0", "Process Step": "Wood Chipping & Storage", "Core Equipment": "Chipper CM108-CM2011, Belt Conveyor BE, Chain Conveyor DC", "Technological Target": "Convert round logs/wood waste into standard size chips"},
                {"Zone Code": "Zone 1", "Process Step": "Wet Wood Grinding", "Core Equipment": "Hammer Mill HM118-HM418 (400-450kW), Feeder FD", "Technological Target": "Reduce green chip size before entering the dryer drum"},
                {"Zone Code": "Zone 2", "Process Step": "Wet Chip / Sawdust Drying", "Core Equipment": "Rotary Dryer DR124/DR224, PDI Burner, Fan FA", "Technological Target": "Reduce moisture from ~45% down to 12-15%"},
                {"Zone Code": "Zone 4", "Process Step": "Dry Material Fine Grinding", "Core Equipment": "Fine Hammer Mill HM147-HM347 (450kW), Pulse-jet Filter FI", "Technological Target": "Grind dry sawdust to uniform fine powder before pelletizing"},
                {"Zone Code": "Zone 5", "Process Step": "Conditioning & Pelletizing", "Core Equipment": "8 ANDRITZ PM30-6 Pellet Mills (PE1510-8510), Conditioner CD", "Technological Target": "Extrude biomass pellets, oil lubrication & cooling"},
                {"Zone Code": "Zone 6", "Process Step": "Cooling & Screening", "Core Equipment": "Counterflow Cooler MD1520/2520, Vibrating Screen ST167/267", "Technological Target": "Cool pellets, cure natural lignin & screen fines"},
                {"Zone Code": "Zone 7", "Process Step": "Packaging & Shipping", "Core Equipment": "Rotary Magnet RMN, Metal Detector, Jumbo Scale LC169-469", "Technological Target": "Final metal inspection, Jumbo bag packing & export shipping"}
            ])
        else:
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
        if is_en():
            steps_data = [
                {
                    "step": "STEP 1", "code": "ZONE 0", "icon": "🪵", "color": "#0284c7",
                    "title": "Raw Material Receiving, Chipping & Primary Separation",
                    "equip": ["Log Crane", "Chipper CM108–CM2011", "Chain Conveyor DC203/204/206", "Belt Conveyor BE207/1013", "Hydraulic Walking Floor HP137-139", "4 Magnets (1-4)", "Stone Drawer"],
                    "content": """
                    • <b>Input Raw Material:</b> Round logs and forestry residues with FSC certification, strictly inspected by QC from purchase to unloading.<br>
                    • <b>Chipping Process:</b> Log crane feeds roundwood into Chipper Line 1 (CM108–CM1011) and Line 2 (CM208–CM2011). High-speed disc blades chop logs into uniform wood chips.<br>
                    • <b>Storage & Debris Control:</b> Green chips move to walking-floor storage HP137-HP139. Conveyor line includes <b>4 magnetic separators (Points 1-4)</b> and <b>Stone Drawer</b> to remove large iron and stones, protecting downstream mills.
                    """
                },
                {
                    "step": "STEP 2", "code": "ZONE 1", "icon": "🔨", "color": "#ea580c",
                    "title": "Wet Wood Chip Grinding (Occurs BEFORE Drying)",
                    "equip": ["Walking Floor", "Screw Conveyor SC112, SC211", "Metering Screw FD115-FD217", "Hammer Mill HM418 (400-450kW)", "10 Magnets (5-14)"],
                    "content": """
                    • <b>Wet Chip Infeed:</b> Green chips from storage are pushed by walking floors into feed screws supplying the wet grinding line.<br>
                    • <b>Wet Grinding Tech:</b> ANDRITZ HM418 hammer mills (<b>400kW - 450kW</b>) crush wet chips into small porous particles. Wet grinding before drying <b>doubles heat transfer area and doubles moisture evaporation rate</b> in the dryer drum.<br>
                    • <b>Dense Magnetic Array:</b> <b>10 magnetic separation points (Points 5 to 14)</b> stationed at HM418 chambers and infeed screws eliminate metal debris before entering the dryer.
                    """
                },
                {
                    "step": "STEP 3", "code": "ZONE 2", "icon": "🔥", "color": "#dc2626",
                    "title": "Wet Chip Drying (PDI Burner System - USA)",
                    "equip": ["Rotary Dryer DR124 & DR224 (315kW)", "PDI Burner 1 & 2", "Blower FA1211", "Exhaust Fan FA127/227", "Quench Valve DP1214", "PID Valve DP1217", "3 Magnets (15-17)"],
                    "content": """
                    • <b>Dryer Feeding:</b> Moist particles are conveyed into dual rotary drying drums DR124 & DR224 (315kW each).<br>
                    • <b>Heat & Pressure Regulation:</b> PDI Burners provide hot flue gas. Combustion chamber temperature T122 is regulated via quench valve DP1214 (safety trip T121 ≤ 1200°C). Air pressure maintained at P121 = 9–10 mbar; exhaust differential at P124 = 10 mbar.<br>
                    • <b>Moisture Control:</b> Outlet temperature auto-controlled < 149°C via PID valve DP1217. <b>Moisture drops from ~45% to standard 12% - 15%</b>. <b>3 magnets (Points 15-17)</b> safeguard post-dryer conveyors.
                    """
                },
                {
                    "step": "STEP 4", "code": "ZONE 4", "icon": "⚙️", "color": "#7c3aed",
                    "title": "Dry Material Fine Grinding (Occurs AFTER Drying)",
                    "equip": ["Distribution Conveyor SC141", "Rotary Airlock AL", "Feed Screw FD143-FD343", "3 ANDRITZ HM147-347 Mills (450kW)", "3 Magnets (18-20)", "Exhaust Fan FA1410-3410", "Pulse-jet Bag Filter FI1410-3410"],
                    "content": """
                    • <b>Dry Distribution:</b> Dried wood passes through distributor conveyor, rotary airlocks and screws to 3 fine hammer mills.<br>
                    • <b>Fine Pulverization:</b> 3 ANDRITZ HM147, HM247, HM347 mills (<b>450kW each</b>) grind dried chips into uniform fine wood flour (< 4-6mm) matching die hole diameter.<br>
                    • <b>Spark Defense & Magnets:</b> <b>3 magnetic separators (Points 18-20)</b> placed ahead of grinding chambers prevent friction sparks and dust explosion risks.<br>
                    • <b>Flour Recovery:</b> 110kW fans and Pulse-jet Bag Filters FI1410-3410 recover 100% fine powder while emitting clean air.
                    """
                },
                {
                    "step": "STEP 5", "code": "ZONE 5", "icon": "🏭", "color": "#059669",
                    "title": "Conditioning, Pelletizing & Auxiliaries (ANDRITZ PM30-6)",
                    "equip": ["Feed Screw SC151", "Conditioner CD156-856 (11kW)", "Water Mist Pump WP", "8 ANDRITZ PM30-6 Mills (355kW)", "Oil Chiller CH137-139", "Auto Grease Pump 1LP-8LP", "9 Magnets (21-29)"],
                    "content": """
                    • <b>Moisture Conditioning:</b> Wood powder enters 11kW Conditioner with water mist spray to achieve optimal <b>9-11% moisture</b>. Force Screw FS feeds mash into die chamber.<br>
                    • <b>8 ANDRITZ PM30-6 Pellet Mills:</b> <b>355kW motors</b> with 10:1 heavy-duty dual gearboxes. Rollers extrude wood through die holes into 6mm - 8mm pellets. Adjustable knives cut pellets to length.<br>
                    • <b>Automated Auxiliaries:</b> <b>9 magnetic traps (Point 21 main feed + Points 22-29 at mill doors)</b>. Gearbox oil chillers and 1LP-8LP auto-grease pumps provide continuous bearing lubrication.
                    """
                },
                {
                    "step": "STEP 6", "code": "ZONE 6", "icon": "❄️", "color": "#0284c7",
                    "title": "Cooling & Screening Area",
                    "equip": ["Vertical Bucket Elevator BC1514, BC2514", "Counterflow Cooler MD1520, MD2520", "Exhaust Fan FA132, FA153", "Vibrating Screen ST167, ST267", "3 Magnets (30-32)"],
                    "content": """
                    • <b>Hot Pellet Handling:</b> Freshly extruded pellets (80°C - 90°C) are elevated to cooler top.<br>
                    • <b>Cooling & Lignin Hardening:</b> Ambient air is drawn counterflow through the pellet bed, cooling pellets to < 35°C. Natural lignin solidifies, yielding mechanical durability DU ≥ 97.5%.<br>
                    • <b>Screening:</b> Pellets discharge onto vibrating screen ST167/267, removing 100% fines which are recycled back to pellet mills. Equipped with <b>3 magnetic separators (Points 30-32)</b>.
                    """
                },
                {
                    "step": "STEP 7", "code": "ZONE 7", "icon": "📦", "color": "#16a34a",
                    "title": "Metal Detection, Jumbo Bagging & Port Shipping",
                    "equip": ["Conveyor BE171, BE173", "Rotary Magnet RMN", "Metal Detector", "Level Switch HL166/266", "Two-way Diverter TW1517/167", "Jumbo Bag Scale LC169-469", "Overhead Magnet Vung Ang Port"],
                    "content": """
                    • <b>100% Metal Clearance:</b> Pellets pass through Rotary Magnet RMN (Points 30-32) and dedicated Metal Detector to ensure absolute zero metallic contamination.<br>
                    • <b>Automated Jumbo Bagging:</b> Pellets fill bins with high-level alarms. Automated load-cell scales fill <b>1,000 kg Jumbo bags</b>.<br>
                    • <b>Export Shipping:</b> Bags are loaded onto trucks to Vung Ang Port. Vessel loading conveyor features suspended cross-belt magnets for final quality assurance prior to ship hold loading.
                    """
                }
            ]
        else:
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
                    <span style="font-size: 11px; font-weight: 700; color: #64748b;">{t('Thiết bị trọng yếu: ', 'Critical Equipment: ')}</span>
                    {' '.join([f'<span class="proc-equip-badge">{eq}</span>' for eq in s['equip']])}
                </div>
                <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
                    {s['content']}
                </div>
            </div>
            """)

    # ================= TAB 2: HỆ THỐNG AN TOÀN & TÁCH TỪ TÍNH =================
    with tab_safety:
        st.markdown(f"#### {t('🛡️ Các Hệ Thống An Toàn, Phòng Nổ & Kiểm Soát Chất Lượng Đạt Chuẩn Xuất Khẩu', '🛡️ Safety, Explosion Prevention & Export Quality Control Systems')}")

        c_g1, c_g2 = st.columns([1.5, 1.2])
        with c_g1:
            st.markdown(f"##### {t('1. Hệ Thống Phòng Chống Cháy Nổ Tự Động GreCon (Đức)', '1. GreCon Automatic Spark Detection & Extinguishing System (Germany)')}")
            st.markdown(t("""
            Đặc thù sản xuất bột gỗ khô có nguy cơ cháy nổ bụi rất cao. Nhà máy BVN Quảng Bình đầu tư toàn bộ hệ thống phát hiện và dập tắt tia lửa **GreCon** trên các tuyến ống vận chuyển bột gỗ (Line L01 đến L07):
            - 📡 **Đầu dò hồng ngoại siêu nhạy:** Cảm biến `FM 1/8` và `DLD 1/9` phát hiện tia lửa ma sát nhỏ nhất trong ống dẫn.
            - 💧 **Dập lửa tức thì trong 0.25 giây:** Tủ trung tâm `Control Console CC7016` kích hoạt cụm dập lửa gồm bơm tăng áp, 2 bình tích áp màng 500L và vòi phun sương góc mở 120° dập tắt tia lửa trong thời gian cực ngắn **t = 0.25 giây**.
            - 📐 **Khoảng cách an toàn tối thiểu:**
            """, """
            Dry wood flour production carries high dust explosion risks. BVN Quang Binh Plant deploys a full German **GreCon** spark detection and extinguishing system across wood flour duct lines (Line L01 to L07):
            - 📡 **Ultra-Sensitive Infrared Detectors:** `FM 1/8` and `DLD 1/9` sensors detect friction sparks inside duct lines instantly.
            - 💧 **Instant Extinguishing in 0.25s:** Central `Control Console CC7016` triggers booster pumps, twin 500L accumulator vessels, and 120° atomizing mist nozzles to quench sparks within **t = 0.25 seconds**.
            - 📐 **Minimum Safety Distance:**
            """))
            st.latex(r"S = v \times t = 30\text{ m/s} \times 0.25\text{ s} = 7.5\text{ " + t("mét", "meters") + "}")
            st.markdown(t("""
            - 🛑 **Cơ chế ngắt dừng máy khẩn cấp:** Nếu cảm biến đếm số tia lửa **> 20 tia/lần** hoặc tần suất báo cháy **> 10 lần/30 phút**, hệ thống tự động phát lệnh ngắt `G147, G247, G347` dừng ngay lập tức máy nghiền tinh và lò đốt để ngăn ngừa thảm họa.
            """, """
            - 🛑 **Emergency Trip Interlock:** If spark count exceeds **> 20 sparks/event** or alarm frequency **> 10 times/30 min**, the system automatically issues emergency trips `G147, G247, G347` stopping fine hammer mills and burners immediately.
            """))

        with c_g2:
            st.markdown(f"##### {t('2. Ma Trận 32 Điểm Gắn Nam Châm Tách Từ (Bản Vẽ Rev 5.10)', '2. Matrix of 32 Magnetic Separator Stations (Drawing Rev 5.10)')}")
            st.caption(t("Chi tiết phân bổ 32 điểm tách từ tính bảo vệ thiết bị và kiểm soát chất lượng xuất khẩu:", "Allocation details of 32 magnetic stations protecting equipment and guaranteeing export purity:"))
            if is_en():
                df_magnets = pd.DataFrame([
                    {"Process Area": "Wood chip chipping (Zone 0)", "Drawing Zone": "Wood chip processing", "Stations": "4 points", "Point ID": "Points 1, 2, 3, 4", "Installation Location": "Chip belt conveyors & Stone Drawer trap"},
                    {"Process Area": "Wet grinding area (Zone 1)", "Drawing Zone": "Wet grinding area", "Stations": "10 points", "Point ID": "Points 5 to 14", "Installation Location": "HM418 hammer mill chutes & HP110-310 screws"},
                    {"Process Area": "Wet chip drying (Zone 2)", "Drawing Zone": "Dryer area", "Stations": "3 points", "Point ID": "Points 15, 16, 17", "Installation Location": "Conveying lines post-PDI rotary drying drum"},
                    {"Process Area": "Fine dry grinding (Zone 4)", "Drawing Zone": "Dry grinding area", "Stations": "3 points", "Point ID": "Points 18, 19, 20", "Installation Location": "Inlet chutes to 3 HM147-347 fine mills"},
                    {"Process Area": "ANDRITZ pelletizing (Zone 5)", "Drawing Zone": "Pelleting area", "Stations": "9 points", "Point ID": "Points 21 to 29", "Installation Location": "Point 21 (main feed) + Points 22-29 (8 PM30-6 doors)"},
                    {"Process Area": "Screening & Jumbo packing (Zone 6-7)", "Drawing Zone": "Screening area", "Stations": "3 points", "Point ID": "Points 30, 31, 32", "Installation Location": "ST167/267 screen, Rotary Magnet RMN & scale"}
                ])
            else:
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
                        label=t("📥 Tải Bản Vẽ Sơ Đồ Nam Châm Gốc (PDF Rev 5.10)", "📥 Download Original Magnet Layout Drawing (PDF Rev 5.10)"),
                        data=f_pdf.read(),
                        file_name="20250220R5.10-So_do_Nam_cham-Model.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            mag_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "so_do_nam_cham.png")
            if os.path.exists(mag_img_path):
                with st.expander(f"🔍 **{t('Xem Bản Vẽ Bố Trí 32 Điểm Nam Châm Trực Quan', 'View 32 Magnet Layout Drawing Online')}**", expanded=False):
                    st.image(mag_img_path, caption=t("Sơ đồ bố trí 32 điểm nam châm (Rev 5.10) - Nhà máy viên nén gỗ BVN Quảng Bình", "Layout of 32 magnetic separation points (Rev 5.10) - BVN Quang Binh Wood Pellet Plant"), use_container_width=True)

        st.markdown("---")
        st.markdown(f"##### {t('3. Kiểm Soát Chất Lượng KCS & Giám Sát Độ Ẩm SCADA Online', '3. QC Quality Inspection & Online SCADA Moisture Monitoring')}")
        col_qc1, col_qc2 = st.columns(2)
        with col_qc1:
            st.markdown(t("""
            - 📟 **Cảm biến đo ẩm Online HU301:** Gắn trực tiếp trên dây chuyền sấy và vận chuyển bột gỗ. Đồ thị độ ẩm truyền về trung tâm điều khiển SCADA và đồng bộ thời gian thực.
            - 🔬 **Phòng Thí Nghiệm KCS Nội Bộ:** Trang bị máy đo ẩm quét phổ hồng ngoại, lò nung độ tro, máy đo tỷ trọng viên nén và cân tiểu ly phân tích lấy mẫu 2 giờ/lần.
            """, """
            - 📟 **Online Moisture Sensor HU301:** Mounted directly along drying and conveying ducts. Moisture trend feeds continuously to the central SCADA terminal in real time.
            - 🔬 **In-House QC Laboratory:** Equipped with NIR moisture spectrometers, muffle ash furnace, pellet density analyzers, and precision scales sampling every 2 hours.
            """))
        with col_qc2:
            st.markdown(t("""
            - 🏢 **Kiểm Định Độc Lập VinaControl:** Định kỳ hàng tháng gửi mẫu viên nén thành phẩm kiểm tra độc lập tại Trung tâm Kiểm định VinaControl các chỉ tiêu:
              - *Độ ẩm:* `8.0 - 9.5%`
              - *Tỷ trọng:* `≥ 600 kg/m³`
              - *Độ bền cơ học (DU):* `≥ 97.5%`
              - *Độ tro:* `≤ 1.5%`
              - *Nhiệt lượng:* `≥ 4.000 kcal/kg`
            """, """
            - 🏢 **Independent Testing by VinaControl:** Finished pellet samples are sent monthly to accredited laboratory VinaControl:
              - *Moisture:* `8.0 - 9.5%`
              - *Bulk Density:* `≥ 600 kg/m³`
              - *Mechanical Durability (DU):* `≥ 97.5%`
              - *Ash Content:* `≤ 1.5%`
              - *Calorific Value:* `≥ 4,000 kcal/kg`
            """))

    # ================= TAB 3: KỸ THUẬT VẬN HÀNH & TRÁNG KHUÔN ANDRITZ PM30-6 =================
    with tab_mold:
        st.markdown(f"#### {t('🛠️ Hướng Dẫn Vận Hành Kỹ Thuật & Quy Trình Tráng Khuôn ANDRITZ PM30-6', '🛠️ Technical Operating Guide & ANDRITZ PM30-6 Die Conditioning Procedure')}")
        st.caption(t("Trích xuất từ hồ sơ kỹ thuật vận hành máy ép viên 355kW — Nhà máy BVN Quảng Bình", "Extracted from 355kW pellet mill technical operating dossier — BVN Quang Binh Plant"))

        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            t("✨ Tráng Mài Bóng Khuôn Mới", "✨ New Die Running-in"),
            t("🛑 Tráng Xả Dừng Máy Bắt Buộc", "🛑 Mandatory Shutdown Flushing"),
            t("📊 Bảng Thông Số Kiểm Soát", "📊 Parameter Control Table"),
            t("⚠️ Xử Lý Sự Cố & ATEX Zone 22", "⚠️ Troubleshooting & ATEX Zone 22")
        ])

        with sub_tab1:
            st.markdown(f"##### {t('I. QUY TRÌNH TRÁNG / MÀI BÓNG KHUÔN MỚI (DIE RUNNING-IN)', 'I. NEW DIE RUNNING-IN & POLISHING PROCEDURE')}")
            st.caption(t("Áp dụng khi thay mới khuôn hoặc sau khi mài phẳng lại bề mặt khuôn:", "Applied when installing new dies or after regrinding die surfaces:"))
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(t("""
                **1. Công thức hỗn hợp mài bóng (Abrasive Mixture):**
                - 🪵 `50 kg` bột gỗ mùn cưa tinh nghiền qua sàng mịn (< 1mm) hoặc cám gạo mịn.
                - 🏖️ `24 kg` cát mài kỹ thuật tiêu chuẩn (carborundum).
                - 🛢️ `3 lít` dầu bôi trơn công nghiệp sạch (kết dính và bôi trơn thành lỗ nén).
                """, """
                **1. Polishing / Abrasive Mixture Recipe:**
                - 🪵 `50 kg` fine wood sawdust screened < 1mm or fine rice bran.
                - 🏖️ `24 kg` standard carborundum abrasive sand.
                - 🛢️ `3 liters` clean industrial lubricant oil.
                """))
            with col_m2:
                st.markdown(t("""
                **2. Kiểm tra lắp ráp cơ khí trước khi chạy rà:**
                - 🔧 **Lực siết bu-lông khuôn:** 24 bu-lông M30 siết chéo đối xứng đạt **1000 Nm**.
                - 📏 **Khe hở vành mòn (Wear ring):** Tiêu chuẩn **0.3 mm ≤ X ≤ 1.8 mm**.
                - 🔄 **Cân chỉnh rulo:** Chỉnh khe hở rulo và khuôn vừa chạm nhẹ (**0.0 - 0.2 mm**).
                """, """
                **2. Pre-run Mechanical Assembly Verification:**
                - 🔧 **Die Bolt Torque:** 24 × M30 bolts torqued diagonally to **1000 Nm**.
                - 📏 **Wear Ring Clearance:** Standard **0.3 mm ≤ X ≤ 1.8 mm**.
                - 🔄 **Roller Gap Setting:** Adjust roller-to-die gap to slight contact (**0.0 - 0.2 mm**).
                """))
            st.markdown(t("""
            **3. Trình tự 5 bước vận hành mài bóng:**
            1. Khởi động bôi trơn hộp số (áp suất ≥ 5 bar), mở nước làm mát rulo (< 60°C).
            2. Chạy không tải động cơ chính 355kW trong 3 - 5 phút kiểm tra truyền động đai V.
            3. Cấp liệu mài bóng từ từ qua phễu ở tốc độ tối thiểu (0 - 10%), theo dõi dòng Ampe.
            4. Tuần hoàn hỗn hợp ép đùn nạp lại liên tục trong **0.5 - 1 giờ**.
            5. Nghiệm thu khi 100% lỗ nén đùn viên đồng đều, lòng lỗ bóng nhẵn và Ampe ổn định.
            """, """
            **3. 5-Step Polishing Sequence:**
            1. Start gearbox forced lube (P ≥ 5 bar), enable roller cooling water (< 60°C).
            2. Run 355kW main motor unladen for 3 - 5 min checking V-belt drive.
            3. Feed abrasive mixture slowly via chute at minimum feed rate (0 - 10%), monitor motor Amps.
            4. Recycle extruded mix back into feeder continuously for **0.5 - 1.0 hour**.
            5. Accept run when 100% die holes extrude uniformly, hole bores polished, and Amps stabilize.
            """))

        with sub_tab2:
            st.markdown(f"##### {t('II. QUY TRÌNH TRÁNG KHUÔN XẢ KHI DỪNG MÁY (SHUTDOWN FLUSHING)', 'II. MANDATORY SHUTDOWN FLUSHING PROCEDURE')}")
            st.warning(t("⚠️ **BẮT BUỘC THỰC HIỆN:** Phải tiến hành trước khi dừng máy kết thúc ca hoặc dừng máy dài ngày để ngăn chặn bột gỗ nướng cứng (>80°C) gây nghẹt đá khuôn.", "⚠️ **MANDATORY PRACTICE:** Must execute before shift shutdown or extended stops to prevent residual wood flour baking hard (>80°C) and seizing die holes."))
            col_x1, col_x2 = st.columns(2)
            with col_x1:
                st.markdown(t("""
                **1. Chuẩn bị nguyên liệu tráng:**
                - Viên nén thành phẩm ngâm dầu công nghiệp sạch.
                - ⚠️ **Lưu ý kỹ thuật:** Viên phải ngấm đều dầu nhưng **KHÔNG ĐƯỢC NGÂM QUÁ MỀM/NHÃO**. Viên nhão sẽ làm trượt rulo, mất lực đẩy tống mùn thô ra ngoài.
                """, """
                **1. Flushing Mixture Preparation:**
                - Finished wood pellets soaked in clean industrial oil.
                - ⚠️ **Technical Caution:** Pellets must absorb oil evenly but **MUST NOT BE OVER-SOAKED OR SOGGY**. Mushy pellets cause roller slipping and loss of pushing force.
                """))
            with col_x2:
                st.markdown(t("""
                **2. Trình tự 5 bước dừng máy:**
                - Giảm vít định lượng về 0%, ngắt cấp liệu, tắt bơm nước phun sương.
                - Cho bộ điều hòa (Conditioner) chạy không tải xả sạch tồn dư.
                - Đổ hỗn hợp viên dầu nén đẩy toàn bộ mùn cưa trong lỗ khuôn ra ngoài.
                - Xác nhận **100% lỗ khuôn đùn viên màu sẫm bóng đồng nhất của dầu**.
                - Dừng vít cấp liệu ➔ Dừng động cơ 355kW ➔ Dừng bơm dầu & làm mát.
                """, """
                **2. 5-Step Shutdown Sequence:**
                - Throttle metering screw to 0%, stop fresh infeed, shut off water mist spray.
                - Run Conditioner unladen to evacuate remaining mash.
                - Charge oil-soaked pellets to purge all dry sawdust out of die holes.
                - Confirm **100% die holes extrude glossy, dark oily pellets**.
                - Stop feeder screw ➔ Stop 355kW main motor ➔ Stop oil pump and cooling.
                """))

        with sub_tab3:
            st.markdown(f"##### {t('III. BẢNG THÔNG SỐ VÀ DỮ LIỆU KIỂM SOÁT KỸ THUẬT (PM30-6)', 'III. PM30-6 TECHNICAL SPECIFICATION & CONTROL MATRIX')}")
            if is_en():
                df_specs = pd.DataFrame([
                    {"Parameter": "Die Bolt Tightening Torque", "Standard": "1000 Nm", "Verification": "Torque wrench (24 × M30 nuts)", "Objective": "Prevent bolt loosening/fatigue, die centering"},
                    {"Parameter": "Wear Ring Radial Clearance", "Standard": "0.3 mm ≤ X ≤ 1.8 mm", "Verification": "Feeler gauge 0.2 mm", "Objective": "Guarantee taper clamping, protect quill shaft"},
                    {"Parameter": "Roller-to-Die Gap", "Standard": "0.0 - 0.2 mm (slight contact)", "Verification": "Manual rotation acoustic check", "Objective": "Prevent metal-to-metal impact chipping"},
                    {"Parameter": "Roller Shaft Bearing Temp", "Standard": "< 60°C", "Verification": "PT100 RTD sensor", "Objective": "Prevent premature bearing burnout"},
                    {"Parameter": "Press Chamber Temp at Stop", "Standard": "≥ 80°C", "Verification": "Thermometer gauge", "Objective": "Warning of severe hole glazing without oil purge"},
                    {"Parameter": "Lube Oil Delivery Pressure", "Standard": "≥ 5 bar (cold) / 1.5 bar (hot)", "Verification": "Lube pump pressure gauge", "Objective": "Forced lubrication to heavy gears & bearings"},
                    {"Parameter": "Die Hole Oil Purge Fill", "Standard": "100% hole area", "Verification": "Glossy pellets at discharge door", "Objective": "Rust inhibition & zero blockage on next restart"}
                ])
            else:
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
            st.markdown(f"##### {t('IV. XỬ LÝ SỰ CỐ & AN TOÀN LAO ĐỘNG (ATEX ZONE 22)', 'IV. TROUBLESHOOTING & ATEX ZONE 22 SAFETY')}")
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.error(t("❌ Rulo Trượt Mất Tải", "❌ Roller Slippage & Lost Traction"))
                st.markdown(t("• *Nguyên nhân:* Viên dầu quá nhão.<br>• *Khắc phục:* Nạp ngay bột khô/cám khô tăng ma sát kéo rulo quay lại.", "• *Root Cause:* Oily pellets too soggy.<br>• *Remedy:* Immediately feed dry flour/bran to restore friction traction."), unsafe_allow_html=True)
            with col_e2:
                st.warning(t("⚠️ Quá Tải Động Cơ Chính", "⚠️ Main Motor Overload"))
                st.markdown(t("• *Nguyên nhân:* Hỗn hợp mài quá đặc, nạp quá nhanh.<br>• *Khắc phục:* Giảm cấp liệu về 0%, xả tồn dư và tăng tải từ từ.", "• *Root Cause:* Abrasive mix too thick or fed too rapidly.<br>• *Remedy:* Reduce feeder to 0%, purge cavity and reload gradually."), unsafe_allow_html=True)
            with col_e3:
                st.error(t("🚫 Nghẹt Khuôn Ca Sau", "🚫 Die Seizure on Next Shift"))
                st.markdown(t("• *Nguyên nhân:* Tráng xả chưa đủ 100% lỗ.<br>• *Khắc phục:* Khoan thông lỗ chuyên dụng. Cấm dùng búa đục phá.", "• *Root Cause:* Oil purge failed to penetrate 100% holes.<br>• *Remedy:* Use drill press or dedicated bore clearing tools. Never chisel."), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(t("""
            **Quy định an toàn lao động & Chống cháy nổ:**
            - 🔥 **Bỏng nhiệt:** Nhiệt độ buồng ép khi dừng luôn **≥ 80°C**. Bắt buộc đeo găng tay chịu nhiệt và bảo hộ.
            - 🏗️ **Nâng hạ vật nặng:** Khuôn và rulo nặng trên 1 tấn, bắt buộc dùng tời nâng chuyên dụng (Die Crane).
            - 💥 **ATEX Zone 22:** Môi trường bụi sinh khối, tuyệt đối không tạo tia lửa điện khi mở cửa máy.
            - 🔒 **Lockout / Tagout:** Cắt cầu dao tổng và khóa thẻ cảnh báo trước khi thao tác bảo dưỡng.
            """, """
            **Workplace Safety & Explosion Prevention Regulations:**
            - 🔥 **Thermal Hazards:** Press chamber is always **≥ 80°C** upon shutdown. Wear heat-resistant PPE and safety gloves.
            - 🏗️ **Heavy Rigging:** Dies and rollers exceed 1 metric ton; always use the dedicated overhead Die Crane.
            - 💥 **ATEX Zone 22:** Biomass dust atmosphere; strictly prohibit electrical sparks or open flame when opening access doors.
            - 🔒 **Lockout / Tagout (LOTO):** Isolate main breakers and affix safety warning tags prior to servicing.
            """))

    # ================= TAB 4: TRA CỨU TOÀN VĂN GOOGLE DOCS =================
    with tab_doc:
        st.markdown(f"#### {t('📑 Tra Cứu Toàn Văn Tài Liệu SOP (Google Docs Live)', '📑 SOP Full Documentation (Google Docs Live)')}")
        st.caption(t("Xem toàn văn tài liệu Kỹ thuật Vận hành Chuẩn (SOP) được cập nhật đồng bộ từ Google Docs:", "View full standard operating procedures (SOP) document synchronized live from Google Docs:"))
        st.markdown(
            f'<div style="margin-bottom: 10px;">'
            f'<a href="{doc_url}" target="_blank" style="display:inline-block; padding:8px 16px; background:#2563eb; color:#ffffff; font-weight:700; font-size:13px; border-radius:6px; text-decoration:none;">'
            f'{t("🌐 Mở Trong Tab Mới (Google Docs Full View) ↗", "🌐 Open in New Tab (Google Docs Full View) ↗")}</a>'
            f'</div>', unsafe_allow_html=True
        )
        components.iframe(doc_preview_url, height=750, scrolling=True)

"""
Giao diện Dashboard Báo Cáo Sản Xuất Tự Động - Nhà Máy Viên Nén Gỗ
Chạy bằng lệnh: streamlit run app.py
"""
import os
import sys
import re
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
import io
from process_and_org_chart import render_organization_chart, render_wood_pellet_process_and_die_conditioning
from schematic_diagram import render_factory_schematic_diagram
from data_entry import (
    render_data_entry_module, 
    get_current_user, 
    logout_user,
    check_viewer_authorization,
    render_viewer_lock_screen,
    logout_viewer,
    AUTHORIZED_VIEWER_EMAIL
)

# Đường dẫn Logo BVN Quảng Bình
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_bvn.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join("assets", "logo_bvn.png")

logo_img = None
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    try:
        logo_img = Image.open(LOGO_PATH)
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

if not logo_b64:
    try:
        from logo_data import LOGO_BVN_BASE64
        logo_b64 = LOGO_BVN_BASE64
        logo_img = Image.open(io.BytesIO(base64.b64decode(logo_b64)))
    except Exception:
        pass

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Production",
    page_icon=logo_img if logo_img is not None else "🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại
st.markdown("""
<style>
    /* Metric Card Styling */
    .kpi-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-title {
        color: #6c757d;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: #1e293b;
        font-size: 28px;
        font-weight: 700;
        line-height: 1.2;
    }
    .kpi-unit {
        font-size: 14px;
        font-weight: 500;
        color: #64748b;
        margin-left: 4px;
    }
    .kpi-badge {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        margin-top: 6px;
    }
    .badge-success { background: #dcfce7; color: #15803d; }
    .badge-info { background: #e0f2fe; color: #0369a1; }
    .badge-warning { background: #fef3c7; color: #b45309; }
    .badge-danger { background: #fee2e2; color: #b91c1c; }
    
    /* Section headers */
    .section-title {
        font-size: 18px;
        font-weight: 800;
        color: var(--text-color, #1e293b);
        margin-top: 18px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Leader Dashboard Cards */
    .leader-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 18px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        margin-bottom: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 430px;
    }
    .leader-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(0,0,0,0.1);
    }
    .leader-card-long { border-top: 5px solid #2563eb; }
    .leader-card-sac { border-top: 5px solid #16a34a; }
    .leader-card-tai { border-top: 5px solid #ea580c; }
    .leader-card-tong { border-top: 5px solid #0f172a; }

    .leader-metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 13px;
    }
    .leader-metric-row:last-child {
        border-bottom: none;
    }
    .leader-metric-label {
        color: #64748b;
        font-weight: 500;
    }
    .leader-metric-val {
        font-weight: 700;
        color: #0f172a;
    }

    /* Sidebar Vertical Navigation Menu (Không chói, đều 1 hàng) */
    div[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 4px;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
        padding: 7px 10px;
        margin-bottom: 2px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        display: flex;
        align-items: center;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-size: 13px !important;
        line-height: 1.3 !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(56, 189, 248, 0.08);
        border-color: #38bdf8;
        transform: translateX(3px);
    }
    /* Active styling cho Nhóm 1: Vận hành (Muted Sky Blue dịu mắt) */
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_op_radio"]) div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(56, 189, 248, 0.14) !important;
        border-left: 4px solid #38bdf8 !important;
        border-color: #0284c7 !important;
        box-shadow: 0 2px 6px rgba(2,132,199,0.2);
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_op_radio"]) div[role="radiogroup"] > label:has(input:checked) p {
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }
    /* Active styling cho Nhóm 2: Quy trình & Sơ đồ (Muted Lavender dịu mắt) */
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_static_radio"]) div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(167, 139, 250, 0.14) !important;
        border-left: 4px solid #a78bfa !important;
        border-color: #7c3aed !important;
        box-shadow: 0 2px 6px rgba(124,58,237,0.2);
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_static_radio"]) div[role="radiogroup"] > label:has(input:checked) p {
        color: #c4b5fd !important;
        font-weight: 700 !important;
    }
    /* Active styling cho Nhóm 3: Nhập số liệu trực tiếp (Emerald Green) */
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_entry_radio"]) div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(16, 185, 129, 0.14) !important;
        border-left: 4px solid #10b981 !important;
        border-color: #059669 !important;
        box-shadow: 0 2px 6px rgba(5,150,105,0.2);
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(input[name*="sidebar_entry_radio"]) div[role="radiogroup"] > label:has(input:checked) p {
        color: #34d399 !important;
        font-weight: 700 !important;
    }
    /* Tối ưu hiển thị Responsive cho Thiết Bị Di Động (Mobile) & Tablet */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }
        .kpi-card {
            padding: 10px 14px !important;
            margin-bottom: 8px !important;
        }
        .kpi-value {
            font-size: 20px !important;
        }
        .leader-card {
            min-height: auto !important;
            padding: 12px 14px !important;
            margin-bottom: 12px !important;
        }
        .section-title {
            font-size: 15px !important;
            margin-top: 12px !important;
            margin-bottom: 8px !important;
        }
    }
    @media (max-width: 1024px) {
        .leader-card {
            min-height: 380px;
        }
    }
</style>
""", unsafe_allow_html=True)

from data_loader import DataLoader, DEFAULT_SHIFT_COLUMNS
from kpi_calculator import (
    classify_shift_counts,
    get_latest_day_kpis,
    get_equipment_statistics,
    get_shift_leader_kpis,
    get_kpi_leaderboard,
    get_incident_statistics,
    get_equipment_incident_alerts,
    get_all_leaders_dashboard_summary,
    evaluate_kpi_score,
    evaluate_electricity,
    evaluate_productivity,
    evaluate_moisture,
    evaluate_ash,
    evaluate_density,
    ELEC_MIN_BENCHMARK,
    ELEC_MAX_BENCHMARK,
    PRODUCTIVITY_TARGET,
    DENSITY_BENCHMARK_MIN,
    EQUIPMENT_INFO
)

@st.cache_data(ttl=300)
def load_all_factory_data():
    """Tải và lưu đệm dữ liệu từ cả 4 Google Sheets trong 5 phút"""
    loader = DataLoader()
    loader.connect()
    df_shifts = loader.load_shift_data()
    df_daily = loader.load_daily_summary()
    df_weekly = loader.load_weekly_report()
    df_monthly = loader.load_monthly_report()
    df_kcs = loader.load_kcs_data()
    df_diezen = loader.load_diezen_data()
    
    # Dữ liệu từ file KPI mới (2026 Nhat ky KPI)
    df_wm_weekly, df_wm_monthly = loader.load_wm_kpi_scores()
    leaders_kpi = loader.load_all_leaders_kpi()
    df_chart_moist = loader.load_kpi_chart_data('Chart moisture')
    df_chart_dien = loader.load_kpi_chart_data('Chart dien')
    df_chart_cap = loader.load_kpi_chart_data('Chart capacity')
    df_chart_sl = loader.load_kpi_sl_chart_data()

    # Dữ liệu Sự Cố và Bảo Trì mới
    df_incidents = loader.load_incident_data()
    df_maint_log = loader.load_maintenance_log()
    df_maint_plan = loader.load_maintenance_plan_monthly()
    df_4m = loader.load_4m_management()

    # Dữ liệu Quy Trình Chế Biến & Kỹ Thuật (ID: 1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw)
    process_data = loader.load_wood_pellet_process_data()

    # Dữ liệu Lịch Thay Nhớt Hộp Số Máy Ép PE1-PE8 (ID: 1DRHrUPkLk7650XbxW1zZ73dp0k0Dcg4FZeKZriUKRso)
    oil_change_data = loader.load_oil_change_data()

    return {
        'shifts': df_shifts,
        'daily': df_daily,
        'weekly': df_weekly,
        'monthly': df_monthly,
        'kcs': df_kcs,
        'diezen': df_diezen,
        'wm_weekly': df_wm_weekly,
        'wm_monthly': df_wm_monthly,
        'leaders_kpi': leaders_kpi,
        'chart_moist': df_chart_moist,
        'chart_dien': df_chart_dien,
        'chart_cap': df_chart_cap,
        'chart_sl': df_chart_sl,
        'incidents': df_incidents,
        'maint_log': df_maint_log,
        'maint_plan': df_maint_plan,
        'maint_4m': df_4m,
        'process_data': process_data,
        'oil_change_data': oil_change_data,
        'loader': loader,
        'prod_title': loader.spreadsheet.title if loader.spreadsheet else "2026 BVN QB Nhật kí sản xuất",
        'kpi_title': loader.kpi_spreadsheet.title if loader.kpi_spreadsheet else "2026 Nhat ky KPI",
        'maint_log_title': loader.maint_log_spreadsheet.title if loader.maint_log_spreadsheet else "2026 BẢO TRÌ BVN",
        'maint_plan_title': loader.maint_plan_spreadsheet.title if loader.maint_plan_spreadsheet else "Mainternance BVN QB",
        'oil_title': loader.oil_spreadsheet.title if loader.oil_spreadsheet else "Lịch thay nhớt hộp số máy ép"
    }

# ================= KIỂM TRA KHÓA CHẾ ĐỘ PUBLIC (CHỈ CẤP QUYỀN CHO SANGMCC1@GMAIL.COM) =================
if not check_viewer_authorization():
    render_viewer_lock_screen(logo_b64=logo_b64)
    st.stop()

# Load dữ liệu
try:
    with st.spinner("Đang kết nối 6 Google Sheets và nạp dữ liệu sản xuất, KPI, bảo trì, quy trình & lịch thay nhớt..."):
        data = load_all_factory_data()
        df_shifts = data['shifts']
        df_daily = data['daily']
        df_weekly = data['weekly']
        df_monthly = data['monthly']
        df_kcs = data['kcs']
        df_diezen = data['diezen']
        df_wm_weekly = data['wm_weekly']
        df_wm_monthly = data['wm_monthly']
        leaders_kpi = data['leaders_kpi']
        df_chart_moist = data['chart_moist']
        df_chart_dien = data['chart_dien']
        df_chart_cap = data['chart_cap']
        df_chart_sl = data.get('chart_sl', pd.DataFrame())
        df_incidents = data.get('incidents', pd.DataFrame())
        df_maint_log = data.get('maint_log', pd.DataFrame())
        df_maint_plan = data.get('maint_plan', pd.DataFrame())
        df_4m = data.get('maint_4m', pd.DataFrame())
        process_data = data.get('process_data', {})
        oil_change_data = data.get('oil_change_data', {'summary': pd.DataFrame(), 'details': {}, 'title': "Lịch thay nhớt hộp số máy ép"})
        app_loader = data.get('loader', None)
        sheet_title = data['prod_title']
        kpi_sheet_title = data['kpi_title']
        maint_log_title = data.get('maint_log_title', "2026 BẢO TRÌ BVN")
        maint_plan_title = data.get('maint_plan_title', "Mainternance BVN QB")
        oil_title = data.get('oil_title', "Lịch thay nhớt hộp số máy ép")
except Exception as e:
    st.error(f"❌ Không thể kết nối tới Google Sheets: {e}")
    st.info("Vui lòng kiểm tra file `credentials.json` và phân quyền chia sẻ bảng tính.")
    st.stop()

# Danh sách chuẩn 52 tuần và 12 tháng trong năm
ALL_WEEKS_52 = [f"Tuần {i}" for i in range(1, 53)]
ALL_MONTHS_12 = [f"Tháng {i}" for i in range(1, 13)]
ALL_MONTHS_CODE_12 = [f"{i:02d}/2026" for i in range(1, 13)]

# Tìm tuần và tháng mới nhất có dữ liệu thực tế để chọn làm mặc định
latest_kpi_w_str = df_wm_weekly['week_label'].iloc[-1] if not df_wm_weekly.empty else "Tuần 38"
default_w_idx = ALL_WEEKS_52.index(latest_kpi_w_str) if latest_kpi_w_str in ALL_WEEKS_52 else 37

latest_kpi_m_str = df_wm_monthly['month_label'].iloc[-1] if not df_wm_monthly.empty else "Tháng 9"
default_m_idx = ALL_MONTHS_12.index(latest_kpi_m_str) if latest_kpi_m_str in ALL_MONTHS_12 else 8
default_m_code_idx = 8 # Tháng 09/2026

# ================= DANH MỤC CỬA SỔ TÁC VỤ (PHÂN 3 NHÓM) =================
# Nhóm 1: Các tác vụ có hoạt động, có KPI, đo lường cập nhật hàng ngày (10 tác vụ)
OP_TASKS = [
    "📋 1. Nhật Ký Ca Sản Xuất",
    "🎯 2. Đánh Giá Xếp Hạng KPI",
    "📈 3. Xu Hướng Tuần & Tháng",
    "⚙️ 4. Giám Sát Thiết Bị",
    "🚨 5. Cảnh Báo Sự Cố",
    "🔧 6. Nhật Ký Bảo Trì",
    "🛠️ 7. Kế Hoạch Bảo Trì 4M",
    "🔬 8. Kiểm Định KCS",
    "⛽ 9. Quản Lý Dầu Diezen",
    "👤 10. Lịch Sử Ca Trưởng"
]

# Nhóm 2: Các tác vụ không có thay đổi và không có số liệu hàng ngày (3 tác vụ cố định)
STATIC_TASKS = [
    "👥 11. Sơ Đồ Nhân Sự",
    "🌲 12. Quy Trình Chế Biến Gỗ",
    "📐 13. Sơ Đồ Nguyên Lý"
]

# Nhóm 3: Nhập liệu & Báo cáo trực tiếp (Phân quyền & Bảo mật PIN cho Ca Trưởng/KCS)
ENTRY_TASKS = [
    "📝 14. Nhập Báo Cáo Ca & KCS"
]

TASK_LIST = OP_TASKS + STATIC_TASKS + ENTRY_TASKS

if 'active_task' not in st.session_state:
    st.session_state['active_task'] = OP_TASKS[0]

# Tự động đồng bộ trạng thái radio của 3 nhóm trước khi vẽ widget
_curr_active = st.session_state['active_task']
if _curr_active in OP_TASKS:
    st.session_state['sidebar_op_radio'] = _curr_active
    st.session_state['sidebar_static_radio'] = None
    st.session_state['sidebar_entry_radio'] = None
elif _curr_active in STATIC_TASKS:
    st.session_state['sidebar_static_radio'] = _curr_active
    st.session_state['sidebar_op_radio'] = None
    st.session_state['sidebar_entry_radio'] = None
else:
    st.session_state['sidebar_entry_radio'] = _curr_active
    st.session_state['sidebar_op_radio'] = None
    st.session_state['sidebar_static_radio'] = None

# ================= SIDEBAR =================
with st.sidebar:
    if logo_b64:
        st.markdown(f"""
        <div style="background: #ffffff; padding: 12px 16px; border-radius: 14px; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.12);">
            <img src="data:image/png;base64,{logo_b64}" style="width: 100%; max-height: 90px; object-fit: contain;">
        </div>
        <div style="text-align: center; margin-bottom: 14px;">
            <div style="font-size: 24px; font-weight: 800; letter-spacing: 2px; color: #16a34a; line-height: 1.2;">PRODUCTION</div>
            <div style="font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px;">BVN Quảng Bình</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.title("PRODUCTION")
        st.caption("BVN Quảng Bình")
    with st.expander("🟢 6/6 Google Sheets Tích Hợp", expanded=False):
        st.markdown(f"📗 **Sản xuất:** `{sheet_title}`")
        st.markdown(f"🎯 **Đánh giá KPI:** `{kpi_sheet_title}`")
        st.markdown(f"🔧 **Nhật ký bảo trì:** `{maint_log_title}`")
        st.markdown(f"🛠️ **Kế hoạch & 4M:** `{maint_plan_title}`")
        st.markdown("🌲 **Quy trình chế biến:** `1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw`")
        st.markdown(f"🛢️ **Lịch thay nhớt PE1-PE8:** `{oil_title}`")
    
    if st.button("🔄 Tải lại dữ liệu (Refresh)", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    # Hiển thị thông tin người xem hoặc Admin được cấp quyền
    v_auth = st.session_state.get("viewer_authorized_email")
    if v_auth == "admin":
        st.markdown(f"""
        <div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #eab308; border-radius: 8px; padding: 6px 10px; margin-top: 8px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 11px; font-weight: 700; color: #facc15;">
                <span>👑</span>
                <span>QUẢN TRỊ VIÊN (ADMIN)</span>
            </div>
            <span style="background: #ca8a04; color: white; padding: 1px 6px; border-radius: 4px; font-size: 9px; font-weight: 700;">TOÀN QUYỀN</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔒 Khóa Lại (Đăng Xuất)", key="btn_logout_viewer", use_container_width=True):
            logout_viewer()
    elif v_auth == AUTHORIZED_VIEWER_EMAIL:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 10px; margin-top: 8px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 11px; font-weight: 700; color: #38bdf8;">
                <span>👤</span>
                <span>{AUTHORIZED_VIEWER_EMAIL}</span>
            </div>
            <span style="background: #0284c7; color: white; padding: 1px 6px; border-radius: 4px; font-size: 9px; font-weight: 700;">QUYỀN XEM</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔒 Khóa Lại (Đăng Xuất)", key="btn_logout_viewer", use_container_width=True):
            logout_viewer()

    st.markdown("---")
    st.subheader("👤 Lọc Ca Trưởng")
    if 'shift_leader' in df_shifts.columns and not df_shifts.empty:
        available_leaders = ["Tất cả"] + sorted([str(l).strip() for l in df_shifts['shift_leader'].dropna().unique() if str(l).strip() != ''])
    else:
        available_leaders = ["Tất cả", "Long", "Sắc", "Tài"]
    selected_leader = st.selectbox("Ca Trưởng:", available_leaders, index=0)

    st.markdown("---")
    # Callbacks đồng bộ khi chọn trên sidebar
    def on_sb_op_nav_change():
        val = st.session_state.get('sidebar_op_radio')
        if val:
            st.session_state['active_task'] = val

    def on_sb_static_nav_change():
        val = st.session_state.get('sidebar_static_radio')
        if val:
            st.session_state['active_task'] = val

    def on_sb_entry_nav_change():
        val = st.session_state.get('sidebar_entry_radio')
        if val:
            st.session_state['active_task'] = val

    # Khối Nhóm 1: Vận hành & Đo lường KPI (Màu Slate dịu mắt, 1 dòng gọn gàng)
    st.markdown("""
    <div style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; border: 1px solid #334155; border-left: 4px solid #38bdf8; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
            <span>📊</span>
            <span>VẬN HÀNH & KPI</span>
        </div>
        <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">10 MỤC</span>
    </div>
    """, unsafe_allow_html=True)

    st.radio(
        "Nhóm 1 (Vận Hành & Đo Lường):",
        OP_TASKS,
        key="sidebar_op_radio",
        on_change=on_sb_op_nav_change,
        label_visibility="collapsed"
    )

    # Khối Nhóm 2: Quy trình & Sơ đồ chuẩn (Cố định - Màu Slate dịu mắt, 1 dòng gọn gàng)
    st.markdown("""
    <div style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-top: 12px; margin-bottom: 6px; border: 1px solid #334155; border-left: 4px solid #a78bfa; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
            <span>📘</span>
            <span>QUY TRÌNH & SƠ ĐỒ</span>
        </div>
        <span style="background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">3 MỤC</span>
    </div>
    """, unsafe_allow_html=True)

    st.radio(
        "Nhóm 2 (Quy Trình & Sơ Đồ Cố Định):",
        STATIC_TASKS,
        key="sidebar_static_radio",
        on_change=on_sb_static_nav_change,
        label_visibility="collapsed"
    )

    # Khối Nhóm 3: Nhập liệu & Báo cáo trực tiếp (Bảo mật mã PIN Ca Trưởng / KCS)
    curr_user = get_current_user()
    user_status_badge = f"""<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">🟢 {curr_user.get('name', 'USER')}</span>""" if curr_user else """<span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">🔒 PIN</span>"""

    st.markdown(f"""
    <div style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-top: 12px; margin-bottom: 6px; border: 1px solid #334155; border-left: 4px solid #10b981; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
            <span>📝</span>
            <span>NHẬP BÁO CÁO CA</span>
        </div>
        {user_status_badge}
    </div>
    """, unsafe_allow_html=True)

    st.radio(
        "Nhóm 3 (Nhập Báo Cáo):",
        ENTRY_TASKS,
        key="sidebar_entry_radio",
        on_change=on_sb_entry_nav_change,
        label_visibility="collapsed"
    )

    st.markdown("---")
    with st.expander("📌 **ĐỊNH MỨC & TIÊU CHUẨN KỸ THUẬT**", expanded=False):
        st.markdown("""
        **⚙️ Mục 1: Định mức kỹ thuật:**
        - Suất điện chuẩn: `170 - 175 kWh/tấn`
        - Năng suất máy ép: `≥ 4.0 tấn/h`
        - Năng suất tổng chuyền: `≥ 30.0 tấn/h`
        - Chỉ số OEE: `≥ 85%`

        **🌲 Mục 2: Tiêu chuẩn KỸ THUẬT VIÊN NÉN GỖ (ISO 17225-2 / ENplus):**
        - Độ ẩm thành phẩm: `8.0 - 9.5%`
        - Độ tro: `≤ 1.5%`
        - Tỷ trọng thể tích: `≥ 600 kg/m³`
        - Độ bền cơ học (DU): `≥ 97.5%`
        - Nhiệt trị: `≥ 4.000 kcal/kg`
        - Tỷ lệ vụn cám: `≤ 1.0%`
        - Đường kính viên: `6 - 8 mm`
        """)


# ================= HEADER & BỘ LỌC THỜI GIAN ĐẦU TRANG =================
st.title("🏭 PRODUCTION | BÁO CÁO SẢN XUẤT BVN QUẢNG BÌNH")

# Xác định ngày có dữ liệu gần nhất và danh sách các ngày
max_date = df_shifts['date'].max() if ('date' in df_shifts.columns and not df_shifts.empty) else datetime.now()
min_date = df_shifts['date'].min() if ('date' in df_shifts.columns and not df_shifts.empty) else (datetime.now() - timedelta(days=30))

# Khởi tạo trạng thái bộ lọc trong st.session_state nếu chưa có
if 'top_view_mode' not in st.session_state:
    st.session_state['top_view_mode'] = "☀️ Ngày gần nhất"
if 'top_target_date' not in st.session_state:
    st.session_state['top_target_date'] = max_date.date()

# Hàm trợ giúp làm sạch chuỗi HTML (tránh markdown hiểu nhầm 4 khoảng trắng là code block)
def clean_html(raw_html: str) -> str:
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

# Danh sách chuẩn các chế độ lọc thời gian: Ngày / Tuần / Tháng / Năm / Khoảng ngày
time_modes = [
    "☀️ Theo Ngày",
    "📅 Theo Tuần",
    "📆 Theo Tháng",
    "🏛️ Theo Năm",
    "⏱️ Khoảng ngày"
]

default_idx = 0
curr_mode = st.session_state.get('top_view_mode', "☀️ Theo Ngày")
for i, tm in enumerate(time_modes):
    if ("Ngày" in curr_mode and "Ngày" in tm) or ("Tuần" in curr_mode and "Tuần" in tm) or ("Tháng" in curr_mode and "Tháng" in tm) or ("Năm" in curr_mode and "Năm" in tm) or ("Khoảng" in curr_mode and "Khoảng" in tm):
        default_idx = i
        break

# ================= HÀM TRỢ GIÚP TÍNH CHỈ SỐ TỒN KHO VIÊN NÉN THEO KỲ =================
def get_inventory_for_period(df_all_shifts: pd.DataFrame, target_end_date: Any = None, period_shifts: pd.DataFrame = None) -> float:
    """
    Tính chỉ số tồn kho viên nén (tấn) tại thời điểm kết thúc kỳ lọc (cuối ngày/tuần/tháng/năm/khoảng ngày).
    Tồn kho là chỉ số thời điểm (stock metric) của kho thành phẩm nhà máy.
    """
    if period_shifts is not None and not period_shifts.empty and 'ton_kho_tan' in period_shifts.columns:
        valid_p = period_shifts[period_shifts['ton_kho_tan'] > 0]
        if not valid_p.empty:
            return float(valid_p.iloc[-1]['ton_kho_tan'])
            
    if df_all_shifts is not None and not df_all_shifts.empty and 'ton_kho_tan' in df_all_shifts.columns:
        if target_end_date is not None:
            t_dt = pd.to_datetime(target_end_date).date()
            sub = df_all_shifts[(df_all_shifts['date'].dt.date <= t_dt) & (df_all_shifts['ton_kho_tan'] > 0)]
            if not sub.empty:
                return float(sub.iloc[-1]['ton_kho_tan'])
        sub_all = df_all_shifts[df_all_shifts['ton_kho_tan'] > 0]
        if not sub_all.empty:
            return float(sub_all.iloc[-1]['ton_kho_tan'])
            
    return 0.0

# ================= BỘ LỌC THỜI GIAN SẢN XUẤT (FULL WIDTH NHƯ HÌNH 2) =================
st.markdown("""<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-left: 5px solid #38bdf8; border-radius: 10px; padding: 10px 16px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<div style="font-size: 14px; font-weight: 800; color: #ffffff; letter-spacing: 0.3px; display: flex; align-items: center; justify-content: space-between;">
<span>📅 BỘ LỌC THỜI GIAN</span>
<span style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">NGÀY / TUẦN / THÁNG / NĂM</span>
</div>
</div>""", unsafe_allow_html=True)

view_mode = st.radio(
    "Chọn hình thức lọc:",
    time_modes,
    index=default_idx,
    horizontal=True,
    key="main_view_mode_radio"
)
st.session_state['top_view_mode'] = view_mode

selected_date = max_date
date_range = (min_date, max_date)
selected_week_sidebar = None
selected_month_sidebar = None
selected_year_sidebar = None

if view_mode == "☀️ Theo Ngày":
    c_d1, c_d2, c_d3 = st.columns([5, 2.5, 2.5])
    with c_d1:
        avail_dates = sorted(df_shifts['date'].dt.date.unique(), reverse=True) if ('date' in df_shifts.columns and not df_shifts.empty) else [max_date.date()]
        default_d = st.session_state.get('top_target_date', max_date.date())
        if default_d not in avail_dates and len(avail_dates) > 0:
            default_d = avail_dates[0]
        picked_date = st.date_input(
            "Chọn ngày làm việc:",
            value=default_d,
            min_value=min_date.date(),
            max_value=max_date.date(),
            key="main_date_picker"
        )
        selected_date = datetime.combine(picked_date, datetime.min.time())
        st.session_state['top_target_date'] = picked_date
    with c_d2:
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
        if st.button("👉 Ngày đủ 3 ca (13/09)", help="Nhảy nhanh đến ngày 13/09/2026: Cả 3 Ca Trưởng đều chạy máy đầy đủ!", use_container_width=True):
            st.session_state['top_view_mode'] = "☀️ Theo Ngày"
            st.session_state['top_target_date'] = datetime(2026, 9, 13).date()
            st.rerun()
    with c_d3:
        inv_val_peek = get_inventory_for_period(df_shifts, selected_date)
        st.markdown(f"""
        <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 12px; margin-top: 24px; text-align: center; box-shadow: 0 2px 6px rgba(2,132,199,0.15);">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 700;">📦 TỒN KHO VIÊN NÉN</div>
            <div style="font-size: 16px; font-weight: 800; color: #38bdf8; line-height: 1.2;">{inv_val_peek:,.1f} <span style="font-size: 11px; font-weight: 600; color: #cbd5e1;">tấn</span></div>
        </div>
        """, unsafe_allow_html=True)

elif view_mode == "📅 Theo Tuần":
    c_w1, c_w2 = st.columns([7, 3])
    with c_w1:
        selected_week_sidebar = st.selectbox("Chọn tuần trong năm 2026:", ALL_WEEKS_52, index=default_w_idx, key="main_week_select")
        selected_date = None
    with c_w2:
        w_num_peek = int(selected_week_sidebar.replace("Tuần ", "")) if selected_week_sidebar else None
        w_peek = df_shifts[df_shifts['date'].dt.isocalendar().week == w_num_peek] if (w_num_peek and 'date' in df_shifts.columns) else None
        inv_w_peek = get_inventory_for_period(df_shifts, w_peek['date'].max() if (w_peek is not None and not w_peek.empty) else None, w_peek)
        st.markdown(f"""
        <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 12px; margin-top: 24px; text-align: center; box-shadow: 0 2px 6px rgba(2,132,199,0.15);">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 700;">📦 TỒN KHO CUỐI TUẦN</div>
            <div style="font-size: 16px; font-weight: 800; color: #38bdf8; line-height: 1.2;">{inv_w_peek:,.1f} <span style="font-size: 11px; font-weight: 600; color: #cbd5e1;">tấn</span></div>
        </div>
        """, unsafe_allow_html=True)

elif view_mode == "📆 Theo Tháng":
    c_m1, c_m2 = st.columns([7, 3])
    with c_m1:
        selected_month_sidebar = st.selectbox("Chọn tháng trong năm 2026:", ALL_MONTHS_CODE_12, index=default_m_code_idx, key="main_month_select")
        selected_date = None
    with c_m2:
        m_num_peek, y_num_peek = map(int, selected_month_sidebar.split('/')) if selected_month_sidebar else (9, 2026)
        m_peek = df_shifts[(df_shifts['date'].dt.month == m_num_peek) & (df_shifts['date'].dt.year == y_num_peek)] if 'date' in df_shifts.columns else None
        inv_m_peek = get_inventory_for_period(df_shifts, m_peek['date'].max() if (m_peek is not None and not m_peek.empty) else None, m_peek)
        st.markdown(f"""
        <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 12px; margin-top: 24px; text-align: center; box-shadow: 0 2px 6px rgba(2,132,199,0.15);">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 700;">📦 TỒN KHO CUỐI THÁNG</div>
            <div style="font-size: 16px; font-weight: 800; color: #38bdf8; line-height: 1.2;">{inv_m_peek:,.1f} <span style="font-size: 11px; font-weight: 600; color: #cbd5e1;">tấn</span></div>
        </div>
        """, unsafe_allow_html=True)

elif view_mode == "🏛️ Theo Năm":
    c_y1, c_y2 = st.columns([7, 3])
    with c_y1:
        selected_year_sidebar = 2026
        st.selectbox("Chọn năm vận hành:", ["Năm 2026 (Toàn bộ 229 ngày làm việc)"], index=0, key="main_year_select")
        selected_date = None
    with c_y2:
        inv_y_peek = get_inventory_for_period(df_shifts, df_shifts['date'].max() if not df_shifts.empty else None, df_shifts)
        st.markdown(f"""
        <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 12px; margin-top: 24px; text-align: center; box-shadow: 0 2px 6px rgba(2,132,199,0.15);">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 700;">📦 TỒN KHO NĂM 2026</div>
            <div style="font-size: 16px; font-weight: 800; color: #38bdf8; line-height: 1.2;">{inv_y_peek:,.1f} <span style="font-size: 11px; font-weight: 600; color: #cbd5e1;">tấn</span></div>
        </div>
        """, unsafe_allow_html=True)

elif view_mode == "⏱️ Khoảng ngày":
    c_r1, c_r2 = st.columns([7, 3])
    with c_r1:
        date_range_input = st.date_input(
            "Chọn khoảng ngày:",
            value=(max_date.date() - timedelta(days=14), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
            key="main_range_picker"
        )
        if isinstance(date_range_input, tuple) and len(date_range_input) == 2:
            date_range = (
                datetime.combine(date_range_input[0], datetime.min.time()),
                datetime.combine(date_range_input[1], datetime.max.time())
            )
            selected_date = None
    with c_r2:
        end_d_peek = date_range[1] if (isinstance(date_range_input, tuple) and len(date_range_input) == 2) else max_date
        inv_r_peek = get_inventory_for_period(df_shifts, end_d_peek)
        st.markdown(f"""
        <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 12px; margin-top: 24px; text-align: center; box-shadow: 0 2px 6px rgba(2,132,199,0.15);">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 700;">📦 TỒN KHO CUỐI KỲ</div>
            <div style="font-size: 16px; font-weight: 800; color: #38bdf8; line-height: 1.2;">{inv_r_peek:,.1f} <span style="font-size: 11px; font-weight: 600; color: #cbd5e1;">tấn</span></div>
        </div>
        """, unsafe_allow_html=True)

# Lọc dữ liệu theo ca trưởng nếu có
df_filtered_shifts = df_shifts.copy()
if selected_leader != "Tất cả" and 'shift_leader' in df_filtered_shifts.columns:
    df_filtered_shifts = df_filtered_shifts[df_filtered_shifts['shift_leader'] == selected_leader]

# Tính KPI cho ngày/tuần/tháng/năm được chọn
if view_mode == "📅 Theo Tuần" and selected_week_sidebar:
    w_num = int(selected_week_sidebar.replace("Tuần ", ""))
    w_shifts = df_filtered_shifts[df_filtered_shifts['date'].dt.isocalendar().week == w_num] if ('date' in df_filtered_shifts.columns and not df_filtered_shifts.empty) else pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)
    tot_out = float(w_shifts['san_luong_tan'].sum())
    tot_h = float(w_shifts['tong_gio_ep'].sum())
    tot_kwh = float(w_shifts['dien_kwh'].sum())
    avg_e = tot_kwh / tot_out if tot_out > 0 else 0.0
    avg_p = tot_out / tot_h if tot_h > 0 else 0.0
    ratio_w = float(w_shifts['nghien_tho_tan'].sum() / tot_out) if tot_out > 0 and 'nghien_tho_tan' in w_shifts.columns else 0.0

    eq_w = {}
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        h_val = float(w_shifts[col].sum()) if col in w_shifts.columns else 0.0
        eq_w[code] = {
            'code': code,
            'name': info['name'],
            'brand': info['brand'],
            'group': info['group'],
            'hours': round(h_val, 1)
        }
    group_h_w = {
        'Nghiền búa thô': sum(eq_w[c]['hours'] for c in ['HM118', 'HM218', 'HM318']),
        'Trống sấy': sum(eq_w[c]['hours'] for c in ['DR124', 'DR224']),
        'Nghiền búa tinh': sum(eq_w[c]['hours'] for c in ['HM147', 'HM247', 'HM347']),
        'Máy ép viên': sum(eq_w[f'PE{i}']['hours'] for i in range(1, 9)),
    }

    w_shift_details = []
    if not w_shifts.empty and 'shift_leader' in w_shifts.columns:
        for ldr, g in w_shifts.groupby('shift_leader'):
            if not ldr:
                continue
            l_out = float(g['san_luong_tan'].sum())
            l_h = float(g['tong_gio_ep'].sum())
            l_kwh = float(g['dien_kwh'].sum())
            l_ns = l_out / l_h if l_h > 0 else 0.0
            l_e = l_kwh / l_out if l_out > 0 else 0.0
            w_shift_details.append({
                'ca_truong': ldr,
                'san_luong_tan': round(l_out, 1),
                'tong_gio_ep': round(l_h, 1),
                'nang_suat_tph': round(l_ns, 2),
                'ns_eval': evaluate_productivity(l_ns),
                'dien_kwh': round(l_kwh, 0),
                'dien_tb_kwh_tan': round(l_e, 1),
                'elec_eval': evaluate_electricity(l_e),
                'nl_dot_tan': round(float(g['nl_dot_tan'].sum()) if 'nl_dot_tan' in g.columns else 0.0, 1),
                'nghien_tho_tan': round(float(g['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in g.columns else 0.0, 1),
            })

    num_days_w = int(w_shifts['date'].dt.date.nunique()) if not w_shifts.empty and 'date' in w_shifts.columns else 0
    is_single_ldr = (selected_leader != "Tất cả")
    prod_w, maint_w, off_w = classify_shift_counts(w_shifts, num_days=num_days_w, is_single_leader=is_single_ldr)
    ton_kho_w = get_inventory_for_period(df_shifts, w_shifts['date'].max() if not w_shifts.empty else None, w_shifts)
    tot_xuat_w = float(w_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in w_shifts.columns else 0.0

    kpis = {
        'date_str': f"{selected_week_sidebar} (Năm 2026)",
        'num_shifts': len(w_shifts),
        'prod_shifts': prod_w,
        'maint_shifts': maint_w,
        'off_shifts': off_w,
        'ton_kho_tan': ton_kho_w,
        'xuat_hang_tan': tot_xuat_w,
        'total_output': tot_out,
        'delta_output': 0.0,
        'avg_electricity_kwh_ton': avg_e,
        'electricity_eval': evaluate_electricity(avg_e),
        'avg_productivity': avg_p,
        'productivity_eval': evaluate_productivity(avg_p),
        'total_pellet_hours': tot_h,
        'processing_ratio': ratio_w,
        'do_am_tb_pct': 8.5,
        'equipment_hours': eq_w,
        'group_hours': group_h_w,
        'shift_details': w_shift_details,
    }
elif view_mode == "📆 Theo Tháng" and selected_month_sidebar:
    m_num, y_num = map(int, selected_month_sidebar.split('/'))
    m_shifts = df_filtered_shifts[
        (df_filtered_shifts['date'].dt.month == m_num) & 
        (df_filtered_shifts['date'].dt.year == y_num)
    ] if ('date' in df_filtered_shifts.columns and not df_filtered_shifts.empty) else pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)
    tot_out = float(m_shifts['san_luong_tan'].sum())
    tot_h = float(m_shifts['tong_gio_ep'].sum())
    tot_kwh = float(m_shifts['dien_kwh'].sum())
    avg_e = tot_kwh / tot_out if tot_out > 0 else 0.0
    avg_p = tot_out / tot_h if tot_h > 0 else 0.0
    ratio_m = float(m_shifts['nghien_tho_tan'].sum() / tot_out) if tot_out > 0 and 'nghien_tho_tan' in m_shifts.columns else 0.0

    eq_m = {}
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        h_val = float(m_shifts[col].sum()) if col in m_shifts.columns else 0.0
        eq_m[code] = {
            'code': code,
            'name': info['name'],
            'brand': info['brand'],
            'group': info['group'],
            'hours': round(h_val, 1)
        }
    group_h_m = {
        'Nghiền búa thô': sum(eq_m[c]['hours'] for c in ['HM118', 'HM218', 'HM318']),
        'Trống sấy': sum(eq_m[c]['hours'] for c in ['DR124', 'DR224']),
        'Nghiền búa tinh': sum(eq_m[c]['hours'] for c in ['HM147', 'HM247', 'HM347']),
        'Máy ép viên': sum(eq_m[f'PE{i}']['hours'] for i in range(1, 9)),
    }

    m_shift_details = []
    if not m_shifts.empty and 'shift_leader' in m_shifts.columns:
        for ldr, g in m_shifts.groupby('shift_leader'):
            if not ldr:
                continue
            l_out = float(g['san_luong_tan'].sum())
            l_h = float(g['tong_gio_ep'].sum())
            l_kwh = float(g['dien_kwh'].sum())
            l_ns = l_out / l_h if l_h > 0 else 0.0
            l_e = l_kwh / l_out if l_out > 0 else 0.0
            m_shift_details.append({
                'ca_truong': ldr,
                'san_luong_tan': round(l_out, 1),
                'tong_gio_ep': round(l_h, 1),
                'nang_suat_tph': round(l_ns, 2),
                'ns_eval': evaluate_productivity(l_ns),
                'dien_kwh': round(l_kwh, 0),
                'dien_tb_kwh_tan': round(l_e, 1),
                'elec_eval': evaluate_electricity(l_e),
                'nl_dot_tan': round(float(g['nl_dot_tan'].sum()) if 'nl_dot_tan' in g.columns else 0.0, 1),
                'nghien_tho_tan': round(float(g['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in g.columns else 0.0, 1),
            })

    num_days_m = int(m_shifts['date'].dt.date.nunique()) if not m_shifts.empty and 'date' in m_shifts.columns else 0
    is_single_ldr = (selected_leader != "Tất cả")
    prod_m, maint_m, off_m = classify_shift_counts(m_shifts, num_days=num_days_m, is_single_leader=is_single_ldr)
    ton_kho_m = get_inventory_for_period(df_shifts, m_shifts['date'].max() if not m_shifts.empty else None, m_shifts)
    tot_xuat_m = float(m_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in m_shifts.columns else 0.0

    kpis = {
        'date_str': f"Tháng {selected_month_sidebar}",
        'num_shifts': len(m_shifts),
        'prod_shifts': prod_m,
        'maint_shifts': maint_m,
        'off_shifts': off_m,
        'ton_kho_tan': ton_kho_m,
        'xuat_hang_tan': tot_xuat_m,
        'total_output': tot_out,
        'delta_output': 0.0,
        'avg_electricity_kwh_ton': avg_e,
        'electricity_eval': evaluate_electricity(avg_e),
        'avg_productivity': avg_p,
        'productivity_eval': evaluate_productivity(avg_p),
        'total_pellet_hours': tot_h,
        'processing_ratio': ratio_m,
        'do_am_tb_pct': round(float(df_daily[df_daily['date'].dt.month == m_num]['do_am_tb_pct'].mean()), 2) if not df_daily.empty and 'date' in df_daily.columns and (df_daily['date'].dt.month == m_num).any() and (df_daily[df_daily['date'].dt.month == m_num]['do_am_tb_pct'] > 0).any() else 8.5,
        'ty_trong_vien': round(float(df_daily[df_daily['date'].dt.month == m_num]['ty_trong_vien'].mean()), 1) if not df_daily.empty and 'date' in df_daily.columns and (df_daily['date'].dt.month == m_num).any() and (df_daily[df_daily['date'].dt.month == m_num]['ty_trong_vien'] > 0).any() else 640.0,
        'equipment_hours': eq_m,
        'group_hours': group_h_m,
        'shift_details': m_shift_details,
    }
    kpis['moisture_eval'] = evaluate_moisture(kpis['do_am_tb_pct'])
    kpis['density_eval'] = evaluate_density(kpis['ty_trong_vien'])
elif view_mode == "🏛️ Theo Năm":
    y_num = 2026
    y_shifts = df_filtered_shifts[df_filtered_shifts['date'].dt.year == y_num] if ('date' in df_filtered_shifts.columns and not df_filtered_shifts.empty) else pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)
    tot_out = float(y_shifts['san_luong_tan'].sum())
    tot_h = float(y_shifts['tong_gio_ep'].sum())
    tot_kwh = float(y_shifts['dien_kwh'].sum())
    avg_e = tot_kwh / tot_out if tot_out > 0 else 0.0
    avg_p = tot_out / tot_h if tot_h > 0 else 0.0
    ratio_y = float(y_shifts['nghien_tho_tan'].sum() / tot_out) if tot_out > 0 and 'nghien_tho_tan' in y_shifts.columns else 0.0

    eq_y = {}
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        h_val = float(y_shifts[col].sum()) if col in y_shifts.columns else 0.0
        eq_y[code] = {
            'code': code,
            'name': info['name'],
            'brand': info['brand'],
            'group': info['group'],
            'hours': round(h_val, 1)
        }
    group_h_y = {
        'Nghiền búa thô': sum(eq_y[c]['hours'] for c in ['HM118', 'HM218', 'HM318']),
        'Trống sấy': sum(eq_y[c]['hours'] for c in ['DR124', 'DR224']),
        'Nghiền búa tinh': sum(eq_y[c]['hours'] for c in ['HM147', 'HM247', 'HM347']),
        'Máy ép viên': sum(eq_y[f'PE{i}']['hours'] for i in range(1, 9)),
    }

    y_shift_details = []
    if not y_shifts.empty and 'shift_leader' in y_shifts.columns:
        for ldr, g in y_shifts.groupby('shift_leader'):
            if not ldr:
                continue
            l_out = float(g['san_luong_tan'].sum())
            l_h = float(g['tong_gio_ep'].sum())
            l_kwh = float(g['dien_kwh'].sum())
            l_ns = l_out / l_h if l_h > 0 else 0.0
            l_e = l_kwh / l_out if l_out > 0 else 0.0
            y_shift_details.append({
                'ca_truong': ldr,
                'san_luong_tan': round(l_out, 1),
                'tong_gio_ep': round(l_h, 1),
                'nang_suat_tph': round(l_ns, 2),
                'ns_eval': evaluate_productivity(l_ns),
                'dien_kwh': round(l_kwh, 0),
                'dien_tb_kwh_tan': round(l_e, 1),
                'elec_eval': evaluate_electricity(l_e),
                'nl_dot_tan': round(float(g['nl_dot_tan'].sum()) if 'nl_dot_tan' in g.columns else 0.0, 1),
                'nghien_tho_tan': round(float(g['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in g.columns else 0.0, 1),
            })

    num_days_y = int(y_shifts['date'].dt.date.nunique()) if not y_shifts.empty and 'date' in y_shifts.columns else 0
    is_single_ldr = (selected_leader != "Tất cả")
    prod_y, maint_y, off_y = classify_shift_counts(y_shifts, num_days=num_days_y, is_single_leader=is_single_ldr)
    ton_kho_y = get_inventory_for_period(df_shifts, y_shifts['date'].max() if not y_shifts.empty else None, y_shifts)
    tot_xuat_y = float(y_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in y_shifts.columns else 0.0

    kpis = {
        'date_str': f"Năm {y_num}",
        'num_shifts': len(y_shifts),
        'prod_shifts': prod_y,
        'maint_shifts': maint_y,
        'off_shifts': off_y,
        'ton_kho_tan': ton_kho_y,
        'xuat_hang_tan': tot_xuat_y,
        'total_output': tot_out,
        'delta_output': 0.0,
        'avg_electricity_kwh_ton': avg_e,
        'electricity_eval': evaluate_electricity(avg_e),
        'avg_productivity': avg_p,
        'productivity_eval': evaluate_productivity(avg_p),
        'total_pellet_hours': tot_h,
        'processing_ratio': ratio_y,
        'do_am_tb_pct': 8.5,
        'equipment_hours': eq_y,
        'group_hours': group_h_y,
        'shift_details': y_shift_details,
    }
    kpis['moisture_eval'] = evaluate_moisture(kpis['do_am_tb_pct'])
    kpis['density_eval'] = evaluate_density(kpis.get('ty_trong_vien', 640.0))
elif view_mode == "⏱️ Khoảng ngày" and date_range:
    r_start, r_end = date_range
    r_shifts = df_filtered_shifts[
        (df_filtered_shifts['date'] >= r_start) & 
        (df_filtered_shifts['date'] <= r_end)
    ] if ('date' in df_filtered_shifts.columns and not df_filtered_shifts.empty) else pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)
    tot_out = float(r_shifts['san_luong_tan'].sum())
    tot_h = float(r_shifts['tong_gio_ep'].sum())
    tot_kwh = float(r_shifts['dien_kwh'].sum())
    avg_e = tot_kwh / tot_out if tot_out > 0 else 0.0
    avg_p = tot_out / tot_h if tot_h > 0 else 0.0
    ratio_r = float(r_shifts['nghien_tho_tan'].sum() / tot_out) if tot_out > 0 and 'nghien_tho_tan' in r_shifts.columns else 0.0

    eq_r = {}
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        h_val = float(r_shifts[col].sum()) if col in r_shifts.columns else 0.0
        eq_r[code] = {
            'code': code,
            'name': info['name'],
            'brand': info['brand'],
            'group': info['group'],
            'hours': round(h_val, 1)
        }
    group_h_r = {
        'Nghiền búa thô': sum(eq_r[c]['hours'] for c in ['HM118', 'HM218', 'HM318']),
        'Trống sấy': sum(eq_r[c]['hours'] for c in ['DR124', 'DR224']),
        'Nghiền búa tinh': sum(eq_r[c]['hours'] for c in ['HM147', 'HM247', 'HM347']),
        'Máy ép viên': sum(eq_r[f'PE{i}']['hours'] for i in range(1, 9)),
    }

    r_shift_details = []
    if not r_shifts.empty and 'shift_leader' in r_shifts.columns:
        for ldr, g in r_shifts.groupby('shift_leader'):
            if not ldr:
                continue
            l_out = float(g['san_luong_tan'].sum())
            l_h = float(g['tong_gio_ep'].sum())
            l_kwh = float(g['dien_kwh'].sum())
            l_ns = l_out / l_h if l_h > 0 else 0.0
            l_e = l_kwh / l_out if l_out > 0 else 0.0
            r_shift_details.append({
                'ca_truong': ldr,
                'san_luong_tan': round(l_out, 1),
                'tong_gio_ep': round(l_h, 1),
                'nang_suat_tph': round(l_ns, 2),
                'ns_eval': evaluate_productivity(l_ns),
                'dien_kwh': round(l_kwh, 0),
                'dien_tb_kwh_tan': round(l_e, 1),
                'elec_eval': evaluate_electricity(l_e),
                'nl_dot_tan': round(float(g['nl_dot_tan'].sum()) if 'nl_dot_tan' in g.columns else 0.0, 1),
                'nghien_tho_tan': round(float(g['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in g.columns else 0.0, 1),
            })

    num_days_r = int(r_shifts['date'].dt.date.nunique()) if not r_shifts.empty and 'date' in r_shifts.columns else 0
    is_single_ldr = (selected_leader != "Tất cả")
    prod_r, maint_r, off_r = classify_shift_counts(r_shifts, num_days=num_days_r, is_single_leader=is_single_ldr)
    ton_kho_r = get_inventory_for_period(df_shifts, r_end, r_shifts)
    tot_xuat_r = float(r_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in r_shifts.columns else 0.0

    kpis = {
        'date_str': f"{r_start.strftime('%d/%m/%Y')} - {r_end.strftime('%d/%m/%Y')}",
        'num_shifts': len(r_shifts),
        'prod_shifts': prod_r,
        'maint_shifts': maint_r,
        'off_shifts': off_r,
        'ton_kho_tan': ton_kho_r,
        'xuat_hang_tan': tot_xuat_r,
        'total_output': tot_out,
        'delta_output': 0.0,
        'avg_electricity_kwh_ton': avg_e,
        'electricity_eval': evaluate_electricity(avg_e),
        'avg_productivity': avg_p,
        'productivity_eval': evaluate_productivity(avg_p),
        'total_pellet_hours': tot_h,
        'processing_ratio': ratio_r,
        'do_am_tb_pct': 8.5,
        'equipment_hours': eq_r,
        'group_hours': group_h_r,
        'shift_details': r_shift_details,
    }
    kpis['moisture_eval'] = evaluate_moisture(kpis['do_am_tb_pct'])
    kpis['density_eval'] = evaluate_density(kpis.get('ty_trong_vien', 640.0))
else:
    kpis = get_latest_day_kpis(df_filtered_shifts, df_daily, df_kcs=df_kcs, target_date=selected_date)
    if selected_leader != "Tất cả" and 'date' in df_filtered_shifts.columns and not df_filtered_shifts.empty and 'date' in kpis:
        k_dt = pd.to_datetime(kpis['date']).date()
        day_ldr_shifts = df_filtered_shifts[df_filtered_shifts['date'].dt.date == k_dt]
        p_c, m_c, o_c = classify_shift_counts(day_ldr_shifts, num_days=1, is_single_leader=True)
        kpis['prod_shifts'] = p_c
        kpis['maint_shifts'] = m_c
        kpis['off_shifts'] = o_c
    if 'ton_kho_tan' not in kpis or kpis.get('ton_kho_tan', 0) == 0:
        kpis['ton_kho_tan'] = get_inventory_for_period(df_shifts, selected_date)

# ================= THANH TRẠNG THÁI CA HOẠT ĐỘNG (GỌN GÀNG, KHÔNG BỊ TRÙNG LẶP) =================
sb_date = kpis.get('date_str', 'N/A')
sb_prod = int(kpis.get('prod_shifts', 0))
sb_maint = int(kpis.get('maint_shifts', 0))
sb_off = int(kpis.get('off_shifts', 0))
sb_ton_kho = float(kpis.get('ton_kho_tan', 0.0))
tot_s = sb_prod + sb_maint + sb_off
tot_denom = tot_s if tot_s > 0 else 1
pct_prod = (sb_prod / tot_denom) * 100.0
pct_maint = (sb_maint / tot_denom) * 100.0
pct_off = (sb_off / tot_denom) * 100.0

st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-left: 5px solid #22c55e; border-radius: 8px; padding: 8px 16px; margin: 6px 0 14px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
    <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; flex-wrap: wrap;">
        <span style="color: #94a3b8; font-weight: 600;">⏱️ Trạng thái ca kỳ:</span>
        <code style="background: #0f172a; border: 1px solid #475569; padding: 2px 8px; border-radius: 6px; color: #38bdf8; font-weight: 700; font-family: monospace; font-size: 11.5px;">{sb_date}</code>
        <span style="color: #475569;">|</span>
        <span style="color: #86efac; font-weight: 700; background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">🏭 {sb_prod} ca sản xuất ({pct_prod:.0f}%)</span>
        <span style="color: #fde68a; font-weight: 700; background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">🔧 {sb_maint} ca bảo trì ({pct_maint:.0f}%)</span>
        <span style="color: #cbd5e1; font-weight: 700; background: rgba(148, 163, 184, 0.15); border: 1px solid #94a3b8; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">☕ {sb_off} ca nghỉ ({pct_off:.0f}%)</span>
        <span style="color: #475569;">|</span>
        <span style="color: #38bdf8; font-weight: 800; background: rgba(14, 165, 233, 0.18); border: 1px solid #0284c7; padding: 2px 12px; border-radius: 12px; font-size: 11.5px; box-shadow: 0 0 10px rgba(56,189,248,0.2); display: inline-flex; align-items: center; gap: 5px;">
            <span>📦</span> <span>Tồn kho viên nén:</span> <strong style="color: #ffffff; font-size: 12.5px;">{sb_ton_kho:,.1f}</strong> <span>tấn</span>
        </span>
    </div>
    <div style="display: flex; align-items: center; gap: 14px; font-size: 12px; color: #94a3b8;">
        <div>📊 <strong>Tổng số:</strong> <span style="color: #ffffff; font-weight: 700;">{tot_s} ca</span></div>
        <div>🏢 <strong>Nhà máy:</strong> <span style="color: #4ade80; font-weight: 700;">BVN Quảng Bình</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Chuẩn bị chỉ số chất lượng dùng chung
am_val = float(kpis.get('do_am_tb_pct', 0))
moist_eval = kpis.get('moisture_eval', evaluate_moisture(am_val))
ty_trong_val = float(kpis.get('ty_trong_vien', 0))
dens_eval = kpis.get('density_eval', evaluate_density(ty_trong_val))

# Tính toán dữ liệu Dashboard cho cả 3 Ca Trưởng và Toàn Nhà Máy
active_w_num = int(selected_week_sidebar.replace("Tuần ", "")) if view_mode == "📅 Theo Tuần" and selected_week_sidebar else None
active_m_num = m_num if view_mode == "📆 Theo Tháng" and selected_month_sidebar else None
active_range = date_range if view_mode == "⏱️ Khoảng ngày" else None
active_t_date = selected_date if view_mode == "☀️ Theo Ngày" else None
active_y_num = 2026 if view_mode == "🏛️ Theo Năm" else None

all_db_summary = get_all_leaders_dashboard_summary(
    df_shifts=df_shifts,
    kpis_tong=kpis,
    df_daily=df_daily,
    df_kcs=df_kcs,
    df_chart_dien=df_chart_dien,
    df_chart_cap=df_chart_cap,
    df_chart_moist=df_chart_moist,
    leaders_kpi=leaders_kpi,
    df_wm_weekly=df_wm_weekly,
    df_wm_monthly=df_wm_monthly,
    df_incidents=df_incidents,
    target_date=active_t_date,
    week_num=active_w_num,
    month_num=active_m_num,
    date_range=active_range,
    year_num=active_y_num
)

# Hàm trợ giúp làm sạch chuỗi HTML (tránh markdown hiểu nhầm 4 khoảng trắng là code block)
def clean_html(raw_html: str) -> str:
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

# Banner tiêu đề phân mục chuẩn công nghiệp, tương thích hoàn hảo cả Light và Dark theme
def render_section_banner(title: str, subtitle: str = "", accent_color: str = "#2563eb") -> str:
    raw = f"""
    <div style="background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border-left: 5px solid {accent_color}; padding: 14px 20px; border-radius: 10px; margin: 18px 0 14px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <div style="font-size: 17px; font-weight: 800; color: #ffffff; letter-spacing: 0.2px;">{title}</div>
        <div style="font-size: 12px; font-weight: 600; color: #94a3b8;">{subtitle}</div>
    </div>
    """
    return clean_html(raw)

# Hàm trợ giúp hiển thị 1 thẻ KPI
def render_kpi_card_html(title, value, unit, badge_text, badge_cls="badge-info"):
    raw = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
        <div class="kpi-badge {badge_cls}">{badge_text}</div>
    </div>
    """
    return clean_html(raw)

# Hàm hiển thị 8 thẻ KPI của Toàn Nhà Máy
def render_factory_dashboard_cards(kpis_data, df_weekly_data):
    # Hàng 1: Vận hành & Năng suất (4 thẻ)
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    with r1_c1:
        delta_txt = f"{kpis_data.get('delta_output', 0):+,.1f} t so hôm trước" if kpis_data.get('delta_output', 0) != 0 else "Hôm nay"
        st.markdown(render_kpi_card_html("Sản Lượng Thực Tế", f"{kpis_data.get('total_output', 0):,.1f}", "Tấn", delta_txt, "badge-info"), unsafe_allow_html=True)
    with r1_c2:
        e_eval = kpis_data.get('electricity_eval', {})
        b_cls = "badge-success" if e_eval.get('status') == 'EXCELLENT' else ("badge-info" if e_eval.get('status') == 'STANDARD' else "badge-danger")
        st.markdown(render_kpi_card_html("Suất Điện Tiêu Hao", f"{kpis_data.get('avg_electricity_kwh_ton', 0):.1f}", "kWh/t", f"{e_eval.get('icon', '')} {e_eval.get('label', '')}", b_cls), unsafe_allow_html=True)
    with r1_c3:
        p_eval = kpis_data.get('productivity_eval', {})
        b_cls = "badge-success" if p_eval.get('status') == 'PASS' else "badge-warning"
        st.markdown(render_kpi_card_html("Năng Suất Ép TB", f"{kpis_data.get('avg_productivity', 0):.2f}", "Tấn/h", f"{p_eval.get('icon', '')} {p_eval.get('label', '')}", b_cls), unsafe_allow_html=True)
    with r1_c4:
        st.markdown(render_kpi_card_html("Tổng Giờ Máy Ép", f"{kpis_data.get('total_pellet_hours', 0):.1f}", "Giờ", "8 Máy Ép Viên", "badge-info"), unsafe_allow_html=True)

    # Hàng 2: Chất Lượng & Tiêu Hao (4 thẻ)
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    with r2_c1:
        a_val = kpis_data.get('do_am_tb_pct', 0)
        m_eval = kpis_data.get('moisture_eval', evaluate_moisture(a_val))
        b_cls = "badge-success" if m_eval.get('status') == 'PASS' else ("badge-warning" if m_eval.get('status') == 'WARN' else "badge-danger")
        st.markdown(render_kpi_card_html("Độ Ẩm TB Viên (Ngày)", f"{a_val:.2f}", "%", f"{m_eval.get('icon', '💧')} {m_eval.get('label', 'Chuẩn: 8.0 - 9.5%')}", b_cls), unsafe_allow_html=True)
    with r2_c2:
        ty_val = kpis_data.get('ty_trong_vien', 0)
        d_eval = kpis_data.get('density_eval', evaluate_density(ty_val))
        b_cls = "badge-success" if d_eval.get('status') == 'PASS' else ("badge-warning" if d_eval.get('status') == 'WARN' else "badge-info")
        st.markdown(render_kpi_card_html("Tỷ Trọng Viên Nén", f"{ty_val:,.1f}", "kg/m³", f"{d_eval.get('icon', '⚖️')} {d_eval.get('label', 'Chuẩn: ≥ 600 kg/m³')}", b_cls), unsafe_allow_html=True)
    with r2_c3:
        st.markdown(render_kpi_card_html("Tỷ Lệ Chế Biến", f"{kpis_data.get('processing_ratio', 0):.2f}", "lần", "Định mức: 1.8 - 2.1", "badge-info"), unsafe_allow_html=True)
    with r2_c4:
        lat_dz = df_weekly_data.iloc[-1]['diezen_lit'] if not df_weekly_data.empty else 0.0
        lat_dz_r = df_weekly_data.iloc[-1]['diezen_tb_lit_tan'] if not df_weekly_data.empty else 0.0
        st.markdown(render_kpi_card_html("Dầu Diezen Tiêu Thụ", f"{lat_dz_r:.1f}", "Lít/tấn", f"{lat_dz:,.0f} Lít/tuần", "badge-info"), unsafe_allow_html=True)

    # Hàng 3: Tồn Kho & Xuất Hàng Kho Thành Phẩm (Kho BVN Quảng Bình)
    tk_val = float(kpis_data.get('ton_kho_tan', 0.0))
    xh_val = float(kpis_data.get('xuat_hang_tan', 0.0))
    r3_c1, r3_c2 = st.columns(2)
    with r3_c1:
        st.markdown(render_kpi_card_html("Tồn Kho Viên Nén (Cuối Kỳ)", f"{tk_val:,.1f}", "Tấn", "📦 Kho Thành Phẩm BVN Quảng Bình", "badge-info"), unsafe_allow_html=True)
    with r3_c2:
        xh_badge = f"🚛 {xh_val:,.1f} Tấn xuất kho" if xh_val > 0 else "Chưa phát sinh xuất hàng trong kỳ"
        xh_cls = "badge-success" if xh_val > 0 else "badge-info"
        st.markdown(render_kpi_card_html("Lũy Kế Xuất Hàng (Trong Kỳ)", f"{xh_val:,.1f}", "Tấn", xh_badge, xh_cls), unsafe_allow_html=True)

    # Cảnh báo nổi bật
    e_eval = kpis_data.get('electricity_eval', {})
    if e_eval.get('status') == 'WARNING':
        st.error(f"⚠️ **CẢNH BÁO ĐIỆN NĂNG:** Suất tiêu hao điện đạt **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, vượt định mức trần 175 kWh/tấn (+{e_eval.get('diff')} kWh/tấn). Đề nghị kiểm tra phụ tải máy nghiền búa và hệ thống sấy.")
    elif e_eval.get('status') == 'EXCELLENT':
        st.success(f"✨ **HIỆU QUẢ CAO:** Suất tiêu hao điện chỉ **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, thấp hơn định mức chuẩn 170 kWh/tấn.")

    m_eval = kpis_data.get('moisture_eval', evaluate_moisture(kpis_data.get('do_am_tb_pct', 0)))
    if m_eval.get('status') == 'ALERT':
        st.error(f"💧 **CẢNH BÁO ĐỘ ẨM VIÊN CAO:** Độ ẩm trung bình đạt **{kpis_data.get('do_am_tb_pct', 0):.2f}%**, vượt trần 9.5%. Đề nghị kiểm tra nhiệt độ trống sấy.")
    elif m_eval.get('status') == 'WARN':
        st.warning(f"💧 **LƯU Ý ĐỘ ẨM VIÊN THẤP:** Độ ẩm trung bình đạt **{kpis_data.get('do_am_tb_pct', 0):.2f}%** (< 8.0%), viên nén có nguy cơ giòn.")

    if 0 < kpis_data.get('ty_trong_vien', 0) < DENSITY_BENCHMARK_MIN:
        st.warning(f"⚖️ **CẢNH BÁO TỶ TRỌNG:** Tỷ trọng viên nén đạt **{kpis_data.get('ty_trong_vien', 0):,.1f} kg/m³**, thấp hơn chuẩn xuất khẩu ({DENSITY_BENCHMARK_MIN:,.0f} kg/m³).")

# Hàm render nội dung thẻ của từng Ca Trưởng chuẩn công nghiệp (Đồng bộ 100% cấu trúc 3 Ca)
def render_leader_card_html(ldr: dict, key: str, view_period: str = "☀️ Theo Ngày") -> str:
    name = ldr.get('name', key)
    display_name = ldr.get('display_name', f"Ca Trưởng {name}")
    icon = ldr.get('icon', '👤')
    color = ldr.get('color', '#2563eb')
    bg_color = ldr.get('bg_color', '#eff6ff')
    border_color = ldr.get('border_color', '#3b82f6')
    badge_cls = ldr.get('badge_cls', 'leader-card-long')
    has_active = ldr.get('has_active_shift', False)
    
    # KPI Thi đua
    kpi_score = ldr.get('kpi_score', 0.0)
    kpi_eval = ldr.get('kpi_eval', {})
    kpi_medal = kpi_eval.get('medal', '🎗️')
    kpi_rank = kpi_eval.get('rank', 'Đạt chuẩn')
    kpi_color = kpi_eval.get('color', '#16a34a')
    
    # Dữ liệu chi tiết 3 kỳ: Ngày / Tuần / Tháng
    d_out = ldr.get('day_out', 0.0)
    d_shifts = ldr.get('day_shifts', 0)
    d_kwh = ldr.get('day_kwh_ton', 0.0)
    d_tph = ldr.get('day_tph', 0.0)
    d_hours = ldr.get('day_hours', 0.0)
    d_lbl = ldr.get('day_label', '')
    d_full_date = ldr.get('day_full_date', '')
    d_ratio = ldr.get('day_ratio', 0.0)
    d_nl_dot = ldr.get('day_nl_dot', 0.0)

    w_out = ldr.get('week_out', 0.0)
    w_shifts = ldr.get('week_shifts', 0)
    w_kwh = ldr.get('week_kwh_ton', 0.0)
    w_tph = ldr.get('week_tph', 0.0)
    w_hours = ldr.get('week_hours', 0.0)
    w_lbl = ldr.get('week_label', '')
    w_ratio = ldr.get('week_ratio', 0.0)
    w_nl_dot = ldr.get('week_nl_dot', 0.0)

    m_out = ldr.get('month_output', 0.0)
    m_shifts = ldr.get('month_shifts', 0)
    m_kwh = ldr.get('month_kwh_ton', 0.0)
    m_tph = ldr.get('month_tph', 0.0)
    m_hours = ldr.get('month_hours', 0.0)
    m_lbl = ldr.get('month_label', '')
    m_ratio = ldr.get('month_ratio', 0.0)
    m_nl_dot = ldr.get('month_nl_dot', 0.0)

    # 5. Độ ẩm viên TB & đánh giá (chuẩn ISO 17225-2 / ENplus: 8.0 - 9.5%)
    moist_val = ldr.get('moisture', 8.5)
    m_eval = ldr.get('moist_eval', evaluate_moisture(moist_val))
    m_label = m_eval.get('label', 'Chuẩn: 8.0 - 9.5%')
    m_color = "#15803d" if m_eval.get('status') == 'PASS' else "#b45309"

    duty_type = ldr.get('duty_type', 'PROD' if has_active else 'OFF')
    shift_count = ldr.get('shift_count', 1)
    period_lbl = ldr.get('period_label', '')

    # Huy hiệu trạng thái trực ca
    if duty_type == 'PROD':
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; white-space: nowrap;">🟢 Đang trực ca SX ({shift_count} ca)</div>"""
    elif duty_type == 'MAINT':
        m_cnt = ldr.get('maint_count', shift_count)
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #fffbeb; color: #92400e; border: 1px solid #fde68a; white-space: nowrap;">🔧 Trực Bảo trì - VS ({m_cnt} ca)</div>"""
    else:
        badge_lbl = f"⚪ Nghỉ ca ({period_lbl})" if period_lbl else "⚪ Nghỉ ca"
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #f8fafc; color: #64748b; border: 1px solid #cbd5e1; white-space: nowrap;">{badge_lbl}</div>"""

    # Thiết lập số liệu cho 6 ô chỉ số lớn theo kỳ chọn (view_period)
    if view_period == "📅 Theo Tuần":
        active_period_title = f"Tuần {w_lbl}"
        active_period_tag = "📅 TUẦN"
        highlight_day = "#ffffff"
        highlight_week = "#ecfdf5"
        highlight_month = "#ffffff"
        
        out_val = w_out
        out_title = "📦 Sản Lượng Tuần"
        out_disp = f"{out_val:,.1f}"
        out_sub = f"Lũy kế {w_shifts} ca tuần"
        out_sub_color = "#16a34a"

        kwh_val = w_kwh
        kwh_title = "⚡ Suất Điện TB Tuần"
        if kwh_val > 0:
            kwh_disp = f"{kwh_val:.1f}"
            e_eval = evaluate_electricity(kwh_val)
            e_label = e_eval.get('label', 'Đạt chuẩn')
            e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
        else:
            kwh_disp = "--"
            e_label = "Chờ số liệu"
            e_color = "#64748b"

        tph_val = w_tph
        tph_title = "⚙️ Năng Suất TB Tuần"
        p_eval = evaluate_productivity(tph_val)
        p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
        p_label = p_eval.get('label', 'Đạt chỉ tiêu') if tph_val > 0 else 'Chờ số liệu'
        p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

        hours_val = w_hours
        hours_title = "⏱️ Giờ Máy Ép Tuần"
        hours_disp = f"{hours_val:.1f}"
        hours_sub = f"{w_shifts} ca vận hành"

        ratio_val = w_ratio
        ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
        ratio_sub = f"NL đốt: {w_nl_dot:,.1f}t"

    elif view_period == "📆 Theo Tháng":
        active_period_title = f"{m_lbl}/2026"
        active_period_tag = "📆 THÁNG"
        highlight_day = "#ffffff"
        highlight_week = "#ffffff"
        highlight_month = "#faf5ff"

        out_val = m_out
        out_title = "📦 Sản Lượng Tháng"
        out_disp = f"{out_val:,.1f}"
        out_sub = f"Lũy kế {m_shifts} ca tháng"
        out_sub_color = "#7c3aed"

        kwh_val = m_kwh
        kwh_title = "⚡ Suất Điện TB Tháng"
        if kwh_val > 0:
            kwh_disp = f"{kwh_val:.1f}"
            e_eval = evaluate_electricity(kwh_val)
            e_label = e_eval.get('label', 'Đạt chuẩn')
            e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
        else:
            kwh_disp = "--"
            e_label = "Chờ số liệu"
            e_color = "#64748b"

        tph_val = m_tph
        tph_title = "⚙️ Năng Suất TB Tháng"
        p_eval = evaluate_productivity(tph_val)
        p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
        p_label = p_eval.get('label', 'Đạt chỉ tiêu') if tph_val > 0 else 'Chờ số liệu'
        p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

        hours_val = m_hours
        hours_title = "⏱️ Giờ Máy Ép Tháng"
        hours_disp = f"{hours_val:.1f}"
        hours_sub = f"{m_shifts} ca vận hành"

        ratio_val = m_ratio
        ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
        ratio_sub = f"NL đốt: {m_nl_dot:,.1f}t"

    else:
        # Mặc định: ☀️ Theo Ngày
        active_period_title = f"Ngày {d_full_date}" if d_full_date else "Hôm nay"
        active_period_tag = "☀️ NGÀY"
        highlight_day = "#f0f9ff"
        highlight_week = "#ffffff"
        highlight_month = "#ffffff"

        hours_title = "⏱️ Giờ Máy Ép"
        if duty_type == 'PROD':
            out_val = d_out if d_out > 0 else ldr.get('output', 0.0)
            out_pct = ldr.get('output_pct', 0.0)
            out_title = "📦 Sản Lượng Ca"
            out_disp = f"{out_val:,.1f}"
            out_sub = f"{out_pct:.0f}% tổng nhà máy" if out_pct > 0 else f"{d_shifts} ca vận hành"
            out_sub_color = "#0284c7"

            kwh_val = d_kwh if d_kwh > 0 else ldr.get('kwh_per_ton', 0.0)
            kwh_title = "⚡ Suất Tiêu Hao Điện"
            if kwh_val > 0:
                kwh_disp = f"{kwh_val:.1f}"
                e_eval = ldr.get('elec_eval', evaluate_electricity(kwh_val))
                e_label = e_eval.get('label', 'Đạt chuẩn')
                e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
            else:
                kwh_disp = "--"
                e_label = f"TB tháng: {m_kwh:.1f}" if m_kwh > 0 else "Chờ số liệu"
                e_color = "#64748b"

            tph_val = d_tph if d_tph > 0 else ldr.get('tph', 0.0)
            tph_title = "⚙️ Năng Suất Ép TB"
            p_eval = ldr.get('prod_eval', evaluate_productivity(tph_val))
            p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
            p_label = p_eval.get('label', 'Đạt chỉ tiêu') if tph_val > 0 else 'Đang chạy máy'
            p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

            hours_val = d_hours if d_hours > 0 else ldr.get('pellet_hours', 0.0)
            hours_disp = f"{hours_val:.1f}"
            hours_sub = f"{d_shifts} ca vận hành"

            ratio_val = d_ratio if d_ratio > 0 else ldr.get('processing_ratio', 0.0)
            nl_dot_val = d_nl_dot if d_nl_dot > 0 else ldr.get('nl_dot', 0.0)
            ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
            ratio_sub = f"NL đốt: {nl_dot_val:,.1f}t"
        elif duty_type == 'MAINT':
            m_cnt = ldr.get('maint_count', shift_count)
            out_title = "📦 Sản Lượng Ca"
            out_disp = "0.0"
            out_sub = "🔧 Trực Bảo trì - Vệ sinh"
            out_sub_color = "#d97706"

            kwh_title = "⚡ Suất Tiêu Hao Điện"
            kwh_disp = "--"
            e_label = "Bảo dưỡng máy"
            e_color = "#d97706"

            tph_title = "⚙️ Năng Suất Ép TB"
            p_disp = "--"
            p_label = "Bảo trì thiết bị"
            p_color = "#d97706"

            hours_disp = "0.0"
            hours_sub = f"{m_cnt} ca bảo trì"

            ratio_disp = "0.0"
            ratio_sub = "Bảo dưỡng xưởng"
        else:
            latest_date = ldr.get('latest_shift_date', 'N/A')
            latest_out = ldr.get('latest_shift_out', 0.0)
            out_title = "📦 Sản Lượng Ca"
            out_disp = "0.0"
            out_sub = f"Ca gần nhất: {latest_date} ({latest_out:,.1f}t)" if latest_date != 'N/A' else "Nghỉ ca"
            out_sub_color = "#64748b"

            kwh_title = "⚡ Suất Tiêu Hao Điện"
            kwh_disp = "--"
            e_label = f"TB tháng: {m_kwh:.1f}" if m_kwh > 0 else "Nghỉ ca"
            e_color = "#64748b"

            tph_title = "⚙️ Năng Suất Ép TB"
            p_disp = "--"
            p_label = f"TB tháng: {m_tph:.2f}" if m_tph > 0 else "Nghỉ ca"
            p_color = "#64748b"

            hours_disp = "0.0"
            hours_sub = "0 ca vận hành"

            ratio_disp = "--"
            ratio_sub = "Không phát sinh"

    moist_disp = f"{moist_val:.2f}" if has_active else "--"

    # Định dạng chuỗi hiển thị ở bảng Lũy kế 3 kỳ (Footer)
    day_kwh_str = f"{d_kwh:.1f} kWh/t" if d_kwh > 0 else ("-- kWh/t" if d_out == 0 else f"{m_kwh:.1f}*")
    day_tph_str = f"{d_tph:.2f} t/h" if d_tph > 0 else "-- t/h"
    day_kwh_c = "#15803d" if (0 < d_kwh <= 175) else ("#b91c1c" if d_kwh > 175 else "#64748b")
    day_tph_c = "#15803d" if d_tph >= 4.0 else ("#b45309" if d_tph > 0 else "#64748b")

    week_kwh_str = f"{w_kwh:.1f} kWh/t" if w_kwh > 0 else "-- kWh/t"
    week_tph_str = f"{w_tph:.2f} t/h" if w_tph > 0 else "-- t/h"
    week_kwh_c = "#15803d" if (0 < w_kwh <= 175) else ("#b91c1c" if w_kwh > 175 else "#64748b")
    week_tph_c = "#15803d" if w_tph >= 4.0 else ("#b45309" if w_tph > 0 else "#64748b")

    month_kwh_str = f"{m_kwh:.1f} kWh/t" if m_kwh > 0 else "-- kWh/t"
    month_tph_str = f"{m_tph:.2f} t/h" if m_tph > 0 else "-- t/h"
    month_kwh_c = "#15803d" if (0 < m_kwh <= 175) else ("#b91c1c" if m_kwh > 175 else "#64748b")
    month_tph_c = "#15803d" if m_tph >= 4.0 else ("#b45309" if m_tph > 0 else "#64748b")

    raw_card = f"""
    <div class="leader-card {badge_cls}">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 2px solid {border_color};">
                <div>
                    <div style="font-size: 16px; font-weight: 800; color: {color}; display: flex; align-items: center; gap: 6px;">
                        <span>{icon}</span> <span>{display_name.upper()}</span>
                    </div>
                    <div style="font-size: 11px; font-weight: 700; color: #475569; margin-top: 3px; display: flex; align-items: center; gap: 6px;">
                        <span style="background: {border_color}18; color: {color}; padding: 1px 6px; border-radius: 4px; font-weight: 800;">{active_period_tag}</span>
                        <span>{active_period_title}</span>
                    </div>
                </div>
                {duty_badge_html}
            </div>
            <div style="background: linear-gradient(135deg, #f8fafc 0%, {bg_color} 100%); border-radius: 8px; padding: 7px 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid {border_color}30;">
                <div style="font-size: 12px; font-weight: 700; color: #475569;">🏆 Thi Đua KPI:</div>
                <div style="font-size: 13px; font-weight: 800; color: {kpi_color};">
                    {kpi_score:.1f}đ <span style="font-size: 11px; font-weight: 700; color: #475569;">({kpi_medal} {kpi_rank})</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{out_title}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{out_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">tấn</span></div>
                    <div style="font-size: 10px; font-weight: 600; color: {out_sub_color}; margin-top: 2px;">{out_sub}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{kwh_title}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{kwh_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">kWh/t</span></div>
                    <div style="font-size: 10px; font-weight: 700; color: {e_color}; margin-top: 2px;">{e_label}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{tph_title}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{p_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">t/h</span></div>
                    <div style="font-size: 10px; font-weight: 700; color: {p_color}; margin-top: 2px;">{p_label}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{hours_title}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{hours_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">giờ</span></div>
                    <div style="font-size: 10px; font-weight: 600; color: #475569; margin-top: 2px;">{hours_sub}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">💧 Độ Ẩm Viên TB</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{moist_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">%</span></div>
                    <div style="font-size: 10px; font-weight: 700; color: {m_color}; margin-top: 2px;">{m_label}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">🔄 Tỷ Lệ Chế Biến</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{ratio_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">lần</span></div>
                    <div style="font-size: 10px; font-weight: 600; color: #475569; margin-top: 2px;">{ratio_sub}</div>
                </div>
            </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; margin-top: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; font-weight: 700; color: #334155; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #cbd5e1; padding-bottom: 4px;">
                <span>📊 LŨY KẾ 3 KỲ (NGÀY / TUẦN / THÁNG):</span>
                <span style="font-size: 10px; color: #64748b; font-weight: 600;">Sản Lượng | Ca | Điện | NS</span>
            </div>
            
            <!-- Dòng 1: Ngày -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 3px 6px; background: {highlight_day}; border: 1px solid {'#bae6fd' if highlight_day != '#ffffff' else '#f1f5f9'}; border-radius: 5px; margin-bottom: 3px; font-size: 11px;">
                <span style="font-weight: 700; color: #0284c7; display: flex; align-items: center; gap: 4px;">
                    <span>☀️</span> Ngày ({d_lbl}):
                </span>
                <span style="font-weight: 800; color: #0f172a;">
                    {d_out:,.1f}t <span style="font-size: 10px; font-weight: 600; color: #64748b;">({d_shifts} ca)</span> 
                    | <span style="color: {day_kwh_c}; font-weight: 700;">{day_kwh_str}</span>
                    | <span style="color: {day_tph_c}; font-weight: 700;">{day_tph_str}</span>
                </span>
            </div>

            <!-- Dòng 2: Tuần -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 3px 6px; background: {highlight_week}; border: 1px solid {'#bbf7d0' if highlight_week != '#ffffff' else '#f1f5f9'}; border-radius: 5px; margin-bottom: 3px; font-size: 11px;">
                <span style="font-weight: 700; color: #16a34a; display: flex; align-items: center; gap: 4px;">
                    <span>📅</span> Tuần ({w_lbl}):
                </span>
                <span style="font-weight: 800; color: #0f172a;">
                    {w_out:,.1f}t <span style="font-size: 10px; font-weight: 600; color: #64748b;">({w_shifts} ca)</span> 
                    | <span style="color: {week_kwh_c}; font-weight: 700;">{week_kwh_str}</span>
                    | <span style="color: {week_tph_c}; font-weight: 700;">{week_tph_str}</span>
                </span>
            </div>

            <!-- Dòng 3: Tháng -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 3px 6px; background: {highlight_month}; border: 1px solid {'#e9d5ff' if highlight_month != '#ffffff' else '#f1f5f9'}; border-radius: 5px; font-size: 11px;">
                <span style="font-weight: 700; color: #7c3aed; display: flex; align-items: center; gap: 4px;">
                    <span>📆</span> Tháng ({m_lbl}):
                </span>
                <span style="font-weight: 800; color: #0f172a;">
                    {m_out:,.1f}t <span style="font-size: 10px; font-weight: 600; color: #64748b;">({m_shifts} ca)</span> 
                    | <span style="color: {month_kwh_c}; font-weight: 700;">{month_kwh_str}</span>
                    | <span style="color: {month_tph_c}; font-weight: 700;">{month_tph_str}</span>
                </span>
            </div>
        </div>
    </div>
    """
    return clean_html(raw_card)

# Hàm hiển thị Dashboard 3 Ca Trưởng song song
def render_leaders_side_by_side(all_db, default_time_view: str = "☀️ Theo Ngày"):
    leaders = all_db.get('leaders', {})
    
    # Thanh điều khiển chọn kỳ trọng tâm hiển thị cho 3 Ca Trưởng
    col_banner_txt, col_banner_ctrl = st.columns([5, 5])
    with col_banner_txt:
        st.caption("💡 *Tùy chọn hiển thị 6 ô số liệu trọng tâm cho 3 Ca Trưởng. Bảng lũy kế 3 kỳ ở cuối thẻ luôn tổng hợp đầy đủ cả Ngày, Tuần, Tháng.*")
    with col_banner_ctrl:
        selected_kpi_time_view = st.segmented_control(
            "⏱️ **CHỌN KỲ HIỂN THỊ TRỌNG TÂM:**",
            options=["☀️ Theo Ngày", "📅 Theo Tuần", "📆 Theo Tháng"],
            default=default_time_view,
            key="leader_kpi_time_view_segmented"
        )
        if not selected_kpi_time_view:
            selected_kpi_time_view = default_time_view

    col_l, col_s, col_t = st.columns(3)
    leader_order = [('Long', col_l), ('Sắc', col_s), ('Tài', col_t)]

    for key, col in leader_order:
        ldr = leaders.get(key, {})
        with col:
            html = render_leader_card_html(ldr, key, view_period=selected_kpi_time_view)
            st.markdown(html, unsafe_allow_html=True)

    # Bảng đối sánh toàn diện
    with st.expander("📊 Xem Bảng Đối Sánh Toàn Diện: Toàn Nhà Máy vs 3 Ca Trưởng (Long - Sắc - Tài)", expanded=True):
        st.dataframe(all_db.get('comparison_df', pd.DataFrame()), use_container_width=True, hide_index=True)

# Hàm hiển thị Dashboard chuyên sâu cho 1 Ca Trưởng
def render_single_leader_dashboard(ldr, all_db):
    raw_header = f"""
    <div style="background: {ldr['bg_color']}; border-left: 6px solid {ldr['color']}; padding: 14px 20px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px; font-weight: 800; color: {ldr['color']};">{ldr['icon']} BẢNG ĐIỀU KHIỂN SẢN XUẤT: {ldr['display_name'].upper()}</span>
            <span style="font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 20px; background: #ffffff; color: {ldr['color']}; border: 1px solid {ldr['border_color']};">{ldr['status_icon']} {ldr['status_text']}</span>
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #1e293b;">
            🏆 Điểm Thi Đua KPI: <span style="color: {ldr['kpi_eval'].get('color', '#16a34a')};">{ldr['kpi_score']:.1f}/100</span> ({ldr['kpi_eval'].get('medal', '')} {ldr['kpi_eval'].get('rank', '')})
        </div>
    </div>
    """
    st.markdown(clean_html(raw_header), unsafe_allow_html=True)

    if ldr.get('has_active_shift'):
        # Hàng 1
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        with r1_c1:
            st.markdown(render_kpi_card_html(f"Sản Lượng (Ca {ldr['name']})", f"{ldr['output']:,.1f}", "Tấn", f"{ldr['output_pct']:.0f}% tổng nhà máy", "badge-info"), unsafe_allow_html=True)
        with r1_c2:
            e_eval = ldr.get('elec_eval', {})
            b_cls = "badge-success" if e_eval.get('status') == 'EXCELLENT' else ("badge-info" if e_eval.get('status') == 'STANDARD' else "badge-danger")
            val_e = f"{ldr['kwh_per_ton']:.1f}" if ldr['kwh_per_ton'] > 0 else f"{ldr['month_kwh_ton']:.1f}*"
            lbl_e = f"{e_eval.get('icon', '')} {e_eval.get('label', '')}" if ldr['kwh_per_ton'] > 0 else "TB tháng"
            st.markdown(render_kpi_card_html(f"Suất Điện (Ca {ldr['name']})", val_e, "kWh/t", lbl_e, b_cls), unsafe_allow_html=True)
        with r1_c3:
            p_eval = ldr.get('prod_eval', {})
            b_cls = "badge-success" if p_eval.get('status') == 'PASS' else "badge-warning"
            st.markdown(render_kpi_card_html(f"Năng Suất Ép (Ca {ldr['name']})", f"{ldr['tph']:.2f}", "Tấn/h", f"{p_eval.get('icon', '')} {p_eval.get('label', '')}", b_cls), unsafe_allow_html=True)
        with r1_c4:
            st.markdown(render_kpi_card_html(f"Giờ Máy Ép (Ca {ldr['name']})", f"{ldr['pellet_hours']:.1f}", "Giờ", f"{ldr['shift_count']} ca phụ trách", "badge-info"), unsafe_allow_html=True)

        # Hàng 2
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
        with r2_c1:
            m_eval = ldr.get('moist_eval', {})
            b_cls = "badge-success" if m_eval.get('status') == 'PASS' else "badge-warning"
            st.markdown(render_kpi_card_html("Độ Ẩm TB Viên", f"{ldr['moisture']:.2f}", "%", f"{m_eval.get('icon', '💧')} {m_eval.get('label', '8.0 - 9.5%')}", b_cls), unsafe_allow_html=True)
        with r2_c2:
            st.markdown(render_kpi_card_html("Điểm KPI Thi Đua", f"{ldr['kpi_score']:.1f}", "/100", f"{ldr['kpi_eval'].get('medal', '')} {ldr['kpi_eval'].get('rank', '')}", "badge-success"), unsafe_allow_html=True)
        with r2_c3:
            st.markdown(render_kpi_card_html("Tỷ Lệ Chế Biến", f"{ldr['processing_ratio']:.2f}", "lần", f"NL đốt: {ldr['nl_dot']:,.1f}t", "badge-info"), unsafe_allow_html=True)
        with r2_c4:
            st.markdown(render_kpi_card_html("Lũy Kế Tháng", f"{ldr['month_output']:,.0f}", "Tấn", f"{ldr['month_shifts']} ca | {ldr['month_tph']:.2f} t/h", "badge-info"), unsafe_allow_html=True)

        st.markdown(f"##### 📊 TIẾN ĐỘ THEO KỲ: NGÀY / TUẦN / THÁNG (CA TRƯỞNG {ldr['name'].upper()})")
        r_per_1, r_per_2, r_per_3 = st.columns(3)
        with r_per_1:
            st.markdown(render_kpi_card_html(f"☀️ Ngày ({ldr.get('day_label', 'Hôm nay')})", f"{ldr.get('day_out', 0):,.1f}", "Tấn", f"{ldr.get('day_shifts', 0)} ca | {ldr.get('day_kwh_ton', 0):.1f} kWh/t", "badge-info"), unsafe_allow_html=True)
        with r_per_2:
            st.markdown(render_kpi_card_html(f"📅 Tuần ({ldr.get('week_label', 'Tuần')})", f"{ldr.get('week_out', 0):,.1f}", "Tấn", f"{ldr.get('week_shifts', 0)} ca | {ldr.get('week_kwh_ton', 0):.1f} kWh/t", "badge-success"), unsafe_allow_html=True)
        with r_per_3:
            st.markdown(render_kpi_card_html(f"📆 Tháng ({ldr.get('month_label', 'Tháng')})", f"{ldr.get('month_output', 0):,.1f}", "Tấn", f"{ldr.get('month_shifts', 0)} ca | {ldr.get('month_kwh_ton', 0):.1f} kWh/t", "badge-warning"), unsafe_allow_html=True)
    else:
        # Off-duty: Hiển thị Thành tích Ca gần nhất & Lũy kế tháng cực kỳ chuyên nghiệp
        st.info(f"ℹ️ **Ca Trưởng {ldr['name']} không có ca trực trong kỳ này ({ldr['period_label']}).** Dưới đây là thành tích tại **Ca trực gần nhất (Ngày {ldr['latest_shift_date']})** và **Tổng hợp Lũy kế tháng**.")
        
        st.markdown(f"##### 🕒 THÀNH TÍCH CA TRỰC GẦN NHẤT (NGÀY {ldr['latest_shift_date']})")
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        with r1_c1:
            st.markdown(render_kpi_card_html(f"Sản Lượng (Ca {ldr['latest_shift_date']})", f"{ldr['latest_shift_out']:,.1f}", "Tấn", "Ca gần nhất", "badge-info"), unsafe_allow_html=True)
        with r1_c2:
            val_kwh_lat = f"{ldr['latest_shift_kwh']:.1f}" if ldr['latest_shift_kwh'] > 0 else (f"{ldr['month_kwh_ton']:.1f}*" if ldr['month_kwh_ton'] > 0 else "--")
            st.markdown(render_kpi_card_html("Suất Điện Tiêu Hao", val_kwh_lat, "kWh/t", "Ca gần nhất", "badge-info"), unsafe_allow_html=True)
        with r1_c3:
            st.markdown(render_kpi_card_html("Năng Suất Ép TB", f"{ldr['latest_shift_tph']:.2f}", "Tấn/h", "Ca gần nhất", "badge-success"), unsafe_allow_html=True)
        with r1_c4:
            st.markdown(render_kpi_card_html("Trạng Thái Trực", "Nghỉ Ca", "", f"Kỳ: {ldr['period_label']}", "badge-warning"), unsafe_allow_html=True)

        st.markdown(f"##### 📊 TIẾN ĐỘ THEO KỲ: NGÀY / TUẦN / THÁNG (CA TRƯỞNG {ldr['name'].upper()})")
        r_per_1, r_per_2, r_per_3 = st.columns(3)
        with r_per_1:
            st.markdown(render_kpi_card_html(f"☀️ Ngày ({ldr.get('day_label', 'Hôm nay')})", f"{ldr.get('day_out', 0):,.1f}", "Tấn", f"{ldr.get('day_shifts', 0)} ca | {ldr.get('day_kwh_ton', 0):.1f} kWh/t", "badge-info"), unsafe_allow_html=True)
        with r_per_2:
            st.markdown(render_kpi_card_html(f"📅 Tuần ({ldr.get('week_label', 'Tuần')})", f"{ldr.get('week_out', 0):,.1f}", "Tấn", f"{ldr.get('week_shifts', 0)} ca | {ldr.get('week_kwh_ton', 0):.1f} kWh/t", "badge-success"), unsafe_allow_html=True)
        with r_per_3:
            st.markdown(render_kpi_card_html(f"📆 Tháng ({ldr.get('month_label', 'Tháng')})", f"{ldr.get('month_output', 0):,.1f}", "Tấn", f"{ldr.get('month_shifts', 0)} ca | {ldr.get('month_kwh_ton', 0):.1f} kWh/t", "badge-warning"), unsafe_allow_html=True)

    # Nhật ký ca chi tiết nếu có
    if not ldr['shifts_df'].empty and (ldr['shifts_df']['san_luong_tan'] > 0).any():
        st.markdown(f"##### 📋 Nhật Ký Chi Tiết Ca Trực Của Ca Trưởng {ldr['name']}")
        cols_disp = ['date_str', 'san_luong_tan', 'tong_gio_ep', 'nang_suat_tph', 'dien_kwh', 'dien_tb_kwh_tan', 'nl_dot_tan', 'nghien_tho_tan']
        avail = [c for c in cols_disp if c in ldr['shifts_df'].columns]
        df_sub_disp = ldr['shifts_df'][avail].copy()
        df_sub_disp.rename(columns={
            'date_str': 'Ngày',
            'san_luong_tan': 'Sản lượng (tấn)',
            'tong_gio_ep': 'Giờ ép (h)',
            'nang_suat_tph': 'Năng suất (tấn/h)',
            'dien_kwh': 'Điện (kWh)',
            'dien_tb_kwh_tan': 'Suất điện (kWh/t)',
            'nl_dot_tan': 'NL Đốt (tấn)',
            'nghien_tho_tan': 'Nghiền thô (tấn)'
        }, inplace=True)
        st.dataframe(df_sub_disp, use_container_width=True, hide_index=True)

# Bộ chọn Dashboard hiển thị
st.markdown("---")
selected_dashboard_view = st.radio(
    "📌 **LỰA CHỌN DASHBOARD HIỂN THỊ:**",
    [
        "🌟 Tất Cả (1 Dashboard Tổng + 3 Dashboard Ca Trưởng Long, Sắc, Tài)",
        "🏭 Chỉ Dashboard Tổng Thể",
        "🔵 Dashboard Ca Trưởng Long",
        "🟢 Dashboard Ca Trưởng Sắc",
        "🟠 Dashboard Ca Trưởng Tài"
    ],
    horizontal=True,
    index=0
)

# Hiển thị theo chế độ đã chọn
if selected_dashboard_view == "🌟 Tất Cả (1 Dashboard Tổng + 3 Dashboard Ca Trưởng Long, Sắc, Tài)":
    st.markdown(render_section_banner("🏭 1. BẢNG ĐIỀU KHIỂN TỔNG HỢP TOÀN NHÀ MÁY", "Định mức & Mục tiêu Kỹ thuật BVN Quảng Bình", "#2563eb"), unsafe_allow_html=True)
    render_factory_dashboard_cards(kpis, df_weekly)
    st.markdown("---")
    st.markdown(render_section_banner("👥 2. BẢNG ĐIỀU KHIỂN CHI TIẾT 3 CA TRƯỞNG: LONG - SẮC - TÀI", "Theo dõi Song Song & Thi Đua KPI", "#10b981"), unsafe_allow_html=True)
    cur_def_time = "☀️ Theo Ngày"
    if view_mode == "📅 Theo Tuần":
        cur_def_time = "📅 Theo Tuần"
    elif view_mode in ["📆 Theo Tháng", "🏛️ Theo Năm"]:
        cur_def_time = "📆 Theo Tháng"
    render_leaders_side_by_side(all_db_summary, default_time_view=cur_def_time)
elif selected_dashboard_view == "🏭 Chỉ Dashboard Tổng Thể":
    st.markdown(render_section_banner("🏭 BẢNG ĐIỀU KHIỂN TỔNG HỢP TOÀN NHÀ MÁY", "Định mức & Mục tiêu Kỹ thuật BVN Quảng Bình", "#2563eb"), unsafe_allow_html=True)
    render_factory_dashboard_cards(kpis, df_weekly)
elif selected_dashboard_view == "🔵 Dashboard Ca Trưởng Long":
    render_single_leader_dashboard(all_db_summary['leaders']['Long'], all_db_summary)
elif selected_dashboard_view == "🟢 Dashboard Ca Trưởng Sắc":
    render_single_leader_dashboard(all_db_summary['leaders']['Sắc'], all_db_summary)
elif selected_dashboard_view == "🟠 Dashboard Ca Trưởng Tài":
    render_single_leader_dashboard(all_db_summary['leaders']['Tài'], all_db_summary)

st.markdown("---")

# ================= CỬA SỔ TÁC VỤ (ĐIỀU HƯỚNG DỌC BÊN TRÁI MÀN HÌNH) =================
active_task = st.session_state.get('active_task', OP_TASKS[0])
if active_task not in TASK_LIST:
    active_task = OP_TASKS[0]
active_task_idx = TASK_LIST.index(active_task)

is_op = active_task in OP_TASKS
is_static = active_task in STATIC_TASKS
is_entry = active_task in ENTRY_TASKS

if is_op:
    group_title = "📊 NHÓM 1: VẬN HÀNH, KPI & ĐO LƯỜNG (SỐ LIỆU ĐỘNG HÀNG NGÀY)"
    group_color = "#38bdf8"
    group_tag = f"Mục {OP_TASKS.index(active_task) + 1}/10 Vận Hành & KPI"
elif is_static:
    group_title = "📘 NHÓM 2: QUY TRÌNH, SƠ ĐỒ & CƠ CẤU (TÀI LIỆU KỸ THUẬT CỐ ĐỊNH)"
    group_color = "#c084fc"
    group_tag = f"Mục {STATIC_TASKS.index(active_task) + 1}/3 Quy Trình & Sơ Đồ"
else:
    group_title = "📝 NHÓM 3: NHẬP BÁO CÁO CA & KCS TRỰC TIẾP (BẢO MẬT CA TRƯỞNG)"
    group_color = "#34d399"
    group_tag = "Mục 14/14 Nhập Liệu Trực Tiếp"

st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 14px 20px; margin-bottom: 12px; border: 1px solid #334155; box-shadow: 0 4px 14px rgba(0,0,0,0.15); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
    <div>
        <div style="font-size: 11px; font-weight: 700; color: {group_color}; text-transform: uppercase; letter-spacing: 1px;">
            {group_title}
        </div>
        <div style="font-size: 20px; font-weight: 800; color: #ffffff; margin-top: 2px;">
            {active_task}
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 12px; color: {group_color}; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); padding: 5px 12px; border-radius: 6px; font-weight: 700;">
            {group_tag}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

col_quick_nav, col_btn_prev, col_btn_next = st.columns([6, 2, 2])
with col_quick_nav:
    def on_main_select_change():
        st.session_state['active_task'] = st.session_state['main_task_dropdown']
        
    st.selectbox(
        "Chuyển nhanh cửa sổ tác vụ:",
        TASK_LIST,
        index=active_task_idx,
        format_func=lambda x: f"📊 [Vận hành] {x}" if x in OP_TASKS else (f"📘 [Cố định] {x}" if x in STATIC_TASKS else f"📝 [Nhập liệu] {x}"),
        key="main_task_dropdown",
        on_change=on_main_select_change,
        label_visibility="collapsed"
    )

with col_btn_prev:
    if st.button("⬅️ Tác vụ trước", disabled=(active_task_idx == 0), use_container_width=True, key="btn_prev_task"):
        new_task = TASK_LIST[active_task_idx - 1]
        st.session_state['active_task'] = new_task
        st.rerun()

with col_btn_next:
    if st.button("Tác vụ kế tiếp ➡️", disabled=(active_task_idx == len(TASK_LIST) - 1), use_container_width=True, key="btn_next_task"):
        new_task = TASK_LIST[active_task_idx + 1]
        st.session_state['active_task'] = new_task
        st.rerun()

st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# Trích xuất số thứ tự tác vụ chính xác (tránh lỗi xung đột chuỗi "1. " với "11. ")
m_task = re.search(r'(\d+)\.', active_task)
task_num = int(m_task.group(1)) if m_task else 1

# ----------------- TAB 1: NHẬT KÝ CA & THIẾT BỊ NGÀY -----------------
if task_num == 1:
    st.markdown('<div class="section-title">📊 Chi Tiết Các Ca Sản Xuất Trong Ngày</div>', unsafe_allow_html=True)
    st.info(f"🧪 **Chỉ số chất lượng & chế biến thành phẩm ngày ({kpis.get('date_str', 'N/A')}):** Độ ẩm viên TB: **{am_val:.2f}%** ({moist_eval.get('label', '')}) | Tỷ trọng viên nén: **{ty_trong_val:,.1f} kg/m³** ({dens_eval.get('label', '')}) | Tỷ lệ chế biến: **{kpis.get('processing_ratio', 0):.2f} lần** | 📦 Tồn kho viên nén: **{kpis.get('ton_kho_tan', 0):,.1f} tấn**")
    
    col_t1_left, col_t1_right = st.columns([3, 2])
    
    with col_t1_left:
        shift_data = kpis.get('shift_details', [])
        if shift_data:
            df_shifts_table = pd.DataFrame(shift_data)
            # Tạo các cột hiển thị đẹp
            df_view = pd.DataFrame({
                'Ca Trưởng': df_shifts_table['ca_truong'],
                'Sản Lượng (tấn)': df_shifts_table['san_luong_tan'],
                'Giờ Máy Ép (h)': df_shifts_table['tong_gio_ep'],
                'Năng Suất (tấn/h)': df_shifts_table['nang_suat_tph'],
                'Đánh Giá NS': df_shifts_table['ns_eval'].apply(lambda x: f"{x['icon']} {x['label']}"),
                'Điện Tiêu Thụ (kWh)': df_shifts_table['dien_kwh'],
                'Suất Điện (kWh/t)': df_shifts_table['dien_tb_kwh_tan'],
                'Đánh Giá Điện': df_shifts_table['elec_eval'].apply(lambda x: f"{x['icon']} {x['label']}"),
                'NL Đốt (tấn)': df_shifts_table['nl_dot_tan'],
                'Nghiền Thô (tấn)': df_shifts_table['nghien_tho_tan']
            })
            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.info("Không có dữ liệu ca cho ngày này.")

    with col_t1_right:
        # Biểu đồ Donut tỷ trọng sản lượng theo ca
        if shift_data:
            fig_donut = px.pie(
                df_shifts_table,
                names='ca_truong',
                values='san_luong_tan',
                title="Tỷ Trọng Sản Lượng Giữa Các Ca",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(shift_data))
            fig_donut.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260)
            st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown('<div class="section-title">⏱️ Thời Gian Máy Chạy Của Các Cụm Thiết Bị (Giờ/Ngày)</div>', unsafe_allow_html=True)
    
    eq_hours = kpis.get('equipment_hours', {})
    if eq_hours:
        c_eq1, c_eq2, c_eq3, c_eq4 = st.columns(4)
        
        # 1. Nghiền búa thô
        with c_eq1:
            st.markdown("##### 🔨 Nghiền Búa Thô")
            data_tho = [
                {'Máy': 'HM118 (Andritz)', 'Giờ': eq_hours.get('HM118', {}).get('hours', 0)},
                {'Máy': 'HM218 (Andritz)', 'Giờ': eq_hours.get('HM218', {}).get('hours', 0)},
                {'Máy': 'HM318 (SHT)', 'Giờ': eq_hours.get('HM318', {}).get('hours', 0)},
            ]
            fig_tho = px.bar(data_tho, x='Máy', y='Giờ', text='Giờ', color='Máy', color_discrete_sequence=['#3b82f6', '#1d4ed8', '#0284c7'])
            fig_tho.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_tho, use_container_width=True)

        # 2. Trống sấy
        with c_eq2:
            st.markdown("##### ♨️ Trống Sấy")
            data_say = [
                {'Máy': 'DR124', 'Giờ': eq_hours.get('DR124', {}).get('hours', 0)},
                {'Máy': 'DR224', 'Giờ': eq_hours.get('DR224', {}).get('hours', 0)},
            ]
            fig_say = px.bar(data_say, x='Máy', y='Giờ', text='Giờ', color='Máy', color_discrete_sequence=['#f97316', '#ea580c'])
            fig_say.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_say, use_container_width=True)

        # 3. Nghiền búa tinh
        with c_eq3:
            st.markdown("##### ⚙️ Nghiền Búa Tinh")
            data_tinh = [
                {'Máy': 'HM147 (SHT)', 'Giờ': eq_hours.get('HM147', {}).get('hours', 0)},
                {'Máy': 'HM247 (Andritz)', 'Giờ': eq_hours.get('HM247', {}).get('hours', 0)},
                {'Máy': 'HM347 (Andritz)', 'Giờ': eq_hours.get('HM347', {}).get('hours', 0)},
            ]
            fig_tinh = px.bar(data_tinh, x='Máy', y='Giờ', text='Giờ', color='Máy', color_discrete_sequence=['#8b5cf6', '#6d28d9', '#4c1d95'])
            fig_tinh.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_tinh, use_container_width=True)

        # 4. Cụm 8 máy ép viên
        with c_eq4:
            st.markdown("##### 🔄 Cụm 8 Máy Ép Viên")
            data_pe = [{'Máy': f'PE{i}', 'Giờ': eq_hours.get(f'PE{i}', {}).get('hours', 0)} for i in range(1, 9)]
            fig_pe = px.bar(data_pe, x='Máy', y='Giờ', text='Giờ', color_discrete_sequence=['#10b981'])
            fig_pe.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pe, use_container_width=True)

# ----------------- TAB KPI: ĐÁNH GIÁ & XẾP HẠNG KPI CA TRƯỞNG (FILE MỚI) -----------------
elif task_num == 2:
    st.markdown('<div class="section-title">🎯 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI CA TRƯỞNG</div>', unsafe_allow_html=True)
    st.caption(f"Nguồn dữ liệu tích hợp: **{kpi_sheet_title}** (Google Sheets ID: `1M75tg_kZNxItv3VOlAjNi-RF63S_2NtxBMXSAxCRe14`)")

    # 1. Bộ lọc chọn Tuần và Tháng cho Bảng Xếp Hạng Thi Đua (Toàn bộ 52 tuần & 12 tháng)
    available_kpi_weeks = ALL_WEEKS_52
    available_kpi_months = ALL_MONTHS_12

    def render_rank_cards(lb_items, period_name="tuần"):
        if not lb_items:
            st.info(f"Chưa có số liệu điểm KPI cho {period_name}.")
            return
        bg_colors = {
            1: "linear-gradient(135deg, #fef9c3 0%, #ffffff 100%)",
            2: "linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%)",
            3: "linear-gradient(135deg, #ffedd5 0%, #ffffff 100%)"
        }
        border_colors = {1: "#eab308", 2: "#94a3b8", 3: "#f97316"}
        for item in lb_items:
            rank_eval = item['eval']
            delta_val = item.get('delta', 0.0)
            if delta_val > 0:
                delta_badge = f'<span style="color:#15803d; font-size:12px; font-weight:700;">▲ +{delta_val:.2f} đ</span>'
            elif delta_val < 0:
                delta_badge = f'<span style="color:#b91c1c; font-size:12px; font-weight:700;">▼ {delta_val:.2f} đ</span>'
            else:
                delta_badge = '<span style="color:#64748b; font-size:12px;">kỳ đầu / giữ nguyên</span>'

            c_bg = bg_colors.get(item['hang'], "#ffffff")
            c_bd = border_colors.get(item['hang'], "#e2e8f0")

            st.markdown(f"""
            <div style="background:{c_bg}; border:1.5px solid {c_bd}; border-radius:12px; padding:14px 18px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <div>
                    <span style="font-size:28px; margin-right:10px;">{item['huy_chuong']}</span>
                    <strong style="font-size:19px; color:#0f172a;">Ca {item['ca_truong']}</strong>
                    <div style="font-size:12px; color:#64748b; margin-left:38px; margin-top:2px;">
                        Hạng {item['hang']} • {delta_badge} so với {period_name} trước
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:25px; font-weight:800; color:{rank_eval['color']};">{item['diem_kpi']:.2f}</span>
                    <span style="font-size:13px; color:#64748b;"> / 100đ</span>
                    <div style="font-size:12px; font-weight:700; color:{rank_eval['color']}; margin-top:2px;">
                        {rank_eval['icon']} {rank_eval['rank']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def render_component_breakdown(df_detail, period_label, chart_key=None):
        if df_detail.empty:
            st.info(f"Chưa có dữ liệu cơ cấu điểm cho {period_label}.")
            return
        plot_data = []
        for _, r in df_detail.iterrows():
            plot_data.extend([
                {'Ca': f"Ca {r['ca_truong']}", 'Tiêu chí': '1. Điểm Sản Lượng (/40)', 'Điểm': r.get('diem_sl', 0)},
                {'Ca': f"Ca {r['ca_truong']}", 'Tiêu chí': '2. Điểm Độ Ẩm (/22)', 'Điểm': r.get('diem_am', 0)},
                {'Ca': f"Ca {r['ca_truong']}", 'Tiêu chí': '3. Điểm Điện Năng (/20)', 'Điểm': r.get('diem_dien', 0)},
                {'Ca': f"Ca {r['ca_truong']}", 'Tiêu chí': '4. Điểm Năng Suất (/18)', 'Điểm': r.get('diem_nang_suat', 0)},
            ])
        df_plot_kpi = pd.DataFrame(plot_data)
        c_chart, c_tbl = st.columns([3, 2])
        with c_chart:
            fig_bar = px.bar(
                df_plot_kpi,
                x='Ca',
                y='Điểm',
                color='Tiêu chí',
                barmode='group',
                text='Điểm',
                title=f"So Sánh 4 Tiêu Chí Điểm KPI - {period_label}",
                color_discrete_sequence=['#3b82f6', '#0284c7', '#10b981', '#f59e0b']
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_bar.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True, key=chart_key)

        with c_tbl:
            st.markdown(f"##### Bảng Điểm Chi Tiết - {period_label}")
            cols_show = ['ca_truong', 'sl_thuc_te', 'diem_sl', 'diem_am', 'diem_dien', 'diem_nang_suat', 'diem_kpi']
            avail_cols = [c for c in cols_show if c in df_detail.columns]
            df_disp = df_detail[avail_cols].copy()
            col_names_map = {
                'ca_truong': 'Ca Trưởng',
                'sl_thuc_te': 'SL (tấn)',
                'diem_sl': 'Đ.SL (/40)',
                'diem_am': 'Đ.Ẩm (/22)',
                'diem_dien': 'Đ.Điện (/20)',
                'diem_nang_suat': 'Đ.NS (/18)',
                'diem_kpi': 'TỔNG ĐIỂM'
            }
            df_disp.rename(columns=col_names_map, inplace=True)
            st.dataframe(df_disp, hide_index=True, use_container_width=True)

    def render_leader_summary_cards(df_sub, period_label):
        if df_sub.empty:
            return
        st.markdown(f"##### 📋 Chỉ Số Kỹ Thuật & Sản Xuất Thực Tế Từng Ca - {period_label}")
        c_ldrs = st.columns(min(3, len(df_sub)))
        for idx, (_, r_ldr) in enumerate(df_sub.iterrows()):
            if idx < len(c_ldrs):
                with c_ldrs[idx]:
                    pct_target = (r_ldr['sl_thuc_te'] / r_ldr['chi_tieu_sl'] * 100) if r_ldr.get('chi_tieu_sl', 0) > 0 else 0
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:12px 16px; margin-bottom:12px; box-shadow:0 2px 5px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong style="font-size:18px; color:#0f172a;">Ca {r_ldr['ca_truong']}</strong>
                            <span style="background:#f1f5f9; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; color:#475569;">{r_ldr.get('so_ca', 0):.0f} Ca Trực</span>
                        </div>
                        <div style="font-size:13px; color:#334155; line-height:1.8;">
                            • <b>Sản lượng:</b> {r_ldr.get('sl_thuc_te', 0):,.1f} / {r_ldr.get('chi_tieu_sl', 0):,.0f} t ({pct_target:.1f}%)<br/>
                            • <b>Suất điện TB:</b> {r_ldr.get('dien_tb', 0):.1f} kWh/tấn<br/>
                            • <b>Năng suất ép:</b> {r_ldr.get('nang_suat_tb', 0):.2f} tấn/h<br/>
                            • <b>Độ ẩm viên:</b> {r_ldr.get('do_am_tb', 0):.2f}%<br/>
                            • <b>Tổng điểm KPI:</b> <span style="font-weight:800; color:#2563eb; font-size:16px;">{r_ldr.get('diem_kpi', 0):.2f} đ</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    df_leaders_w = leaders_kpi.get('weekly', pd.DataFrame())
    df_leaders_m = leaders_kpi.get('monthly', pd.DataFrame())

    # Các Tabs chuyên biệt cho Tuần và Tháng - Click chọn trực tiếp
    subtab_kpi_w, subtab_kpi_m, subtab_kpi_all = st.tabs([
        "📅 BẢNG XẾP HẠNG KPI THEO TUẦN",
        "📆 BẢNG XẾP HẠNG KPI THEO THÁNG",
        "⚖️ XEM SONG SONG CẢ TUẦN & THÁNG"
    ])

    # ===== SUBTAB 1: KPI THEO TUẦN =====
    with subtab_kpi_w:
        st.markdown("### 📅 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI THEO TUẦN")
        col_w_pick, _ = st.columns([1, 1])
        with col_w_pick:
            sel_kpi_week = st.selectbox(
                "📅 Click Chọn Tuần Đánh Giá KPI (Tuần 1 - 52):",
                options=available_kpi_weeks,
                index=default_w_idx,
                key="sb_kpi_week_tab"
            )
        lb_w = get_kpi_leaderboard(df_wm_weekly, df_wm_monthly, selected_week=sel_kpi_week)
        w_title = lb_w['weekly']['label'] if lb_w['weekly'] else (sel_kpi_week or "Tuần")

        st.markdown(f"#### 🏆 Kết Quả Thi Đua Ca Trưởng: **{w_title}**")
        w_has_kpi = bool(lb_w['weekly'] and lb_w['weekly']['leaderboard'])
        if w_has_kpi:
            render_rank_cards(lb_w['weekly']['leaderboard'], "tuần")
        else:
            st.info(f"ℹ️ **{w_title}**: Bảng điểm KPI chưa có dữ liệu chấm điểm thi đua.")

        df_w_sub = df_leaders_w[df_leaders_w['week_label'] == sel_kpi_week] if not df_leaders_w.empty else pd.DataFrame()
        if not df_w_sub.empty:
            render_leader_summary_cards(df_w_sub, w_title)
            st.markdown("---")
            st.markdown(f"#### 📊 Cơ Cấu 4 Tiêu Chí Điểm KPI (Trọng Số 40 - 22 - 20 - 18) - **{w_title}**")
            render_component_breakdown(df_w_sub, w_title, chart_key="comp_bar_week")
        else:
            # Kiểm tra xem df_shifts có dữ liệu ca cho tuần này không
            try:
                w_num = int(sel_kpi_week.replace("Tuần ", ""))
                w_shifts_kpi = df_shifts[df_shifts['date'].dt.isocalendar().week == w_num]
            except Exception:
                w_shifts_kpi = pd.DataFrame()

            if not w_shifts_kpi.empty:
                st.markdown(f"##### 📋 Dữ Liệu Sản Xuất Thực Tế Từng Ca - {w_title} (Từ Nhật Ký Ca Sản Xuất)")
                w_lead = get_shift_leader_kpis(w_shifts_kpi)
                if not w_lead.empty:
                    st.dataframe(w_lead, hide_index=True, use_container_width=True)
            elif not w_has_kpi:
                st.caption(f"Chưa có dữ liệu sản xuất ca trong {sel_kpi_week}.")

        if not df_wm_weekly.empty:
            st.markdown("---")
            min_w_label = df_wm_weekly['week_label'].iloc[0] if not df_wm_weekly.empty else "Tuần 32"
            max_w_label = df_wm_weekly['week_label'].iloc[-1] if not df_wm_weekly.empty else "Tuần 38"
            st.markdown(f"#### 📈 Diễn Biến Tổng Điểm KPI Ca Trưởng Qua Các Tuần ({min_w_label} - {max_w_label})")
            fig_trend_w = go.Figure()
            colors_l = {'Long': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c'}
            for name in ['Long', 'Sắc', 'Tài']:
                if name in df_wm_weekly.columns:
                    fig_trend_w.add_trace(go.Scatter(
                        x=df_wm_weekly['week_label'],
                        y=df_wm_weekly[name],
                        mode='lines+markers+text',
                        name=f'Ca {name}',
                        text=[f"{v:.1f}" if pd.notna(v) else "" for v in df_wm_weekly[name]],
                        textposition="top center",
                        line=dict(color=colors_l.get(name, '#64748b'), width=2.5)
                    ))
            fig_trend_w.update_layout(
                yaxis_title="Tổng Điểm KPI (/100)",
                height=350,
                hovermode="x unified",
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_trend_w, use_container_width=True, key="fig_trend_w_line")

    # ===== SUBTAB 2: KPI THEO THÁNG =====
    with subtab_kpi_m:
        st.markdown("### 📆 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI THEO THÁNG")
        col_m_pick, _ = st.columns([1, 1])
        with col_m_pick:
            sel_kpi_month = st.selectbox(
                "📆 Click Chọn Tháng Đánh Giá KPI (Tháng 1 - 12):",
                options=available_kpi_months,
                index=default_m_idx,
                key="sb_kpi_month_tab"
            )
        lb_m = get_kpi_leaderboard(df_wm_weekly, df_wm_monthly, selected_month=sel_kpi_month)
        m_title = lb_m['monthly']['label'] if lb_m['monthly'] else (sel_kpi_month or "Tháng")

        st.markdown(f"#### 👑 Kết Quả Thi Đua Ca Trưởng: **{m_title}**")
        m_has_kpi = bool(lb_m['monthly'] and lb_m['monthly']['leaderboard'])
        if m_has_kpi:
            render_rank_cards(lb_m['monthly']['leaderboard'], "tháng")
        else:
            st.info(f"ℹ️ **{m_title}**: Bảng điểm KPI chưa có dữ liệu chấm điểm thi đua.")

        df_m_sub = df_leaders_m[df_leaders_m['month_label'] == sel_kpi_month] if not df_leaders_m.empty else pd.DataFrame()
        if not df_m_sub.empty:
            render_leader_summary_cards(df_m_sub, m_title)
            st.markdown("---")
            st.markdown(f"#### 📊 Cơ Cấu 4 Tiêu Chí Điểm KPI (Trọng Số 40 - 22 - 20 - 18) - **{m_title}**")
            render_component_breakdown(df_m_sub, m_title, chart_key="comp_bar_month")
        else:
            # Kiểm tra xem df_shifts có dữ liệu ca cho tháng này không
            try:
                m_num = int(sel_kpi_month.replace("Tháng ", ""))
                m_shifts_kpi = df_shifts[df_shifts['date'].dt.month == m_num]
            except Exception:
                m_shifts_kpi = pd.DataFrame()

            if not m_shifts_kpi.empty:
                st.markdown(f"##### 📋 Dữ Liệu Sản Xuất Thực Tế Từng Ca - {m_title} (Từ Nhật Ký Ca Sản Xuất)")
                m_lead = get_shift_leader_kpis(m_shifts_kpi)
                if not m_lead.empty:
                    st.dataframe(m_lead, hide_index=True, use_container_width=True)
            elif not m_has_kpi:
                st.caption(f"Chưa có dữ liệu sản xuất ca trong {sel_kpi_month}.")

        if not df_wm_monthly.empty:
            st.markdown("---")
            all_m_labels = " vs ".join(df_wm_monthly['month_label'].tolist()) if not df_wm_monthly.empty else "Tháng 8 vs Tháng 9"
            st.markdown(f"#### 📈 So Sánh Tổng Điểm KPI Qua Các Tháng ({all_m_labels})")
            fig_trend_m = go.Figure()
            colors_l = {'Long': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c'}
            for name in ['Long', 'Sắc', 'Tài']:
                if name in df_wm_monthly.columns:
                    fig_trend_m.add_trace(go.Bar(
                        x=df_wm_monthly['month_label'],
                        y=df_wm_monthly[name],
                        name=f'Ca {name}',
                        text=[f"{v:.2f} đ" if pd.notna(v) else "" for v in df_wm_monthly[name]],
                        textposition="outside",
                        marker_color=colors_l.get(name, '#64748b')
                    ))
            fig_trend_m.update_layout(
                barmode='group',
                yaxis_title="Tổng Điểm KPI (/100)",
                yaxis_range=[0, 110],
                height=350,
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_trend_m, use_container_width=True, key="fig_trend_m_bar")

    # ===== SUBTAB 3: XEM SONG SONG CẢ TUẦN & THÁNG =====
    with subtab_kpi_all:
        st.markdown("### ⚖️ ĐỐI CHIẾU SONG SONG KPI TUẦN VÀ THÁNG")
        col_filter_w, col_filter_m = st.columns(2)
        with col_filter_w:
            sel_kpi_week_p = st.selectbox(
                "📅 Click Chọn Tuần Đối Chiếu (Tuần 1 - 52):",
                options=available_kpi_weeks,
                index=default_w_idx,
                key="sb_kpi_week_parallel"
            )

        with col_filter_m:
            sel_kpi_month_p = st.selectbox(
                "📆 Click Chọn Tháng Đối Chiếu (Tháng 1 - 12):",
                options=available_kpi_months,
                index=default_m_idx,
                key="sb_kpi_month_parallel"
            )

        lb_p = get_kpi_leaderboard(
            df_wm_weekly, 
            df_wm_monthly, 
            selected_week=sel_kpi_week_p, 
            selected_month=sel_kpi_month_p
        )
        col_lb_w, col_lb_m = st.columns(2)

        with col_lb_w:
            w_title_p = lb_p['weekly']['label'] if lb_p['weekly'] else (sel_kpi_week_p or "Tuần")
            st.markdown(f"#### 🏆 Kết Quả Thi Đua: **{w_title_p}**")
            if lb_p['weekly'] and lb_p['weekly']['leaderboard']:
                render_rank_cards(lb_p['weekly']['leaderboard'], "tuần")
            else:
                st.info(f"ℹ️ {w_title_p} chưa có số liệu xếp hạng KPI.")

        with col_lb_m:
            m_title_p = lb_p['monthly']['label'] if lb_p['monthly'] else (sel_kpi_month_p or "Tháng")
            st.markdown(f"#### 👑 Kết Quả Thi Đua: **{m_title_p}**")
            if lb_p['monthly'] and lb_p['monthly']['leaderboard']:
                render_rank_cards(lb_p['monthly']['leaderboard'], "tháng")
            else:
                st.info(f"ℹ️ {m_title_p} chưa có số liệu xếp hạng KPI.")

        st.markdown("---")
        st.markdown('<div class="section-title">📊 Cơ Cấu Thành Phần Điểm KPI (Trọng Số 40 - 22 - 20 - 18)</div>', unsafe_allow_html=True)
        tab_bd_w, tab_bd_m = st.tabs([f"📅 Cơ Cấu {w_title_p}", f"📆 Cơ Cấu {m_title_p}"])
        with tab_bd_w:
            df_w_sub_p = df_leaders_w[df_leaders_w['week_label'] == sel_kpi_week_p] if not df_leaders_w.empty else pd.DataFrame()
            if not df_w_sub_p.empty:
                render_component_breakdown(df_w_sub_p, w_title_p, chart_key="comp_bar_p_week")
            else:
                st.info(f"Chưa có dữ liệu cơ cấu điểm cho {w_title_p}.")
        with tab_bd_m:
            df_m_sub_p = df_leaders_m[df_leaders_m['month_label'] == sel_kpi_month_p] if not df_leaders_m.empty else pd.DataFrame()
            if not df_m_sub_p.empty:
                render_component_breakdown(df_m_sub_p, m_title_p, chart_key="comp_bar_p_month")
            else:
                st.info(f"Chưa có dữ liệu cơ cấu điểm cho {m_title_p}.")

    st.markdown("---")

    # 3. Biểu đồ so sánh 3 ca trưởng theo ngày
    st.markdown('<div class="section-title">📈 Xu Hướng Đối Sánh Trực Tiếp 3 Ca Trưởng Theo Ngày</div>', unsafe_allow_html=True)
    
    tab_c1, tab_c2, tab_c3, tab_c4 = st.tabs([
        "⚡ Suất Điện Năng (kWh/tấn)", 
        "🚀 Năng Suất Ép (tấn/h)", 
        "💧 Độ Ẩm Viên Nén (%)",
        "📦 Sản Lượng & Chỉ Tiêu (Tấn)"
    ])

    with tab_c1:
        if not df_chart_dien.empty:
            fig_cd = go.Figure()
            colors = {'Long': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c'}
            for name in ['Long', 'Sắc', 'Tài']:
                if name in df_chart_dien.columns:
                    fig_cd.add_trace(go.Scatter(
                        x=df_chart_dien['date_str'], y=df_chart_dien[name],
                        mode='lines+markers', name=f'Ca {name}',
                        line=dict(color=colors[name], width=2)
                    ))
            # Đường line chuẩn 172
            fig_cd.add_hline(y=172, line_dash="dash", line_color="red", annotation_text="Định mức 172 kWh/tấn", annotation_position="top right")
            fig_cd.update_layout(
                title="Suất Tiêu Hao Điện Năng (kWh/tấn) Của Long vs Sắc vs Tài (So Với Chuẩn 172)",
                xaxis_title="Ngày", yaxis_title="kWh/tấn", height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cd, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu biểu đồ điện năng ca.")

    with tab_c2:
        if not df_chart_cap.empty:
            fig_cc = go.Figure()
            colors = {'Long': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c'}
            for name in ['Long', 'Sắc', 'Tài']:
                if name in df_chart_cap.columns:
                    fig_cc.add_trace(go.Scatter(
                        x=df_chart_cap['date_str'], y=df_chart_cap[name],
                        mode='lines+markers', name=f'Ca {name}',
                        line=dict(color=colors[name], width=2)
                    ))
            fig_cc.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="Chỉ tiêu ≥ 4.0 tấn/h", annotation_position="top left")
            fig_cc.update_layout(
                title="Năng Suất Ép Trung Bình (tấn/h) Của Long vs Sắc vs Tài (So Với Chỉ Tiêu 4.0)",
                xaxis_title="Ngày", yaxis_title="Tấn/giờ", height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cc, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu biểu đồ năng suất ca.")

    with tab_c3:
        if not df_chart_moist.empty:
            fig_cm = go.Figure()
            colors = {'Long': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c'}
            for name in ['Long', 'Sắc', 'Tài']:
                if name in df_chart_moist.columns:
                    fig_cm.add_trace(go.Scatter(
                        x=df_chart_moist['date_str'], y=df_chart_moist[name],
                        mode='lines+markers', name=f'Ca {name}',
                        line=dict(color=colors[name], width=2)
                    ))
            fig_cm.add_hline(y=9.0, line_dash="dash", line_color="red", annotation_text="Tiêu chuẩn 9.0%", annotation_position="top right")
            fig_cm.update_layout(
                title="Độ Ẩm Trung Bình (%) Của Long vs Sắc vs Tài (Sheet Chart Moisture)",
                xaxis_title="Ngày", yaxis_title="%", height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cm, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu biểu đồ độ ẩm ca.")

    with tab_c4:
        if not df_chart_sl.empty:
            fig_csl = go.Figure()
            colors_actual = {'Long': '#2563eb', 'Sac': '#16a34a', 'Tai': '#ea580c'}
            colors_target = {'Long': '#93c5fd', 'Sac': '#86efac', 'Tai': '#fdba74'}
            for code, name in [('Long', 'Long'), ('Sac', 'Sắc'), ('Tai', 'Tài')]:
                act_col = f'{code}_actual'
                tgt_col = f'{code}_target'
                if act_col in df_chart_sl.columns:
                    fig_csl.add_trace(go.Bar(
                        x=df_chart_sl['date_str'], y=df_chart_sl[act_col],
                        name=f'SL Thực Tế - Ca {name}',
                        marker_color=colors_actual[code]
                    ))
                if tgt_col in df_chart_sl.columns:
                    fig_csl.add_trace(go.Scatter(
                        x=df_chart_sl['date_str'], y=df_chart_sl[tgt_col],
                        mode='lines', name=f'Chỉ Tiêu - Ca {name}',
                        line=dict(color=colors_target[code], dash='dot', width=2)
                    ))
            fig_csl.update_layout(
                title="Sản Lượng Thực Tế vs Chỉ Tiêu Từng Ca (Từ Sheet Chart SL)",
                xaxis_title="Ngày", yaxis_title="Tấn", height=380, hovermode="x unified",
                barmode='group'
            )
            st.plotly_chart(fig_csl, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu biểu đồ sản lượng ca.")

    # 4. Bảng tổng hợp điểm các tuần
    st.markdown('<div class="section-title">📋 Bảng Tổng Hợp Điểm Thi Đua Các Tuần & Tháng (W-M KPI)</div>', unsafe_allow_html=True)
    c_wm1, c_wm2 = st.columns(2)
    with c_wm1:
        st.markdown("##### 📅 Điểm Thi Đua Các Tuần (W-M KPI)")
        if not df_wm_weekly.empty:
            st.dataframe(df_wm_weekly, hide_index=True, use_container_width=True)
    with c_wm2:
        st.markdown("##### 📆 Điểm Thi Đua Các Tháng (W-M KPI)")
        if not df_wm_monthly.empty:
            st.dataframe(df_wm_monthly, hide_index=True, use_container_width=True)



# ----------------- TAB 2: XU HƯỚNG TUẦN & THÁNG -----------------
elif task_num == 3:
    st.markdown('<div class="section-title">📈 Xu Hướng & Cảnh Báo Định Mức Điện Năng (kWh/tấn)</div>', unsafe_allow_html=True)
    
    # Biểu đồ đường điện năng theo ngày với đường định mức
    if 'date' in df_shifts.columns and not df_shifts.empty:
        df_day_trend = df_shifts.groupby('date').agg(
            total_output=('san_luong_tan', 'sum'),
            total_elec=('dien_kwh', 'sum'),
            total_hours=('tong_gio_ep', 'sum')
        ).reset_index()
        df_day_trend['kwh_per_ton'] = df_day_trend['total_elec'] / df_day_trend['total_output']
        df_day_trend['tph'] = df_day_trend['total_output'] / df_day_trend['total_hours']
        df_day_trend = df_day_trend[(df_day_trend['total_output'] > 0) & (df_day_trend['kwh_per_ton'] > 50)].tail(45)
    else:
        df_day_trend = pd.DataFrame(columns=['date', 'total_output', 'total_elec', 'total_hours', 'kwh_per_ton', 'tph'])

    fig_elec_trend = go.Figure()

    # Đường thực tế
    fig_elec_trend.add_trace(go.Scatter(
        x=df_day_trend['date'],
        y=df_day_trend['kwh_per_ton'],
        mode='lines+markers',
        name='Suất điện thực tế (kWh/tấn)',
        line=dict(color='#2563eb', width=3),
        marker=dict(size=6)
    ))

    # Giới hạn trên 175
    fig_elec_trend.add_hline(
        y=ELEC_MAX_BENCHMARK,
        line_dash="dash",
        line_color="#dc2626",
        annotation_text=f"Mức trần chuẩn ({ELEC_MAX_BENCHMARK} kWh/tấn)",
        annotation_position="top right"
    )

    # Giới hạn dưới 170
    fig_elec_trend.add_hline(
        y=ELEC_MIN_BENCHMARK,
        line_dash="dash",
        line_color="#16a34a",
        annotation_text=f"Mức sàn chuẩn ({ELEC_MIN_BENCHMARK} kWh/tấn)",
        annotation_position="bottom right"
    )

    # Vùng đạt chuẩn (170 - 175)
    fig_elec_trend.add_hrect(
        y0=ELEC_MIN_BENCHMARK, y1=ELEC_MAX_BENCHMARK,
        fillcolor="#10b981", opacity=0.1, line_width=0
    )

    fig_elec_trend.update_layout(
        title="Biểu Đồ Theo Dõi Suất Tiêu Hao Điện Năng Theo Ngày (So Với Khung Chuẩn 170 - 175 kWh/tấn)",
        xaxis_title="Ngày",
        yaxis_title="kWh/tấn",
        hovermode="x unified",
        height=380,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_elec_trend, use_container_width=True)

    # Biểu đồ năng suất ép vs mục tiêu 4.0 tấn/h
    st.markdown('<div class="section-title">⚡ Xu Hướng Năng Suất Ép (tấn/h) So Với Chỉ Tiêu (≥ 4.0 tấn/h)</div>', unsafe_allow_html=True)
    
    fig_prod_trend = go.Figure()
    fig_prod_trend.add_trace(go.Scatter(
        x=df_day_trend['date'],
        y=df_day_trend['tph'],
        mode='lines+markers',
        name='Năng suất ép (tấn/h)',
        line=dict(color='#0d9488', width=3),
        marker=dict(size=6)
    ))
    fig_prod_trend.add_hline(
        y=PRODUCTIVITY_TARGET,
        line_dash="dash",
        line_color="#e11d48",
        annotation_text=f"Chỉ tiêu tối thiểu (≥ {PRODUCTIVITY_TARGET} tấn/h)",
        annotation_position="top left"
    )
    fig_prod_trend.update_layout(
        title="Biểu Đồ Năng Suất Ép Trung Bình Theo Ngày",
        xaxis_title="Ngày",
        yaxis_title="Tấn/giờ (TPH)",
        hovermode="x unified",
        height=340,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_prod_trend, use_container_width=True)

    # Báo cáo Tuần & Tháng
    col_w, col_m = st.columns(2)
    with col_w:
        st.markdown("##### 📅 Báo Cáo Tuần (Weekly Report)")
        sel_w_rep = st.selectbox(
            "📅 Click chọn tuần xem chi tiết (Tuần 1 - 52):",
            options=ALL_WEEKS_52,
            index=default_w_idx,
            key="sb_week_rep_tab2"
        )
        row_w_df = df_weekly[df_weekly['week_label'] == sel_w_rep] if not df_weekly.empty else pd.DataFrame()
        if not row_w_df.empty:
            r_w_val = row_w_df.iloc[0]
            cw1, cw2, cw3, cw4 = st.columns(4)
            cw1.metric("Sản Lượng", f"{r_w_val.get('san_luong_tan', 0):,.1f} t")
            cw2.metric("Suất Điện", f"{r_w_val.get('dien_tb_kwh_tan', 0):.1f} kWh/t")
            cw3.metric("Năng Suất Ép", f"{r_w_val.get('nang_suat_ep_tph', 0):.2f} t/h")
            cw4.metric("Dầu Diezen", f"{r_w_val.get('diezen_lit', 0):,.0f} L")
        else:
            # Kiểm tra df_shifts cho tuần này
            try:
                w_num_r = int(sel_w_rep.replace("Tuần ", ""))
                w_shifts_r = df_shifts[df_shifts['date'].dt.isocalendar().week == w_num_r]
            except Exception:
                w_shifts_r = pd.DataFrame()

            if not w_shifts_r.empty:
                w_tot_out = float(w_shifts_r['san_luong_tan'].sum())
                w_tot_h = float(w_shifts_r['tong_gio_ep'].sum())
                w_tot_kwh = float(w_shifts_r['dien_kwh'].sum())
                w_avg_e = w_tot_kwh / w_tot_out if w_tot_out > 0 else 0.0
                w_avg_p = w_tot_out / w_tot_h if w_tot_h > 0 else 0.0
                cw1, cw2, cw3 = st.columns(3)
                cw1.metric("Sản Lượng (Ca)", f"{w_tot_out:,.1f} t")
                cw2.metric("Suất Điện TB", f"{w_avg_e:.1f} kWh/t")
                cw3.metric("Năng Suất Ép TB", f"{w_avg_p:.2f} t/h")
            else:
                st.info(f"ℹ️ {sel_w_rep} chưa có dữ liệu sản xuất.")

        if not df_weekly.empty:
            fig_w = px.bar(
                df_weekly,
                x='week_label',
                y='san_luong_tan',
                text='san_luong_tan',
                title="Sản Lượng Theo Tuần (Tấn)",
                color_discrete_sequence=['#3b82f6']
            )
            fig_w.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_w.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_w, use_container_width=True, key="fig_w_tab2_bar")
            st.dataframe(df_weekly[['week_label', 'san_luong_tan', 'dien_tb_kwh_tan', 'nang_suat_ep_tph', 'diezen_lit', 'do_tro_pct']].tail(6), hide_index=True)

    with col_m:
        st.markdown("##### 📆 Báo Cáo Tháng (Monthly Report)")
        sel_m_rep = st.selectbox(
            "📆 Click chọn tháng xem chi tiết (Tháng 1 - 12):",
            options=ALL_MONTHS_CODE_12,
            index=default_m_code_idx,
            key="sb_month_rep_tab2"
        )
        row_m_df = df_monthly[df_monthly['month_label'] == sel_m_rep] if not df_monthly.empty else pd.DataFrame()
        if not row_m_df.empty:
            r_val = row_m_df.iloc[0]
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Sản Lượng", f"{r_val.get('san_luong_tan', 0):,.1f} t")
            cm2.metric("Suất Điện", f"{r_val.get('dien_tb_kwh_tan', 0):.1f} kWh/t")
            cm3.metric("Năng Suất Ép", f"{r_val.get('nang_suat_ep_tph', 0):.2f} t/h")
        else:
            # Kiểm tra df_shifts cho tháng này
            try:
                m_num_r, y_num_r = map(int, sel_m_rep.split('/'))
                m_shifts_r = df_shifts[
                    (df_shifts['date'].dt.month == m_num_r) & 
                    (df_shifts['date'].dt.year == y_num_r)
                ]
            except Exception:
                m_shifts_r = pd.DataFrame()

            if not m_shifts_r.empty:
                m_tot_out = float(m_shifts_r['san_luong_tan'].sum())
                m_tot_h = float(m_shifts_r['tong_gio_ep'].sum())
                m_tot_kwh = float(m_shifts_r['dien_kwh'].sum())
                m_avg_e = m_tot_kwh / m_tot_out if m_tot_out > 0 else 0.0
                m_avg_p = m_tot_out / m_tot_h if m_tot_h > 0 else 0.0
                cm1, cm2, cm3 = st.columns(3)
                cm1.metric("Sản Lượng (Ca)", f"{m_tot_out:,.1f} t")
                cm2.metric("Suất Điện TB", f"{m_avg_e:.1f} kWh/t")
                cm3.metric("Năng Suất Ép TB", f"{m_avg_p:.2f} t/h")
            else:
                st.info(f"ℹ️ Tháng {sel_m_rep} chưa có dữ liệu sản xuất.")

        if not df_monthly.empty:
            fig_m = px.bar(
                df_monthly,
                x='month_label',
                y='san_luong_tan',
                text='san_luong_tan',
                title="Sản Lượng Theo Tháng (Tấn)",
                color_discrete_sequence=['#8b5cf6']
            )
            fig_m.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_m.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_m, use_container_width=True, key="fig_m_tab2_bar")
            st.dataframe(df_monthly[['month_label', 'san_luong_tan', 'dien_tb_kwh_tan', 'nang_suat_ep_tph', 'do_tro_pct']].tail(6), hide_index=True)

# ----------------- TAB 3: GIÁM SÁT CỤM THIẾT BỊ -----------------
elif task_num == 4:
    st.markdown('<div class="section-title">🛠️ Bảng Thống Kê Giờ Hoạt Động Cụm Thiết Bị Toàn Nhà Máy</div>', unsafe_allow_html=True)
    
    df_eq_stats = get_equipment_statistics(df_shifts)
    if not df_eq_stats.empty:
        st.dataframe(
            df_eq_stats,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tỷ lệ sử dụng (%)": st.column_config.ProgressColumn(
                    "Tỷ lệ sử dụng (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

        c_bar1, c_bar2 = st.columns(2)
        with c_bar1:
            # So sánh tổng giờ chạy 8 máy ép
            df_pe = df_eq_stats[df_eq_stats['Cụm thiết bị'] == 'Máy ép viên']
            fig_pe_comp = px.bar(
                df_pe,
                x='Mã TB',
                y='Tổng giờ chạy (h)',
                text='Tổng giờ chạy (h)',
                color='Tổng giờ chạy (h)',
                color_continuous_scale='Viridis',
                title="Tổng Giờ Hoạt Động Của Từng Máy Ép (PE1 - PE8)"
            )
            fig_pe_comp.update_traces(texttemplate='%{text:,.0f}h', textposition='outside')
            fig_pe_comp.update_layout(height=360)
            st.plotly_chart(fig_pe_comp, use_container_width=True)

        with c_bar2:
            # So sánh giờ máy nghiền búa Andritz vs SHT
            df_hm = df_eq_stats[df_eq_stats['Cụm thiết bị'].str.contains('Nghiền búa')]
            fig_hm_comp = px.bar(
                df_hm,
                x='Mã TB',
                y='Tổng giờ chạy (h)',
                color='Hãng / Chủng loại',
                text='Tổng giờ chạy (h)',
                barmode='group',
                title="Giờ Hoạt Động Máy Nghiền Búa (Andritz vs SHT)"
            )
            fig_hm_comp.update_traces(texttemplate='%{text:,.0f}h', textposition='outside')
            fig_hm_comp.update_layout(height=360)
            st.plotly_chart(fig_hm_comp, use_container_width=True)

# ----------------- TAB INCIDENTS: QUẢN LÝ & CẢNH BÁO SỰ CỐ THIẾT BỊ -----------------
elif task_num == 5:
    st.markdown('<div class="section-title">🚨 HỆ THỐNG QUẢN LÝ & CẢNH BÁO SỰ CỐ THIẾT BỊ (SHEET SỰ CỐ)</div>', unsafe_allow_html=True)
    st.caption("Dữ liệu tự động từ sheet `Su co` - Thống kê sự cố hàng ngày & hàng tuần, vẽ biểu đồ và bật cảnh báo cho các thiết bị.")

    if not df_incidents.empty:
        # Bộ lọc chu kỳ cho Sự Cố: Ngày, Tuần, Tháng hoặc Toàn bộ
        col_inc_mode, col_inc_sel = st.columns([1, 2])
        with col_inc_mode:
            inc_filter_mode = st.radio(
                "Bộ lọc thời gian sự cố:",
                ["📅 Theo Tuần (52 tuần)", "📆 Theo Tháng (12 tháng)", "📅 Theo Ngày Cụ Thể", "Toàn bộ lịch sử"],
                index=0,
                key="inc_filter_mode_radio"
            )

        target_inc_w = None
        target_inc_m = None
        target_inc_d = None

        with col_inc_sel:
            if inc_filter_mode == "📅 Theo Tuần (52 tuần)":
                target_inc_w = st.selectbox("Chọn tuần xem sự cố:", ALL_WEEKS_52, index=default_w_idx, key="sb_inc_week")
            elif inc_filter_mode == "📆 Theo Tháng (12 tháng)":
                target_inc_m = st.selectbox("Chọn tháng xem sự cố:", ALL_MONTHS_CODE_12, index=default_m_code_idx, key="sb_inc_month")
            elif inc_filter_mode == "📅 Theo Ngày Cụ Thể":
                inc_dates = [d for d in df_incidents['date_str'].unique() if d]
                target_inc_d = st.selectbox("Chọn ngày xem sự cố:", inc_dates, index=len(inc_dates)-1 if inc_dates else 0, key="sb_inc_day")

        # Tính toán thống kê & cảnh báo
        inc_stats = get_incident_statistics(df_incidents, target_date=target_inc_d, target_week=target_inc_w, target_month=target_inc_m)
        alerts_list = get_equipment_incident_alerts(df_incidents, target_week=target_inc_w, target_date=target_inc_d)

        # --- KHU VỰC BẬT CẢNH BÁO CHO CÁC THIẾT BỊ (ALERTS) ---
        st.markdown("---")
        st.markdown("#### ⚡ HỆ THỐNG CẢNH BÁO THIẾT BỊ HƯ HỎNG & BẢO TRÌ SỰ CỐ")
        
        red_alerts = [a for a in alerts_list if a['severity'] == 'RED']
        yellow_alerts = [a for a in alerts_list if a['severity'] == 'YELLOW']

        if red_alerts:
            st.error(f"🚨 **PHÁT HIỆN {len(red_alerts)} THIẾT BỊ BÁO ĐỘNG ĐỎ VỀ SỰ CỐ!** Cần can thiệp bảo trì khẩn cấp hoặc rà soát chế độ vận hành.")
        elif yellow_alerts:
            st.warning(f"⚠️ **CẢNH BÁO:** Có {len(yellow_alerts)} thiết bị ghi nhận sự cố lặp lại. Cần theo dõi kiểm tra ca tiếp.")
        else:
            st.success("✅ **AN TOÀN:** Không ghi nhận sự cố nghiêm trọng trên các cụm máy trong kỳ được chọn.")

        if alerts_list:
            c_al1, c_al2 = st.columns(2)
            for idx, al in enumerate(alerts_list[:8]):
                target_col = c_al1 if (idx % 2 == 0) else c_al2
                with target_col:
                    border_color = "#ef4444" if al['severity'] == 'RED' else "#eab308"
                    bg_color = "#fef2f2" if al['severity'] == 'RED' else "#fefce8"
                    badge_style = "background:#fee2e2; color:#b91c1c;" if al['severity'] == 'RED' else "background:#fef3c7; color:#b45309;"
                    
                    issues_html = "<br/>".join([f"• {desc}" for desc in al['descriptions']])
                    dates_html = ", ".join(al['recent_dates'])

                    st.markdown(f"""
                    <div style="background:{bg_color}; border:1.5px solid {border_color}; border-radius:10px; padding:12px 16px; margin-bottom:12px; box-shadow:0 2px 5px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong style="font-size:17px; color:#0f172a;">{al['icon']} Thiết bị: <code>{al['equipment']}</code></strong>
                            <span style="{badge_style} padding:3px 8px; border-radius:6px; font-size:12px; font-weight:700;">{al['level_label']}</span>
                        </div>
                        <div style="font-size:13px; color:#1e293b; line-height:1.6;">
                            <b>Trạng thái:</b> {al['message']}<br/>
                            <b>Hiện tượng / Sự cố:</b><br/>{issues_html}<br/>
                            <span style="font-size:11px; color:#64748b;">Thời gian ghi nhận: {dates_html}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        # 4 Thẻ KPI Sự Cố
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        with c_i1:
            st.metric("Tổng Số Vụ Sự Cố", f"{inc_stats['total_incidents']} vụ")
        with c_i2:
            st.metric("Tổng Giờ Dừng Máy", f"{inc_stats['total_hours']} giờ")
        with c_i3:
            st.metric("Số Vụ Bảo Trì Sự Cố", f"{inc_stats['breakdown_count']} vụ", f"{inc_stats['proactive_count']} chủ động")
        with c_i4:
            st.metric("Tỷ Lệ Xử Lý Hoàn Thành", f"{inc_stats['completion_rate']}%", f"{inc_stats['pending_count']} chưa xong")

        # Biểu đồ Sự Cố
        c_ch1, c_ch2 = st.columns(2)
        with c_ch1:
            df_eq_st = inc_stats['equipment_stats']
            if not df_eq_st.empty:
                fig_eq_inc = px.bar(
                    df_eq_st.head(10),
                    x='Mã Thiết Bị',
                    y='Số Vụ Sự Cố',
                    text='Số Vụ Sự Cố',
                    color='Tổng Giờ Dừng (h)',
                    color_continuous_scale='Reds',
                    title="Top Thiết Bị Phát Sinh Sự Cố Nhiều Nhất"
                )
                fig_eq_inc.update_traces(textposition='outside')
                fig_eq_inc.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_eq_inc, use_container_width=True, key="fig_eq_inc_bar")
            else:
                st.info("Không có sự cố thiết bị trong kỳ này.")

        with c_ch2:
            df_cause_st = inc_stats['cause_stats']
            if not df_cause_st.empty:
                fig_cause = px.bar(
                    df_cause_st.head(8),
                    y='Nguyên Nhân / Hiện Tượng',
                    x='Số Lần',
                    text='Số Lần',
                    orientation='h',
                    color_discrete_sequence=['#f97316'],
                    title="Các Nguyên Nhân / Hiện Tượng Sự Cố Phổ Biến"
                )
                fig_cause.update_traces(textposition='outside')
                fig_cause.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20), yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_cause, use_container_width=True, key="fig_cause_bar")
            else:
                st.info("Không có dữ liệu nguyên nhân sự cố.")

        # Thống kê theo ca trưởng & Danh sách sự cố chi tiết
        c_ldr_inc, c_tbl_inc = st.columns([1, 2])
        with c_ldr_inc:
            df_ldr_st = inc_stats['leader_stats']
            if not df_ldr_st.empty:
                st.markdown("##### 👤 Sự Cố Theo Ca Trưởng Trực")
                fig_ldr_inc = px.pie(
                    df_ldr_st,
                    names='Ca Trưởng Trực',
                    values='Số Vụ Sự Cố',
                    title="Tỷ Trọng Sự Cố Giữa Các Ca",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_ldr_inc.update_layout(height=280, margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig_ldr_inc, use_container_width=True, key="fig_ldr_inc_pie")

        with c_tbl_inc:
            st.markdown("##### 📋 Bảng Chi Tiết Các Vụ Sự Cố Đã Ghi Nhận")
            df_show_inc = inc_stats['df_filtered']
            if not df_show_inc.empty:
                cols_inc_disp = ['id_su_co', 'date_str', 'shift_leader', 'equipment_raw', 'description', 'solution', 'performer', 'duration_hours', 'status']
                avail_c_inc = [c for c in cols_inc_disp if c in df_show_inc.columns]
                df_disp_inc = df_show_inc[avail_c_inc].copy()
                df_disp_inc.rename(columns={
                    'id_su_co': 'ID',
                    'date_str': 'Ngày',
                    'shift_leader': 'Ca Trưởng',
                    'equipment_raw': 'Mã Thiết Bị',
                    'description': 'Mô Tả Sự Cố',
                    'solution': 'Biện Pháp Xử Lý',
                    'performer': 'Người Xử Lý',
                    'duration_hours': 'Giờ Dừng',
                    'status': 'Trạng Thái'
                }, inplace=True)
                st.dataframe(df_disp_inc, hide_index=True, use_container_width=True)
            else:
                st.info("Không có bản ghi sự cố nào.")
    else:
        st.info("Chưa có dữ liệu từ sheet 'Su co'.")

# ----------------- TAB MAINT LOG: NHẬT KÝ BẢO TRÌ & SỬA CHỮA (2026 BẢO TRÌ BVN) -----------------
elif task_num == 6:
    st.markdown('<div class="section-title">🔧 NHẬT KÝ BẢO TRÌ, GIA CÔNG & PHỤC HỒI THIẾT BỊ (2026 BẢO TRÌ BVN)</div>', unsafe_allow_html=True)
    st.caption(f"Nguồn dữ liệu: **{maint_log_title}** (Google Sheets ID: `1hInwQQgN3zXWFEXC1qaFgaXeIiogXUJtm0cPgP3PlX8`)")

    if not df_maint_log.empty:
        # Bộ lọc thiết bị và loại bảo trì
        c_ml_f1, c_ml_f2, c_ml_f3 = st.columns(3)
        with c_ml_f1:
            all_acts = ["Tất cả"] + sorted([a for a in df_maint_log['activity'].unique() if a])
            sel_act = st.selectbox("Loại hoạt động bảo trì:", all_acts, key="sb_ml_act")
        with c_ml_f2:
            all_eqs = ["Tất cả"] + sorted([e for e in df_maint_log['equipment'].unique() if e])
            sel_eq = st.selectbox("Lọc theo thiết bị:", all_eqs, key="sb_ml_eq")
        with c_ml_f3:
            all_status = ["Tất cả"] + sorted([s for s in df_maint_log['status'].unique() if s])
            sel_status = st.selectbox("Trạng thái:", all_status, key="sb_ml_status")

        df_ml_filt = df_maint_log.copy()
        if sel_act != "Tất cả":
            df_ml_filt = df_ml_filt[df_ml_filt['activity'] == sel_act]
        if sel_eq != "Tất cả":
            df_ml_filt = df_ml_filt[df_ml_filt['equipment'] == sel_eq]
        if sel_status != "Tất cả":
            df_ml_filt = df_ml_filt[df_ml_filt['status'] == sel_status]

        # Thẻ KPI
        tot_maint = len(df_ml_filt)
        tot_proactive = len(df_ml_filt[df_ml_filt['activity'].str.contains('Bảo trì chủ động', case=False, na=False)])
        tot_rulo_die = len(df_ml_filt[df_ml_filt['activity'].str.contains('rulo|khuôn', case=False, na=False)])
        tot_done = len(df_ml_filt[df_ml_filt['status'].str.contains('Hoàn thành', case=False, na=False)])
        rate_done = round(tot_done / tot_maint * 100, 1) if tot_maint > 0 else 100.0

        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Tổng Số Lượt Bảo Trì", f"{tot_maint:,} lượt")
        c_m2.metric("Bảo Trì Chủ Động", f"{tot_proactive:,} lượt")
        c_m3.metric("Phục Hồi Rulo & Khuôn", f"{tot_rulo_die:,} lượt")
        c_m4.metric("Tỷ Lệ Hoàn Thành", f"{rate_done}%")

        # Biểu đồ phân bổ
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            df_act_cnt = df_maint_log['activity'].value_counts().head(7).reset_index()
            df_act_cnt.columns = ['Hoạt Động', 'Số Lần']
            fig_act = px.pie(
                df_act_cnt,
                names='Hoạt Động',
                values='Số Lần',
                title="Cơ Cấu Hoạt Động Bảo Trì & Sửa Chữa Toàn Nhà Máy",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_act.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_act, use_container_width=True, key="fig_act_pie")

        with c_g2:
            df_eq_cnt = df_maint_log[df_maint_log['equipment'] != '']['equipment'].value_counts().head(10).reset_index()
            df_eq_cnt.columns = ['Thiết Bị', 'Số Lần Bảo Trì']
            fig_eq_m = px.bar(
                df_eq_cnt,
                x='Thiết Bị',
                y='Số Lần Bảo Trì',
                text='Số Lần Bảo Trì',
                color='Số Lần Bảo Trì',
                color_continuous_scale='Blues',
                title="Top 10 Thiết Bị Được Bảo Dưỡng & Sửa Chữa Nhiều Nhất"
            )
            fig_eq_m.update_traces(textposition='outside')
            fig_eq_m.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_eq_m, use_container_width=True, key="fig_eq_maint_bar")

        st.markdown("##### 📋 Bảng Chi Tiết Nhật Ký Bảo Trì Thiết Bị")
        cols_ml_disp = ['date_str', 'ca', 'equipment', 'die_code', 'activity', 'description', 'performer', 'status']
        avail_ml_cols = [c for c in cols_ml_disp if c in df_ml_filt.columns]
        df_show_ml = df_ml_filt[avail_ml_cols].copy()
        df_show_ml.rename(columns={
            'date_str': 'Ngày',
            'ca': 'Ca / Người Trực',
            'equipment': 'Mã Thiết Bị',
            'die_code': 'Mã Khuôn',
            'activity': 'Hoạt Động',
            'description': 'Nội Dung Công Việc',
            'performer': 'Người Thực Hiện',
            'status': 'Trạng Thái'
        }, inplace=True)
        st.dataframe(df_show_ml, hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu từ bảng tính '2026 BẢO TRÌ BVN'.")

# ----------------- TAB MAINT PLAN: KẾ HOẠCH BẢO TRÌ & QUẢN TRỊ 4M -----------------
elif task_num == 7:
    st.markdown('<div class="section-title">🛠️ KẾ HOẠCH BẢO TRÌ ĐỊNH KỲ, QUẢN TRỊ 4M & LỊCH THAY NHỚT MÁY ÉP</div>', unsafe_allow_html=True)
    st.caption(f"Nguồn dữ liệu: **{maint_plan_title}** & **{oil_title}** (Google Sheets ID: `1DRHrUPkLk7650XbxW1zZ73dp0k0Dcg4FZeKZriUKRso`)")

    subtab_plan, subtab_4m, subtab_oil = st.tabs([
        "📅 KẾ HOẠCH BẢO TRÌ THEO THÁNG",
        "🎯 QUẢN TRỊ CHIẾN LƯỢC 4M (6 THÁNG CUỐI NĂM 2026)",
        "🛢️ LỊCH THAY NHỚT HỘP SỐ MÁY ÉP (MOBIL GLYGOYLE 460)"
    ])

    with subtab_plan:
        if not df_maint_plan.empty:
            avail_months = sorted(list(df_maint_plan['month_label'].unique()), reverse=True)
            sel_plan_m = st.selectbox("📆 Click chọn tháng xem kế hoạch bảo trì:", avail_months, key="sb_plan_month")
            df_plan_sub = df_maint_plan[df_maint_plan['month_label'] == sel_plan_m]

            tot_tasks = len(df_plan_sub)
            done_tasks = len(df_plan_sub[df_plan_sub['status'].str.contains('Đã hoàn thành', case=False, na=False)])
            prog_tasks = len(df_plan_sub[df_plan_sub['status'].str.contains('Đang thực hiện', case=False, na=False)])
            not_started = len(df_plan_sub[df_plan_sub['status'].str.contains('Chưa bắt đầu', case=False, na=False)])
            urgent_tasks = len(df_plan_sub[df_plan_sub['priority'].str.contains('Khẩn cấp|Cao', case=False, na=False)])
            pct_done = round(done_tasks / tot_tasks * 100, 1) if tot_tasks > 0 else 0.0

            cp1, cp2, cp3, cp4, cp5 = st.columns(5)
            cp1.metric("Tổng Số Công Việc", f"{tot_tasks} việc")
            cp2.metric("Đã Hoàn Thành", f"{done_tasks} việc ({pct_done}%)")
            cp3.metric("Đang Thực Hiện", f"{prog_tasks} việc")
            cp4.metric("Chưa Bắt Đầu", f"{not_started} việc")
            cp5.metric("Mức Độ Khẩn Cấp / Cao", f"{urgent_tasks} việc")

            st.markdown("---")
            c_pchart1, c_pchart2 = st.columns(2)
            with c_pchart1:
                df_p_st = df_plan_sub['status'].value_counts().reset_index()
                df_p_st.columns = ['Trạng Thái', 'Số Việc']
                fig_pst = px.pie(
                    df_p_st,
                    names='Trạng Thái',
                    values='Số Việc',
                    title=f"Tiến Độ Thực Hiện Kế Hoạch - {sel_plan_m}",
                    hole=0.4,
                    color_discrete_sequence=['#16a34a', '#0284c7', '#f59e0b', '#dc2626']
                )
                fig_pst.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_pst, use_container_width=True, key="fig_plan_status_pie")

            with c_pchart2:
                df_p_mat = df_plan_sub[df_plan_sub['material'] != '']['material'].value_counts().reset_index()
                df_p_mat.columns = ['Tình Trạng Vật Tư', 'Số Việc']
                fig_mat = px.bar(
                    df_p_mat,
                    x='Tình Trạng Vật Tư',
                    y='Số Việc',
                    text='Số Việc',
                    color='Tình Trạng Vật Tư',
                    color_discrete_sequence=['#10b981', '#ef4444', '#f59e0b'],
                    title="Nhu Cầu & Tình Trạng Vật Tư Phụ Tùng"
                )
                fig_mat.update_traces(textposition='outside')
                fig_mat.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20), showlegend=False)
                st.plotly_chart(fig_mat, use_container_width=True, key="fig_plan_mat_bar")

            st.markdown(f"##### 📋 Danh Mục Công Việc Kế Hoạch Bảo Trì - {sel_plan_m}")
            disp_plan_cols = ['task_name', 'equipment', 'priority', 'pic', 'status', 'start_date', 'end_date', 'total_days', 'material', 'material_status']
            avail_p_cols = [c for c in disp_plan_cols if c in df_plan_sub.columns]
            df_disp_plan = df_plan_sub[avail_p_cols].copy()
            df_disp_plan.rename(columns={
                'task_name': 'Hạng Mục Công Việc',
                'equipment': 'Mã Thiết Bị',
                'priority': 'Ưu Tiên',
                'pic': 'Phụ Trách',
                'status': 'Trạng Thái',
                'start_date': 'Bắt Đầu',
                'end_date': 'Kết Thúc',
                'total_days': 'Số Ngày',
                'material': 'Vật Tư',
                'material_status': 'Phụ Thuộc'
            }, inplace=True)
            st.dataframe(df_disp_plan, hide_index=True, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu kế hoạch bảo trì theo tháng.")

    with subtab_4m:
        st.markdown("### 🎯 BẢNG QUẢN TRỊ CHIẾN LƯỢC 4M (6 THÁNG CUỐI NĂM 2026)")
        st.markdown("""
        Mô hình quản trị 4M trong sản xuất:
        - 👥 **Men (Con người):** Đào tạo tay nghề ép viên, luân chuyển tổ, xây dựng nhân sự lõi, văn hóa kỹ trị.
        - 🪵 **Material (Nguyên vật liệu):** Nâng tỷ lệ vỏ cây đốt >60%, kiểm soát độ ẩm, phối trộn nguyên liệu tối ưu giá thành.
        - 📐 **Method (Phương pháp / Quy trình):** Mô hình quản lý, kỷ luật vận hành, chuẩn hóa quy trình, cải tiến.
        - 📊 **Measurement (Đo lường / Thống kê):** Nâng cao kỹ năng đo lường, hạch toán năng lượng từng khâu, hệ thống báo cáo.
        """)

        if not df_4m.empty:
            c_4m1, c_4m2, c_4m3, c_4m4 = st.columns(4)
            c_4m1.metric("👥 1. Men (Con người)", f"{len(df_4m[df_4m['pillar']=='Men'])} mục tiêu")
            c_4m2.metric("🪵 2. Material (Nguyên liệu)", f"{len(df_4m[df_4m['pillar']=='Material'])} mục tiêu")
            c_4m3.metric("📐 3. Method (Phương pháp)", f"{len(df_4m[df_4m['pillar']=='Method'])} mục tiêu")
            c_4m4.metric("📊 4. Measurement (Đo lường)", f"{len(df_4m[df_4m['pillar']=='Measurement'])} mục tiêu")

            st.markdown("---")
            sel_pillar = st.selectbox(
                "Lọc theo trụ cột 4M:",
                ["Tất cả 4M", "Men (Con người)", "Material (Nguyên vật liệu)", "Method (Phương pháp)", "Measurement (Đo lường)"],
                key="sb_4m_pillar"
            )

            df_4m_disp = df_4m.copy()
            if sel_pillar != "Tất cả 4M":
                pillar_code = sel_pillar.split()[0]
                df_4m_disp = df_4m_disp[df_4m_disp['pillar'] == pillar_code]

            disp_4m_cols = ['pillar', 'objective', 'action', 'pic', 'deadline', 'status', 'evaluation']
            avail_4m_cols = [c for c in disp_4m_cols if c in df_4m_disp.columns]
            df_4m_table = df_4m_disp[avail_4m_cols].copy()
            df_4m_table.rename(columns={
                'pillar': 'Trụ Cột 4M',
                'objective': 'Mục Tiêu Chiến Lược',
                'action': 'Hành Động Cụ Thể',
                'pic': 'Người Phụ Trách',
                'deadline': 'Hạn Chót',
                'status': 'Trạng Thái',
                'evaluation': 'Đánh Giá'
            }, inplace=True)
            st.dataframe(df_4m_table, hide_index=True, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu từ sheet 'Theo dõi 4M2026'.")

    with subtab_oil:
        st.markdown("### 🛢️ LỊCH THAY NHỚT HỘP SỐ MÁY ÉP VIÊN NÉN (MOBIL GLYGOYLE 460)")
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #3b82f6; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;">
            <div style="font-size: 15px; font-weight: 700; color: #60a5fa; margin-bottom: 6px;">
                ⚙️ TIÊU CHUẨN KỸ THUẬT DẦU BÔI TRƠN HỘP SỐ MÁY ÉP ANDRITZ PM30 (PE1 - PE8)
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; font-size: 13px; color: #cbd5e1;">
                <div>🔹 <b>Chủng loại dầu:</b> <span style="color: #facc15; font-weight: 600;">Mobil Glygoyle 460</span> (PAG tổng hợp)</div>
                <div>🔹 <b>Định mức thay dầu:</b> <span style="color: #38bdf8; font-weight: 600;">4.000 giờ</span> vận hành / chu kỳ</div>
                <div>🔹 <b>Dung tích mỗi máy:</b> <span style="color: #4ade80; font-weight: 600;">208 Lít</span> (1 phuy / máy)</div>
                <div>🔹 <b>Tổng dung tích xưởng:</b> <span style="color: #fb923c; font-weight: 600;">1.664 Lít</span> (8 máy PE1 - PE8)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_oil_sum = oil_change_data.get('summary', pd.DataFrame())
        oil_details = oil_change_data.get('details', {})

        if not df_oil_sum.empty:
            tot_machines = len(df_oil_sum)
            tot_oil_lit = float(df_oil_sum['oil_capacity_l'].sum()) if 'oil_capacity_l' in df_oil_sum.columns else 1664.0
            c1_done_count = len(df_oil_sum[df_oil_sum['change_status_c1'].astype(str).str.contains('Đã thay', case=False, na=False)])
            c1_pct = round(c1_done_count / tot_machines * 100, 1) if tot_machines > 0 else 100.0
            latest_change_date = df_oil_sum['change_date_c1'].iloc[0] if 'change_date_c1' in df_oil_sum.columns else "18/09/2026"

            c_o1, c_o2, c_o3, c_o4, c_o5 = st.columns(5)
            c_o1.metric("Tổng Máy Ép", f"{tot_machines} máy", "PE1 → PE8")
            c_o2.metric("Tổng Lượng Nhớt", f"{tot_oil_lit:,.0f} Lít", "208 L / máy")
            c_o3.metric("Định Mức Chu Kỳ", "4.000 Giờ", "Mobil Glygoyle 460")
            c_o4.metric("Tiến Độ Lần 1", f"{c1_done_count}/{tot_machines} máy ({c1_pct}%)", f"Ngày {latest_change_date}")
            c_o5.metric("Chu Kỳ Hiện Tại", "Chu kỳ 2 (0h)", "Bình thường")

            st.markdown("---")

            c_og1, c_og2 = st.columns([3, 2])
            with c_og1:
                fig_oil_bar = px.bar(
                    df_oil_sum,
                    x='machine_code',
                    y='run_hours_c1',
                    text='run_hours_c1',
                    labels={'machine_code': 'Máy Ép', 'run_hours_c1': 'Giờ Chạy Thực Tế (h)'},
                    title="Số Giờ Vận Hành Thực Tế Khi Thay Nhớt Lần 1 vs Định Mức 4.000h",
                    color='run_hours_c1',
                    color_continuous_scale=['#38bdf8', '#10b981', '#f59e0b', '#ef4444']
                )
                fig_oil_bar.add_hline(
                    y=4000, 
                    line_dash="dash", 
                    line_color="#ef4444", 
                    annotation_text="Định mức chuẩn: 4.000h", 
                    annotation_position="top left",
                    annotation_font_color="#ef4444"
                )
                fig_oil_bar.update_traces(texttemplate='%{text:,.1f}h', textposition='outside')
                fig_oil_bar.update_layout(
                    height=320, 
                    margin=dict(t=40, b=20, l=20, r=20),
                    coloraxis_showscale=False,
                    yaxis=dict(range=[0, 4800])
                )
                st.plotly_chart(fig_oil_bar, use_container_width=True, key="fig_oil_c1_bar")

            with c_og2:
                df_st_c1 = df_oil_sum['change_status_c1'].value_counts().reset_index()
                df_st_c1.columns = ['Trạng Thái', 'Số Máy']
                fig_oil_pie = px.pie(
                    df_st_c1,
                    names='Trạng Thái',
                    values='Số Máy',
                    title=f"Tỷ Lệ Hoàn Thành Lần 1 ({latest_change_date})",
                    hole=0.45,
                    color_discrete_sequence=['#10b981', '#f59e0b']
                )
                fig_oil_pie.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_oil_pie, use_container_width=True, key="fig_oil_pie_c1")

            st.markdown("##### 📋 Bảng Tổng Hợp Theo Dõi Thay Nhớt Hộp Số PE1 - PE8")
            disp_oil = df_oil_sum.copy()
            disp_oil['Tỷ Lệ Giờ Đạt C1'] = (disp_oil['run_hours_c1'] / disp_oil['standard_hours'] * 100).round(1).astype(str) + '%'
            disp_oil.rename(columns={
                'machine_code': 'Mã Máy',
                'machine_name': 'Tên Thiết Bị',
                'oil_type': 'Loại Nhớt Bôi Trơn',
                'oil_capacity_l': 'Dung Tích (L)',
                'standard_hours': 'Định Mức (h)',
                'run_hours_c1': 'Giờ Chạy Lần 1 (h)',
                'change_date_c1': 'Ngày Thay Lần 1',
                'change_status_c1': 'Trạng Thái Lần 1',
                'run_hours_c2': 'Giờ Chu Kỳ 2 (h)',
                'alert_status_c2': 'Nhắc Nhở Chu Kỳ 2'
            }, inplace=True)
            
            ordered_cols = ['Mã Máy', 'Tên Thiết Bị', 'Loại Nhớt Bôi Trơn', 'Dung Tích (L)', 'Định Mức (h)', 'Giờ Chạy Lần 1 (h)', 'Tỷ Lệ Giờ Đạt C1', 'Ngày Thay Lần 1', 'Trạng Thái Lần 1', 'Giờ Chu Kỳ 2 (h)', 'Nhắc Nhở Chu Kỳ 2']
            avail_oil_cols = [c for c in ordered_cols if c in disp_oil.columns]
            st.dataframe(disp_oil[avail_oil_cols], hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("##### 🔍 Chi Tiết Kế Hoạch 10 Chu Kỳ Thay Nhớt Từng Máy Ép")
            sel_pe = st.selectbox(
                "Chọn máy ép để kiểm tra chi tiết toàn bộ chu kỳ:",
                [f"PE{i}" for i in range(1, 9)],
                key="sb_oil_pe_detail"
            )
            
            if sel_pe in oil_details and not oil_details[sel_pe].empty:
                df_pe_dt = oil_details[sel_pe].copy()
                st.dataframe(df_pe_dt, hide_index=True, use_container_width=True)
            else:
                st.info(f"Chưa có bảng chi tiết chu kỳ cho {sel_pe}.")

            st.markdown("""
            > [!NOTE]
            > **Khuyến nghị kỹ thuật:** Dầu **Mobil Glygoyle 460** là dầu tổng hợp gốc Polyalkylene Glycol (PAG). Tuyệt đối **không pha trộn** với dầu gốc khoáng hoặc dầu gốc PAO/Ester khác. Khi thay nhớt cần xả kiệt cặn dầu cũ, vệ sinh nam châm bẫy mạt kim loại và kiểm tra độ kín các phớt làm kín của hộp số máy ép.
            """)
        else:
            st.info("Chưa có dữ liệu từ bảng tính 'Lịch thay nhớt hộp số máy ép'.")

# ----------------- TAB 8: KIỂM TRA CHẤT LƯỢNG KCS -----------------
elif task_num == 8:
    st.markdown('<div class="section-title">🔬 Kiểm Tra Chất Lượng KCS: Độ Ẩm, Độ Tro & Tỷ Trọng Viên Nén</div>', unsafe_allow_html=True)
    st.caption("Dữ liệu kiểm nghiệm chất lượng sản phẩm từ sheet KCS & Tổng hợp ngày - Tiêu chuẩn xuất khẩu ISO 17225-2 / ENplus.")
    
    if not df_kcs.empty:
        # Thẻ tóm tắt chỉ số KCS mới nhất
        last_kcs = df_kcs.iloc[-1] if not df_kcs.empty else {}
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        am_vien_val = last_kcs.get('am_vien_pct', 0.0)
        tro_val = last_kcs.get('do_tro_pct', 0.0)
        ty_trong_latest = df_daily['ty_trong_vien'].dropna().iloc[-1] if (not df_daily.empty and 'ty_trong_vien' in df_daily.columns and (df_daily['ty_trong_vien'] > 0).any()) else 0.0
        
        with c_k1:
            st.metric("💧 Độ Ẩm Viên Mẫu Mới Nhất", f"{am_vien_val:.2f}%" if am_vien_val > 0 else "N/A", "Chuẩn 8.0 - 9.5%")
        with c_k2:
            st.metric("🔥 Độ Tro Mẫu Mới Nhất", f"{tro_val:.2f}%" if tro_val > 0 else "N/A", "Chuẩn ≤ 1.5%")
        with c_k3:
            st.metric("⚖️ Tỷ Trọng Thể Tích", f"{ty_trong_latest:,.0f} kg/m³" if ty_trong_latest > 0 else "N/A", f"Chuẩn ≥ {DENSITY_BENCHMARK_MIN:.0f} kg/m³")
        with c_k4:
            st.metric("🧪 Ca Trưởng Phụ Trách", f"Ca {last_kcs.get('shift_leader', 'N/A')}", f"Lúc {last_kcs.get('time_sample', '')} ({last_kcs.get('date_str', '')})")

        st.markdown("---")
        col_kcs_chart1, col_kcs_chart2 = st.columns(2)
        with col_kcs_chart1:
            recent_kcs = df_kcs.tail(30)
            fig_am = go.Figure()
            if 'am_vien_pct' in recent_kcs.columns and recent_kcs['am_vien_pct'].max() > 0:
                fig_am.add_trace(go.Scatter(
                    x=recent_kcs['date_str'],
                    y=recent_kcs['am_vien_pct'],
                    mode='lines+markers',
                    name='Độ ẩm viên (%)',
                    line=dict(color='#0284c7', width=2)
                ))
            fig_am.add_hline(y=9.5, line_dash="dash", line_color="red", annotation_text="Trần chuẩn (9.5%)")
            fig_am.add_hline(y=8.0, line_dash="dash", line_color="green", annotation_text="Sàn chuẩn (8.0%)")
            fig_am.update_layout(
                title="Biểu Đồ Xu Hướng Độ Ẩm Viên Nén (%) 30 Mẫu Gần Đây",
                xaxis_title="Thời gian lấy mẫu",
                yaxis_title="Độ ẩm (%)",
                height=320,
                margin=dict(t=40, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_am, use_container_width=True)

        with col_kcs_chart2:
            if not df_daily.empty and 'ty_trong_vien' in df_daily.columns:
                recent_daily = df_daily[df_daily['ty_trong_vien'] > 0].tail(30)
                if not recent_daily.empty:
                    fig_dens = go.Figure()
                    fig_dens.add_trace(go.Scatter(
                        x=recent_daily['date_str'],
                        y=recent_daily['ty_trong_vien'],
                        mode='lines+markers',
                        name='Tỷ trọng viên (kg/m³)',
                        line=dict(color='#10b981', width=2)
                    ))
                    fig_dens.add_hline(y=DENSITY_BENCHMARK_MIN, line_dash="dash", line_color="#f59e0b", annotation_text=f"Chuẩn tối thiểu ({DENSITY_BENCHMARK_MIN:,.0f} kg/m³)")
                    fig_dens.update_layout(
                        title="Diễn Biến Tỷ Trọng Thể Tích Viên Nén (kg/m³)",
                        xaxis_title="Ngày",
                        yaxis_title="kg/m³",
                        height=320,
                        margin=dict(t=40, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig_dens, use_container_width=True)

        st.markdown("##### 📋 Nhật Ký Kết Quả Đo Kiểm KCS Gần Nhất")
        disp_kcs_cols = ['date_str', 'time_sample', 'shift_leader', 'am_sau_say_1_pct', 'am_sau_say_2_pct', 'am_vien_pct', 'do_tro_pct']
        avail_k_cols = [c for c in disp_kcs_cols if c in df_kcs.columns]
        df_kcs_disp = df_kcs[avail_k_cols].tail(15).copy()
        df_kcs_disp.rename(columns={
            'date_str': 'Ngày',
            'time_sample': 'Giờ lấy mẫu',
            'shift_leader': 'Ca Trưởng',
            'am_sau_say_1_pct': 'Ẩm sau sấy 1 (%)',
            'am_sau_say_2_pct': 'Ẩm sau sấy 2 (%)',
            'am_vien_pct': 'Ẩm viên (%)',
            'do_tro_pct': 'Độ tro (%)'
        }, inplace=True)
        st.dataframe(df_kcs_disp, hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu kiểm nghiệm KCS.")

# ----------------- TAB 9: QUẢN LÝ DẦU DIEZEN -----------------
elif task_num == 9:
    st.markdown('<div class="section-title">⛽ Hệ Thống Quản Lý Cấp Phát & Tiêu Hao Dầu Diezen</div>', unsafe_allow_html=True)
    st.caption("Dữ liệu theo dõi cấp phát và tiêu hao nhiên liệu dầu Diezen phục vụ xe cơ giới & vận hành nhà máy.")
    
    if not df_diezen.empty:
        total_dz_all = float(df_diezen['tong_diezen_lit'].sum()) if 'tong_diezen_lit' in df_diezen.columns else 0.0
        latest_dz_row = df_diezen.iloc[-1]
        latest_dz_vol = float(latest_dz_row.get('tong_diezen_lit', 0.0))
        latest_w_label = latest_dz_row.get('week_label', 'Tuần gần nhất')

        c_dz1, c_dz2, c_dz3 = st.columns(3)
        c_dz1.metric("Tổng Dầu Diezen Đã Cấp", f"{total_dz_all:,.0f} Lít", f"Toàn bộ {len(df_diezen)} kỳ theo dõi")
        c_dz2.metric(f"Tiêu Thụ {latest_w_label}", f"{latest_dz_vol:,.0f} Lít", "Kỳ báo cáo mới nhất")
        avg_dz = total_dz_all / len(df_diezen) if len(df_diezen) > 0 else 0.0
        c_dz3.metric("Mức Tiêu Thụ Trung Bình", f"{avg_dz:,.0f} Lít/kỳ", "Định mức theo dõi")

        st.markdown("---")
        col_dz_left, col_dz_right = st.columns([1, 1])
        with col_dz_left:
            latest_dz = latest_dz_row.to_dict()
            vehicles = [k for k in latest_dz.keys() if k not in ['month', 'week', 'week_label', 'tong_diezen_lit', 'date_str'] and isinstance(latest_dz[k], (int, float)) and latest_dz[k] > 0]
            if vehicles:
                dz_breakdown = [{'Thiết bị / Phương tiện': v, 'Nhiên liệu (Lít)': latest_dz[v]} for v in vehicles]
                df_dz_pie = pd.DataFrame(dz_breakdown)
                fig_dz = px.pie(
                    df_dz_pie,
                    names='Thiết bị / Phương tiện',
                    values='Nhiên liệu (Lít)',
                    title=f"Cơ Cấu Phân Bổ Dầu Theo Phương Tiện - {latest_w_label}",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_dz.update_traces(textinfo='percent+label')
                fig_dz.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_dz, use_container_width=True)

        with col_dz_right:
            if 'week_label' in df_diezen.columns and 'tong_diezen_lit' in df_diezen.columns:
                fig_dz_bar = px.bar(
                    df_diezen.tail(12),
                    x='week_label',
                    y='tong_diezen_lit',
                    text='tong_diezen_lit',
                    title="Diễn Biến Cấp Phát Dầu Diezen Qua Các Tuần (Lít)",
                    color_discrete_sequence=['#f59e0b']
                )
                fig_dz_bar.update_traces(texttemplate='%{text:,.0f}L', textposition='outside')
                fig_dz_bar.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20), xaxis_title="Tuần", yaxis_title="Lít")
                st.plotly_chart(fig_dz_bar, use_container_width=True)

        st.markdown("##### 📋 Bảng Chi Tiết Cấp Phát & Tiêu Hao Dầu Diezen")
        st.dataframe(df_diezen, hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu dầu Diezen.")

# ----------------- TAB 10: HIỆU SUẤT CA TRƯỞNG -----------------
elif task_num == 10:
    st.markdown('<div class="section-title">🏆 So Sánh Hiệu Suất Sản Xuất Theo Ca Trưởng</div>', unsafe_allow_html=True)
    df_leaders = get_shift_leader_kpis(df_shifts)
    
    if not df_leaders.empty:
        st.dataframe(df_leaders, use_container_width=True, hide_index=True)

        col_ld1, col_ld2 = st.columns(2)
        with col_ld1:
            fig_ld_output = px.bar(
                df_leaders,
                x='Ca Trưởng',
                y='Tổng sản lượng (tấn)',
                text='Tổng sản lượng (tấn)',
                color='Ca Trưởng',
                title="Tổng Sản Lượng Lũy Kế Theo Ca Trưởng (Tấn)"
            )
            fig_ld_output.update_traces(texttemplate='%{text:,.0f}t', textposition='outside')
            fig_ld_output.update_layout(height=340, showlegend=False)
            st.plotly_chart(fig_ld_output, use_container_width=True)

        with col_ld2:
            fig_ld_elec = px.bar(
                df_leaders,
                x='Ca Trưởng',
                y='Điện năng TB (kWh/tấn)',
                text='Điện năng TB (kWh/tấn)',
                color='Điện năng TB (kWh/tấn)',
                color_continuous_scale='RdYlGn_r',
                title="Suất Điện Trung Bình Theo Ca Trưởng (kWh/tấn - Càng Thấp Càng Tốt)"
            )
            fig_ld_elec.add_hline(y=175, line_dash="dash", line_color="red", annotation_text="Trần 175")
            fig_ld_elec.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_ld_elec.update_layout(height=340)
            st.plotly_chart(fig_ld_elec, use_container_width=True)

# ----------------- TAB 11: SƠ ĐỒ CƠ CẤU NHÂN SỰ -----------------
elif task_num == 11:
    render_organization_chart(app_loader)

# ----------------- TAB 12: QUY TRÌNH CHẾ BIẾN & KỸ THUẬT -----------------
elif task_num == 12:
    render_wood_pellet_process_and_die_conditioning(app_loader, process_data)

# ----------------- TAB 13: SƠ ĐỒ NGUYÊN LÝ NHÀ MÁY -----------------
elif task_num == 13:
    render_factory_schematic_diagram()

# ----------------- TAB 14: NHẬP BÁO CÁO CA & KCS TRỰC TIẾP -----------------
elif task_num == 14:
    if app_loader is None:
        app_loader = DataLoader()
    render_data_entry_module(app_loader)

# Footer
st.markdown("---")
st.caption(f"Hệ Thống Báo Cáo Sản Xuất Tự Động Viên Nén Gỗ | Dữ liệu cập nhật thời gian thực từ Google Sheets | Phiên bản 1.0")

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
    AUTHORIZED_VIEWER_EMAIL,
    check_tab_permission,
    render_permission_denied_card,
    render_shift_production_form,
    render_login_box
)
from i18n import (
    get_lang, set_lang, apply_language_change, is_en, t, translate_eval, strip_accents, format_person_name,
    translate_comparison_df, translate_wm_weekly, translate_wm_monthly, translate_shift_leader_kpis,
    get_op_tasks, get_static_tasks, get_entry_tasks, get_all_tasks,
    map_task_name, get_time_modes, map_time_mode,
    get_dashboard_choices, map_dashboard_choice,
    OP_TASKS_VI, OP_TASKS_EN, STATIC_TASKS_VI, STATIC_TASKS_EN,
    ENTRY_TASKS_VI, ENTRY_TASKS_EN, TIME_MODES_VI, TIME_MODES_EN
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

from data_loader import DataLoader, DEFAULT_SHIFT_COLUMNS, match_shift_leader, POSITION_DIRECTORY, parse_vn_date
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

@st.cache_data(ttl=60)
def load_all_factory_data():
    """Tải và lưu đệm dữ liệu từ các Google Sheets trong 60 giây (tự động làm mới sau mỗi 1 phút)"""
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
    tpm_data = loader.load_tpm_improvements()
    grease_data = loader.load_pm30_grease_data()

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
        'tpm_data': tpm_data,
        'grease_data': grease_data,
        'process_data': process_data,
        'oil_change_data': oil_change_data,
        'loader': loader,
        'prod_title': loader.spreadsheet.title if loader.spreadsheet else "2026 BVN QB Nhật kí sản xuất",
        'kpi_title': loader.kpi_spreadsheet.title if loader.kpi_spreadsheet else "2026 Nhat ky KPI",
        'maint_log_title': loader.maint_log_spreadsheet.title if loader.maint_log_spreadsheet else "Maninternance BVNQB",
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
        tpm_data = data.get('tpm_data', {'summary': {}, 'tasks': pd.DataFrame()})
        grease_data = data.get('grease_data', pd.DataFrame())
        process_data = data.get('process_data', {})
        oil_change_data = data.get('oil_change_data', {'summary': pd.DataFrame(), 'details': {}, 'title': "Lịch thay nhớt hộp số máy ép"})
        app_loader = data.get('loader', None)
        sheet_title = data['prod_title']
        kpi_sheet_title = data['kpi_title']
        maint_log_title = data.get('maint_log_title', "Maninternance BVNQB")
        maint_plan_title = data.get('maint_plan_title', "Mainternance BVN QB")
        oil_title = data.get('oil_title', "Lịch thay nhớt hộp số máy ép")
except Exception as e:
    st.error(f"❌ Không thể kết nối tới Google Sheets: {e}")
    st.info("Vui lòng kiểm tra file `credentials.json` và phân quyền chia sẻ bảng tính.")
    st.stop()


# ==============================================================================
# BỘ CÔNG CỤ TÌM KIẾM & TRA CỨU TÙY BIẾN TOÀN HỆ THỐNG (UNIVERSAL SEARCH ENGINE)
# ==============================================================================
def search_df(df: pd.DataFrame, query: str, search_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Tìm kiếm nhanh không phân biệt hoa/thường và không phân biệt dấu tiếng Việt trên DataFrame.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty or not query:
        return df
    q_str = str(query).strip().lower()
    if not q_str:
        return df
    q_no = strip_accents(q_str).lower()

    target_cols = [c for c in (search_cols or list(df.columns)) if c in df.columns]
    if not target_cols:
        return df
    try:
        row_text = df[target_cols[0]].fillna('').astype(str)
        for c in target_cols[1:]:
            row_text = row_text + " " + df[c].fillna('').astype(str)
        row_text = row_text.str.lower()
        row_text_no = row_text.apply(strip_accents).str.lower()
        mask = row_text.str.contains(q_str, regex=False, na=False) | row_text_no.str.contains(q_no, regex=False, na=False)
        return df[mask]
    except Exception:
        return df


def search_shifts_df(df_shifts: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Tìm kiếm thông minh trên bảng ca sản xuất: hỗ trợ tìm theo ngày, ca trưởng,
    ghi chú hoặc theo mã thiết bị (nếu người dùng gõ PE1, DR124... sẽ lọc ca máy đó vận hành).
    """
    if df_shifts is None or not isinstance(df_shifts, pd.DataFrame) or df_shifts.empty or not query:
        return df_shifts
    q_str = str(query).strip().lower()
    if not q_str:
        return df_shifts
    q_no = strip_accents(q_str).lower()

    try:
        str_cols = [c for c in ['date_str', 'shift_leader', 'week', 'month', 'date'] if c in df_shifts.columns]
        if not str_cols:
            str_cols = list(df_shifts.columns)
        row_text = df_shifts[str_cols[0]].fillna('').astype(str)
        for c in str_cols[1:]:
            row_text = row_text + " " + df_shifts[c].fillna('').astype(str)
        row_text = row_text.str.lower()
        row_text_no = row_text.apply(strip_accents).str.lower()
        mask = row_text.str.contains(q_str, regex=False, na=False) | row_text_no.str.contains(q_no, regex=False, na=False)

        q_upper = query.strip().upper()
        if f"h_{q_upper}" in df_shifts.columns:
            mask = mask | (df_shifts[f"h_{q_upper}"] > 0)
        elif q_upper in df_shifts.columns:
            mask = mask | (df_shifts[q_upper] > 0)

        # 3. Tìm theo tên ca trưởng (Sắc -> Ca A, Tài -> Ca B, Long -> Ca C)
        if 'shift_leader' in df_shifts.columns:
            if any(k in q_no for k in ['sac', 'ca a', 'hai']):
                mask = mask | df_shifts['shift_leader'].apply(lambda val: match_shift_leader(val, 'Ca A'))
            elif any(k in q_no for k in ['tai', 'ca b', 'lam']):
                mask = mask | df_shifts['shift_leader'].apply(lambda val: match_shift_leader(val, 'Ca B'))
            elif any(k in q_no for k in ['long', 'ca c']):
                mask = mask | df_shifts['shift_leader'].apply(lambda val: match_shift_leader(val, 'Ca C'))

        return df_shifts[mask]
    except Exception:
        return df_shifts


def universal_system_search(query: str, data_dict: dict) -> dict:
    """
    Tra cứu thông tin tùy biến trên toàn bộ các nguồn dữ liệu:
    - Sự Cố Kỹ Thuật (df_incidents)
    - Nhật Ký Bảo Trì (df_maint_log)
    - Ca Sản Xuất (df_shifts)
    - Đánh Giá Điểm KPI Tuần / Tháng (wm_weekly, wm_monthly)
    - TPM & Cải Tiến Thiết Bị (tpm_data['tasks'])
    - Kiểm Định Mỡ Máy Ép PM30-6 (grease_data)
    - Lịch Thay Nhớt PE1-PE8 (oil_change_data)
    - Kiểm Định Chất Lượng KCS (df_kcs)
    """
    if not query or not str(query).strip():
        return {}

    q = str(query).strip()
    q_no = strip_accents(q.lower())

    df_inc = data_dict.get('incidents', pd.DataFrame())
    df_ml = data_dict.get('maint_log', pd.DataFrame())
    df_sh = data_dict.get('shifts', pd.DataFrame())
    df_kpi_w = data_dict.get('wm_weekly', pd.DataFrame())
    df_kpi_m = data_dict.get('wm_monthly', pd.DataFrame())
    tpm_info = data_dict.get('tpm_data', {})
    df_tpm = tpm_info.get('tasks', pd.DataFrame()) if isinstance(tpm_info, dict) else pd.DataFrame()
    df_gr = data_dict.get('grease_data', pd.DataFrame())
    oil_info = data_dict.get('oil_change_data', {})
    df_oil = oil_info.get('summary', pd.DataFrame()) if isinstance(oil_info, dict) else pd.DataFrame()
    df_kcs = data_dict.get('kcs', pd.DataFrame())

    res_inc = search_df(df_inc, q)
    res_ml = search_df(df_ml, q)
    res_sh = search_shifts_df(df_sh, q)
    res_tpm = search_df(df_tpm, q)
    res_gr = search_df(df_gr, q)
    res_oil = search_df(df_oil, q)
    res_kcs = search_df(df_kcs, q)

    # Tra cứu KPI: nếu gõ 'kpi' hoặc liên quan điểm số/đánh giá
    if 'kpi' in q_no or 'danh gia' in q_no or 'diem' in q_no:
        res_kpi_w = df_kpi_w.copy() if not df_kpi_w.empty else pd.DataFrame()
        res_kpi_m = df_kpi_m.copy() if not df_kpi_m.empty else pd.DataFrame()
    else:
        res_kpi_w = search_df(df_kpi_w, q)
        res_kpi_m = search_df(df_kpi_m, q)

    total_matches = (
        len(res_inc) + len(res_ml) + len(res_sh) + 
        len(res_tpm) + len(res_gr) + len(res_oil) + 
        len(res_kcs) + len(res_kpi_w) + len(res_kpi_m)
    )

    return {
        'query': q,
        'total': total_matches,
        'incidents': res_inc,
        'maint_log': res_ml,
        'shifts': res_sh,
        'tpm': res_tpm,
        'grease': res_gr,
        'oil': res_oil,
        'kcs': res_kcs,
        'kpi_w': res_kpi_w,
        'kpi_m': res_kpi_m
    }


def reset_global_search():
    """
    Callback xóa an toàn ô tìm kiếm (chạy ở đầu chu kỳ rerun Streamlit, tránh StreamlitWidgetAlreadyInstantiatedError).
    """
    st.session_state['global_search_input_widget'] = ""
    st.session_state['global_search_kw'] = ""


def render_universal_search_panel(search_res: dict):
    """
    Hiển thị giao diện tổng hợp kết quả tìm kiếm tùy biến đa nguồn trực quan và tiện dụng.
    """
    if not search_res:
        return

    q = search_res.get('query', '')
    total = search_res.get('total', 0)

    hdr_title = t(f'KẾT QUẢ TÌM KIẾM TOÀN BỘ HỆ THỐNG: "{q}"', f'SYSTEM-WIDE SEARCH RESULTS: "{q}"')
    sub_title = t(f"Đã quét qua 6 cơ sở dữ liệu • Tìm thấy <b>{total:,}</b> kết quả phù hợp", f"Scanned 6 databases • Found <b>{total:,}</b> matching records")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 2px solid #0284c7; border-radius: 12px; padding: 12px 18px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 4px 18px rgba(2,132,199,0.22);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🔍</span>
                <div>
                    <div style="font-size: 15px; font-weight: 800; color: #ffffff;">
                        {hdr_title}
                    </div>
                    <div style="font-size: 12px; color: #38bdf8; font-weight: 600; margin-top: 2px;">
                        {sub_title}
                    </div>
                </div>
            </div>
            <div>
                <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #0284c7; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;">
                    {total} {t("KẾT QUẢ", "RESULTS")}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total == 0:
        st.warning(t(
            f"⚠️ Không tìm thấy bản ghi nào khớp với từ khóa **'{q}'**. Vui lòng kiểm tra lại hoặc thử với mã thiết bị (`PE1`, `HM118`), tên ca trưởng (`Sắc`, `Tài`, `Long`), sự cố (`bạc đạn`, `cháy`, `kẹt`), ngày làm việc...",
            f"⚠️ No records found matching **'{q}'**. Please try machine code (`PE1`, `HM118`), leader name (`Sac`, `Tai`, `Long`), issue (`bearing`, `jam`), or date..."
        ))
        st.button(
            t("✖ Đóng & Xóa Tìm Kiếm", "✖ Close & Clear Search"),
            key="btn_clear_search_empty",
            on_click=reset_global_search,
            use_container_width=True
        )
        return

    # Metric Badges
    res_inc = search_res.get('incidents', pd.DataFrame())
    res_ml = search_res.get('maint_log', pd.DataFrame())
    res_sh = search_res.get('shifts', pd.DataFrame())
    res_tpm = search_res.get('tpm', pd.DataFrame())
    res_gr = search_res.get('grease', pd.DataFrame())
    res_oil = search_res.get('oil', pd.DataFrame())
    res_kcs = search_res.get('kcs', pd.DataFrame())
    res_kpi_w = search_res.get('kpi_w', pd.DataFrame())
    res_kpi_m = search_res.get('kpi_m', pd.DataFrame())
    total_kpi = len(res_kpi_w) + len(res_kpi_m)

    c_m1, c_m2, c_m3, c_m4, c_m5, c_m6 = st.columns(6)
    c_m1.metric(t("🚨 Sự Cố", "🚨 Incidents"), f"{len(res_inc):,} " + t("vụ", "cases"))
    c_m2.metric(t("🔧 Bảo Trì", "🔧 Maintenance"), f"{len(res_ml):,} " + t("lượt", "jobs"))
    c_m3.metric(t("📋 Ca Sản Xuất", "📋 Prod Shifts"), f"{len(res_sh):,} " + t("ca", "shifts"))
    c_m4.metric(t("🎯 Đánh Giá KPI", "🎯 KPI Scores"), f"{total_kpi:,} " + t("kỳ", "periods"))
    c_m5.metric(t("🚀 Cải Tiến TPM", "🚀 TPM Items"), f"{len(res_tpm):,} " + t("việc", "tasks"))
    c_m6.metric(t("🛢️ Bôi Trơn", "🛢️ Lubrication"), f"{len(res_gr) + len(res_oil):,} " + t("lần", "times"))

    # Tabs chi tiết
    with st.expander(t("📋 BẤM ĐỂ XEM / THU GỌN DANH SÁCH CHI TIẾT CÁC BẢN GHI TÌM ĐƯỢC", "📋 CLICK TO EXPAND / COLLAPSE DETAILED MATCHING RECORDS"), expanded=True):
        st_tabs = st.tabs([
            f"🚨 {t('Sự Cố', 'Incidents')} ({len(res_inc)})",
            f"🔧 {t('Bảo Trì', 'Maintenance')} ({len(res_ml)})",
            f"📋 {t('Ca Sản Xuất', 'Shifts')} ({len(res_sh)})",
            f"🎯 {t('Đánh Giá KPI', 'KPI Scores')} ({total_kpi})",
            f"🚀 {t('TPM & Cải Tiến', 'TPM')} ({len(res_tpm)})",
            f"🛢️ {t('Bôi Trơn', 'Lubrication')} ({len(res_gr) + len(res_oil)})",
            f"🔬 {t('KCS', 'QC')} ({len(res_kcs)})"
        ])

        with st_tabs[0]:
            if not res_inc.empty:
                cols_inc = ['id_su_co', 'date_str', 'shift_leader', 'equipment_raw', 'description', 'solution', 'performer', 'duration_hours', 'status']
                avail_cols = [c for c in cols_inc if c in res_inc.columns]
                st.dataframe(res_inc[avail_cols], hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có sự cố nào khớp với từ khóa.", "No incidents matching keyword."))

        with st_tabs[1]:
            if not res_ml.empty:
                cols_ml = ['id', 'date', 'equipment', 'activity', 'description', 'duration_hours', 'performer', 'status']
                avail_cols = [c for c in cols_ml if c in res_ml.columns]
                st.dataframe(res_ml[avail_cols], hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có bản ghi bảo trì nào khớp với từ khóa.", "No maintenance records matching keyword."))

        with st_tabs[2]:
            if not res_sh.empty:
                cols_sh = ['date_str', 'shift_leader', 'san_luong_tan', 'tong_gio_ep', 'nang_suat_tph', 'dien_kwh', 'dien_tb_kwh_tan', 'ton_kho_tan']
                avail_cols = [c for c in cols_sh if c in res_sh.columns]
                st.dataframe(res_sh[avail_cols], hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có ca sản xuất nào khớp với từ khóa.", "No production shifts matching keyword."))

        with st_tabs[3]:
            if total_kpi > 0:
                if not res_kpi_w.empty:
                    st.markdown(f"**{t('Điểm KPI Theo Tuần (34 tuần gần nhất):', 'Weekly KPI Scores:')}**")
                    st.dataframe(res_kpi_w, hide_index=True, use_container_width=True)
                if not res_kpi_m.empty:
                    st.markdown(f"**{t('Điểm KPI Theo Tháng:', 'Monthly KPI Scores:')}**")
                    st.dataframe(res_kpi_m, hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có dữ liệu KPI nào khớp với từ khóa.", "No KPI records matching keyword."))

        with st_tabs[4]:
            if not res_tpm.empty:
                cols_tpm = ['id', 'category', 'description', 'location', 'assignee', 'priority', 'status', 'start_date', 'due_date']
                avail_cols = [c for c in cols_tpm if c in res_tpm.columns]
                st.dataframe(res_tpm[avail_cols], hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có mục TPM nào khớp với từ khóa.", "No TPM items matching keyword."))

        with st_tabs[5]:
            if not res_gr.empty:
                st.markdown(f"**{t('Kiểm Định Mỡ Máy Ép PM30-6 (Google Sheet):', 'PM30-6 Grease Dosing:')}**")
                st.dataframe(res_gr.head(50), hide_index=True, use_container_width=True)
            if not res_oil.empty:
                st.markdown(f"**{t('Lịch Thay Nhớt Hộp Số PE1-PE8:', 'PE1-PE8 Oil Change Schedule:')}**")
                st.dataframe(res_oil, hide_index=True, use_container_width=True)
            if res_gr.empty and res_oil.empty:
                st.info(t("Không có dữ liệu bôi trơn nào khớp với từ khóa.", "No lubrication records matching keyword."))

        with st_tabs[6]:
            if not res_kcs.empty:
                st.dataframe(res_kcs.head(50), hide_index=True, use_container_width=True)
            else:
                st.info(t("Không có dữ liệu KCS nào khớp với từ khóa.", "No QC records matching keyword."))

    col_btn_c1, col_btn_c2 = st.columns([3, 1])
    with col_btn_c2:
        st.button(
            t("✖ Tắt Chế Độ Tìm Kiếm & Hiển Thị Đầy Đủ", "✖ Exit Search Mode & Show All"),
            key="btn_exit_search_panel",
            on_click=reset_global_search,
            type="secondary",
            use_container_width=True
        )


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

# ================= DANH MỤC CỬA SỔ TÁC VỤ (PHÂN 3 NHÓM - SONG NGỮ VI / EN) =================
curr_lang = get_lang()
OP_TASKS = get_op_tasks(curr_lang)
STATIC_TASKS = get_static_tasks(curr_lang)
ENTRY_TASKS = get_entry_tasks(curr_lang)
TASK_LIST = OP_TASKS + STATIC_TASKS + ENTRY_TASKS

if 'active_task' not in st.session_state:
    st.session_state['active_task'] = OP_TASKS[0]
else:
    # Luôn đồng bộ tên tác vụ khớp với ngôn ngữ đang chọn
    st.session_state['active_task'] = map_task_name(st.session_state['active_task'], curr_lang)

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
        <div style="text-align: center; margin-bottom: 10px;">
            <div style="font-size: 24px; font-weight: 800; letter-spacing: 2px; color: #16a34a; line-height: 1.2;">PRODUCTION</div>
            <div style="font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px;">{t("BVN Quảng Bình", "BVN Quang Binh")}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.title("PRODUCTION")
        st.caption(t("BVN Quảng Bình", "BVN Quang Binh"))

    # 🌐 CHUYỂN ĐỔI SONG NGỮ (VIỆT - ANH)
    def on_lang_change():
        chosen_val = st.session_state.get('lang_radio_select', '')
        new_lang = 'en' if 'English' in chosen_val else 'vi'
        if new_lang != get_lang():
            apply_language_change(new_lang)

    st.radio(
        "🌐 Ngôn ngữ / Language:",
        ["🇻🇳 Tiếng Việt", "🇬🇧 English"],
        index=0 if curr_lang == 'vi' else 1,
        horizontal=True,
        key="lang_radio_select",
        on_change=on_lang_change
    )

    with st.expander(t("🟢 6/6 Google Sheets Tích Hợp", "🟢 6/6 Connected Google Sheets"), expanded=False):
        st.markdown(f"📗 **{t('Sản xuất:', 'Production:')}** `{sheet_title}`")
        st.markdown(f"🎯 **{t('Đánh giá KPI:', 'KPI Assessment:')}** `{kpi_sheet_title}`")
        st.markdown(f"🔧 **{t('Nhật ký bảo trì:', 'Maintenance Log:')}** `{maint_log_title}`")
        st.markdown(f"🛠️ **{t('Kế hoạch & 4M:', '4M & Maintenance Plan:')}** `{maint_plan_title}`")
        st.markdown(f"🌲 **{t('Quy trình chế biến:', 'Processing Workflow:')}** `1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw`")
        st.markdown(f"🛢️ **{t('Lịch thay nhớt PE1-PE8:', 'PE1-PE8 Lubrication:')}** `{oil_title}`")
    
    if st.button(t("🔄 Làm Mới Dữ Liệu (Refresh)", "🔄 Refresh Data"), key="sidebar_manual_refresh_btn", use_container_width=True, help=t("Xóa bộ nhớ đệm và tải lại dữ liệu mới nhất từ Google Sheets", "Clear cache and reload latest data from Google Sheets")):
        st.cache_data.clear()
        if 'hr_data' in st.session_state:
            del st.session_state['hr_data']
        st.rerun()

    # Hiển thị thông tin người xem hoặc Admin được cấp quyền
    v_auth = st.session_state.get("viewer_authorized_email")
    if v_auth == "admin":
        st.markdown(f"""
        <div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #eab308; border-radius: 8px; padding: 6px 10px; margin-top: 8px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 11px; font-weight: 700; color: #facc15;">
                <span>👑</span>
                <span>{t("QUẢN TRỊ VIÊN (ADMIN)", "ADMINISTRATOR")}</span>
            </div>
            <span style="background: #ca8a04; color: white; padding: 1px 6px; border-radius: 4px; font-size: 9px; font-weight: 700;">{t("TOÀN QUYỀN", "ALL ACCESS")}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("🔒 Khóa Lại (Đăng Xuất)", "🔒 Logout"), key="btn_logout_viewer", use_container_width=True):
            logout_viewer()
    elif v_auth == AUTHORIZED_VIEWER_EMAIL:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid #0284c7; border-radius: 8px; padding: 6px 10px; margin-top: 8px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 11px; font-weight: 700; color: #38bdf8;">
                <span>👤</span>
                <span>{AUTHORIZED_VIEWER_EMAIL}</span>
            </div>
            <span style="background: #0284c7; color: white; padding: 1px 6px; border-radius: 4px; font-size: 9px; font-weight: 700;">{t("QUYỀN XEM", "VIEW ONLY")}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("🔒 Khóa Lại (Đăng Xuất)", "🔒 Logout"), key="btn_logout_viewer", use_container_width=True):
            logout_viewer()

    st.markdown("---")
    st.subheader(t("🔍 Tra Cứu & Tìm Kiếm Tùy Biến", "🔍 Quick & Custom Search"))
    global_search_raw = st.text_input(
        t("Nhập từ khóa tìm kiếm:", "Enter search keyword:"),
        placeholder=t("Thiết bị, sự cố, người, ngày, lỗi...", "Machine, incident, staff, date, issue..."),
        key="global_search_input_widget",
        help=t("Nhập bất kỳ thông tin nào (mã máy PE1, DR124, tên người, sự cố, linh kiện, ngày...) để tra cứu tức thì trên toàn hệ thống.",
               "Enter any search keyword (machine code, person, incident, parts, date...) to search across the entire system.")
    )
    global_search_kw = (global_search_raw or "").strip()
    st.session_state['global_search_kw'] = global_search_kw

    if global_search_kw:
        col_c1, col_c2 = st.columns([3, 2])
        with col_c1:
            lbl_searching = t('Đang tìm:', 'Searching:')
            st.markdown(f"<div style='font-size: 11px; color: #38bdf8; font-weight: 700; margin-top: 6px;'>🔎 {lbl_searching} <span style='color: #facc15;'>&quot;{global_search_kw}&quot;</span></div>", unsafe_allow_html=True)
        with col_c2:
            st.button(
                t("✖ Xóa lọc", "✖ Clear"),
                key="btn_clear_sb_search",
                on_click=reset_global_search,
                use_container_width=True
            )

    st.markdown("---")
    st.subheader(t("👤 Lọc Ca Trưởng", "👤 Filter Shift Leader"))
    all_ldr_lbl = t("Tất cả", "All")
    available_leaders = [
        all_ldr_lbl,
        "Ca A (Sắc)",
        "Ca B (Tài)",
        "Ca C (Long)",
        "BT-VS (Bảo trì)",
        "OFF (Nghỉ ca)"
    ]
    selected_leader = st.selectbox(
        t("Ca Trưởng:", "Shift Leader:"),
        available_leaders,
        index=0,
        format_func=lambda x: (strip_accents(x) if is_en() else x)
    )

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
    st.markdown(f"""
    <div style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; border: 1px solid #334155; border-left: 4px solid #38bdf8; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
            <span>📊</span>
            <span>{t("VẬN HÀNH & KPI", "OPERATIONS & KPI")}</span>
        </div>
        <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">{t("10 MỤC", "10 ITEMS")}</span>
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
    st.markdown(f"""
    <div style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-top: 12px; margin-bottom: 6px; border: 1px solid #334155; border-left: 4px solid #a78bfa; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
            <span>📘</span>
            <span>{t("QUY TRÌNH & SƠ ĐỒ", "WORKFLOWS & SCHEMATICS")}</span>
        </div>
        <span style="background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; white-space: nowrap;">{t("3 MỤC", "3 ITEMS")}</span>
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
            <span>{t("NHẬP SỐ LIỆU", "DATA ENTRY")}</span>
        </div>
        {user_status_badge}
    </div>
    """, unsafe_allow_html=True)

    cur_task = st.session_state.get('active_task', OP_TASKS[0])
    is_entry_active = (cur_task == ENTRY_TASKS[0])
    btn_text = f"👉 📝 14. {t('Nhập Số Liệu', 'Data Entry')} 🟢" if is_entry_active else f"📝 14. {t('Nhập Số Liệu', 'Data Entry')}"
    if st.button(
        btn_text,
        key="sidebar_entry_button",
        use_container_width=True,
        type="primary" if is_entry_active else "secondary"
    ):
        st.session_state['active_task'] = ENTRY_TASKS[0]
        st.rerun()

    st.markdown("---")
    with st.expander(t("📌 **ĐỊNH MỨC & TIÊU CHUẨN KỸ THUẬT**", "📌 **TECHNICAL SPECS & STANDARDS**"), expanded=False):
        if is_en():
            st.markdown("""
            **⚙️ Section 1: Technical Benchmarks:**
            - Specific Power Consumption: `170 - 175 kWh/ton`
            - Pellet Mill Output Rate: `≥ 4.0 ton/h`
            - Whole Plant Throughput: `≥ 30.0 ton/h`
            - Overall Equipment Effectiveness (OEE): `≥ 85%`

            **🌲 Section 2: Wood Pellet Quality (ISO 17225-2 / ENplus):**
            - Moisture Content: `8.0 - 9.5%`
            - Ash Content: `≤ 1.5%`
            - Bulk Density: `≥ 600 kg/m³`
            - Mechanical Durability (DU): `≥ 97.5%`
            - Calorific Value: `≥ 4,000 kcal/kg`
            - Fines Content: `≤ 1.0%`
            - Pellet Diameter: `6 - 8 mm`
            """)
        else:
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


# ================= BỘ LỌC THỜI GIAN ĐẦU TRANG =================

# Xác định ngày có dữ liệu gần nhất và danh sách các ngày
max_date = df_shifts['date'].max() if ('date' in df_shifts.columns and not df_shifts.empty) else datetime.now()
min_date = df_shifts['date'].min() if ('date' in df_shifts.columns and not df_shifts.empty) else (datetime.now() - timedelta(days=30))

# Khởi tạo trạng thái bộ lọc trong st.session_state nếu chưa có
if 'top_view_mode' not in st.session_state:
    st.session_state['top_view_mode'] = t("☀️ Theo Ngày", "☀️ Daily")
if 'top_target_date' not in st.session_state:
    st.session_state['top_target_date'] = max_date.date()

# Hàm trợ giúp làm sạch chuỗi HTML (tránh markdown hiểu nhầm 4 khoảng trắng là code block)
def clean_html(raw_html: str) -> str:
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

# Danh sách chuẩn các chế độ lọc thời gian: Ngày / Tuần / Tháng / Năm / Khoảng ngày
time_modes = get_time_modes(curr_lang)

curr_mode = st.session_state.get('top_view_mode', time_modes[0])
curr_mode = map_time_mode(curr_mode, curr_lang)
st.session_state['top_view_mode'] = curr_mode
try:
    default_idx = time_modes.index(curr_mode)
except ValueError:
    default_idx = 0

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

# ================= BỘ LỌC THỜI GIAN SẢN XUẤT & NÚT LÀM MỚI ĐẦU TRANG =================
col_top_filter_title, col_top_refresh = st.columns([7, 3])
with col_top_filter_title:
    st.markdown(f"""<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-left: 5px solid #38bdf8; border-radius: 10px; padding: 10px 16px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="font-size: 14px; font-weight: 800; color: #ffffff; letter-spacing: 0.3px; display: flex; align-items: center; justify-content: space-between;">
    <span>{t("📅 BỘ LỌC THỜI GIAN", "📅 TIME FILTER")}</span>
    <span style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">{t("NGÀY / TUẦN / THÁNG / NĂM", "DAY / WEEK / MONTH / YEAR")}</span>
    </div>
    </div>""", unsafe_allow_html=True)
with col_top_refresh:
    if st.button(
        t("🔄 Làm Mới Dữ Liệu", "🔄 Refresh Data"),
        key="top_manual_refresh_btn",
        use_container_width=True,
        type="primary",
        help=t("Xóa bộ nhớ đệm và tải lại số liệu mới nhất từ Google Sheets ngay lập tức (dành cho điện thoại & máy tính)", "Clear cache and reload latest data from Google Sheets immediately (for mobile & desktop)")
    ):
        st.cache_data.clear()
        if 'hr_data' in st.session_state:
            del st.session_state['hr_data']
        st.rerun()

if 'main_view_mode_radio' in st.session_state and st.session_state['main_view_mode_radio'] not in time_modes:
    st.session_state['main_view_mode_radio'] = curr_mode

view_mode = st.radio(
    t("Chọn hình thức lọc:", "Filter Mode:"),
    time_modes,
    index=default_idx,
    horizontal=True,
    key="main_view_mode_radio"
)
st.session_state['top_view_mode'] = view_mode

is_day_mode = ("Ngày" in view_mode or "Daily" in view_mode)
is_week_mode = ("Tuần" in view_mode or "Weekly" in view_mode)
is_month_mode = ("Tháng" in view_mode or "Monthly" in view_mode)
is_year_mode = ("Năm" in view_mode or "Yearly" in view_mode)
is_range_mode = ("Khoảng" in view_mode or "Range" in view_mode)

selected_date = max_date
date_range = (min_date, max_date)
selected_week_sidebar = None
selected_month_sidebar = None
selected_year_sidebar = None

if is_day_mode:
    avail_dates = sorted(df_shifts['date'].dt.date.unique(), reverse=True) if ('date' in df_shifts.columns and not df_shifts.empty) else [max_date.date()]
    default_d = st.session_state.get('top_target_date', max_date.date())
    if default_d not in avail_dates and len(avail_dates) > 0:
        default_d = avail_dates[0]
    picked_date = st.date_input(
        t("Chọn ngày làm việc:", "Select Working Date:"),
        value=default_d,
        min_value=min_date.date(),
        max_value=max_date.date(),
        key="main_date_picker"
    )
    selected_date = datetime.combine(picked_date, datetime.min.time())
    st.session_state['top_target_date'] = picked_date

elif is_week_mode:
    selected_week_sidebar = st.selectbox(t("Chọn tuần trong năm 2026:", "Select Week in 2026:"), ALL_WEEKS_52, index=default_w_idx, key="main_week_select")
    selected_date = None

elif is_month_mode:
    selected_month_sidebar = st.selectbox(t("Chọn tháng trong năm 2026:", "Select Month in 2026:"), ALL_MONTHS_CODE_12, index=default_m_code_idx, key="main_month_select")
    selected_date = None

elif is_year_mode:
    selected_year_sidebar = 2026
    st.selectbox(t("Chọn năm vận hành:", "Select Operating Year:"), [t("Năm 2026 (Toàn bộ 229 ngày làm việc)", "Year 2026 (All 229 operating days)")], index=0, key="main_year_select")
    selected_date = None

elif is_range_mode:
    date_range_input = st.date_input(
        t("Chọn khoảng ngày:", "Select Date Range:"),
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

# Lọc dữ liệu theo ca trưởng nếu có
df_filtered_shifts = df_shifts.copy()
if selected_leader not in ["Tất cả", "All"] and 'shift_leader' in df_filtered_shifts.columns:
    df_filtered_shifts = df_filtered_shifts[df_filtered_shifts['shift_leader'].apply(lambda val: match_shift_leader(val, selected_leader))]

# ================= XỬ LÝ TRA CỨU & TÌM KIẾM TÙY BIẾN TOÀN HỆ THỐNG =================
search_results_data = None
if global_search_kw:
    search_results_data = universal_system_search(global_search_kw, data)
    render_universal_search_panel(search_results_data)

    # Nếu từ khóa có khớp với ca sản xuất, tinh chỉnh bảng df_filtered_shifts
    matched_shifts = search_shifts_df(df_filtered_shifts, global_search_kw)
    if not matched_shifts.empty:
        df_filtered_shifts = matched_shifts

# Tính KPI cho ngày/tuần/tháng/năm được chọn
if is_week_mode and selected_week_sidebar:
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
elif is_month_mode and selected_month_sidebar:
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
    is_single_ldr = (selected_leader not in ["Tất cả", "All"])
    prod_m, maint_m, off_m = classify_shift_counts(m_shifts, num_days=num_days_m, is_single_leader=is_single_ldr)
    ton_kho_m = get_inventory_for_period(df_shifts, m_shifts['date'].max() if not m_shifts.empty else None, m_shifts)
    tot_xuat_m = float(m_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in m_shifts.columns else 0.0

    kpis = {
        'date_str': f"{t('Tháng', 'Month')} {selected_month_sidebar}",
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
elif is_year_mode:
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
    is_single_ldr = (selected_leader not in ["Tất cả", "All"])
    prod_y, maint_y, off_y = classify_shift_counts(y_shifts, num_days=num_days_y, is_single_leader=is_single_ldr)
    ton_kho_y = get_inventory_for_period(df_shifts, y_shifts['date'].max() if not y_shifts.empty else None, y_shifts)
    tot_xuat_y = float(y_shifts['xuat_hang_tan'].sum()) if 'xuat_hang_tan' in y_shifts.columns else 0.0

    kpis = {
        'date_str': f"{t('Năm', 'Year')} {y_num}",
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
elif is_range_mode and date_range:
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
    is_single_ldr = (selected_leader not in ["Tất cả", "All"])
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
    if selected_leader not in ["Tất cả", "All"] and 'date' in df_filtered_shifts.columns and not df_filtered_shifts.empty and 'date' in kpis:
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
        <span style="color: #94a3b8; font-weight: 600;">⏱️ {t("Trạng thái ca kỳ:", "Shift status:")}</span>
        <code style="background: #0f172a; border: 1px solid #475569; padding: 2px 8px; border-radius: 6px; color: #38bdf8; font-weight: 700; font-family: monospace; font-size: 11.5px;">{sb_date}</code>
        <span style="color: #475569;">|</span>
        <span style="color: #86efac; font-weight: 700; background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">🏭 {sb_prod} {t("ca sản xuất", "prod shifts")} ({pct_prod:.0f}%)</span>
        <span style="color: #fde68a; font-weight: 700; background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">🔧 {sb_maint} {t("ca bảo trì", "maint shifts")} ({pct_maint:.0f}%)</span>
        <span style="color: #cbd5e1; font-weight: 700; background: rgba(148, 163, 184, 0.15); border: 1px solid #94a3b8; padding: 2px 10px; border-radius: 12px; font-size: 11.5px;">☕ {sb_off} {t("ca nghỉ", "idle shifts")} ({pct_off:.0f}%)</span>
        <span style="color: #475569;">|</span>
        <span style="color: #38bdf8; font-weight: 800; background: rgba(14, 165, 233, 0.18); border: 1px solid #0284c7; padding: 2px 12px; border-radius: 12px; font-size: 11.5px; box-shadow: 0 0 10px rgba(56,189,248,0.2); display: inline-flex; align-items: center; gap: 5px;">
            <span>📦</span> <span>{t("Tồn kho viên nén:", "Pellet inventory:")}</span> <strong style="color: #ffffff; font-size: 12.5px;">{sb_ton_kho:,.1f}</strong> <span>{t("tấn", "tons")}</span>
        </span>
    </div>
    <div style="display: flex; align-items: center; gap: 14px; font-size: 12px; color: #94a3b8;">
        <div>📊 <strong>{t("Tổng số:", "Total:")}</strong> <span style="color: #ffffff; font-weight: 700;">{tot_s} {t("ca", "shifts")}</span></div>
        <div>🏢 <strong>{t("Nhà máy:", "Plant:")}</strong> <span style="color: #4ade80; font-weight: 700;">{t("BVN Quảng Bình", "BVN Quang Binh")}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Chuẩn bị chỉ số chất lượng dùng chung
am_val = float(kpis.get('do_am_tb_pct', 0))
moist_eval = kpis.get('moisture_eval', evaluate_moisture(am_val))
ty_trong_val = float(kpis.get('ty_trong_vien', 0))
dens_eval = kpis.get('density_eval', evaluate_density(ty_trong_val))

# Tính toán dữ liệu Dashboard cho cả 3 Ca Trưởng và Toàn Nhà Máy
active_w_num = int(selected_week_sidebar.replace("Tuần ", "").replace("Week ", "")) if is_week_mode and selected_week_sidebar else None
active_m_num = m_num if is_month_mode and selected_month_sidebar else None
active_range = date_range if is_range_mode else None
active_t_date = selected_date if is_day_mode else None
active_y_num = 2026 if is_year_mode else None

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
        delta_txt = t(f"{kpis_data.get('delta_output', 0):+,.1f} t so hôm trước", f"{kpis_data.get('delta_output', 0):+,.1f} t vs yesterday") if kpis_data.get('delta_output', 0) != 0 else t("Hôm nay", "Today")
        st.markdown(render_kpi_card_html(t("Sản Lượng Thực Tế", "Actual Output"), f"{kpis_data.get('total_output', 0):,.1f}", t("Tấn", "Tons"), delta_txt, "badge-info"), unsafe_allow_html=True)
    with r1_c2:
        e_eval = kpis_data.get('electricity_eval', {})
        b_cls = "badge-success" if e_eval.get('status') == 'EXCELLENT' else ("badge-info" if e_eval.get('status') == 'STANDARD' else "badge-danger")
        e_badge = f"{e_eval.get('icon', '')} {translate_eval(e_eval.get('label', ''))}"
        st.markdown(render_kpi_card_html(t("Suất Điện Tiêu Hao", "Specific Power"), f"{kpis_data.get('avg_electricity_kwh_ton', 0):.1f}", "kWh/t", e_badge, b_cls), unsafe_allow_html=True)
    with r1_c3:
        p_eval = kpis_data.get('productivity_eval', {})
        b_cls = "badge-success" if p_eval.get('status') == 'PASS' else "badge-warning"
        p_badge = f"{p_eval.get('icon', '')} {translate_eval(p_eval.get('label', ''))}"
        st.markdown(render_kpi_card_html(t("Năng Suất Ép TB", "Avg Pellet Mill Rate"), f"{kpis_data.get('avg_productivity', 0):.2f}", t("Tấn/h", "Ton/h"), p_badge, b_cls), unsafe_allow_html=True)
    with r1_c4:
        st.markdown(render_kpi_card_html(t("Tổng Giờ Máy Ép", "Total Mill Hours"), f"{kpis_data.get('total_pellet_hours', 0):.1f}", t("Giờ", "Hours"), t("8 Máy Ép Viên", "8 Pellet Mills"), "badge-info"), unsafe_allow_html=True)

    # Hàng 2: Chất Lượng & Tiêu Hao (4 thẻ)
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    with r2_c1:
        a_val = kpis_data.get('do_am_tb_pct', 0)
        m_eval = kpis_data.get('moisture_eval', evaluate_moisture(a_val))
        b_cls = "badge-success" if m_eval.get('status') == 'PASS' else ("badge-warning" if m_eval.get('status') == 'WARN' else "badge-danger")
        m_badge = f"{m_eval.get('icon', '💧')} {translate_eval(m_eval.get('label', t('Chuẩn: 8.0 - 9.5%', 'Std: 8.0 - 9.5%')))}"
        st.markdown(render_kpi_card_html(t("Độ Ẩm TB Viên (Ngày)", "Avg Pellet Moisture"), f"{a_val:.2f}", "%", m_badge, b_cls), unsafe_allow_html=True)
    with r2_c2:
        ty_val = kpis_data.get('ty_trong_vien', 0)
        d_eval = kpis_data.get('density_eval', evaluate_density(ty_val))
        b_cls = "badge-success" if d_eval.get('status') == 'PASS' else ("badge-warning" if d_eval.get('status') == 'WARN' else "badge-info")
        d_badge = f"{d_eval.get('icon', '⚖️')} {translate_eval(d_eval.get('label', t('Chuẩn: ≥ 600 kg/m³', 'Std: ≥ 600 kg/m³')))}"
        st.markdown(render_kpi_card_html(t("Tỷ Trọng Viên Nén", "Bulk Density"), f"{ty_val:,.1f}", "kg/m³", d_badge, b_cls), unsafe_allow_html=True)
    with r2_c3:
        st.markdown(render_kpi_card_html(t("Tỷ Lệ Chế Biến", "Processing Ratio"), f"{kpis_data.get('processing_ratio', 0):.2f}", t("lần", "x"), t("Định mức: 1.8 - 2.1", "Standard: 1.8 - 2.1"), "badge-info"), unsafe_allow_html=True)
    with r2_c4:
        lat_dz = df_weekly_data.iloc[-1]['diezen_lit'] if not df_weekly_data.empty else 0.0
        lat_dz_r = df_weekly_data.iloc[-1]['diezen_tb_lit_tan'] if not df_weekly_data.empty else 0.0
        st.markdown(render_kpi_card_html(t("Dầu Diezen Tiêu Thụ", "Diesel Consumption"), f"{lat_dz_r:.1f}", t("Lít/tấn", "L/ton"), t(f"{lat_dz:,.0f} Lít/tuần", f"{lat_dz:,.0f} L/week"), "badge-info"), unsafe_allow_html=True)

    # Hàng 3: Tồn Kho & Xuất Hàng Kho Thành Phẩm (Kho BVN Quảng Bình)
    tk_val = float(kpis_data.get('ton_kho_tan', 0.0))
    xh_val = float(kpis_data.get('xuat_hang_tan', 0.0))
    r3_c1, r3_c2 = st.columns(2)
    with r3_c1:
        st.markdown(render_kpi_card_html(t("Tồn Kho Viên Nén (Cuối Kỳ)", "Pellet Inventory (End of Period)"), f"{tk_val:,.1f}", t("Tấn", "Tons"), t("📦 Kho Thành Phẩm BVN Quảng Bình", "📦 BVN Quang Binh Finished Warehouse"), "badge-info"), unsafe_allow_html=True)
    with r3_c2:
        xh_badge = t(f"🚛 {xh_val:,.1f} Tấn xuất kho", f"🚛 {xh_val:,.1f} Tons shipped") if xh_val > 0 else t("Chưa phát sinh xuất hàng trong kỳ", "No shipments in period")
        xh_cls = "badge-success" if xh_val > 0 else "badge-info"
        st.markdown(render_kpi_card_html(t("Lũy Kế Xuất Hàng (Trong Kỳ)", "Accumulated Shipments (In Period)"), f"{xh_val:,.1f}", t("Tấn", "Tons"), xh_badge, xh_cls), unsafe_allow_html=True)

    # Cảnh báo nổi bật
    e_eval = kpis_data.get('electricity_eval', {})
    if e_eval.get('status') == 'WARNING':
        st.error(t(
            f"⚠️ **CẢNH BÁO ĐIỆN NĂNG:** Suất tiêu hao điện đạt **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, vượt định mức trần 175 kWh/tấn (+{e_eval.get('diff')} kWh/tấn). Đề nghị kiểm tra phụ tải máy nghiền búa và hệ thống sấy.",
            f"⚠️ **POWER ALERT:** Specific power consumption reached **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/ton**, exceeding the 175 kWh/ton limit (+{e_eval.get('diff')} kWh/ton). Please inspect hammer mill and dryer loads."
        ))
    elif e_eval.get('status') == 'EXCELLENT':
        st.success(t(
            f"✨ **HIỆU QUẢ CAO:** Suất tiêu hao điện chỉ **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, thấp hơn định mức chuẩn 170 kWh/tấn.",
            f"✨ **HIGH EFFICIENCY:** Specific power consumption is only **{kpis_data.get('avg_electricity_kwh_ton'):.1f} kWh/ton**, below the 170 kWh/ton standard."
        ))

    m_eval = kpis_data.get('moisture_eval', evaluate_moisture(kpis_data.get('do_am_tb_pct', 0)))
    if m_eval.get('status') == 'ALERT':
        st.error(t(
            f"💧 **CẢNH BÁO ĐỘ ẨM VIÊN CAO:** Độ ẩm trung bình đạt **{kpis_data.get('do_am_tb_pct', 0):.2f}%**, vượt trần 9.5%. Đề nghị kiểm tra nhiệt độ trống sấy.",
            f"💧 **HIGH MOISTURE ALERT:** Average moisture reached **{kpis_data.get('do_am_tb_pct', 0):.2f}%**, exceeding 9.5% ceiling. Please check rotary dryer temperatures."
        ))
    elif m_eval.get('status') == 'WARN':
        st.warning(t(
            f"💧 **LƯU Ý ĐỘ ẨM VIÊN THẤP:** Độ ẩm trung bình đạt **{kpis_data.get('do_am_tb_pct', 0):.2f}%** (< 8.0%), viên nén có nguy cơ giòn.",
            f"💧 **LOW MOISTURE NOTICE:** Average moisture is **{kpis_data.get('do_am_tb_pct', 0):.2f}%** (< 8.0%), pellets may be brittle."
        ))

    if 0 < kpis_data.get('ty_trong_vien', 0) < DENSITY_BENCHMARK_MIN:
        st.warning(t(
            f"⚖️ **CẢNH BÁO TỶ TRỌNG:** Tỷ trọng viên nén đạt **{kpis_data.get('ty_trong_vien', 0):,.1f} kg/m³**, thấp hơn chuẩn xuất khẩu ({DENSITY_BENCHMARK_MIN:,.0f} kg/m³).",
            f"⚖️ **BULK DENSITY ALERT:** Bulk density reached **{kpis_data.get('ty_trong_vien', 0):,.1f} kg/m³**, below export standard ({DENSITY_BENCHMARK_MIN:,.0f} kg/m³)."
        ))

# Hàm render nội dung thẻ của từng Ca Trưởng chuẩn công nghiệp (Đồng bộ 100% cấu trúc 3 Ca)
def render_leader_card_html(ldr: dict, key: str, view_period: str = "☀️ Theo Ngày") -> str:
    name = ldr.get('name', key)
    name_disp = format_person_name(name)
    display_name = f"Shift Leader {name_disp}" if is_en() else ldr.get('display_name', f"Ca Trưởng {name}")
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
    kpi_rank = translate_eval(kpi_eval.get('rank', 'Đạt chuẩn'))
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
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; white-space: nowrap;">{t(f"🟢 Đang trực ca SX ({shift_count} ca)", f"🟢 On Shift ({shift_count} shifts)")}</div>"""
    elif duty_type == 'MAINT':
        m_cnt = ldr.get('maint_count', shift_count)
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #fffbeb; color: #92400e; border: 1px solid #fde68a; white-space: nowrap;">{t(f"🔧 Trực Bảo trì - VS ({m_cnt} ca)", f"🔧 Maintenance ({m_cnt} shifts)")}</div>"""
    else:
        badge_lbl = f"⚪ Nghỉ ca ({period_lbl})" if period_lbl else "⚪ Nghỉ ca"
        duty_badge_html = f"""<div style="font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 14px; background: #f8fafc; color: #64748b; border: 1px solid #cbd5e1; white-space: nowrap;">{t(badge_lbl, f"⚪ Off Shift ({period_lbl})" if period_lbl else "⚪ Off Shift")}</div>"""

    is_week_view = ("tuần" in str(view_period).lower() or "week" in str(view_period).lower())
    is_month_view = ("tháng" in str(view_period).lower() or "month" in str(view_period).lower())

    # Thiết lập số liệu cho 6 ô chỉ số lớn theo kỳ chọn (view_period)
    if is_week_view:
        active_period_title = f"{t('Tuần', 'Week')} {w_lbl}"
        active_period_tag = f"📅 {t('TUẦN', 'WEEK')}"
        highlight_day = "#ffffff"
        highlight_week = "#ecfdf5"
        highlight_month = "#ffffff"
        
        out_val = w_out
        out_title = f"📦 {t('Sản Lượng Tuần', 'Weekly Output')}"
        out_disp = f"{out_val:,.1f}"
        out_sub = f"{t('Lũy kế', 'Total')} {w_shifts} {t('ca tuần', 'shifts')}"
        out_sub_color = "#16a34a"

        kwh_val = w_kwh
        kwh_title = f"⚡ {t('Suất Điện TB Tuần', 'Weekly Power Rate')}"
        if kwh_val > 0:
            kwh_disp = f"{kwh_val:.1f}"
            e_eval = evaluate_electricity(kwh_val)
            e_label = translate_eval(e_eval.get('label', 'Đạt chuẩn'))
            e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
        else:
            kwh_disp = "--"
            e_label = t("Chờ số liệu", "Pending")
            e_color = "#64748b"

        tph_val = w_tph
        tph_title = f"⚙️ {t('Năng Suất TB Tuần', 'Weekly Press Rate')}"
        p_eval = evaluate_productivity(tph_val)
        p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
        p_label = translate_eval(p_eval.get('label', 'Đạt chỉ tiêu')) if tph_val > 0 else t('Chờ số liệu', 'Pending')
        p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

        hours_val = w_hours
        hours_title = f"⏱️ {t('Giờ Máy Ép Tuần', 'Weekly Press Hours')}"
        hours_disp = f"{hours_val:.1f}"
        hours_sub = f"{w_shifts} {t('ca vận hành', 'shifts')}"

        ratio_val = w_ratio
        ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
        ratio_sub = f"{t('NL đốt:', 'Biomass fuel:')} {w_nl_dot:,.1f}t"

    elif is_month_view:
        active_period_title = f"{t('Tháng', 'Month')} {m_lbl}/2026"
        active_period_tag = f"📆 {t('THÁNG', 'MONTH')}"
        highlight_day = "#ffffff"
        highlight_week = "#ffffff"
        highlight_month = "#faf5ff"

        out_val = m_out
        out_title = f"📦 {t('Sản Lượng Tháng', 'Monthly Output')}"
        out_disp = f"{out_val:,.1f}"
        out_sub = f"{t('Lũy kế', 'Total')} {m_shifts} {t('ca tháng', 'shifts')}"
        out_sub_color = "#7c3aed"

        kwh_val = m_kwh
        kwh_title = f"⚡ {t('Suất Điện TB Tháng', 'Monthly Power Rate')}"
        if kwh_val > 0:
            kwh_disp = f"{kwh_val:.1f}"
            e_eval = evaluate_electricity(kwh_val)
            e_label = translate_eval(e_eval.get('label', 'Đạt chuẩn'))
            e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
        else:
            kwh_disp = "--"
            e_label = t("Chờ số liệu", "Pending")
            e_color = "#64748b"

        tph_val = m_tph
        tph_title = f"⚙️ {t('Năng Suất TB Tháng', 'Monthly Press Rate')}"
        p_eval = evaluate_productivity(tph_val)
        p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
        p_label = translate_eval(p_eval.get('label', 'Đạt chỉ tiêu')) if tph_val > 0 else t('Chờ số liệu', 'Pending')
        p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

        hours_val = m_hours
        hours_title = f"⏱️ {t('Giờ Máy Ép Tháng', 'Monthly Press Hours')}"
        hours_disp = f"{hours_val:.1f}"
        hours_sub = f"{m_shifts} {t('ca vận hành', 'shifts')}"

        ratio_val = m_ratio
        ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
        ratio_sub = f"{t('NL đốt:', 'Biomass fuel:')} {m_nl_dot:,.1f}t"

    else:
        # Mặc định: ☀️ Theo Ngày
        active_period_title = f"{t('Ngày', 'Date')} {d_full_date}" if d_full_date else t("Hôm nay", "Today")
        active_period_tag = f"☀️ {t('NGÀY', 'DAY')}"
        highlight_day = "#f0f9ff"
        highlight_week = "#ffffff"
        highlight_month = "#ffffff"

        hours_title = f"⏱️ {t('Giờ Máy Ép', 'Press Hours')}"
        if duty_type == 'PROD':
            out_val = d_out if d_out > 0 else ldr.get('output', 0.0)
            out_pct = ldr.get('output_pct', 0.0)
            out_title = f"📦 {t('Sản Lượng Ca', 'Shift Output')}"
            out_disp = f"{out_val:,.1f}"
            out_sub = f"{out_pct:.0f}% {t('tổng nhà máy', 'of plant')}" if out_pct > 0 else f"{d_shifts} {t('ca vận hành', 'shifts')}"
            out_sub_color = "#0284c7"

            kwh_val = d_kwh if d_kwh > 0 else ldr.get('kwh_per_ton', 0.0)
            kwh_title = f"⚡ {t('Suất Tiêu Hao Điện', 'Power Consumption')}"
            if kwh_val > 0:
                kwh_disp = f"{kwh_val:.1f}"
                e_eval = ldr.get('elec_eval', evaluate_electricity(kwh_val))
                e_label = translate_eval(e_eval.get('label', 'Đạt chuẩn'))
                e_color = "#15803d" if e_eval.get('status') == 'EXCELLENT' else ("#0369a1" if e_eval.get('status') == 'STANDARD' else "#b91c1c")
            else:
                kwh_disp = "--"
                e_label = f"{t('TB tháng:', 'Monthly avg:')} {m_kwh:.1f}" if m_kwh > 0 else t("Chờ số liệu", "Pending")
                e_color = "#64748b"

            tph_val = d_tph if d_tph > 0 else ldr.get('tph', 0.0)
            tph_title = f"⚙️ {t('Năng Suất Ép TB', 'Avg Press Rate')}"
            p_eval = ldr.get('prod_eval', evaluate_productivity(tph_val))
            p_disp = f"{tph_val:.2f}" if tph_val > 0 else "--"
            p_label = translate_eval(p_eval.get('label', 'Đạt chỉ tiêu')) if tph_val > 0 else t('Đang chạy máy', 'Running')
            p_color = "#15803d" if p_eval.get('status') == 'PASS' else "#b45309"

            hours_val = d_hours if d_hours > 0 else ldr.get('pellet_hours', 0.0)
            hours_disp = f"{hours_val:.1f}"
            hours_sub = f"{d_shifts} {t('ca vận hành', 'shifts')}"

            ratio_val = d_ratio if d_ratio > 0 else ldr.get('processing_ratio', 0.0)
            nl_dot_val = d_nl_dot if d_nl_dot > 0 else ldr.get('nl_dot', 0.0)
            ratio_disp = f"{ratio_val:.2f}" if ratio_val > 0 else "--"
            ratio_sub = f"{t('NL đốt:', 'Biomass fuel:')} {nl_dot_val:,.1f}t"
        elif duty_type == 'MAINT':
            m_cnt = ldr.get('maint_count', shift_count)
            out_title = f"📦 {t('Sản Lượng Ca', 'Shift Output')}"
            out_disp = "0.0"
            out_sub = f"🔧 {t('Trực Bảo trì - Vệ sinh', 'Maintenance - Cleaning')}"
            out_sub_color = "#d97706"

            kwh_title = f"⚡ {t('Suất Tiêu Hao Điện', 'Power Consumption')}"
            kwh_disp = "--"
            e_label = t("Bảo dưỡng máy", "Maintenance")
            e_color = "#d97706"

            tph_title = f"⚙️ {t('Năng Suất Ép TB', 'Avg Press Rate')}"
            p_disp = "--"
            p_label = t("Bảo trì thiết bị", "Equipment maintenance")
            p_color = "#d97706"

            hours_disp = "0.0"
            hours_sub = f"{m_cnt} {t('ca bảo trì', 'maintenance shifts')}"

            ratio_disp = "0.0"
            ratio_sub = t("Bảo dưỡng xưởng", "Plant maintenance")
        else:
            latest_date = ldr.get('latest_shift_date', 'N/A')
            latest_out = ldr.get('latest_shift_out', 0.0)
            out_title = f"📦 {t('Sản Lượng Ca', 'Shift Output')}"
            out_disp = "0.0"
            out_sub = f"{t('Ca gần nhất:', 'Latest shift:')} {latest_date} ({latest_out:,.1f}t)" if latest_date != 'N/A' else t("Nghỉ ca", "Off shift")
            out_sub_color = "#64748b"

            kwh_title = f"⚡ {t('Suất Tiêu Hao Điện', 'Power Consumption')}"
            kwh_disp = "--"
            e_label = f"{t('TB tháng:', 'Monthly avg:')} {m_kwh:.1f}" if m_kwh > 0 else t("Nghỉ ca", "Off shift")
            e_color = "#64748b"

            tph_title = f"⚙️ {t('Năng Suất Ép TB', 'Avg Press Rate')}"
            p_disp = "--"
            p_label = f"{t('TB tháng:', 'Monthly avg:')} {m_tph:.2f}" if m_tph > 0 else t("Nghỉ ca", "Off shift")
            p_color = "#64748b"

            hours_disp = "0.0"
            hours_sub = f"0 {t('ca vận hành', 'shifts')}"

            ratio_disp = "--"
            ratio_sub = t("Không phát sinh", "None")

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
                <div style="font-size: 12px; font-weight: 700; color: #475569;">🏆 {t("Thi Đua KPI:", "KPI Competition:")}</div>
                <div style="font-size: 13px; font-weight: 800; color: {kpi_color};">
                    {kpi_score:.1f}{t("đ", " pts")} <span style="font-size: 11px; font-weight: 700; color: #475569;">({kpi_medal} {kpi_rank})</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{out_title}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{out_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">{t("tấn", "tons")}</span></div>
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
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{hours_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">{t("giờ", "hrs")}</span></div>
                    <div style="font-size: 10px; font-weight: 600; color: #475569; margin-top: 2px;">{hours_sub}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{t("💧 Độ Ẩm Viên TB", "💧 Avg Pellet Moisture")}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{moist_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">%</span></div>
                    <div style="font-size: 10px; font-weight: 700; color: {m_color}; margin-top: 2px;">{m_label}</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">{t("🔄 Tỷ Lệ Chế Biến", "🔄 Processing Ratio")}</div>
                    <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 2px;">{ratio_disp} <span style="font-size: 11px; font-weight: 500; color: #64748b;">{t("lần", "x")}</span></div>
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
def render_leaders_side_by_side(all_db, default_time_view: str = None):
    leaders = all_db.get('leaders', {})
    
    kpi_time_options = [
        t("☀️ Theo Ngày", "☀️ Daily"),
        t("📅 Theo Tuần", "📅 Weekly"),
        t("📆 Theo Tháng", "📆 Monthly")
    ]
    
    if not default_time_view or default_time_view not in kpi_time_options:
        if is_week_mode:
            default_time_view = kpi_time_options[1]
        elif is_month_mode or is_year_mode:
            default_time_view = kpi_time_options[2]
        else:
            default_time_view = kpi_time_options[0]

    # Đồng bộ session state của segmented control nếu có giá trị cũ từ ngôn ngữ trước
    if 'leader_kpi_time_view_segmented' in st.session_state:
        cur_val = st.session_state['leader_kpi_time_view_segmented']
        if cur_val not in kpi_time_options:
            if cur_val and ('tuần' in str(cur_val).lower() or 'week' in str(cur_val).lower()):
                st.session_state['leader_kpi_time_view_segmented'] = kpi_time_options[1]
            elif cur_val and ('tháng' in str(cur_val).lower() or 'month' in str(cur_val).lower()):
                st.session_state['leader_kpi_time_view_segmented'] = kpi_time_options[2]
            else:
                st.session_state['leader_kpi_time_view_segmented'] = kpi_time_options[0]

    # Thanh điều khiển chọn kỳ trọng tâm hiển thị cho 3 Ca Trưởng
    col_banner_txt, col_banner_ctrl = st.columns([5, 5])
    with col_banner_txt:
        st.caption(t(
            "💡 *Tùy chọn hiển thị 6 ô số liệu trọng tâm cho 3 Ca Trưởng. Bảng lũy kế 3 kỳ ở cuối thẻ luôn tổng hợp đầy đủ cả Ngày, Tuần, Tháng.*",
            "💡 *Focus period for the 6 primary metric cards across the 3 Shift Leaders. The 3-period summary table always aggregates Day, Week, and Month.*"
        ))
    with col_banner_ctrl:
        selected_kpi_time_view = st.segmented_control(
            t("⏱️ **CHỌN KỲ HIỂN THỊ TRỌNG TÂM:**", "⏱️ **FOCUS PERIOD FOR METRIC CARDS:**"),
            options=kpi_time_options,
            default=default_time_view,
            key="leader_kpi_time_view_segmented"
        )
        if not selected_kpi_time_view:
            selected_kpi_time_view = default_time_view

    col_a, col_b, col_c = st.columns(3)
    leader_order = [('Sắc', col_a), ('Tài', col_b), ('Long', col_c)]

    for key, col in leader_order:
        ldr = leaders.get(key, {})
        with col:
            html = render_leader_card_html(ldr, key, view_period=selected_kpi_time_view)
            st.markdown(html, unsafe_allow_html=True)

    # Bảng đối sánh toàn diện
    with st.expander(t("📊 Xem Bảng Đối Sánh Toàn Diện: Toàn Nhà Máy vs 3 Ca Trưởng (Ca A Sắc - Ca B Tài - Ca C Long)", "📊 Comprehensive Comparison: Plant-Wide vs 3 Shift Leaders (Shift A Sac - Shift B Tai - Shift C Long)"), expanded=True):
        st.dataframe(translate_comparison_df(all_db.get('comparison_df', pd.DataFrame())), use_container_width=True, hide_index=True)

# Hàm hiển thị Dashboard chuyên sâu cho 1 Ca Trưởng
def render_single_leader_dashboard(ldr, all_db):
    ldr_name_disp = format_person_name(ldr['name'])
    ldr_title_disp = f"Shift Leader {ldr_name_disp}" if is_en() else ldr['display_name']
    kpi_rank_str = translate_eval(ldr['kpi_eval'].get('rank', ''))
    status_text_disp = t(ldr['status_text'], "On Duty" if "trực" in ldr['status_text'].lower() else ("Maintenance" if "bảo" in ldr['status_text'].lower() else "Off Duty"))

    raw_header = f"""
    <div style="background: {ldr['bg_color']}; border-left: 6px solid {ldr['color']}; padding: 14px 20px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px; font-weight: 800; color: {ldr['color']};">{ldr['icon']} {t('BẢNG ĐIỀU KHIỂN SẢN XUẤT:', 'PRODUCTION DASHBOARD:')} {ldr_title_disp.upper()}</span>
            <span style="font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 20px; background: #ffffff; color: {ldr['color']}; border: 1px solid {ldr['border_color']};">{ldr['status_icon']} {status_text_disp}</span>
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #1e293b;">
            🏆 {t('Điểm Thi Đua KPI:', 'KPI Competition Score:')} <span style="color: {ldr['kpi_eval'].get('color', '#16a34a')};">{ldr['kpi_score']:.1f}/100</span> ({ldr['kpi_eval'].get('medal', '')} {kpi_rank_str})
        </div>
    </div>
    """
    st.markdown(clean_html(raw_header), unsafe_allow_html=True)

    if ldr.get('has_active_shift'):
        # Hàng 1
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        with r1_c1:
            st.markdown(render_kpi_card_html(f"{t('Sản Lượng', 'Output')} ({t('Ca', 'Shift')} {ldr_name_disp})", f"{ldr['output']:,.1f}", t("Tấn", "Tons"), f"{ldr['output_pct']:.0f}% {t('tổng nhà máy', 'of plant')}", "badge-info"), unsafe_allow_html=True)
        with r1_c2:
            e_eval = ldr.get('elec_eval', {})
            b_cls = "badge-success" if e_eval.get('status') == 'EXCELLENT' else ("badge-info" if e_eval.get('status') == 'STANDARD' else "badge-danger")
            val_e = f"{ldr['kwh_per_ton']:.1f}" if ldr['kwh_per_ton'] > 0 else f"{ldr['month_kwh_ton']:.1f}*"
            lbl_e = f"{e_eval.get('icon', '')} {translate_eval(e_eval.get('label', ''))}" if ldr['kwh_per_ton'] > 0 else t("TB tháng", "Monthly avg")
            st.markdown(render_kpi_card_html(f"{t('Suất Điện', 'Power Rate')} ({t('Ca', 'Shift')} {ldr_name_disp})", val_e, "kWh/t", lbl_e, b_cls), unsafe_allow_html=True)
        with r1_c3:
            p_eval = ldr.get('prod_eval', {})
            b_cls = "badge-success" if p_eval.get('status') == 'PASS' else "badge-warning"
            st.markdown(render_kpi_card_html(f"{t('Năng Suất Ép', 'Press Rate')} ({t('Ca', 'Shift')} {ldr_name_disp})", f"{ldr['tph']:.2f}", "Tấn/h", f"{p_eval.get('icon', '')} {translate_eval(p_eval.get('label', ''))}", b_cls), unsafe_allow_html=True)
        with r1_c4:
            st.markdown(render_kpi_card_html(f"{t('Giờ Máy Ép', 'Press Hours')} ({t('Ca', 'Shift')} {ldr_name_disp})", f"{ldr['pellet_hours']:.1f}", t("Giờ", "Hours"), f"{ldr['shift_count']} {t('ca phụ trách', 'shifts')}", "badge-info"), unsafe_allow_html=True)

        # Hàng 2
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
        with r2_c1:
            m_eval = ldr.get('moist_eval', {})
            b_cls = "badge-success" if m_eval.get('status') == 'PASS' else "badge-warning"
            st.markdown(render_kpi_card_html(t("Độ Ẩm TB Viên", "Avg Pellet Moisture"), f"{ldr['moisture']:.2f}", "%", f"{m_eval.get('icon', '💧')} {m_eval.get('label', '8.0 - 9.5%')}", b_cls), unsafe_allow_html=True)
        with r2_c2:
            st.markdown(render_kpi_card_html(t("Điểm KPI Thi Đua", "KPI Score"), f"{ldr['kpi_score']:.1f}", "/100", f"{ldr['kpi_eval'].get('medal', '')} {kpi_rank_str}", "badge-success"), unsafe_allow_html=True)
        with r2_c3:
            st.markdown(render_kpi_card_html(t("Tỷ Lệ Chế Biến", "Processing Ratio"), f"{ldr['processing_ratio']:.2f}", t("lần", "x"), f"{t('NL đốt:', 'Fuel:')} {ldr['nl_dot']:,.1f}t", "badge-info"), unsafe_allow_html=True)
        with r2_c4:
            st.markdown(render_kpi_card_html(t("Lũy Kế Tháng", "Monthly Total"), f"{ldr['month_output']:,.0f}", t("Tấn", "Tons"), f"{ldr['month_shifts']} {t('ca', 'shifts')} | {ldr['month_tph']:.2f} t/h", "badge-info"), unsafe_allow_html=True)

        st.markdown(f"##### 📊 {t('TIẾN ĐỘ THEO KỲ: NGÀY / TUẦN / THÁNG', 'PERIOD PROGRESS: DAY / WEEK / MONTH')} ({t('CA TRƯỞNG', 'SHIFT LEADER')} {ldr_name_disp.upper()})")
        r_per_1, r_per_2, r_per_3 = st.columns(3)
        with r_per_1:
            st.markdown(render_kpi_card_html(f"☀️ {t('Ngày', 'Daily')} ({ldr.get('day_label', t('Hôm nay', 'Today'))})", f"{ldr.get('day_out', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('day_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('day_kwh_ton', 0):.1f} kWh/t", "badge-info"), unsafe_allow_html=True)
        with r_per_2:
            st.markdown(render_kpi_card_html(f"📅 {t('Tuần', 'Weekly')} ({ldr.get('week_label', t('Tuần', 'Week'))})", f"{ldr.get('week_out', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('week_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('week_kwh_ton', 0):.1f} kWh/t", "badge-success"), unsafe_allow_html=True)
        with r_per_3:
            st.markdown(render_kpi_card_html(f"📆 {t('Tháng', 'Monthly')} ({ldr.get('month_label', t('Tháng', 'Month'))})", f"{ldr.get('month_output', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('month_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('month_kwh_ton', 0):.1f} kWh/t", "badge-warning"), unsafe_allow_html=True)
    else:
        # Off-duty: Hiển thị Thành tích Ca gần nhất & Lũy kế tháng cực kỳ chuyên nghiệp
        st.info(t(
            f"ℹ️ **Ca Trưởng {ldr['name']} không có ca trực trong kỳ này ({ldr['period_label']}).** Dưới đây là thành tích tại **Ca trực gần nhất (Ngày {ldr['latest_shift_date']})** và **Tổng hợp Lũy kế tháng**.",
            f"ℹ️ **Shift Leader {ldr_name_disp} has no shifts in this period ({ldr['period_label']}).** Below are metrics from **Latest Shift ({ldr['latest_shift_date']})** and **Monthly Total**."
        ))
        
        st.markdown(f"##### 🕒 {t('THÀNH TÍCH CA TRỰC GẦN NHẤT', 'LATEST SHIFT RECORD')} ({t('NGÀY', 'DATE')} {ldr['latest_shift_date']})")
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        with r1_c1:
            st.markdown(render_kpi_card_html(f"{t('Sản Lượng', 'Output')} ({t('Ca', 'Shift')} {ldr['latest_shift_date']})", f"{ldr['latest_shift_out']:,.1f}", t("Tấn", "Tons"), t("Ca gần nhất", "Latest shift"), "badge-info"), unsafe_allow_html=True)
        with r1_c2:
            val_kwh_lat = f"{ldr['latest_shift_kwh']:.1f}" if ldr['latest_shift_kwh'] > 0 else (f"{ldr['month_kwh_ton']:.1f}*" if ldr['month_kwh_ton'] > 0 else "--")
            st.markdown(render_kpi_card_html(t("Suất Điện Tiêu Hao", "Power Consumption"), val_kwh_lat, "kWh/t", t("Ca gần nhất", "Latest shift"), "badge-info"), unsafe_allow_html=True)
        with r1_c3:
            st.markdown(render_kpi_card_html(t("Năng Suất Ép TB", "Avg Press Rate"), f"{ldr['latest_shift_tph']:.2f}", "Tấn/h", t("Ca gần nhất", "Latest shift"), "badge-success"), unsafe_allow_html=True)
        with r1_c4:
            st.markdown(render_kpi_card_html(t("Trạng Thái Trực", "Shift Status"), t("Nghỉ Ca", "Off Shift"), "", f"{t('Kỳ:', 'Period:')} {ldr['period_label']}", "badge-warning"), unsafe_allow_html=True)

        st.markdown(f"##### 📊 {t('TIẾN ĐỘ THEO KỲ: NGÀY / TUẦN / THÁNG', 'PERIOD PROGRESS: DAY / WEEK / MONTH')} ({t('CA TRƯỞNG', 'SHIFT LEADER')} {ldr_name_disp.upper()})")
        r_per_1, r_per_2, r_per_3 = st.columns(3)
        with r_per_1:
            st.markdown(render_kpi_card_html(f"☀️ {t('Ngày', 'Daily')} ({ldr.get('day_label', t('Hôm nay', 'Today'))})", f"{ldr.get('day_out', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('day_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('day_kwh_ton', 0):.1f} kWh/t", "badge-info"), unsafe_allow_html=True)
        with r_per_2:
            st.markdown(render_kpi_card_html(f"📅 {t('Tuần', 'Weekly')} ({ldr.get('week_label', t('Tuần', 'Week'))})", f"{ldr.get('week_out', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('week_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('week_kwh_ton', 0):.1f} kWh/t", "badge-success"), unsafe_allow_html=True)
        with r_per_3:
            st.markdown(render_kpi_card_html(f"📆 {t('Tháng', 'Monthly')} ({ldr.get('month_label', t('Tháng', 'Month'))})", f"{ldr.get('month_output', 0):,.1f}", t("Tấn", "Tons"), f"{ldr.get('month_shifts', 0)} {t('ca', 'shifts')} | {ldr.get('month_kwh_ton', 0):.1f} kWh/t", "badge-warning"), unsafe_allow_html=True)

    # Nhật ký ca chi tiết nếu có
    if not ldr['shifts_df'].empty and (ldr['shifts_df']['san_luong_tan'] > 0).any():
        raw_ldr_name = ldr.get('name', '')
        st.markdown(f"##### 📋 {t(f'Nhật Ký Chi Tiết Ca Trực Của Ca Trưởng {raw_ldr_name}', f'Detailed Shift Log for Leader {ldr_name_disp}')}")
        cols_disp = ['date_str', 'san_luong_tan', 'tong_gio_ep', 'nang_suat_tph', 'dien_kwh', 'dien_tb_kwh_tan', 'nl_dot_tan', 'nghien_tho_tan']
        avail = [c for c in cols_disp if c in ldr['shifts_df'].columns]
        df_sub_disp = ldr['shifts_df'][avail].copy()
        if is_en():
            df_sub_disp.rename(columns={
                'date_str': 'Date',
                'san_luong_tan': 'Output (tons)',
                'tong_gio_ep': 'Press Hours (h)',
                'nang_suat_tph': 'Productivity (t/h)',
                'dien_kwh': 'Power (kWh)',
                'dien_tb_kwh_tan': 'Power Rate (kWh/t)',
                'nl_dot_tan': 'Fuel Material (t)',
                'nghien_tho_tan': 'Coarse Grind (t)'
            }, inplace=True)
        else:
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

# ================= CỬA SỔ TÁC VỤ & ĐIỀU HƯỚNG =================
active_task = st.session_state.get('active_task', OP_TASKS[0])
active_task = map_task_name(active_task, curr_lang)
st.session_state['active_task'] = active_task
if active_task not in TASK_LIST:
    active_task = OP_TASKS[0]
active_task_idx = TASK_LIST.index(active_task)

is_op = active_task in OP_TASKS
is_static = active_task in STATIC_TASKS
is_entry = active_task in ENTRY_TASKS

# Nếu ở nhóm 1 (Vận hành & KPI), hiển thị Dashboard tổng hợp & Dashboard ca trưởng
if is_op:
    st.markdown("---")
    db_choices = get_dashboard_choices(curr_lang)
    curr_db_choice = st.session_state.get('main_db_view_choice', db_choices[0])
    curr_db_choice = map_dashboard_choice(curr_db_choice, curr_lang)
    try:
        default_db_idx = db_choices.index(curr_db_choice)
    except ValueError:
        default_db_idx = 0

    if 'main_db_view_select' in st.session_state and st.session_state['main_db_view_select'] not in db_choices:
        st.session_state['main_db_view_select'] = curr_db_choice

    selected_dashboard_view = st.selectbox(
        t("📌 LỰA CHỌN DASHBOARD HIỂN THỊ:", "📌 SELECT DASHBOARD VIEW:"),
        db_choices,
        index=default_db_idx,
        key="main_db_view_select"
    )
    st.session_state['main_db_view_choice'] = selected_dashboard_view
    sel_db_idx = db_choices.index(selected_dashboard_view) if selected_dashboard_view in db_choices else 0

    # Hiển thị theo chế độ đã chọn
    if sel_db_idx == 0:
        st.markdown(render_section_banner(t("🏭 1. BẢNG ĐIỀU KHIỂN TỔNG HỢP TOÀN NHÀ MÁY", "🏭 1. PLANT-WIDE CONSOLIDATED DASHBOARD"), t("Định mức & Mục tiêu Kỹ thuật BVN Quảng Bình", "Technical Benchmarks & Targets - BVN Quang Binh"), "#2563eb"), unsafe_allow_html=True)
        render_factory_dashboard_cards(kpis, df_weekly)

        # Thanh chuyển nhanh sang phân hệ nhập số liệu trực tiếp
        c_eb1, c_eb2 = st.columns([7, 3])
        with c_eb1:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 8px; padding: 8px 14px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">✍️</span>
                <div>
                    <span style="font-size: 13px; font-weight: 700; color: #34d399;">{t("KHÔNG GIAN NHẬP SỐ LIỆU SẢN XUẤT TRỰC TIẾP", "DIRECT PRODUCTION DATA ENTRY WORKSPACE")}</span>
                    <span style="font-size: 11px; color: #94a3b8; margin-left: 8px;">{t("Phân quyền: 🏭 Sản Xuất (Ca A, B, C, QĐ) • 🔬 KCS • 🔧 Bảo Trì • 🪵 Chipper", "Role-based: 🏭 Production • 🔬 KCS • 🔧 Maint • 🪵 Chipper")}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_eb2:
            if st.button(f"🚀 {t('NHẬP SỐ LIỆU NGAY (4 TABS)', 'ENTER DATA NOW (4 TABS)')}", key="btn_jump_to_entry_from_overview", type="primary", use_container_width=True):
                st.session_state['active_task'] = ENTRY_TASKS[0]
                st.rerun()

        st.markdown("---")
        st.markdown(render_section_banner(t("👥 2. BẢNG ĐIỀU KHIỂN CHI TIẾT 3 CA TRƯỞNG: SẮC (CA A) - TÀI (CA B) - LONG (CA C)", "👥 2. DETAILED SHIFT LEADER DASHBOARDS: SAC (SHIFT A) - TAI (SHIFT B) - LONG (SHIFT C)"), t("Theo dõi Song Song & Thi Đua KPI", "Parallel Monitoring & KPI Competition"), "#10b981"), unsafe_allow_html=True)
        cur_def_time = t("☀️ Theo Ngày", "☀️ Daily")
        if is_week_mode:
            cur_def_time = t("📅 Theo Tuần", "📅 Weekly")
        elif is_month_mode or is_year_mode:
            cur_def_time = t("📆 Theo Tháng", "📆 Monthly")
        render_leaders_side_by_side(all_db_summary, default_time_view=cur_def_time)
    elif sel_db_idx == 1:
        st.markdown(render_section_banner(t("🏭 BẢNG ĐIỀU KHIỂN TỔNG HỢP TOÀN NHÀ MÁY", "🏭 PLANT-WIDE CONSOLIDATED DASHBOARD"), t("Định mức & Mục tiêu Kỹ thuật BVN Quảng Bình", "Technical Benchmarks & Targets - BVN Quang Binh"), "#2563eb"), unsafe_allow_html=True)
        render_factory_dashboard_cards(kpis, df_weekly)

        # Thanh chuyển nhanh sang phân hệ nhập số liệu trực tiếp
        c_eb1, c_eb2 = st.columns([7, 3])
        with c_eb1:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 8px; padding: 8px 14px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">✍️</span>
                <div>
                    <span style="font-size: 13px; font-weight: 700; color: #34d399;">{t("KHÔNG GIAN NHẬP SỐ LIỆU SẢN XUẤT TRỰC TIẾP", "DIRECT PRODUCTION DATA ENTRY WORKSPACE")}</span>
                    <span style="font-size: 11px; color: #94a3b8; margin-left: 8px;">{t("Phân quyền: 🏭 Sản Xuất (Ca A, B, C, QĐ) • 🔬 KCS • 🔧 Bảo Trì • 🪵 Chipper", "Role-based: 🏭 Production • 🔬 KCS • 🔧 Maint • 🪵 Chipper")}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_eb2:
            if st.button(f"🚀 {t('NHẬP SỐ LIỆU NGAY (4 TABS)', 'ENTER DATA NOW (4 TABS)')}", key="btn_jump_to_entry_from_overview_single", type="primary", use_container_width=True):
                st.session_state['active_task'] = ENTRY_TASKS[0]
                st.rerun()
    elif sel_db_idx == 2:
        render_single_leader_dashboard(all_db_summary['leaders']['Sắc'], all_db_summary)
    elif sel_db_idx == 3:
        render_single_leader_dashboard(all_db_summary['leaders']['Tài'], all_db_summary)
    elif sel_db_idx == 4:
        render_single_leader_dashboard(all_db_summary['leaders']['Long'], all_db_summary)

st.markdown("---")

if is_op:
    group_title = t("📊 NHÓM 1: VẬN HÀNH, KPI & ĐO LƯỜNG (SỐ LIỆU ĐỘNG HÀNG NGÀY)", "📊 GROUP 1: OPERATIONS, KPI & METRICS (DYNAMIC DAILY DATA)")
    group_color = "#38bdf8"
    group_tag = t(f"Mục {OP_TASKS.index(active_task) + 1}/10 Vận Hành & KPI", f"Item {OP_TASKS.index(active_task) + 1}/10 Operations & KPI")
elif is_static:
    group_title = t("📘 NHÓM 2: QUY TRÌNH, SƠ ĐỒ & CƠ CẤU (TÀI LIỆU KỸ THUẬT CỐ ĐỊNH)", "📘 GROUP 2: WORKFLOWS, SCHEMATICS & STRUCTURE (STANDARDIZED)")
    group_color = "#c084fc"
    group_tag = t(f"Mục {STATIC_TASKS.index(active_task) + 1}/3 Quy Trình & Sơ Đồ", f"Item {STATIC_TASKS.index(active_task) + 1}/3 Workflows & Schematics")
else:
    group_title = t("📝 NHÓM 3: NHẬP SỐ LIỆU (PHÂN QUYỀN TRUY CẬP)", "📝 GROUP 3: DATA ENTRY (ROLE PROTECTED)")
    group_color = "#34d399"
    group_tag = t("Mục 14/14 Nhập Số Liệu", "Item 14/14 Data Entry")

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
        
    tag_op = t("Vận hành", "Operations")
    tag_st = t("Cố định", "Standard")
    tag_en = t("Nhập liệu", "Data Entry")

    if 'main_task_dropdown' in st.session_state and st.session_state['main_task_dropdown'] not in TASK_LIST:
        st.session_state['main_task_dropdown'] = TASK_LIST[active_task_idx]

    st.selectbox(
        t("Chuyển nhanh cửa sổ tác vụ:", "Quick switch task window:"),
        TASK_LIST,
        index=active_task_idx,
        format_func=lambda x: f"📊 [{tag_op}] {x}" if x in OP_TASKS else (f"📘 [{tag_st}] {x}" if x in STATIC_TASKS else f"📝 [{tag_en}] {x}"),
        key="main_task_dropdown",
        on_change=on_main_select_change,
        label_visibility="collapsed"
    )

with col_btn_prev:
    if st.button(t("⬅️ Tác vụ trước", "⬅️ Previous Task"), disabled=(active_task_idx == 0), use_container_width=True, key="btn_prev_task"):
        new_task = TASK_LIST[active_task_idx - 1]
        st.session_state['active_task'] = new_task
        st.rerun()

with col_btn_next:
    if st.button(t("Tác vụ kế tiếp ➡️", "Next Task ➡️"), disabled=(active_task_idx == len(TASK_LIST) - 1), use_container_width=True, key="btn_next_task"):
        new_task = TASK_LIST[active_task_idx + 1]
        st.session_state['active_task'] = new_task
        st.rerun()

st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# Trích xuất số thứ tự tác vụ chính xác (tránh lỗi xung đột chuỗi "1. " với "11. ")
m_task = re.search(r'(\d+)\.', active_task)
task_num = int(m_task.group(1)) if m_task else 1

# ----------------- TAB 1: NHẬT KÝ CA & THIẾT BỊ NGÀY -----------------
if task_num == 1:
    st.markdown(f'<div class="section-title">{t("📊 Chi Tiết Các Ca Sản Xuất Trong Ngày", "📊 Daily Production Shift Details")}</div>', unsafe_allow_html=True)
    lbl_moist = translate_eval(moist_eval.get('label', ''))
    lbl_dens = translate_eval(dens_eval.get('label', ''))
    st.info(
        f"🧪 **{t('Chỉ số chất lượng & chế biến thành phẩm ngày', 'Quality & Finished Goods Processing Metrics')} ({kpis.get('date_str', 'N/A')}):** "
        f"{t('Độ ẩm viên TB', 'Avg Pellet Moisture')}: **{am_val:.2f}%** ({lbl_moist}) | "
        f"{t('Tỷ trọng viên nén', 'Pellet Density')}: **{ty_trong_val:,.1f} kg/m³** ({lbl_dens}) | "
        f"{t('Tỷ lệ chế biến', 'Processing Ratio')}: **{kpis.get('processing_ratio', 0):.2f} {t('lần', 'x')}** | "
        f"📦 {t('Tồn kho viên nén', 'Pellet Inventory')}: **{kpis.get('ton_kho_tan', 0):,.1f} {t('tấn', 'tons')}**"
    )
    
    col_t1_left, col_t1_right = st.columns([3, 2])
    
    with col_t1_left:
        shift_data = kpis.get('shift_details', [])
        if shift_data:
            df_shifts_table = pd.DataFrame(shift_data)
            if global_search_kw and not df_shifts_table.empty:
                s_match = search_df(df_shifts_table, global_search_kw)
                if not s_match.empty:
                    df_shifts_table = s_match
            # Tạo các cột hiển thị đẹp
            df_view = pd.DataFrame({
                t('Ca Trưởng', 'Shift Leader'): df_shifts_table['ca_truong'],
                t('Sản Lượng (tấn)', 'Output (tons)'): df_shifts_table['san_luong_tan'],
                t('Giờ Máy Ép (h)', 'Press Hours (h)'): df_shifts_table['tong_gio_ep'],
                t('Năng Suất (tấn/h)', 'Productivity (t/h)'): df_shifts_table['nang_suat_tph'],
                t('Đánh Giá NS', 'Prod. Eval'): df_shifts_table['ns_eval'].apply(lambda x: f"{x['icon']} {translate_eval(x['label'])}"),
                t('Điện Tiêu Thụ (kWh)', 'Power Used (kWh)'): df_shifts_table['dien_kwh'],
                t('Suất Điện (kWh/t)', 'Power Rate (kWh/t)'): df_shifts_table['dien_tb_kwh_tan'],
                t('Đánh Giá Điện', 'Power Eval'): df_shifts_table['elec_eval'].apply(lambda x: f"{x['icon']} {translate_eval(x['label'])}"),
                t('NL Đốt (tấn)', 'Fuel Biomass (tons)'): df_shifts_table['nl_dot_tan'],
                t('Nghiền Thô (tấn)', 'Coarse Milling (tons)'): df_shifts_table['nghien_tho_tan']
            })
            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(234, 179, 8, 0.08); border: 1.5px dashed #eab308; border-radius: 10px; padding: 18px 16px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: #facc15; font-size: 14px;">
                    <span>⚠️</span>
                    <span>{t(f"Ngày {kpis.get('date_str', '')} chưa có dữ liệu ca sản xuất", f"No shift production data for {kpis.get('date_str', '')}")}</span>
                </div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 6px; line-height: 1.5;">
                    {t("Chưa có ca nào được ghi nhận cho ngày này. Quý khách có thể nhập trực tiếp bằng biểu mẫu bên dưới hoặc bấm nút chuyển nhanh sang phân hệ Nhập Số Liệu.", "No shifts recorded yet for this date. You can enter data using the form below or switch to the Data Entry workspace.")}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_t1_right:
        # Biểu đồ Donut tỷ trọng sản lượng theo ca
        if shift_data:
            fig_donut = px.pie(
                df_shifts_table,
                names='ca_truong',
                values='san_luong_tan',
                title=t("Tỷ Trọng Sản Lượng Giữa Các Ca", "Production Share by Shift"),
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(shift_data))
            fig_donut.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 26px; margin-bottom: 4px;">📝</div>
                <div style="font-size: 13px; font-weight: 700; color: #34d399;">{t("KHÔNG GIAN NHẬP SỐ LIỆU", "DATA ENTRY WORKSPACE")}</div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 4px; margin-bottom: 10px;">{t("4 Tabs: 🏭 Sản Xuất • 🔬 KCS • 🔧 Bảo Trì • 🪵 Chipper", "4 Tabs: 🏭 Prod • 🔬 KCS • 🔧 Maint • 🪵 Chipper")}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🚀 {t('NHẬP SỐ LIỆU NGAY (4 TABS)', 'ENTER DATA NOW (4 TABS)')}", key="btn_jump_to_entry_empty_shift", type="primary", use_container_width=True):
                st.session_state['active_task'] = ENTRY_TASKS[0]
                st.rerun()

    st.markdown(f'<div class="section-title">{t("⏱️ Thời Gian Máy Chạy Của Các Cụm Thiết Bị (Giờ/Ngày)", "⏱️ Equipment Operating Hours (Hours/Day)")}</div>', unsafe_allow_html=True)
    
    eq_hours = kpis.get('equipment_hours', {})
    if eq_hours:
        c_eq1, c_eq2, c_eq3, c_eq4 = st.columns(4)
        col_mach = t('Máy', 'Machine')
        col_hr = t('Giờ', 'Hours')
        
        # 1. Nghiền búa thô
        with c_eq1:
            st.markdown(f"##### {t('🔨 Nghiền Búa Thô', '🔨 Coarse Hammer Mills')}")
            data_tho = [
                {col_mach: 'HM118 (Andritz)', col_hr: eq_hours.get('HM118', {}).get('hours', 0)},
                {col_mach: 'HM218 (Andritz)', col_hr: eq_hours.get('HM218', {}).get('hours', 0)},
                {col_mach: 'HM318 (SHT)', col_hr: eq_hours.get('HM318', {}).get('hours', 0)},
            ]
            fig_tho = px.bar(data_tho, x=col_mach, y=col_hr, text=col_hr, color=col_mach, color_discrete_sequence=['#3b82f6', '#1d4ed8', '#0284c7'])
            fig_tho.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_tho, use_container_width=True)

        # 2. Trống sấy
        with c_eq2:
            st.markdown(f"##### {t('♨️ Trống Sấy', '♨️ Rotary Dryers')}")
            data_say = [
                {col_mach: 'DR124', col_hr: eq_hours.get('DR124', {}).get('hours', 0)},
                {col_mach: 'DR224', col_hr: eq_hours.get('DR224', {}).get('hours', 0)},
            ]
            fig_say = px.bar(data_say, x=col_mach, y=col_hr, text=col_hr, color=col_mach, color_discrete_sequence=['#f97316', '#ea580c'])
            fig_say.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_say, use_container_width=True)

        # 3. Nghiền búa tinh
        with c_eq3:
            st.markdown(f"##### {t('⚙️ Nghiền Búa Tinh', '⚙️ Fine Hammer Mills')}")
            data_tinh = [
                {col_mach: 'HM147 (SHT)', col_hr: eq_hours.get('HM147', {}).get('hours', 0)},
                {col_mach: 'HM247 (Andritz)', col_hr: eq_hours.get('HM247', {}).get('hours', 0)},
                {col_mach: 'HM347 (Andritz)', col_hr: eq_hours.get('HM347', {}).get('hours', 0)},
            ]
            fig_tinh = px.bar(data_tinh, x=col_mach, y=col_hr, text=col_hr, color=col_mach, color_discrete_sequence=['#8b5cf6', '#6d28d9', '#4c1d95'])
            fig_tinh.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_tinh, use_container_width=True)

        # 4. Cụm 8 máy ép viên
        with c_eq4:
            st.markdown(f"##### {t('🔄 Cụm 8 Máy Ép Viên', '🔄 Pellet Mills (8 units)')}")
            data_pe = [{col_mach: f'PE{i}', col_hr: eq_hours.get(f'PE{i}', {}).get('hours', 0)} for i in range(1, 9)]
            fig_pe = px.bar(data_pe, x=col_mach, y=col_hr, text=col_hr, color_discrete_sequence=['#10b981'])
            fig_pe.update_layout(yaxis_range=[0, 24], height=240, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pe, use_container_width=True)

    # KHÔNG GIAN NHẬP SỐ LIỆU SẢN XUẤT TRỰC TIẾP (ĐỒNG BỘ GOOGLE SHEETS)
    st.markdown("---")
    st.markdown(f'<div class="section-title">{t("✍️ Không Gian Nhập Liệu & Báo Cáo Ca Sản Xuất (Đồng Bộ Google Sheets)", "✍️ Direct Shift Data Entry Workspace (Sync to Google Sheets)")}</div>', unsafe_allow_html=True)
    c_inline_l, c_inline_r = st.columns([7, 3])
    with c_inline_l:
        st.caption(t(
            f"Nhập trực tiếp số liệu ca sản xuất cho ngày **{kpis.get('date_str', 'hôm nay')}** lên Google Sheets (Sheet `Product_Data`). Hệ thống sẽ tự động tính toán KPI và cập nhật toàn bộ biểu đồ tức thì.",
            f"Enter shift production data for **{kpis.get('date_str', 'today')}** directly to Google Sheets (`Product_Data`). Dashboard KPI metrics refresh instantly."
        ))
    with c_inline_r:
        if st.button(f"🚀 {t('MỞ PHÂN HỆ NHẬP SỐ LIỆU (4 TABS)', 'OPEN DATA ENTRY (4 TABS)')}", key="btn_jump_to_tab14_from_tab1_footer", type="primary", use_container_width=True):
            st.session_state['active_task'] = ENTRY_TASKS[0]
            st.rerun()

    has_shifts = bool(kpis.get('shift_details', []))
    exp_label = f"📝 {t('MỞ BIỂU MẪU NHẬP SỐ LIỆU CA CHO NGÀY', 'OPEN SHIFT PRODUCTION FORM FOR')} {kpis.get('date_str', 'HÔM NAY')}"
    with st.expander(exp_label, expanded=(not has_shifts)):
        c_user = get_current_user()
        if c_user is None:
            render_login_box("tab1_inline_login")
        else:
            if check_tab_permission(c_user.get('id', ''), 'san_xuat'):
                render_shift_production_form(app_loader or DataLoader(), c_user)
            else:
                render_permission_denied_card(t("Sản Xuất", "Production"), "san_xuat", c_user)

# ----------------- TAB KPI: ĐÁNH GIÁ & XẾP HẠNG KPI CA TRƯỞNG (FILE MỚI) -----------------
elif task_num == 2:
    c_kpi_head, c_kpi_btn = st.columns([7, 3])
    with c_kpi_head:
        st.markdown(f'<div class="section-title">{t("🎯 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI CA TRƯỞNG", "🎯 SHIFT LEADER KPI RANKING & PERFORMANCE")}</div>', unsafe_allow_html=True)
        st.caption(f"{t('Nguồn dữ liệu tích hợp:', 'Integrated Data Source:')} **{kpi_sheet_title}** (Google Sheets ID: `1M75tg_kZNxItv3VOlAjNi-RF63S_2NtxBMXSAxCRe14`)")
    with c_kpi_btn:
        if st.button(t("🔄 Cập Nhật Lại Điểm KPI", "🔄 Refresh KPI Scores"), help=t("Xóa cache và tải lại dữ liệu điểm KPI mới nhất từ Google Sheets", "Clear cache and reload latest KPI scores from Google Sheets"), use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 1. Bộ lọc chọn Tuần và Tháng cho Bảng Xếp Hạng Thi Đua (Toàn bộ 52 tuần & 12 tháng)
    available_kpi_weeks = ALL_WEEKS_52
    available_kpi_months = ALL_MONTHS_12

    def render_rank_cards(lb_items, period_name="tuần"):
        p_display = t("tuần", "week") if period_name in ["tuần", "week"] else (t("tháng", "month") if period_name in ["tháng", "month"] else period_name)
        if not lb_items:
            st.info(f"{t('Chưa có số liệu điểm KPI cho', 'No KPI score data available for')} {p_display}.")
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
            pts_unit = t("đ", "pts")
            if delta_val > 0:
                delta_badge = f'<span style="color:#15803d; font-size:12px; font-weight:700;">▲ +{delta_val:.2f} {pts_unit}</span>'
            elif delta_val < 0:
                delta_badge = f'<span style="color:#b91c1c; font-size:12px; font-weight:700;">▼ {delta_val:.2f} {pts_unit}</span>'
            else:
                delta_badge = f'<span style="color:#64748b; font-size:12px;">{t("kỳ đầu / giữ nguyên", "first period / unchanged")}</span>'

            c_bg = bg_colors.get(item['hang'], "#ffffff")
            c_bd = border_colors.get(item['hang'], "#e2e8f0")
            rank_label = translate_eval(rank_eval['rank'])

            st.markdown(f"""
            <div style="background:{c_bg}; border:1.5px solid {c_bd}; border-radius:12px; padding:14px 18px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <div>
                    <span style="font-size:28px; margin-right:10px;">{item['huy_chuong']}</span>
                    <strong style="font-size:19px; color:#0f172a;">{t('Ca', 'Shift')} {format_person_name(item['ca_truong'])}</strong>
                    <div style="font-size:12px; color:#64748b; margin-left:38px; margin-top:2px;">
                        {t('Hạng', 'Rank')} {item['hang']} • {delta_badge} {t(f'so với {period_name} trước', f'vs previous {p_display}')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:25px; font-weight:800; color:{rank_eval['color']};">{item['diem_kpi']:.2f}</span>
                    <span style="font-size:13px; color:#64748b;"> / 100{t('đ', 'pts')}</span>
                    <div style="font-size:12px; font-weight:700; color:{rank_eval['color']}; margin-top:2px;">
                        {rank_eval['icon']} {rank_label}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def render_component_breakdown(df_detail, period_label, chart_key=None):
        if df_detail.empty:
            st.info(f"{t('Chưa có dữ liệu cơ cấu chỉ số cho', 'No indicator structure data available for')} {period_label}.")
            return

        ca_colors = {
            'Ca A': '#16a34a',
            'Ca B': '#ea580c',
            'Ca C': '#2563eb',
            'Sắc': '#16a34a',
            'Tài': '#ea580c',
            'Long': '#2563eb',
        }
        pts_lbl = t("đ", "pts")

        # 3 ĐỒ THỊ ĐIỂM SỐ GOM 3 CA: ĐIỂM SẢN LƯỢNG (/50), ĐIỂM ĐỘ ẨM (/30), ĐIỂM NĂNG SUẤT (/20)
        c1, c2, c3 = st.columns(3)
        
        # --- ĐỒ THỊ 1: GOM ĐIỂM SẢN LƯỢNG CỦA 3 CA (THANG 50Đ) ---
        with c1:
            fig_sl_pts = go.Figure()
            for _, r in df_detail.iterrows():
                ca_name = format_person_name(str(r['ca_truong']))
                c_col = ca_colors.get(r['ca_truong'], '#2563eb')
                score_val = r.get('diem_sl', 0)
                sl_act = r.get('sl_thuc_te', 0)
                sl_tgt = r.get('chi_tieu_sl', 0)
                
                fig_sl_pts.add_trace(go.Bar(
                    x=[f"{t('Ca', 'Shift')} {ca_name}"],
                    y=[score_val],
                    name=f"{t('Ca', 'Shift')} {ca_name}",
                    text=[f"<b>{score_val:.1f} {pts_lbl}</b><br><span style='font-size:11px;'>({sl_act:,.0f}t / {sl_tgt:,.0f}t)</span>"],
                    textposition='outside',
                    marker_color=c_col,
                    showlegend=False
                ))
            
            fig_sl_pts.add_hline(
                y=50.0, 
                line_dash="dash", 
                line_color="#eab308",
                annotation_text=f"{t('Tối đa:', 'Max:')} 50 {pts_lbl}",
                annotation_position="top left"
            )
            fig_sl_pts.update_layout(
                title=dict(text=f"<b>1. {t('Điểm Sản Lượng', 'Output Score')} (/50) - {period_label}</b>", font=dict(size=13)),
                yaxis_title=t("Điểm số (/50)", "Score (/50)"),
                height=350,
                margin=dict(t=50, b=20, l=20, r=20),
                yaxis_range=[0, 58]
            )
            st.plotly_chart(fig_sl_pts, use_container_width=True, key=f"{chart_key}_sl_pts" if chart_key else None)

        # --- ĐỒ THỊ 2: GOM ĐIỂM ĐỘ ẨM CỦA 3 CA (THANG 30Đ) ---
        with c2:
            fig_moist_pts = go.Figure()
            for _, r in df_detail.iterrows():
                ca_name = format_person_name(str(r['ca_truong']))
                c_col = ca_colors.get(r['ca_truong'], '#0284c7')
                score_val = r.get('diem_am', 0)
                moist_val = r.get('do_am_tb', 0)
                
                fig_moist_pts.add_trace(go.Bar(
                    x=[f"{t('Ca', 'Shift')} {ca_name}"],
                    y=[score_val],
                    name=f"{t('Ca', 'Shift')} {ca_name}",
                    text=[f"<b>{score_val:.1f} {pts_lbl}</b><br><span style='font-size:11px;'>({t('Ẩm', 'Moist')}: {moist_val:.2f}%)</span>"],
                    textposition='outside',
                    marker_color=c_col,
                    showlegend=False
                ))
            
            fig_moist_pts.add_hline(
                y=30.0, 
                line_dash="dash", 
                line_color="#eab308",
                annotation_text=f"{t('Tối đa:', 'Max:')} 30 {pts_lbl}",
                annotation_position="top left"
            )
            fig_moist_pts.update_layout(
                title=dict(text=f"<b>2. {t('Điểm Độ Ẩm', 'Moisture Score')} (/30) - {period_label}</b>", font=dict(size=13)),
                yaxis_title=t("Điểm số (/30)", "Score (/30)"),
                height=350,
                margin=dict(t=50, b=20, l=20, r=20),
                yaxis_range=[0, 36]
            )
            st.plotly_chart(fig_moist_pts, use_container_width=True, key=f"{chart_key}_moist_pts" if chart_key else None)

        # --- ĐỒ THỊ 3: GOM ĐIỂM NĂNG SUẤT CỦA 3 CA (THANG 20Đ) ---
        with c3:
            fig_cap_pts = go.Figure()
            for _, r in df_detail.iterrows():
                ca_name = format_person_name(str(r['ca_truong']))
                c_col = ca_colors.get(r['ca_truong'], '#f59e0b')
                score_val = r.get('diem_nang_suat', 0)
                cap_val = r.get('nang_suat_tb', 0)
                
                fig_cap_pts.add_trace(go.Bar(
                    x=[f"{t('Ca', 'Shift')} {ca_name}"],
                    y=[score_val],
                    name=f"{t('Ca', 'Shift')} {ca_name}",
                    text=[f"<b>{score_val:.1f} {pts_lbl}</b><br><span style='font-size:11px;'>({t('NS', 'Rate')}: {cap_val:.2f} t/h)</span>"],
                    textposition='outside',
                    marker_color=c_col,
                    showlegend=False
                ))
            
            fig_cap_pts.add_hline(
                y=20.0, 
                line_dash="dash", 
                line_color="#eab308",
                annotation_text=f"{t('Tối đa:', 'Max:')} 20 {pts_lbl}",
                annotation_position="top left"
            )
            fig_cap_pts.update_layout(
                title=dict(text=f"<b>3. {t('Điểm Năng Suất', 'Productivity Score')} (/20) - {period_label}</b>", font=dict(size=13)),
                yaxis_title=t("Điểm số (/20)", "Score (/20)"),
                height=350,
                margin=dict(t=50, b=20, l=20, r=20),
                yaxis_range=[0, 24]
            )
            st.plotly_chart(fig_cap_pts, use_container_width=True, key=f"{chart_key}_cap_pts" if chart_key else None)

        # --- BẢNG ĐIỂM CHI TIẾT & SỐ LIỆU KỸ THUẬT THỰC TẾ ---
        with st.expander(f"📋 {t('Bảng Chi Tiết & 3 Đồ Thị Số Liệu Thực Tế (Tấn - % - Tấn/h)', 'Detailed Table & 3 Actual Metrics Charts (Tons - % - Tons/h)')} - {period_label}", expanded=True):
            cols_show = ['ca_truong', 'sl_thuc_te', 'chi_tieu_sl', 'diem_sl', 'do_am_tb', 'diem_am', 'nang_suat_tb', 'diem_nang_suat', 'dien_tb', 'diem_kpi']
            avail_cols = [c for c in cols_show if c in df_detail.columns]
            df_disp = df_detail[avail_cols].copy()
            
            if 'sl_thuc_te' in df_disp.columns and 'chi_tieu_sl' in df_disp.columns:
                df_disp['pct_sl'] = df_disp.apply(lambda r: f"{(r['sl_thuc_te'] / r['chi_tieu_sl'] * 100):.1f}%" if r['chi_tieu_sl'] > 0 else "-", axis=1)
                if 'pct_sl' not in avail_cols:
                    insert_idx = avail_cols.index('chi_tieu_sl') + 1 if 'chi_tieu_sl' in avail_cols else len(avail_cols)
                    avail_cols.insert(insert_idx, 'pct_sl')
                    df_disp = df_disp[avail_cols]

            if is_en():
                if 'ca_truong' in df_disp.columns:
                    df_disp['ca_truong'] = df_disp['ca_truong'].apply(lambda x: format_person_name(str(x)))
                col_names_map = {
                    'ca_truong': 'Shift Leader',
                    'sl_thuc_te': 'Actual Prod (t)',
                    'chi_tieu_sl': 'Target (t)',
                    'pct_sl': '% Target',
                    'diem_sl': 'Output Pts (/50)',
                    'do_am_tb': 'Avg Moist (%)',
                    'diem_am': 'Moist Pts (/30)',
                    'nang_suat_tb': 'Avg Press (t/h)',
                    'diem_nang_suat': 'Press Pts (/20)',
                    'dien_tb': 'Avg Power (kWh/t)',
                    'diem_kpi': 'TOTAL KPI PTS'
                }
            else:
                col_names_map = {
                    'ca_truong': 'Ca Trưởng',
                    'sl_thuc_te': 'SL Thực tế (tấn)',
                    'chi_tieu_sl': 'Chỉ Tiêu',
                    'pct_sl': 'Đạt CT',
                    'diem_sl': 'Đ.Sản Lượng (/50)',
                    'do_am_tb': 'Độ ẩm TB (%)',
                    'diem_am': 'Đ.Độ Ẩm (/30)',
                    'nang_suat_tb': 'Năng suất TB (t/h)',
                    'diem_nang_suat': 'Đ.Năng Suất (/20)',
                    'dien_tb': 'Điện TB (kWh/t)',
                    'diem_kpi': 'TỔNG ĐIỂM KPI'
                }
            df_disp.rename(columns=col_names_map, inplace=True)
            st.dataframe(df_disp, hide_index=True, use_container_width=True)

            # 3 Biểu đồ số liệu kỹ thuật thực tế hỗ trợ đối chiếu
            st.markdown("---")
            st.markdown(f"##### 📈 {t('Đối Chiếu Số Liệu Kỹ Thuật Thực Tế (Tấn - % - Tấn/h)', 'Actual Technical Metrics Comparison (Tons - % - Tons/h)')}")
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                fig_sl_raw = go.Figure()
                for _, r in df_detail.iterrows():
                    ca_name = format_person_name(str(r['ca_truong']))
                    c_col = ca_colors.get(r['ca_truong'], '#2563eb')
                    sl_act = r.get('sl_thuc_te', 0)
                    sl_tgt = r.get('chi_tieu_sl', 0)
                    pct = (sl_act / sl_tgt * 100) if sl_tgt > 0 else 0
                    fig_sl_raw.add_trace(go.Bar(
                        x=[f"{t('Ca', 'Shift')} {ca_name}"], y=[sl_act],
                        text=[f"<b>{sl_act:,.1f}t</b><br>({pct:.0f}%)"],
                        textposition='outside', marker_color=c_col, showlegend=False
                    ))
                mean_tgt = df_detail['chi_tieu_sl'].mean() if 'chi_tieu_sl' in df_detail.columns else 0
                if mean_tgt > 0:
                    fig_sl_raw.add_hline(y=mean_tgt, line_dash="dash", line_color="#94a3b8", annotation_text=f"{t('CT', 'Target')}: {mean_tgt:,.0f}t", annotation_position="top left")
                max_sl = df_detail['sl_thuc_te'].max() if not df_detail.empty else 100
                fig_sl_raw.update_layout(title=dict(text=f"<b>{t('Sản Lượng Thực Tế (Tấn)', 'Actual Production (Tons)')}</b>", font=dict(size=12)), yaxis_title=t("Tấn", "Tons"), height=280, margin=dict(t=40, b=20, l=15, r=15), yaxis_range=[0, max_sl * 1.28])
                st.plotly_chart(fig_sl_raw, use_container_width=True, key=f"{chart_key}_sl_raw" if chart_key else None)

            with cm2:
                fig_moist_raw = go.Figure()
                for _, r in df_detail.iterrows():
                    ca_name = format_person_name(str(r['ca_truong']))
                    c_col = ca_colors.get(r['ca_truong'], '#0284c7')
                    moist_val = r.get('do_am_tb', 0)
                    fig_moist_raw.add_trace(go.Bar(
                        x=[f"{t('Ca', 'Shift')} {ca_name}"], y=[moist_val],
                        text=[f"<b>{moist_val:.2f}%</b>"],
                        textposition='outside', marker_color=c_col, showlegend=False
                    ))
                fig_moist_raw.add_hline(y=9.0, line_dash="dash", line_color="#ef4444", annotation_text="Max 9.0%", annotation_position="top left")
                fig_moist_raw.add_hline(y=8.0, line_dash="dot", line_color="#10b981", annotation_text="Min 8.0%", annotation_position="bottom left")
                max_m = df_detail['do_am_tb'].max() if not df_detail.empty else 10
                fig_moist_raw.update_layout(title=dict(text=f"<b>{t('Độ Ẩm Thực Tế (%)', 'Actual Moisture (%)')}</b>", font=dict(size=12)), yaxis_title="%", height=280, margin=dict(t=40, b=20, l=15, r=15), yaxis_range=[0, max(11.5, max_m * 1.25)])
                st.plotly_chart(fig_moist_raw, use_container_width=True, key=f"{chart_key}_moist_raw" if chart_key else None)

            with cm3:
                fig_cap_raw = go.Figure()
                for _, r in df_detail.iterrows():
                    ca_name = format_person_name(str(r['ca_truong']))
                    c_col = ca_colors.get(r['ca_truong'], '#f59e0b')
                    cap_val = r.get('nang_suat_tb', 0)
                    fig_cap_raw.add_trace(go.Bar(
                        x=[f"{t('Ca', 'Shift')} {ca_name}"], y=[cap_val],
                        text=[f"<b>{cap_val:.2f} t/h</b>"],
                        textposition='outside', marker_color=c_col, showlegend=False
                    ))
                fig_cap_raw.add_hline(y=4.0, line_dash="dash", line_color="#16a34a", annotation_text=t("Chỉ tiêu ≥ 4.0 t/h", "Target ≥ 4.0 t/h"), annotation_position="top left")
                max_c = df_detail['nang_suat_tb'].max() if not df_detail.empty else 5
                fig_cap_raw.update_layout(title=dict(text=f"<b>{t('Năng Suất Ép Thực Tế (t/h)', 'Actual Press Productivity (t/h)')}</b>", font=dict(size=12)), yaxis_title=t("Tấn/h", "Tons/h"), height=280, margin=dict(t=40, b=20, l=15, r=15), yaxis_range=[0, max(5.2, max_c * 1.25)])
                st.plotly_chart(fig_cap_raw, use_container_width=True, key=f"{chart_key}_cap_raw" if chart_key else None)

    def render_leader_summary_cards(df_sub, period_label):
        if df_sub.empty:
            return
        st.markdown(f"##### 📋 {t('Chỉ Số Kỹ Thuật & Sản Xuất Thực Tế Từng Ca', 'Actual Production & Technical Metrics by Shift')} - {period_label}")
        c_ldrs = st.columns(min(3, len(df_sub)))
        for idx, (_, r_ldr) in enumerate(df_sub.iterrows()):
            if idx < len(c_ldrs):
                with c_ldrs[idx]:
                    pct_target = (r_ldr['sl_thuc_te'] / r_ldr['chi_tieu_sl'] * 100) if r_ldr.get('chi_tieu_sl', 0) > 0 else 0
                    kpi_val = r_ldr.get('diem_kpi', 0)
                    kpi_info = evaluate_kpi_score(kpi_val)
                    rank_str = translate_eval(kpi_info['rank'])
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:12px 16px; margin-bottom:12px; box-shadow:0 2px 5px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong style="font-size:18px; color:#0f172a;">{t('Ca', 'Shift')} {format_person_name(r_ldr['ca_truong'])}</strong>
                            <span style="background:#f1f5f9; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; color:#475569;">{r_ldr.get('so_ca', 0):.0f} {t('Ca Trực', 'Shifts')}</span>
                        </div>
                        <div style="font-size:13px; color:#334155; line-height:1.8;">
                            • <b>{t('Sản lượng', 'Output')}:</b> {r_ldr.get('sl_thuc_te', 0):,.1f} / {r_ldr.get('chi_tieu_sl', 0):,.0f} t ({pct_target:.1f}%)<br/>
                            • <b>{t('Suất điện TB', 'Avg Power')}:</b> {r_ldr.get('dien_tb', 0):.1f} kWh/{t('tấn', 'ton')}<br/>
                            • <b>{t('Năng suất ép', 'Press Productivity')}:</b> {r_ldr.get('nang_suat_tb', 0):.2f} {t('tấn/h', 't/h')}<br/>
                            • <b>{t('Độ ẩm viên', 'Pellet Moisture')}:</b> {r_ldr.get('do_am_tb', 0):.2f}%<br/>
                            • <b>{t('Tổng điểm KPI', 'Total KPI Score')}:</b> <span style="font-weight:800; color:{kpi_info['color']}; font-size:16px;">{kpi_val:.2f} {t('đ', 'pts')}</span> {kpi_info['medal']} ({rank_str})
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    df_leaders_w = leaders_kpi.get('weekly', pd.DataFrame())
    df_leaders_m = leaders_kpi.get('monthly', pd.DataFrame())

    # Các Tabs chuyên biệt cho Tuần và Tháng - Click chọn trực tiếp
    subtab_kpi_w, subtab_kpi_m, subtab_kpi_all = st.tabs([
        t("📅 BẢNG XẾP HẠNG KPI THEO TUẦN", "📅 WEEKLY KPI RANKING"),
        t("📆 BẢNG XẾP HẠNG KPI THEO THÁNG", "📆 MONTHLY KPI RANKING"),
        t("⚖️ XEM SONG SONG CẢ TUẦN & THÁNG", "⚖️ WEEK & MONTH SIDE-BY-SIDE")
    ])

    # ===== SUBTAB 1: KPI THEO TUẦN =====
    with subtab_kpi_w:
        st.markdown(f"### {t('📅 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI THEO TUẦN', '📅 WEEKLY SHIFT LEADER KPI EVALUATION & RANKING')}")
        col_w_pick, _ = st.columns([1, 1])
        with col_w_pick:
            sel_kpi_week = st.selectbox(
                t("📅 Click Chọn Tuần Đánh Giá KPI (Tuần 1 - 52):", "📅 Select KPI Evaluation Week (Week 1 - 52):"),
                options=available_kpi_weeks,
                index=default_w_idx,
                key="sb_kpi_week_tab"
            )
        lb_w = get_kpi_leaderboard(df_wm_weekly, df_wm_monthly, selected_week=sel_kpi_week)
        w_title = lb_w['weekly']['label'] if lb_w['weekly'] else (sel_kpi_week or t("Tuần", "Week"))

        st.markdown(f"#### 🏆 {t('Kết Quả Thi Đua Ca Trưởng:', 'Shift Leader Ranking Results:')} **{w_title}**")
        w_has_kpi = bool(lb_w['weekly'] and lb_w['weekly']['leaderboard'])
        if w_has_kpi:
            render_rank_cards(lb_w['weekly']['leaderboard'], "tuần")
        else:
            st.info(f"ℹ️ **{w_title}**: {t('Bảng điểm KPI chưa có dữ liệu chấm điểm thi đua.', 'No KPI evaluation data available.')}")

        df_w_sub = df_leaders_w[df_leaders_w['week_label'] == sel_kpi_week] if not df_leaders_w.empty else pd.DataFrame()
        if not df_w_sub.empty:
            render_leader_summary_cards(df_w_sub, w_title)
            st.markdown("---")
            st.markdown(f"#### 📊 {t('3 Đồ Thị So Sánh & Chỉ Số Chi Tiết (Sản Lượng - Độ Ẩm - Năng Suất Ép)', '3 Comparison Charts & Details (Output - Moisture - Press Productivity)')} - **{w_title}**")
            render_component_breakdown(df_w_sub, w_title, chart_key="comp_bar_week")
        else:
            # Kiểm tra xem df_shifts có dữ liệu ca cho tuần này không
            try:
                w_num = int(sel_kpi_week.replace("Tuần ", ""))
                w_shifts_kpi = df_shifts[df_shifts['date'].dt.isocalendar().week == w_num]
            except Exception:
                w_shifts_kpi = pd.DataFrame()

            if not w_shifts_kpi.empty:
                st.markdown(f"##### 📋 {t('Dữ Liệu Sản Xuất Thực Tế Từng Ca', 'Actual Production Data by Shift')} - {w_title} ({t('Từ Nhật Ký Ca Sản Xuất', 'From Shift Log')})")
                w_lead = get_shift_leader_kpis(w_shifts_kpi)
                if not w_lead.empty:
                    st.dataframe(translate_shift_leader_kpis(w_lead), hide_index=True, use_container_width=True)
            elif not w_has_kpi:
                st.caption(f"{t('Chưa có dữ liệu sản xuất ca trong', 'No shift production data in')} {sel_kpi_week}.")

        if not df_wm_weekly.empty:
            st.markdown("---")
            min_w_label = df_wm_weekly['week_label'].iloc[0] if not df_wm_weekly.empty else "Tuần 32"
            max_w_label = df_wm_weekly['week_label'].iloc[-1] if not df_wm_weekly.empty else "Tuần 38"
            st.markdown(f"#### 📈 {t('Diễn Biến Tổng Điểm KPI Ca Trưởng Qua Các Tuần', 'Shift Leader KPI Trend Across Weeks')} ({min_w_label} - {max_w_label})")
            fig_trend_w = go.Figure()
            colors_l = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c', 'Long': '#2563eb'}
            display_ca_map = {
                'Ca A': 'Ca A (Sắc)',
                'Ca B': 'Ca B (Tài)',
                'Ca C': 'Ca C (Long)',
                'Sắc': 'Ca Trưởng Sắc (Ca A)',
                'Tài': 'Ca Trưởng Tài (Ca B)',
                'Long': 'Ca Trưởng Long (Ca C)'
            }
            target_cas = ['Ca A', 'Ca B', 'Ca C'] if any(c in df_wm_weekly.columns for c in ['Ca A', 'Ca B', 'Ca C']) else ['Sắc', 'Tài', 'Long']
            for name in target_cas:
                if name in df_wm_weekly.columns:
                    lbl = display_ca_map.get(name, f'{t("Ca", "Shift")} {format_person_name(name)}')
                    fig_trend_w.add_trace(go.Scatter(
                        x=df_wm_weekly['week_label'],
                        y=df_wm_weekly[name],
                        mode='lines+markers+text',
                        name=lbl,
                        text=[f"{v:.1f}" if pd.notna(v) else "" for v in df_wm_weekly[name]],
                        textposition="top center",
                        line=dict(color=colors_l.get(name, '#64748b'), width=2.5)
                    ))
            fig_trend_w.update_layout(
                yaxis_title=t("Tổng Điểm KPI (/100)", "Total KPI Score (/100)"),
                height=350,
                hovermode="x unified",
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_trend_w, use_container_width=True, key="fig_trend_w_line")

    # ===== SUBTAB 2: KPI THEO THÁNG =====
    with subtab_kpi_m:
        st.markdown(f"### {t('📆 BẢNG ĐÁNH GIÁ & XẾP HẠNG THI ĐUA KPI THEO THÁNG', '📆 MONTHLY SHIFT LEADER KPI EVALUATION & RANKING')}")
        col_m_pick, _ = st.columns([1, 1])
        with col_m_pick:
            sel_kpi_month = st.selectbox(
                t("📆 Click Chọn Tháng Đánh Giá KPI (Tháng 1 - 12):", "📆 Select KPI Evaluation Month (Month 1 - 12):"),
                options=available_kpi_months,
                index=default_m_idx,
                key="sb_kpi_month_tab"
            )
        lb_m = get_kpi_leaderboard(df_wm_weekly, df_wm_monthly, selected_month=sel_kpi_month)
        m_title = lb_m['monthly']['label'] if lb_m['monthly'] else (sel_kpi_month or t("Tháng", "Month"))

        st.markdown(f"#### 👑 {t('Kết Quả Thi Đua Ca Trưởng:', 'Shift Leader Ranking Results:')} **{m_title}**")
        m_has_kpi = bool(lb_m['monthly'] and lb_m['monthly']['leaderboard'])
        if m_has_kpi:
            render_rank_cards(lb_m['monthly']['leaderboard'], "tháng")
        else:
            st.info(f"ℹ️ **{m_title}**: {t('Bảng điểm KPI chưa có dữ liệu chấm điểm thi đua.', 'No KPI evaluation data available.')}")

        df_m_sub = df_leaders_m[df_leaders_m['month_label'] == sel_kpi_month] if not df_leaders_m.empty else pd.DataFrame()
        if not df_m_sub.empty:
            render_leader_summary_cards(df_m_sub, m_title)
            st.markdown("---")
            st.markdown(f"#### 📊 {t('3 Đồ Thị So Sánh & Chỉ Số Chi Tiết (Sản Lượng - Độ Ẩm - Năng Suất Ép)', '3 Comparison Charts & Details (Output - Moisture - Press Productivity)')} - **{m_title}**")
            render_component_breakdown(df_m_sub, m_title, chart_key="comp_bar_month")
        else:
            # Kiểm tra xem df_shifts có dữ liệu ca cho tháng này không
            try:
                m_num = int(sel_kpi_month.replace("Tháng ", ""))
                m_shifts_kpi = df_shifts[df_shifts['date'].dt.month == m_num]
            except Exception:
                m_shifts_kpi = pd.DataFrame()

            if not m_shifts_kpi.empty:
                st.markdown(f"##### 📋 {t('Dữ Liệu Sản Xuất Thực Tế Từng Ca', 'Actual Production Data by Shift')} - {m_title} ({t('Từ Nhật Ký Ca Sản Xuất', 'From Shift Log')})")
                m_lead = get_shift_leader_kpis(m_shifts_kpi)
                if not m_lead.empty:
                    st.dataframe(translate_shift_leader_kpis(m_lead), hide_index=True, use_container_width=True)
            elif not m_has_kpi:
                st.caption(f"{t('Chưa có dữ liệu sản xuất ca trong', 'No shift production data in')} {sel_kpi_month}.")

        if not df_wm_monthly.empty:
            st.markdown("---")
            all_m_labels = " vs ".join(df_wm_monthly['month_label'].tolist()) if not df_wm_monthly.empty else "Tháng 8 vs Tháng 9"
            st.markdown(f"#### 📈 {t('So Sánh Tổng Điểm KPI Qua Các Tháng', 'KPI Score Comparison Across Months')} ({all_m_labels})")
            fig_trend_m = go.Figure()
            colors_l = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c', 'Long': '#2563eb'}
            display_ca_map = {
                'Ca A': 'Ca A (Sắc)',
                'Ca B': 'Ca B (Tài)',
                'Ca C': 'Ca C (Long)',
                'Sắc': 'Ca Trưởng Sắc (Ca A)',
                'Tài': 'Ca Trưởng Tài (Ca B)',
                'Long': 'Ca Trưởng Long (Ca C)'
            }
            target_cas = ['Ca A', 'Ca B', 'Ca C'] if any(c in df_wm_monthly.columns for c in ['Ca A', 'Ca B', 'Ca C']) else ['Sắc', 'Tài', 'Long']
            for name in target_cas:
                if name in df_wm_monthly.columns:
                    lbl = display_ca_map.get(name, f'{t("Ca", "Shift")} {format_person_name(name)}')
                    fig_trend_m.add_trace(go.Bar(
                        x=df_wm_monthly['month_label'],
                        y=df_wm_monthly[name],
                        name=lbl,
                        text=[f"{v:.2f} {t('đ', 'pts')}" if pd.notna(v) else "" for v in df_wm_monthly[name]],
                        textposition="outside",
                        marker_color=colors_l.get(name, '#64748b')
                    ))
            fig_trend_m.update_layout(
                barmode='group',
                yaxis_title=t("Tổng Điểm KPI (/100)", "Total KPI Score (/100)"),
                yaxis_range=[0, 110],
                height=350,
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_trend_m, use_container_width=True, key="fig_trend_m_bar")

    # ===== SUBTAB 3: XEM SONG SONG CẢ TUẦN & THÁNG =====
    with subtab_kpi_all:
        st.markdown(f"### {t('⚖️ ĐỐI CHIẾU SONG SONG KPI TUẦN VÀ THÁNG', '⚖️ WEEK & MONTH KPI SIDE-BY-SIDE COMPARISON')}")
        col_filter_w, col_filter_m = st.columns(2)
        with col_filter_w:
            sel_kpi_week_p = st.selectbox(
                t("📅 Click Chọn Tuần Đối Chiếu (Tuần 1 - 52):", "📅 Select Week to Compare (Week 1 - 52):"),
                options=available_kpi_weeks,
                index=default_w_idx,
                key="sb_kpi_week_parallel"
            )

        with col_filter_m:
            sel_kpi_month_p = st.selectbox(
                t("📆 Click Chọn Tháng Đối Chiếu (Tháng 1 - 12):", "📆 Select Month to Compare (Month 1 - 12):"),
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
            w_title_p = lb_p['weekly']['label'] if lb_p['weekly'] else (sel_kpi_week_p or t("Tuần", "Week"))
            st.markdown(f"#### 🏆 {t('Kết Quả Thi Đua:', 'Competition Results:')} **{w_title_p}**")
            if lb_p['weekly'] and lb_p['weekly']['leaderboard']:
                render_rank_cards(lb_p['weekly']['leaderboard'], "tuần")
            else:
                st.info(f"ℹ️ {w_title_p} {t('chưa có số liệu xếp hạng KPI.', 'has no KPI ranking data.')}")

        with col_lb_m:
            m_title_p = lb_p['monthly']['label'] if lb_p['monthly'] else (sel_kpi_month_p or t("Tháng", "Month"))
            st.markdown(f"#### 👑 {t('Kết Quả Thi Đua:', 'Competition Results:')} **{m_title_p}**")
            if lb_p['monthly'] and lb_p['monthly']['leaderboard']:
                render_rank_cards(lb_p['monthly']['leaderboard'], "tháng")
            else:
                st.info(f"ℹ️ {m_title_p} {t('chưa có số liệu xếp hạng KPI.', 'has no KPI ranking data.')}")

        st.markdown("---")
        st.markdown(f'<div class="section-title">{t("📊 3 Đồ Thị So Sánh & Chỉ Số Chi Tiết (Sản Lượng - Độ Ẩm - Năng Suất Ép)", "📊 3 Comparison Charts & Details (Output - Moisture - Press Productivity)")}</div>', unsafe_allow_html=True)
        tab_bd_w, tab_bd_m = st.tabs([f"📅 {t('Cơ Cấu', 'Breakdown')} {w_title_p}", f"📆 {t('Cơ Cấu', 'Breakdown')} {m_title_p}"])
        with tab_bd_w:
            df_w_sub_p = df_leaders_w[df_leaders_w['week_label'] == sel_kpi_week_p] if not df_leaders_w.empty else pd.DataFrame()
            if not df_w_sub_p.empty:
                render_component_breakdown(df_w_sub_p, w_title_p, chart_key="comp_bar_p_week")
            else:
                st.info(f"{t('Chưa có dữ liệu cơ cấu điểm cho', 'No score breakdown data available for')} {w_title_p}.")
        with tab_bd_m:
            df_m_sub_p = df_leaders_m[df_leaders_m['month_label'] == sel_kpi_month_p] if not df_leaders_m.empty else pd.DataFrame()
            if not df_m_sub_p.empty:
                render_component_breakdown(df_m_sub_p, m_title_p, chart_key="comp_bar_p_month")
            else:
                st.info(f"{t('Chưa có dữ liệu cơ cấu điểm cho', 'No score breakdown data available for')} {m_title_p}.")

    st.markdown("---")

    # 3. Biểu đồ so sánh 3 ca trưởng theo ngày
    st.markdown(f'<div class="section-title">{t("📈 Xu Hướng Đối Sánh Trực Tiếp 3 Ca Trưởng Theo Ngày", "📈 Daily Direct Comparison Trends of 3 Shift Leaders")}</div>', unsafe_allow_html=True)
    
    tab_c1, tab_c2, tab_c3, tab_c4 = st.tabs([
        t("⚡ Suất Điện Năng (kWh/tấn)", "⚡ Power Specific Rate (kWh/ton)"), 
        t("🚀 Năng Suất Ép (tấn/h)", "🚀 Press Productivity (t/h)"), 
        t("💧 Độ Ẩm Viên Nén (%)", "💧 Pellet Moisture (%)"),
        t("📦 Sản Lượng & Chỉ Tiêu (Tấn)", "📦 Actual Output & Target (Tons)")
    ])

    with tab_c1:
        if not df_chart_dien.empty:
            fig_cd = go.Figure()
            colors = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c', 'Long': '#2563eb'}
            display_ca_map = {
                'Ca A': 'Ca A (Sắc)',
                'Ca B': 'Ca B (Tài)',
                'Ca C': 'Ca C (Long)',
                'Sắc': 'Ca Trưởng Sắc (Ca A)',
                'Tài': 'Ca Trưởng Tài (Ca B)',
                'Long': 'Ca Trưởng Long (Ca C)'
            }
            target_cas = ['Ca A', 'Ca B', 'Ca C'] if any(c in df_chart_dien.columns for c in ['Ca A', 'Ca B', 'Ca C']) else ['Sắc', 'Tài', 'Long']
            for name in target_cas:
                if name in df_chart_dien.columns:
                    lbl = display_ca_map.get(name, f'{t("Ca", "Shift")} {format_person_name(name)}')
                    fig_cd.add_trace(go.Scatter(
                        x=df_chart_dien['date_str'], y=df_chart_dien[name],
                        mode='lines+markers', name=lbl,
                        line=dict(color=colors.get(name, '#64748b'), width=2)
                    ))
            # Đường line chuẩn 175 kWh/tấn (theo Danh mục mới)
            fig_cd.add_hline(y=175, line_dash="dash", line_color="red", annotation_text=t("Định mức 175 kWh/tấn", "Standard 175 kWh/ton"), annotation_position="top right")
            fig_cd.update_layout(
                title=t("Suất Tiêu Hao Điện Năng (kWh/tấn) Theo Ca (So Với Chuẩn 175)", "Specific Power Consumption (kWh/ton) by Shift (vs Std 175)"),
                xaxis_title=t("Ngày", "Date"), yaxis_title=t("kWh/tấn", "kWh/ton"), height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cd, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu biểu đồ điện năng ca.", "No shift power data available."))

    with tab_c2:
        if not df_chart_cap.empty:
            fig_cc = go.Figure()
            colors = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c', 'Long': '#2563eb'}
            display_ca_map = {
                'Ca A': 'Ca A (Sắc)',
                'Ca B': 'Ca B (Tài)',
                'Ca C': 'Ca C (Long)',
                'Sắc': 'Ca Trưởng Sắc (Ca A)',
                'Tài': 'Ca Trưởng Tài (Ca B)',
                'Long': 'Ca Trưởng Long (Ca C)'
            }
            target_cas = ['Ca A', 'Ca B', 'Ca C'] if any(c in df_chart_cap.columns for c in ['Ca A', 'Ca B', 'Ca C']) else ['Sắc', 'Tài', 'Long']
            for name in target_cas:
                if name in df_chart_cap.columns:
                    lbl = display_ca_map.get(name, f'{t("Ca", "Shift")} {format_person_name(name)}')
                    fig_cc.add_trace(go.Scatter(
                        x=df_chart_cap['date_str'], y=df_chart_cap[name],
                        mode='lines+markers', name=lbl,
                        line=dict(color=colors.get(name, '#64748b'), width=2)
                    ))
            fig_cc.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text=t("Chỉ tiêu ≥ 4.0 tấn/h", "Target ≥ 4.0 tons/h"), annotation_position="top left")
            fig_cc.update_layout(
                title=t("Năng Suất Ép Trung Bình (tấn/h) Theo Ca (So Với Chỉ Tiêu 4.0)", "Average Press Productivity (t/h) by Shift (vs Target 4.0)"),
                xaxis_title=t("Ngày", "Date"), yaxis_title=t("Tấn/giờ", "Tons/hour"), height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cc, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu biểu đồ năng suất ca.", "No shift productivity data available."))

    with tab_c3:
        if not df_chart_moist.empty:
            fig_cm = go.Figure()
            colors = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Tài': '#ea580c', 'Long': '#2563eb'}
            display_ca_map = {
                'Ca A': 'Ca A (Sắc)',
                'Ca B': 'Ca B (Tài)',
                'Ca C': 'Ca C (Long)',
                'Sắc': 'Ca Trưởng Sắc (Ca A)',
                'Tài': 'Ca Trưởng Tài (Ca B)',
                'Long': 'Ca Trưởng Long (Ca C)'
            }
            target_cas = ['Ca A', 'Ca B', 'Ca C'] if any(c in df_chart_moist.columns for c in ['Ca A', 'Ca B', 'Ca C']) else ['Sắc', 'Tài', 'Long']
            for name in target_cas:
                if name in df_chart_moist.columns:
                    lbl = display_ca_map.get(name, f'{t("Ca", "Shift")} {format_person_name(name)}')
                    fig_cm.add_trace(go.Scatter(
                        x=df_chart_moist['date_str'], y=df_chart_moist[name],
                        mode='lines+markers', name=lbl,
                        line=dict(color=colors.get(name, '#64748b'), width=2)
                    ))
            fig_cm.add_hline(y=9.0, line_dash="dash", line_color="red", annotation_text=t("Tiêu chuẩn 9.0%", "Standard 9.0%"), annotation_position="top right")
            fig_cm.update_layout(
                title=t("Độ Ẩm Trung Bình (%) Theo Ca (Dữ Liệu Đo Kiểm Data KCS)", "Average Moisture (%) by Shift (Data KCS)"),
                xaxis_title=t("Ngày", "Date"), yaxis_title="%", height=380, hovermode="x unified"
            )
            st.plotly_chart(fig_cm, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu biểu đồ độ ẩm ca.", "No shift moisture data available."))

    with tab_c4:
        if not df_chart_sl.empty:
            fig_csl = go.Figure()
            colors_actual = {'Ca A': '#16a34a', 'Ca B': '#ea580c', 'Ca C': '#2563eb', 'Sắc': '#16a34a', 'Sac': '#16a34a', 'Tài': '#ea580c', 'Tai': '#ea580c', 'Long': '#2563eb'}
            colors_target = {'Ca A': '#86efac', 'Ca B': '#fdba74', 'Ca C': '#93c5fd', 'Sắc': '#86efac', 'Sac': '#86efac', 'Tài': '#fdba74', 'Tai': '#fdba74', 'Long': '#93c5fd'}
            pairs = [
                ('Ca A', 'Ca A (Sắc)'),
                ('Ca B', 'Ca B (Tài)'),
                ('Ca C', 'Ca C (Long)')
            ] if any(f'{c}_actual' in df_chart_sl.columns for c in ['Ca A', 'Ca B', 'Ca C']) else [
                ('Sac', 'Ca Sắc (Ca A)'),
                ('Tai', 'Ca Tài (Ca B)'),
                ('Long', 'Ca Long (Ca C)')
            ]
            for code, name in pairs:
                act_col = f'{code}_actual'
                tgt_col = f'{code}_target'
                if act_col in df_chart_sl.columns:
                    fig_csl.add_trace(go.Bar(
                        x=df_chart_sl['date_str'], y=df_chart_sl[act_col],
                        name=f"{t('SL Thực Tế', 'Actual')} - {name}",
                        marker_color=colors_actual.get(code, '#16a34a')
                    ))
                if tgt_col in df_chart_sl.columns:
                    fig_csl.add_trace(go.Scatter(
                        x=df_chart_sl['date_str'], y=df_chart_sl[tgt_col],
                        mode='lines', name=f"{t('Chỉ Tiêu', 'Target')} - {name}",
                        line=dict(color=colors_target.get(code, '#86efac'), dash='dot', width=2)
                    ))
            fig_csl.update_layout(
                title=t("Sản Lượng Thực Tế vs Chỉ Tiêu Từng Ca (Từ Data KPI)", "Actual Output vs Target by Shift (From Data KPI)"),
                xaxis_title=t("Ngày", "Date"), yaxis_title=t("Tấn", "Tons"), height=380, hovermode="x unified",
                barmode='group'
            )
            st.plotly_chart(fig_csl, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu biểu đồ sản lượng ca.", "No shift output data available."))

    # 4. Bảng tổng hợp điểm các tuần
    st.markdown(f'<div class="section-title">{t("📋 Bảng Tổng Hợp Điểm Thi Đua Các Tuần & Tháng (W-M KPI)", "📋 Weekly & Monthly KPI Ranking Summary Tables (W-M KPI)")}</div>', unsafe_allow_html=True)
    c_wm1, c_wm2 = st.columns(2)
    with c_wm1:
        st.markdown(f"##### 📅 {t('Điểm Thi Đua Các Tuần (W-M KPI)', 'Weekly KPI Scores (W-M KPI)')}")
        if not df_wm_weekly.empty:
            st.dataframe(translate_wm_weekly(df_wm_weekly), hide_index=True, use_container_width=True)
    with c_wm2:
        st.markdown(f"##### 📆 {t('Điểm Thi Đua Các Tháng (W-M KPI)', 'Monthly KPI Scores (W-M KPI)')}")
        if not df_wm_monthly.empty:
            st.dataframe(translate_wm_monthly(df_wm_monthly), hide_index=True, use_container_width=True)



# ----------------- TAB 2: XU HƯỚNG TUẦN & THÁNG -----------------
elif task_num == 3:
    st.markdown(f'<div class="section-title">{t("📈 Xu Hướng & Cảnh Báo Định Mức Điện Năng (kWh/tấn)", "📈 Electricity Benchmark Trends & Warnings (kWh/ton)")}</div>', unsafe_allow_html=True)
    
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
        name=t('Suất điện thực tế (kWh/tấn)', 'Actual Power Rate (kWh/ton)'),
        line=dict(color='#2563eb', width=3),
        marker=dict(size=6)
    ))

    # Giới hạn trên 175
    fig_elec_trend.add_hline(
        y=ELEC_MAX_BENCHMARK,
        line_dash="dash",
        line_color="#dc2626",
        annotation_text=f"{t('Mức trần chuẩn', 'Standard Ceiling')} ({ELEC_MAX_BENCHMARK} kWh/{t('tấn', 'ton')})",
        annotation_position="top right"
    )

    # Giới hạn dưới 170
    fig_elec_trend.add_hline(
        y=ELEC_MIN_BENCHMARK,
        line_dash="dash",
        line_color="#16a34a",
        annotation_text=f"{t('Mức sàn chuẩn', 'Standard Floor')} ({ELEC_MIN_BENCHMARK} kWh/{t('tấn', 'ton')})",
        annotation_position="bottom right"
    )

    # Vùng đạt chuẩn (170 - 175)
    fig_elec_trend.add_hrect(
        y0=ELEC_MIN_BENCHMARK, y1=ELEC_MAX_BENCHMARK,
        fillcolor="#10b981", opacity=0.1, line_width=0
    )

    fig_elec_trend.update_layout(
        title=t("Biểu Đồ Theo Dõi Suất Tiêu Hao Điện Năng Theo Ngày (So Với Khung Chuẩn 170 - 175 kWh/tấn)", "Daily Electricity Consumption Rate vs Benchmark (170 - 175 kWh/ton)"),
        xaxis_title=t("Ngày", "Date"),
        yaxis_title=t("kWh/tấn", "kWh/ton"),
        hovermode="x unified",
        height=380,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_elec_trend, use_container_width=True)

    # Biểu đồ năng suất ép vs mục tiêu 4.0 tấn/h
    st.markdown(f'<div class="section-title">{t("⚡ Xu Hướng Năng Suất Ép (tấn/h) So Với Chỉ Tiêu (≥ 4.0 tấn/h)", "⚡ Pellet Mill Productivity Trend (tons/h) vs Target (≥ 4.0 tons/h)")}</div>', unsafe_allow_html=True)
    
    fig_prod_trend = go.Figure()
    fig_prod_trend.add_trace(go.Scatter(
        x=df_day_trend['date'],
        y=df_day_trend['tph'],
        mode='lines+markers',
        name=t('Năng suất ép (tấn/h)', 'Pellet Productivity (tons/h)'),
        line=dict(color='#0d9488', width=3),
        marker=dict(size=6)
    ))
    fig_prod_trend.add_hline(
        y=PRODUCTIVITY_TARGET,
        line_dash="dash",
        line_color="#e11d48",
        annotation_text=f"{t('Chỉ tiêu tối thiểu', 'Min Target')} (≥ {PRODUCTIVITY_TARGET} {t('tấn/h', 'tons/h')})",
        annotation_position="top left"
    )
    fig_prod_trend.update_layout(
        title=t("Biểu Đồ Năng Suất Ép Trung Bình Theo Ngày", "Daily Average Pellet Mill Productivity"),
        xaxis_title=t("Ngày", "Date"),
        yaxis_title=t("Tấn/giờ (TPH)", "Tons/hour (TPH)"),
        hovermode="x unified",
        height=340,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_prod_trend, use_container_width=True)

    # Báo cáo Tuần & Tháng
    col_w, col_m = st.columns(2)
    with col_w:
        st.markdown(f"##### 📅 {t('Báo Cáo Tuần (Weekly Report)', 'Weekly Report')}")
        sel_w_rep = st.selectbox(
            t("📅 Click chọn tuần xem chi tiết (Tuần 1 - 52):", "📅 Select week for details (Week 1 - 52):"),
            options=ALL_WEEKS_52,
            index=default_w_idx,
            key="sb_week_rep_tab2"
        )
        row_w_df = df_weekly[df_weekly['week_label'] == sel_w_rep] if not df_weekly.empty else pd.DataFrame()
        if not row_w_df.empty:
            r_w_val = row_w_df.iloc[0]
            cw1, cw2, cw3, cw4 = st.columns(4)
            cw1.metric(t("Sản Lượng", "Output"), f"{r_w_val.get('san_luong_tan', 0):,.1f} {t('t', 'tons')}")
            cw2.metric(t("Suất Điện", "Power Rate"), f"{r_w_val.get('dien_tb_kwh_tan', 0):.1f} kWh/{t('t', 'ton')}")
            cw3.metric(t("Năng Suất Ép", "Pellet Productivity"), f"{r_w_val.get('nang_suat_ep_tph', 0):.2f} {t('t/h', 'tons/h')}")
            cw4.metric(t("Dầu Diezen", "Diesel Fuel"), f"{r_w_val.get('diezen_lit', 0):,.0f} L")
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
                cw1.metric(t("Sản Lượng (Ca)", "Shift Output"), f"{w_tot_out:,.1f} {t('t', 'tons')}")
                cw2.metric(t("Suất Điện TB", "Avg Power Rate"), f"{w_avg_e:.1f} kWh/{t('t', 'ton')}")
                cw3.metric(t("Năng Suất Ép TB", "Avg Productivity"), f"{w_avg_p:.2f} {t('t/h', 'tons/h')}")
            else:
                st.info(f"ℹ️ {sel_w_rep} " + t("chưa có dữ liệu sản xuất.", "has no production data."))

        if not df_weekly.empty:
            fig_w = px.bar(
                df_weekly,
                x='week_label',
                y='san_luong_tan',
                text='san_luong_tan',
                title=t("Sản Lượng Theo Tuần (Tấn)", "Weekly Output (Tons)"),
                color_discrete_sequence=['#3b82f6']
            )
            fig_w.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_w.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20), xaxis_title=t("Tuần", "Week"), yaxis_title=t("Tấn", "Tons"))
            st.plotly_chart(fig_w, use_container_width=True, key="fig_w_tab2_bar")
            df_w_disp = df_weekly[['week_label', 'san_luong_tan', 'dien_tb_kwh_tan', 'nang_suat_ep_tph', 'diezen_lit', 'do_tro_pct']].tail(6).copy()
            if is_en():
                df_w_disp.rename(columns={'week_label': 'Week', 'san_luong_tan': 'Output (t)', 'dien_tb_kwh_tan': 'Power (kWh/t)', 'nang_suat_ep_tph': 'Productivity (t/h)', 'diezen_lit': 'Diesel (L)', 'do_tro_pct': 'Ash (%)'}, inplace=True)
            else:
                df_w_disp.rename(columns={'week_label': 'Tuần', 'san_luong_tan': 'Sản lượng (t)', 'dien_tb_kwh_tan': 'Điện TB (kWh/t)', 'nang_suat_ep_tph': 'Năng suất ép (t/h)', 'diezen_lit': 'Dầu (L)', 'do_tro_pct': 'Độ tro (%)'}, inplace=True)
            st.dataframe(df_w_disp, hide_index=True)

    with col_m:
        st.markdown(f"##### 📆 {t('Báo Cáo Tháng (Monthly Report)', 'Monthly Report')}")
        sel_m_rep = st.selectbox(
            t("📆 Click chọn tháng xem chi tiết (Tháng 1 - 12):", "📆 Select month for details (Month 1 - 12):"),
            options=ALL_MONTHS_CODE_12,
            index=default_m_code_idx,
            key="sb_month_rep_tab2"
        )
        row_m_df = df_monthly[df_monthly['month_label'] == sel_m_rep] if not df_monthly.empty else pd.DataFrame()
        if not row_m_df.empty:
            r_val = row_m_df.iloc[0]
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric(t("Sản Lượng", "Output"), f"{r_val.get('san_luong_tan', 0):,.1f} {t('t', 'tons')}")
            cm2.metric(t("Suất Điện", "Power Rate"), f"{r_val.get('dien_tb_kwh_tan', 0):.1f} kWh/{t('t', 'ton')}")
            cm3.metric(t("Năng Suất Ép", "Pellet Productivity"), f"{r_val.get('nang_suat_ep_tph', 0):.2f} {t('t/h', 'tons/h')}")
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
                m_avg_e = w_tot_kwh / m_tot_out if m_tot_out > 0 else 0.0
                m_avg_p = m_tot_out / m_tot_h if m_tot_h > 0 else 0.0
                cm1, cm2, cm3 = st.columns(3)
                cm1.metric(t("Sản Lượng (Ca)", "Shift Output"), f"{m_tot_out:,.1f} {t('t', 'tons')}")
                cm2.metric(t("Suất Điện TB", "Avg Power Rate"), f"{m_avg_e:.1f} kWh/{t('t', 'ton')}")
                cm3.metric(t("Năng Suất Ép TB", "Avg Productivity"), f"{m_avg_p:.2f} {t('t/h', 'tons/h')}")
            else:
                st.info(f"ℹ️ {t('Tháng', 'Month')} {sel_m_rep} " + t("chưa có dữ liệu sản xuất.", "has no production data."))

        if not df_monthly.empty:
            fig_m = px.bar(
                df_monthly,
                x='month_label',
                y='san_luong_tan',
                text='san_luong_tan',
                title=t("Sản Lượng Theo Tháng (Tấn)", "Monthly Output (Tons)"),
                color_discrete_sequence=['#8b5cf6']
            )
            fig_m.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_m.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20), xaxis_title=t("Tháng", "Month"), yaxis_title=t("Tấn", "Tons"))
            st.plotly_chart(fig_m, use_container_width=True, key="fig_m_tab2_bar")
            df_m_disp = df_monthly[['month_label', 'san_luong_tan', 'dien_tb_kwh_tan', 'nang_suat_ep_tph', 'do_tro_pct']].tail(6).copy()
            if is_en():
                df_m_disp.rename(columns={'month_label': 'Month', 'san_luong_tan': 'Output (t)', 'dien_tb_kwh_tan': 'Power (kWh/t)', 'nang_suat_ep_tph': 'Productivity (t/h)', 'do_tro_pct': 'Ash (%)'}, inplace=True)
            else:
                df_m_disp.rename(columns={'month_label': 'Tháng', 'san_luong_tan': 'Sản lượng (t)', 'dien_tb_kwh_tan': 'Điện TB (kWh/t)', 'nang_suat_ep_tph': 'Năng suất ép (t/h)', 'do_tro_pct': 'Độ tro (%)'}, inplace=True)
            st.dataframe(df_m_disp, hide_index=True)

# ----------------- TAB 3: GIÁM SÁT CỤM THIẾT BỊ -----------------
elif task_num == 4:
    st.markdown(f'<div class="section-title">{t("🛠️ Bảng Thống Kê Giờ Hoạt Động Cụm Thiết Bị Toàn Nhà Máy", "🛠️ Plant-wide Equipment Operating Hours Statistics")}</div>', unsafe_allow_html=True)
    
    df_eq_stats = get_equipment_statistics(df_shifts)
    if not df_eq_stats.empty:
        df_eq_disp = df_eq_stats.copy()
        if is_en():
            df_eq_disp.rename(columns={
                'Cụm thiết bị': 'Equipment Group',
                'Mã TB': 'Tag',
                'Tên thiết bị': 'Equipment Name',
                'Công suất (kW)': 'Power (kW)',
                'Hãng / Chủng loại': 'Make / Type',
                'Tổng giờ chạy (h)': 'Total Hours (h)',
                'Tỷ lệ sử dụng (%)': 'Utilization (%)'
            }, inplace=True)
            prog_col = "Utilization (%)"
        else:
            prog_col = "Tỷ lệ sử dụng (%)"

        st.dataframe(
            df_eq_disp,
            use_container_width=True,
            hide_index=True,
            column_config={
                prog_col: st.column_config.ProgressColumn(
                    prog_col,
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
                title=t("Tổng Giờ Hoạt Động Của Từng Máy Ép (PE1 - PE8)", "Total Operating Hours of Pellet Mills (PE1 - PE8)")
            )
            fig_pe_comp.update_traces(texttemplate='%{text:,.0f}h', textposition='outside')
            fig_pe_comp.update_layout(height=360, xaxis_title=t("Máy ép", "Pellet Mill"), yaxis_title=t("Giờ chạy (h)", "Run Hours (h)"))
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
                title=t("Giờ Hoạt Động Máy Nghiền Búa (Andritz vs SHT)", "Hammer Mill Operating Hours (Andritz vs SHT)")
            )
            fig_hm_comp.update_traces(texttemplate='%{text:,.0f}h', textposition='outside')
            fig_hm_comp.update_layout(height=360, xaxis_title=t("Máy nghiền", "Hammer Mill"), yaxis_title=t("Giờ chạy (h)", "Run Hours (h)"))
            st.plotly_chart(fig_hm_comp, use_container_width=True)

# ----------------- TAB INCIDENTS: QUẢN LÝ & CẢNH BÁO SỰ CỐ THIẾT BỊ -----------------
elif task_num == 5:
    st.markdown(f'<div class="section-title">{t("🚨 HỆ THỐNG QUẢN LÝ & CẢNH BÁO SỰ CỐ THIẾT BỊ (SHEET SỰ CỐ)", "🚨 EQUIPMENT INCIDENT MANAGEMENT & ALERTS (INCIDENTS SHEET)")}</div>', unsafe_allow_html=True)
    st.caption(t("Dữ liệu tự động từ sheet `Su co` - Thống kê sự cố hàng ngày & hàng tuần, vẽ biểu đồ và bật cảnh báo cho các thiết bị.", "Automated data from `Su co` sheet - Daily & weekly incident statistics, charts, and proactive machine alerts."))

    if not df_incidents.empty:
        # Bộ lọc chu kỳ cho Sự Cố: Ngày, Tuần, Tháng hoặc Toàn bộ
        col_inc_mode, col_inc_sel = st.columns([1, 2])
        with col_inc_mode:
            inc_modes = [
                t("📅 Theo Tuần (52 tuần)", "📅 By Week (52 weeks)"),
                t("📆 Theo Tháng (12 tháng)", "📆 By Month (12 months)"),
                t("📅 Theo Ngày Cụ Thể", "📅 By Specific Date"),
                t("Toàn bộ lịch sử", "Full History")
            ]
            inc_filter_mode = st.radio(
                t("Bộ lọc thời gian sự cố:", "Incident Time Filter:"),
                inc_modes,
                index=0,
                key="inc_filter_mode_radio"
            )

        target_inc_w = None
        target_inc_m = None
        target_inc_d = None

        with col_inc_sel:
            if "Tuần" in inc_filter_mode or "Week" in inc_filter_mode:
                target_inc_w = st.selectbox(t("Chọn tuần xem sự cố:", "Select week to view incidents:"), ALL_WEEKS_52, index=default_w_idx, key="sb_inc_week")
            elif "Tháng" in inc_filter_mode or "Month" in inc_filter_mode:
                target_inc_m = st.selectbox(t("Chọn tháng xem sự cố:", "Select month to view incidents:"), ALL_MONTHS_CODE_12, index=default_m_code_idx, key="sb_inc_month")
            elif "Ngày" in inc_filter_mode or "Date" in inc_filter_mode:
                inc_dates = [d for d in df_incidents['date_str'].unique() if d]
                target_inc_d = st.selectbox(t("Chọn ngày xem sự cố:", "Select date to view incidents:"), inc_dates, index=len(inc_dates)-1 if inc_dates else 0, key="sb_inc_day")

        # Tính toán thống kê & cảnh báo
        inc_stats = get_incident_statistics(df_incidents, target_date=target_inc_d, target_week=target_inc_w, target_month=target_inc_m)
        alerts_list = get_equipment_incident_alerts(df_incidents, target_week=target_inc_w, target_date=target_inc_d)

        # --- KHU VỰC BẬT CẢNH BÁO CHO CÁC THIẾT BỊ (ALERTS) ---
        st.markdown("---")
        st.markdown(f"#### {t('⚡ HỆ THỐNG CẢNH BÁO THIẾT BỊ HƯ HỎNG & BẢO TRÌ SỰ CỐ', '⚡ EQUIPMENT FAILURE ALERTS & BREAKDOWN MAINTENANCE')}")
        
        red_alerts = [a for a in alerts_list if a['severity'] == 'RED']
        yellow_alerts = [a for a in alerts_list if a['severity'] == 'YELLOW']

        if red_alerts:
            st.error(t(f"🚨 **PHÁT HIỆN {len(red_alerts)} THIẾT BỊ BÁO ĐỘNG ĐỎ VỀ SỰ CỐ!** Cần can thiệp bảo trì khẩn cấp hoặc rà soát chế độ vận hành.", f"🚨 **DETECTED {len(red_alerts)} EQUIPMENT WITH RED ALERTS!** Urgent maintenance intervention or operational review required."))
        elif yellow_alerts:
            st.warning(t(f"⚠️ **CẢNH BÁO:** Có {len(yellow_alerts)} thiết bị ghi nhận sự cố lặp lại. Cần theo dõi kiểm tra ca tiếp.", f"⚠️ **WARNING:** {len(yellow_alerts)} machines recorded recurring issues. Monitor closely on next shift."))
        else:
            st.success(t("✅ **AN TOÀN:** Không ghi nhận sự cố nghiêm trọng trên các cụm máy trong kỳ được chọn.", "✅ **SAFE:** No severe incidents recorded across machines during selected period."))

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

                    lbl_eq = t("Thiết bị:", "Equipment:")
                    lbl_st = t("Trạng thái:", "Status:")
                    lbl_iss = t("Hiện tượng / Sự cố:", "Symptom / Incident:")
                    lbl_rec = t("Thời gian ghi nhận:", "Logged at:")

                    st.markdown(f"""
                    <div style="background:{bg_color}; border:1.5px solid {border_color}; border-radius:10px; padding:12px 16px; margin-bottom:12px; box-shadow:0 2px 5px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong style="font-size:17px; color:#0f172a;">{al['icon']} {lbl_eq} <code>{al['equipment']}</code></strong>
                            <span style="{badge_style} padding:3px 8px; border-radius:6px; font-size:12px; font-weight:700;">{al['level_label']}</span>
                        </div>
                        <div style="font-size:13px; color:#1e293b; line-height:1.6;">
                            <b>{lbl_st}</b> {al['message']}<br/>
                            <b>{lbl_iss}</b><br/>{issues_html}<br/>
                            <span style="font-size:11px; color:#64748b;">{lbl_rec} {dates_html}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        # 4 Thẻ KPI Sự Cố
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        with c_i1:
            st.metric(t("Tổng Số Vụ Sự Cố", "Total Incidents"), f"{inc_stats['total_incidents']} " + t("vụ", "cases"))
        with c_i2:
            st.metric(t("Tổng Giờ Dừng Máy", "Total Downtime"), f"{inc_stats['total_hours']} " + t("giờ", "hrs"))
        with c_i3:
            st.metric(t("Số Vụ Bảo Trì Sự Cố", "Breakdown Maintenance"), f"{inc_stats['breakdown_count']} " + t("vụ", "cases"), f"{inc_stats['proactive_count']} " + t("chủ động", "proactive"))
        with c_i4:
            st.metric(t("Tỷ Lệ Xử Lý Hoàn Thành", "Resolution Rate"), f"{inc_stats['completion_rate']}%", f"{inc_stats['pending_count']} " + t("chưa xong", "pending"))

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
                    title=t("Top Thiết Bị Phát Sinh Sự Cố Nhiều Nhất", "Top Incident-Prone Equipment")
                )
                fig_eq_inc.update_traces(textposition='outside')
                fig_eq_inc.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20), xaxis_title=t("Mã Thiết Bị", "Equipment Tag"), yaxis_title=t("Số Vụ", "Incidents"))
                st.plotly_chart(fig_eq_inc, use_container_width=True, key="fig_eq_inc_bar")
            else:
                st.info(t("Không có sự cố thiết bị trong kỳ này.", "No equipment incidents during this period."))

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
                    title=t("Các Nguyên Nhân / Hiện Tượng Sự Cố Phổ Biến", "Common Incident Causes / Symptoms")
                )
                fig_cause.update_traces(textposition='outside')
                fig_cause.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20), yaxis=dict(autorange="reversed"), xaxis_title=t("Số Lần", "Count"), yaxis_title="")
                st.plotly_chart(fig_cause, use_container_width=True, key="fig_cause_bar")
            else:
                st.info(t("Không có dữ liệu nguyên nhân sự cố.", "No incident cause data available."))

        # Thống kê theo ca trưởng & Danh sách sự cố chi tiết
        c_ldr_inc, c_tbl_inc = st.columns([1, 2])
        with c_ldr_inc:
            df_ldr_st = inc_stats['leader_stats']
            if not df_ldr_st.empty:
                st.markdown(f"##### 👤 {t('Sự Cố Theo Ca Trưởng Trực', 'Incidents by Shift Leader on Duty')}")
                fig_ldr_inc = px.pie(
                    df_ldr_st,
                    names='Ca Trưởng Trực',
                    values='Số Vụ Sự Cố',
                    title=t("Tỷ Trọng Sự Cố Giữa Các Ca", "Incident Share Across Shifts"),
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_ldr_inc.update_layout(height=280, margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig_ldr_inc, use_container_width=True, key="fig_ldr_inc_pie")

        with c_tbl_inc:
            st.markdown(f"##### 📋 {t('Bảng Chi Tiết Các Vụ Sự Cố Đã Ghi Nhận', 'Detailed Incident Log Table')}")
            df_show_inc = inc_stats['df_filtered']
            if global_search_kw and not df_show_inc.empty:
                inc_match = search_df(df_show_inc, global_search_kw)
                if not inc_match.empty:
                    df_show_inc = inc_match
            if not df_show_inc.empty:
                cols_inc_disp = ['id_su_co', 'date_str', 'shift_leader', 'equipment_raw', 'description', 'solution', 'performer', 'duration_hours', 'status']
                avail_c_inc = [c for c in cols_inc_disp if c in df_show_inc.columns]
                df_disp_inc = df_show_inc[avail_c_inc].copy()
                if is_en():
                    df_disp_inc.rename(columns={
                        'id_su_co': 'ID',
                        'date_str': 'Date',
                        'shift_leader': 'Shift Leader',
                        'equipment_raw': 'Equipment Tag',
                        'description': 'Description',
                        'solution': 'Corrective Action',
                        'performer': 'Assignee',
                        'duration_hours': 'Downtime (h)',
                        'status': 'Status'
                    }, inplace=True)
                else:
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
                st.info(t("Không có bản ghi sự cố nào.", "No incident records found."))
    else:
        st.info(t("Chưa có dữ liệu từ sheet 'Su co'.", "No data from sheet 'Su co'."))

# ----------------- TAB MAINT LOG: NHẬT KÝ BẢO TRÌ & SỬA CHỮA (2026 BẢO TRÌ BVN) -----------------
elif task_num == 6:
    st.markdown(f'<div class="section-title">{t("🔧 BÁO CÁO ĐỊNH KỲ, NHẬT KÝ BẢO TRÌ & QUẢN TRỊ TPM (MANINTERNANCE BVNQB)", "🔧 PERIODIC REPORTS, MAINTENANCE LOG & TPM MANAGEMENT (MANINTERNANCE BVNQB)")}</div>', unsafe_allow_html=True)
    st.caption(f"{t('Nguồn dữ liệu:', 'Data source:')} **{maint_log_title}** (Google Sheets ID: `1hInwQQgN3zXWFEXC1qaFgaXeIiogXUJtm0cPgP3PlX8` | GID: `1631161446`)")

    maint_tab1, maint_tab2, maint_tab3, maint_tab4 = st.tabs([
        t("📊 BÁO CÁO ĐỊNH KỲ (MONTHLY / WEEKLY / DAILY)", "📊 PERIODIC REPORTS (MONTHLY / WEEKLY / DAILY)"),
        t("🔧 NHẬT KÝ BẢO TRÌ CHI TIẾT (SHEET DATA)", "🔧 DETAILED MAINTENANCE LOG (DATA SHEET)"),
        t("🚀 QUẢN TRỊ TPM & CẢI TIẾN (TPM & IMPROVEMENTS)", "🚀 TPM & IMPROVEMENT MANAGEMENT"),
        t("🛢️ KIỂM ĐỊNH MỠ BÔI TRƠN MÁY ÉP (PM30-6)", "🛢️ PELLET MILL GREASE DOSING CHECK (PM30-6)")
    ])

    # -------------------------------------------------------------
    # SUBTAB 1: BÁO CÁO ĐỊNH KỲ (TƯƠNG ỨNG SHEET MONTHLY_REPORT GID 1631161446)
    # -------------------------------------------------------------
    with maint_tab1:
        st.markdown(f"#### 📊 {t('BÁO CÁO BẢO TRÌ & SỰ CỐ TỔNG HỢP (MONTHLY / WEEKLY / DAILY)', 'SYNTHESIZED MAINTENANCE & INCIDENT REPORT')}")
        st.caption(t("Báo cáo tương thích trực tiếp với trang Google Sheets `Monthly_Report` (GID: 1631161446), `Weekly_Report` và `Daily_Report`.", "Report directly compatible with Google Sheets `Monthly_Report` (GID: 1631161446), `Weekly_Report`, and `Daily_Report`."))

        c_rep_type, c_rep_sel = st.columns([1, 2])
        with c_rep_type:
            rep_type = st.radio(
                t("Chọn chu kỳ báo cáo:", "Select report period:"),
                [
                    t("📆 Theo Tháng (Monthly Report)", "📆 Monthly Report"),
                    t("📅 Theo Tuần (Weekly Report)", "📅 Weekly Report"),
                    t("☀️ Theo Ngày (Daily Report)", "☀️ Daily Report")
                ],
                key="sb_maint_rep_type"
            )

        # Lọc dữ liệu theo chu kỳ được chọn
        df_inc_sub = df_incidents.copy() if not df_incidents.empty else pd.DataFrame()
        df_ml_sub = df_maint_log.copy() if not df_maint_log.empty else pd.DataFrame()

        period_title = ""

        with c_rep_sel:
            if "Tháng" in rep_type or "Monthly" in rep_type:
                available_months = sorted(list(set(
                    ([int(m) for m in df_ml_sub['month'].dropna().unique() if int(m) > 0] if not df_ml_sub.empty and 'month' in df_ml_sub else []) +
                    ([int(m) for m in df_inc_sub['month'].dropna().unique() if int(m) > 0] if not df_inc_sub.empty and 'month' in df_inc_sub else [])
                )))
                if not available_months:
                    available_months = [2, 5, 6, 7, 8, 9]
                month_opts = [f"Tháng {int(m)}" for m in available_months]
                def_m_idx = len(month_opts) - 1
                sel_m_str = st.selectbox(t("Chọn Tháng báo cáo:", "Select reporting month:"), month_opts, index=def_m_idx, key="sb_maint_month_pick")
                m_match = re.search(r'\d+', sel_m_str)
                sel_m_num = int(m_match.group()) if m_match else 9
                period_title = f"{t('Tháng', 'Month')} {sel_m_num}"

                if not df_inc_sub.empty and 'month' in df_inc_sub:
                    df_inc_sub = df_inc_sub[df_inc_sub['month'] == sel_m_num]
                if not df_ml_sub.empty and 'month' in df_ml_sub:
                    df_ml_sub = df_ml_sub[df_ml_sub['month'] == sel_m_num]

            elif "Tuần" in rep_type or "Weekly" in rep_type:
                available_weeks = sorted(list(set(
                    ([int(w) for w in df_ml_sub['week'].dropna().unique() if int(w) > 0] if not df_ml_sub.empty and 'week' in df_ml_sub else []) +
                    ([int(w) for w in df_inc_sub['week'].dropna().unique() if int(w) > 0] if not df_inc_sub.empty and 'week' in df_inc_sub else [])
                )))
                if not available_weeks:
                    available_weeks = list(range(1, 53))
                week_opts = [f"Tuần {int(w)}" for w in available_weeks]
                def_w_idx = len(week_opts) - 1
                sel_w_str = st.selectbox(t("Chọn Tuần báo cáo:", "Select reporting week:"), week_opts, index=def_w_idx, key="sb_maint_week_pick")
                w_match = re.search(r'\d+', sel_w_str)
                sel_w_num = int(w_match.group()) if w_match else 36
                period_title = f"{t('Tuần', 'Week')} {sel_w_num}"

                if not df_inc_sub.empty and 'week' in df_inc_sub:
                    df_inc_sub = df_inc_sub[df_inc_sub['week'] == sel_w_num]
                if not df_ml_sub.empty and 'week' in df_ml_sub:
                    df_ml_sub = df_ml_sub[df_ml_sub['week'] == sel_w_num]

            else:
                available_dates = []
                if not df_ml_sub.empty and 'date_str' in df_ml_sub:
                    available_dates.extend([d for d in df_ml_sub['date_str'].unique() if d and d != 'N/A'])
                if not df_inc_sub.empty and 'date_str' in df_inc_sub:
                    available_dates.extend([d for d in df_inc_sub['date_str'].unique() if d and d != 'N/A'])
                
                valid_date_objs = []
                for d in available_dates:
                    dt = parse_vn_date(d)
                    if dt and dt.year == 2026:
                        valid_date_objs.append(dt.date())
                
                valid_date_objs = sorted(list(set(valid_date_objs)))
                default_date = valid_date_objs[-1] if valid_date_objs else datetime(2026, 9, 20).date()
                min_date = valid_date_objs[0] if valid_date_objs else datetime(2026, 1, 1).date()
                max_date = datetime(2026, 12, 31).date()

                sel_d_obj = st.date_input(
                    t("📅 Chọn Ngày báo cáo (Click vào để mở lịch):", "📅 Select Reporting Date (Click to open calendar):"),
                    value=default_date,
                    min_value=min_date,
                    max_value=max_date,
                    format="DD/MM/YYYY",
                    key="cal_maint_date_pick"
                )
                sel_d_str = sel_d_obj.strftime("%d/%m/%Y")
                period_title = f"{t('Ngày', 'Date')} {sel_d_str}"

                if not df_inc_sub.empty:
                    if 'date' in df_inc_sub:
                        df_inc_sub = df_inc_sub[pd.to_datetime(df_inc_sub['date'], errors='coerce').dt.date == sel_d_obj]
                    elif 'date_str' in df_inc_sub:
                        df_inc_sub = df_inc_sub[df_inc_sub['date_str'] == sel_d_str]

                if not df_ml_sub.empty:
                    if 'date' in df_ml_sub:
                        df_ml_sub = df_ml_sub[pd.to_datetime(df_ml_sub['date'], errors='coerce').dt.date == sel_d_obj]
                    elif 'date_str' in df_ml_sub:
                        df_ml_sub = df_ml_sub[df_ml_sub['date_str'] == sel_d_str]

        # Tinh chỉnh theo từ khóa tìm kiếm nếu có
        if global_search_kw:
            if not df_inc_sub.empty:
                inc_m = search_df(df_inc_sub, global_search_kw)
                if not inc_m.empty:
                    df_inc_sub = inc_m
            if not df_ml_sub.empty:
                ml_m = search_df(df_ml_sub, global_search_kw)
                if not ml_m.empty:
                    df_ml_sub = ml_m

        # 3 Thẻ Metric then chốt chuẩn theo Google Sheets Monthly_Report
        tot_inc_cases = len(df_inc_sub)
        tot_down_hours = df_inc_sub['duration_hours'].sum() if not df_inc_sub.empty and 'duration_hours' in df_inc_sub else 0.0
        tot_maint_jobs = len(df_ml_sub)

        c_rp1, c_rp2, c_rp3 = st.columns(3)
        with c_rp1:
            st.metric(
                t(f"🚨 Tổng Số Vụ Sự Cố ({period_title})", f"🚨 Total Incidents ({period_title})"),
                f"{tot_inc_cases:,} " + t("vụ", "cases"),
                help="Tính từ cột D trong sheet 'Su co' (tương ứng công thức =COUNTIF)"
            )
        with c_rp2:
            st.metric(
                t(f"⏱️ Tổng Thời Gian Dừng Máy ({period_title})", f"⏱️ Total Downtime ({period_title})"),
                f"{tot_down_hours:,.2f} " + t("giờ", "hours"),
                help="Tính từ cột L trong sheet 'Su co' (tương ứng công thức =SUMIF)"
            )
        with c_rp3:
            st.metric(
                t(f"🔧 Tổng Việc Bảo Trì Thực Hiện ({period_title})", f"🔧 Total Maintenance Jobs ({period_title})"),
                f"{tot_maint_jobs:,} " + t("lượt", "jobs"),
                help="Tính từ cột D trong sheet 'Data' (tương ứng công thức =COUNTIF)"
            )

        st.markdown("---")

        # 2 Bảng hiển thị song song theo chuẩn Monthly_Report
        c_tbl_inc, c_tbl_maint = st.columns(2)

        with c_tbl_inc:
            st.markdown(f"##### 🚨 {t('Danh Sách Chi Tiết Sự Cố Phát Sinh Trong Kỳ (Su co)', 'Detailed Incident Breakdown (Su co)')}")
            if not df_inc_sub.empty:
                cols_inc_show = ['id_su_co', 'date_str', 'shift_leader', 'equipment_raw', 'description', 'solution', 'duration_hours', 'status']
                avail_inc_cols = [c for c in cols_inc_show if c in df_inc_sub.columns]
                df_disp_inc_p = df_inc_sub[avail_inc_cols].copy()
                if is_en():
                    df_disp_inc_p.rename(columns={
                        'id_su_co': 'Case ID',
                        'date_str': 'Date',
                        'shift_leader': 'Leader',
                        'equipment_raw': 'Equipment',
                        'description': 'Incident Description',
                        'solution': 'Action Taken',
                        'duration_hours': 'Downtime (h)',
                        'status': 'Status'
                    }, inplace=True)
                else:
                    df_disp_inc_p.rename(columns={
                        'id_su_co': 'Mã SC',
                        'date_str': 'Ngày',
                        'shift_leader': 'Ca Trực',
                        'equipment_raw': 'Thiết Bị',
                        'description': 'Mô Tả Hiện Trạng',
                        'solution': 'Biện Pháp Xử Lý',
                        'duration_hours': 'TG Dừng (h)',
                        'status': 'Trạng Thái'
                    }, inplace=True)
                st.dataframe(df_disp_inc_p, hide_index=True, use_container_width=True, height=400)
            else:
                st.info(t(f"Không có sự cố nào ghi nhận trong {period_title}.", f"No incidents recorded in {period_title}."))

        with c_tbl_maint:
            st.markdown(f"##### 🔧 {t('Công Việc Bảo Trì & Phục Hồi Đã Làm (Sheet Data)', 'Maintenance & Overhaul Jobs Done (Data)')}")
            if not df_ml_sub.empty:
                cols_ml_show = ['id', 'date_str', 'ca', 'equipment', 'activity', 'description', 'performer', 'status']
                avail_ml_cols = [c for c in cols_ml_show if c in df_ml_sub.columns]
                df_disp_ml_p = df_ml_sub[avail_ml_cols].copy()
                if is_en():
                    df_disp_ml_p.rename(columns={
                        'id': 'Job ID',
                        'date_str': 'Date',
                        'ca': 'Shift',
                        'equipment': 'Equipment',
                        'activity': 'Activity',
                        'description': 'Work Description',
                        'performer': 'Assignee',
                        'status': 'Status'
                    }, inplace=True)
                else:
                    df_disp_ml_p.rename(columns={
                        'id': 'Mã BT',
                        'date_str': 'Ngày',
                        'ca': 'Ca Trực',
                        'equipment': 'Mã Thiết Bị',
                        'activity': 'Hoạt Động',
                        'description': 'Nội Dung Công Việc',
                        'performer': 'Người Thực Hiện',
                        'status': 'Trạng Thái'
                    }, inplace=True)
                st.dataframe(df_disp_ml_p, hide_index=True, use_container_width=True, height=400)
            else:
                st.info(t(f"Chưa có dữ liệu bảo trì ghi nhận trong {period_title}.", f"No maintenance recorded in {period_title}."))

        # Biểu đồ phân tích trực quan
        if not df_inc_sub.empty or not df_ml_sub.empty:
            st.markdown("---")
            c_cht1, c_cht2 = st.columns(2)
            with c_cht1:
                if not df_inc_sub.empty and 'equipment_raw' in df_inc_sub:
                    eq_down = df_inc_sub.groupby('equipment_raw')['duration_hours'].sum().reset_index()
                    eq_down = eq_down[eq_down['duration_hours'] > 0].sort_values('duration_hours', ascending=False).head(8)
                    if not eq_down.empty:
                        fig_down = px.bar(
                            eq_down,
                            x='equipment_raw',
                            y='duration_hours',
                            text='duration_hours',
                            title=t(f"Top Thiết Bị Dừng Máy Nhiều Nhất ({period_title})", f"Top Downtime Equipment ({period_title})"),
                            labels={'equipment_raw': t('Thiết Bị', 'Equipment'), 'duration_hours': t('Giờ Dừng (h)', 'Hours')},
                            color='duration_hours',
                            color_continuous_scale='Reds'
                        )
                        fig_down.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
                        fig_down.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
                        st.plotly_chart(fig_down, use_container_width=True, key="fig_rep_downtime_bar")
            with c_cht2:
                if not df_ml_sub.empty and 'activity' in df_ml_sub:
                    act_pie = df_ml_sub['activity'].value_counts().head(7).reset_index()
                    act_pie.columns = ['Hoạt Động', 'Số Lần']
                    fig_act_p = px.pie(
                        act_pie,
                        names='Hoạt Động',
                        values='Số Lần',
                        title=t(f"Cơ Cấu Hoạt Động Bảo Trì ({period_title})", f"Maintenance Activities Breakdown ({period_title})"),
                        hole=0.45,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_act_p.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
                    st.plotly_chart(fig_act_p, use_container_width=True, key="fig_rep_act_pie")

    # -------------------------------------------------------------
    # SUBTAB 2: NHẬT KÝ BẢO TRÌ CHI TIẾT (SHEET DATA - 2.264 BẢN GHI)
    # -------------------------------------------------------------
    with maint_tab2:
        st.markdown(f"#### 🔧 {t('TOÀN BỘ NHẬT KÝ BẢO TRÌ, GIA CÔNG & PHỤC HỒI (SHEET DATA)', 'FULL MAINTENANCE, FABRICATION & OVERHAUL LOG (DATA SHEET)')}")
        st.caption(f"{t('Tổng hợp 2.264+ lượt bảo trì máy ép, nghiền, sấy, chipper, rulo, dao băm từ Google Sheets.', 'Consolidated 2,264+ maintenance records for pellet mills, hammer mills, dryers, chipper, rollers, knives.')}")

        if not df_maint_log.empty:
            c_ml_f1, c_ml_f2, c_ml_f3, c_ml_f4 = st.columns(4)
            all_lbl = t("Tất cả", "All")
            with c_ml_f1:
                all_acts = [all_lbl] + sorted([a for a in df_maint_log['activity'].unique() if a])
                sel_act = st.selectbox(t("Loại hoạt động:", "Activity:"), all_acts, key="sb_ml_act_t2")
            with c_ml_f2:
                all_eqs = [all_lbl] + sorted([e for e in df_maint_log['equipment'].unique() if e])
                sel_eq = st.selectbox(t("Thiết bị:", "Equipment:"), all_eqs, key="sb_ml_eq_t2")
            with c_ml_f3:
                all_status = [all_lbl] + sorted([s for s in df_maint_log['status'].unique() if s])
                sel_status = st.selectbox(t("Trạng thái:", "Status:"), all_status, key="sb_ml_status_t2")
            with c_ml_f4:
                search_kw = st.text_input(t("Tìm kiếm từ khóa:", "Search keyword:"), placeholder=t("Gõ tên dao, rulo, người làm...", "Type knife, roller, name..."), key="txt_ml_kw")

            df_ml_filt = df_maint_log.copy()
            if sel_act != all_lbl:
                df_ml_filt = df_ml_filt[df_ml_filt['activity'] == sel_act]
            if sel_eq != all_lbl:
                df_ml_filt = df_ml_filt[df_ml_filt['equipment'] == sel_eq]
            if sel_status != all_lbl:
                df_ml_filt = df_ml_filt[df_ml_filt['status'] == sel_status]
            eff_kw = search_kw.strip() if search_kw.strip() else global_search_kw
            if eff_kw:
                df_ml_filt = search_df(df_ml_filt, eff_kw)

            # 4 Thẻ KPI
            tot_maint = len(df_ml_filt)
            tot_proactive = len(df_ml_filt[df_ml_filt['activity'].str.contains('Bảo trì chủ động', case=False, na=False)])
            tot_rulo_die = len(df_ml_filt[df_ml_filt['activity'].str.contains('rulo|khuôn', case=False, na=False)])
            tot_done = len(df_ml_filt[df_ml_filt['status'].str.contains('Hoàn thành|OK', case=False, na=False)])
            rate_done = round(tot_done / tot_maint * 100, 1) if tot_maint > 0 else 100.0

            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric(t("Tổng Số Lượt Bảo Trì", "Total Maintenance Jobs"), f"{tot_maint:,} " + t("lượt", "jobs"))
            c_m2.metric(t("Bảo Trì Chủ Động", "Proactive Maintenance"), f"{tot_proactive:,} " + t("lượt", "jobs"))
            c_m3.metric(t("Phục Hồi Rulo & Khuôn", "Roller & Die Overhaul"), f"{tot_rulo_die:,} " + t("lượt", "jobs"))
            c_m4.metric(t("Tỷ Lệ Hoàn Thành", "Completion Rate"), f"{rate_done}%")

            # Biểu đồ
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                df_act_cnt = df_ml_filt['activity'].value_counts().head(7).reset_index()
                df_act_cnt.columns = ['Hoạt Động', 'Số Lần']
                fig_act = px.pie(
                    df_act_cnt,
                    names='Hoạt Động',
                    values='Số Lần',
                    title=t("Cơ Cấu Hoạt Động Bảo Trì & Sửa Chữa", "Maintenance & Repair Breakdown"),
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_act.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_act, use_container_width=True, key="fig_act_pie_t2")

            with c_g2:
                df_eq_cnt = df_ml_filt[df_ml_filt['equipment'] != '']['equipment'].value_counts().head(10).reset_index()
                df_eq_cnt.columns = ['Thiết Bị', 'Số Lần Bảo Trì']
                fig_eq_m = px.bar(
                    df_eq_cnt,
                    x='Thiết Bị',
                    y='Số Lần Bảo Trì',
                    text='Số Lần Bảo Trì',
                    color='Số Lần Bảo Trì',
                    color_continuous_scale='Blues',
                    title=t("Top 10 Thiết Bị Được Bảo Dưỡng Nhiều Nhất", "Top 10 Maintained Equipment")
                )
                fig_eq_m.update_traces(textposition='outside')
                fig_eq_m.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20), xaxis_title=t("Thiết Bị", "Equipment"), yaxis_title=t("Số Lần", "Count"))
                st.plotly_chart(fig_eq_m, use_container_width=True, key="fig_eq_maint_bar_t2")

            st.markdown(f"##### 📋 {t('Bảng Chi Tiết Nhật Ký Bảo Trì Thiết Bị (Data)', 'Equipment Maintenance Detailed Table (Data)')}")
            cols_ml_disp = ['id', 'date_str', 'ca', 'equipment', 'die_code', 'activity', 'description', 'duration_str', 'performer', 'status']
            avail_ml_cols = [c for c in cols_ml_disp if c in df_ml_filt.columns]
            df_show_ml = df_ml_filt[avail_ml_cols].copy()
            if is_en():
                df_show_ml.rename(columns={
                    'id': 'ID',
                    'date_str': 'Date',
                    'ca': 'Shift / Tech',
                    'equipment': 'Equipment Tag',
                    'die_code': 'Die Code',
                    'activity': 'Activity',
                    'description': 'Work Description',
                    'duration_str': 'Hours',
                    'performer': 'Assignee',
                    'status': 'Status'
                }, inplace=True)
            else:
                df_show_ml.rename(columns={
                    'id': 'Mã BT',
                    'date_str': 'Ngày',
                    'ca': 'Ca / Người Trực',
                    'equipment': 'Mã Thiết Bị',
                    'die_code': 'Mã Khuôn',
                    'activity': 'Hoạt Động',
                    'description': 'Nội Dung Công Việc',
                    'duration_str': 'Thời Gian (h)',
                    'performer': 'Người Thực Hiện',
                    'status': 'Trạng Thái'
                }, inplace=True)
            st.dataframe(df_show_ml, hide_index=True, use_container_width=True)

            csv_maint = df_show_ml.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=t("📥 Tải dữ liệu nhật ký bảo trì (CSV)", "📥 Download Maintenance Data (CSV)"),
                data=csv_maint,
                file_name=f"maintenance_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                key="btn_dl_maint_csv"
            )
        else:
            st.info(t("Chưa có dữ liệu từ bảng tính 'Maninternance BVNQB'.", "No data from 'Maninternance BVNQB' sheet."))

    # -------------------------------------------------------------
    # SUBTAB 3: QUẢN TRỊ TPM & CẢI TIẾN (SHEET TPM VÀ CAI TIEN)
    # -------------------------------------------------------------
    with maint_tab3:
        st.markdown(f"#### 🚀 {t('BẢNG QUẢN TRỊ MỤC TIÊU TPM & CẢI TIẾN THIẾT BỊ', 'TOTAL PRODUCTIVE MAINTENANCE & CONTINUOUS IMPROVEMENT (TPM)')}")
        st.caption(t("Theo dõi 115 hạng mục cải tiến máy móc, thiết bị xưởng băm, sấy, nghiền, ép từ sheet `TPM và cai tien`.", "Tracking 115 equipment improvement actions from `TPM và cai tien` sheet."))

        tpm_summary = tpm_data.get('summary', {})
        df_tpm_tasks = tpm_data.get('tasks', pd.DataFrame())

        tpm_total = tpm_summary.get('total', len(df_tpm_tasks))
        tpm_done = tpm_summary.get('completed', 0)
        tpm_prog = tpm_summary.get('in_progress', 0)
        tpm_not = tpm_summary.get('not_started', 0)
        tpm_rate = round(tpm_done / tpm_total * 100, 1) if tpm_total > 0 else 0.0

        c_tp1, c_tp2, c_tp3, c_tp4, c_tp5 = st.columns(5)
        c_tp1.metric(t("Tổng Việc Cải Tiến", "Total Improvements"), f"{tpm_total} " + t("việc", "tasks"))
        c_tp2.metric(t("Đã Hoàn Thành", "Completed"), f"{tpm_done} " + t("việc", "tasks"))
        c_tp3.metric(t("Đang Thực Hiện", "In Progress"), f"{tpm_prog} " + t("việc", "tasks"))
        c_tp4.metric(t("Chưa Bắt Đầu", "Not Started"), f"{tpm_not} " + t("việc", "tasks"))
        c_tp5.metric(t("Tỷ Lệ Hoàn Thành", "Completion Rate"), f"{tpm_rate}%")

        st.progress(min(max(tpm_rate / 100.0, 0.0), 1.0))

        if not df_tpm_tasks.empty:
            c_tf1, c_tf2, c_tf3 = st.columns(3)
            all_lbl = t("Tất cả", "All")
            with c_tf1:
                all_priorities = [all_lbl] + sorted([p for p in df_tpm_tasks['priority'].unique() if p])
                sel_prio = st.selectbox(t("Mức độ ưu tiên:", "Priority:"), all_priorities, key="sb_tpm_prio")
            with c_tf2:
                all_tpm_st = [all_lbl] + sorted([s for s in df_tpm_tasks['status'].unique() if s])
                sel_tpm_st = st.selectbox(t("Trạng thái:", "Status:"), all_tpm_st, key="sb_tpm_status")
            with c_tf3:
                all_assignees = [all_lbl] + sorted([a for a in df_tpm_tasks['person_in_charge'].unique() if a])
                sel_assignee = st.selectbox(t("Người phụ trách:", "Person in charge:"), all_assignees, key="sb_tpm_assignee")

            df_tpm_filt = df_tpm_tasks.copy()
            if sel_prio != all_lbl:
                df_tpm_filt = df_tpm_filt[df_tpm_filt['priority'] == sel_prio]
            if sel_tpm_st != all_lbl:
                df_tpm_filt = df_tpm_filt[df_tpm_filt['status'] == sel_tpm_st]
            if sel_assignee != all_lbl:
                df_tpm_filt = df_tpm_filt[df_tpm_filt['person_in_charge'] == sel_assignee]

            if global_search_kw and not df_tpm_filt.empty:
                tpm_m = search_df(df_tpm_filt, global_search_kw)
                if not tpm_m.empty:
                    df_tpm_filt = tpm_m

            df_tpm_disp = df_tpm_filt[['task', 'equipment_code', 'priority', 'person_in_charge', 'status', 'start_date', 'end_date', 'total_days', 'materials', 'note']].copy()
            if is_en():
                df_tpm_disp.rename(columns={
                    'task': 'Improvement Action / Task',
                    'equipment_code': 'Equipment Tag',
                    'priority': 'Priority',
                    'person_in_charge': 'Person in Charge',
                    'status': 'Status',
                    'start_date': 'Start Date',
                    'end_date': 'End Date',
                    'total_days': 'Days',
                    'materials': 'Materials',
                    'note': 'Note'
                }, inplace=True)
            else:
                df_tpm_disp.rename(columns={
                    'task': 'Thiết Bị / Hạng Mục Cải Tiến',
                    'equipment_code': 'Mã Thiết Bị',
                    'priority': 'Mức Độ Ưu Tiên',
                    'person_in_charge': 'Người Phụ Trách',
                    'status': 'Trạng Thái',
                    'start_date': 'Ngày Bắt Đầu',
                    'end_date': 'Ngày Kết Thúc',
                    'total_days': 'Tổng Ngày',
                    'materials': 'Vật Tư',
                    'note': 'Ghi Chú / Nhận Xét'
                }, inplace=True)
            st.dataframe(df_tpm_disp, hide_index=True, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu từ sheet 'TPM và cai tien'.", "No data from 'TPM và cai tien' sheet."))

    # -------------------------------------------------------------
    # SUBTAB 4: KIỂM ĐỊNH MỠ BÔI TRƠN MÁY ÉP (CHECK GREASE FOR PM30_6)
    # -------------------------------------------------------------
    with maint_tab4:
        st.markdown(f"#### 🛢️ {t('KIỂM TRA ĐỊNH LƯỢNG MỠ BÔI TRƠN MÁY ÉP PM30-6 (PE1 - PE8)', 'PELLET MILL LUBRICATING GREASE CONSUMPTION MONITORING (PE1 - PE8)')}")
        st.caption(t("Dữ liệu thực nghiệm cân định lượng mỡ bôi trơn máy ép viên PM30-6 (Tiêu chuẩn SCADA: 360s / 5 pulses ~ 1.5 - 1.6 g/pulse).", "Empirical grease weighing data for PM30-6 pellet mills (SCADA standard: 360s / 5 pulses ~ 1.5 - 1.6 g/pulse)."))

        if not grease_data.empty:
            c_gr_eq, c_gr_info = st.columns([1, 2])
            all_lbl = t("Tất cả", "All")
            with c_gr_eq:
                all_gr_eqs = [all_lbl] + sorted([e for e in grease_data['equipment'].unique() if e])
                sel_gr_eq = st.selectbox(t("Chọn máy ép:", "Select Pellet Mill:"), all_gr_eqs, key="sb_grease_eq")
            with c_gr_info:
                st.info(t("💡 **Chuẩn bôi trơn:** 360s / 5 xung (pulses) tương ứng ~1.5 - 1.6 g/xung để đảm bảo bảo vệ ổ bi lô ép và trục chính không bị quá nhiệt.", "💡 **Standard lubrication:** 360s / 5 pulses (~1.5 - 1.6 g/pulse) ensuring roller bearing and main shaft protection against overheating."))

            df_gr_filt = grease_data.copy()
            if sel_gr_eq != all_lbl:
                df_gr_filt = df_gr_filt[df_gr_filt['equipment'] == sel_gr_eq]

            avg_left = df_gr_filt['left_roller_g'].mean() if not df_gr_filt.empty else 0.0
            avg_right = df_gr_filt['right_roller_g'].mean() if not df_gr_filt.empty else 0.0
            avg_shaft = df_gr_filt['main_shaft_g'].mean() if not df_gr_filt.empty else 0.0
            avg_total = df_gr_filt['total_g'].mean() if not df_gr_filt.empty else 0.0

            c_g1, c_g2, c_g3, c_g4 = st.columns(4)
            c_g1.metric(t("TB Lô Trái (Left Roller)", "Avg Left Roller"), f"{avg_left:.2f} g")
            c_g2.metric(t("TB Lô Phải (Right Roller)", "Avg Right Roller"), f"{avg_right:.2f} g")
            c_g3.metric(t("TB Trục Chính (Main Shaft)", "Avg Main Shaft"), f"{avg_shaft:.2f} g")
            c_g4.metric(t("TB Tổng Lượng Mỡ / Chu Kỳ", "Avg Total Grease / Cycle"), f"{avg_total:.2f} g")

            # Biểu đồ so sánh lượng mỡ theo máy ép
            df_gr_summary = grease_data.groupby('equipment')[['left_roller_g', 'right_roller_g', 'main_shaft_g']].mean().reset_index()
            fig_gr = px.bar(
                df_gr_summary,
                x='equipment',
                y=['left_roller_g', 'right_roller_g', 'main_shaft_g'],
                barmode='group',
                title=t("Định Lượng Mỡ Bôi Trơn Trung Bình Từng Vị Trí (g)", "Average Lubricating Grease per Position (g)"),
                labels={'equipment': t('Máy Ép', 'Pellet Mill'), 'value': 'Gam (g)', 'variable': t('Vị Trí', 'Position')},
                color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b']
            )
            fig_gr.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_gr, use_container_width=True, key="fig_grease_bar")

            # Bảng chi tiết
            st.markdown(f"##### 📋 {t('Bảng Nhật Ký Kiểm Tra Định Lượng Mỡ Máy Ép', 'Pellet Mill Grease Inspection Log')}")
            df_gr_disp = df_gr_filt[['date_str', 'leader', 'equipment', 'circle', 'left_roller_g', 'right_roller_g', 'main_shaft_g', 'total_g', 'pulses']].copy()
            if is_en():
                df_gr_disp.rename(columns={
                    'date_str': 'Date',
                    'leader': 'Inspector / Leader',
                    'equipment': 'Mill Tag',
                    'circle': 'Circle',
                    'left_roller_g': 'Left Roller (g)',
                    'right_roller_g': 'Right Roller (g)',
                    'main_shaft_g': 'Main Shaft (g)',
                    'total_g': 'Total (g)',
                    'pulses': 'Pulses'
                }, inplace=True)
            else:
                df_gr_disp.rename(columns={
                    'date_str': 'Ngày Kiểm Tra',
                    'leader': 'Người Kiểm Tra',
                    'equipment': 'Máy Ép',
                    'circle': 'Chu Kỳ (Vòng)',
                    'left_roller_g': 'Lô Trái (g)',
                    'right_roller_g': 'Lô Phải (g)',
                    'main_shaft_g': 'Trục Chính (g)',
                    'total_g': 'Tổng Mỡ (g)',
                    'pulses': 'Số Xung (Pulses)'
                }, inplace=True)
            st.dataframe(df_gr_disp, hide_index=True, use_container_width=True)
        else:
            st.info(t("Chưa có dữ liệu từ sheet 'Check Grease for PM30_6'.", "No data from 'Check Grease for PM30_6' sheet."))

# ----------------- TAB MAINT PLAN: KẾ HOẠCH BẢO TRÌ & QUẢN TRỊ 4M -----------------
elif task_num == 7:
    st.markdown(f'<div class="section-title">{t("🛠️ KẾ HOẠCH BẢO TRÌ ĐỊNH KỲ, QUẢN TRỊ 4M & LỊCH THAY NHỚT MÁY ÉP", "🛠️ PREVENTIVE MAINTENANCE PLAN, 4M MANAGEMENT & PELLET MILL OIL CHANGE SCHEDULE")}</div>', unsafe_allow_html=True)
    st.caption(f"{t('Nguồn dữ liệu:', 'Data source:')} **{maint_plan_title}** & **{oil_title}** (Google Sheets ID: `1DRHrUPkLk7650XbxW1zZ73dp0k0Dcg4FZeKZriUKRso`)")

    subtab_plan, subtab_4m, subtab_oil = st.tabs([
        t("📅 KẾ HOẠCH BẢO TRÌ THEO THÁNG", "📅 MONTHLY PREVENTIVE PLAN"),
        t("🎯 QUẢN TRỊ CHIẾN LƯỢC 4M (6 THÁNG CUỐI NĂM 2026)", "🎯 4M STRATEGIC MANAGEMENT (H2 2026)"),
        t("🛢️ LỊCH THAY NHỚT HỘP SỐ MÁY ÉP (MOBIL GLYGOYLE 460)", "🛢️ PELLET MILL GEARBOX OIL CHANGE (MOBIL GLYGOYLE 460)")
    ])

    with subtab_plan:
        if not df_maint_plan.empty:
            avail_months = sorted(list(df_maint_plan['month_label'].unique()), reverse=True)
            sel_plan_m = st.selectbox(t("📆 Click chọn tháng xem kế hoạch bảo trì:", "📆 Select month for maintenance plan:"), avail_months, key="sb_plan_month")
            df_plan_sub = df_maint_plan[df_maint_plan['month_label'] == sel_plan_m]

            tot_tasks = len(df_plan_sub)
            done_tasks = len(df_plan_sub[df_plan_sub['status'].str.contains('Đã hoàn thành', case=False, na=False)])
            prog_tasks = len(df_plan_sub[df_plan_sub['status'].str.contains('Đang thực hiện', case=False, na=False)])
            not_started = len(df_plan_sub[df_plan_sub['status'].str.contains('Chưa bắt đầu', case=False, na=False)])
            urgent_tasks = len(df_plan_sub[df_plan_sub['priority'].str.contains('Khẩn cấp|Cao', case=False, na=False)])
            pct_done = round(done_tasks / tot_tasks * 100, 1) if tot_tasks > 0 else 0.0

            cp1, cp2, cp3, cp4, cp5 = st.columns(5)
            cp1.metric(t("Tổng Số Công Việc", "Total Tasks"), f"{tot_tasks} " + t("việc", "tasks"))
            cp2.metric(t("Đã Hoàn Thành", "Completed"), f"{done_tasks} " + t("việc", "tasks") + f" ({pct_done}%)")
            cp3.metric(t("Đang Thực Hiện", "In Progress"), f"{prog_tasks} " + t("việc", "tasks"))
            cp4.metric(t("Chưa Bắt Đầu", "Not Started"), f"{not_started} " + t("việc", "tasks"))
            cp5.metric(t("Mức Độ Khẩn Cấp / Cao", "Urgent / High Priority"), f"{urgent_tasks} " + t("việc", "tasks"))

            st.markdown("---")
            c_pchart1, c_pchart2 = st.columns(2)
            with c_pchart1:
                df_p_st = df_plan_sub['status'].value_counts().reset_index()
                df_p_st.columns = ['Trạng Thái', 'Số Việc']
                fig_pst = px.pie(
                    df_p_st,
                    names='Trạng Thái',
                    values='Số Việc',
                    title=f"{t('Tiến Độ Thực Hiện Kế Hoạch', 'Plan Execution Progress')} - {sel_plan_m}",
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
                    title=t("Nhu Cầu & Tình Trạng Vật Tư Phụ Tùng", "Spare Parts & Material Status")
                )
                fig_mat.update_traces(textposition='outside')
                fig_mat.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20), showlegend=False, xaxis_title="", yaxis_title=t("Số Việc", "Tasks"))
                st.plotly_chart(fig_mat, use_container_width=True, key="fig_plan_mat_bar")

            st.markdown(f"##### 📋 {t('Danh Mục Công Việc Kế Hoạch Bảo Trì', 'Maintenance Plan Task List')} - {sel_plan_m}")
            disp_plan_cols = ['task_name', 'equipment', 'priority', 'pic', 'status', 'start_date', 'end_date', 'total_days', 'material', 'material_status']
            avail_p_cols = [c for c in disp_plan_cols if c in df_plan_sub.columns]
            df_disp_plan = df_plan_sub[avail_p_cols].copy()
            if is_en():
                df_disp_plan.rename(columns={
                    'task_name': 'Task Item',
                    'equipment': 'Equipment Tag',
                    'priority': 'Priority',
                    'pic': 'PIC',
                    'status': 'Status',
                    'start_date': 'Start Date',
                    'end_date': 'End Date',
                    'total_days': 'Duration (days)',
                    'material': 'Material',
                    'material_status': 'Dependency'
                }, inplace=True)
            else:
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
            st.info(t("Chưa có dữ liệu kế hoạch bảo trì theo tháng.", "No monthly preventive maintenance data."))

    with subtab_4m:
        st.markdown(f"### 🎯 {t('BẢNG QUẢN TRỊ CHIẾN LƯỢC 4M (6 THÁNG CUỐI NĂM 2026)', '4M STRATEGIC MANAGEMENT (H2 2026)')}")
        st.markdown(t("""
        Mô hình quản trị 4M trong sản xuất:
        - 👥 **Men (Con người):** Đào tạo tay nghề ép viên, luân chuyển tổ, xây dựng nhân sự lõi, văn hóa kỹ trị.
        - 🪵 **Material (Nguyên vật liệu):** Nâng tỷ lệ vỏ cây đốt >60%, kiểm soát độ ẩm, phối trộn nguyên liệu tối ưu giá thành.
        - 📐 **Method (Phương pháp / Quy trình):** Mô hình quản lý, kỷ luật vận hành, chuẩn hóa quy trình, cải tiến.
        - 📊 **Measurement (Đo lường / Thống kê):** Nâng cao kỹ năng đo lường, hạch toán năng lượng từng khâu, hệ thống báo cáo.
        """, """
        4M Production Management Framework:
        - 👥 **Men (People):** Pellet mill operator training, shift cross-rotation, core personnel retention, technocratic culture.
        - 🪵 **Material:** Increase bark fuel ratio >60%, strict moisture control, cost-optimized raw material blending.
        - 📐 **Method:** Modern management models, operational discipline, SOP standardization, continuous improvement (Kaizen).
        - 📊 **Measurement:** Advanced metrology skills, stage-by-stage energy accounting, real-time reporting system.
        """))

        if not df_4m.empty:
            c_4m1, c_4m2, c_4m3, c_4m4 = st.columns(4)
            c_4m1.metric(t("👥 1. Men (Con người)", "👥 1. Men (People)"), f"{len(df_4m[df_4m['pillar']=='Men'])} " + t("mục tiêu", "goals"))
            c_4m2.metric(t("🪵 2. Material (Nguyên liệu)", "🪵 2. Material"), f"{len(df_4m[df_4m['pillar']=='Material'])} " + t("mục tiêu", "goals"))
            c_4m3.metric(t("📐 3. Method (Phương pháp)", "📐 3. Method"), f"{len(df_4m[df_4m['pillar']=='Method'])} " + t("mục tiêu", "goals"))
            c_4m4.metric(t("📊 4. Measurement (Đo lường)", "📊 4. Measurement"), f"{len(df_4m[df_4m['pillar']=='Measurement'])} " + t("mục tiêu", "goals"))

            st.markdown("---")
            p_all = t("Tất cả 4M", "All 4M")
            p_men = t("Men (Con người)", "Men (People)")
            p_mat = t("Material (Nguyên vật liệu)", "Material")
            p_met = t("Method (Phương pháp)", "Method")
            p_mea = t("Measurement (Đo lường)", "Measurement")
            sel_pillar = st.selectbox(
                t("Lọc theo trụ cột 4M:", "Filter by 4M Pillar:"),
                [p_all, p_men, p_mat, p_met, p_mea],
                key="sb_4m_pillar"
            )

            df_4m_disp = df_4m.copy()
            if sel_pillar != p_all:
                pillar_code = sel_pillar.split()[0]
                df_4m_disp = df_4m_disp[df_4m_disp['pillar'] == pillar_code]

            disp_4m_cols = ['pillar', 'objective', 'action', 'pic', 'deadline', 'status', 'evaluation']
            avail_4m_cols = [c for c in disp_4m_cols if c in df_4m_disp.columns]
            df_4m_table = df_4m_disp[avail_4m_cols].copy()
            if is_en():
                df_4m_table.rename(columns={
                    'pillar': '4M Pillar',
                    'objective': 'Strategic Objective',
                    'action': 'Specific Action',
                    'pic': 'PIC',
                    'deadline': 'Deadline',
                    'status': 'Status',
                    'evaluation': 'Evaluation'
                }, inplace=True)
            else:
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
            st.info(t("Chưa có dữ liệu từ sheet 'Theo dõi 4M2026'.", "No data from sheet 'Theo dõi 4M2026'."))

    with subtab_oil:
        st.markdown(f"### 🛢️ {t('LỊCH THAY NHỚT HỘP SỐ MÁY ÉP VIÊN NÉN (MOBIL GLYGOYLE 460)', 'PELLET MILL GEARBOX OIL CHANGE SCHEDULE (MOBIL GLYGOYLE 460)')}")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #3b82f6; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;">
            <div style="font-size: 15px; font-weight: 700; color: #60a5fa; margin-bottom: 6px;">
                ⚙️ {t('TIÊU CHUẨN KỸ THUẬT DẦU BÔI TRƠN HỘP SỐ MÁY ÉP ANDRITZ PM30 (PE1 - PE8)', 'TECHNICAL SPECIFICATIONS FOR ANDRITZ PM30 GEARBOX LUBRICANT (PE1 - PE8)')}
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; font-size: 13px; color: #cbd5e1;">
                <div>🔹 <b>{t('Chủng loại dầu:', 'Oil Type:')}</b> <span style="color: #facc15; font-weight: 600;">Mobil Glygoyle 460</span> {t('(PAG tổng hợp)', '(Synthetic PAG)')}</div>
                <div>🔹 <b>{t('Định mức thay dầu:', 'Change Interval:')}</b> <span style="color: #38bdf8; font-weight: 600;">4.000 {t('giờ', 'hours')}</span> {t('vận hành / chu kỳ', 'running hours / cycle')}</div>
                <div>🔹 <b>{t('Dung tích mỗi máy:', 'Capacity per Machine:')}</b> <span style="color: #4ade80; font-weight: 600;">208 {t('Lít', 'Liters')}</span> {t('(1 phuy / máy)', '(1 drum / machine)')}</div>
                <div>🔹 <b>{t('Tổng dung tích xưởng:', 'Total Plant Capacity:')}</b> <span style="color: #fb923c; font-weight: 600;">1.664 {t('Lít', 'Liters')}</span> {t('(8 máy PE1 - PE8)', '(8x PE1 - PE8)')}</div>
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
            c_o1.metric(t("Tổng Máy Ép", "Total Pellet Mills"), f"{tot_machines} " + t("máy", "units"), "PE1 → PE8")
            c_o2.metric(t("Tổng Lượng Nhớt", "Total Oil Volume"), f"{tot_oil_lit:,.0f} " + t("Lít", "Liters"), t("208 L / máy", "208 L / unit"))
            c_o3.metric(t("Định Mức Chu Kỳ", "Standard Interval"), t("4.000 Giờ", "4,000 Hours"), "Mobil Glygoyle 460")
            c_o4.metric(t("Tiến Độ Lần 1", "Cycle 1 Progress"), f"{c1_done_count}/{tot_machines} " + t("máy", "units") + f" ({c1_pct}%)", f"{t('Ngày', 'Date')} {latest_change_date}")
            c_o5.metric(t("Chu Kỳ Hiện Tại", "Current Cycle"), t("Chu kỳ 2 (0h)", "Cycle 2 (0h)"), t("Bình thường", "Normal"))

            st.markdown("---")

            c_og1, c_og2 = st.columns([3, 2])
            with c_og1:
                fig_oil_bar = px.bar(
                    df_oil_sum,
                    x='machine_code',
                    y='run_hours_c1',
                    text='run_hours_c1',
                    labels={'machine_code': t('Máy Ép', 'Pellet Mill'), 'run_hours_c1': t('Giờ Chạy Thực Tế (h)', 'Actual Run Hours (h)')},
                    title=t("Số Giờ Vận Hành Thực Tế Khi Thay Nhớt Lần 1 vs Định Mức 4.000h", "Actual Operating Hours at 1st Oil Change vs 4,000h Target"),
                    color='run_hours_c1',
                    color_continuous_scale=['#38bdf8', '#10b981', '#f59e0b', '#ef4444']
                )
                fig_oil_bar.add_hline(
                    y=4000, 
                    line_dash="dash", 
                    line_color="#ef4444", 
                    annotation_text=t("Định mức chuẩn: 4.000h", "Standard target: 4,000h"), 
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
                    title=f"{t('Tỷ Lệ Hoàn Thành Lần 1', 'Cycle 1 Completion Rate')} ({latest_change_date})",
                    hole=0.45,
                    color_discrete_sequence=['#10b981', '#f59e0b']
                )
                fig_oil_pie.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_oil_pie, use_container_width=True, key="fig_oil_pie_c1")

            st.markdown(f"##### 📋 {t('Bảng Tổng Hợp Theo Dõi Thay Nhớt Hộp Số PE1 - PE8', 'PE1 - PE8 Gearbox Oil Change Summary Table')}")
            disp_oil = df_oil_sum.copy()
            disp_oil['Tỷ Lệ Giờ Đạt C1'] = (disp_oil['run_hours_c1'] / disp_oil['standard_hours'] * 100).round(1).astype(str) + '%'
            if is_en():
                disp_oil.rename(columns={
                    'machine_code': 'Machine Tag',
                    'machine_name': 'Equipment Name',
                    'oil_type': 'Lubricant Type',
                    'oil_capacity_l': 'Capacity (L)',
                    'standard_hours': 'Interval (h)',
                    'run_hours_c1': 'Cycle 1 Run Hours (h)',
                    'change_date_c1': 'Cycle 1 Date',
                    'change_status_c1': 'Cycle 1 Status',
                    'run_hours_c2': 'Cycle 2 Run Hours (h)',
                    'alert_status_c2': 'Cycle 2 Alert',
                    'Tỷ Lệ Giờ Đạt C1': 'Cycle 1 Completion %'
                }, inplace=True)
                ordered_cols = ['Machine Tag', 'Equipment Name', 'Lubricant Type', 'Capacity (L)', 'Interval (h)', 'Cycle 1 Run Hours (h)', 'Cycle 1 Completion %', 'Cycle 1 Date', 'Cycle 1 Status', 'Cycle 2 Run Hours (h)', 'Cycle 2 Alert']
            else:
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
            st.markdown(f"##### 🔍 {t('Chi Tiết Kế Hoạch 10 Chu Kỳ Thay Nhớt Từng Máy Ép', 'Detailed 10-Cycle Oil Change Schedule per Machine')}")
            sel_pe = st.selectbox(
                t("Chọn máy ép để kiểm tra chi tiết toàn bộ chu kỳ:", "Select pellet mill for full cycle details:"),
                [f"PE{i}" for i in range(1, 9)],
                key="sb_oil_pe_detail"
            )
            
            if sel_pe in oil_details and not oil_details[sel_pe].empty:
                df_pe_dt = oil_details[sel_pe].copy()
                st.dataframe(df_pe_dt, hide_index=True, use_container_width=True)
            else:
                st.info(f"{t('Chưa có bảng chi tiết chu kỳ cho', 'No detailed cycle table for')} {sel_pe}.")

            st.markdown(t("""
            > [!NOTE]
            > **Khuyến nghị kỹ thuật:** Dầu **Mobil Glygoyle 460** là dầu tổng hợp gốc Polyalkylene Glycol (PAG). Tuyệt đối **không pha trộn** với dầu gốc khoáng hoặc dầu gốc PAO/Ester khác. Khi thay nhớt cần xả kiệt cặn dầu cũ, vệ sinh nam châm bẫy mạt kim loại và kiểm tra độ kín các phớt làm kín của hộp số máy ép.
            """, """
            > [!NOTE]
            > **Technical Recommendation:** **Mobil Glygoyle 460** is a Polyalkylene Glycol (PAG) synthetic lubricant. Strictly **do not mix** with mineral oils or PAO/Ester synthetics. When changing oil, fully drain old sludge, clean magnetic chip catchers, and inspect gearbox oil seals for leakage.
            """))
        else:
            st.info(t("Chưa có dữ liệu từ bảng tính 'Lịch thay nhớt hộp số máy ép'.", "No data from 'Pellet Mill Gearbox Oil Change Schedule' sheet."))

# ----------------- TAB 8: KIỂM TRA CHẤT LƯỢNG KCS -----------------
elif task_num == 8:
    st.markdown(f'<div class="section-title">{t("🔬 Kiểm Tra Chất Lượng KCS: Độ Ẩm, Độ Tro & Tỷ Trọng Viên Nén", "🔬 KCS Quality Inspection: Moisture, Ash Content & Bulk Density")}</div>', unsafe_allow_html=True)
    st.caption(t("Dữ liệu kiểm nghiệm chất lượng sản phẩm từ sheet KCS & Tổng hợp ngày - Tiêu chuẩn xuất khẩu ISO 17225-2 / ENplus.", "Product quality inspection data from KCS sheet & Daily summary - Export standard ISO 17225-2 / ENplus."))
    
    if not df_kcs.empty:
        # Thẻ tóm tắt chỉ số KCS mới nhất
        last_kcs = df_kcs.iloc[-1] if not df_kcs.empty else {}
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        am_vien_val = last_kcs.get('am_vien_pct', 0.0)
        tro_val = last_kcs.get('do_tro_pct', 0.0)
        ty_trong_latest = df_daily['ty_trong_vien'].dropna().iloc[-1] if (not df_daily.empty and 'ty_trong_vien' in df_daily.columns and (df_daily['ty_trong_vien'] > 0).any()) else 0.0
        
        with c_k1:
            st.metric(t("💧 Độ Ẩm Viên Mẫu Mới Nhất", "💧 Latest Pellet Moisture"), f"{am_vien_val:.2f}%" if am_vien_val > 0 else "N/A", t("Chuẩn 8.0 - 9.5%", "Target 8.0 - 9.5%"))
        with c_k2:
            st.metric(t("🔥 Độ Tro Mẫu Mới Nhất", "🔥 Latest Ash Content"), f"{tro_val:.2f}%" if tro_val > 0 else "N/A", t("Chuẩn ≤ 1.5%", "Target ≤ 1.5%"))
        with c_k3:
            st.metric(t("⚖️ Tỷ Trọng Thể Tích", "⚖️ Bulk Density"), f"{ty_trong_latest:,.0f} kg/m³" if ty_trong_latest > 0 else "N/A", f"{t('Chuẩn ≥', 'Target ≥')} {DENSITY_BENCHMARK_MIN:.0f} kg/m³")
        with c_k4:
            st.metric(t("🧪 Ca Trưởng Phụ Trách", "🧪 Shift Leader on Duty"), f"{t('Ca', 'Shift')} {last_kcs.get('shift_leader', 'N/A')}", f"{t('Lúc', 'At')} {last_kcs.get('time_sample', '')} ({last_kcs.get('date_str', '')})")

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
                    name=t('Độ ẩm viên (%)', 'Pellet Moisture (%)'),
                    line=dict(color='#0284c7', width=2)
                ))
            fig_am.add_hline(y=9.5, line_dash="dash", line_color="red", annotation_text=t("Trần chuẩn (9.5%)", "Upper Limit (9.5%)"))
            fig_am.add_hline(y=8.0, line_dash="dash", line_color="green", annotation_text=t("Sàn chuẩn (8.0%)", "Lower Limit (8.0%)"))
            fig_am.update_layout(
                title=t("Biểu Đồ Xu Hướng Độ Ẩm Viên Nén (%) 30 Mẫu Gần Đây", "Pellet Moisture Trend (%) - Last 30 Samples"),
                xaxis_title=t("Thời gian lấy mẫu", "Sampling Time"),
                yaxis_title=t("Độ ẩm (%)", "Moisture (%)"),
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
                        name=t('Tỷ trọng viên (kg/m³)', 'Bulk Density (kg/m³)'),
                        line=dict(color='#10b981', width=2)
                    ))
                    fig_dens.add_hline(y=DENSITY_BENCHMARK_MIN, line_dash="dash", line_color="#f59e0b", annotation_text=f"{t('Chuẩn tối thiểu', 'Min Standard')} ({DENSITY_BENCHMARK_MIN:,.0f} kg/m³)")
                    fig_dens.update_layout(
                        title=t("Diễn Biến Tỷ Trọng Thể Tích Viên Nén (kg/m³)", "Pellet Bulk Density Trend (kg/m³)"),
                        xaxis_title=t("Ngày", "Date"),
                        yaxis_title="kg/m³",
                        height=320,
                        margin=dict(t=40, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig_dens, use_container_width=True)

        st.markdown(f"##### 📋 {t('Nhật Ký Kết Quả Đo Kiểm KCS Gần Nhất', 'Recent KCS Quality Inspection Log')}")
        disp_kcs_cols = ['date_str', 'time_sample', 'shift_leader', 'am_sau_say_1_pct', 'am_sau_say_2_pct', 'am_vien_pct', 'do_tro_pct']
        avail_k_cols = [c for c in disp_kcs_cols if c in df_kcs.columns]
        df_kcs_disp = df_kcs[avail_k_cols].tail(15).copy()
        if is_en():
            df_kcs_disp.rename(columns={
                'date_str': 'Date',
                'time_sample': 'Sample Time',
                'shift_leader': 'Shift Leader',
                'am_sau_say_1_pct': 'Post-Dryer 1 Moist (%)',
                'am_sau_say_2_pct': 'Post-Dryer 2 Moist (%)',
                'am_vien_pct': 'Pellet Moist (%)',
                'do_tro_pct': 'Ash Content (%)'
            }, inplace=True)
        else:
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
        st.info(t("Chưa có dữ liệu kiểm nghiệm KCS.", "No KCS quality inspection data available."))

# ----------------- TAB 9: QUẢN LÝ DẦU DIEZEN -----------------
elif task_num == 9:
    st.markdown(f'<div class="section-title">{t("⛽ Hệ Thống Quản Lý Cấp Phát & Tiêu Hao Dầu Diezen", "⛽ Diesel Fuel Dispensation & Consumption Management")}</div>', unsafe_allow_html=True)
    st.caption(t("Dữ liệu theo dõi cấp phát và tiêu hao nhiên liệu dầu Diezen phục vụ xe cơ giới & vận hành nhà máy.", "Fuel tracking data for diesel dispensation and consumption for heavy mobile equipment & plant operations."))
    
    if not df_diezen.empty:
        total_dz_all = float(df_diezen['tong_diezen_lit'].sum()) if 'tong_diezen_lit' in df_diezen.columns else 0.0
        latest_dz_row = df_diezen.iloc[-1]
        latest_dz_vol = float(latest_dz_row.get('tong_diezen_lit', 0.0))
        latest_w_label = latest_dz_row.get('week_label', 'Tuần gần nhất')

        c_dz1, c_dz2, c_dz3 = st.columns(3)
        c_dz1.metric(t("Tổng Dầu Diezen Đã Cấp", "Total Diesel Dispensed"), f"{total_dz_all:,.0f} " + t("Lít", "Liters"), f"{t('Toàn bộ', 'Across')} {len(df_diezen)} {t('kỳ theo dõi', 'reporting periods')}")
        c_dz2.metric(f"{t('Tiêu Thụ', 'Consumption')} {latest_w_label}", f"{latest_dz_vol:,.0f} " + t("Lít", "Liters"), t("Kỳ báo cáo mới nhất", "Latest reporting period"))
        avg_dz = total_dz_all / len(df_diezen) if len(df_diezen) > 0 else 0.0
        c_dz3.metric(t("Mức Tiêu Thụ Trung Bình", "Average Consumption"), f"{avg_dz:,.0f} " + t("Lít/kỳ", "Liters/period"), t("Định mức theo dõi", "Benchmark monitoring"))

        st.markdown("---")
        col_dz_left, col_dz_right = st.columns([1, 1])
        with col_dz_left:
            latest_dz = latest_dz_row.to_dict()
            vehicles = [k for k in latest_dz.keys() if k not in ['month', 'week', 'week_label', 'tong_diezen_lit', 'date_str'] and isinstance(latest_dz[k], (int, float)) and latest_dz[k] > 0]
            if vehicles:
                dz_breakdown = [{t('Thiết bị / Phương tiện', 'Equipment / Vehicle'): v, t('Nhiên liệu (Lít)', 'Fuel (Liters)'): latest_dz[v]} for v in vehicles]
                df_dz_pie = pd.DataFrame(dz_breakdown)
                fig_dz = px.pie(
                    df_dz_pie,
                    names=t('Thiết bị / Phương tiện', 'Equipment / Vehicle'),
                    values=t('Nhiên liệu (Lít)', 'Fuel (Liters)'),
                    title=f"{t('Cơ Cấu Phân Bổ Dầu Theo Phương Tiện', 'Diesel Distribution by Vehicle')} - {latest_w_label}",
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
                    title=t("Diễn Biến Cấp Phát Dầu Diezen Qua Các Tuần (Lít)", "Weekly Diesel Dispensation Trend (Liters)"),
                    color_discrete_sequence=['#f59e0b']
                )
                fig_dz_bar.update_traces(texttemplate='%{text:,.0f}L', textposition='outside')
                fig_dz_bar.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20), xaxis_title=t("Tuần", "Week"), yaxis_title=t("Lít", "Liters"))
                st.plotly_chart(fig_dz_bar, use_container_width=True)

        st.markdown(f"##### 📋 {t('Bảng Chi Tiết Cấp Phát & Tiêu Hao Dầu Diezen', 'Detailed Diesel Dispensation & Consumption Table')}")
        st.dataframe(df_diezen, hide_index=True, use_container_width=True)
    else:
        st.info(t("Chưa có dữ liệu dầu Diezen.", "No diesel fuel data available."))

# ----------------- TAB 10: HIỆU SUẤT CA TRƯỞNG -----------------
elif task_num == 10:
    st.markdown(f'<div class="section-title">{t("🏆 So Sánh Hiệu Suất Sản Xuất Theo Ca Trưởng", "🏆 Shift Leader Production Performance Benchmarking")}</div>', unsafe_allow_html=True)
    df_leaders = get_shift_leader_kpis(df_shifts)
    if global_search_kw and not df_leaders.empty:
        ld_m = search_df(df_leaders, global_search_kw)
        if not ld_m.empty:
            df_leaders = ld_m
    
    if not df_leaders.empty:
        df_ld_disp = translate_shift_leader_kpis(df_leaders)
        st.dataframe(df_ld_disp, use_container_width=True, hide_index=True)

        col_ld1, col_ld2 = st.columns(2)
        df_chart_ld = df_leaders.copy()
        if is_en():
            df_chart_ld['Ca Trưởng'] = df_chart_ld['Ca Trưởng'].apply(lambda x: format_person_name(str(x)))
        with col_ld1:
            fig_ld_output = px.bar(
                df_chart_ld,
                x='Ca Trưởng',
                y='Tổng sản lượng (tấn)',
                text='Tổng sản lượng (tấn)',
                color='Ca Trưởng',
                title=t("Tổng Sản Lượng Lũy Kế Theo Ca Trưởng (Tấn)", "Cumulative Output by Shift Leader (Tons)")
            )
            fig_ld_output.update_traces(texttemplate='%{text:,.0f}t', textposition='outside')
            fig_ld_output.update_layout(height=340, showlegend=False, xaxis_title=t("Ca Trưởng", "Shift Leader"), yaxis_title=t("Tấn", "Tons"))
            st.plotly_chart(fig_ld_output, use_container_width=True)

        with col_ld2:
            fig_ld_elec = px.bar(
                df_chart_ld,
                x='Ca Trưởng',
                y='Điện năng TB (kWh/tấn)',
                text='Điện năng TB (kWh/tấn)',
                color='Điện năng TB (kWh/tấn)',
                color_continuous_scale='RdYlGn_r',
                title=t("Suất Điện Trung Bình Theo Ca Trưởng (kWh/tấn - Càng Thấp Càng Tốt)", "Average Electricity by Shift Leader (kWh/ton - Lower is Better)")
            )
            fig_ld_elec.add_hline(y=175, line_dash="dash", line_color="red", annotation_text=t("Trần 175", "Ceiling 175"))
            fig_ld_elec.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_ld_elec.update_layout(height=340, xaxis_title=t("Ca Trưởng", "Shift Leader"), yaxis_title="kWh/t")
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

# ----------------- TAB 14: NHẬP SỐ LIỆU (PHÂN QUYỀN TRUY CẬP) -----------------
elif task_num == 14:
    if app_loader is None:
        app_loader = DataLoader()
    render_data_entry_module(app_loader)

# Footer
st.markdown("---")
st.caption(t("Hệ Thống Báo Cáo Sản Xuất Tự Động Viên Nén Gỗ | Dữ liệu cập nhật thời gian thực từ Google Sheets | Phiên bản 1.0", "Automated Wood Pellet Production Reporting System | Real-time data from Google Sheets | Version 1.0"))


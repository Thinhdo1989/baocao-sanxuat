"""
Giao diện Dashboard Báo Cáo Sản Xuất Tự Động - Nhà Máy Viên Nén Gỗ
Chạy bằng lệnh: streamlit run app.py
"""
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Báo Cáo Sản Xuất - Nhà Máy Viên Nén Gỗ",
    page_icon="🌲",
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
        font-weight: 700;
        color: #0f172a;
        margin-top: 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

from data_loader import DataLoader
from kpi_calculator import (
    get_latest_day_kpis,
    get_equipment_statistics,
    get_shift_leader_kpis,
    get_kpi_leaderboard,
    get_incident_statistics,
    get_equipment_incident_alerts,
    evaluate_kpi_score,
    evaluate_electricity,
    evaluate_productivity,
    evaluate_moisture,
    evaluate_ash,
    ELEC_MIN_BENCHMARK,
    ELEC_MAX_BENCHMARK,
    PRODUCTIVITY_TARGET,
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

    # Dữ liệu Sự Cố và Bảo Trì mới
    df_incidents = loader.load_incident_data()
    df_maint_log = loader.load_maintenance_log()
    df_maint_plan = loader.load_maintenance_plan_monthly()
    df_4m = loader.load_4m_management()

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
        'incidents': df_incidents,
        'maint_log': df_maint_log,
        'maint_plan': df_maint_plan,
        'maint_4m': df_4m,
        'prod_title': loader.spreadsheet.title if loader.spreadsheet else "2026 BVN QB Nhật kí sản xuất",
        'kpi_title': loader.kpi_spreadsheet.title if loader.kpi_spreadsheet else "2026 Nhat ky KPI",
        'maint_log_title': loader.maint_log_spreadsheet.title if loader.maint_log_spreadsheet else "2026 BẢO TRÌ BVN",
        'maint_plan_title': loader.maint_plan_spreadsheet.title if loader.maint_plan_spreadsheet else "Mainternance BVN QB"
    }

# Load dữ liệu
try:
    with st.spinner("Đang kết nối 4 Google Sheets và nạp dữ liệu sản xuất, KPI & bảo trì..."):
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
        df_incidents = data.get('incidents', pd.DataFrame())
        df_maint_log = data.get('maint_log', pd.DataFrame())
        df_maint_plan = data.get('maint_plan', pd.DataFrame())
        df_4m = data.get('maint_4m', pd.DataFrame())
        sheet_title = data['prod_title']
        kpi_sheet_title = data['kpi_title']
        maint_log_title = data.get('maint_log_title', "2026 BẢO TRÌ BVN")
        maint_plan_title = data.get('maint_plan_title', "Mainternance BVN QB")
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

# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wood.png", width=64)
    st.title("VIÊN NÉN GỖ")
    st.markdown(f"📗 **Sản xuất:** `{sheet_title}`")
    st.markdown(f"🎯 **Đánh giá KPI:** `{kpi_sheet_title}`")
    st.markdown(f"🔧 **Nhật ký bảo trì:** `{maint_log_title}`")
    st.markdown(f"🛠️ **Kế hoạch & 4M:** `{maint_plan_title}`")
    
    st.success("🟢 4/4 Google Sheets Connected")
    
    if st.button("🔄 Tải lại dữ liệu (Refresh)", width="stretch"):
        st.cache_data.clear()
        st.rerun()


    st.markdown("---")
    st.subheader("📅 Bộ Lọc Thời Gian")

    # Xác định ngày có dữ liệu gần nhất
    max_date = df_shifts['date'].max() if not df_shifts.empty else datetime.now()
    min_date = df_shifts['date'].min() if not df_shifts.empty else (datetime.now() - timedelta(days=30))

    view_mode = st.radio(
        "Chế độ xem:",
        ["Ngày gần nhất", "Chọn ngày cụ thể", "📅 Theo Tuần (52 tuần)", "📆 Theo Tháng (12 tháng)", "Khoảng thời gian (Toàn bộ)"],
        index=0
    )

    selected_date = max_date
    date_range = (min_date, max_date)
    selected_week_sidebar = None
    selected_month_sidebar = None

    if view_mode == "Chọn ngày cụ thể":
        selected_date_input = st.date_input(
            "Chọn ngày:",
            value=max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        selected_date = datetime.combine(selected_date_input, datetime.min.time())
    elif view_mode == "📅 Theo Tuần (52 tuần)":
        selected_week_sidebar = st.selectbox("Chọn tuần trong năm (Tuần 1 - 52):", ALL_WEEKS_52, index=default_w_idx)
        selected_date = None
    elif view_mode == "📆 Theo Tháng (12 tháng)":
        selected_month_sidebar = st.selectbox("Chọn tháng trong năm (Tháng 1 - 12):", ALL_MONTHS_CODE_12, index=default_m_code_idx)
        selected_date = None
    elif view_mode == "Khoảng thời gian (Toàn bộ)":
        date_range_input = st.date_input(
            "Chọn khoảng ngày:",
            value=(max_date.date() - timedelta(days=14), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        if isinstance(date_range_input, tuple) and len(date_range_input) == 2:
            date_range = (
                datetime.combine(date_range_input[0], datetime.min.time()),
                datetime.combine(date_range_input[1], datetime.max.time())
            )

    # Lọc ca trưởng
    available_leaders = ["Tất cả"] + sorted(list(df_shifts[df_shifts['shift_leader'] != '']['shift_leader'].unique()))
    selected_leader = st.selectbox("Ca Trưởng:", available_leaders)

    st.markdown("---")
    st.markdown("""
    **Định mức kỹ thuật:**
    - Suất điện chuẩn: `170 - 175 kWh/tấn`
    - Năng suất ép: `≥ 4.0 tấn/h`
    - Độ ẩm thành phẩm: `8.0 - 9.5%`
    - Độ tro: `≤ 1.5%`
    """)

# Lọc dữ liệu theo ca trưởng nếu có
df_filtered_shifts = df_shifts.copy()
if selected_leader != "Tất cả":
    df_filtered_shifts = df_filtered_shifts[df_filtered_shifts['shift_leader'] == selected_leader]

# Tính KPI cho ngày/tuần/tháng được chọn
if view_mode == "📅 Theo Tuần (52 tuần)" and selected_week_sidebar:
    w_num = int(selected_week_sidebar.replace("Tuần ", ""))
    w_shifts = df_filtered_shifts[df_filtered_shifts['date'].dt.isocalendar().week == w_num]
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
    if not w_shifts.empty:
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

    kpis = {
        'date_str': f"{selected_week_sidebar} (Năm 2026)",
        'num_shifts': len(w_shifts),
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
elif view_mode == "📆 Theo Tháng (12 tháng)" and selected_month_sidebar:
    m_num, y_num = map(int, selected_month_sidebar.split('/'))
    m_shifts = df_filtered_shifts[
        (df_filtered_shifts['date'].dt.month == m_num) & 
        (df_filtered_shifts['date'].dt.year == y_num)
    ]
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
    if not m_shifts.empty:
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

    kpis = {
        'date_str': f"Tháng {selected_month_sidebar}",
        'num_shifts': len(m_shifts),
        'total_output': tot_out,
        'delta_output': 0.0,
        'avg_electricity_kwh_ton': avg_e,
        'electricity_eval': evaluate_electricity(avg_e),
        'avg_productivity': avg_p,
        'productivity_eval': evaluate_productivity(avg_p),
        'total_pellet_hours': tot_h,
        'processing_ratio': ratio_m,
        'do_am_tb_pct': 8.5,
        'equipment_hours': eq_m,
        'group_hours': group_h_m,
        'shift_details': m_shift_details,
    }
else:
    kpis = get_latest_day_kpis(df_filtered_shifts, df_daily, target_date=selected_date)

# ================= HEADER =================
st.title("🏭 HỆ THỐNG GIÁM SÁT & BÁO CÁO SẢN XUẤT TỰ ĐỘNG")
st.markdown(f"**Báo cáo ngày:** `{kpis.get('date_str', 'N/A')}` | **Số ca hoạt động:** `{kpis.get('num_shifts', 0)} ca`")

# ================= TOP KPI CARDS =================
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    delta_txt = f"{kpis.get('delta_output', 0):+,.1f} t so hôm trước" if kpis.get('delta_output', 0) != 0 else "Hôm nay"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Sản Lượng Thực Tế</div>
        <div class="kpi-value">{kpis.get('total_output', 0):,.1f}<span class="kpi-unit">Tấn</span></div>
        <div class="kpi-badge badge-info">{delta_txt}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    elec_eval = kpis.get('electricity_eval', {})
    badge_cls = "badge-success" if elec_eval.get('status') == 'EXCELLENT' else ("badge-info" if elec_eval.get('status') == 'STANDARD' else "badge-danger")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Suất Điện Tiêu Hao</div>
        <div class="kpi-value">{kpis.get('avg_electricity_kwh_ton', 0):.1f}<span class="kpi-unit">kWh/t</span></div>
        <div class="kpi-badge {badge_cls}">{elec_eval.get('icon', '')} {elec_eval.get('label', '')}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    prod_eval = kpis.get('productivity_eval', {})
    badge_cls = "badge-success" if prod_eval.get('status') == 'PASS' else "badge-warning"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Năng Suất Ép TB</div>
        <div class="kpi-value">{kpis.get('avg_productivity', 0):.2f}<span class="kpi-unit">Tấn/h</span></div>
        <div class="kpi-badge {badge_cls}">{prod_eval.get('icon', '')} {prod_eval.get('label', '')}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Tổng Giờ Máy Ép</div>
        <div class="kpi-value">{kpis.get('total_pellet_hours', 0):.1f}<span class="kpi-unit">Giờ</span></div>
        <div class="kpi-badge badge-info">8 Máy Ép Viên</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    ratio = kpis.get('processing_ratio', 0)
    am = kpis.get('do_am_tb_pct', 0)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Tỷ Lệ Chế Biến</div>
        <div class="kpi-value">{ratio:.2f}<span class="kpi-unit">lần</span></div>
        <div class="kpi-badge badge-info">Độ ẩm: {am:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    # Lấy dầu diezen tuần gần nhất
    latest_diesel = df_weekly.iloc[-1]['diezen_lit'] if not df_weekly.empty else 0.0
    latest_diesel_rate = df_weekly.iloc[-1]['diezen_tb_lit_tan'] if not df_weekly.empty else 0.0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Dầu Diezen Tiêu Thụ</div>
        <div class="kpi-value">{latest_diesel_rate:.1f}<span class="kpi-unit">Lít/tấn</span></div>
        <div class="kpi-badge badge-info">{latest_diesel:,.0f} Lít/tuần</div>
    </div>
    """, unsafe_allow_html=True)

# Hiển thị cảnh báo nổi bật nếu điện hoặc năng suất vượt ngưỡng
if elec_eval.get('status') == 'WARNING':
    st.error(f"⚠️ **CẢNH BÁO ĐIỆN NĂNG:** Suất tiêu hao điện đạt **{kpis.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, vượt định mức trần 175 kWh/tấn (+{elec_eval.get('diff')} kWh/tấn). Đề nghị kiểm tra phụ tải máy nghiền búa và hệ thống sấy.")
elif elec_eval.get('status') == 'EXCELLENT':
    st.success(f"✨ **HIỆU QUẢ CAO:** Suất tiêu hao điện chỉ **{kpis.get('avg_electricity_kwh_ton'):.1f} kWh/tấn**, thấp hơn định mức chuẩn 170 kWh/tấn.")

# ================= MAIN TABS =================
tab1, tab_kpi, tab2, tab3, tab_incidents, tab_maint_log, tab_maint_plan, tab4, tab5 = st.tabs([
    "📋 Nhật Ký Ca & Thiết Bị Ngày",
    "🎯 Đánh Giá & Xếp Hạng KPI",
    "📈 Xu Hướng Tuần & Tháng",
    "⚙️ Giám Sát Cụm Thiết Bị",
    "🚨 Quản Lý & Cảnh Báo Sự Cố (Sheet Sự Cố)",
    "🔧 Nhật Ký Bảo Trì & Sửa Chữa (2026 BẢO TRÌ BVN)",
    "🛠️ Kế Hoạch Bảo Trì & Quản Trị 4M (Mainternance BVN QB)",
    "🔬 Chất Lượng KCS & Dầu Diezen",
    "👤 Lịch Sử Sản Xuất Ca Trưởng"
])

# ----------------- TAB 1: NHẬT KÝ CA & THIẾT BỊ NGÀY -----------------
with tab1:
    st.markdown('<div class="section-title">📊 Chi Tiết Các Ca Sản Xuất Trong Ngày</div>', unsafe_allow_html=True)
    
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
with tab_kpi:
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
            st.markdown("#### 📈 Diễn Biến Tổng Điểm KPI Ca Trưởng Qua Các Tuần (Tuần 31 - 38)")
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
            st.markdown("#### 📈 So Sánh Tổng Điểm KPI Qua Các Tháng (Tháng 8 vs Tháng 9)")
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
    
    tab_c1, tab_c2, tab_c3 = st.tabs(["⚡ Suất Điện Năng (kWh/tấn)", "🚀 Năng Suất Ép (tấn/h)", "💧 Độ Ẩm Viên Nén (%)"])

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
with tab2:
    st.markdown('<div class="section-title">📈 Xu Hướng & Cảnh Báo Định Mức Điện Năng (kWh/tấn)</div>', unsafe_allow_html=True)
    
    # Biểu đồ đường điện năng theo ngày với đường định mức
    df_day_trend = df_shifts.groupby('date').agg(
        total_output=('san_luong_tan', 'sum'),
        total_elec=('dien_kwh', 'sum'),
        total_hours=('tong_gio_ep', 'sum')
    ).reset_index()
    df_day_trend['kwh_per_ton'] = df_day_trend['total_elec'] / df_day_trend['total_output']
    df_day_trend['tph'] = df_day_trend['total_output'] / df_day_trend['total_hours']
    df_day_trend = df_day_trend[(df_day_trend['total_output'] > 0) & (df_day_trend['kwh_per_ton'] > 50)].tail(45)

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
with tab3:
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
with tab_incidents:
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
with tab_maint_log:
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
with tab_maint_plan:
    st.markdown('<div class="section-title">🛠️ KẾ HOẠCH BẢO TRÌ ĐỊNH KỲ & QUẢN TRỊ CHIẾN LƯỢC 4M</div>', unsafe_allow_html=True)
    st.caption(f"Nguồn dữ liệu: **{maint_plan_title}** (Google Sheets ID: `1d7cmTioaJyRSGxgC7ArPUnmBtTvToby-vNCsgXV1bOQ`)")

    subtab_plan, subtab_4m = st.tabs([
        "📅 KẾ HOẠCH BẢO TRÌ THEO THÁNG",
        "🎯 QUẢN TRỊ CHIẾN LƯỢC 4M (6 THÁNG CUỐI NĂM 2026)"
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

# ----------------- TAB 4: KCS & DẦU DIEZEN -----------------
with tab4:
    col_kcs_left, col_diezen_right = st.columns(2)

    with col_kcs_left:
        st.markdown('<div class="section-title">🧪 Chất Lượng KCS: Độ Ẩm & Độ Tro</div>', unsafe_allow_html=True)
        if not df_kcs.empty:
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
                title="Độ Ẩm Viên Nén (%) Gần Đây",
                xaxis_title="Ngày đo",
                yaxis_title="%",
                height=300,
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_am, use_container_width=True)

            st.dataframe(
                recent_kcs[['date_str', 'time_sample', 'shift_leader', 'am_sau_say_1_pct', 'am_sau_say_2_pct', 'am_vien_pct', 'do_tro_pct']].tail(10),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Chưa có dữ liệu KCS.")

    with col_diezen_right:
        st.markdown('<div class="section-title">⛽ Tiêu Thụ Dầu Diezen Theo Phương Tiện</div>', unsafe_allow_html=True)
        if not df_diezen.empty:
            # Lấy dòng mới nhất để xem phân bổ dầu theo xe
            latest_dz = df_diezen.iloc[-1].to_dict()
            vehicles = [k for k in latest_dz.keys() if k not in ['month', 'week', 'week_label', 'tong_diezen_lit'] and isinstance(latest_dz[k], (int, float)) and latest_dz[k] > 0]
            
            if vehicles:
                dz_breakdown = [{'Thiết bị': v, 'Lít': latest_dz[v]} for v in vehicles]
                df_dz_pie = pd.DataFrame(dz_breakdown)
                fig_dz = px.pie(
                    df_dz_pie,
                    names='Thiết bị',
                    values='Lít',
                    title=f"Phân Bổ Tiêu Thụ Dầu Diezen - {latest_dz.get('week_label', '')}",
                    hole=0.4
                )
                fig_dz.update_traces(textinfo='percent+label')
                fig_dz.update_layout(height=300, margin=dict(t=30, b=20, l=20, r=20))
                st.plotly_chart(fig_dz, use_container_width=True)

            st.dataframe(df_diezen.tail(6), hide_index=True, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu dầu Diezen.")

# ----------------- TAB 5: HIỆU SUẤT CA TRƯỞNG -----------------
with tab5:
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

# Footer
st.markdown("---")
st.caption(f"Hệ Thống Báo Cáo Sản Xuất Tự Động Viên Nén Gỗ | Dữ liệu cập nhật thời gian thực từ Google Sheets | Phiên bản 1.0")

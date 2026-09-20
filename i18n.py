"""
Module Bản Địa Hóa & Song Ngữ (Internationalization - i18n)
Hỗ trợ chuyển đổi song ngữ Tiếng Việt 🇻🇳 và Tiếng Anh 🇬🇧 cho Dashboard Nhà Máy Viên Nén Gỗ BVN Quảng Bình.
"""
import re
from typing import List, Dict, Any, Optional
import streamlit as st

APP_LANG_KEY = 'app_lang'

# Danh mục 14 tác vụ phân 3 nhóm (Tiếng Việt & Tiếng Anh)
OP_TASKS_VI = [
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

OP_TASKS_EN = [
    "📋 1. Production Shift Log",
    "🎯 2. KPI Evaluation & Ranking",
    "📈 3. Weekly & Monthly Trends",
    "⚙️ 4. Equipment Monitoring",
    "🚨 5. Incident Alerts",
    "🔧 6. Maintenance Log",
    "🛠️ 7. 4M Maintenance Plan",
    "🔬 8. QC / KCS Inspection",
    "⛽ 9. Diesel Fuel Management",
    "👤 10. Shift Leader History"
]

STATIC_TASKS_VI = [
    "👥 11. Sơ Đồ Nhân Sự",
    "🌲 12. Quy Trình Chế Biến Gỗ",
    "📐 13. Sơ Đồ Nguyên Lý"
]

STATIC_TASKS_EN = [
    "👥 11. Organization Chart",
    "🌲 12. Wood Processing Flow",
    "📐 13. Schematic Diagram"
]

ENTRY_TASKS_VI = [
    "📝 14. Nhập Báo Cáo Ca & KCS"
]

ENTRY_TASKS_EN = [
    "📝 14. Shift & QC Data Entry"
]

TIME_MODES_VI = [
    "☀️ Theo Ngày",
    "📅 Theo Tuần",
    "📆 Theo Tháng",
    "🏛️ Theo Năm",
    "⏱️ Khoảng ngày"
]

TIME_MODES_EN = [
    "☀️ Daily",
    "📅 Weekly",
    "📆 Monthly",
    "🏛️ Yearly",
    "⏱️ Date Range"
]

DASHBOARD_CHOICES_VI = [
    "Tất Cả (1 Dashboard Tổng + 3 Dashboard Ca Trưởng)",
    "Chỉ Dashboard Tổng Thể",
    "Dashboard Ca Trưởng Long (Ca A)",
    "Dashboard Ca Trưởng Sắc (Ca B)",
    "Dashboard Ca Trưởng Tài (Ca C)"
]

DASHBOARD_CHOICES_EN = [
    "All (1 Plant Overview + 3 Shift Dashboards)",
    "Plant Overview Only",
    "Shift Leader Long (Shift A) Dashboard",
    "Shift Leader Sac (Shift B) Dashboard",
    "Shift Leader Tai (Shift C) Dashboard"
]

# Từ điển ánh xạ đánh giá kỹ thuật & trạng thái
EVAL_DICT = {
    # Tiết kiệm điện / suất điện
    "TIẾT KIỆM ĐIỆN": "POWER SAVING",
    "VƯỢT ĐỊNH MỨC": "OVER LIMIT",
    "TRONG ĐỊNH MỨC": "WITHIN LIMIT",
    "ĐẠT CHUẨN": "STANDARD PASS",
    "TIÊU THỤ CAO": "HIGH CONSUMPTION",
    "ĐẠT CHỈ TIÊU": "TARGET MET",
    "CHƯA ĐẠT CHỈ TIÊU": "BELOW TARGET",
    "ĐẠT CHUẨN XUẤT KHẨU": "EXPORT COMPLIANT",
    "ẨM CAO": "HIGH MOISTURE",
    "ẨM THẤP": "LOW MOISTURE",
    "ĐẠT CHUẨN ENplus": "ENplus COMPLIANT",
    "CHƯA ĐẠT CHUẨN": "NON-COMPLIANT",
    "Xuất sắc": "Excellent",
    "Khá tốt": "Good",
    "Cần cải thiện": "Needs Improvement",
    "Tối ưu": "Optimal",
    "Bình thường": "Normal",
    "Nguy hiểm": "Critical",
    "Chờ số liệu": "Pending data",
    "Hôm nay": "Today",
    "Kỳ này": "Current Period",
    # KPI Ranks
    "Xuất Sắc (A+)": "Excellent (A+)",
    "Tốt (A)": "Good (A)",
    "Khá (B+)": "Fair (B+)",
    "Đạt Yêu Cầu (B)": "Pass (B)",
    "Cần Cải Thiện (C)": "Needs Improvement (C)",
    "Chưa xếp hạng": "Unranked",
    "XUẤT SẮC": "EXCELLENT",
    "TỐT": "GOOD",
    "KHÁ": "FAIR",
    "ĐẠT YÊU CẦU": "PASS",
    "CẦN CẢI THIỆN": "NEEDS IMPROVEMENT"
}


def get_lang() -> str:
    """
    Lấy mã ngôn ngữ hiện tại ('vi' hoặc 'en').
    Ưu tiên:
    1. st.session_state[APP_LANG_KEY]
    2. URL query parameters: ?lang=en hoặc ?locale=en (đặc biệt quan trọng trên iPhone/Safari/PWA)
    3. Mặc định 'vi'
    """
    if APP_LANG_KEY in st.session_state:
        return st.session_state[APP_LANG_KEY]

    # Kiểm tra URL query parameter nếu có
    try:
        qp = st.query_params
        lang_param = qp.get('lang') or qp.get('locale')
        if lang_param:
            l_str = str(lang_param).lower().strip()
            if l_str in ('en', 'vi'):
                st.session_state[APP_LANG_KEY] = l_str
                return l_str
    except Exception:
        pass

    return 'vi'


def set_lang(lang: str):
    """
    Đặt mã ngôn ngữ hiện tại ('vi' hoặc 'en') vào st.session_state 
    và đồng bộ vào URL query parameters (?lang=...) 
    để trên iPhone không bị mất phiên khi tải lại trang hoặc mở lại từ màn hình chính.
    """
    if lang in ('vi', 'en'):
        st.session_state[APP_LANG_KEY] = lang
        try:
            st.query_params['lang'] = lang
        except Exception:
            pass


def apply_language_change(new_lang: str):
    """
    Chuyển đổi và đồng bộ toàn diện trạng thái ứng dụng khi đổi ngôn ngữ ('vi' <-> 'en').
    Cập nhật st.session_state, URL query params, và dịch chuyển các widget điều hướng.
    """
    if new_lang not in ('vi', 'en'):
        return
    set_lang(new_lang)

    # Đồng bộ widget radio trong sidebar
    st.session_state['lang_radio_select'] = "🇬🇧 English" if new_lang == 'en' else "🇻🇳 Tiếng Việt"

    # Đồng bộ tên tác vụ hiện tại sang ngôn ngữ mới
    if 'active_task' in st.session_state:
        st.session_state['active_task'] = map_task_name(st.session_state['active_task'], new_lang)
    if 'main_task_dropdown' in st.session_state:
        st.session_state['main_task_dropdown'] = map_task_name(st.session_state['main_task_dropdown'], new_lang)

    # Đồng bộ chế độ xem thời gian
    if 'main_view_mode_radio' in st.session_state:
        st.session_state['main_view_mode_radio'] = map_time_mode(st.session_state['main_view_mode_radio'], new_lang)
    if 'top_view_mode' in st.session_state:
        st.session_state['top_view_mode'] = map_time_mode(st.session_state['top_view_mode'], new_lang)

    # Đồng bộ lựa chọn Dashboard
    if 'main_db_view_radio' in st.session_state:
        st.session_state['main_db_view_radio'] = map_dashboard_choice(st.session_state['main_db_view_radio'], new_lang)
    if 'main_db_view_choice' in st.session_state:
        st.session_state['main_db_view_choice'] = map_dashboard_choice(st.session_state['main_db_view_choice'], new_lang)

    # Đồng bộ chế độ xem thi đua ca trưởng
    if 'leader_kpi_time_view_segmented' in st.session_state:
        cur_k = st.session_state['leader_kpi_time_view_segmented']
        if 'tuần' in str(cur_k).lower() or 'week' in str(cur_k).lower():
            st.session_state['leader_kpi_time_view_segmented'] = "📅 Weekly" if new_lang == 'en' else "📅 Theo Tuần"
        elif 'tháng' in str(cur_k).lower() or 'month' in str(cur_k).lower():
            st.session_state['leader_kpi_time_view_segmented'] = "📆 Monthly" if new_lang == 'en' else "📆 Theo Tháng"
        else:
            st.session_state['leader_kpi_time_view_segmented'] = "☀️ Daily" if new_lang == 'en' else "☀️ Theo Ngày"


def is_en() -> bool:
    """Kiểm tra có đang ở chế độ Tiếng Anh hay không"""
    return get_lang() == 'en'


def t(vi: str, en: str, lang: Optional[str] = None) -> str:
    """
    Trả về chuỗi Tiếng Việt hoặc Tiếng Anh tùy thuộc ngôn ngữ hiện tại.
    Ví dụ: t("Sản Lượng Thực Tế", "Actual Output")
    """
    target = lang or get_lang()
    return en if target == 'en' else vi


def get_op_tasks(lang: Optional[str] = None) -> List[str]:
    target = lang or get_lang()
    return OP_TASKS_EN if target == 'en' else OP_TASKS_VI


def get_static_tasks(lang: Optional[str] = None) -> List[str]:
    target = lang or get_lang()
    return STATIC_TASKS_EN if target == 'en' else STATIC_TASKS_VI


def get_entry_tasks(lang: Optional[str] = None) -> List[str]:
    target = lang or get_lang()
    return ENTRY_TASKS_EN if target == 'en' else ENTRY_TASKS_VI


def get_all_tasks(lang: Optional[str] = None) -> List[str]:
    return get_op_tasks(lang) + get_static_tasks(lang) + get_entry_tasks(lang)


def get_task_number(task_str: str) -> int:
    """Trích xuất số thứ tự tác vụ 1..14 từ chuỗi tên tác vụ"""
    m = re.search(r'(\d+)\.', str(task_str))
    return int(m.group(1)) if m else 1


def map_task_name(task_str: str, target_lang: Optional[str] = None) -> str:
    """
    Chuyển đổi tên tác vụ từ ngôn ngữ này sang ngôn ngữ khác theo đúng số thứ tự 1..14.
    Đảm bảo khi đổi ngôn ngữ, người dùng vẫn ở nguyên tab tác vụ đó.
    """
    if not task_str:
        return get_op_tasks(target_lang)[0]
    num = get_task_number(task_str)
    all_target = get_all_tasks(target_lang)
    for t_item in all_target:
        if get_task_number(t_item) == num:
            return t_item
    return all_target[0]


def get_time_modes(lang: Optional[str] = None) -> List[str]:
    target = lang or get_lang()
    return TIME_MODES_EN if target == 'en' else TIME_MODES_VI


def map_time_mode(mode_str: str, target_lang: Optional[str] = None) -> str:
    """Ánh xạ chế độ lọc thời gian khi chuyển ngôn ngữ"""
    target_modes = get_time_modes(target_lang)
    target_l = target_lang or get_lang()
    source_modes = TIME_MODES_EN if target_l == 'vi' else TIME_MODES_VI
    for idx, sm in enumerate(source_modes):
        if sm == mode_str:
            return target_modes[idx]
    # Fallback theo từ khóa
    mode_str_low = mode_str.lower()
    if 'ngày' in mode_str_low or 'day' in mode_str_low or 'daily' in mode_str_low:
        return target_modes[0]
    if 'tuần' in mode_str_low or 'week' in mode_str_low:
        return target_modes[1]
    if 'tháng' in mode_str_low or 'month' in mode_str_low:
        return target_modes[2]
    if 'năm' in mode_str_low or 'year' in mode_str_low:
        return target_modes[3]
    if 'khoảng' in mode_str_low or 'range' in mode_str_low:
        return target_modes[4]
    return target_modes[0]


def get_dashboard_choices(lang: Optional[str] = None) -> List[str]:
    target = lang or get_lang()
    return DASHBOARD_CHOICES_EN if target == 'en' else DASHBOARD_CHOICES_VI


def map_dashboard_choice(choice_str: str, target_lang: Optional[str] = None) -> str:
    """Ánh xạ lựa chọn Dashboard khi chuyển ngôn ngữ"""
    target_choices = get_dashboard_choices(target_lang)
    choice_str_low = str(choice_str).lower()
    if 'tất cả' in choice_str_low or 'all' in choice_str_low:
        return target_choices[0]
    if 'chỉ dashboard tổng' in choice_str_low or 'overview only' in choice_str_low:
        return target_choices[1]
    if 'long' in choice_str_low or 'ca a' in choice_str_low or 'shift a' in choice_str_low:
        return target_choices[2]
    if 'sắc' in choice_str_low or 'sac' in choice_str_low or 'ca b' in choice_str_low or 'shift b' in choice_str_low:
        return target_choices[3]
    if 'tài' in choice_str_low or 'tai' in choice_str_low or 'ca c' in choice_str_low or 'shift c' in choice_str_low:
        return target_choices[4]
    return target_choices[0]


def translate_eval(text: str, lang: Optional[str] = None) -> str:
    """Dịch các nhãn đánh giá kỹ thuật sang Tiếng Anh nếu đang ở chế độ EN"""
    target = lang or get_lang()
    if target != 'en' or not text:
        return text
    clean_txt = str(text).strip()
    return EVAL_DICT.get(clean_txt, clean_txt)


def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để hiển thị danh từ riêng, tên người trên giao diện tiếng Anh."""
    if not text:
        return ''
    import unicodedata
    text = str(text)
    text = text.replace('Đ', 'D').replace('đ', 'd')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return unicodedata.normalize('NFC', text)


def format_person_name(name: str) -> str:
    """Nếu đang ở chế độ tiếng Anh, chuyển tên người / danh từ riêng sang không dấu."""
    if not name:
        return ''
    if is_en():
        return strip_accents(name)
    return str(name)


def translate_comparison_df(df: Any) -> Any:
    """Dịch bảng đối sánh toàn diện sang tiếng Anh khi is_en() == True"""
    if df is None or not hasattr(df, 'empty') or df.empty or not is_en():
        return df
    df_res = df.copy()
    col_map = {
        'Chỉ Số Đo Lường': 'Metric',
        '🏭 Toàn Nhà Máy': '🏭 Plant-Wide',
        '🔵 Ca Long': '🔵 Shift Long (A)',
        '🟢 Ca Sắc': '🟢 Shift Sac (B)',
        '🟠 Ca Tài': '🟠 Shift Tai (C)',
        '🔵 Ca A': '🔵 Shift A',
        '🟢 Ca B': '🟢 Shift B',
        '🟠 Ca C': '🟠 Shift C',
        'Định Mức Kỹ Thuật': 'Technical Standard'
    }
    df_res.rename(columns=col_map, inplace=True)
    
    metric_map = {
        'Sản lượng thực tế (tấn)': 'Actual Output (tons)',
        'Suất tiêu hao điện (kWh/tấn)': 'Power Consumption Rate (kWh/ton)',
        'Năng suất ép trung bình (tấn/h)': 'Avg Press Productivity (tons/h)',
        'Tổng giờ máy ép (giờ)': 'Total Press Hours (h)',
        'Độ ẩm trung bình viên (%)': 'Avg Pellet Moisture (%)',
        'Tỷ lệ chế biến (lần)': 'Processing Ratio (times)',
        'Điểm KPI thi đua (/100)': 'KPI Score (/100)'
    }
    if 'Metric' in df_res.columns:
        df_res['Metric'] = df_res['Metric'].replace(metric_map)

    std_map = {
        'Kế hoạch ngày': 'Daily Target',
        '170 - 175 kWh/t': '170 - 175 kWh/t',
        '≥ 4.0 tấn/h': '≥ 4.0 tons/h',
        '8 Máy Ép': '8 Pellet Mills',
        '8.0 - 9.5%': '8.0 - 9.5%',
        '1.8 - 2.1': '1.8 - 2.1',
        'Thang 100 điểm': '100-point scale'
    }
    if 'Technical Standard' in df_res.columns:
        df_res['Technical Standard'] = df_res['Technical Standard'].replace(std_map)

    for col in ['🔵 Shift Long (A)', '🟢 Shift Sac (B)', '🟠 Shift Tai (C)', '🔵 Shift Long', '🟢 Shift Sac', '🟠 Shift Tai', '🔵 Shift A', '🟢 Shift B', '🟠 Shift C']:
        if col in df_res.columns:
            df_res[col] = df_res[col].astype(str).str.replace('(tháng)', '(month)', regex=False)
            df_res[col] = df_res[col].str.replace('(Lk:', '(Acc:', regex=False)
            df_res[col] = df_res[col].str.replace('Xuất Sắc', 'Excellent', regex=False)
            df_res[col] = df_res[col].str.replace('Xuất sắc', 'Excellent', regex=False)
            df_res[col] = df_res[col].str.replace('Khá tốt', 'Good', regex=False)
            df_res[col] = df_res[col].str.replace('Tốt', 'Good', regex=False)
            df_res[col] = df_res[col].str.replace('Khá', 'Fair', regex=False)
            df_res[col] = df_res[col].str.replace('Đạt Yêu Cầu', 'Pass', regex=False)
            df_res[col] = df_res[col].str.replace('Đạt', 'Pass', regex=False)
            df_res[col] = df_res[col].str.replace('Cần Cải Thiện', 'Needs Improvement', regex=False)
            df_res[col] = df_res[col].str.replace('Cần cải thiện', 'Needs Improvement', regex=False)
    return df_res


def translate_wm_weekly(df: Any) -> Any:
    """Dịch bảng điểm W-M KPI tuần sang tiếng Anh khi is_en() == True"""
    if df is None or not hasattr(df, 'empty') or df.empty or not is_en():
        return df
    df_res = df.copy()
    col_map = {
        'week': 'Week',
        'week_label': 'Week Label',
        'Long': 'Long',
        'Sắc': 'Sac',
        'Tài': 'Tai',
        'Ca A': 'Shift A',
        'Ca B': 'Shift B',
        'Ca C': 'Shift C'
    }
    df_res.rename(columns=col_map, inplace=True)
    if 'Week Label' in df_res.columns:
        df_res['Week Label'] = df_res['Week Label'].astype(str).str.replace('Tuần ', 'Week ', regex=False)
    return df_res


def translate_wm_monthly(df: Any) -> Any:
    """Dịch bảng điểm W-M KPI tháng sang tiếng Anh khi is_en() == True"""
    if df is None or not hasattr(df, 'empty') or df.empty or not is_en():
        return df
    df_res = df.copy()
    col_map = {
        'month_label': 'Month',
        'Long': 'Long',
        'Sắc': 'Sac',
        'Tài': 'Tai',
        'Ca A': 'Shift A',
        'Ca B': 'Shift B',
        'Ca C': 'Shift C'
    }
    df_res.rename(columns=col_map, inplace=True)
    if 'Month' in df_res.columns:
        df_res['Month'] = df_res['Month'].astype(str).str.replace('Tháng ', 'Month ', regex=False)
    return df_res


def translate_shift_leader_kpis(df: Any) -> Any:
    """Dịch bảng KPIs Ca Trưởng sang tiếng Anh khi is_en() == True"""
    if df is None or not hasattr(df, 'empty') or df.empty or not is_en():
        return df
    df_res = df.copy()
    col_map = {
        'Ca Trưởng': 'Shift Leader',
        'Số ca phụ trách': 'Assigned Shifts',
        'Tổng sản lượng (tấn)': 'Total Output (tons)',
        'Sản lượng TB/ca (tấn)': 'Avg Output/Shift (tons)',
        'Điện năng TB (kWh/tấn)': 'Avg Power (kWh/ton)',
        'Năng suất ép TB (tấn/h)': 'Avg Press Productivity (t/h)',
        'Tổng giờ ép (h)': 'Total Press Hours (h)',
        'Năng suất TB (tấn/h)': 'Avg Productivity (t/h)',
        'Độ ẩm TB (%)': 'Avg Moisture (%)'
    }
    df_res.rename(columns=col_map, inplace=True)
    if 'Shift Leader' in df_res.columns:
        df_res['Shift Leader'] = df_res['Shift Leader'].apply(lambda x: format_person_name(str(x)))
    return df_res



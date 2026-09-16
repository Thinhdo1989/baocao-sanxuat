"""
Module tính toán các chỉ số sản xuất (KPI), suất tiêu hao và gắn cờ cảnh báo.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Định mức chuẩn ngành sản xuất viên nén gỗ theo yêu cầu
ELEC_MIN_BENCHMARK = 170.0    # kWh/tấn
ELEC_MAX_BENCHMARK = 175.0    # kWh/tấn
PRODUCTIVITY_TARGET = 4.0     # tấn/h
MOISTURE_TARGET_MIN = 8.0     # %
MOISTURE_TARGET_MAX = 9.5     # %
ASH_TARGET_MAX = 1.5          # %
DENSITY_BENCHMARK_MIN = 600.0 # kg/m3 - Chuẩn tỷ trọng xuất khẩu ENplus/ISO 17225-2

# Danh mục thiết bị
EQUIPMENT_INFO = {
    'HM118': {'name': 'Nghiền búa thô HM118', 'brand': 'Andritz', 'group': 'Nghiền búa thô', 'col': 'h_HM118'},
    'HM218': {'name': 'Nghiền búa thô HM218', 'brand': 'Andritz', 'group': 'Nghiền búa thô', 'col': 'h_HM218'},
    'HM318': {'name': 'Nghiền búa thô HM318', 'brand': 'SHT', 'group': 'Nghiền búa thô', 'col': 'h_HM318'},
    'DR124': {'name': 'Trống sấy DR124', 'brand': 'Trống sấy', 'group': 'Trống sấy', 'col': 'h_DR124'},
    'DR224': {'name': 'Trống sấy DR224', 'brand': 'Trống sấy', 'group': 'Trống sấy', 'col': 'h_DR224'},
    'HM147': {'name': 'Nghiền búa tinh HM147', 'brand': 'SHT', 'group': 'Nghiền búa tinh', 'col': 'h_HM147'},
    'HM247': {'name': 'Nghiền búa tinh HM247', 'brand': 'Andritz', 'group': 'Nghiền búa tinh', 'col': 'h_HM247'},
    'HM347': {'name': 'Nghiền búa tinh HM347', 'brand': 'Andritz', 'group': 'Nghiền búa tinh', 'col': 'h_HM347'},
    'PE1': {'name': 'Máy ép viên PE1', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE1'},
    'PE2': {'name': 'Máy ép viên PE2', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE2'},
    'PE3': {'name': 'Máy ép viên PE3', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE3'},
    'PE4': {'name': 'Máy ép viên PE4', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE4'},
    'PE5': {'name': 'Máy ép viên PE5', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE5'},
    'PE6': {'name': 'Máy ép viên PE6', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE6'},
    'PE7': {'name': 'Máy ép viên PE7', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE7'},
    'PE8': {'name': 'Máy ép viên PE8', 'brand': 'Pellet Mill', 'group': 'Máy ép viên', 'col': 'h_PE8'},
}

def evaluate_electricity(kwh_per_ton: float) -> Dict[str, Any]:
    """
    Đánh giá suất tiêu hao điện năng (kWh/tấn) so với định mức chuẩn 170 - 175 kWh/tấn.
    """
    if kwh_per_ton <= 0:
        return {
            'status': 'UNKNOWN',
            'label': 'Chưa có dữ liệu',
            'badge': 'secondary',
            'color': '#6c757d',
            'icon': '⚪',
            'message': 'Chưa ghi nhận điện năng tiêu thụ',
            'diff': 0.0
        }
    elif kwh_per_ton < ELEC_MIN_BENCHMARK:
        diff = round(kwh_per_ton - ELEC_MIN_BENCHMARK, 2)
        return {
            'status': 'EXCELLENT',
            'label': 'Tiết kiệm điện',
            'badge': 'success',
            'color': '#28a745',
            'icon': '🟢',
            'message': f'Rất tốt! Thấp hơn định mức {abs(diff)} kWh/tấn (< 170 kWh/tấn)',
            'diff': diff
        }
    elif ELEC_MIN_BENCHMARK <= kwh_per_ton <= ELEC_MAX_BENCHMARK:
        return {
            'status': 'STANDARD',
            'label': 'Đạt định mức',
            'badge': 'info',
            'color': '#17a2b8',
            'icon': '🔵',
            'message': 'Đạt định mức chuẩn (170 - 175 kWh/tấn)',
            'diff': 0.0
        }
    else:
        diff = round(kwh_per_ton - ELEC_MAX_BENCHMARK, 2)
        return {
            'status': 'WARNING',
            'label': 'VƯỢT ĐỊNH MỨC',
            'badge': 'danger',
            'color': '#dc3545',
            'icon': '🔴',
            'message': f'Cảnh báo: Vượt chuẩn +{diff} kWh/tấn (> 175 kWh/tấn)! Cần rà soát tải máy ép/sấy.',
            'diff': diff
        }


def evaluate_productivity(tph: float) -> Dict[str, Any]:
    """
    Đánh giá năng suất ép trung bình (tấn/h) so với chỉ tiêu >= 4.0 tấn/h.
    """
    if tph <= 0:
        return {
            'status': 'UNKNOWN',
            'label': 'Chưa có dữ liệu',
            'badge': 'secondary',
            'color': '#6c757d',
            'icon': '⚪',
            'message': 'Chưa ghi nhận giờ ép',
            'diff': 0.0
        }
    diff = round(tph - PRODUCTIVITY_TARGET, 2)
    if tph >= PRODUCTIVITY_TARGET:
        return {
            'status': 'PASS',
            'label': 'Đạt chỉ tiêu',
            'badge': 'success',
            'color': '#28a745',
            'icon': '🟢',
            'message': f'Đạt chỉ tiêu (>= 4.0 tấn/h), vượt +{diff} tấn/h',
            'diff': diff
        }
    else:
        return {
            'status': 'WARNING',
            'label': 'CHƯA ĐẠT CHỈ TIÊU',
            'badge': 'warning',
            'color': '#ffc107',
            'icon': '🟠',
            'message': f'Chưa đạt chỉ tiêu 4.0 tấn/h (thiếu {abs(diff)} tấn/h). Cần tối ưu dòng cấp liệu.',
            'diff': diff
        }


def evaluate_moisture(moisture_pct: float) -> Dict[str, Any]:
    """
    Đánh giá độ ẩm viên nén (chuẩn: 8.0 - 9.5%)
    """
    if moisture_pct <= 0:
        return {'status': 'UNKNOWN', 'label': 'N/A', 'color': '#6c757d'}
    if MOISTURE_TARGET_MIN <= moisture_pct <= MOISTURE_TARGET_MAX:
        return {'status': 'PASS', 'label': 'Đạt chuẩn (8 - 9.5%)', 'color': '#28a745', 'icon': '🟢'}
    elif moisture_pct < MOISTURE_TARGET_MIN:
        return {'status': 'WARN', 'label': 'Quá khô (< 8%)', 'color': '#ffc107', 'icon': '🟠'}
    else:
        return {'status': 'ALERT', 'label': 'Độ ẩm cao (> 9.5%)', 'color': '#dc3545', 'icon': '🔴'}


def evaluate_ash(ash_pct: float) -> Dict[str, Any]:
    """
    Đánh giá độ tro viên nén (chuẩn: <= 1.5%)
    """
    if ash_pct <= 0:
        return {'status': 'UNKNOWN', 'label': 'N/A', 'color': '#6c757d'}
    if ash_pct <= ASH_TARGET_MAX:
        return {'status': 'PASS', 'label': f'Đạt chuẩn (<= {ASH_TARGET_MAX}%)', 'color': '#28a745', 'icon': '🟢'}
    else:
        return {'status': 'ALERT', 'label': f'Độ tro cao (> {ASH_TARGET_MAX}%)', 'color': '#dc3545', 'icon': '🔴'}


def evaluate_density(density: float) -> Dict[str, Any]:
    """
    Đánh giá tỷ trọng viên nén (chuẩn xuất khẩu ENplus / ISO 17225-2: >= 600 kg/m3)
    """
    if density <= 0:
        return {'status': 'UNKNOWN', 'label': 'Chưa đo', 'color': '#6c757d', 'icon': '⚪'}
    if density >= DENSITY_BENCHMARK_MIN:
        return {'status': 'PASS', 'label': f'Đạt chuẩn (≥ {DENSITY_BENCHMARK_MIN:,.0f} kg/m³)', 'color': '#15803d', 'icon': '🟢'}
    else:
        return {'status': 'WARN', 'label': f'Thấp (< {DENSITY_BENCHMARK_MIN:,.0f} kg/m³)', 'color': '#b45309', 'icon': '🟠'}


def classify_shift_counts(df_subset: pd.DataFrame, num_days: Optional[int] = None, is_single_leader: bool = False) -> Tuple[int, int, int]:
    """
    Phân loại và đếm 3 loại ca trong tập dữ liệu:
    - 🏭 Ca sản xuất (prod_shifts): ca có sản lượng > 0 hoặc giờ ép > 0 và không thuộc ca bảo trì
    - 🔧 Ca bảo trì (maint_shifts): tên ca trưởng hoặc nội dung chứa 'bảo trì', 'vệ sinh', 'bảo dưỡng'
    - ☕ Ca nghỉ (off_shifts): số ca còn lại theo định mức chuẩn 3 ca/ngày (hoặc ghi nhận 'Nghĩ')
    Trả về tuple: (prod_shifts, maint_shifts, off_shifts)
    """
    if df_subset is None or df_subset.empty:
        if num_days and num_days > 0:
            expected_per_d = 1 if is_single_leader else 3
            return 0, 0, num_days * expected_per_d
        return 0, 0, 0

    shift_str = df_subset['shift_leader'].astype(str).str.lower() if 'shift_leader' in df_subset.columns else pd.Series([''] * len(df_subset), index=df_subset.index)
    maint_mask = shift_str.str.contains('bảo trì|vệ sinh|bảo dưỡng|bảo trì-vs|bảo trì - vs', regex=True, na=False)
    
    sl_col = df_subset['san_luong_tan'] if 'san_luong_tan' in df_subset.columns else 0
    h_col = df_subset['tong_gio_ep'] if 'tong_gio_ep' in df_subset.columns else 0
    prod_mask = ((sl_col > 0) | (h_col > 0)) & (~maint_mask)

    prod_count = int(prod_mask.sum())
    maint_count = int(maint_mask.sum())

    if num_days is None:
        if 'date' in df_subset.columns and not df_subset.empty:
            num_days = int(df_subset['date'].dt.date.nunique())
        else:
            num_days = 1

    expected_per_day = 1 if is_single_leader else 3
    total_expected = max(len(df_subset), num_days * expected_per_day)
    off_count = max(0, total_expected - (prod_count + maint_count))

    return prod_count, maint_count, off_count


def get_latest_day_kpis(df_shifts: pd.DataFrame, df_daily: pd.DataFrame = None, df_kcs: pd.DataFrame = None, target_date: Any = None) -> Dict[str, Any]:
    """
    Tính toán toàn diện chỉ số KPI cho ngày gần nhất hoặc ngày được chọn.
    """
    if df_shifts.empty:
        return {}

    # Xác định ngày mục tiêu: nếu không chỉ định, lấy ngày có sản lượng mới nhất
    df_valid = df_shifts[df_shifts['san_luong_tan'] > 0]
    if df_valid.empty:
        df_valid = df_shifts

    if target_date is None:
        target_date = df_shifts['date'].max() if 'date' in df_shifts.columns else df_valid['date'].max()
    else:
        target_date = pd.to_datetime(target_date)

    # Lọc dữ liệu của ngày được chọn
    day_shifts = df_shifts[df_shifts['date'].dt.date == target_date.date()]
    if day_shifts.empty:
        # Nếu ngày được chọn không có ca, thử tìm ngày gần nhất có dữ liệu
        target_date = df_valid['date'].max()
        day_shifts = df_shifts[df_shifts['date'].dt.date == target_date.date()]

    # Lấy dữ liệu ngày trước đó để tính delta
    prev_date = target_date - timedelta(days=1)
    prev_shifts = df_shifts[df_shifts['date'].dt.date == prev_date.date()]

    # Tổng hợp số liệu trong ngày
    total_output = float(day_shifts['san_luong_tan'].sum())
    total_pellet_hours = float(day_shifts['tong_gio_ep'].sum())
    avg_productivity = total_output / total_pellet_hours if total_pellet_hours > 0 else 0.0

    total_electricity_kwh = float(day_shifts['dien_kwh'].sum())
    total_electricity_vnd = float(day_shifts['tien_dien_vnd'].sum())
    avg_electricity_kwh_ton = total_electricity_kwh / total_output if total_output > 0 else 0.0

    # Nguyên liệu
    total_nl_tho = float(day_shifts['nghien_tho_tan'].sum())
    total_nl_dot = float(day_shifts['nl_dot_tan'].sum())
    processing_ratio = (total_nl_tho / total_output) if total_output > 0 and total_nl_tho > 0 else 0.0

    # Nếu có df_daily, đối soát lấy thêm tỷ lệ chế biến, độ ẩm và tỷ trọng viên
    daily_record = {}
    if df_daily is not None and not df_daily.empty:
        daily_match = df_daily[df_daily['date'].dt.date == target_date.date()]
        if not daily_match.empty:
            daily_record = daily_match.iloc[0].to_dict()
            if processing_ratio == 0 and daily_record.get('ty_le_che_bien', 0) > 0:
                processing_ratio = daily_record.get('ty_le_che_bien', 0)

    # Lấy độ ẩm trung bình và tỷ trọng viên từ df_daily
    do_am_tb = float(daily_record.get('do_am_tb_pct', 0.0))
    ty_trong = float(daily_record.get('ty_trong_vien', 0.0))

    # Nếu df_daily chưa có hoặc = 0, đối soát lấy từ df_kcs
    if (do_am_tb == 0 or ty_trong == 0) and df_kcs is not None and not df_kcs.empty:
        kcs_day = df_kcs[df_kcs['date'].dt.date == target_date.date()]
        if not kcs_day.empty:
            if do_am_tb == 0 and 'am_vien_pct' in kcs_day.columns:
                m_vals = kcs_day['am_vien_pct'][kcs_day['am_vien_pct'] > 0]
                if not m_vals.empty:
                    do_am_tb = float(m_vals.mean())
            if ty_trong == 0 and 'density_vien' in kcs_day.columns:
                d_vals = kcs_day['density_vien'][kcs_day['density_vien'] > 0]
                if not d_vals.empty:
                    ty_trong = float(d_vals.mean())

    # Tính delta so với ngày hôm trước
    prev_output = float(prev_shifts['san_luong_tan'].sum()) if not prev_shifts.empty else 0.0
    prev_pellet_hours = float(prev_shifts['tong_gio_ep'].sum()) if not prev_shifts.empty else 0.0
    prev_productivity = prev_output / prev_pellet_hours if prev_pellet_hours > 0 else 0.0
    prev_electricity_kwh = float(prev_shifts['dien_kwh'].sum()) if not prev_shifts.empty else 0.0
    prev_elec_kwh_ton = prev_electricity_kwh / prev_output if prev_output > 0 else 0.0

    delta_output = total_output - prev_output if prev_output > 0 else 0.0
    delta_productivity = avg_productivity - prev_productivity if prev_productivity > 0 else 0.0
    delta_elec_kwh_ton = avg_electricity_kwh_ton - prev_elec_kwh_ton if prev_elec_kwh_ton > 0 else 0.0

    # Thống kê giờ chạy từng thiết bị trong ngày
    equipment_hours = {}
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        h_val = float(day_shifts[col].sum()) if col in day_shifts.columns else 0.0
        equipment_hours[code] = {
            'code': code,
            'name': info['name'],
            'brand': info['brand'],
            'group': info['group'],
            'hours': round(h_val, 1)
        }

    # Tổng giờ theo cụm
    group_hours = {
        'Nghiền búa thô': sum(equipment_hours[c]['hours'] for c in ['HM118', 'HM218', 'HM318']),
        'Trống sấy': sum(equipment_hours[c]['hours'] for c in ['DR124', 'DR224']),
        'Nghiền búa tinh': sum(equipment_hours[c]['hours'] for c in ['HM147', 'HM247', 'HM347']),
        'Máy ép viên': sum(equipment_hours[f'PE{i}']['hours'] for i in range(1, 9)),
    }

    # Chi tiết từng ca
    shift_details = []
    for _, row in day_shifts.iterrows():
        shift_output = float(row['san_luong_tan'])
        shift_hours = float(row['tong_gio_ep'])
        shift_ns = float(row['nang_suat_tph']) if row['nang_suat_tph'] > 0 else (shift_output / shift_hours if shift_hours > 0 else 0)
        shift_elec = float(row['dien_tb_kwh_tan']) if row['dien_tb_kwh_tan'] > 0 else (float(row['dien_kwh']) / shift_output if shift_output > 0 else 0)
        
        shift_details.append({
            'ca_truong': row['shift_leader'],
            'san_luong_tan': round(shift_output, 2),
            'tong_gio_ep': round(shift_hours, 1),
            'nang_suat_tph': round(shift_ns, 2),
            'ns_eval': evaluate_productivity(shift_ns),
            'dien_kwh': round(float(row['dien_kwh']), 0),
            'dien_tb_kwh_tan': round(shift_elec, 1),
            'elec_eval': evaluate_electricity(shift_elec),
            'nl_dot_tan': round(float(row['nl_dot_tan']), 2),
            'nghien_tho_tan': round(float(row['nghien_tho_tan']), 2),
        })

    # Phân loại 3 loại ca trong ngày: Ca sản xuất, Ca bảo trì, Ca nghỉ
    prod_shifts, maint_shifts, off_shifts = classify_shift_counts(day_shifts, num_days=1)

    return {
        'date': target_date,
        'date_str': target_date.strftime('%d/%m/%Y'),
        'total_output': round(total_output, 2),
        'delta_output': round(delta_output, 2),
        'total_pellet_hours': round(total_pellet_hours, 1),
        'avg_productivity': round(avg_productivity, 2),
        'delta_productivity': round(delta_productivity, 2),
        'productivity_eval': evaluate_productivity(avg_productivity),
        'total_electricity_kwh': round(total_electricity_kwh, 0),
        'total_electricity_vnd': round(total_electricity_vnd, 0),
        'avg_electricity_kwh_ton': round(avg_electricity_kwh_ton, 1),
        'delta_elec_kwh_ton': round(delta_elec_kwh_ton, 1),
        'electricity_eval': evaluate_electricity(avg_electricity_kwh_ton),
        'total_nl_tho': round(total_nl_tho, 2),
        'total_nl_dot': round(total_nl_dot, 2),
        'processing_ratio': round(processing_ratio, 2),
        'do_am_tb_pct': round(do_am_tb, 2),
        'moisture_eval': evaluate_moisture(do_am_tb),
        'ty_trong_vien': round(ty_trong, 1),
        'density_eval': evaluate_density(ty_trong),
        'equipment_hours': equipment_hours,
        'group_hours': group_hours,
        'shift_details': shift_details,
        'num_shifts': len(day_shifts),
        'prod_shifts': prod_shifts,
        'maint_shifts': maint_shifts,
        'off_shifts': off_shifts,
    }


def get_equipment_statistics(df_shifts: pd.DataFrame, start_date: Any = None, end_date: Any = None) -> pd.DataFrame:
    """
    Tổng hợp thời gian máy chạy, số ca hoạt động và tỷ lệ sử dụng cho từng máy.
    """
    if df_shifts.empty:
        return pd.DataFrame()

    df = df_shifts.copy()
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]

    num_days = max(1, (df['date'].max() - df['date'].min()).days + 1)
    num_shifts = len(df)

    stats = []
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        if col not in df.columns:
            continue
        
        series = df[col]
        total_hours = float(series.sum())
        active_shifts = int((series > 0).sum())
        avg_hours_per_day = total_hours / num_days
        avg_hours_active_shift = total_hours / active_shifts if active_shifts > 0 else 0.0
        
        # Max lý thuyết mỗi ca là 8h, mỗi ngày 24h
        max_possible_hours = num_days * 24
        utilization_rate = (total_hours / max_possible_hours * 100) if max_possible_hours > 0 else 0.0

        stats.append({
            'Mã TB': code,
            'Tên thiết bị': info['name'],
            'Hãng / Chủng loại': info['brand'],
            'Cụm thiết bị': info['group'],
            'Tổng giờ chạy (h)': round(total_hours, 1),
            'Số ca chạy': active_shifts,
            'Giờ chạy TB/ngày (h/ngày)': round(avg_hours_per_day, 1),
            'Giờ TB/ca hoạt động (h)': round(avg_hours_active_shift, 1),
            'Tỷ lệ sử dụng (%)': round(min(100.0, utilization_rate), 1)
        })

    return pd.DataFrame(stats)


def get_shift_leader_kpis(df_shifts: pd.DataFrame) -> pd.DataFrame:
    """
    Thống kê và so sánh hiệu suất sản xuất theo từng Ca Trưởng.
    """
    if df_shifts.empty or 'shift_leader' not in df_shifts.columns or 'san_luong_tan' not in df_shifts.columns:
        return pd.DataFrame()

    valid = df_shifts[(df_shifts['san_luong_tan'] > 0) & (df_shifts['shift_leader'].astype(str).str.strip() != '')]
    if valid.empty:
        return pd.DataFrame()

    grouped = valid.groupby('shift_leader').agg(
        so_ca=('row_index', 'count'),
        tong_san_luong=('san_luong_tan', 'sum'),
        san_luong_tb=('san_luong_tan', 'mean'),
        tong_dien=('dien_kwh', 'sum'),
        tong_gio_ep=('tong_gio_ep', 'sum'),
    ).reset_index()

    grouped['suat_dien_tb'] = grouped['tong_dien'] / grouped['tong_san_luong']
    grouped['nang_suat_tb'] = grouped['tong_san_luong'] / grouped['tong_gio_ep']

    # Làm tròn
    grouped['tong_san_luong'] = grouped['tong_san_luong'].round(2)
    grouped['san_luong_tb'] = grouped['san_luong_tb'].round(2)
    grouped['suat_dien_tb'] = grouped['suat_dien_tb'].round(1)
    grouped['nang_suat_tb'] = grouped['nang_suat_tb'].round(2)

    grouped.rename(columns={
        'shift_leader': 'Ca Trưởng',
        'so_ca': 'Số ca phụ trách',
        'tong_san_luong': 'Tổng sản lượng (tấn)',
        'san_luong_tb': 'Sản lượng TB/ca (tấn)',
        'suat_dien_tb': 'Điện năng TB (kWh/tấn)',
        'nang_suat_tb': 'Năng suất ép TB (tấn/h)'
    }, inplace=True)

    return grouped.sort_values('Tổng sản lượng (tấn)', ascending=False).reset_index(drop=True)


def evaluate_kpi_score(score: float) -> Dict[str, Any]:
    """
    Đánh giá xếp loại tổng điểm KPI (thang điểm 100).
    """
    if score >= 90.0:
        return {'rank': 'Xuất Sắc (A+)', 'badge': 'badge-success', 'color': '#16a34a', 'icon': '🌟', 'medal': '🥇'}
    elif score >= 85.0:
        return {'rank': 'Tốt (A)', 'badge': 'badge-success', 'color': '#22c55e', 'icon': '🟢', 'medal': '🥈'}
    elif score >= 80.0:
        return {'rank': 'Khá (B+)', 'badge': 'badge-info', 'color': '#0284c7', 'icon': '🔵', 'medal': '🥉'}
    elif score >= 70.0:
        return {'rank': 'Đạt Yêu Cầu (B)', 'badge': 'badge-warning', 'color': '#eab308', 'icon': '🟡', 'medal': '🎗️'}
    else:
        return {'rank': 'Cần Cải Thiện (C)', 'badge': 'badge-danger', 'color': '#ef4444', 'icon': '🔴', 'medal': '⚠️'}


def get_kpi_leaderboard(
    df_wm_weekly: pd.DataFrame, 
    df_wm_monthly: pd.DataFrame,
    selected_week: Optional[str] = None,
    selected_month: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tổng hợp bảng xếp hạng KPI ca trưởng theo tuần và theo tháng được chọn (hoặc mới nhất).
    Hỗ trợ tính chênh lệch (delta) so với kỳ trước.
    """
    result = {'weekly': None, 'monthly': None}

    # 1. Tuần được chọn
    if selected_week:
        match_w = df_wm_weekly[df_wm_weekly['week_label'] == selected_week] if not df_wm_weekly.empty else pd.DataFrame()
        if not match_w.empty:
            week_idx = match_w.index[0]
            week_row = match_w.iloc[0]
            prev_week_row = df_wm_weekly.iloc[week_idx - 1] if week_idx > 0 else None
            w_label = week_row['week_label']
            leaders = ['Long', 'Sắc', 'Tài']
            scores = []
            for name in leaders:
                val = week_row.get(name)
                if pd.notna(val) and val > 0:
                    prev_val = prev_week_row.get(name) if prev_week_row is not None else None
                    delta_score = round(float(val) - float(prev_val), 2) if pd.notna(prev_val) and prev_val > 0 else 0.0
                    scores.append({
                        'ca_truong': name, 
                        'diem_kpi': float(val),
                        'delta': delta_score
                    })
            scores.sort(key=lambda x: x['diem_kpi'], reverse=True)
            medals = ['🥇', '🥈', '🥉']
            for idx, item in enumerate(scores):
                item['hang'] = idx + 1
                item['huy_chuong'] = medals[idx] if idx < len(medals) else f"#{idx+1}"
                item['eval'] = evaluate_kpi_score(item['diem_kpi'])

            result['weekly'] = {
                'label': w_label,
                'leaderboard': scores
            }
        else:
            result['weekly'] = {
                'label': selected_week,
                'leaderboard': []
            }
    elif not df_wm_weekly.empty:
        week_idx = len(df_wm_weekly) - 1
        week_row = df_wm_weekly.iloc[-1]
        prev_week_row = df_wm_weekly.iloc[week_idx - 1] if week_idx > 0 else None
        w_label = week_row['week_label']
        leaders = ['Long', 'Sắc', 'Tài']
        scores = []
        for name in leaders:
            val = week_row.get(name)
            if pd.notna(val) and val > 0:
                prev_val = prev_week_row.get(name) if prev_week_row is not None else None
                delta_score = round(float(val) - float(prev_val), 2) if pd.notna(prev_val) and prev_val > 0 else 0.0
                scores.append({
                    'ca_truong': name, 
                    'diem_kpi': float(val),
                    'delta': delta_score
                })
        scores.sort(key=lambda x: x['diem_kpi'], reverse=True)
        medals = ['🥇', '🥈', '🥉']
        for idx, item in enumerate(scores):
            item['hang'] = idx + 1
            item['huy_chuong'] = medals[idx] if idx < len(medals) else f"#{idx+1}"
            item['eval'] = evaluate_kpi_score(item['diem_kpi'])

        result['weekly'] = {
            'label': w_label,
            'leaderboard': scores
        }

    # 2. Tháng được chọn
    if selected_month:
        match_m = df_wm_monthly[df_wm_monthly['month_label'] == selected_month] if not df_wm_monthly.empty else pd.DataFrame()
        if not match_m.empty:
            month_idx = match_m.index[0]
            month_row = match_m.iloc[0]
            prev_month_row = df_wm_monthly.iloc[month_idx - 1] if month_idx > 0 else None
            m_label = month_row['month_label']
            leaders = ['Long', 'Sắc', 'Tài']
            scores = []
            for name in leaders:
                val = month_row.get(name)
                if pd.notna(val) and val > 0:
                    prev_val = prev_month_row.get(name) if prev_month_row is not None else None
                    delta_score = round(float(val) - float(prev_val), 2) if pd.notna(prev_val) and prev_val > 0 else 0.0
                    scores.append({
                        'ca_truong': name, 
                        'diem_kpi': float(val),
                        'delta': delta_score
                    })
            scores.sort(key=lambda x: x['diem_kpi'], reverse=True)
            medals = ['🥇', '🥈', '🥉']
            for idx, item in enumerate(scores):
                item['hang'] = idx + 1
                item['huy_chuong'] = medals[idx] if idx < len(medals) else f"#{idx+1}"
                item['eval'] = evaluate_kpi_score(item['diem_kpi'])

            result['monthly'] = {
                'label': m_label,
                'leaderboard': scores
            }
        else:
            result['monthly'] = {
                'label': selected_month,
                'leaderboard': []
            }
    elif not df_wm_monthly.empty:
        month_idx = len(df_wm_monthly) - 1
        month_row = df_wm_monthly.iloc[-1]
        prev_month_row = df_wm_monthly.iloc[month_idx - 1] if month_idx > 0 else None
        m_label = month_row['month_label']
        leaders = ['Long', 'Sắc', 'Tài']
        scores = []
        for name in leaders:
            val = month_row.get(name)
            if pd.notna(val) and val > 0:
                prev_val = prev_month_row.get(name) if prev_month_row is not None else None
                delta_score = round(float(val) - float(prev_val), 2) if pd.notna(prev_val) and prev_val > 0 else 0.0
                scores.append({
                    'ca_truong': name, 
                    'diem_kpi': float(val),
                    'delta': delta_score
                })
        scores.sort(key=lambda x: x['diem_kpi'], reverse=True)
        medals = ['🥇', '🥈', '🥉']
        for idx, item in enumerate(scores):
            item['hang'] = idx + 1
            item['huy_chuong'] = medals[idx] if idx < len(medals) else f"#{idx+1}"
            item['eval'] = evaluate_kpi_score(item['diem_kpi'])

        result['monthly'] = {
            'label': m_label,
            'leaderboard': scores
        }

    return result


def get_incident_statistics(
    df_incidents: pd.DataFrame, 
    target_date: Any = None, 
    target_week: Optional[str] = None, 
    target_month: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thống kê chi tiết sự cố theo ngày hoặc tuần hoặc tháng:
    - Tổng số vụ sự cố
    - Tổng thời gian dừng máy (giờ)
    - Số vụ bảo trì sự cố vs bảo trì chủ động
    - Tỷ lệ xử lý hoàn thành (%)
    - Top thiết bị gặp sự cố
    - Top nguyên nhân sự cố
    - Thống kê theo ca trưởng
    """
    if df_incidents.empty:
        return {
            'total_incidents': 0,
            'total_hours': 0.0,
            'breakdown_count': 0,
            'proactive_count': 0,
            'completed_count': 0,
            'pending_count': 0,
            'completion_rate': 0.0,
            'equipment_stats': pd.DataFrame(),
            'cause_stats': pd.DataFrame(),
            'leader_stats': pd.DataFrame(),
            'df_filtered': pd.DataFrame()
        }

    df_filt = df_incidents.copy()

    if target_date:
        if isinstance(target_date, datetime):
            target_d_str = target_date.strftime('%d/%m/%Y')
        else:
            target_d_str = str(target_date)
        df_filt = df_filt[df_filt['date_str'] == target_d_str]
    elif target_week:
        w_num = int(str(target_week).replace("Tuần ", "").strip()) if str(target_week).replace("Tuần ", "").strip().isdigit() else None
        if w_num:
            df_filt = df_filt[df_filt['week'] == w_num]
    elif target_month:
        clean_m = str(target_month).replace("Tháng ", "").strip()
        m_num = int(clean_m.split('/')[0]) if clean_m.split('/')[0].isdigit() else None
        if m_num:
            df_filt = df_filt[df_filt['month'] == m_num]

    total_incidents = len(df_filt)
    total_hours = round(float(df_filt['duration_hours'].sum()), 1)
    
    breakdown_count = int(df_filt['activity'].str.lower().str.contains('sự cố').sum())
    proactive_count = int(df_filt['activity'].str.lower().str.contains('chủ động').sum())
    completed_count = int(df_filt['status'].str.lower().str.contains('hoàn thành').sum())
    pending_count = total_incidents - completed_count
    completion_rate = round((completed_count / total_incidents * 100), 1) if total_incidents > 0 else 100.0

    # Bóc tách từng thiết bị từ equipment_list
    eq_rows = []
    for _, row in df_filt.iterrows():
        eqs = row.get('equipment_list', [])
        dur = row.get('duration_hours', 0.0)
        if eqs:
            for eq in eqs:
                eq_rows.append({'equipment': eq, 'duration_hours': dur / len(eqs)})
        elif row.get('equipment_raw'):
            eq_rows.append({'equipment': row['equipment_raw'], 'duration_hours': dur})

    if eq_rows:
        df_eq = pd.DataFrame(eq_rows)
        df_eq_summary = df_eq.groupby('equipment').agg(
            so_vu=('equipment', 'count'),
            tong_gio=('duration_hours', 'sum')
        ).reset_index().sort_values(['so_vu', 'tong_gio'], ascending=[False, False])
        df_eq_summary['tong_gio'] = df_eq_summary['tong_gio'].round(1)
        df_eq_summary.rename(columns={'equipment': 'Mã Thiết Bị', 'so_vu': 'Số Vụ Sự Cố', 'tong_gio': 'Tổng Giờ Dừng (h)'}, inplace=True)
    else:
        df_eq_summary = pd.DataFrame(columns=['Mã Thiết Bị', 'Số Vụ Sự Cố', 'Tổng Giờ Dừng (h)'])

    # Thống kê nguyên nhân
    if not df_filt.empty and 'description' in df_filt.columns:
        df_cause = df_filt[df_filt['description'] != '']['description'].value_counts().reset_index()
        df_cause.columns = ['Nguyên Nhân / Hiện Tượng', 'Số Lần']
    else:
        df_cause = pd.DataFrame(columns=['Nguyên Nhân / Hiện Tượng', 'Số Lần'])

    # Thống kê theo ca trưởng
    if not df_filt.empty and 'shift_leader' in df_filt.columns:
        df_ldr = df_filt[df_filt['shift_leader'] != ''].groupby('shift_leader').agg(
            so_vu=('id_su_co', 'count'),
            tong_gio=('duration_hours', 'sum')
        ).reset_index().sort_values('so_vu', ascending=False)
        df_ldr.columns = ['Ca Trưởng Trực', 'Số Vụ Sự Cố', 'Tổng Giờ Dừng (h)']
        df_ldr['Tổng Giờ Dừng (h)'] = df_ldr['Tổng Giờ Dừng (h)'].round(1)
    else:
        df_ldr = pd.DataFrame(columns=['Ca Trưởng Trực', 'Số Vụ Sự Cố', 'Tổng Giờ Dừng (h)'])

    return {
        'total_incidents': total_incidents,
        'total_hours': total_hours,
        'breakdown_count': breakdown_count,
        'proactive_count': proactive_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'completion_rate': completion_rate,
        'equipment_stats': df_eq_summary,
        'cause_stats': df_cause,
        'leader_stats': df_ldr,
        'df_filtered': df_filt
    }


def get_equipment_incident_alerts(
    df_incidents: pd.DataFrame, 
    target_week: Optional[str] = None, 
    target_date: Any = None
) -> List[Dict[str, Any]]:
    """
    Phân tích và kích hoạt hệ thống CẢNH BÁO THIẾT BỊ (Equipment Failure Alerts):
    - ĐỎ (RED): Thiết bị có >= 3 sự cố trong kỳ, hoặc thời gian dừng đơn lẻ >= 2 giờ, hoặc chưa giải quyết / chuyển ca tiếp.
    - VÀNG (YELLOW): Thiết bị có 1 - 2 sự cố lặp lại.
    """
    if df_incidents.empty:
        return []

    df_filt = df_incidents.copy()
    if target_week:
        w_num = int(str(target_week).replace("Tuần ", "").strip()) if str(target_week).replace("Tuần ", "").strip().isdigit() else None
        if w_num:
            df_filt = df_filt[df_filt['week'] == w_num]
    elif target_date:
        d_str = target_date.strftime('%d/%m/%Y') if isinstance(target_date, datetime) else str(target_date)
        df_filt = df_filt[df_filt['date_str'] == d_str]
    else:
        latest_w = df_filt['week'].max() if 'week' in df_filt.columns else 0
        if latest_w > 0:
            df_filt = df_filt[df_filt['week'] >= max(1, latest_w - 3)]

    if df_filt.empty:
        return []

    eq_dict: Dict[str, Dict[str, Any]] = {}
    for _, r in df_filt.iterrows():
        eqs = r.get('equipment_list', [])
        if not eqs and r.get('equipment_raw'):
            eqs = [r['equipment_raw']]
        dur = r.get('duration_hours', 0.0)
        desc = r.get('description', '')
        status = r.get('status', '')
        d_str = r.get('date_str', '')

        for eq in eqs:
            eq = eq.strip()
            if not eq:
                continue
            if eq not in eq_dict:
                eq_dict[eq] = {
                    'equipment': eq,
                    'count': 0,
                    'total_hours': 0.0,
                    'max_single_hour': 0.0,
                    'has_pending': False,
                    'descriptions': [],
                    'dates': []
                }
            eq_dict[eq]['count'] += 1
            eq_dict[eq]['total_hours'] += dur
            if dur > eq_dict[eq]['max_single_hour']:
                eq_dict[eq]['max_single_hour'] = dur
            if 'chưa' in status.lower() or 'tiếp' in status.lower():
                eq_dict[eq]['has_pending'] = True
            if desc and desc not in eq_dict[eq]['descriptions']:
                eq_dict[eq]['descriptions'].append(desc)
            if d_str and d_str not in eq_dict[eq]['dates']:
                eq_dict[eq]['dates'].append(d_str)

    alerts = []
    for eq, info in eq_dict.items():
        cnt = info['count']
        tot_h = round(info['total_hours'], 1)
        max_h = round(info['max_single_hour'], 1)
        is_pending = info['has_pending']
        
        if cnt >= 3 or max_h >= 2.0 or is_pending:
            severity = 'RED'
            badge_cls = 'badge-danger'
            icon = '🚨'
            level_label = 'BÁO ĐỘNG ĐỎ'
            reasons = []
            if cnt >= 3:
                reasons.append(f"Tần suất cao ({cnt} lần sự cố)")
            if max_h >= 2.0:
                reasons.append(f"Dừng máy kéo dài ({max_h}h)")
            if is_pending:
                reasons.append("Chưa hoàn thành / Chuyển ca")
            msg = " • ".join(reasons)
        else:
            severity = 'YELLOW'
            badge_cls = 'badge-warning'
            icon = '⚠️'
            level_label = 'CẢNH BÁO VÀNG'
            msg = f"Phát sinh {cnt} lần sự cố (tổng dừng {tot_h}h)"

        alerts.append({
            'equipment': eq,
            'severity': severity,
            'badge_cls': badge_cls,
            'icon': icon,
            'level_label': level_label,
            'message': msg,
            'count': cnt,
            'total_hours': tot_h,
            'descriptions': info['descriptions'][:3],
            'recent_dates': info['dates'][:2]
        })

    severity_order = {'RED': 0, 'YELLOW': 1}
    alerts.sort(key=lambda x: (severity_order.get(x['severity'], 2), -x['count'], -x['total_hours']))
    return alerts


def get_all_leaders_dashboard_summary(
    df_shifts: pd.DataFrame,
    kpis_tong: Optional[Dict[str, Any]] = None,
    df_daily: Optional[pd.DataFrame] = None,
    df_kcs: Optional[pd.DataFrame] = None,
    df_chart_dien: Optional[pd.DataFrame] = None,
    df_chart_cap: Optional[pd.DataFrame] = None,
    df_chart_moist: Optional[pd.DataFrame] = None,
    leaders_kpi: Optional[Dict[str, pd.DataFrame]] = None,
    df_wm_weekly: Optional[pd.DataFrame] = None,
    df_wm_monthly: Optional[pd.DataFrame] = None,
    df_incidents: Optional[pd.DataFrame] = None,
    target_date: Any = None,
    week_num: Optional[int] = None,
    month_num: Optional[int] = None,
    date_range: Optional[Tuple[datetime, datetime]] = None,
    year_num: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tính toán và chuẩn bị dữ liệu Dashboard hoàn chỉnh cho 3 Ca Trưởng (Long, Sắc, Tài)
    và lập bảng đối sánh toàn diện với Dashboard Tổng Thể của nhà máy.
    """
    leader_configs = {
        'Long': {
            'pattern': r'long',
            'display_name': 'Ca Trưởng Long',
            'color': '#2563eb',
            'bg_color': '#eff6ff',
            'border_color': '#3b82f6',
            'icon': '🔵',
            'badge_cls': 'leader-card-long'
        },
        'Sắc': {
            'pattern': r'sắc|sac',
            'display_name': 'Ca Trưởng Sắc',
            'color': '#16a34a',
            'bg_color': '#f0fdf4',
            'border_color': '#22c55e',
            'icon': '🟢',
            'badge_cls': 'leader-card-sac'
        },
        'Tài': {
            'pattern': r'tài|tai',
            'display_name': 'Ca Trưởng Tài',
            'color': '#ea580c',
            'bg_color': '#fff7ed',
            'border_color': '#f97316',
            'icon': '🟠',
            'badge_cls': 'leader-card-tai'
        }
    }

    tot_factory_output = float(kpis_tong.get('total_output', 0.0)) if kpis_tong else 0.0
    leaders_summary = {}

    if df_shifts.empty or 'shift_leader' not in df_shifts.columns:
        return {'leaders': {}, 'comparison_df': pd.DataFrame()}

    for name, cfg in leader_configs.items():
        mask_leader = df_shifts['shift_leader'].astype(str).str.contains(cfg['pattern'], case=False, na=False)
        df_ldr = df_shifts[mask_leader].copy()

        # 1. Lọc theo kỳ được chọn
        if year_num is not None:
            p_shifts = df_ldr[df_ldr['date'].dt.year == year_num]
            period_label = f"Năm {year_num}"
        elif month_num is not None:
            p_shifts = df_ldr[df_ldr['date'].dt.month == month_num]
            period_label = f"Tháng {month_num}/2026"
        elif week_num is not None:
            p_shifts = df_ldr[df_ldr['date'].dt.isocalendar().week == week_num]
            period_label = f"Tuần {week_num}"
        elif date_range is not None:
            p_shifts = df_ldr[(df_ldr['date'] >= date_range[0]) & (df_ldr['date'] <= date_range[1])]
            period_label = "Khoảng thời gian"
        elif target_date is not None:
            t_date = pd.to_datetime(target_date).date()
            p_shifts = df_ldr[df_ldr['date'].dt.date == t_date]
            period_label = t_date.strftime('%d/%m/%Y')
        else:
            p_shifts = df_ldr.tail(1)
            period_label = "Gần nhất"

        # Tính toán chỉ số trong kỳ
        active_shifts = p_shifts[p_shifts['san_luong_tan'] > 0]
        shift_count = len(p_shifts)
        
        # Phân loại ca của riêng ca trưởng: ca sản xuất và ca bảo trì
        shift_ldr_str = p_shifts['shift_leader'].astype(str).str.lower() if not p_shifts.empty else pd.Series([], dtype=str)
        maint_shifts_ldr = p_shifts[shift_ldr_str.str.contains('bảo trì|vệ sinh|bảo dưỡng|bảo trì-vs|bảo trì - vs', regex=True, na=False)]
        maint_count = len(maint_shifts_ldr)
        prod_count = len(active_shifts)

        if prod_count > 0:
            duty_type = 'PROD'
            has_active_shift = True
            status_text = f"Đang trực ca SX ({prod_count} ca)"
            status_cls = "badge-success"
            status_icon = "🟢"
        elif maint_count > 0:
            duty_type = 'MAINT'
            has_active_shift = True
            status_text = f"Trực Bảo Trì - VS ({maint_count} ca)"
            status_cls = "badge-warning"
            status_icon = "🔧"
        else:
            duty_type = 'OFF'
            has_active_shift = False
            status_text = f"Nghỉ ca ngày {period_label}"
            status_cls = "badge-secondary"
            status_icon = "⚪"
        
        output = float(p_shifts['san_luong_tan'].sum())
        pellet_hours = float(p_shifts['tong_gio_ep'].sum())
        elec_kwh = float(p_shifts['dien_kwh'].sum())
        elec_vnd = float(p_shifts['tien_dien_vnd'].sum()) if 'tien_dien_vnd' in p_shifts.columns else 0.0
        
        kwh_ton = (elec_kwh / output) if output > 0 else 0.0
        tph = (output / pellet_hours) if pellet_hours > 0 else 0.0
        output_pct = (output / tot_factory_output * 100.0) if tot_factory_output > 0 else 0.0
        
        nl_tho = float(p_shifts['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in p_shifts.columns else 0.0
        nl_dot = float(p_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in p_shifts.columns else 0.0
        ratio = (nl_tho / output) if output > 0 and nl_tho > 0 else 0.0

        # Nếu chưa có điện kwh trong p_shifts nhưng có ở chart_dien
        if kwh_ton == 0 and df_chart_dien is not None and not df_chart_dien.empty and target_date is not None:
            t_dt = pd.to_datetime(target_date).date()
            match_cd = df_chart_dien[df_chart_dien['date'].dt.date == t_dt]
            if not match_cd.empty and name in match_cd.columns:
                val_cd = match_cd.iloc[0][name]
                if pd.notna(val_cd) and float(val_cd) > 0:
                    kwh_ton = float(val_cd)

        # Nếu chưa có tph nhưng có ở chart_cap
        if tph == 0 and df_chart_cap is not None and not df_chart_cap.empty and target_date is not None:
            t_dt = pd.to_datetime(target_date).date()
            match_cc = df_chart_cap[df_chart_cap['date'].dt.date == t_dt]
            if not match_cc.empty and name in match_cc.columns:
                val_cc = match_cc.iloc[0][name]
                if pd.notna(val_cc) and float(val_cc) > 0:
                    tph = float(val_cc)

        # Độ ẩm của ca trưởng
        moist_val = 0.0
        if df_chart_moist is not None and not df_chart_moist.empty and target_date is not None:
            t_dt = pd.to_datetime(target_date).date()
            match_cm = df_chart_moist[df_chart_moist['date'].dt.date == t_dt]
            if not match_cm.empty and name in match_cm.columns:
                val_cm = match_cm.iloc[0][name]
                if pd.notna(val_cm) and float(val_cm) > 0:
                    moist_val = float(val_cm)
        
        if moist_val == 0 and df_kcs is not None and not df_kcs.empty:
            kcs_ldr = df_kcs[df_kcs['shift_leader'].astype(str).str.contains(cfg['pattern'], case=False, na=False)]
            if target_date is not None:
                t_dt = pd.to_datetime(target_date).date()
                kcs_match = kcs_ldr[kcs_ldr['date'].dt.date == t_dt]
                if not kcs_match.empty and (kcs_match['am_vien_pct'] > 0).any():
                    moist_val = float(kcs_match['am_vien_pct'][kcs_match['am_vien_pct'] > 0].mean())
            if moist_val == 0 and not kcs_ldr.empty and (kcs_ldr['am_vien_pct'] > 0).any():
                moist_val = float(kcs_ldr['am_vien_pct'][kcs_ldr['am_vien_pct'] > 0].tail(10).mean())
        
        if moist_val == 0 and kpis_tong:
            moist_val = float(kpis_tong.get('do_am_tb_pct', 8.5))
        if moist_val == 0:
            moist_val = 8.5

        # Tỷ trọng viên
        density_val = float(kpis_tong.get('ty_trong_vien', 640.0)) if kpis_tong else 640.0

        # 2. Ca trực gần nhất (nếu ngày này không trực)
        all_active_shifts = df_ldr[df_ldr['san_luong_tan'] > 0].sort_values('date')
        latest_shift = all_active_shifts.iloc[-1] if not all_active_shifts.empty else None
        latest_shift_date = latest_shift['date_str'] if latest_shift is not None else 'N/A'
        latest_shift_out = float(latest_shift['san_luong_tan']) if latest_shift is not None else 0.0
        latest_shift_tph = float(latest_shift['nang_suat_tph']) if latest_shift is not None else 0.0
        latest_shift_kwh = float(latest_shift['dien_tb_kwh_tan']) if latest_shift is not None else 0.0
        latest_shift_hours = float(latest_shift['tong_gio_ep']) if latest_shift is not None and 'tong_gio_ep' in latest_shift and pd.notna(latest_shift['tong_gio_ep']) else 0.0
        latest_shift_nl_tho = float(latest_shift['nghien_tho_tan']) if latest_shift is not None and 'nghien_tho_tan' in latest_shift and pd.notna(latest_shift['nghien_tho_tan']) else 0.0
        latest_shift_nl_dot = float(latest_shift['nl_dot_tan']) if latest_shift is not None and 'nl_dot_tan' in latest_shift and pd.notna(latest_shift['nl_dot_tan']) else 0.0
        latest_shift_ratio = (latest_shift_nl_tho / latest_shift_out) if latest_shift_out > 0 and latest_shift_nl_tho > 0 else 0.0

        # 3. Tính toán thống kê đa kỳ chuẩn xác: NGÀY / TUẦN / THÁNG của ca trưởng
        if target_date is not None:
            ref_d = pd.to_datetime(target_date).date()
        elif not p_shifts.empty and pd.notna(p_shifts['date'].max()):
            ref_d = pd.to_datetime(p_shifts['date'].max()).date()
        elif not df_ldr.empty and pd.notna(df_ldr['date'].max()):
            ref_d = pd.to_datetime(df_ldr['date'].max()).date()
        else:
            ref_d = datetime.now().date()

        ref_w = week_num if week_num is not None else ref_d.isocalendar().week
        ref_m = month_num if month_num is not None else ref_d.month
        ref_y = year_num if year_num is not None else ref_d.year

        # A. Kỳ NGÀY của ca trưởng
        d_shifts = df_ldr[df_ldr['date'].dt.date == ref_d]
        d_act = d_shifts[d_shifts['san_luong_tan'] > 0]
        d_out = float(d_shifts['san_luong_tan'].sum())
        d_hours = float(d_shifts['tong_gio_ep'].sum())
        d_kwh = float(d_shifts['dien_kwh'].sum())
        d_kwh_ton = (d_kwh / d_out) if d_out > 0 else 0.0
        d_tph = (d_out / d_hours) if d_hours > 0 else 0.0
        d_shifts_cnt = len(d_act) if len(d_act) > 0 else len(d_shifts)
        d_ratio = float(d_shifts['nghien_tho_tan'].sum() / d_out) if d_out > 0 and 'nghien_tho_tan' in d_shifts.columns else 0.0
        d_nl_dot = float(d_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in d_shifts.columns else 0.0
        d_label = ref_d.strftime('%d/%m')
        d_full_date = ref_d.strftime('%d/%m/%Y')

        # B. Kỳ TUẦN của ca trưởng
        w_shifts = df_ldr[(df_ldr['date'].dt.isocalendar().week == ref_w) & (df_ldr['date'].dt.year == ref_y)]
        w_act = w_shifts[w_shifts['san_luong_tan'] > 0]
        w_out = float(w_shifts['san_luong_tan'].sum())
        w_hours = float(w_shifts['tong_gio_ep'].sum())
        w_kwh = float(w_shifts['dien_kwh'].sum())
        w_kwh_ton = (w_kwh / w_out) if w_out > 0 else 0.0
        w_tph = (w_out / w_hours) if w_hours > 0 else 0.0
        w_shifts_cnt = len(w_act)
        w_ratio = float(w_shifts['nghien_tho_tan'].sum() / w_out) if w_out > 0 and 'nghien_tho_tan' in w_shifts.columns else 0.0
        w_nl_dot = float(w_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in w_shifts.columns else 0.0
        w_label = f"W{ref_w}"

        # C. Kỳ THÁNG của ca trưởng
        m_shifts = df_ldr[(df_ldr['date'].dt.month == ref_m) & (df_ldr['date'].dt.year == ref_y) & (df_ldr['san_luong_tan'] > 0)]
        m_out = float(m_shifts['san_luong_tan'].sum())
        m_hours = float(m_shifts['tong_gio_ep'].sum())
        m_kwh = float(m_shifts['dien_kwh'].sum())
        m_kwh_ton = (m_kwh / m_out) if m_out > 0 else 0.0
        m_tph = (m_out / m_hours) if m_hours > 0 else 0.0
        m_count = len(m_shifts)
        m_ratio = float(m_shifts['nghien_tho_tan'].sum() / m_out) if m_out > 0 and 'nghien_tho_tan' in m_shifts.columns else 0.0
        m_nl_dot = float(m_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in m_shifts.columns else 0.0
        m_label = f"T{ref_m}"

        # 4. Điểm thi đua KPI
        kpi_score = 0.0
        kpi_row = None
        if df_wm_weekly is not None and not df_wm_weekly.empty:
            if week_num is not None and 'week' in df_wm_weekly.columns:
                match_w = df_wm_weekly[df_wm_weekly['week'] == week_num]
                if not match_w.empty:
                    kpi_row = match_w.iloc[0]
            if kpi_row is None:
                kpi_row = df_wm_weekly.iloc[-1]
            if kpi_row is not None and name in kpi_row and pd.notna(kpi_row[name]):
                kpi_score = float(kpi_row[name])

        if kpi_score == 0 and df_wm_monthly is not None and not df_wm_monthly.empty:
            last_m_row = df_wm_monthly.iloc[-1]
            if name in last_m_row and pd.notna(last_m_row[name]):
                kpi_score = float(last_m_row[name])

        kpi_eval = evaluate_kpi_score(kpi_score) if kpi_score > 0 else {'rank': 'Chưa xếp hạng', 'badge': 'badge-info', 'color': '#64748b', 'icon': '⚪', 'medal': '🎗️'}

        # 5. Sự cố trong ca
        inc_count = 0
        if df_incidents is not None and not df_incidents.empty and 'shift_leader' in df_incidents.columns:
            inc_match = df_incidents[df_incidents['shift_leader'].astype(str).str.contains(cfg['pattern'], case=False, na=False)]
            inc_count = len(inc_match)

        leaders_summary[name] = {
            'name': name,
            'display_name': cfg['display_name'],
            'color': cfg['color'],
            'bg_color': cfg['bg_color'],
            'border_color': cfg['border_color'],
            'badge_cls': cfg['badge_cls'],
            'icon': cfg['icon'],
            'has_active_shift': has_active_shift,
            'duty_type': duty_type,
            'maint_count': maint_count,
            'prod_count': prod_count,
            'period_label': period_label,
            'shift_count': shift_count,
            'status_text': status_text,
            'status_cls': status_cls,
            'status_icon': status_icon,
            'output': round(output, 2),
            'output_pct': round(output_pct, 1),
            'pellet_hours': round(pellet_hours, 1),
            'elec_kwh': round(elec_kwh, 0),
            'elec_vnd': round(elec_vnd, 0),
            'kwh_per_ton': round(kwh_ton, 1),
            'elec_eval': evaluate_electricity(kwh_ton),
            'tph': round(tph, 2),
            'prod_eval': evaluate_productivity(tph),
            'processing_ratio': round(ratio, 2),
            'nl_tho': round(nl_tho, 1),
            'nl_dot': round(nl_dot, 1),
            'moisture': round(moist_val, 2),
            'moist_eval': evaluate_moisture(moist_val),
            'density': round(density_val, 1),
            'density_eval': evaluate_density(density_val),
            'latest_shift_date': latest_shift_date,
            'latest_shift_out': round(latest_shift_out, 1),
            'latest_shift_tph': round(latest_shift_tph, 2),
            'latest_shift_kwh': round(latest_shift_kwh, 1),
            'latest_shift_hours': round(latest_shift_hours, 1),
            'latest_shift_nl_dot': round(latest_shift_nl_dot, 1),
            'latest_shift_ratio': round(latest_shift_ratio, 2),
            
            # Thống kê chi tiết Ngày
            'day_out': round(d_out, 1),
            'day_hours': round(d_hours, 1),
            'day_kwh_ton': round(d_kwh_ton, 1),
            'day_tph': round(d_tph, 2),
            'day_shifts': d_shifts_cnt,
            'day_ratio': round(d_ratio, 2),
            'day_nl_dot': round(d_nl_dot, 1),
            'day_label': d_label,
            'day_full_date': d_full_date,

            # Thống kê chi tiết Tuần
            'week_out': round(w_out, 1),
            'week_hours': round(w_hours, 1),
            'week_kwh_ton': round(w_kwh_ton, 1),
            'week_tph': round(w_tph, 2),
            'week_shifts': w_shifts_cnt,
            'week_ratio': round(w_ratio, 2),
            'week_nl_dot': round(w_nl_dot, 1),
            'week_label': w_label,

            # Thống kê chi tiết Tháng
            'month_output': round(m_out, 1),
            'month_hours': round(m_hours, 1),
            'month_kwh_ton': round(m_kwh_ton, 1),
            'month_tph': round(m_tph, 2),
            'month_shifts': m_count,
            'month_ratio': round(m_ratio, 2),
            'month_nl_dot': round(m_nl_dot, 1),
            'month_label': m_label,

            'kpi_score': round(kpi_score, 2),
            'kpi_eval': kpi_eval,
            'inc_count': inc_count,
            'period_label': period_label,
            'shifts_df': p_shifts
        }

    # Bảng đối sánh DataFrame
    long_s = leaders_summary.get('Long', {})
    sac_s = leaders_summary.get('Sắc', {})
    tai_s = leaders_summary.get('Tài', {})

    comp_data = [
        {
            'Chỉ Số Đo Lường': 'Sản lượng thực tế (tấn)',
            '🏭 Toàn Nhà Máy': f"{tot_factory_output:,.1f}",
            '🔵 Ca Long': f"{long_s.get('output', 0):,.1f}" if long_s.get('has_active_shift') else f"0.0 (Lk: {long_s.get('month_output', 0):,.0f})",
            '🟢 Ca Sắc': f"{sac_s.get('output', 0):,.1f}" if sac_s.get('has_active_shift') else f"0.0 (Lk: {sac_s.get('month_output', 0):,.0f})",
            '🟠 Ca Tài': f"{tai_s.get('output', 0):,.1f}" if tai_s.get('has_active_shift') else f"0.0 (Lk: {tai_s.get('month_output', 0):,.0f})",
            'Định Mức Kỹ Thuật': 'Kế hoạch ngày'
        },
        {
            'Chỉ Số Đo Lường': 'Suất tiêu hao điện (kWh/tấn)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('avg_electricity_kwh_ton', 0):.1f}" if kpis_tong else "-",
            '🔵 Ca Long': f"{long_s.get('kwh_per_ton', 0):.1f}" if long_s.get('kwh_per_ton', 0) > 0 else f"{long_s.get('month_kwh_ton', 0):.1f} (tháng)",
            '🟢 Ca Sắc': f"{sac_s.get('kwh_per_ton', 0):.1f}" if sac_s.get('kwh_per_ton', 0) > 0 else f"{sac_s.get('month_kwh_ton', 0):.1f} (tháng)",
            '🟠 Ca Tài': f"{tai_s.get('kwh_per_ton', 0):.1f}" if tai_s.get('kwh_per_ton', 0) > 0 else f"{tai_s.get('month_kwh_ton', 0):.1f} (tháng)",
            'Định Mức Kỹ Thuật': '170 - 175 kWh/t'
        },
        {
            'Chỉ Số Đo Lường': 'Năng suất ép trung bình (tấn/h)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('avg_productivity', 0):.2f}" if kpis_tong else "-",
            '🔵 Ca Long': f"{long_s.get('tph', 0):.2f}" if long_s.get('tph', 0) > 0 else f"{long_s.get('month_tph', 0):.2f} (tháng)",
            '🟢 Ca Sắc': f"{sac_s.get('tph', 0):.2f}" if sac_s.get('tph', 0) > 0 else f"{sac_s.get('month_tph', 0):.2f} (tháng)",
            '🟠 Ca Tài': f"{tai_s.get('tph', 0):.2f}" if tai_s.get('tph', 0) > 0 else f"{tai_s.get('month_tph', 0):.2f} (tháng)",
            'Định Mức Kỹ Thuật': '≥ 4.0 tấn/h'
        },
        {
            'Chỉ Số Đo Lường': 'Tổng giờ máy ép (giờ)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('total_pellet_hours', 0):.1f}" if kpis_tong else "-",
            '🔵 Ca Long': f"{long_s.get('pellet_hours', 0):.1f}",
            '🟢 Ca Sắc': f"{sac_s.get('pellet_hours', 0):.1f}",
            '🟠 Ca Tài': f"{tai_s.get('pellet_hours', 0):.1f}",
            'Định Mức Kỹ Thuật': '8 Máy Ép'
        },
        {
            'Chỉ Số Đo Lường': 'Độ ẩm trung bình viên (%)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('do_am_tb_pct', 0):.2f}%" if kpis_tong else "-",
            '🔵 Ca Long': f"{long_s.get('moisture', 0):.2f}%",
            '🟢 Ca Sắc': f"{sac_s.get('moisture', 0):.2f}%",
            '🟠 Ca Tài': f"{tai_s.get('moisture', 0):.2f}%",
            'Định Mức Kỹ Thuật': '8.0 - 9.5%'
        },
        {
            'Chỉ Số Đo Lường': 'Tỷ lệ chế biến (lần)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('processing_ratio', 0):.2f}" if kpis_tong else "-",
            '🔵 Ca Long': f"{long_s.get('processing_ratio', 0):.2f}",
            '🟢 Ca Sắc': f"{sac_s.get('processing_ratio', 0):.2f}",
            '🟠 Ca Tài': f"{tai_s.get('processing_ratio', 0):.2f}",
            'Định Mức Kỹ Thuật': '1.8 - 2.1'
        },
        {
            'Chỉ Số Đo Lường': 'Điểm KPI thi đua (/100)',
            '🏭 Toàn Nhà Máy': '-',
            '🔵 Ca Long': f"{long_s.get('kpi_score', 0):.1f} ({long_s.get('kpi_eval', {}).get('medal', '')} {long_s.get('kpi_eval', {}).get('rank', '')})",
            '🟢 Ca Sắc': f"{sac_s.get('kpi_score', 0):.1f} ({sac_s.get('kpi_eval', {}).get('medal', '')} {sac_s.get('kpi_eval', {}).get('rank', '')})",
            '🟠 Ca Tài': f"{tai_s.get('kpi_score', 0):.1f} ({tai_s.get('kpi_eval', {}).get('medal', '')} {tai_s.get('kpi_eval', {}).get('rank', '')})",
            'Định Mức Kỹ Thuật': 'Thang 100 điểm'
        }
    ]

    return {
        'leaders': leaders_summary,
        'comparison_df': pd.DataFrame(comp_data)
    }




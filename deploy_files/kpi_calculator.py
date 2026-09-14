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


def get_latest_day_kpis(df_shifts: pd.DataFrame, df_daily: pd.DataFrame = None, target_date: Any = None) -> Dict[str, Any]:
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
        target_date = df_valid['date'].max()
    elif isinstance(target_date, str):
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

    # Nếu có df_daily, đối soát lấy thêm tỷ lệ chế biến và độ ẩm
    daily_record = {}
    if df_daily is not None and not df_daily.empty:
        daily_match = df_daily[df_daily['date'].dt.date == target_date.date()]
        if not daily_match.empty:
            daily_record = daily_match.iloc[0].to_dict()
            if processing_ratio == 0 and daily_record.get('ty_le_che_bien', 0) > 0:
                processing_ratio = daily_record.get('ty_le_che_bien', 0)

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
        'do_am_tb_pct': round(daily_record.get('do_am_tb_pct', 0.0), 2),
        'ty_trong_vien': round(daily_record.get('ty_trong_vien', 0.0), 1),
        'equipment_hours': equipment_hours,
        'group_hours': group_hours,
        'shift_details': shift_details,
        'num_shifts': len(day_shifts),
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
    if df_shifts.empty:
        return pd.DataFrame()

    valid = df_shifts[(df_shifts['san_luong_tan'] > 0) & (df_shifts['shift_leader'].str.strip() != '')]
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




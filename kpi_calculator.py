"""
Module tính toán các chỉ số sản xuất (KPI), suất tiêu hao và gắn cờ cảnh báo.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
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

# 3 Tiêu chí KPI đánh giá ca sản xuất theo file '2026 Nhat ky KPI' (sheet 'W-M KPI' - gid=1921415360):
# 1. Sản lượng (tấn): Trọng số 50 điểm (50%) = (SL Thực tế / Chỉ tiêu SL) * 50
# 2. Độ ẩm của viên nén (%): Trọng số 30 điểm (30%) = (Độ ẩm TB / 9.0) * 30 (Chỉ tiêu chuẩn: 9.0%)
# 3. Năng suất của máy ép (tấn/h): Trọng số 20 điểm (20%) = (Năng suất TB / 4.0) * 20 (Chỉ tiêu chuẩn: 4.0 tấn/h)
KPI_WEIGHT_OUTPUT = 50.0          # Trọng số sản lượng (50 điểm)
KPI_WEIGHT_MOISTURE = 30.0        # Trọng số độ ẩm viên nén (30 điểm)
KPI_WEIGHT_PRODUCTIVITY = 20.0    # Trọng số năng suất máy ép viên (20 điểm)

KPI_TARGET_MOISTURE = 9.0         # Chỉ tiêu độ ẩm chuẩn (%): 9.0%
KPI_TARGET_PRODUCTIVITY = 4.0     # Chỉ tiêu năng suất chuẩn (tấn/h): 4.0 tấn/h

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
    maint_mask = shift_str.str.contains(r'bảo trì|vệ sinh|bảo dưỡng|bt[-_]?vs|bao tri', regex=True, na=False)
    
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
    total_nl_all = total_nl_tho + total_nl_dot
    processing_ratio = (total_nl_all / total_output) if total_output > 0 and total_nl_all > 0 else 0.0

    # Nếu có df_daily, đối soát lấy thêm tỷ lệ chế biến, độ ẩm và tỷ trọng viên
    daily_record = {}
    if df_daily is not None and not df_daily.empty:
        daily_match = df_daily[df_daily['date'].dt.date == target_date.date()]
        if not daily_match.empty:
            daily_record = daily_match.iloc[0].to_dict()
            if daily_record.get('ty_le_che_bien', 0) > 0:
                processing_ratio = float(daily_record.get('ty_le_che_bien', 0))

    # Lấy độ ẩm trung bình và tỷ trọng viên từ df_daily
    do_am_tb = float(daily_record.get('do_am_tb_pct', 0.0))
    ty_trong = float(daily_record.get('ty_trong_vien', 0.0))

    # Nếu df_daily chưa có hoặc = 0, đối soát lấy từ df_kcs (sheet KCS của file Nhật kí sản xuất)
    if df_kcs is not None and not df_kcs.empty:
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

        # Nếu ngày đó chưa kịp đo tỷ trọng, lấy mẫu đo tỷ trọng gần nhất trước đó từ df_kcs
        if ty_trong == 0 and 'density_vien' in df_kcs.columns:
            past_density = df_kcs[(df_kcs['date'].dt.date <= target_date.date()) & (df_kcs['density_vien'] > 0)]
            if not past_density.empty:
                ty_trong = float(past_density.iloc[-1]['density_vien'])
            else:
                all_density = df_kcs[df_kcs['density_vien'] > 0]
                if not all_density.empty:
                    ty_trong = float(all_density.iloc[-1]['density_vien'])
                else:
                    ty_trong = 645.0

        if do_am_tb == 0 and 'am_vien_pct' in df_kcs.columns:
            past_am = df_kcs[(df_kcs['date'].dt.date <= target_date.date()) & (df_kcs['am_vien_pct'] > 0)]
            if not past_am.empty:
                do_am_tb = float(past_am.iloc[-1]['am_vien_pct'])
            else:
                do_am_tb = 8.5
    else:
        if ty_trong == 0: ty_trong = 645.0
        if do_am_tb == 0: do_am_tb = 8.5

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

    # Tồn kho viên nén tại thời điểm ngày này (lấy ca cuối cùng trong ngày có tồn kho > 0 hoặc tìm ngày gần nhất)
    ton_kho_day = 0.0
    if not day_shifts.empty and 'ton_kho_tan' in day_shifts.columns:
        valid_tk = day_shifts[day_shifts['ton_kho_tan'] > 0]
        if not valid_tk.empty:
            ton_kho_day = float(valid_tk.iloc[-1]['ton_kho_tan'])
    if ton_kho_day == 0 and not df_shifts.empty and 'ton_kho_tan' in df_shifts.columns:
        sub_tk = df_shifts[(df_shifts['date'].dt.date <= target_date.date()) & (df_shifts['ton_kho_tan'] > 0)]
        if not sub_tk.empty:
            ton_kho_day = float(sub_tk.iloc[-1]['ton_kho_tan'])
        elif (df_shifts['ton_kho_tan'] > 0).any():
            ton_kho_day = float(df_shifts[df_shifts['ton_kho_tan'] > 0].iloc[-1]['ton_kho_tan'])

    tot_xuat_day = float(day_shifts['xuat_hang_tan'].sum()) if (not day_shifts.empty and 'xuat_hang_tan' in day_shifts.columns) else 0.0

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
        'ton_kho_tan': round(ton_kho_day, 2),
        'xuat_hang_tan': round(tot_xuat_day, 2),
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

    if df.empty or 'date' not in df.columns or df['date'].dropna().empty:
        num_days = 1
    else:
        try:
            delta = (df['date'].max() - df['date'].min()).days
            num_days = max(1, delta + 1) if pd.notna(delta) else 1
        except Exception:
            num_days = 1
    num_shifts = len(df)

    stats = []
    for code, info in EQUIPMENT_INFO.items():
        col = info['col']
        if col not in df.columns:
            continue
        
        series = df[col]
        total_hours = float(series.sum())
        active_shifts = int((series > 0).sum())
        avg_hours_per_day = total_hours / num_days if num_days > 0 else 0.0
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

    grouped['suat_dien_tb'] = np.where(grouped['tong_san_luong'] > 0, grouped['tong_dien'] / grouped['tong_san_luong'], 0.0)
    grouped['nang_suat_tb'] = np.where(grouped['tong_gio_ep'] > 0, grouped['tong_san_luong'] / grouped['tong_gio_ep'], 0.0)

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


def calculate_kpi_components(
    sl_thuc_te: float,
    chi_tieu_sl: float,
    do_am_tb: float,
    nang_suat_tb: float,
    target_moisture: float = KPI_TARGET_MOISTURE,
    target_productivity: float = KPI_TARGET_PRODUCTIVITY
) -> Dict[str, float]:
    """
    Tính điểm 3 chỉ tiêu KPI chuẩn hóa theo Google Sheet 'W-M KPI' (gid=1921415360):
    1. Sản lượng (tấn): Điểm SL = (SL Thực tế / Chỉ tiêu SL) * 50
    2. Độ ẩm của viên nén (%): Điểm Ẩm = (Độ ẩm TB / 9.0) * 30 (Chỉ tiêu: 9.0%)
    3. Năng suất của máy ép (tấn/h): Điểm Năng Suất = (Năng suất TB / 4.0) * 20 (Chỉ tiêu: 4.0 t/h)
    Tổng điểm KPI = Điểm SL + Điểm Ẩm + Điểm Năng Suất (Thang điểm 100).
    Lưu ý: Điện năng tiêu thụ (kWh/tấn) là chỉ số tham khảo kỹ thuật, không cộng điểm vào KPI.
    """
    diem_sl = (sl_thuc_te / chi_tieu_sl * KPI_WEIGHT_OUTPUT) if chi_tieu_sl > 0 else 0.0
    diem_am = (do_am_tb / target_moisture * KPI_WEIGHT_MOISTURE) if (target_moisture > 0 and do_am_tb > 0) else 0.0
    diem_ns = (nang_suat_tb / target_productivity * KPI_WEIGHT_PRODUCTIVITY) if (target_productivity > 0 and nang_suat_tb > 0) else 0.0
    diem_kpi = round(diem_sl + diem_am + diem_ns, 2)
    return {
        'diem_sl': round(diem_sl, 2),
        'diem_am': round(diem_am, 2),
        'diem_nang_suat': round(diem_ns, 2),
        'diem_kpi': diem_kpi
    }


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
            if any(c in week_row.index for c in ['Ca A', 'Ca B', 'Ca C']):
                leaders = [c for c in ['Ca A', 'Ca B', 'Ca C'] if c in week_row.index]
            else:
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
        if any(c in week_row.index for c in ['Ca A', 'Ca B', 'Ca C']):
            leaders = [c for c in ['Ca A', 'Ca B', 'Ca C'] if c in week_row.index]
        else:
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
            if any(c in month_row.index for c in ['Ca A', 'Ca B', 'Ca C']):
                leaders = [c for c in ['Ca A', 'Ca B', 'Ca C'] if c in month_row.index]
            else:
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
        if any(c in month_row.index for c in ['Ca A', 'Ca B', 'Ca C']):
            leaders = [c for c in ['Ca A', 'Ca B', 'Ca C'] if c in month_row.index]
        else:
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
            target_d_str = str(target_date).strip()
        m_d = pd.Series(False, index=df_filt.index)
        if 'date_str' in df_filt.columns:
            m_d = m_d | (df_filt['date_str'].astype(str).str.strip() == target_d_str)
        if 'date' in df_filt.columns:
            m_d = m_d | (pd.to_datetime(df_filt['date'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y') == target_d_str)
        df_filt = df_filt[m_d]
    elif target_week:
        w_match = re.search(r'\d+', str(target_week))
        if w_match:
            df_filt = df_filt[pd.to_numeric(df_filt['week'], errors='coerce') == int(w_match.group())]
    elif target_month:
        m_match = re.search(r'\d+', str(target_month))
        if m_match:
            df_filt = df_filt[pd.to_numeric(df_filt['month'], errors='coerce') == int(m_match.group())]

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
        w_match = re.search(r'\d+', str(target_week))
        if w_match:
            df_filt = df_filt[pd.to_numeric(df_filt['week'], errors='coerce') == int(w_match.group())]
    elif target_date:
        d_str = target_date.strftime('%d/%m/%Y') if isinstance(target_date, datetime) else str(target_date).strip()
        m_d = pd.Series(False, index=df_filt.index)
        if 'date_str' in df_filt.columns:
            m_d = m_d | (df_filt['date_str'].astype(str).str.strip() == d_str)
        if 'date' in df_filt.columns:
            m_d = m_d | (pd.to_datetime(df_filt['date'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y') == d_str)
        df_filt = df_filt[m_d]
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
    year_num: Optional[int] = None,
    df_kpi_daily: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Tính toán và chuẩn bị dữ liệu Dashboard hoàn chỉnh cho 3 Ca Trưởng (Long, Sắc, Tài)
    và lập bảng đối sánh toàn diện với Dashboard Tổng Thể của nhà máy.
    Truy vết dữ liệu gốc từ sheet 'Data KPI' cho sản lượng, độ ẩm, năng suất và suất điện.
    """
    leader_configs = {
        'Sắc': {
            'code': 'Ca A',
            'pattern': r'\bca a\b|sắc|sac|\bhải\b|\bhai\b',
            'display_name': 'Ca Trưởng Sắc (Ca A)',
            'color': '#16a34a',
            'bg_color': '#f0fdf4',
            'border_color': '#22c55e',
            'icon': '🟢',
            'badge_cls': 'leader-card-sac'
        },
        'Tài': {
            'code': 'Ca B',
            'pattern': r'\bca b\b|tài|tai|\blâm\b|\blam\b',
            'display_name': 'Ca Trưởng Tài (Ca B)',
            'color': '#ea580c',
            'bg_color': '#fff7ed',
            'border_color': '#f97316',
            'icon': '🟠',
            'badge_cls': 'leader-card-tai'
        },
        'Long': {
            'code': 'Ca C',
            'pattern': r'\bca c\b|long',
            'display_name': 'Ca Trưởng Long (Ca C)',
            'color': '#2563eb',
            'bg_color': '#eff6ff',
            'border_color': '#3b82f6',
            'icon': '🔵',
            'badge_cls': 'leader-card-long'
        }
    }

    # Tự động nạp bộ đệm sheet 'Data KPI' nếu chưa được truyền vào
    if df_kpi_daily is None or df_kpi_daily.empty:
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kpi_daily_shifts.parquet"),
            os.path.join("assets", "cache_kpi_daily_shifts.parquet"),
            os.path.join("deploy_files", "assets", "cache_kpi_daily_shifts.parquet"),
        ]
        for cp in cache_paths:
            if os.path.exists(cp):
                try:
                    df_kpi_daily = pd.read_parquet(cp)
                    if not df_kpi_daily.empty:
                        break
                except Exception:
                    pass

    tot_factory_output = float(kpis_tong.get('total_output', 0.0)) if kpis_tong else 0.0
    leaders_summary = {}

    if df_shifts.empty or 'shift_leader' not in df_shifts.columns:
        return {'leaders': {}, 'comparison_df': pd.DataFrame()}

    for name, cfg in leader_configs.items():
        ca_code = cfg['code']
        mask_leader = df_shifts['shift_leader'].astype(str).str.contains(cfg['pattern'], case=False, na=False)
        df_ldr = df_shifts[mask_leader].copy()

        # Dữ liệu từ sheet 'Data KPI' của ca trưởng này
        kpi_ldr = pd.DataFrame()
        if df_kpi_daily is not None and not df_kpi_daily.empty and 'ca_truong' in df_kpi_daily.columns:
            kpi_ldr = df_kpi_daily[df_kpi_daily['ca_truong'].astype(str).str.contains(ca_code, case=False, na=False)].copy()

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
        maint_shifts_ldr = p_shifts[shift_ldr_str.str.contains(r'bảo trì|vệ sinh|bảo dưỡng|bt[-_]?vs|bao tri', regex=True, na=False)]
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
        ratio = ((nl_tho + nl_dot) / output) if output > 0 and (nl_tho + nl_dot) > 0 else 0.0

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
        latest_shift_ratio = ((latest_shift_nl_tho + latest_shift_nl_dot) / latest_shift_out) if latest_shift_out > 0 and (latest_shift_nl_tho + latest_shift_nl_dot) > 0 else 0.0

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
        d_nl_tho = float(d_shifts['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in d_shifts.columns else 0.0
        d_nl_dot = float(d_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in d_shifts.columns else 0.0
        d_ratio = float((d_nl_tho + d_nl_dot) / d_out) if d_out > 0 else 0.0
        d_label = ref_d.strftime('%d/%m')
        d_full_date = ref_d.strftime('%d/%m/%Y')
        d_tgt = 0.0
        d_moist = moist_val

        # Truy vết chính xác từ sheet 'Data KPI' cho ngày ref_d
        if not kpi_ldr.empty:
            kpi_day = kpi_ldr[kpi_ldr['date'].dt.date == ref_d]
            if not kpi_day.empty:
                k_row = kpi_day.iloc[0]
                k_out = float(k_row.get('sl_thuc_te', 0.0))
                k_tgt = float(k_row.get('chi_tieu_sl', 0.0))
                k_ns = float(k_row.get('nang_suat_tb', 0.0))
                k_am = float(k_row.get('do_am_tb', 0.0))
                k_dien = float(k_row.get('dien_tb', 0.0))
                if k_out > 0:
                    d_out = k_out
                    d_tgt = k_tgt
                    if k_ns > 0:
                        d_tph = k_ns
                    if k_am > 0:
                        d_moist = k_am
                    if k_dien > 0:
                        d_kwh_ton = k_dien
                    d_shifts_cnt = 1
                    if d_hours == 0.0 and d_tph > 0:
                        d_hours = round(d_out / d_tph, 1)

        # Tính điểm KPI Ngày: Sản lượng 50đ, Độ ẩm 30đ, Năng suất 20đ
        sc_sl = (d_out / d_tgt) * 50.0 if d_tgt > 0 else (50.0 if d_out > 0 else 0.0)
        sc_moist = (d_moist / 9.0) * 30.0 if d_moist > 0 else 0.0
        sc_tph = (d_tph / 4.0) * 20.0 if d_tph > 0 else 0.0
        day_kpi_score = round(sc_sl + sc_moist + sc_tph, 2)
        day_kpi_eval = evaluate_kpi_score(day_kpi_score)

        # B. Kỳ TUẦN của ca trưởng
        w_shifts = df_ldr[(df_ldr['date'].dt.isocalendar().week == ref_w) & (df_ldr['date'].dt.year == ref_y)]
        w_act = w_shifts[w_shifts['san_luong_tan'] > 0]
        w_out = float(w_shifts['san_luong_tan'].sum())
        w_hours = float(w_shifts['tong_gio_ep'].sum())
        w_kwh = float(w_shifts['dien_kwh'].sum())
        w_kwh_ton = (w_kwh / w_out) if w_out > 0 else 0.0
        w_tph = (w_out / w_hours) if w_hours > 0 else 0.0
        w_shifts_cnt = len(w_act)
        w_nl_tho = float(w_shifts['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in w_shifts.columns else 0.0
        w_nl_dot = float(w_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in w_shifts.columns else 0.0
        w_ratio = float((w_nl_tho + w_nl_dot) / w_out) if w_out > 0 else 0.0
        w_label = f"W{ref_w}"
        w_tgt = 0.0
        w_moist = d_moist

        # Truy vết Tuần từ 'Data KPI'
        if not kpi_ldr.empty:
            kpi_week = kpi_ldr[(kpi_ldr['week'] == ref_w) & (kpi_ldr['date'].dt.year == ref_y) & (kpi_ldr['sl_thuc_te'] > 0)]
            if not kpi_week.empty:
                w_out = float(kpi_week['sl_thuc_te'].sum())
                w_tgt = float(kpi_week['chi_tieu_sl'].sum())
                if (kpi_week['nang_suat_tb'] > 0).any():
                    w_tph = float(kpi_week[kpi_week['nang_suat_tb'] > 0]['nang_suat_tb'].mean())
                if (kpi_week['do_am_tb'] > 0).any():
                    w_moist = float(kpi_week[kpi_week['do_am_tb'] > 0]['do_am_tb'].mean())
                if (kpi_week['dien_tb'] > 0).any():
                    w_kwh_ton = float(kpi_week[kpi_week['dien_tb'] > 0]['dien_tb'].mean())
                w_shifts_cnt = len(kpi_week)

        # Điểm thi đua KPI Tuần
        week_kpi_score = 0.0
        if df_wm_weekly is not None and not df_wm_weekly.empty:
            m_w = df_wm_weekly[df_wm_weekly['week'] == ref_w]
            if not m_w.empty:
                k_r = m_w.iloc[0]
                if name in k_r and pd.notna(k_r[name]):
                    week_kpi_score = float(k_r[name])
                elif ca_code in k_r and pd.notna(k_r[ca_code]):
                    week_kpi_score = float(k_r[ca_code])
        if week_kpi_score == 0.0:
            w_sc_sl = (w_out / w_tgt) * 50.0 if w_tgt > 0 else (50.0 if w_out > 0 else 0.0)
            w_sc_moist = (w_moist / 9.0) * 30.0 if w_moist > 0 else 0.0
            w_sc_tph = (w_tph / 4.0) * 20.0 if w_tph > 0 else 0.0
            week_kpi_score = round(w_sc_sl + w_sc_moist + w_sc_tph, 2)
        week_kpi_eval = evaluate_kpi_score(week_kpi_score)

        # C. Kỳ THÁNG của ca trưởng
        m_shifts = df_ldr[(df_ldr['date'].dt.month == ref_m) & (df_ldr['date'].dt.year == ref_y) & (df_ldr['san_luong_tan'] > 0)]
        m_out = float(m_shifts['san_luong_tan'].sum())
        m_hours = float(m_shifts['tong_gio_ep'].sum())
        m_kwh = float(m_shifts['dien_kwh'].sum())
        m_kwh_ton = (m_kwh / m_out) if m_out > 0 else 0.0
        m_tph = (m_out / m_hours) if m_hours > 0 else 0.0
        m_count = len(m_shifts)
        m_nl_tho = float(m_shifts['nghien_tho_tan'].sum()) if 'nghien_tho_tan' in m_shifts.columns else 0.0
        m_nl_dot = float(m_shifts['nl_dot_tan'].sum()) if 'nl_dot_tan' in m_shifts.columns else 0.0
        m_ratio = float((m_nl_tho + m_nl_dot) / m_out) if m_out > 0 else 0.0
        m_label = f"T{ref_m}"
        m_tgt = 0.0
        m_moist = d_moist

        # Truy vết Tháng từ 'Data KPI'
        if not kpi_ldr.empty:
            kpi_month = kpi_ldr[(kpi_ldr['month'] == ref_m) & (kpi_ldr['date'].dt.year == ref_y) & (kpi_ldr['sl_thuc_te'] > 0)]
            if not kpi_month.empty:
                m_out = float(kpi_month['sl_thuc_te'].sum())
                m_tgt = float(kpi_month['chi_tieu_sl'].sum())
                if (kpi_month['nang_suat_tb'] > 0).any():
                    m_tph = float(kpi_month[kpi_month['nang_suat_tb'] > 0]['nang_suat_tb'].mean())
                if (kpi_month['do_am_tb'] > 0).any():
                    m_moist = float(kpi_month[kpi_month['do_am_tb'] > 0]['do_am_tb'].mean())
                if (kpi_month['dien_tb'] > 0).any():
                    m_kwh_ton = float(kpi_month[kpi_month['dien_tb'] > 0]['dien_tb'].mean())
                m_count = len(kpi_month)

        # Điểm thi đua KPI Tháng
        month_kpi_score = 0.0
        if df_wm_monthly is not None and not df_wm_monthly.empty:
            m_m = df_wm_monthly[df_wm_monthly['month_label'].astype(str).str.contains(str(ref_m), na=False)]
            if not m_m.empty:
                k_rm = m_m.iloc[0]
                if name in k_rm and pd.notna(k_rm[name]):
                    month_kpi_score = float(k_rm[name])
                elif ca_code in k_rm and pd.notna(k_rm[ca_code]):
                    month_kpi_score = float(k_rm[ca_code])
        if month_kpi_score == 0.0:
            m_sc_sl = (m_out / m_tgt) * 50.0 if m_tgt > 0 else (50.0 if m_out > 0 else 0.0)
            m_sc_moist = (m_moist / 9.0) * 30.0 if m_moist > 0 else 0.0
            m_sc_tph = (m_tph / 4.0) * 20.0 if m_tph > 0 else 0.0
            month_kpi_score = round(m_sc_sl + m_sc_moist + m_sc_tph, 2)
        month_kpi_eval = evaluate_kpi_score(month_kpi_score)

        # 4. Xác định số liệu trọng tâm hiển thị trên thẻ theo bộ lọc sidebar
        if month_num is not None:
            output = m_out
            tph = m_tph
            moist_val = m_moist
            kwh_ton = m_kwh_ton
            kpi_score = month_kpi_score
            kpi_eval = month_kpi_eval
            if m_out > 0:
                duty_type = 'PROD'
                has_active_shift = True
        elif week_num is not None:
            output = w_out
            tph = w_tph
            moist_val = w_moist
            kwh_ton = w_kwh_ton
            kpi_score = week_kpi_score
            kpi_eval = week_kpi_eval
            if w_out > 0:
                duty_type = 'PROD'
                has_active_shift = True
        else:
            # Mặc định theo Ngày
            output = d_out
            tph = d_tph
            moist_val = d_moist
            kwh_ton = d_kwh_ton
            kpi_score = day_kpi_score
            kpi_eval = day_kpi_eval
            if d_out > 0:
                duty_type = 'PROD'
                has_active_shift = True
                status_text = f"Đang trực ca SX (1 ca)"
                status_cls = "badge-success"
                status_icon = "🟢"

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
            'day_moist': round(d_moist, 2),
            'day_shifts': d_shifts_cnt,
            'day_ratio': round(d_ratio, 2),
            'day_nl_dot': round(d_nl_dot, 1),
            'day_label': d_label,
            'day_full_date': d_full_date,
            'day_kpi_score': day_kpi_score,
            'day_kpi_eval': day_kpi_eval,

            # Thống kê chi tiết Tuần
            'week_out': round(w_out, 1),
            'week_hours': round(w_hours, 1),
            'week_kwh_ton': round(w_kwh_ton, 1),
            'week_tph': round(w_tph, 2),
            'week_moist': round(w_moist, 2),
            'week_shifts': w_shifts_cnt,
            'week_ratio': round(w_ratio, 2),
            'week_nl_dot': round(w_nl_dot, 1),
            'week_label': w_label,
            'week_kpi_score': week_kpi_score,
            'week_kpi_eval': week_kpi_eval,

            # Thống kê chi tiết Tháng
            'month_output': round(m_out, 1),
            'month_hours': round(m_hours, 1),
            'month_kwh_ton': round(m_kwh_ton, 1),
            'month_tph': round(m_tph, 2),
            'month_moist': round(m_moist, 2),
            'month_shifts': m_count,
            'month_ratio': round(m_ratio, 2),
            'month_nl_dot': round(m_nl_dot, 1),
            'month_label': m_label,
            'month_kpi_score': month_kpi_score,
            'month_kpi_eval': month_kpi_eval,

            'kpi_score': round(kpi_score, 2),
            'kpi_eval': kpi_eval,
            'inc_count': inc_count,
            'period_label': period_label,
            'shifts_df': p_shifts
        }

    # Bổ sung alias theo mã vị trí Ca A, Ca B, Ca C
    if 'Sắc' in leaders_summary:
        leaders_summary['Ca A'] = leaders_summary['Sắc']
    if 'Tài' in leaders_summary:
        leaders_summary['Ca B'] = leaders_summary['Tài']
    if 'Long' in leaders_summary:
        leaders_summary['Ca C'] = leaders_summary['Long']

    # Bảng đối sánh DataFrame theo chuẩn thứ tự Ca A (Sắc) - Ca B (Tài) - Ca C (Long)
    sac_s = leaders_summary.get('Sắc', {})
    tai_s = leaders_summary.get('Tài', {})
    long_s = leaders_summary.get('Long', {})

    comp_data = [
        {
            'Chỉ Số Đo Lường': 'Sản lượng thực tế (tấn)',
            '🏭 Toàn Nhà Máy': f"{tot_factory_output:,.1f}",
            '🟢 Ca A (Sắc)': f"{sac_s.get('output', 0):,.1f}" if sac_s.get('has_active_shift') else f"0.0 (Lk: {sac_s.get('month_output', 0):,.0f})",
            '🟠 Ca B (Tài)': f"{tai_s.get('output', 0):,.1f}" if tai_s.get('has_active_shift') else f"0.0 (Lk: {tai_s.get('month_output', 0):,.0f})",
            '🔵 Ca C (Long)': f"{long_s.get('output', 0):,.1f}" if long_s.get('has_active_shift') else f"0.0 (Lk: {long_s.get('month_output', 0):,.0f})",
            'Định Mức Kỹ Thuật': 'Kế hoạch ngày'
        },
        {
            'Chỉ Số Đo Lường': 'Suất tiêu hao điện (kWh/tấn)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('avg_electricity_kwh_ton', 0):.1f}" if kpis_tong else "-",
            '🟢 Ca A (Sắc)': f"{sac_s.get('kwh_per_ton', 0):.1f}" if sac_s.get('kwh_per_ton', 0) > 0 else f"{sac_s.get('month_kwh_ton', 0):.1f} (tháng)",
            '🟠 Ca B (Tài)': f"{tai_s.get('kwh_per_ton', 0):.1f}" if tai_s.get('kwh_per_ton', 0) > 0 else f"{tai_s.get('month_kwh_ton', 0):.1f} (tháng)",
            '🔵 Ca C (Long)': f"{long_s.get('kwh_per_ton', 0):.1f}" if long_s.get('kwh_per_ton', 0) > 0 else f"{long_s.get('month_kwh_ton', 0):.1f} (tháng)",
            'Định Mức Kỹ Thuật': '170 - 175 kWh/t'
        },
        {
            'Chỉ Số Đo Lường': 'Năng suất ép trung bình (tấn/h)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('avg_productivity', 0):.2f}" if kpis_tong else "-",
            '🟢 Ca A (Sắc)': f"{sac_s.get('tph', 0):.2f}" if sac_s.get('tph', 0) > 0 else f"{sac_s.get('month_tph', 0):.2f} (tháng)",
            '🟠 Ca B (Tài)': f"{tai_s.get('tph', 0):.2f}" if tai_s.get('tph', 0) > 0 else f"{tai_s.get('month_tph', 0):.2f} (tháng)",
            '🔵 Ca C (Long)': f"{long_s.get('tph', 0):.2f}" if long_s.get('tph', 0) > 0 else f"{long_s.get('month_tph', 0):.2f} (tháng)",
            'Định Mức Kỹ Thuật': '≥ 4.0 tấn/h'
        },
        {
            'Chỉ Số Đo Lường': 'Tổng giờ máy ép (giờ)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('total_pellet_hours', 0):.1f}" if kpis_tong else "-",
            '🟢 Ca A (Sắc)': f"{sac_s.get('pellet_hours', 0):.1f}",
            '🟠 Ca B (Tài)': f"{tai_s.get('pellet_hours', 0):.1f}",
            '🔵 Ca C (Long)': f"{long_s.get('pellet_hours', 0):.1f}",
            'Định Mức Kỹ Thuật': '8 Máy Ép'
        },
        {
            'Chỉ Số Đo Lường': 'Độ ẩm trung bình viên (%)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('do_am_tb_pct', 0):.2f}%" if kpis_tong else "-",
            '🟢 Ca A (Sắc)': f"{sac_s.get('moisture', 0):.2f}%",
            '🟠 Ca B (Tài)': f"{tai_s.get('moisture', 0):.2f}%",
            '🔵 Ca C (Long)': f"{long_s.get('moisture', 0):.2f}%",
            'Định Mức Kỹ Thuật': '8.0 - 9.5%'
        },
        {
            'Chỉ Số Đo Lường': 'Tỷ lệ chế biến (lần)',
            '🏭 Toàn Nhà Máy': f"{kpis_tong.get('processing_ratio', 0):.2f}" if kpis_tong else "-",
            '🟢 Ca A (Sắc)': f"{sac_s.get('processing_ratio', 0):.2f}",
            '🟠 Ca B (Tài)': f"{tai_s.get('processing_ratio', 0):.2f}",
            '🔵 Ca C (Long)': f"{long_s.get('processing_ratio', 0):.2f}",
            'Định Mức Kỹ Thuật': '1.8 - 2.1'
        },
        {
            'Chỉ Số Đo Lường': 'Điểm KPI thi đua (/100)',
            '🏭 Toàn Nhà Máy': '-',
            '🟢 Ca A (Sắc)': f"{sac_s.get('kpi_score', 0):.1f} ({sac_s.get('kpi_eval', {}).get('medal', '')} {sac_s.get('kpi_eval', {}).get('rank', '')})",
            '🟠 Ca B (Tài)': f"{tai_s.get('kpi_score', 0):.1f} ({tai_s.get('kpi_eval', {}).get('medal', '')} {tai_s.get('kpi_eval', {}).get('rank', '')})",
            '🔵 Ca C (Long)': f"{long_s.get('kpi_score', 0):.1f} ({long_s.get('kpi_eval', {}).get('medal', '')} {long_s.get('kpi_eval', {}).get('rank', '')})",
            'Định Mức Kỹ Thuật': 'Thang 100 điểm'
        }
    ]

    return {
        'leaders': leaders_summary,
        'comparison_df': pd.DataFrame(comp_data)
    }




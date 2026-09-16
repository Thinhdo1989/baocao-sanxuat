"""
Module kết nối và chuẩn hóa dữ liệu từ Google Sheets cho Nhà máy viên nén gỗ.
"""
import os
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

DEFAULT_SHIFT_COLUMNS = [
    'row_index', 'date', 'date_str', 'month', 'week', 'shift_leader',
    'nl_dot_spoon', 'nl_dot_tan', 'nghien_tho_spoon', 'nghien_tho_tan',
    'san_luong_tan', 'chi_tieu_tan', 'xuat_hang_tan', 'ton_kho_tan',
    'ti_le_nl_dot_pct', 'dien_kwh', 'tien_dien_vnd', 'dien_tb_kwh_tan',
    'h_HM118', 'h_HM218', 'h_HM318', 'h_DR124', 'h_DR224',
    'h_HM147', 'h_HM247', 'h_HM347',
    'h_PE1', 'h_PE2', 'h_PE3', 'h_PE4', 'h_PE5', 'h_PE6', 'h_PE7', 'h_PE8',
    'tong_gio_ep', 'nang_suat_tph'
]

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

DEFAULT_PRODUCTION_SPREADSHEET_ID = "1HH1r7O_eL_iW6spNruAKCM947G79rCyJRFHRVVb9apU"
DEFAULT_KPI_SPREADSHEET_ID = "1M75tg_kZNxItv3VOlAjNi-RF63S_2NtxBMXSAxCRe14"
DEFAULT_MAINT_LOG_SPREADSHEET_ID = "1hInwQQgN3zXWFEXC1qaFgaXeIiogXUJtm0cPgP3PlX8"
DEFAULT_MAINT_PLAN_SPREADSHEET_ID = "1d7cmTioaJyRSGxgC7ArPUnmBtTvToby-vNCsgXV1bOQ"
DEFAULT_PROCESS_SPREADSHEET_ID = "1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw"
DEFAULT_CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def clean_number(val: Any) -> float:
    """
    Chuyển đổi chuỗi số định dạng tiếng Việt / quốc tế sang float.
    Xử lý dấu phân cách hàng nghìn (.), dấu thập phân (,), các ký tự %, tấn, kWh, '-'...
    """
    if val is None:
        return 0.0
    val_str = str(val).strip()
    if not val_str or val_str in ['-', 'N/A', 'None', '', 'NaN']:
        return 0.0
    
    # Loại bỏ ký hiệu đơn vị, tiền tệ, phần trăm
    for unit in ['%', 'tấn', 'kWh', 'VND', 'kg/m3', 'h', 'lit', 'lít', ' ']:
        val_str = val_str.replace(unit, '')
    val_str = val_str.strip()
    
    # TH1: Cả dấu chấm và dấu phẩy: "2.029.280,00" hoặc "1.118,5"
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        # TH2: Chỉ có dấu phẩy: "186,961" hoặc "4,0" -> phẩy là thập phân
        val_str = val_str.replace(',', '.')
    elif '.' in val_str:
        # TH3: Chỉ có dấu chấm
        parts = val_str.split('.')
        if len(parts) > 2:
            # Nhiều dấu chấm -> phân cách hàng nghìn: 68.997.840 -> 68997840
            val_str = val_str.replace('.', '')
        elif len(parts) == 2:
            # 1 dấu chấm: nếu phần sau có đúng 3 chữ số và phần nguyên khác 0 -> phân cách hàng nghìn (vd: 30.880, 1.200)
            if len(parts[1]) == 3 and not (len(parts[0]) == 1 and parts[0] == '0'):
                val_str = val_str.replace('.', '')
            else:
                # Thập phân thông thường (vd: 4.0, 3.95)
                pass

    try:
        return float(val_str)
    except (ValueError, TypeError):
        return 0.0



def parse_vn_date(date_str: Any) -> Optional[datetime]:
    """
    Chuẩn hóa chuỗi ngày tháng sang datetime object.
    Hỗ trợ định dạng: d/m/yyyy, dd/mm/yyyy, yyyy-mm-dd
    """
    if not date_str:
        return None
    s = str(date_str).strip()
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


class DataLoader:
    """
    Lớp quản lý kết nối Google Sheets và chuẩn hóa các bảng dữ liệu sản xuất & KPI.
    """
    def __init__(
        self, 
        credentials_path: str = DEFAULT_CREDENTIALS_FILE, 
        spreadsheet_id: str = DEFAULT_PRODUCTION_SPREADSHEET_ID,
        kpi_spreadsheet_id: str = DEFAULT_KPI_SPREADSHEET_ID,
        maint_log_spreadsheet_id: str = DEFAULT_MAINT_LOG_SPREADSHEET_ID,
        maint_plan_spreadsheet_id: str = DEFAULT_MAINT_PLAN_SPREADSHEET_ID,
        process_spreadsheet_id: str = DEFAULT_PROCESS_SPREADSHEET_ID
    ):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.kpi_spreadsheet_id = kpi_spreadsheet_id
        self.maint_log_spreadsheet_id = maint_log_spreadsheet_id
        self.maint_plan_spreadsheet_id = maint_plan_spreadsheet_id
        self.process_spreadsheet_id = process_spreadsheet_id
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.kpi_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.maint_log_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.maint_plan_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.process_spreadsheet: Optional[gspread.Spreadsheet] = None
        self._ensure_credentials()

    def _ensure_credentials(self):
        """Tìm file credentials nếu đường dẫn mặc định không tồn tại"""
        if not os.path.exists(self.credentials_path):
            # Thử tìm trong thư mục cha hoặc các file .json có service_account
            candidates = [
                os.path.join(os.path.dirname(__file__), "credentials.json"),
                os.path.join("..", "credentials.json"),
            ]
            # Quét các file json có dạng service account
            parent_dir = os.path.dirname(os.path.abspath(self.credentials_path))
            for f in os.listdir(parent_dir):
                if f.endswith(".json") and "credentials" in f.lower():
                    candidates.append(os.path.join(parent_dir, f))
            
            for c in candidates:
                if os.path.exists(c):
                    self.credentials_path = c
                    break

    def connect(self) -> bool:
        """Xác thực và kết nối tới cả 4 Google Spreadsheets"""
        creds = None
        # 1. Kiểm tra Streamlit Secrets (khi deploy lên Streamlit Community Cloud)
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "gcp_service_account" in st.secrets:
                    service_account_info = dict(st.secrets["gcp_service_account"])
                    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
                elif "credentials" in st.secrets:
                    # Trường hợp dán trực tiếp chuỗi json vào secret credentials
                    raw_creds = st.secrets["credentials"]
                    if isinstance(raw_creds, str):
                        service_account_info = json.loads(raw_creds)
                    else:
                        service_account_info = dict(raw_creds)
                    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        except Exception:
            pass

        # 2. Nếu không có Streamlit Secrets, đọc từ file credentials.json cục bộ
        if creds is None:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Không tìm thấy file xác thực hoặc Streamlit Secret: {self.credentials_path}")
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=SCOPES)
        
        self.client = gspread.authorize(creds)
        
        # 1. Bảng tính nhật ký sản xuất
        try:
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            print(f"[-] Không thể mở bảng tính sản xuất: {e}")
            self.spreadsheet = None

        # 2. Bảng tính đánh giá KPI
        try:
            self.kpi_spreadsheet = self.client.open_by_key(self.kpi_spreadsheet_id)
        except Exception as e:
            print(f"[-] Không thể mở bảng tính KPI: {e}")
            self.kpi_spreadsheet = None

        # 3. Bảng tính nhật ký bảo trì
        try:
            self.maint_log_spreadsheet = self.client.open_by_key(self.maint_log_spreadsheet_id)
        except Exception as e:
            print(f"[-] Không thể mở bảng tính nhật ký bảo trì: {e}")
            self.maint_log_spreadsheet = None

        # 4. Bảng tính kế hoạch bảo trì & 4M
        try:
            self.maint_plan_spreadsheet = self.client.open_by_key(self.maint_plan_spreadsheet_id)
        except Exception as e:
            print(f"[-] Không thể mở bảng tính kế hoạch bảo trì & 4M: {e}")
            self.maint_plan_spreadsheet = None

        try:
            self.process_spreadsheet = self.client.open_by_key(self.process_spreadsheet_id)
        except Exception as e:
            try:
                print(f"[-] Không thể mở bảng tính quy trình chế biến: {e}")
            except Exception:
                print(f"[-] Cannot open process spreadsheet: {e}")
            self.process_spreadsheet = None

        return True

    def get_sheet_values(self, sheet_name: str) -> List[List[str]]:
        """Đọc toàn bộ dữ liệu của một sheet từ bảng tính sản xuất với retry 3 lần"""
        for attempt in range(3):
            try:
                if not self.spreadsheet:
                    self.connect()
                if not self.spreadsheet:
                    return []
                ws = self.spreadsheet.worksheet(sheet_name)
                return ws.get_all_values()
            except Exception as e:
                print(f"[-] Lỗi đọc sheet '{sheet_name}' (lần {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(0.8 * (attempt + 1))
        return []

    def get_kpi_sheet_values(self, sheet_name: str) -> List[List[str]]:
        """Đọc toàn bộ dữ liệu của một sheet từ bảng tính đánh giá KPI với retry 3 lần"""
        for attempt in range(3):
            try:
                if not self.kpi_spreadsheet:
                    self.connect()
                if not self.kpi_spreadsheet:
                    return []
                ws = self.kpi_spreadsheet.worksheet(sheet_name)
                return ws.get_all_values()
            except Exception as e:
                print(f"[-] Lỗi đọc KPI sheet '{sheet_name}' (lần {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(0.8 * (attempt + 1))
        return []


    def load_shift_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu ca/ngày từ sheet 'Product'.
        Bao gồm: sản lượng, chỉ tiêu, điện năng, giờ chạy các máy nghiền, sấy, ép viên.
        Tích hợp bộ đệm cục bộ (cache_shifts.parquet) dự phòng khi mất kết nối mạng.
        """
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_shifts.parquet"),
            os.path.join("assets", "cache_shifts.parquet"),
            os.path.join("deploy_files", "assets", "cache_shifts.parquet"),
        ]

        raw_rows = self.get_sheet_values('Product')
        if len(raw_rows) < 7:
            # Google Sheet tạm thời không tải được -> Đọc từ bộ đệm parquet
            for cp in cache_paths:
                if os.path.exists(cp):
                    try:
                        df_cached = pd.read_parquet(cp)
                        if not df_cached.empty and 'shift_leader' in df_cached.columns:
                            print(f"[i] Đã nạp {len(df_cached)} dòng dữ liệu ca từ bộ đệm cục bộ ({cp})")
                            return df_cached
                    except Exception as e:
                        print(f"[-] Lỗi đọc cache {cp}: {e}")
            return pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)

        # Dữ liệu bắt đầu từ dòng 7 (index 6)
        records = []
        for r_idx, r in enumerate(raw_rows[6:], start=7):
            if not r or not r[0].strip():
                continue
            
            date_raw = r[0].strip()
            date_dt = parse_vn_date(date_raw)
            if not date_dt:
                continue

            # Bỏ qua các dòng tương lai không có sản lượng hoặc giờ máy chạy
            san_luong = clean_number(r[10] if len(r) > 10 else 0)
            gio_ep_tong = clean_number(r[34] if len(r) > 34 else 0)
            ca_truong = r[3].strip() if len(r) > 3 else ''

            if san_luong == 0 and gio_ep_tong == 0 and ca_truong in ['Nghĩ', '']:
                # Dòng trống hoặc ca nghỉ không hoạt động
                continue

            record = {
                'row_index': r_idx,
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'month': int(clean_number(r[1])) if len(r) > 1 and r[1].strip().isdigit() else date_dt.month,
                'week': int(clean_number(r[2])) if len(r) > 2 and r[2].strip().isdigit() else date_dt.isocalendar()[1],
                'shift_leader': ca_truong,
                
                # Nguyên liệu
                'nl_dot_spoon': clean_number(r[4] if len(r) > 4 else 0),
                'nl_dot_tan': clean_number(r[6] if len(r) > 6 else 0),
                'nghien_tho_spoon': clean_number(r[7] if len(r) > 7 else 0),
                'nghien_tho_tan': clean_number(r[9] if len(r) > 9 else 0),
                
                # Sản lượng & Tiêu thụ
                'san_luong_tan': san_luong,
                'chi_tieu_tan': clean_number(r[11] if len(r) > 11 else 0),
                'xuat_hang_tan': clean_number(r[12] if len(r) > 12 else 0),
                'ton_kho_tan': clean_number(r[13] if len(r) > 13 else 0),
                'ti_le_nl_dot_pct': clean_number(r[14] if len(r) > 14 else 0),
                
                # Điện năng
                'dien_kwh': clean_number(r[15] if len(r) > 15 else 0),
                'tien_dien_vnd': clean_number(r[16] if len(r) > 16 else 0),
                'dien_tb_kwh_tan': clean_number(r[17] if len(r) > 17 else 0),

                # Giờ máy chạy - Máy nghiền búa thô
                'h_HM118': clean_number(r[18] if len(r) > 18 else 0),
                'h_HM218': clean_number(r[19] if len(r) > 19 else 0),
                'h_HM318': clean_number(r[20] if len(r) > 20 else 0),

                # Giờ máy chạy - Trống sấy
                'h_DR124': clean_number(r[21] if len(r) > 21 else 0),
                'h_DR224': clean_number(r[22] if len(r) > 22 else 0),

                # Giờ máy chạy - Máy nghiền búa tinh
                'h_HM147': clean_number(r[23] if len(r) > 23 else 0),
                'h_HM247': clean_number(r[24] if len(r) > 24 else 0),
                'h_HM347': clean_number(r[25] if len(r) > 25 else 0),

                # Giờ máy chạy - 8 Máy ép viên (PE1 -> PE8)
                'h_PE1': clean_number(r[26] if len(r) > 26 else 0),
                'h_PE2': clean_number(r[27] if len(r) > 27 else 0),
                'h_PE3': clean_number(r[28] if len(r) > 28 else 0),
                'h_PE4': clean_number(r[29] if len(r) > 29 else 0),
                'h_PE5': clean_number(r[30] if len(r) > 30 else 0),
                'h_PE6': clean_number(r[31] if len(r) > 31 else 0),
                'h_PE7': clean_number(r[32] if len(r) > 32 else 0),
                'h_PE8': clean_number(r[33] if len(r) > 33 else 0),

                # Tổng giờ & Năng suất ép
                'tong_gio_ep': gio_ep_tong,
                'nang_suat_tph': clean_number(r[35] if len(r) > 35 else 0),
            }
            records.append(record)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
            # Nếu điện năng tb = 0 nhưng có điện kwh và sản lượng > 0 -> tự tính lại
            mask_dien = (df['dien_tb_kwh_tan'] == 0) & (df['san_luong_tan'] > 0) & (df['dien_kwh'] > 0)
            df.loc[mask_dien, 'dien_tb_kwh_tan'] = df.loc[mask_dien, 'dien_kwh'] / df.loc[mask_dien, 'san_luong_tan']
            
            # Nếu năng suất = 0 nhưng có sản lượng và giờ ép > 0 -> tự tính lại
            mask_ns = (df['nang_suat_tph'] == 0) & (df['san_luong_tan'] > 0) & (df['tong_gio_ep'] > 0)
            df.loc[mask_ns, 'nang_suat_tph'] = df.loc[mask_ns, 'san_luong_tan'] / df.loc[mask_ns, 'tong_gio_ep']

            # Tự động cập nhật cache parquet dự phòng
            for cp in cache_paths:
                try:
                    os.makedirs(os.path.dirname(cp), exist_ok=True)
                    df.to_parquet(cp, index=False)
                except Exception:
                    pass
        else:
            # Nếu df rỗng, kiểm tra cache
            for cp in cache_paths:
                if os.path.exists(cp):
                    try:
                        df_cached = pd.read_parquet(cp)
                        if not df_cached.empty and 'shift_leader' in df_cached.columns:
                            return df_cached
                    except Exception:
                        pass
            df = pd.DataFrame(columns=DEFAULT_SHIFT_COLUMNS)

        return df

    def load_daily_summary(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu tổng hợp ngày từ sheet 'Daily report'.
        Sheet này ở dạng xoay ngang: Cột là từng ngày, Hàng là các chỉ tiêu.
        """
        rows = self.get_sheet_values('Daily report')
        if len(rows) < 11:
            return pd.DataFrame()

        # Dòng 3 (index 2): Danh sách Ngày (bắt đầu từ cột 2)
        # Dòng 4: Khối lượng sản xuất (tấn)
        # Dòng 5: Tổng nguyên liệu (tấn)
        # Dòng 6: Tổng nguyên liệu đốt (tấn)
        # Dòng 7: Tỷ lệ chế biến (n)
        # Dòng 8: Độ ẩm trung bình (%)
        # Dòng 9: Tỷ trọng viên (kg/m3)
        # Dòng 10: Năng suất trung bình (tấn/h)
        # Dòng 11: Tổng nguyên liệu nhập (tấn)
        # Dòng 12: Chỉ tiêu sản lượng (tấn)
        dates_row = rows[2]
        records = []

        for col_idx in range(2, len(dates_row)):
            date_raw = dates_row[col_idx].strip()
            if not date_raw or date_raw == '-':
                continue
            date_dt = parse_vn_date(date_raw)
            if not date_dt:
                continue

            san_luong = clean_number(rows[3][col_idx]) if len(rows) > 3 and col_idx < len(rows[3]) else 0.0
            # Nếu sản lượng bằng 0 hoặc chưa có thì vẫn lưu nếu có chỉ số khác
            record = {
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'san_luong_tan': san_luong,
                'tong_nguyen_lieu_tan': clean_number(rows[4][col_idx]) if len(rows) > 4 and col_idx < len(rows[4]) else 0.0,
                'tong_nl_dot_tan': clean_number(rows[5][col_idx]) if len(rows) > 5 and col_idx < len(rows[5]) else 0.0,
                'ty_le_che_bien': clean_number(rows[6][col_idx]) if len(rows) > 6 and col_idx < len(rows[6]) else 0.0,
                'do_am_tb_pct': clean_number(rows[7][col_idx]) if len(rows) > 7 and col_idx < len(rows[7]) else 0.0,
                'ty_trong_vien': clean_number(rows[8][col_idx]) if len(rows) > 8 and col_idx < len(rows[8]) else 0.0,
                'nang_suat_tb_tph': clean_number(rows[9][col_idx]) if len(rows) > 9 and col_idx < len(rows[9]) else 0.0,
                'nguyen_lieu_nhap_tan': clean_number(rows[10][col_idx]) if len(rows) > 10 and col_idx < len(rows[10]) else 0.0,
                'chi_tieu_tan': clean_number(rows[11][col_idx]) if len(rows) > 11 and col_idx < len(rows[11]) else 0.0,
            }
            if record['san_luong_tan'] > 0 or record['tong_nguyen_lieu_tan'] > 0:
                records.append(record)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_weekly_report(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu báo cáo tuần từ sheet 'weekly report'.
        Bao gồm: sản lượng, suất điện, dầu diezen, độ ẩm, độ tro, tỷ lệ chế biến.
        """
        rows = self.get_sheet_values('weekly report')
        if len(rows) < 17:
            return pd.DataFrame()

        # Dòng 2 (index 1): Số tuần (Tuần 31, 32, ...)
        week_row = rows[1]
        records = []

        for col_idx in range(2, len(week_row)):
            week_str = week_row[col_idx].strip().replace(',0', '').replace('.0', '')
            if not week_str or not week_str.isdigit():
                continue
            week_num = int(week_str)

            # Lấy các chỉ tiêu theo dòng
            san_luong = clean_number(rows[2][col_idx]) if len(rows) > 2 and col_idx < len(rows[2]) else 0.0
            if san_luong == 0 and clean_number(rows[3][col_idx]) == 0:
                continue

            record = {
                'week': week_num,
                'week_label': f"Tuần {week_num}",
                'san_luong_tan': san_luong,
                'gio_hoat_dong': clean_number(rows[3][col_idx]) if len(rows) > 3 and col_idx < len(rows[3]) else 0.0,
                'nang_suat_ep_tph': clean_number(rows[4][col_idx]) if len(rows) > 4 and col_idx < len(rows[4]) else 0.0,
                'dien_kwh': clean_number(rows[5][col_idx]) if len(rows) > 5 and col_idx < len(rows[5]) else 0.0,
                'tien_dien_vnd': clean_number(rows[6][col_idx]) if len(rows) > 6 and col_idx < len(rows[6]) else 0.0,
                'dien_tb_kwh_tan': clean_number(rows[7][col_idx]) if len(rows) > 7 and col_idx < len(rows[7]) else 0.0,
                'tien_dien_per_tan': clean_number(rows[8][col_idx]) if len(rows) > 8 and col_idx < len(rows[8]) else 0.0,
                'diezen_lit': clean_number(rows[9][col_idx]) if len(rows) > 9 and col_idx < len(rows[9]) else 0.0,
                'diezen_tb_lit_tan': clean_number(rows[10][col_idx]) if len(rows) > 10 and col_idx < len(rows[10]) else 0.0,
                'do_am_vien_pct': clean_number(rows[11][col_idx]) if len(rows) > 11 and col_idx < len(rows[11]) else 0.0,
                'ty_trong_vien': clean_number(rows[12][col_idx]) if len(rows) > 12 and col_idx < len(rows[12]) else 0.0,
                'do_tro_pct': clean_number(rows[13][col_idx]) if len(rows) > 13 and col_idx < len(rows[13]) else 0.0,
                'nguyen_lieu_tan': clean_number(rows[14][col_idx]) if len(rows) > 14 and col_idx < len(rows[14]) else 0.0,
                'nl_dot_tan': clean_number(rows[15][col_idx]) if len(rows) > 15 and col_idx < len(rows[15]) else 0.0,
                'ty_le_che_bien': clean_number(rows[16][col_idx]) if len(rows) > 16 and col_idx < len(rows[16]) else 0.0,
            }
            records.append(record)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('week').reset_index(drop=True)
        return df

    def load_monthly_report(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu báo cáo tháng từ sheet 'Monthly report'.
        """
        rows = self.get_sheet_values('Monthly report')
        if len(rows) < 17:
            return pd.DataFrame()

        month_row = rows[0]
        records = []

        for col_idx in range(2, len(month_row)):
            m_str = month_row[col_idx].strip()
            if not m_str or m_str in ['-', 'Năm', '2026']:
                continue

            san_luong = clean_number(rows[1][col_idx]) if len(rows) > 1 and col_idx < len(rows[1]) else 0.0
            if san_luong == 0:
                continue

            record = {
                'month_label': m_str,
                'san_luong_tan': san_luong,
                'gio_hoat_dong': clean_number(rows[2][col_idx]) if len(rows) > 2 and col_idx < len(rows[2]) else 0.0,
                'nang_suat_ep_tph': clean_number(rows[3][col_idx]) if len(rows) > 3 and col_idx < len(rows[3]) else 0.0,
                'dien_kwh': clean_number(rows[4][col_idx]) if len(rows) > 4 and col_idx < len(rows[4]) else 0.0,
                'tien_dien_vnd': clean_number(rows[5][col_idx]) if len(rows) > 5 and col_idx < len(rows[5]) else 0.0,
                'dien_tb_kwh_tan': clean_number(rows[6][col_idx]) if len(rows) > 6 and col_idx < len(rows[6]) else 0.0,
                'tien_dien_per_tan': clean_number(rows[7][col_idx]) if len(rows) > 7 and col_idx < len(rows[7]) else 0.0,
                'diezen_lit': clean_number(rows[8][col_idx]) if len(rows) > 8 and col_idx < len(rows[8]) else 0.0,
                'diezen_tb_lit_tan': clean_number(rows[9][col_idx]) if len(rows) > 9 and col_idx < len(rows[9]) else 0.0,
                'do_am_vien_pct': clean_number(rows[10][col_idx]) if len(rows) > 10 and col_idx < len(rows[10]) else 0.0,
                'ty_trong_vien': clean_number(rows[11][col_idx]) if len(rows) > 11 and col_idx < len(rows[11]) else 0.0,
                'do_tro_pct': clean_number(rows[12][col_idx]) if len(rows) > 12 and col_idx < len(rows[12]) else 0.0,
                'nguyen_lieu_sx_tan': clean_number(rows[13][col_idx]) if len(rows) > 13 and col_idx < len(rows[13]) else 0.0,
                'nl_dot_tan': clean_number(rows[14][col_idx]) if len(rows) > 14 and col_idx < len(rows[14]) else 0.0,
                'ty_le_che_bien': clean_number(rows[15][col_idx]) if len(rows) > 15 and col_idx < len(rows[15]) else 0.0,
                'nl_mua_tan': clean_number(rows[16][col_idx]) if len(rows) > 16 and col_idx < len(rows[16]) else 0.0,
                'ton_kho_tan': clean_number(rows[17][col_idx]) if len(rows) > 17 and col_idx < len(rows[17]) else 0.0,
            }
            records.append(record)

        return pd.DataFrame(records)

    def load_kcs_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu KCS (độ ẩm dăm, sau sấy, độ ẩm viên, độ tro).
        """
        rows = self.get_sheet_values('KCS')
        if len(rows) < 4:
            return pd.DataFrame()

        records = []
        for r in rows[3:]:
            if not r or not r[0].strip():
                continue
            date_dt = parse_vn_date(r[0])
            if not date_dt:
                continue

            record = {
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'week': clean_number(r[1]) if len(r) > 1 else 0,
                'time_sample': r[2].strip() if len(r) > 2 else '',
                'shift_leader': r[3].strip() if len(r) > 3 else '',
                'tester': r[4].strip() if len(r) > 4 else '',
                'ty_le_nl_dot': r[5].strip() if len(r) > 5 else '',
                'ty_le_phoi_tron': r[6].strip() if len(r) > 6 else '',
                'am_dam_pct': clean_number(r[7] if len(r) > 7 else 0),
                'am_truoc_say_pct': clean_number(r[8] if len(r) > 8 else 0),
                'am_sau_say_1_pct': clean_number(r[9] if len(r) > 9 else 0),
                'am_sau_say_2_pct': clean_number(r[10] if len(r) > 10 else 0),
                'am_vien_pct': clean_number(r[11] if len(r) > 11 else 0),
                'density_dam': clean_number(r[12] if len(r) > 12 else 0),
                'density_nghien_tho': clean_number(r[13] if len(r) > 13 else 0),
                'density_nghien_tinh': clean_number(r[14] if len(r) > 14 else 0),
                'density_vien': clean_number(r[15] if len(r) > 15 else 0),
                'do_tro_pct': clean_number(r[21] if len(r) > 21 else 0),
            }
            # Chỉ lấy các dòng có ít nhất 1 giá trị độ ẩm hoặc độ tro
            if any([record['am_dam_pct'], record['am_sau_say_1_pct'], record['am_sau_say_2_pct'], record['am_vien_pct'], record['do_tro_pct']]):
                records.append(record)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_diezen_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu tiêu thụ dầu Diezen từ sheet 'Diezen'.
        """
        rows = self.get_sheet_values('Diezen')
        if len(rows) < 2:
            return pd.DataFrame()

        header = rows[0]
        records = []
        for r in rows[1:]:
            if not r or len(r) < 2:
                continue
            week_str = r[1].strip()
            if not week_str or not week_str.isdigit():
                continue
            
            week_num = int(week_str)
            item = {
                'month': r[0].strip(),
                'week': week_num,
                'week_label': f"Tuần {week_num}",
            }
            total_lit = 0.0
            for col_idx in range(2, len(header)):
                col_name = header[col_idx].strip()
                if not col_name:
                    continue
                val = clean_number(r[col_idx] if col_idx < len(r) else 0)
                item[col_name] = val
                total_lit += val
            item['tong_diezen_lit'] = total_lit
            if total_lit > 0:
                records.append(item)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('week').reset_index(drop=True)
        return df

    def load_wm_kpi_scores(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Đọc bảng điểm KPI theo tuần và theo tháng từ sheet 'W-M KPI' của file 2026 Nhat ky KPI.
        """
        rows = self.get_kpi_sheet_values('W-M KPI')
        if not rows or len(rows) < 2:
            return pd.DataFrame(), pd.DataFrame()

        weekly_records = []
        monthly_records = []

        for r in rows[1:]:
            # 1. Tuần: Col 0-3
            if len(r) > 3 and r[0].strip() and r[0].strip().isdigit():
                w_num = int(r[0].strip())
                long_score = clean_number(r[1])
                sac_score = clean_number(r[2])
                tai_score = clean_number(r[3])
                if any(s > 0 for s in [long_score, sac_score, tai_score]):
                    weekly_records.append({
                        'week': w_num,
                        'week_label': f"Tuần {w_num}",
                        'Long': long_score if long_score > 0 else None,
                        'Sắc': sac_score if sac_score > 0 else None,
                        'Tài': tai_score if tai_score > 0 else None,
                    })

            # 2. Tháng: Col 7-10
            if len(r) > 10 and r[7].strip() and 'tháng' in r[7].strip().lower():
                m_label = r[7].strip()
                long_m = clean_number(r[8])
                sac_m = clean_number(r[9])
                tai_m = clean_number(r[10])
                if any(s > 0 for s in [long_m, sac_m, tai_m]):
                    monthly_records.append({
                        'month_label': m_label,
                        'Long': long_m if long_m > 0 else None,
                        'Sắc': sac_m if sac_m > 0 else None,
                        'Tài': tai_m if tai_m > 0 else None,
                    })

        df_w = pd.DataFrame(weekly_records)
        df_m = pd.DataFrame(monthly_records)
        return df_w, df_m

    def load_leader_kpi_sheet(self, leader_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Đọc chi tiết các tiêu chí điểm KPI theo tuần và tháng của từng ca trưởng ('Long', 'Sắc', 'Tài').
        """
        rows = self.get_kpi_sheet_values(leader_name)
        if not rows or len(rows) < 2:
            return pd.DataFrame(), pd.DataFrame()

        weekly_records = []
        monthly_records = []

        for r in rows[1:]:
            # Phần Tuần: Col 0-12
            if len(r) > 12 and r[0].strip() and r[0].strip().isdigit():
                kpi_score = clean_number(r[12])
                sl_actual = clean_number(r[4])
                if kpi_score > 0 or sl_actual > 0:
                    weekly_records.append({
                        'week': int(r[0].strip()),
                        'week_label': f"Tuần {r[0].strip()}",
                        'ca_truong': leader_name,
                        'so_ca': clean_number(r[2]),
                        'chi_tieu_sl': clean_number(r[3]),
                        'sl_thuc_te': sl_actual,
                        'diem_sl': clean_number(r[5]),
                        'do_am_tb': clean_number(r[6]),
                        'diem_am': clean_number(r[7]),
                        'dien_tb': clean_number(r[8]),
                        'diem_dien': clean_number(r[9]),
                        'nang_suat_tb': clean_number(r[10]),
                        'diem_nang_suat': clean_number(r[11]),
                        'diem_kpi': kpi_score,
                    })

            # Phần Tháng: Col 14-26
            if len(r) > 26 and r[14].strip() and 'tháng' in r[14].strip().lower():
                kpi_m = clean_number(r[26])
                sl_m = clean_number(r[18])
                if kpi_m > 0 or sl_m > 0:
                    monthly_records.append({
                        'month_label': r[14].strip(),
                        'ca_truong': leader_name,
                        'so_ca': clean_number(r[16]),
                        'chi_tieu_sl': clean_number(r[17]),
                        'sl_thuc_te': sl_m,
                        'diem_sl': clean_number(r[19]),
                        'do_am_tb': clean_number(r[20]),
                        'diem_am': clean_number(r[21]),
                        'dien_tb': clean_number(r[22]),
                        'diem_dien': clean_number(r[23]),
                        'nang_suat_tb': clean_number(r[24]),
                        'diem_nang_suat': clean_number(r[25]),
                        'diem_kpi': kpi_m,
                    })

        df_w = pd.DataFrame(weekly_records)
        df_m = pd.DataFrame(monthly_records)
        return df_w, df_m

    def load_all_leaders_kpi(self) -> Dict[str, pd.DataFrame]:
        """
        Tổng hợp chi tiết điểm KPI của cả 3 Ca Trưởng (Long, Sắc, Tài).
        """
        all_weekly = []
        all_monthly = []
        for name in ['Long', 'Sắc', 'Tài']:
            try:
                df_w, df_m = self.load_leader_kpi_sheet(name)
                if not df_w.empty:
                    all_weekly.append(df_w)
                if not df_m.empty:
                    all_monthly.append(df_m)
            except Exception as e:
                print(f"[-] Lỗi đọc sheet KPI của {name}: {e}")

        df_all_w = pd.concat(all_weekly, ignore_index=True) if all_weekly else pd.DataFrame()
        df_all_m = pd.concat(all_monthly, ignore_index=True) if all_monthly else pd.DataFrame()
        if not df_all_w.empty:
            df_all_w = df_all_w.sort_values(['week', 'diem_kpi'], ascending=[True, False]).reset_index(drop=True)
        return {'weekly': df_all_w, 'monthly': df_all_m}

    def load_kpi_chart_data(self, sheet_name: str) -> pd.DataFrame:
        """
        Đọc dữ liệu so sánh 3 ca trưởng theo ngày từ các sheet biểu đồ:
        'Chart moisture', 'Chart dien', 'Chart capacity'
        """
        rows = self.get_kpi_sheet_values(sheet_name)
        if not rows or len(rows) < 3:
            return pd.DataFrame()

        records = []
        for r in rows[2:]:
            if not r or not r[0].strip():
                continue
            date_dt = parse_vn_date(r[0])
            if not date_dt:
                continue

            item = {
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'Long': clean_number(r[1]) if len(r) > 1 and r[1].strip() not in ['', '-'] else None,
                'Sắc': clean_number(r[2]) if len(r) > 2 and r[2].strip() not in ['', '-'] else None,
                'Tài': clean_number(r[3]) if len(r) > 3 and r[3].strip() not in ['', '-'] else None,
            }
            if len(r) > 4 and r[4].strip() not in ['', '-']:
                item['Trung_binh'] = clean_number(r[4])
            if len(r) > 5 and r[5].strip() not in ['', '-']:
                item['Tieu_chuan'] = clean_number(r[5])
            elif len(r) > 4 and ('Line' in rows[1] or 'Tiêu chuẩn' in rows[1]):
                item['Tieu_chuan'] = clean_number(r[4])

            if any(item[k] is not None for k in ['Long', 'Sắc', 'Tài']):
                records.append(item)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_kpi_daily_shifts(self) -> pd.DataFrame:
        """
        Đọc dữ liệu nhật ký ca từ sheet 'Data' của file KPI.
        """
        rows = self.get_kpi_sheet_values('Data')
        if not rows or len(rows) < 2:
            return pd.DataFrame()

        records = []
        for r in rows[1:]:
            if not r or not r[0].strip() or len(r) < 5:
                continue
            ca_truong = r[2].strip()
            if ca_truong in ['Nghĩ', 'Bảo trì-VS, Long, Sắc', ''] or not r[4].strip() or r[4].strip() == '-':
                continue
            date_dt = parse_vn_date(r[0])
            if not date_dt:
                continue

            records.append({
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'week': int(clean_number(r[1])),
                'ca_truong': ca_truong,
                'chi_tieu_sl': clean_number(r[3]),
                'sl_thuc_te': clean_number(r[4]),
                'dien_tb': clean_number(r[5]),
                'nang_suat_tb': clean_number(r[6]),
                'do_am_tb': clean_number(r[7]),
                'nl_dot': clean_number(r[8]),
                'nl_nghien': clean_number(r[9]),
                'ty_le_che_bien': clean_number(r[10]),
                'quan_so': r[11].strip() if len(r) > 11 else '',
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_incident_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu từ sheet 'Su co' trong file sản xuất.
        Gồm: ID Sự cố, Ngày, Trưởng ca, Mã thiết bị/zone, Hoạt động, Mô tả sự cố, Xử lý, Người làm, Thời gian dừng máy, Trạng thái.
        """
        rows = self.get_sheet_values('Su co')
        if not rows or len(rows) < 2:
            return pd.DataFrame()

        records = []
        for r in rows[1:]:
            if not r or len(r) == 0 or not r[0].strip():
                continue
            
            incident_id = r[0].strip()
            date_raw = r[1].strip() if len(r) > 1 else ''
            date_dt = parse_vn_date(date_raw)
            shift_leader = r[2].strip() if len(r) > 2 else ''
            equipment_raw = r[3].strip() if len(r) > 3 else ''
            eq_list = [eq.strip() for eq in equipment_raw.replace(';', ',').split(',') if eq.strip()] if equipment_raw else []
            sensor_code = r[4].strip() if len(r) > 4 else ''
            activity = r[5].strip() if len(r) > 5 else 'bảo trì sự cố'
            description = r[6].strip() if len(r) > 6 else ''
            solution = r[7].strip() if len(r) > 7 else ''
            performer = r[8].strip() if len(r) > 8 else ''
            duration_h = clean_number(r[9]) if len(r) > 9 else 0.0
            status = r[10].strip() if len(r) > 10 else ''
            if not status and (description or equipment_raw):
                status = 'Hoàn thành'

            week_num = date_dt.isocalendar()[1] if date_dt else 0
            month_num = date_dt.month if date_dt else 0

            records.append({
                'id_su_co': incident_id,
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y') if date_dt else date_raw,
                'week': week_num,
                'week_label': f"Tuần {week_num}" if week_num > 0 else '',
                'month': month_num,
                'month_label': f"Tháng {month_num}" if month_num > 0 else '',
                'shift_leader': shift_leader,
                'equipment_raw': equipment_raw,
                'equipment_list': eq_list,
                'sensor_code': sensor_code,
                'activity': activity,
                'description': description,
                'solution': solution,
                'performer': performer,
                'duration_hours': duration_h,
                'status': status
            })

        df = pd.DataFrame(records)
        return df

    def load_maintenance_log(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu từ file '2026 BẢO TRÌ BVN' (sheet 'Nhật kí bảo trì').
        """
        if not self.maint_log_spreadsheet:
            return pd.DataFrame()

        try:
            ws = self.maint_log_spreadsheet.worksheet('Nhật kí bảo trì')
            rows = ws.get_all_values()
        except Exception as e:
            print(f"[-] Lỗi đọc sheet Nhật kí bảo trì: {e}")
            return pd.DataFrame()

        if len(rows) < 2:
            return pd.DataFrame()

        records = []
        last_seen_date = None

        for r_idx, r in enumerate(rows[2:], start=3):
            if not r or len(r) == 0:
                continue
            
            date_raw = r[0].strip() if len(r) > 0 else ''
            date_dt = parse_vn_date(date_raw)
            if date_dt:
                last_seen_date = date_dt
            
            ca = r[1].strip() if len(r) > 1 else ''
            eq = r[2].strip() if len(r) > 2 else ''
            die_code = r[3].strip() if len(r) > 3 else ''
            act = r[4].strip() if len(r) > 4 else ''
            desc = r[5].strip() if len(r) > 5 else ''
            duration = r[6].strip() if len(r) > 6 else ''
            duration_h = clean_number(duration)
            performer = r[7].strip() if len(r) > 7 else ''
            status = r[8].strip() if len(r) > 8 else 'Hoàn thành'

            if not eq and not act and not desc:
                continue

            eff_date = date_dt if date_dt else last_seen_date
            week_num = eff_date.isocalendar()[1] if eff_date else 0
            month_num = eff_date.month if eff_date else 0

            records.append({
                'row_index': r_idx,
                'date': eff_date,
                'date_str': eff_date.strftime('%d/%m/%Y') if eff_date else (date_raw or 'N/A'),
                'week': week_num,
                'week_label': f"Tuần {week_num}" if week_num > 0 else '',
                'month': month_num,
                'month_label': f"Tháng {month_num}" if month_num > 0 else '',
                'ca': ca,
                'equipment': eq,
                'die_code': die_code,
                'activity': act if act else 'Bảo trì chung',
                'description': desc,
                'duration_hours': duration_h,
                'duration_str': duration,
                'performer': performer,
                'status': status if status else 'Hoàn thành'
            })

        return pd.DataFrame(records)

    def load_maintenance_plan_monthly(self) -> pd.DataFrame:
        """
        Đọc các sheet kế hoạch bảo trì theo tháng (082026, 092026...) từ file 'Mainternance BVN QB'.
        """
        if not self.maint_plan_spreadsheet:
            return pd.DataFrame()

        records = []
        try:
            worksheets = self.maint_plan_spreadsheet.worksheets()
        except Exception as e:
            print(f"[-] Lỗi lấy danh sách worksheets: {e}")
            return pd.DataFrame()

        for ws in worksheets:
            t = ws.title.strip()
            # Tìm sheet có dạng MMYYYY (6 chữ số) ví dụ 082026, 092026
            if len(t) == 6 and t.isdigit():
                m_label = f"Tháng {t[:2]}/{t[2:]}"
                try:
                    rows = ws.get_all_values()
                    if len(rows) < 7:
                        continue
                    for r in rows[6:]:
                        if len(r) < 5 or not r[1].strip():
                            continue
                        task_name = r[1].strip()
                        eq_code = r[2].strip() if len(r) > 2 else ''
                        priority = r[3].strip() if len(r) > 3 else 'Trung bình'
                        pic = r[4].strip() if len(r) > 4 else ''
                        status = r[5].strip() if len(r) > 5 else 'Chưa bắt đầu'
                        start_date = r[6].strip() if len(r) > 6 else ''
                        end_date = r[7].strip() if len(r) > 7 else ''
                        total_days = clean_number(r[8]) if len(r) > 8 else 0.0
                        material = r[9].strip() if len(r) > 9 else ''
                        mat_status = r[10].strip() if len(r) > 10 else ''
                        result = r[11].strip() if len(r) > 11 else ''

                        records.append({
                            'month_tab': t,
                            'month_label': m_label,
                            'task_name': task_name,
                            'equipment': eq_code,
                            'priority': priority if priority else 'Trung bình',
                            'pic': pic,
                            'status': status if status else 'Chưa bắt đầu',
                            'start_date': start_date,
                            'end_date': end_date,
                            'total_days': total_days,
                            'material': material,
                            'material_status': mat_status,
                            'result': result
                        })
                except Exception as e:
                    print(f"[-] Lỗi đọc sheet {t}: {e}")

        return pd.DataFrame(records)

    def load_4m_management(self) -> pd.DataFrame:
        """
        Đọc bảng quản trị mục tiêu chiến lược 4M từ file 'Mainternance BVN QB'.
        """
        if not self.maint_plan_spreadsheet:
            return pd.DataFrame()

        try:
            ws = self.maint_plan_spreadsheet.worksheet('Theo dõi 4M2026')
            rows = ws.get_all_values()
        except Exception as e:
            print(f"[-] Lỗi đọc sheet Theo dõi 4M2026: {e}")
            return pd.DataFrame()

        if len(rows) < 7:
            return pd.DataFrame()

        records = []
        for r in rows[6:]:
            if len(r) < 4 or not r[2].strip():
                continue
            pillar = r[1].strip() if len(r) > 1 else 'General'
            obj = r[2].strip() if len(r) > 2 else ''
            action = r[3].strip() if len(r) > 3 else ''
            pic = r[4].strip() if len(r) > 4 else ''
            deadline = r[5].strip() if len(r) > 5 else '31/12/2026'
            status = r[6].strip() if len(r) > 6 else 'Chưa bắt đầu'
            evaluation = r[7].strip() if len(r) > 7 else ''

            records.append({
                'pillar': pillar,
                'objective': obj,
                'action': action,
                'pic': pic,
                'deadline': deadline,
                'status': status if status else 'Chưa bắt đầu',
                'evaluation': evaluation
            })

        return pd.DataFrame(records)

    def load_wood_pellet_process_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Nạp dữ liệu quy trình chế biến viên nén gỗ từ Google Sheets hoặc cache cục bộ:
        https://docs.google.com/spreadsheets/d/1ruzLoVB_LOqmwkkz4iR_1uwVyUr0A4aykl_zdXuwluw/edit
        Nếu chưa được phân quyền (403), trả về dict chứa thông tin trạng thái để hướng dẫn người dùng cấp quyền.
        """
        result = {
            'status': 'PENDING',
            'sheet_id': self.process_spreadsheet_id,
            'sheet_url': f"https://docs.google.com/spreadsheets/d/{self.process_spreadsheet_id}/edit?gid=0#gid=0",
            'service_email': 'bvn-reporter@boxwood-dynamo-508304-t4.iam.gserviceaccount.com',
            'title': 'Quy Trình Chế Biến Viên Nén Gỗ BVN',
            'sheets_data': {},
            'error_message': ''
        }

        if force_reload:
            self.process_spreadsheet = None

        if not self.client:
            self.connect()

        if not self.client:
            result['status'] = 'NO_CLIENT'
            result['error_message'] = 'Chưa khởi tạo được kết nối Google Sheets.'
            # Thử đọc từ cache cục bộ nếu có
            local_cache = os.path.join(os.path.dirname(__file__), "assets", "cache_process_sheets.xlsx")
            if os.path.exists(local_cache):
                try:
                    excel_data = pd.read_excel(local_cache, sheet_name=None)
                    if excel_data:
                        result['sheets_data'] = excel_data
                        result['status'] = 'LOCAL_CACHE'
                        result['title'] = 'Quy Trình Chế Biến Viên Nén Gỗ (Bản Lưu Cục Bộ)'
                except Exception:
                    pass
            return result

        try:
            if not self.process_spreadsheet:
                self.process_spreadsheet = self.client.open_by_key(self.process_spreadsheet_id)

            if self.process_spreadsheet:
                result['title'] = self.process_spreadsheet.title
                result['status'] = 'CONNECTED'
                for ws in self.process_spreadsheet.worksheets():
                    vals = ws.get_all_values()
                    if vals and len(vals) > 1:
                        df = pd.DataFrame(vals[1:], columns=vals[0])
                    elif vals:
                        df = pd.DataFrame(vals)
                    else:
                        df = pd.DataFrame()
                    result['sheets_data'][ws.title] = df
        except Exception as e:
            err_str = str(e)
            is_perm = ('403' in err_str or 'Permission' in err_str or 'The caller does not have permission' in err_str or isinstance(e, PermissionError))
            result['status'] = 'PERMISSION_DENIED' if is_perm else 'ERROR'
            result['error_message'] = err_str

            # Nếu lỗi phân quyền Google API, kiểm tra xem có file cache cục bộ dự phòng không
            local_cache = os.path.join(os.path.dirname(__file__), "assets", "cache_process_sheets.xlsx")
            if os.path.exists(local_cache):
                try:
                    excel_data = pd.read_excel(local_cache, sheet_name=None)
                    if excel_data:
                        result['sheets_data'] = excel_data
                        result['status'] = 'LOCAL_CACHE'
                        result['title'] = 'Quy Trình Chế Biến Viên Nén Gỗ (Bản Lưu Cục Bộ)'
                except Exception:
                    pass

        return result

    def save_shift_record(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Ghi dữ liệu báo cáo ca sản xuất vào Google Sheets 'Product' và cập nhật cache cục bộ.
        - Tìm dòng khớp ngày và ca trưởng (hoặc dòng trống cùng ngày).
        - Cập nhật dải ô D{row}:AJ{row}.
        - Nếu chưa có ngày trong bảng tính, thêm dòng mới (append_row).
        - Tự động cập nhật bộ đệm cache_shifts.parquet để hiển thị ngay trên Dashboard.
        """
        if not self.client:
            self.connect()

        if not self.client or not self.spreadsheet:
            return False, "Chưa kết nối được với Google Sheets sản xuất."

        try:
            ws = self.spreadsheet.worksheet('Product')
            vals = ws.get_all_values()

            date_dt = record.get('date')
            if isinstance(date_dt, str):
                date_dt = parse_vn_date(date_dt)
            if not date_dt:
                date_dt = datetime.now()

            d_str = date_dt.strftime('%d/%m/%Y')
            d_short = f"{date_dt.day}/{date_dt.month}/{date_dt.year}"
            ca_truong = str(record.get('shift_leader', '')).strip()

            month_val = date_dt.month
            week_val = date_dt.isocalendar()[1]

            # Tính toán các chỉ số phái sinh
            san_luong = float(record.get('san_luong_tan', 0.0))
            chi_tieu = float(record.get('chi_tieu_tan', 90.0))
            dien_kwh = float(record.get('dien_kwh', 0.0))
            dien_tb = round(dien_kwh / san_luong, 2) if san_luong > 0 else 0.0
            tien_dien = round(dien_kwh * 2200, 0) # Đơn giá ước tính 2,200đ/kWh

            # Giờ máy chạy
            pe_hours = [float(record.get(f'h_PE{i}', 0.0)) for i in range(1, 9)]
            tong_gio_ep = sum(pe_hours)
            nang_suat = round(san_luong / tong_gio_ep, 2) if tong_gio_ep > 0 else 0.0

            # Dãy giá trị từ cột D đến cột AJ (33 cột)
            row_vals = [
                ca_truong,                                          # D: Ca trưởng
                str(record.get('nl_dot_spoon', 13)),                # E: Muỗng dăm đốt
                "1,4",                                              # F: Hệ số
                str(record.get('nl_dot_tan', 18)),                  # G: Dăm đốt tấn
                str(record.get('nghien_tho_spoon', 105)),           # H: Muỗng nghiền thô
                "1,8",                                              # I: Hệ số
                str(record.get('nghien_tho_tan', 189)),             # J: Nghiền thô tấn
                str(san_luong).replace('.', ','),                   # K: Sản lượng
                str(chi_tieu).replace('.', ','),                    # L: Chỉ tiêu
                str(record.get('xuat_hang_tan', '')),               # M: Xuất hàng
                str(record.get('ton_kho_tan', '')),                 # N: Tồn kho
                "0%",                                               # O: Tỷ lệ
                str(int(dien_kwh)),                                 # P: Điện kWh
                str(int(tien_dien)),                                # Q: Tiền điện
                str(dien_tb).replace('.', ','),                     # R: Suất điện
                str(record.get('h_HM118', 0)),                      # S: HM118
                str(record.get('h_HM218', 0)),                      # T: HM218
                str(record.get('h_HM318', 0)),                      # U: HM318
                str(record.get('h_DR124', 0)),                      # V: DR124
                str(record.get('h_DR224', 0)),                      # W: DR224
                str(record.get('h_HM147', 0)),                      # X: HM147
                str(record.get('h_HM247', 0)),                      # Y: HM247
                str(record.get('h_HM347', 0)),                      # Z: HM347
                str(pe_hours[0]),                                   # AA: PE1
                str(pe_hours[1]),                                   # AB: PE2
                str(pe_hours[2]),                                   # AC: PE3
                str(pe_hours[3]),                                   # AD: PE4
                str(pe_hours[4]),                                   # AE: PE5
                str(pe_hours[5]),                                   # AF: PE6
                str(pe_hours[6]),                                   # AG: PE7
                str(pe_hours[7]),                                   # AH: PE8
                str(tong_gio_ep),                                   # AI: Tổng giờ ép
                str(nang_suat).replace('.', ',')                    # AJ: Năng suất ép
            ]

            target_row = None
            # 1. Tìm dòng có cùng ngày và khớp Ca Trưởng
            for idx, r in enumerate(vals):
                if r and (d_str in r[0] or d_short in r[0]):
                    r_leader = r[3].strip() if len(r) > 3 else ''
                    if r_leader == ca_truong:
                        target_row = idx + 1
                        break

            # 2. Nếu chưa tìm thấy, tìm dòng cùng ngày nhưng chưa có Ca Trưởng (dòng trống)
            if not target_row:
                for idx, r in enumerate(vals):
                    if r and (d_str in r[0] or d_short in r[0]):
                        r_leader = r[3].strip() if len(r) > 3 else ''
                        r_sl = r[10].strip() if len(r) > 10 else ''
                        if r_leader == '' and r_sl == '':
                            target_row = idx + 1
                            break

            if target_row:
                # Cập nhật dải ô D:AJ của dòng đã có sẵn
                ws.update(range_name=f"D{target_row}:AJ{target_row}", values=[row_vals], value_input_option='USER_ENTERED')
                msg = f"Đã cập nhật thành công dữ liệu ngày {d_str} cho Ca Trưởng {ca_truong} (Dòng {target_row}) trên Google Sheets!"
            else:
                # Nếu chưa có dòng nào của ngày này -> Thêm dòng mới
                full_row = [d_str, str(month_val), str(week_val)] + row_vals
                ws.append_row(full_row, value_input_option='USER_ENTERED')
                msg = f"Đã thêm mới thành công dữ liệu ngày {d_str} cho Ca Trưởng {ca_truong} vào Google Sheets!"

            # 3. Cập nhật bộ đệm cục bộ (cache_shifts.parquet)
            cache_paths = [
                os.path.join(os.path.dirname(__file__), "assets", "cache_shifts.parquet"),
                os.path.join("assets", "cache_shifts.parquet"),
                os.path.join("deploy_files", "assets", "cache_shifts.parquet"),
            ]
            try:
                for cp in cache_paths:
                    if os.path.exists(cp):
                        df_c = pd.read_parquet(cp)
                        # Tìm và cập nhật hoặc thêm dòng
                        mask = (df_c['date_str'] == d_str) & (df_c['shift_leader'] == ca_truong)
                        new_row_dict = {
                            'date': pd.to_datetime(date_dt),
                            'date_str': d_str,
                            'month': month_val,
                            'week': week_val,
                            'shift_leader': ca_truong,
                            'nl_dot_spoon': float(record.get('nl_dot_spoon', 13)),
                            'nl_dot_tan': float(record.get('nl_dot_tan', 18)),
                            'nghien_tho_spoon': float(record.get('nghien_tho_spoon', 105)),
                            'nghien_tho_tan': float(record.get('nghien_tho_tan', 189)),
                            'san_luong_tan': san_luong,
                            'chi_tieu_tan': chi_tieu,
                            'xuat_hang_tan': float(record.get('xuat_hang_tan', 0.0)),
                            'ton_kho_tan': float(record.get('ton_kho_tan', 0.0)),
                            'ti_le_nl_dot_pct': 0.0,
                            'dien_kwh': dien_kwh,
                            'tien_dien_vnd': tien_dien,
                            'dien_tb_kwh_tan': dien_tb,
                            'h_HM118': float(record.get('h_HM118', 0)),
                            'h_HM218': float(record.get('h_HM218', 0)),
                            'h_HM318': float(record.get('h_HM318', 0)),
                            'h_DR124': float(record.get('h_DR124', 0)),
                            'h_DR224': float(record.get('h_DR224', 0)),
                            'h_HM147': float(record.get('h_HM147', 0)),
                            'h_HM247': float(record.get('h_HM247', 0)),
                            'h_HM347': float(record.get('h_HM347', 0)),
                            'h_PE1': pe_hours[0],
                            'h_PE2': pe_hours[1],
                            'h_PE3': pe_hours[2],
                            'h_PE4': pe_hours[3],
                            'h_PE5': pe_hours[4],
                            'h_PE6': pe_hours[5],
                            'h_PE7': pe_hours[6],
                            'h_PE8': pe_hours[7],
                            'tong_gio_ep': tong_gio_ep,
                            'nang_suat_tph': nang_suat,
                        }
                        if mask.any():
                            for k, v in new_row_dict.items():
                                if k in df_c.columns:
                                    df_c.loc[mask, k] = v
                        else:
                            df_c = pd.concat([df_c, pd.DataFrame([new_row_dict])], ignore_index=True)
                        df_c = df_c.sort_values('date').reset_index(drop=True)
                        df_c.to_parquet(cp, index=False)
            except Exception as e_cache:
                print(f"[-] Lỗi cập nhật cache parquet: {e_cache}")

            return True, msg

        except Exception as e:
            return False, f"Lỗi ghi dữ liệu Google Sheets: {e}"

    def save_kcs_record(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Ghi dữ liệu kết quả đo kiểm chất lượng KCS vào Google Sheets 'KCS'.
        """
        if not self.client:
            self.connect()

        if not self.client or not self.spreadsheet:
            return False, "Chưa kết nối được với Google Sheets sản xuất."

        try:
            ws = self.spreadsheet.worksheet('KCS')
            date_dt = record.get('date')
            if isinstance(date_dt, str):
                date_dt = parse_vn_date(date_dt)
            if not date_dt:
                date_dt = datetime.now()

            d_str = date_dt.strftime('%d/%m/%Y')
            week_val = date_dt.isocalendar()[1]

            row_vals = [
                d_str,                                              # 0: Ngày
                str(week_val),                                      # 1: Tuần
                str(record.get('time_sample', '08h')),              # 2: Giờ lấy mẫu
                str(record.get('shift_leader', '')),                # 3: Ca trưởng
                str(record.get('tester', 'KCS')),                   # 4: Người đo
                str(record.get('ty_le_nl_dot', '100% Củi')),        # 5: Tỷ lệ NL đốt
                str(record.get('ty_le_phoi_tron', '8:2')),          # 6: Tỷ lệ phối trộn
                str(record.get('am_dam_pct', '')).replace('.', ','),        # 7: Ẩm dăm
                str(record.get('am_truoc_say_pct', '')).replace('.', ','),  # 8: Ẩm trước sấy
                str(record.get('am_sau_say_1_pct', '')).replace('.', ','),  # 9: Ẩm sau sấy 1
                str(record.get('am_sau_say_2_pct', '')).replace('.', ','),  # 10: Ẩm sau sấy 2
                str(record.get('am_vien_pct', '')).replace('.', ','),       # 11: Ẩm viên
                str(record.get('density_dam', '')).replace('.', ','),       # 12: Tỷ trọng dăm
                str(record.get('density_nghien_tho', '')).replace('.', ','),# 13: Tỷ trọng nghiền thô
                str(record.get('density_nghien_tinh', '')).replace('.', ','),# 14: Tỷ trọng nghiền tinh
                str(record.get('density_vien', '')).replace('.', ','),      # 15: Tỷ trọng viên
                "", "", "", "", "",                                         # 16-20: Cột trống
                str(record.get('do_tro_pct', '')).replace('.', ',')         # 21: Độ tro
            ]

            ws.append_row(row_vals, value_input_option='USER_ENTERED')
            return True, f"Đã lưu thành công mẫu kiểm nghiệm KCS lúc {record.get('time_sample')} ngày {d_str}!"

        except Exception as e:
            return False, f"Lỗi ghi dữ liệu KCS lên Google Sheets: {e}"






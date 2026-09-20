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
DEFAULT_HR_SPREADSHEET_ID = "1enwVBuwwFK7k6r4i_xcg_7oJgckLaOfzNUkHPRZfY6s"
DEFAULT_HR_GID = "987654321"
DEFAULT_OIL_CHANGE_SPREADSHEET_ID = "1DRHrUPkLk7650XbxW1zZ73dp0k0Dcg4FZeKZriUKRso"
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
        process_spreadsheet_id: str = DEFAULT_PROCESS_SPREADSHEET_ID,
        hr_spreadsheet_id: str = DEFAULT_HR_SPREADSHEET_ID,
        oil_spreadsheet_id: str = DEFAULT_OIL_CHANGE_SPREADSHEET_ID
    ):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.kpi_spreadsheet_id = kpi_spreadsheet_id
        self.maint_log_spreadsheet_id = maint_log_spreadsheet_id
        self.maint_plan_spreadsheet_id = maint_plan_spreadsheet_id
        self.process_spreadsheet_id = process_spreadsheet_id
        self.hr_spreadsheet_id = hr_spreadsheet_id
        self.oil_spreadsheet_id = oil_spreadsheet_id
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.kpi_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.maint_log_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.maint_plan_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.process_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.hr_spreadsheet: Optional[gspread.Spreadsheet] = None
        self.oil_spreadsheet: Optional[gspread.Spreadsheet] = None
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

        try:
            self.oil_spreadsheet = self.client.open_by_key(self.oil_spreadsheet_id)
        except Exception as e:
            try:
                print(f"[-] Không thể mở bảng tính lịch thay nhớt máy ép: {e}")
            except Exception:
                print(f"[-] Cannot open oil change spreadsheet: {e}")
            self.oil_spreadsheet = None

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
                    wait_sec = 2.5 * (attempt + 1) if '429' in str(e) else 0.8 * (attempt + 1)
                    time.sleep(wait_sec)
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
                    wait_sec = 2.5 * (attempt + 1) if '429' in str(e) else 0.8 * (attempt + 1)
                    time.sleep(wait_sec)
        return []


    def load_shift_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu ca/ngày từ sheet 'Product_Data' (ưu tiên) hoặc 'Product' (dự phòng).
        Bao gồm: sản lượng, chỉ tiêu, điện năng, giờ chạy các máy nghiền, sấy, ép viên.
        Tích hợp bộ đệm cục bộ (cache_shifts.parquet) dự phòng khi mất kết nối mạng.
        """
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_shifts.parquet"),
            os.path.join("assets", "cache_shifts.parquet"),
            os.path.join("deploy_files", "assets", "cache_shifts.parquet"),
        ]

        # Ưu tiên nạp từ sheet mới 'Product_Data', nếu không có hoặc rỗng thì nạp 'Product'
        raw_rows = self.get_sheet_values('Product_Data')
        if not raw_rows or len(raw_rows) < 3:
            raw_rows = self.get_sheet_values('Product')

        if len(raw_rows) < 3:
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

        # Tự động nhận diện dòng bắt đầu dữ liệu (Product_Data bắt đầu từ dòng 3, Product cũ bắt đầu từ dòng 7)
        start_idx = 2
        for idx in range(min(10, len(raw_rows))):
            if raw_rows[idx] and len(raw_rows[idx]) > 0 and parse_vn_date(raw_rows[idx][0].strip()):
                start_idx = idx
                break

        records = []
        for r_idx, r in enumerate(raw_rows[start_idx:], start=start_idx + 1):
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

    @staticmethod
    def compute_kcs_average_moisture(df_kcs: pd.DataFrame, target_date: Any, shift_name: str) -> float:
        """
        Mô phỏng chính xác công thức Google Sheets:
        =IFERROR(AVERAGEIFS('Data KCS'!$N:$N; 'Data KCS'!$B:$B; A2; 'Data KCS'!$F:$F; D2); "")
        Trong đó:
        - 'Data KCS'!$N:$N: am_vien_pct (Cột 14 / index 13)
        - 'Data KCS'!$B:$B: date (Cột 2 / index 1)
        - 'Data KCS'!$F:$F: shift_leader / Trưởng ca (Cột 6 / index 5)
        """
        if df_kcs is None or df_kcs.empty or 'am_vien_pct' not in df_kcs.columns:
            return 0.0
        
        try:
            t_date = pd.to_datetime(target_date).date() if target_date else None
        except Exception:
            t_date = None
        if not t_date:
            return 0.0

        mask_date = df_kcs['date'].dt.date == t_date
        s_clean = str(shift_name).strip().lower()
        
        # Ánh xạ ca tương đương nếu có
        shift_aliases = {
            'ca a': ['ca a', 'thành', 'thanh', 'hải', 'hai'],
            'ca b': ['ca b', 'lâm', 'lam', 'sắc', 'sac'],
            'ca c': ['ca c', 'long', 'tài', 'tai']
        }
        target_keys = [s_clean]
        for k, aliases in shift_aliases.items():
            if s_clean == k or s_clean in aliases:
                target_keys = list(set(target_keys + [k] + aliases))
                break

        mask_shift = df_kcs['shift_leader'].astype(str).str.strip().str.lower().isin(target_keys)
        filtered = df_kcs[mask_date & mask_shift]
        
        if filtered.empty:
            # Tìm kiếm chứa chuỗi
            mask_like = df_kcs['shift_leader'].astype(str).str.contains(s_clean, case=False, na=False)
            filtered = df_kcs[mask_date & mask_like]

        valid_vals = filtered[filtered['am_vien_pct'] > 0]['am_vien_pct']
        if not valid_vals.empty:
            return float(valid_vals.mean())
        return 0.0

    def load_kcs_data(self) -> pd.DataFrame:
        """
        Đọc và chuẩn hóa dữ liệu KCS (độ ẩm dăm, sau sấy, độ ẩm viên, tỷ trọng, độ tro).
        Ưu tiên đọc từ sheet 'Data KCS' của file KPI (self.kpi_spreadsheet),
        sau đó fallback sang sheet 'KCS' của file sản xuất (self.spreadsheet).
        Tự động lưu và tải từ cache cục bộ (cache_kcs.parquet).
        """
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kcs.parquet"),
            os.path.join("assets", "cache_kcs.parquet"),
            os.path.join("deploy_files", "assets", "cache_kcs.parquet"),
        ]

        # 1. Ưu tiên đọc từ 'Data KCS' trong file KPI
        rows = self.get_kpi_sheet_values('Data KCS')

        # 2. Dự phòng đọc từ 'KCS' trong file sản xuất hoặc file KPI
        if not rows or len(rows) < 2:
            rows = self.get_sheet_values('KCS')
        if not rows or len(rows) < 2:
            rows = self.get_kpi_sheet_values('KCS')

        # 3. Nếu không có kết nối mạng, đọc từ cache
        if not rows or len(rows) < 2:
            for cp in cache_paths:
                if os.path.exists(cp):
                    try:
                        return pd.read_parquet(cp)
                    except Exception:
                        pass
            return pd.DataFrame()

        records = []
        for r in rows[1:]:
            if not r or not any(str(c).strip() for c in r):
                continue

            # Xác định vị trí cột Ngày (Col 1 trong Data KCS mới hoặc Col 0 trong KCS cũ)
            dt_candidate_1 = parse_vn_date(r[1]) if len(r) > 1 else None
            dt_candidate_0 = parse_vn_date(r[0])

            if dt_candidate_1:
                date_dt = dt_candidate_1
                sample_id = str(r[0]).strip()
                # Cấu trúc Data KCS mới:
                # 0: ID, 1: Ngày, 2: Tuần, 3: Tháng, 4: Giờ, 5: Trưởng ca, 6: Người đo
                # 7: Tỷ lệ NL đốt, 8: Tỷ lệ phối trộn, 9: Ẩm dăm, 10: Ẩm trước sấy, 11: Ẩm sau sấy 1, 12: Ẩm sau sấy 2
                # 13: Ẩm viên (Col N), 14: Tỷ trọng dăm, 15: Tỷ trọng nghiền thô, 16: Tỷ trọng nghiền tinh, 17: Tỷ trọng viên
                # 18: Nhiệt độ sau làm nguội, 19: Lưới thô, 20: Lưới tinh, 21: Đường kính viên, 22: Chiều dài viên, 23: Độ tro viên
                rec = {
                    'id': sample_id,
                    'date': date_dt,
                    'date_str': date_dt.strftime('%d/%m/%Y'),
                    'week': clean_number(r[2]) if len(r) > 2 else 0,
                    'month': clean_number(r[3]) if len(r) > 3 else 0,
                    'time_sample': str(r[4]).strip() if len(r) > 4 else '',
                    'shift_leader': str(r[5]).strip() if len(r) > 5 else '',
                    'tester': str(r[6]).strip() if len(r) > 6 else '',
                    'ty_le_nl_dot': str(r[7]).strip() if len(r) > 7 else '',
                    'ty_le_phoi_tron': str(r[8]).strip() if len(r) > 8 else '',
                    'am_dam_pct': clean_number(r[9] if len(r) > 9 else 0),
                    'am_truoc_say_pct': clean_number(r[10] if len(r) > 10 else 0),
                    'am_sau_say_1_pct': clean_number(r[11] if len(r) > 11 else 0),
                    'am_sau_say_2_pct': clean_number(r[12] if len(r) > 12 else 0),
                    'am_vien_pct': clean_number(r[13] if len(r) > 13 else 0),
                    'density_dam': clean_number(r[14] if len(r) > 14 else 0),
                    'density_nghien_tho': clean_number(r[15] if len(r) > 15 else 0),
                    'density_nghien_tinh': clean_number(r[16] if len(r) > 16 else 0),
                    'density_vien': clean_number(r[17] if len(r) > 17 else 0),
                    'temp_cooling': clean_number(r[18] if len(r) > 18 else 0),
                    'luoi_nghien_tho': str(r[19]).strip() if len(r) > 19 else '',
                    'luoi_nghien_tinh': str(r[20]).strip() if len(r) > 20 else '',
                    'duong_kinh_vien': clean_number(r[21] if len(r) > 21 else 0),
                    'chieu_dai_vien': str(r[22]).strip() if len(r) > 22 else '',
                    'do_tro_pct': clean_number(r[23] if len(r) > 23 else 0),
                }
            elif dt_candidate_0:
                date_dt = dt_candidate_0
                rec = {
                    'id': '',
                    'date': date_dt,
                    'date_str': date_dt.strftime('%d/%m/%Y'),
                    'week': clean_number(r[1]) if len(r) > 1 else 0,
                    'month': 0,
                    'time_sample': str(r[2]).strip() if len(r) > 2 else '',
                    'shift_leader': str(r[3]).strip() if len(r) > 3 else '',
                    'tester': str(r[4]).strip() if len(r) > 4 else '',
                    'ty_le_nl_dot': str(r[5]).strip() if len(r) > 5 else '',
                    'ty_le_phoi_tron': str(r[6]).strip() if len(r) > 6 else '',
                    'am_dam_pct': clean_number(r[7] if len(r) > 7 else 0),
                    'am_truoc_say_pct': clean_number(r[8] if len(r) > 8 else 0),
                    'am_sau_say_1_pct': clean_number(r[9] if len(r) > 9 else 0),
                    'am_sau_say_2_pct': clean_number(r[10] if len(r) > 10 else 0),
                    'am_vien_pct': clean_number(r[11] if len(r) > 11 else 0),
                    'density_dam': clean_number(r[12] if len(r) > 12 else 0),
                    'density_nghien_tho': clean_number(r[13] if len(r) > 13 else 0),
                    'density_nghien_tinh': clean_number(r[14] if len(r) > 14 else 0),
                    'density_vien': clean_number(r[15] if len(r) > 15 else 0),
                    'temp_cooling': 0.0,
                    'luoi_nghien_tho': '',
                    'luoi_nghien_tinh': '',
                    'duong_kinh_vien': 0.0,
                    'chieu_dai_vien': '',
                    'do_tro_pct': clean_number(r[21] if len(r) > 21 else 0),
                }
            else:
                continue

            if any([rec['am_dam_pct'], rec['am_sau_say_1_pct'], rec['am_sau_say_2_pct'], rec['am_vien_pct'], rec['do_tro_pct'], rec['density_vien']]):
                records.append(rec)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
            for cp in cache_paths:
                try:
                    os.makedirs(os.path.dirname(cp), exist_ok=True)
                    df.to_parquet(cp, index=False)
                except Exception:
                    pass
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
        Hỗ trợ các cột theo Ca A, Ca B, Ca C và ánh xạ tương thích với Long, Sắc, Tài.
        """
        cache_w_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kpi_wm_weekly.parquet"),
            os.path.join("assets", "cache_kpi_wm_weekly.parquet"),
            os.path.join("deploy_files", "assets", "cache_kpi_wm_weekly.parquet"),
        ]
        cache_m_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kpi_wm_monthly.parquet"),
            os.path.join("assets", "cache_kpi_wm_monthly.parquet"),
            os.path.join("deploy_files", "assets", "cache_kpi_wm_monthly.parquet"),
        ]

        rows = self.get_kpi_sheet_values('W-M KPI')
        if not rows or len(rows) < 2:
            # Dự phòng đọc từ cache
            for cw, cm in zip(cache_w_paths, cache_m_paths):
                if os.path.exists(cw) and os.path.exists(cm):
                    try:
                        return pd.read_parquet(cw), pd.read_parquet(cm)
                    except Exception:
                        pass
            return pd.DataFrame(), pd.DataFrame()

        weekly_records = []
        monthly_records = []

        for r in rows[1:]:
            # 1. Tuần: Col 0-3 (Tuần, Ca A, Ca B, Ca C)
            if len(r) > 3 and str(r[0]).strip() and str(r[0]).strip().isdigit():
                w_num = int(str(r[0]).strip())
                score_1 = clean_number(r[1])
                score_2 = clean_number(r[2])
                score_3 = clean_number(r[3])
                if any(s > 0 for s in [score_1, score_2, score_3]):
                    rec_w = {
                        'week': w_num,
                        'week_label': f"Tuần {w_num}",
                        'Ca A': score_1 if score_1 > 0 else None,
                        'Ca B': score_2 if score_2 > 0 else None,
                        'Ca C': score_3 if score_3 > 0 else None,
                        # Ánh xạ tương thích ngược
                        'Long': score_3 if score_3 > 0 else None,
                        'Sắc': score_2 if score_2 > 0 else None,
                        'Tài': score_3 if score_3 > 0 else None,
                        'Thành': score_1 if score_1 > 0 else None,
                        'Lâm': score_2 if score_2 > 0 else None,
                    }
                    weekly_records.append(rec_w)

            # 2. Tháng: Col 7-10 (Tháng, Ca A, Ca B, Ca C)
            if len(r) > 10 and str(r[7]).strip() and 'tháng' in str(r[7]).strip().lower():
                m_label = str(r[7]).strip()
                m_score_1 = clean_number(r[8])
                m_score_2 = clean_number(r[9])
                m_score_3 = clean_number(r[10])
                if any(s > 0 for s in [m_score_1, m_score_2, m_score_3]):
                    rec_m = {
                        'month_label': m_label,
                        'Ca A': m_score_1 if m_score_1 > 0 else None,
                        'Ca B': m_score_2 if m_score_2 > 0 else None,
                        'Ca C': m_score_3 if m_score_3 > 0 else None,
                        # Ánh xạ tương thích ngược
                        'Long': m_score_3 if m_score_3 > 0 else None,
                        'Sắc': m_score_2 if m_score_2 > 0 else None,
                        'Tài': m_score_3 if m_score_3 > 0 else None,
                        'Thành': m_score_1 if m_score_1 > 0 else None,
                        'Lâm': m_score_2 if m_score_2 > 0 else None,
                    }
                    monthly_records.append(rec_m)

        df_w = pd.DataFrame(weekly_records)
        df_m = pd.DataFrame(monthly_records)

        # Cập nhật cache
        if not df_w.empty:
            for cw in cache_w_paths:
                try:
                    os.makedirs(os.path.dirname(cw), exist_ok=True)
                    df_w.to_parquet(cw, index=False)
                except Exception:
                    pass
        if not df_m.empty:
            for cm in cache_m_paths:
                try:
                    os.makedirs(os.path.dirname(cm), exist_ok=True)
                    df_m.to_parquet(cm, index=False)
                except Exception:
                    pass

        return df_w, df_m

    def load_leader_kpi_sheet(self, leader_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Đọc chi tiết các tiêu chí điểm KPI theo tuần và tháng của từng ca ('Ca A', 'Ca B', 'Ca C' hoặc tên ca trưởng).
        Cấu trúc cột:
        Tuần: Col 0: Tuần, Col 1: Ca trưởng, Col 2: Số ca, Col 3: Chỉ tiêu SL, Col 4: SL Thực tế,
              Col 5: Điểm SL (/50), Col 6: Độ ẩm TB, Col 7: Điểm ẩm (/30), Col 8: Điện năng TB,
              Col 9: Năng suất TB, Col 10: Điểm năng suất (/20), Col 11: Điểm KPI (/100)
        Tháng: Col 13: Tháng, Col 14: Ca trưởng, Col 15: Số ca, Col 16: Chỉ tiêu SL, Col 17: SL Thực tế,
               Col 18: Điểm SL (/50), Col 19: Độ ẩm TB, Col 20: Điểm ẩm (/30), Col 21: Điện năng TB,
               Col 22: Năng suất TB, Col 23: Điểm năng suất (/20), Col 24: Điểm KPI (/100)
        """
        target_sheet = leader_name
        alias_map = {
            'Long': 'Ca C', 'Tài': 'Ca C', 'Ca C': 'Ca C',
            'Sắc': 'Ca B', 'Lâm': 'Ca B', 'Ca B': 'Ca B',
            'Thành': 'Ca A', 'Hải': 'Ca A', 'Ca A': 'Ca A'
        }
        rows = self.get_kpi_sheet_values(target_sheet)
        if not rows and target_sheet in alias_map:
            target_sheet = alias_map[target_sheet]
            rows = self.get_kpi_sheet_values(target_sheet)

        if not rows or len(rows) < 2:
            return pd.DataFrame(), pd.DataFrame()

        weekly_records = []
        monthly_records = []

        for r in rows[1:]:
            # Phần Tuần: Col 0-11
            if len(r) > 11 and str(r[0]).strip() and str(r[0]).strip().isdigit():
                kpi_score = clean_number(r[11])
                sl_actual = clean_number(r[4])
                if kpi_score > 0 or sl_actual > 0:
                    weekly_records.append({
                        'week': int(str(r[0]).strip()),
                        'week_label': f"Tuần {str(r[0]).strip()}",
                        'ca_truong': target_sheet,
                        'so_ca': clean_number(r[2]),
                        'chi_tieu_sl': clean_number(r[3]),
                        'sl_thuc_te': sl_actual,
                        'diem_sl': clean_number(r[5]),
                        'do_am_tb': clean_number(r[6]),
                        'diem_am': clean_number(r[7]),
                        'dien_tb': clean_number(r[8]),
                        'diem_dien': 0.0,
                        'nang_suat_tb': clean_number(r[9]),
                        'diem_nang_suat': clean_number(r[10]),
                        'diem_kpi': kpi_score,
                    })

            # Phần Tháng: Col 13-24
            if len(r) > 24 and str(r[13]).strip() and 'tháng' in str(r[13]).strip().lower():
                kpi_m = clean_number(r[24])
                sl_m = clean_number(r[17])
                if kpi_m > 0 or sl_m > 0:
                    monthly_records.append({
                        'month_label': str(r[13]).strip(),
                        'ca_truong': target_sheet,
                        'so_ca': clean_number(r[15]),
                        'chi_tieu_sl': clean_number(r[16]),
                        'sl_thuc_te': sl_m,
                        'diem_sl': clean_number(r[18]),
                        'do_am_tb': clean_number(r[19]),
                        'diem_am': clean_number(r[20]),
                        'dien_tb': clean_number(r[21]),
                        'diem_dien': 0.0,
                        'nang_suat_tb': clean_number(r[22]),
                        'diem_nang_suat': clean_number(r[23]),
                        'diem_kpi': kpi_m,
                    })

        df_w = pd.DataFrame(weekly_records)
        df_m = pd.DataFrame(monthly_records)
        return df_w, df_m

    def load_all_leaders_kpi(self) -> Dict[str, pd.DataFrame]:
        """
        Tổng hợp chi tiết điểm KPI của cả 3 Ca (Ca A, Ca B, Ca C).
        """
        cache_w_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kpi_leaders_weekly.parquet"),
            os.path.join("assets", "cache_kpi_leaders_weekly.parquet"),
            os.path.join("deploy_files", "assets", "cache_kpi_leaders_weekly.parquet"),
        ]
        cache_m_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kpi_leaders_monthly.parquet"),
            os.path.join("assets", "cache_kpi_leaders_monthly.parquet"),
            os.path.join("deploy_files", "assets", "cache_kpi_leaders_monthly.parquet"),
        ]

        all_weekly = []
        all_monthly = []
        target_names = ['Ca A', 'Ca B', 'Ca C']
        for name in target_names:
            try:
                df_w, df_m = self.load_leader_kpi_sheet(name)
                if not df_w.empty:
                    all_weekly.append(df_w)
                if not df_m.empty:
                    all_monthly.append(df_m)
            except Exception as e:
                print(f"[-] Lỗi đọc sheet KPI của {name}: {e}")

        # Fallback tên cũ nếu không đọc được
        if not all_weekly:
            for name in ['Long', 'Sắc', 'Tài']:
                try:
                    df_w, df_m = self.load_leader_kpi_sheet(name)
                    if not df_w.empty:
                        all_weekly.append(df_w)
                    if not df_m.empty:
                        all_monthly.append(df_m)
                except Exception:
                    pass

        df_all_w = pd.concat(all_weekly, ignore_index=True) if all_weekly else pd.DataFrame()
        df_all_m = pd.concat(all_monthly, ignore_index=True) if all_monthly else pd.DataFrame()

        if not df_all_w.empty:
            df_all_w = df_all_w.sort_values(['week', 'diem_kpi'], ascending=[True, False]).reset_index(drop=True)
            for cw in cache_w_paths:
                try:
                    os.makedirs(os.path.dirname(cw), exist_ok=True)
                    df_all_w.to_parquet(cw, index=False)
                except Exception:
                    pass
        else:
            for cw in cache_w_paths:
                if os.path.exists(cw):
                    try:
                        df_all_w = pd.read_parquet(cw)
                        break
                    except Exception:
                        pass

        if not df_all_m.empty:
            df_all_m = df_all_m.sort_values(['month_label', 'diem_kpi'], ascending=[True, False]).reset_index(drop=True)
            for cm in cache_m_paths:
                try:
                    os.makedirs(os.path.dirname(cm), exist_ok=True)
                    df_all_m.to_parquet(cm, index=False)
                except Exception:
                    pass
        else:
            for cm in cache_m_paths:
                if os.path.exists(cm):
                    try:
                        df_all_m = pd.read_parquet(cm)
                        break
                    except Exception:
                        pass

        return {'weekly': df_all_w, 'monthly': df_all_m}

    def load_kpi_chart_data(self, sheet_name: str) -> pd.DataFrame:
        """
        Đọc dữ liệu so sánh 3 ca theo ngày từ sheet 'chart capacity' hoặc tạo động từ 'Data KPI'.
        Hỗ trợ: 'Chart moisture', 'Chart dien', 'Chart capacity'
        """
        s_lower = sheet_name.strip().lower()
        if 'cap' in s_lower:
            for s_try in ['chart capacity', 'Chart capacity', sheet_name]:
                rows = self.get_kpi_sheet_values(s_try)
                if rows and len(rows) >= 3:
                    records = []
                    for r in rows[2:]:
                        if not r or not str(r[0]).strip():
                            continue
                        date_dt = parse_vn_date(r[0])
                        if not date_dt:
                            continue
                        val_a = clean_number(r[1]) if len(r) > 1 and str(r[1]).strip() not in ['', '-'] else None
                        val_b = clean_number(r[2]) if len(r) > 2 and str(r[2]).strip() not in ['', '-'] else None
                        val_c = clean_number(r[3]) if len(r) > 3 and str(r[3]).strip() not in ['', '-'] else None
                        item = {
                            'date': date_dt,
                            'date_str': date_dt.strftime('%d/%m/%Y'),
                            'Ca A': val_a,
                            'Ca B': val_b,
                            'Ca C': val_c,
                            'Long': val_c,
                            'Sắc': val_b,
                            'Tài': val_c,
                        }
                        if any(v is not None for v in [val_a, val_b, val_c]):
                            records.append(item)
                    if records:
                        df = pd.DataFrame(records)
                        return df.sort_values('date').reset_index(drop=True)

        # 2. Tạo động từ Data KPI
        df_shifts = self.load_kpi_daily_shifts()
        if df_shifts.empty:
            return pd.DataFrame()

        metric_col = 'nang_suat_tb'
        tieu_chuan = 4.0
        if 'moist' in s_lower or 'ẩm' in s_lower:
            metric_col = 'do_am_tb'
            tieu_chuan = 9.0
        elif 'dien' in s_lower or 'điện' in s_lower:
            metric_col = 'dien_tb'
            tieu_chuan = 175.0

        records = []
        for dt_val, group in df_shifts.groupby('date'):
            item = {
                'date': dt_val,
                'date_str': dt_val.strftime('%d/%m/%Y'),
                'Ca A': None,
                'Ca B': None,
                'Ca C': None,
                'Long': None,
                'Sắc': None,
                'Tài': None,
                'Tieu_chuan': tieu_chuan
            }
            vals = []
            for _, row in group.iterrows():
                ca = str(row.get('ca_truong', '')).strip()
                val = float(row.get(metric_col, 0.0))
                if val > 0:
                    vals.append(val)
                    if 'ca a' in ca.lower() or 'thành' in ca.lower():
                        item['Ca A'] = val
                    elif 'ca b' in ca.lower() or 'lâm' in ca.lower() or 'sắc' in ca.lower():
                        item['Ca B'] = val
                        item['Sắc'] = val
                    elif 'ca c' in ca.lower() or 'long' in ca.lower() or 'tài' in ca.lower():
                        item['Ca C'] = val
                        item['Long'] = val
                        item['Tài'] = val
            if vals:
                item['Trung_binh'] = round(sum(vals) / len(vals), 2)
            if any(item[k] is not None for k in ['Ca A', 'Ca B', 'Ca C', 'Long', 'Sắc', 'Tài']):
                records.append(item)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_kpi_sl_chart_data(self) -> pd.DataFrame:
        """
        Đọc/tạo dữ liệu so sánh sản lượng thực tế và chỉ tiêu của các ca theo ngày từ Data KPI.
        """
        df_shifts = self.load_kpi_daily_shifts()
        if df_shifts.empty:
            return pd.DataFrame()

        records = []
        for dt_val, group in df_shifts.groupby('date'):
            item = {
                'date': dt_val,
                'date_str': dt_val.strftime('%d/%m/%Y'),
                'Ca A_actual': None, 'Ca A_target': None,
                'Ca B_actual': None, 'Ca B_target': None,
                'Ca C_actual': None, 'Ca C_target': None,
                'Long_actual': None, 'Long_target': None,
                'Sac_actual': None, 'Sac_target': None,
                'Tai_actual': None, 'Tai_target': None,
            }
            for _, row in group.iterrows():
                ca = str(row.get('ca_truong', '')).strip().lower()
                act = float(row.get('sl_thuc_te', 0.0))
                tgt = float(row.get('chi_tieu_sl', 0.0))
                if act > 0 or tgt > 0:
                    if 'ca a' in ca or 'thành' in ca:
                        item['Ca A_actual'] = act if act > 0 else None
                        item['Ca A_target'] = tgt if tgt > 0 else None
                    elif 'ca b' in ca or 'lâm' in ca or 'sắc' in ca:
                        item['Ca B_actual'] = act if act > 0 else None
                        item['Ca B_target'] = tgt if tgt > 0 else None
                        item['Sac_actual'] = act if act > 0 else None
                        item['Sac_target'] = tgt if tgt > 0 else None
                    elif 'ca c' in ca or 'long' in ca or 'tài' in ca:
                        item['Ca C_actual'] = act if act > 0 else None
                        item['Ca C_target'] = tgt if tgt > 0 else None
                        item['Long_actual'] = act if act > 0 else None
                        item['Long_target'] = tgt if tgt > 0 else None
                        item['Tai_actual'] = act if act > 0 else None
                        item['Tai_target'] = tgt if tgt > 0 else None

            if any(item[k] is not None for k in ['Ca A_actual', 'Ca B_actual', 'Ca C_actual', 'Long_actual', 'Sac_actual', 'Tai_actual']):
                records.append(item)

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        return df

    def load_kpi_daily_shifts(self, df_kcs: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Đọc dữ liệu nhật ký ca từ sheet 'Data KPI' (hoặc 'Data') của file KPI.
        Các cột gồm: Ngày, Tuần, Tháng, Ca Trưởng, Thành phẩm (tấn), Chỉ tiêu (tấn), Điện năng TB, Năng suất, Độ ẩm viên %.
        Tự động tính toán độ ẩm trung bình từ df_kcs theo công thức AVERAGEIFS nếu ô độ ẩm rỗng.
        """
        rows = self.get_kpi_sheet_values('Data KPI')
        if not rows or len(rows) < 2:
            rows = self.get_kpi_sheet_values('Data')
        if not rows or len(rows) < 2:
            return pd.DataFrame()

        # Nạp kcs nếu cần để đối soát tính độ ẩm
        if df_kcs is None or df_kcs.empty:
            try:
                df_kcs = self.load_kcs_data()
            except Exception:
                df_kcs = pd.DataFrame()

        records = []
        for r in rows[1:]:
            if not r or not str(r[0]).strip() or len(r) < 4:
                continue

            date_dt = parse_vn_date(r[0])
            if not date_dt:
                continue

            week_num = int(clean_number(r[1])) if len(r) > 1 else 0
            month_num = int(clean_number(r[2])) if len(r) > 2 else 0
            ca_truong = str(r[3]).strip() if len(r) > 3 else ''

            if ca_truong in ['Nghĩ', 'OFF', 'Nghỉ ca', ''] and (len(r) < 5 or clean_number(r[4]) == 0):
                continue

            sl_thuc_te = clean_number(r[4]) if len(r) > 4 else 0.0
            chi_tieu_sl = clean_number(r[5]) if len(r) > 5 else 0.0
            dien_tb = clean_number(r[6]) if len(r) > 6 else 0.0
            nang_suat_tb = clean_number(r[7]) if len(r) > 7 else 0.0
            do_am_tb = clean_number(r[8]) if len(r) > 8 else 0.0

            # Nếu độ ẩm trên Google Sheet rỗng hoặc = 0, áp dụng công thức AVERAGEIFS từ Data KCS
            if do_am_tb == 0.0 and df_kcs is not None and not df_kcs.empty and sl_thuc_te > 0:
                do_am_tb = self.compute_kcs_average_moisture(df_kcs, date_dt, ca_truong)

            records.append({
                'date': date_dt,
                'date_str': date_dt.strftime('%d/%m/%Y'),
                'week': week_num,
                'month': month_num,
                'ca_truong': ca_truong,
                'chi_tieu_sl': chi_tieu_sl,
                'sl_thuc_te': sl_thuc_te,
                'dien_tb': dien_tb,
                'nang_suat_tb': nang_suat_tb,
                'do_am_tb': do_am_tb,
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

    def load_organization_hr_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Nạp dữ liệu Sơ đồ cơ cấu tổ chức & Định biên nhân sự từ Google Sheets hoặc cache cục bộ:
        https://docs.google.com/spreadsheets/d/1enwVBuwwFK7k6r4i_xcg_7oJgckLaOfzNUkHPRZfY6s/edit?gid=987654321#gid=987654321
        Bao gồm:
        - Cây phân cấp tổ chức (Gốc Dữ liệu Sơ đồ khối - gid=987654321)
        - Định biên định lượng theo phòng ban & danh sách nhân sự (Định biên nhân sự - gid=1942073054)
        """
        local_cache_path = os.path.join(os.path.dirname(__file__), "assets", "cache_hr_organization.json")
        result: Dict[str, Any] = {
            'status': 'PENDING',
            'sheet_id': self.hr_spreadsheet_id,
            'sheet_url': f"https://docs.google.com/spreadsheets/d/{self.hr_spreadsheet_id}/edit?gid={DEFAULT_HR_GID}#gid={DEFAULT_HR_GID}",
            'service_email': 'bvn-reporter@boxwood-dynamo-508304-t4.iam.gserviceaccount.com',
            'title': 'Sơ Đồ Cơ Cấu Tổ Chức & Định Biên Nhân Sự BVN Quảng Bình',
            'gid_hierarchy': DEFAULT_HR_GID,
            'gid_roster': '1942073054',
            'total_summary': {
                'plan': 104, 'actual': 92, 'missing': 12, 'rate': '88,46%', 'rate_num': 88.46
            },
            'executive_leadership': [],
            'departments': [],
            'all_roster': [],
            'hierarchy_edges': [],
            'error_message': ''
        }

        # 1. Đọc từ cache cục bộ trước để làm khung dữ liệu chuẩn
        if os.path.exists(local_cache_path):
            try:
                with open(local_cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    if isinstance(cached_data, dict):
                        result.update(cached_data)
                        result['status'] = 'LOCAL_CACHE'
            except Exception as e:
                result['error_message'] = f"Lỗi đọc cache: {e}"

        if force_reload:
            self.hr_spreadsheet = None

        if not self.client:
            self.connect()

        if not self.client:
            if result['status'] == 'PENDING':
                result['status'] = 'NO_CLIENT'
                result['error_message'] = 'Chưa kết nối được Google Sheets API'
            return result

        # 2. Thử truy vấn dữ liệu trực tiếp từ Google Sheets API
        try:
            if not self.hr_spreadsheet:
                self.hr_spreadsheet = self.client.open_by_key(self.hr_spreadsheet_id)

            if self.hr_spreadsheet:
                result['title'] = self.hr_spreadsheet.title
                result['status'] = 'CONNECTED'
        except Exception as e:
            err_str = str(e)
            is_perm = ('403' in err_str or 'Permission' in err_str or 'The caller does not have permission' in err_str)
            if result['status'] != 'LOCAL_CACHE':
                result['status'] = 'PERMISSION_DENIED' if is_perm else 'ERROR'
            result['error_message'] = err_str

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
            # Ưu tiên ghi vào sheet mới 'Product_Data', nếu không có thì ghi 'Product'
            try:
                ws = self.spreadsheet.worksheet('Product_Data')
            except Exception:
                ws = self.spreadsheet.worksheet('Product')
            vals = ws.get_all_values()

            date_dt = record.get('date')
            if isinstance(date_dt, str):
                date_dt = parse_vn_date(date_dt)
            if not date_dt:
                date_dt = datetime.now()

            d_iso = date_dt.strftime('%Y-%m-%d')
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
            # 1. Tìm dòng có cùng ngày và khớp Ca Trưởng (hỗ trợ cả YYYY-MM-DD và DD/MM/YYYY)
            for idx, r in enumerate(vals):
                if r and (d_iso in r[0] or d_str in r[0] or d_short in r[0]):
                    r_leader = r[3].strip() if len(r) > 3 else ''
                    if r_leader == ca_truong:
                        target_row = idx + 1
                        break

            # 2. Nếu chưa tìm thấy, tìm dòng cùng ngày nhưng chưa có Ca Trưởng (dòng trống)
            if not target_row:
                for idx, r in enumerate(vals):
                    if r and (d_iso in r[0] or d_str in r[0] or d_short in r[0]):
                        r_leader = r[3].strip() if len(r) > 3 else ''
                        r_sl = r[10].strip() if len(r) > 10 else ''
                        if r_leader == '' and r_sl == '':
                            target_row = idx + 1
                            break

            date_col_val = d_iso if ws.title == 'Product_Data' else d_str
            if target_row:
                # Cập nhật dải ô D:AJ của dòng đã có sẵn
                ws.update(range_name=f"D{target_row}:AJ{target_row}", values=[row_vals], value_input_option='USER_ENTERED')
                msg = f"Đã cập nhật thành công dữ liệu ngày {d_str} cho Ca Trưởng {ca_truong} (Dòng {target_row}) trên Google Sheets '{ws.title}'!"
            else:
                # Nếu chưa có dòng nào của ngày này -> Thêm dòng mới
                full_row = [date_col_val, str(month_val), str(week_val)] + row_vals
                ws.append_row(full_row, value_input_option='USER_ENTERED')
                msg = f"Đã thêm mới thành công dữ liệu ngày {d_str} cho Ca Trưởng {ca_truong} vào Google Sheets '{ws.title}'!"

            # Nếu cả sheet Product cũ vẫn còn tồn tại, đồng bộ luôn để các công thức ở Daily/Weekly report không bị gián đoạn
            try:
                if ws.title == 'Product_Data':
                    ws_old = self.spreadsheet.worksheet('Product')
                    vals_old = ws_old.get_all_values()
                    target_old_row = None
                    for idx, r in enumerate(vals_old):
                        if r and (d_str in r[0] or d_short in r[0] or d_iso in r[0]):
                            r_l = r[3].strip() if len(r) > 3 else ''
                            if r_l == ca_truong:
                                target_old_row = idx + 1
                                break
                    if target_old_row:
                        ws_old.update(range_name=f"D{target_old_row}:AJ{target_old_row}", values=[row_vals], value_input_option='USER_ENTERED')
            except Exception:
                pass

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
        Ghi dữ liệu kết quả đo kiểm chất lượng KCS vào Google Sheets 'Data KCS' (file KPI) và 'KCS' (file sản xuất).
        Đồng thời đồng bộ bộ đệm cache_kcs.parquet.
        """
        if not self.client:
            self.connect()

        date_dt = record.get('date')
        if isinstance(date_dt, str):
            date_dt = parse_vn_date(date_dt)
        if not date_dt:
            date_dt = datetime.now()

        d_str = date_dt.strftime('%d/%m/%Y')
        week_val = date_dt.isocalendar()[1]
        month_val = date_dt.month

        saved_any = False
        msg_parts = []

        # 1. Ghi vào sheet 'Data KCS' trong file KPI
        if self.kpi_spreadsheet:
            try:
                ws_kpi = self.kpi_spreadsheet.worksheet('Data KCS')
                all_ids = ws_kpi.col_values(1)
                new_id = f"K{len(all_ids):03d}"
                row_data_kcs = [
                    new_id,                                                     # 0: ID
                    d_str,                                                      # 1: Ngày
                    str(week_val),                                              # 2: Tuần
                    str(month_val),                                             # 3: Tháng
                    str(record.get('time_sample', '08h')),                      # 4: Giờ
                    str(record.get('shift_leader', '')),                        # 5: Trưởng ca
                    str(record.get('tester', 'QC')),                            # 6: Người đo
                    str(record.get('ty_le_nl_dot', '100% Củi')),                # 7: Tỷ lệ NL đốt
                    str(record.get('ty_le_phoi_tron', '8:2')),                  # 8: Tỷ lệ phối trộn
                    str(record.get('am_dam_pct', '')).replace('.', ','),        # 9: Ẩm dăm (%)
                    str(record.get('am_truoc_say_pct', '')).replace('.', ','),  # 10: Ẩm trước sấy (%)
                    str(record.get('am_sau_say_1_pct', '')).replace('.', ','),  # 11: Ẩm sau sấy 1 (%)
                    str(record.get('am_sau_say_2_pct', '')).replace('.', ','),  # 12: Ẩm sau sấy 2 (%)
                    str(record.get('am_vien_pct', '')).replace('.', ','),       # 13: Ẩm viên (%)
                    str(record.get('density_dam', '')).replace('.', ','),       # 14: Tỷ trọng dăm
                    str(record.get('density_nghien_tho', '')).replace('.', ','),# 15: Tỷ trọng nghiền thô
                    str(record.get('density_nghien_tinh', '')).replace('.', ','),# 16: Tỷ trọng nghiền tinh
                    str(record.get('density_vien', '')).replace('.', ','),      # 17: Tỷ trọng viên
                    str(record.get('temp_cooling', '30')).replace('.', ','),    # 18: Nhiệt độ sau làm nguội
                    str(record.get('luoi_nghien_tho', '14')),                   # 19: Lưới thô
                    str(record.get('luoi_nghien_tinh', '6')),                   # 20: Lưới tinh
                    str(record.get('duong_kinh_vien', '')).replace('.', ','),   # 21: Đường kính viên
                    str(record.get('chieu_dai_vien', '10-30')),                 # 22: Chiều dài viên
                    str(record.get('do_tro_pct', '')).replace('.', ',')         # 23: Độ tro viên (%)
                ]
                ws_kpi.append_row(row_data_kcs, value_input_option='USER_ENTERED')
                saved_any = True
                msg_parts.append("Data KCS")
            except Exception as e_kpi:
                print(f"[-] Lỗi ghi sheet Data KCS: {e_kpi}")

        # 2. Đồng bộ sheet 'KCS' trong file sản xuất nếu có
        if self.spreadsheet:
            try:
                ws_prod = self.spreadsheet.worksheet('KCS')
                row_prod = [
                    d_str, str(week_val),
                    str(record.get('time_sample', '08h')),
                    str(record.get('shift_leader', '')),
                    str(record.get('tester', 'KCS')),
                    str(record.get('ty_le_nl_dot', '100% Củi')),
                    str(record.get('ty_le_phoi_tron', '8:2')),
                    str(record.get('am_dam_pct', '')).replace('.', ','),
                    str(record.get('am_truoc_say_pct', '')).replace('.', ','),
                    str(record.get('am_sau_say_1_pct', '')).replace('.', ','),
                    str(record.get('am_sau_say_2_pct', '')).replace('.', ','),
                    str(record.get('am_vien_pct', '')).replace('.', ','),
                    str(record.get('density_dam', '')).replace('.', ','),
                    str(record.get('density_nghien_tho', '')).replace('.', ','),
                    str(record.get('density_nghien_tinh', '')).replace('.', ','),
                    str(record.get('density_vien', '')).replace('.', ','),
                    "", "", "", "", "",
                    str(record.get('do_tro_pct', '')).replace('.', ',')
                ]
                ws_prod.append_row(row_prod, value_input_option='USER_ENTERED')
                saved_any = True
                msg_parts.append("KCS (Sản xuất)")
            except Exception as e_prod:
                print(f"[-] Lỗi ghi sheet KCS sản xuất: {e_prod}")

        # 3. Đồng bộ cache_kcs.parquet cục bộ
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_kcs.parquet"),
            os.path.join("assets", "cache_kcs.parquet"),
            os.path.join("deploy_files", "assets", "cache_kcs.parquet"),
        ]
        try:
            new_kcs_dict = {
                'id': f"K{int(time.time())%1000:03d}",
                'date': pd.to_datetime(date_dt),
                'date_str': d_str,
                'week': week_val,
                'month': month_val,
                'time_sample': str(record.get('time_sample', '08h')),
                'shift_leader': str(record.get('shift_leader', '')),
                'tester': str(record.get('tester', 'QC')),
                'ty_le_nl_dot': str(record.get('ty_le_nl_dot', '100% Củi')),
                'ty_le_phoi_tron': str(record.get('ty_le_phoi_tron', '8:2')),
                'am_dam_pct': clean_number(record.get('am_dam_pct', 0)),
                'am_truoc_say_pct': clean_number(record.get('am_truoc_say_pct', 0)),
                'am_sau_say_1_pct': clean_number(record.get('am_sau_say_1_pct', 0)),
                'am_sau_say_2_pct': clean_number(record.get('am_sau_say_2_pct', 0)),
                'am_vien_pct': clean_number(record.get('am_vien_pct', 0)),
                'density_dam': clean_number(record.get('density_dam', 0)),
                'density_nghien_tho': clean_number(record.get('density_nghien_tho', 0)),
                'density_nghien_tinh': clean_number(record.get('density_nghien_tinh', 0)),
                'density_vien': clean_number(record.get('density_vien', 0)),
                'temp_cooling': clean_number(record.get('temp_cooling', 30)),
                'luoi_nghien_tho': str(record.get('luoi_nghien_tho', '14')),
                'luoi_nghien_tinh': str(record.get('luoi_nghien_tinh', '6')),
                'duong_kinh_vien': clean_number(record.get('duong_kinh_vien', 0)),
                'chieu_dai_vien': str(record.get('chieu_dai_vien', '10-30')),
                'do_tro_pct': clean_number(record.get('do_tro_pct', 0)),
            }
            for cp in cache_paths:
                if os.path.exists(cp):
                    df_c = pd.read_parquet(cp)
                    df_c = pd.concat([df_c, pd.DataFrame([new_kcs_dict])], ignore_index=True)
                    df_c = df_c.sort_values('date').reset_index(drop=True)
                    df_c.to_parquet(cp, index=False)
        except Exception as e_c:
            print(f"[-] Lỗi cập nhật cache KCS parquet: {e_c}")

        if saved_any:
            return True, f"Đã lưu thành công mẫu kiểm nghiệm KCS lúc {record.get('time_sample')} ngày {d_str} vào {', '.join(msg_parts)}!"
        return False, "Không thể kết nối để ghi dữ liệu KCS."

    def load_oil_change_data(self) -> Dict[str, Any]:
        """
        Nạp dữ liệu Lịch thay nhớt hộp số máy ép PE1 - PE8 (Mobil Glygoyle 460).
        Sử dụng values_batch_get để đọc toàn bộ 8 máy và danh mục trong 1 request API duy nhất,
        tránh lỗi 429 quota và tăng tốc độ tải trang tối đa.
        Trả về:
          - 'summary': DataFrame tổng hợp 8 máy ép
          - 'details': Dict[str, DataFrame] chi tiết 10 chu kỳ của từng máy PE1-PE8
          - 'title': Tên bảng tính
        """
        cache_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "cache_oil_summary.parquet"),
            os.path.join("assets", "cache_oil_summary.parquet"),
            os.path.join("deploy_files", "assets", "cache_oil_summary.parquet")
        ]

        if not self.oil_spreadsheet:
            self.connect()

        if not self.oil_spreadsheet:
            # Nếu mất kết nối, nạp từ cache parquet dự phòng
            for cp in cache_paths:
                if os.path.exists(cp):
                    try:
                        df_cached = pd.read_parquet(cp)
                        if not df_cached.empty:
                            return {'summary': df_cached, 'details': {}, 'title': "Lịch thay nhớt hộp số máy ép (Cache)"}
                    except Exception:
                        pass
            return {'summary': pd.DataFrame(), 'details': {}, 'title': "Lịch thay nhớt hộp số máy ép"}

        title = getattr(self.oil_spreadsheet, "title", "Lịch thay nhớt hộp số máy ép")
        pe_list = [f"PE{i}" for i in range(1, 9)]
        ranges = ["'Danh muc'!A1:H10"] + [f"'{pe}'!A1:M15" for pe in pe_list]

        try:
            batch_res = self.oil_spreadsheet.values_batch_get(ranges)
            vrs = batch_res.get('valueRanges', [])
        except Exception as e:
            print(f"[-] Lỗi batch get dữ liệu thay nhớt: {e}")
            for cp in cache_paths:
                if os.path.exists(cp):
                    try:
                        df_cached = pd.read_parquet(cp)
                        if not df_cached.empty:
                            return {'summary': df_cached, 'details': {}, 'title': f"{title} (Cache)"}
                    except Exception:
                        pass
            return {'summary': pd.DataFrame(), 'details': {}, 'title': title}

        dm_vals = vrs[0].get('values', []) if len(vrs) > 0 else []
        df_dm = pd.DataFrame(dm_vals[1:], columns=dm_vals[0]) if len(dm_vals) > 1 else pd.DataFrame()

        summary_rows = []
        details = {}

        for idx, pe in enumerate(pe_list):
            vr_vals = vrs[idx + 1].get('values', []) if len(vrs) > idx + 1 else []
            records = []
            if len(vr_vals) > 1:
                headers = [c.strip() for c in vr_vals[0]]
                for r in vr_vals[1:]:
                    rec = {headers[k]: (r[k].strip() if k < len(r) else '') for k in range(len(headers))}
                    records.append(rec)
                df_pe = pd.DataFrame(records)
            else:
                df_pe = pd.DataFrame()
            details[pe] = df_pe

            row1 = records[0] if len(records) > 0 else {}
            row2 = records[1] if len(records) > 1 else {}

            h1_str = str(row1.get('So h', row1.get('So h hoạt dọng', '0'))).strip()
            h2_str = str(row2.get('So h', row2.get('So h hoạt dọng', '0'))).strip()
            dinh_muc_str = str(row1.get('Dinh muc (h)', row1.get('Dinh muc', '4000'))).strip()

            m_name = f"Máy ép viên Andritz PM30-{5+idx+1}"
            if not df_dm.empty and 'Ma may' in df_dm.columns and 'Ten' in df_dm.columns:
                m_match = df_dm.loc[df_dm['Ma may'] == pe, 'Ten']
                if len(m_match) > 0:
                    m_name = str(m_match.values[0])

            std_h = clean_number(dinh_muc_str) if clean_number(dinh_muc_str) > 0 else 4000.0
            h1_num = clean_number(h1_str)
            h2_num = clean_number(h2_str)

            alert_c2 = str(row2.get('Trạng thái nhắc nhở', '')).strip()
            if not alert_c2:
                if h2_num >= std_h:
                    alert_c2 = 'Cần thay nhớt'
                elif h2_num >= std_h * 0.95:
                    alert_c2 = 'Sắp đến hạn (≥95%)'
                else:
                    alert_c2 = 'Bình thường'

            summary_rows.append({
                'machine_code': pe,
                'machine_name': m_name,
                'oil_type': 'Mobil Glygoyle 460',
                'oil_capacity_l': 208,
                'standard_hours': std_h,
                'run_hours_c1': h1_num,
                'change_date_c1': str(row1.get('Ngày thay nhớt', '18/09/2026')),
                'change_status_c1': str(row1.get('Trạng thái thay nhớt', 'Đã thay')),
                'run_hours_c2': h2_num,
                'alert_status_c2': alert_c2
            })

        df_summary = pd.DataFrame(summary_rows)

        # Lưu cache parquet dự phòng
        if not df_summary.empty:
            for cp in cache_paths:
                try:
                    os.makedirs(os.path.dirname(cp), exist_ok=True)
                    df_summary.to_parquet(cp, index=False)
                except Exception:
                    pass

        return {
            'summary': df_summary,
            'details': details,
            'title': title
        }






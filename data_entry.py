"""
Mô-đun Quản Lý Nhập Số Liệu Sản Xuất, KCS, Bảo Trì & Chipper
Hỗ trợ:
1. Phân quyền và xác thực bằng Mã PIN theo các bộ phận:
   - Tab Sản xuất: Ca A, Ca B, Ca C, QĐ (Quản Đốc)
   - Tab KCS: QC (KCS)
   - Tab Bảo trì: Bảo trì
   - Tab Chipper: QL tổ băm, Tổ băm 1, Tổ băm 2
2. Form nhập số liệu ca sản xuất (Sản lượng, điện năng, giờ máy chạy 8 máy ép, nghiền, sấy, dăm đốt).
3. Form nhập kết quả đo kiểm chất lượng KCS (Độ ẩm dăm, sau sấy, ẩm viên, tỷ trọng, độ tro).
4. Form nhập nhật ký bảo trì thiết bị (Cụm máy ép, nghiền, sấy, chipper, mã khuôn/phụ tùng, thời gian dừng, trạng thái).
5. Form nhập vận hành tổ băm Chipper (Gỗ cây vào, dăm băm ra, giờ chạy Line 1 & Line 2, điện/dầu, kiểm tra dao & bẫy đá).
6. Tính toán thời gian thực các chỉ số KPI và ghi tự động vào Google Sheets.
"""

import os
import json
from datetime import datetime, date, time
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from i18n import t, get_lang, is_en, apply_language_change, get_op_tasks

# File lưu trữ mã PIN tùy chỉnh (nếu có)
PIN_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "assets", "user_pins.json")

# Danh sách người dùng mặc định và mã PIN khởi tạo theo đúng phân quyền yêu cầu
DEFAULT_USERS = {
    # 0. Ban Giám Đốc
    "director": {
        "id": "director",
        "name": "Vũ Quang Sáng",
        "shift_code": "GĐ",
        "full_name": "Giám Đốc (GĐ - Vũ Quang Sáng)",
        "role": "director",
        "pin": "6868",
        "icon": "🎖️"
    },
    "pgd": {
        "id": "pgd",
        "name": "Đỗ Công Thịnh",
        "shift_code": "PGĐ",
        "full_name": "Phó Giám Đốc (PGĐ - Đỗ Công Thịnh - Admin)",
        "role": "admin",
        "pin": "9999",
        "icon": "👑"
    },
    # 1. Khối Sản Xuất
    "manager": {
        "id": "manager",
        "name": "Nguyễn Đăng Thành",
        "shift_code": "QĐ",
        "full_name": "Quản Đốc (QĐ - Nguyễn Đăng Thành)",
        "role": "manager",
        "pin": "7777",
        "icon": "⭐"
    },
    "sac": {
        "id": "sac",
        "name": "Lê Chiến Sắc",
        "shift_code": "Ca A",
        "full_name": "Ca Trưởng Lê Chiến Sắc (Ca A)",
        "role": "ca_a",
        "pin": "1111",
        "icon": "🟢"
    },
    "tai": {
        "id": "tai",
        "name": "Hoàng Phúc Tài",
        "shift_code": "Ca B",
        "full_name": "Ca Trưởng Hoàng Phúc Tài (Ca B)",
        "role": "ca_b",
        "pin": "2222",
        "icon": "🟠"
    },
    "long": {
        "id": "long",
        "name": "Nguyễn Long",
        "shift_code": "Ca C",
        "full_name": "Ca Trưởng Nguyễn Long (Ca C)",
        "role": "ca_c",
        "pin": "3333",
        "icon": "🔵"
    },
    # 2. Khối Kiểm Định Chất Lượng KCS
    "kcs": {
        "id": "kcs",
        "name": "Kim Dung",
        "shift_code": "QC",
        "full_name": "KCS / QC (Kim Dung)",
        "role": "qc",
        "pin": "8888",
        "icon": "🔬"
    },
    # 3. Khối Bảo Trì - Cơ Điện
    "baotri": {
        "id": "baotri",
        "name": "Phan Nhớ",
        "shift_code": "Bảo trì",
        "full_name": "Tổ Trưởng Cơ Khí (Phan Nhớ - Bảo Trì)",
        "role": "bao_tri",
        "pin": "4444",
        "icon": "🔧"
    },
    # 4. Khối Phân Xưởng Băm Dăm (Chipper)
    "ql_tobam": {
        "id": "ql_tobam",
        "name": "Phạm Văn Cường",
        "shift_code": "QL tổ băm",
        "full_name": "QL Tổ Băm (Phạm Văn Cường)",
        "role": "ql_tobam",
        "pin": "5555",
        "icon": "🪵"
    },
    "tobam1": {
        "id": "tobam1",
        "name": "Trần Văn Quảng",
        "shift_code": "Tổ băm 1",
        "full_name": "Tổ Băm 1 (Trần Văn Quảng)",
        "role": "tobam1",
        "pin": "5111",
        "icon": "🪓"
    },
    "tobam2": {
        "id": "tobam2",
        "name": "Trần Mạnh Hà",
        "shift_code": "Tổ băm 2",
        "full_name": "Tổ Băm 2 (Trần Mạnh Hà)",
        "role": "tobam2",
        "pin": "5222",
        "icon": "🪓"
    }
}

# Cấu hình phân quyền truy cập chi tiết cho từng tab
TAB_PERMISSIONS = {
    "san_xuat": {
        "title": "Sản Xuất",
        "allowed_ids": ["sac", "tai", "long", "manager", "director", "pgd"],
        "allowed_labels": "GĐ, PGĐ, QĐ, Ca A, Ca B, Ca C"
    },
    "kcs": {
        "title": "KCS",
        "allowed_ids": ["kcs", "manager", "director", "pgd"],
        "allowed_labels": "GĐ, PGĐ, QĐ, QC (Kim Dung)"
    },
    "bao_tri": {
        "title": "Bảo Trì",
        "allowed_ids": ["baotri", "manager", "director", "pgd"],
        "allowed_labels": "GĐ, PGĐ, QĐ, Bảo Trì (Phan Nhớ)"
    },
    "chipper": {
        "title": "Chipper",
        "allowed_ids": ["ql_tobam", "tobam1", "tobam2", "manager", "director", "pgd"],
        "allowed_labels": "GĐ, PGĐ, QĐ, QL tổ băm, Tổ băm 1, Tổ băm 2"
    }
}


def check_tab_permission(user_id: str, tab_key: str) -> bool:
    """Kiểm tra tài khoản có quyền truy cập tab hay không (Giám Đốc, PGĐ & Quản Đốc có toàn quyền)"""
    if user_id in ["manager", "director", "pgd", "admin"]:
        return True
    perm = TAB_PERMISSIONS.get(tab_key, {})
    return user_id in perm.get("allowed_ids", [])


def render_permission_denied_card(tab_title: str, tab_key: str, current_user: Dict[str, Any]):
    """Hiển thị thông báo khi người dùng không có quyền truy cập tab"""
    perm = TAB_PERMISSIONS.get(tab_key, {})
    allowed_str = perm.get("allowed_labels", "")
    st.markdown(f"""
    <div style="background: rgba(239, 68, 68, 0.08); border: 1.5px dashed #ef4444; border-radius: 12px; padding: 28px 20px; text-align: center; margin: 20px auto; max-width: 680px;">
        <div style="font-size: 40px; margin-bottom: 8px;">🔒</div>
        <div style="font-size: 18px; font-weight: 800; color: #f87171; text-transform: uppercase;">
            BẠN KHÔNG CÓ QUYỀN TRUY CẬP TAB {tab_title.upper()}
        </div>
        <div style="font-size: 13.5px; color: #94a3b8; margin-top: 10px; line-height: 1.6;">
            Tab <b>{tab_title}</b> chỉ được phân quyền cho: <span style="color: #38bdf8; font-weight: 700;">{allowed_str}</span>.<br>
            Bạn đang đăng nhập với tư cách: <span style="color: #f8fafc; font-weight: 700;">{current_user.get('full_name')}</span> (<span style="color: #fbbf24; font-weight: 700;">{current_user.get('shift_code')}</span>).
        </div>
        <div style="font-size: 12px; color: #64748b; margin-top: 14px;">
            💡 Nếu cần nhập số liệu cho tab này, vui lòng nhấn nút <b>"🚪 Đăng Xuất"</b> ở trên và đăng nhập bằng tài khoản được phân quyền tương ứng.
        </div>
    </div>
    """, unsafe_allow_html=True)


def load_user_pins() -> Dict[str, Dict[str, Any]]:
    """Đọc cấu hình mã PIN từ file hoặc sử dụng mặc định"""
    users = DEFAULT_USERS.copy()
    if os.path.exists(PIN_CONFIG_FILE):
        try:
            with open(PIN_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for uid, data in saved.items():
                    if uid in users:
                        users[uid]["pin"] = str(data.get("pin", users[uid]["pin"]))
        except Exception:
            pass
    return users


def save_user_pin(user_id: str, new_pin: str) -> bool:
    """Cập nhật mã PIN mới cho người dùng"""
    users = load_user_pins()
    if user_id in users:
        users[user_id]["pin"] = str(new_pin)
        try:
            os.makedirs(os.path.dirname(PIN_CONFIG_FILE), exist_ok=True)
            with open(PIN_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """Lấy thông tin người dùng đang đăng nhập trong phiên làm việc"""
    return st.session_state.get("authenticated_user", None)


def logout_user():
    """Đăng xuất người dùng hiện tại và khóa lại hệ thống"""
    if "authenticated_user" in st.session_state:
        del st.session_state["authenticated_user"]
    if "viewer_authorized_email" in st.session_state:
        del st.session_state["viewer_authorized_email"]
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.rerun()


def render_login_box(key_prefix: str = "main_login"):
    """Hiển thị hộp đăng nhập mã PIN cho tất cả các bộ phận được phân quyền"""
    users = load_user_pins()
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 24px; max-width: 620px; margin: 20px auto; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
        <div style="text-align: center; margin-bottom: 16px;">
            <div style="font-size: 38px; margin-bottom: 8px;">🔐</div>
            <div style="font-size: 20px; font-weight: 800; color: #f8fafc;">XÁC THỰC QUYỀN NHẬP SỐ LIỆU</div>
            <div style="font-size: 13px; color: #94a3b8; margin-top: 4px; line-height: 1.5;">
                Hệ thống hỗ trợ phân quyền theo vai trò:<br>
                • <b>Ban GĐ:</b> Giám Đốc (GĐ), PGĐ (Admin) | • <b>Quản Đốc & Sản xuất:</b> QĐ, Ca A, Ca B, Ca C<br>
                • <b>KCS:</b> QC (Kim Dung) | • <b>Bảo trì:</b> Phan Nhớ | • <b>Chipper:</b> QL tổ băm, Tổ băm 1, Tổ băm 2
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_box1, c_box2, c_box3 = st.columns([1, 2, 1])
    with c_box2:
        user_options = {u["full_name"]: uid for uid, u in users.items()}
        with st.form(f"{key_prefix}_login_form", clear_on_submit=False):
            selected_name = st.selectbox("👤 Chọn Danh Tính Của Bạn:", list(user_options.keys()), key=f"{key_prefix}_sel_name")
            selected_uid = user_options[selected_name]

            input_pin = st.text_input("🔑 Nhập Mã PIN (4 số):", type="password", max_chars=6, placeholder="••••", key=f"{key_prefix}_pin")

            col_btn1, col_btn2 = st.columns([3, 2])
            with col_btn1:
                btn_login = st.form_submit_button("🔓 ĐĂNG NHẬP (Enter ↵)", type="primary", use_container_width=True, key=f"{key_prefix}_btn_submit")
            with col_btn2:
                st.caption("💡 Nhấn Enter ↵ để vào ngay")

        if btn_login:
            target_user = users[selected_uid]
            if input_pin == target_user["pin"]:
                st.session_state["authenticated_user"] = target_user
                st.success(f"✅ Đăng nhập thành công! Xin chào {target_user['full_name']}.")
                st.rerun()
            else:
                st.error("❌ Mã PIN không chính xác! Vui lòng liên hệ Quản lý / Quản trị viên để được cấp mã PIN.")


def render_data_entry_module(dl):
    """
    Hàm chính điều hướng giao diện Nhập Liệu Báo Cáo Sản Xuất & KCS
    """
    current_user = get_current_user()

    # Nếu chưa đăng nhập, hiển thị form xác thực PIN
    if current_user is None:
        render_login_box("entry_module_login")
        return

    # Thanh thông tin người dùng đang đăng nhập
    user_id = current_user.get("id", "")
    user_name = current_user.get("name", "Người dùng")
    user_role = current_user.get("role", "shift_leader")
    user_full = current_user.get("full_name", "")
    user_icon = current_user.get("icon", "👤")

    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 10px; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 16px; font-weight: 800; color: #10b981;">{user_icon} ĐANG ĐĂNG NHẬP: {user_full.upper()}</span>
                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Vị trí: {current_user.get('shift_code', '').upper()} • Hệ thống ghi nhận số liệu trực tiếp vào Google Sheets</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_hdr2:
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            logout_user()

    # Hiển thị thông báo thành công sau khi ghi dữ liệu và tự động rerun
    if 'flash_success_msg' in st.session_state:
        f_msg = st.session_state.pop('flash_success_msg')
        st.success(f_msg)
        st.toast(f_msg, icon="✅")

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    # 4 TAB NGHIỆP VỤ + 1 TAB ĐỔI PIN
    tab_list = [
        "🏭 Sản Xuất",
        "🔬 KCS",
        "🔧 Bảo Trì",
        "🪵 Chipper",
        "⚙️ Đổi Mã PIN"
    ]

    active_entry_tab = st.tabs(tab_list)

    # 1. TAB SẢN XUẤT (Phân quyền: Ca A, Ca B, Ca C, QĐ)
    with active_entry_tab[0]:
        if check_tab_permission(user_id, "san_xuat"):
            render_shift_production_form(dl, current_user)
        else:
            render_permission_denied_card("Sản Xuất", "san_xuat", current_user)

    # 2. TAB KCS (Phân quyền: QC)
    with active_entry_tab[1]:
        if check_tab_permission(user_id, "kcs"):
            render_kcs_entry_form(dl, current_user)
        else:
            render_permission_denied_card("KCS", "kcs", current_user)

    # 3. TAB BẢO TRÌ (Phân quyền: Bảo trì)
    with active_entry_tab[2]:
        if check_tab_permission(user_id, "bao_tri"):
            render_maintenance_entry_form(dl, current_user)
        else:
            render_permission_denied_card("Bảo Trì", "bao_tri", current_user)

    # 4. TAB CHIPPER (Phân quyền: QL tổ băm, Tổ băm 1, Tổ băm 2)
    with active_entry_tab[3]:
        if check_tab_permission(user_id, "chipper"):
            render_chipper_entry_form(dl, current_user)
        else:
            render_permission_denied_card("Chipper", "chipper", current_user)

    # 5. TAB ĐỔI MÃ PIN
    with active_entry_tab[4]:
        render_change_pin_form(current_user)


def render_shift_production_form(dl, current_user: Dict[str, Any]):
    """Form nhập báo cáo sản xuất ca dành cho Ca Trưởng & Quản Đốc"""
    st.markdown("#### 📝 NHẬP BÁO CÁO KẾT QUẢ SẢN XUẤT CA")
    st.caption("Số liệu nhập tại đây sẽ được tự động đồng bộ lên Google Sheets (Sheet `Product_Data`) và làm mới Dashboard tức thì.")

    # Lấy ngày mặc định từ bộ lọc ngày đầu trang nếu có
    default_d = st.session_state.get('top_target_date', date.today())
    if hasattr(default_d, 'date'):
        default_d = default_d.date()

    with st.form("form_shift_entry", clear_on_submit=False):
        # 1. Thông tin chung
        st.markdown("##### 1️⃣ Thông Tin Thời Gian & Phân Ca")
        c_i1, c_i2, c_i3 = st.columns(3)
        with c_i1:
            report_date = st.date_input("📅 Ngày sản xuất:", value=default_d)
        with c_i2:
            shift_choice = st.selectbox("⏰ Ca làm việc:", ["Ca 1 (06h - 14h)", "Ca 2 (14h - 22h)", "Ca 3 (22h - 06h)"])
        with c_i3:
            # Nếu là Quản đốc / Giám đốc / Admin thì cho chọn ca trưởng, nếu là Ca trưởng thì mặc định cố định tên
            if current_user.get("role") in ["manager", "director", "admin"]:
                shift_leader_input = st.selectbox("👤 Ca Trưởng / Phân ca:", ["Ca A (Lê Chiến Sắc)", "Ca B (Hoàng Phúc Tài)", "Ca C (Nguyễn Long)", "BT-VS (Bảo trì - Phan Nhớ)", "OFF (Nghỉ ca)", "XH (Xuất Hàng)"])
            else:
                shift_leader_input = current_user.get("full_name", current_user.get("name", "Ca A (Lê Chiến Sắc)"))
                st.text_input("👤 Ca Trưởng phụ trách:", value=shift_leader_input, disabled=True)

        st.markdown("---")

        # 2. Sản lượng và Điện năng
        st.markdown("##### 2️⃣ Sản Lượng & Tiêu Hao Điện Năng")
        c_s1, c_s2, c_s3 = st.columns(3)
        with c_s1:
            san_luong_val = st.number_input("📦 Sản lượng thực tế (tấn):", min_value=0.0, max_value=300.0, value=100.0, step=0.5, format="%.2f")
        with c_s2:
            chi_tieu_val = st.number_input("🎯 Chỉ tiêu giao ca (tấn):", min_value=0.0, max_value=300.0, value=90.0, step=1.0, format="%.1f")
        with c_s3:
            dien_val = st.number_input("⚡ Điện năng tiêu thụ (kWh):", min_value=0.0, max_value=100000.0, value=17500.0, step=100.0, format="%.0f")

        # Hiển thị tính toán trực quan ngay trên form
        suat_dien_calc = round(dien_val / san_luong_val, 1) if san_luong_val > 0 else 0.0
        if suat_dien_calc > 0:
            if suat_dien_calc <= 175:
                st.success(f"🟢 **Suất điện ước tính:** `{suat_dien_calc} kWh/tấn` (Đạt định mức ≤ 175 kWh/tấn)")
            else:
                st.warning(f"🔴 **Suất điện ước tính:** `{suat_dien_calc} kWh/tấn` (VƯỢT ĐỊNH MỨC +{round(suat_dien_calc - 175, 1)} kWh/tấn)")

        st.markdown("---")

        # 3. Giờ hoạt động các cụm máy (tối đa 8h/ca)
        st.markdown("##### 3️⃣ Giờ Hoạt Động Các Cụm Thiết Bị (Giờ / Ca)")
        
        st.markdown("**🔨 Cụm Nghiền Búa Thô:**")
        c_hm_t1, c_hm_t2, c_hm_t3 = st.columns(3)
        with c_hm_t1:
            h_hm118 = st.number_input("HM118 (Andritz - h):", min_value=0.0, max_value=8.0, value=6.0, step=0.5)
        with c_hm_t2:
            h_hm218 = st.number_input("HM218 (Andritz - h):", min_value=0.0, max_value=8.0, value=6.0, step=0.5)
        with c_hm_t3:
            h_hm318 = st.number_input("HM318 (SHT - h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)

        st.markdown("**🔥 Cụm Trống Sấy:**")
        c_dr1, c_dr2 = st.columns(2)
        with c_dr1:
            h_dr124 = st.number_input("Trống Sấy DR124 (h):", min_value=0.0, max_value=8.0, value=7.0, step=0.5)
        with c_dr2:
            h_dr224 = st.number_input("Trống Sấy DR224 (h):", min_value=0.0, max_value=8.0, value=6.0, step=0.5)

        st.markdown("**⚙️ Cụm Nghiền Búa Tinh:**")
        c_hm_f1, c_hm_f2, c_hm_f3 = st.columns(3)
        with c_hm_f1:
            h_hm147 = st.number_input("HM147 (SHT - h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
        with c_hm_f2:
            h_hm247 = st.number_input("HM247 (Andritz - h):", min_value=0.0, max_value=8.0, value=7.0, step=0.5)
        with c_hm_f3:
            h_hm347 = st.number_input("HM347 (Andritz - h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)

        st.markdown("**🏭 Cụm 8 Máy Ép Viên (PE1 - PE8):**")
        c_pe1, c_pe2, c_pe3, c_pe4 = st.columns(4)
        with c_pe1:
            h_pe1 = st.number_input("PE1 (h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
            h_pe5 = st.number_input("PE5 (h):", min_value=0.0, max_value=8.0, value=5.0, step=0.5)
        with c_pe2:
            h_pe2 = st.number_input("PE2 (h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
            h_pe6 = st.number_input("PE6 (h):", min_value=0.0, max_value=8.0, value=7.0, step=0.5)
        with c_pe3:
            h_pe3 = st.number_input("PE3 (h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
            h_pe7 = st.number_input("PE7 (h):", min_value=0.0, max_value=8.0, value=6.0, step=0.5)
        with c_pe4:
            h_pe4 = st.number_input("PE4 (h):", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
            h_pe8 = st.number_input("PE8 (h):", min_value=0.0, max_value=8.0, value=7.0, step=0.5)

        tong_gio_ep_calc = h_pe1 + h_pe2 + h_pe3 + h_pe4 + h_pe5 + h_pe6 + h_pe7 + h_pe8
        nang_suat_calc = round(san_luong_val / tong_gio_ep_calc, 2) if tong_gio_ep_calc > 0 else 0.0

        st.info(f"📊 **Tổng giờ chạy 8 máy ép:** `{tong_gio_ep_calc} giờ` | **Năng suất máy ép:** `{nang_suat_calc} tấn/giờ` (Định mức chuẩn: ≥ 4.0 tấn/h)")

        st.markdown("---")

        # 4. Nguyên liệu dăm
        st.markdown("##### 4️⃣ Dăm Đốt Lò & Dăm Nghiền")
        c_nl1, c_nl2, c_nl3, c_nl4 = st.columns(4)
        with c_nl1:
            nl_dot_spoon = st.number_input("Dăm đốt (Muỗng):", min_value=0, max_value=50, value=13, step=1)
        with c_nl2:
            nl_dot_tan = st.number_input("Dăm đốt (Tấn = muỗng x 1.4):", min_value=0.0, max_value=100.0, value=round(nl_dot_spoon * 1.4, 1), step=0.5)
        with c_nl3:
            nghien_spoon = st.number_input("Dăm nghiền (Muỗng):", min_value=0, max_value=300, value=105, step=1)
        with c_nl4:
            nghien_tan = st.number_input("Dăm nghiền (Tấn = muỗng x 1.8):", min_value=0.0, max_value=500.0, value=round(nghien_spoon * 1.8, 1), step=0.5)

        note_ca = st.text_area("📝 Ghi chú ca (Sự cố thiết bị, chất lượng nguyên liệu, lý do dừng máy nếu có):", placeholder="Ghi chú tóm tắt...")

        submitted = st.form_submit_button("🚀 GỬI BÁO CÁO CA LÊN HỆ THỐNG", type="primary", use_container_width=True)

    if submitted:
        # Kiểm tra tính hợp lệ
        is_off_or_maint = any(kw in shift_leader_input.lower() for kw in ['nghỉ', 'nghĩ', 'off', 'bảo trì', 'bao tri', 'bt'])
        if san_luong_val <= 0 and not is_off_or_maint:
            st.error("⚠️ Vui lòng kiểm tra lại: Sản lượng ca đang bằng 0!")
            return

        # Chuẩn hóa mã vị trí theo bảng danh mục:
        s_ldr_code = shift_leader_input
        if 'ca a' in shift_leader_input.lower() or 'sắc' in shift_leader_input.lower():
            s_ldr_code = 'Ca A'
        elif 'ca b' in shift_leader_input.lower() or 'tài' in shift_leader_input.lower():
            s_ldr_code = 'Ca B'
        elif 'ca c' in shift_leader_input.lower() or 'long' in shift_leader_input.lower():
            s_ldr_code = 'Ca C'
        elif 'bt' in shift_leader_input.lower() or 'bảo trì' in shift_leader_input.lower():
            s_ldr_code = 'BT_VS'
        elif 'off' in shift_leader_input.lower() or 'nghỉ' in shift_leader_input.lower() or 'nghĩ' in shift_leader_input.lower():
            s_ldr_code = 'OFF'
        elif 'xh' in shift_leader_input.lower() or 'xuất' in shift_leader_input.lower():
            s_ldr_code = 'XH'

        record_data = {
            'date': report_date,
            'shift_leader': s_ldr_code,
            'san_luong_tan': san_luong_val,
            'chi_tieu_tan': chi_tieu_val,
            'dien_kwh': dien_val,
            'nl_dot_spoon': nl_dot_spoon,
            'nl_dot_tan': nl_dot_tan,
            'nghien_tho_spoon': nghien_spoon,
            'nghien_tho_tan': nghien_tan,
            'h_HM118': h_hm118,
            'h_HM218': h_hm218,
            'h_HM318': h_hm318,
            'h_DR124': h_dr124,
            'h_DR224': h_dr224,
            'h_HM147': h_hm147,
            'h_HM247': h_hm247,
            'h_HM347': h_hm347,
            'h_PE1': h_pe1,
            'h_PE2': h_pe2,
            'h_PE3': h_pe3,
            'h_PE4': h_pe4,
            'h_PE5': h_pe5,
            'h_PE6': h_pe6,
            'h_PE7': h_pe7,
            'h_PE8': h_pe8,
        }

        with st.spinner("⏳ Đang đồng bộ số liệu lên Google Sheets và cập nhật hệ thống..."):
            success, message = dl.save_shift_record(record_data)

        if success:
            st.session_state['flash_success_msg'] = f"🎉 **{message}**"
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ {message}")

    # ================= CHỨC NĂNG XÓA BÁO CÁO CA SẢN XUẤT =================
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
    with st.expander("🗑️ Xóa Báo Cáo Ca Sản Xuất (Delete Shift Record)", expanded=False):
        st.warning(f"⚠️ Chức năng này sẽ tìm và xóa vĩnh viễn dòng báo cáo của **{shift_leader_input}** trong ngày **{report_date.strftime('%d/%m/%Y')}** trên Google Sheets.")
        chk_confirm_delete = st.checkbox("Tôi xác nhận muốn xóa báo cáo ca này khỏi hệ thống", key="chk_confirm_delete_shift")
        if st.button("🗑️ XÁC NHẬN XÓA BÁO CÁO KHỎI GOOGLE SHEETS", type="secondary", disabled=not chk_confirm_delete, use_container_width=True, key="btn_del_shift_action"):
            with st.spinner("⏳ Đang xóa dữ liệu báo cáo trên Google Sheets..."):
                del_ok, del_msg = dl.delete_shift_record(report_date, shift_leader_input)
            if del_ok:
                st.session_state['flash_success_msg'] = f"🗑️ **{del_msg}**"
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"❌ {del_msg}")


def render_kcs_entry_form(dl, current_user: Dict[str, Any]):
    """Form nhập kết quả kiểm nghiệm KCS chất lượng độ ẩm & tỷ trọng"""
    st.markdown("#### 🔬 NHẬP KẾT QUẢ ĐO KIỂM CHẤT LƯỢNG KCS")
    st.caption("Dữ liệu đo độ ẩm nguyên liệu, sau sấy và viên nén thành phẩm sẽ được ghi vào sheet `KCS`.")

    # Lấy ngày mặc định từ bộ lọc ngày đầu trang nếu có
    default_d = st.session_state.get('top_target_date', date.today())
    if hasattr(default_d, 'date'):
        default_d = default_d.date()

    with st.form("form_kcs_entry", clear_on_submit=False):
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        with c_k1:
            kcs_date = st.date_input("📅 Ngày kiểm nghiệm:", value=default_d, key="kcs_in_date")
        with c_k2:
            time_sample = st.selectbox("⏰ Giờ lấy mẫu:", ["02h", "04h", "06h", "08h", "10h", "12h", "14h", "16h", "18h", "20h", "22h", "24h"])
        with c_k3:
            shift_leader_kcs = st.selectbox("👤 Ca Trưởng trực:", ["Ca A (Lê Chiến Sắc)", "Ca B (Hoàng Phúc Tài)", "Ca C (Nguyễn Long)"])
        with c_k4:
            tester_name = st.text_input("🧪 KTV kiểm tra (QC):", value=current_user.get("name", "Kim Dung"))

        c_mat1, c_mat2 = st.columns(2)
        with c_mat1:
            ty_le_nl = st.selectbox("🪵 Tỷ lệ NL đốt lò:", ["100% Củi", "80% Củi - 20% Dăm", "50% Củi - 50% Dăm", "100% Dăm"])
        with c_mat2:
            ty_le_mix = st.selectbox("🌾 Tỷ lệ phối trộn:", ["8:2", "7:3", "5:5", "10:0"])

        st.markdown("---")
        st.markdown("##### 💧 Chỉ Số Độ Ẩm (%)")
        c_m1, c_m2, c_m3, c_m4, c_m5 = st.columns(5)
        with c_m1:
            am_dam = st.number_input("Ẩm dăm thô (%):", min_value=0.0, max_value=80.0, value=45.0, step=0.5)
        with c_m2:
            am_truoc_say = st.number_input("Ẩm trước sấy (%):", min_value=0.0, max_value=80.0, value=42.0, step=0.5)
        with c_m3:
            am_sau_say_1 = st.number_input("Ẩm sau sấy 1 (%):", min_value=0.0, max_value=30.0, value=11.5, step=0.1)
        with c_m4:
            am_sau_say_2 = st.number_input("Ẩm sau sấy 2 (%):", min_value=0.0, max_value=30.0, value=11.2, step=0.1)
        with c_m5:
            am_vien = st.number_input("Ẩm viên nén (%):", min_value=0.0, max_value=20.0, value=8.8, step=0.1)

        # Đánh giá ẩm viên tức thì
        if 8.0 <= am_vien <= 9.5:
            st.success(f"🟢 **Độ ẩm viên thành phẩm:** `{am_vien}%` - ĐẠT CHUẨN XUẤT KHẨU (8.0 - 9.5%)")
        else:
            st.error(f"🔴 **Độ ẩm viên thành phẩm:** `{am_vien}%` - KHÔNG ĐẠT CHUẨN (Chuẩn yêu cầu: 8.0 - 9.5%)")

        st.markdown("---")
        st.markdown("##### ⚖️ Tỷ Trọng & Độ Tro Thành Phẩm")
        c_d1, c_d2, c_d3, c_d4 = st.columns(4)
        with c_d1:
            dens_vien = st.number_input("Tỷ trọng viên (kg/m³):", min_value=0.0, max_value=1000.0, value=630.0, step=5.0)
        with c_d2:
            do_tro = st.number_input("Độ tro (%):", min_value=0.0, max_value=10.0, value=1.2, step=0.1)
        with c_d3:
            dens_dam = st.number_input("Tỷ trọng dăm (kg/m³):", min_value=0.0, max_value=500.0, value=250.0, step=5.0)
        with c_d4:
            dens_nghien = st.number_input("Tỷ trọng bột tinh (kg/m³):", min_value=0.0, max_value=500.0, value=180.0, step=5.0)

        # Đánh giá chỉ tiêu
        if dens_vien >= 600:
            st.success(f"🟢 **Tỷ trọng:** `{dens_vien} kg/m³` (Đạt chuẩn ≥ 600 kg/m³)")
        else:
            st.warning(f"⚠️ **Tỷ trọng:** `{dens_vien} kg/m³` (Dưới chuẩn < 600 kg/m³)")

        if do_tro <= 1.5:
            st.success(f"🟢 **Độ tro:** `{do_tro}%` (Đạt chuẩn ≤ 1.5%)")
        else:
            st.warning(f"⚠️ **Độ tro:** `{do_tro}%` (Vượt mức chuẩn > 1.5%)")

        submitted_kcs = st.form_submit_button("🧪 GỬI KẾT QUẢ KIỂM NGHIỆM KCS", type="primary", use_container_width=True)

    if submitted_kcs:
        # Chuẩn hóa mã vị trí theo bảng danh mục:
        kcs_ldr = shift_leader_kcs
        if 'ca a' in shift_leader_kcs.lower() or 'sắc' in shift_leader_kcs.lower():
            kcs_ldr = 'Ca A'
        elif 'ca b' in shift_leader_kcs.lower() or 'tài' in shift_leader_kcs.lower():
            kcs_ldr = 'Ca B'
        elif 'ca c' in shift_leader_kcs.lower() or 'long' in shift_leader_kcs.lower():
            kcs_ldr = 'Ca C'

        kcs_record = {
            'date': kcs_date,
            'time_sample': time_sample,
            'shift_leader': kcs_ldr,
            'tester': tester_name,
            'ty_le_nl_dot': ty_le_nl,
            'ty_le_phoi_tron': ty_le_mix,
            'am_dam_pct': am_dam,
            'am_truoc_say_pct': am_truoc_say,
            'am_sau_say_1_pct': am_sau_say_1,
            'am_sau_say_2_pct': am_sau_say_2,
            'am_vien_pct': am_vien,
            'density_dam': dens_dam,
            'density_nghien_tho': 0.0,
            'density_nghien_tinh': dens_nghien,
            'density_vien': dens_vien,
            'do_tro_pct': do_tro,
        }

        with st.spinner("⏳ Đang lưu kết quả KCS lên Google Sheets..."):
            success_k, msg_k = dl.save_kcs_record(kcs_record)

        if success_k:
            st.session_state['flash_success_msg'] = f"🎉 **{msg_k}**"
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ {msg_k}")


def render_maintenance_entry_form(dl, current_user: Dict[str, Any]):
    """Form nhập nhật ký bảo trì & sửa chữa thiết bị (Phân quyền cho Bảo Trì & QĐ)"""
    st.markdown("#### 🔧 NHẬP NHẬT KÝ BẢO TRÌ & SỬA CHỮA THIẾT BỊ")
    st.caption("Số liệu nhập tại đây sẽ được tự động đồng bộ vào sheet `Data` trong bảng tính bảo trì (`2026 BẢO TRÌ BVN`).")

    # Lấy ngày mặc định từ bộ lọc ngày đầu trang nếu có
    default_d = st.session_state.get('top_target_date', date.today())
    if hasattr(default_d, 'date'):
        default_d = default_d.date()

    with st.form("form_maintenance_entry", clear_on_submit=False):
        st.markdown("##### 1️⃣ Thông Tin Ca & Thời Gian")
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            maint_date = st.date_input("📅 Ngày thực hiện:", value=default_d, key="maint_date_in")
        with c_m2:
            maint_shift = st.selectbox("⏰ Ca làm việc:", ["Ca 1 (06h - 14h)", "Ca 2 (14h - 22h)", "Ca 3 (22h - 06h)", "Hành chính (HC)"], key="maint_shift_in")
        with c_m3:
            default_performer = current_user.get("name", "Phan Nhớ") if current_user.get("role") == "bao_tri" else "Phan Nhớ, Tổ cơ khí"
            maint_performer = st.text_input("👷 Người thực hiện:", value=default_performer, key="maint_perf_in")

        st.markdown("---")
        st.markdown("##### 2️⃣ Cụm Thiết Bị & Hạng Mục Bảo Trì")
        c_eq1, c_eq2, c_eq3 = st.columns(3)
        with c_eq1:
            eq_group = st.selectbox("🏭 Phân xưởng / Cụm máy:", [
                "Máy ép viên (PE1 - PE8)",
                "Nghiền thô (HM118, HM218, HM318)",
                "Trống sấy (DR124, DR224)",
                "Nghiền tinh (HM147, HM247, HM347)",
                "Máy băm Chipper (CM108, CM208)",
                "Băng tải & Xích tải (BE, DC, SC)",
                "Hệ thống Lò đốt PDI & Quạt FA",
                "Khác / Toàn nhà máy"
            ], key="maint_eq_group")
        with c_eq2:
            eq_code = st.text_input("🏷️ Mã thiết bị cụ thể:", value="PE1510", help="Ví dụ: PE1, HM118, DR124, CM108, DC1311...", key="maint_eq_code")
        with c_eq3:
            die_code = st.text_input("⚙️ Mã khuôn / Mã phụ tùng (nếu có):", value="", placeholder="Ví dụ: Khuôn 8mm, Rulo 1LT...", key="maint_die_code")

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            activity_type = st.selectbox("🛠️ Loại hoạt động bảo trì:", [
                "Bảo trì chủ động (Định kỳ)",
                "Bảo trì sự cố (Đột xuất)",
                "Phục hồi rulo khuôn máy ép",
                "Thay thế phụ tùng / Bạc đạn",
                "Cân chỉnh dây curoa / xích tải",
                "Bôi trơn mỡ / Thay nhớt",
                "Vệ sinh thiết bị / Buồng máy",
                "Khác"
            ], key="maint_act_type")
        with c_act2:
            maint_status = st.selectbox("📌 Trạng thái hoàn thành:", [
                "OK (Hoàn thành)",
                "Đang xử lý / Theo dõi",
                "Chờ phụ tùng thay thế"
            ], key="maint_status_choice")

        st.markdown("---")
        st.markdown("##### 3️⃣ Nội Dung Công Việc & Thời Gian Dừng Máy")
        c_d1, c_d2 = st.columns([3, 1])
        with c_d1:
            maint_desc = st.text_area("📝 Mô tả nội dung xử lý / Hiện tượng sự cố:", placeholder="Ghi rõ nguyên nhân, thao tác kỹ thuật đã thực hiện...", key="maint_desc_in")
        with c_d2:
            duration_h = st.number_input("⏱️ Thời gian xử lý (Giờ):", min_value=0.0, max_value=24.0, value=1.0, step=0.5, key="maint_dur_in")

        submit_maint = st.form_submit_button("🚀 GỬI BÁO CÁO BẢO TRÌ LÊN HỆ THỐNG", type="primary", use_container_width=True)

    if submit_maint:
        if not eq_code.strip():
            st.error("⚠️ Vui lòng nhập mã thiết bị bảo trì!")
            return
        if not maint_desc.strip():
            st.error("⚠️ Vui lòng mô tả tóm tắt nội dung công việc bảo trì!")
            return

        shift_str = "Ca 1" if "Ca 1" in maint_shift else ("Ca 2" if "Ca 2" in maint_shift else ("Ca 3" if "Ca 3" in maint_shift else "HC"))
        status_clean = "OK" if "OK" in maint_status else maint_status

        record_data = {
            'date': maint_date,
            'shift': shift_str,
            'equipment': eq_code.strip(),
            'die_code': die_code.strip(),
            'activity': activity_type,
            'description': maint_desc.strip(),
            'duration_hours': duration_h,
            'performer': maint_performer.strip(),
            'status': status_clean
        }

        with st.spinner("⏳ Đang lưu nhật ký bảo trì lên Google Sheets..."):
            success_m, msg_m = dl.save_maintenance_record(record_data)

        if success_m:
            st.session_state['flash_success_msg'] = f"🎉 **{msg_m}**"
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ {msg_m}")


def render_chipper_entry_form(dl, current_user: Dict[str, Any]):
    """Form nhập báo cáo vận hành phân xưởng băm dăm (Chipper) (Phân quyền cho QL tổ băm, Tổ băm 1, Tổ băm 2, QĐ)"""
    st.markdown("#### 🪵 NHẬP BÁO CÁO VẬN HÀNH PHÂN XƯỞNG BĂM DĂM (CHIPPER)")
    st.caption("Số liệu nhập tại đây sẽ được đồng bộ vào hệ thống theo dõi nguyên liệu & nhật ký phân xưởng băm dăm.")

    # Lấy ngày mặc định từ bộ lọc ngày đầu trang nếu có
    default_d = st.session_state.get('top_target_date', date.today())
    if hasattr(default_d, 'date'):
        default_d = default_d.date()

    with st.form("form_chipper_entry", clear_on_submit=False):
        st.markdown("##### 1️⃣ Thông Tin Ca Làm Việc & Tổ Trực")
        c_cp1, c_cp2, c_cp3 = st.columns(3)
        with c_cp1:
            chip_date = st.date_input("📅 Ngày sản xuất:", value=default_d, key="chip_date_in")
        with c_cp2:
            chip_shift = st.selectbox("⏰ Ca băm:", ["Ca 1 (06h - 14h)", "Ca 2 (14h - 22h)", "Ca 3 (22h - 06h)"], key="chip_shift_in")
        with c_cp3:
            u_role = current_user.get("role", "")
            team_default_idx = 0
            if u_role == "tobam1":
                team_default_idx = 1
            elif u_role == "tobam2":
                team_default_idx = 2
            chip_team = st.selectbox("👥 Tổ phụ trách:", [
                "QL tổ băm (Phạm Văn Cường)",
                "Tổ băm 1 (Trần Văn Quảng)",
                "Tổ băm 2 (Trần Mạnh Hà)"
            ], index=team_default_idx, key="chip_team_in")

        st.markdown("---")
        st.markdown("##### 2️⃣ Khối Lượng Nguyên Liệu & Sản Lượng Dăm")
        c_kl1, c_kl2, c_kl3 = st.columns(3)
        with c_kl1:
            go_cay_val = st.number_input("🪵 Gỗ cây / Củi tiếp nhận (tấn):", min_value=0.0, max_value=1000.0, value=150.0, step=1.0, format="%.1f", key="chip_go_in")
        with c_kl2:
            dam_ra_val = st.number_input("📦 Sản lượng dăm băm ra (tấn):", min_value=0.0, max_value=1000.0, value=145.0, step=1.0, format="%.1f", key="chip_dam_in")
        with c_kl3:
            rate_recovery = round(dam_ra_val / go_cay_val * 100, 1) if go_cay_val > 0 else 0.0
            st.metric("📊 Tỷ lệ thu hồi dăm:", f"{rate_recovery}%", help="Tỷ lệ dăm thành phẩm / gỗ cây đầu vào")

        st.markdown("---")
        st.markdown("##### 3️⃣ Giờ Hoạt Động Tuyến Máy Băm & Năng Lượng")
        c_h1, c_h2, c_h3, c_h4 = st.columns(4)
        with c_h1:
            h_chip1 = st.number_input("Máy băm Line 1 (CM108 - h):", min_value=0.0, max_value=8.0, value=6.5, step=0.5, key="chip_h1_in")
        with c_h2:
            h_chip2 = st.number_input("Máy băm Line 2 (CM208 - h):", min_value=0.0, max_value=8.0, value=6.5, step=0.5, key="chip_h2_in")
        with c_h3:
            dien_chip = st.number_input("⚡ Điện năng tiêu thụ (kWh):", min_value=0.0, max_value=20000.0, value=3200.0, step=50.0, key="chip_dien_in")
        with c_h4:
            dau_do = st.number_input("⛽ Dầu DO cẩu gắp / xe xúc (Lít):", min_value=0.0, max_value=1000.0, value=65.0, step=5.0, key="chip_dau_in")

        total_chip_hours = h_chip1 + h_chip2
        tph_chip = round(dam_ra_val / total_chip_hours, 1) if total_chip_hours > 0 else 0.0
        suat_dien_chip = round(dien_chip / dam_ra_val, 1) if dam_ra_val > 0 else 0.0
        st.info(f"⚡ **Tổng giờ băm:** `{total_chip_hours} giờ` | **Năng suất bình quân:** `{tph_chip} tấn/h` | **Suất điện băm dăm:** `{suat_dien_chip} kWh/tấn`")

        st.markdown("---")
        st.markdown("##### 4️⃣ Kiểm Soát Kỹ Thuật & An Toàn Thiết Bị")
        c_chk1, c_chk2 = st.columns(2)
        with c_chk1:
            knife_st = st.selectbox("🔪 Tình trạng lưỡi dao băm:", [
                "Dao sắc bén - Vận hành tốt",
                "Dao mòn nhẹ - Tiếp tục chạy ca sau",
                "Đã đảo mặt dao / Thay bộ dao mới",
                "Mẻ dao do dính đá / kim loại (Cần thay)"
            ], key="chip_knife_in")
        with c_chk2:
            magnet_st = st.selectbox("🧲 Bẫy đá (Stone Drawer) & 4 Nam châm tách từ:", [
                "Đạt chuẩn - Đã vệ sinh sạch khay bẫy đá",
                "Phát hiện mạt sắt / đinh lẫn vào dăm",
                "Có đá sỏi lớn lẫn vào gỗ cây",
                "Chưa vệ sinh bẫy đá"
            ], key="chip_magnet_in")

        chip_notes = st.text_area("📝 Ghi chú ca băm (Chất lượng nguyên liệu gỗ, sự cố dừng máy, tình trạng bãi chứa):", placeholder="Ghi chú tóm tắt...", key="chip_notes_in")

        submit_chip = st.form_submit_button("🚀 GỬI BÁO CÁO TỔ BĂM LÊN HỆ THỐNG", type="primary", use_container_width=True)

    if submit_chip:
        if dam_ra_val <= 0 and go_cay_val <= 0:
            st.error("⚠️ Vui lòng kiểm tra lại: Sản lượng dăm băm và gỗ cây đang bằng 0!")
            return

        team_code = "QL tổ băm" if "QL" in chip_team else ("Tổ băm 1" if "1" in chip_team else "Tổ băm 2")
        shift_code = "Ca 1" if "Ca 1" in chip_shift else ("Ca 2" if "Ca 2" in chip_shift else "Ca 3")

        record_chip = {
            'date': chip_date,
            'shift': shift_code,
            'team': team_code,
            'go_cay_tan': go_cay_val,
            'dam_ra_tan': dam_ra_val,
            'h_chipper1': h_chip1,
            'h_chipper2': h_chip2,
            'dien_kwh': dien_chip,
            'dau_do_lit': dau_do,
            'knife_status': knife_st,
            'magnet_status': magnet_st,
            'notes': chip_notes.strip()
        }

        with st.spinner("⏳ Đang đồng bộ số liệu ca băm dăm lên hệ thống..."):
            success_c, msg_c = dl.save_chipper_record(record_chip)

        if success_c:
            st.session_state['flash_success_msg'] = f"🎉 **{msg_c}**"
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ {msg_c}")


def render_change_pin_form(current_user: Dict[str, Any]):
    """Cho phép người dùng tự đổi mã PIN của mình"""
    st.markdown("#### ⚙️ ĐỔI MÃ PIN ĐĂNG NHẬP")
    st.caption("Mã PIN mới sẽ được áp dụng cho các lần đăng nhập tiếp theo trên thiết bị này.")

    uid = current_user.get("id")
    with st.form("form_change_pin"):
        old_pin = st.text_input("🔑 Nhập mã PIN hiện tại:", type="password", max_chars=6)
        new_pin1 = st.text_input("🔒 Nhập mã PIN mới (4 số):", type="password", max_chars=6)
        new_pin2 = st.text_input("🔒 Xác nhận mã PIN mới:", type="password", max_chars=6)

        sub_pin = st.form_submit_button("LƯU MÃ PIN MỚI", use_container_width=True)

    if sub_pin:
        users = load_user_pins()
        if old_pin != users[uid]["pin"]:
            st.error("❌ Mã PIN hiện tại không chính xác!")
            return
        if len(new_pin1) < 4:
            st.error("⚠️ Mã PIN phải có ít nhất 4 chữ số!")
            return
        if new_pin1 != new_pin2:
            st.error("⚠️ Mã PIN mới và mã xác nhận không trùng khớp!")
            return

        if save_user_pin(uid, new_pin1):
            st.session_state["authenticated_user"]["pin"] = new_pin1
            st.success("✅ Đã cập nhật mã PIN mới thành công!")
        else:
            st.error("❌ Không thể lưu mã PIN. Vui lòng thử lại sau.")


# ================= KHÓA CHẾ ĐỘ PUBLIC - CẤP QUYỀN CHO 3 CA, QC, QĐ & SANGMCC1@GMAIL.COM =================
AUTHORIZED_VIEWER_EMAIL = "sangmcc1@gmail.com"
DEFAULT_VIEWER_KEY = "sang2026"


def check_viewer_authorization() -> bool:
    """
    Kiểm tra quyền xem hệ thống:
    1. Kiểm tra URL query param: ?pin=1111 (Ca A), ?pin=2222 (Ca B), ?pin=3333 (Ca C), ?pin=8888 (QC), ?pin=9999 (QĐ/Admin), ?key=sang2026
    2. Kiểm tra tài khoản Google đăng nhập từ Streamlit Community Cloud (st.user hoặc st.experimental_user)
    3. Kiểm tra phiên làm việc session_state đã được mở khóa bằng email sangmcc1@gmail.com hoặc mã PIN hợp lệ
    4. Hoặc Ca Trưởng / QC / QĐ / Nhân viên đã đăng nhập bằng mã PIN để làm việc
    """
    # 1. Kiểm tra URL query parameter (tiện ích cho Bookmark / Ghim màn hình chính iPhone)
    try:
        qp = st.query_params
        in_key = qp.get("key") or qp.get("pin") or qp.get("token") or qp.get("pass")
        if in_key:
            in_key_str = str(in_key).strip()
            users = load_user_pins()

            # Kiểm tra khớp PIN người dùng (Ca A: 1111, Ca B: 2222, Ca C: 3333, QC: 8888, QĐ: 9999...)
            for uid, u in users.items():
                if in_key_str == str(u.get("pin", "")).strip():
                    st.session_state["authenticated_user"] = u
                    st.session_state["viewer_authorized_email"] = u.get("id", uid)
                    return True

            if in_key_str in ["9999", "admin"]:
                st.session_state["viewer_authorized_email"] = "admin"
                st.session_state["authenticated_user"] = users.get("manager", {"pin": "9999", "full_name": "Quản Trị Viên (Admin)", "icon": "👑"})
                return True
            elif in_key_str in [DEFAULT_VIEWER_KEY, "sang2026"]:
                st.session_state["viewer_authorized_email"] = AUTHORIZED_VIEWER_EMAIL
                return True
    except Exception:
        pass

    # 2. Kiểm tra Streamlit Cloud OAuth User
    try:
        if hasattr(st, "user"):
            u_email = getattr(st.user, "email", None)
            if u_email and str(u_email).strip().lower() == AUTHORIZED_VIEWER_EMAIL.lower():
                return True
        elif hasattr(st, "experimental_user"):
            u_email = getattr(st.experimental_user, "email", None)
            if u_email and str(u_email).strip().lower() == AUTHORIZED_VIEWER_EMAIL.lower():
                return True
    except Exception:
        pass

    # 3. Kiểm tra session state của người xem hoặc Admin được cấp quyền
    if st.session_state.get("viewer_authorized_email"):
        return True

    # 4. Nếu là Ca Trưởng / QC / QĐ đã đăng nhập mã PIN
    if st.session_state.get("authenticated_user") is not None:
        return True

    return False


def logout_viewer():
    """Đăng xuất quyền xem và khóa lại hệ thống"""
    if "viewer_authorized_email" in st.session_state:
        del st.session_state["viewer_authorized_email"]
    if "authenticated_user" in st.session_state:
        del st.session_state["authenticated_user"]
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.rerun()


def render_viewer_lock_screen(logo_b64: str = ""):
    """
    Hiển thị màn hình khóa bảo mật khi chế độ public bị tắt.
    Cấp quyền xem cho: Quản Trị Viên (Admin), QĐ, QC, Ca A, Ca B, Ca C & Email sangmcc1@gmail.com
    Hỗ trợ chuyển đổi song ngữ trực tiếp ngay tại màn hình khóa.
    """
    curr_l = get_lang()

    # 🌐 THANH CHUYỂN ĐỔI NGÔN NGỮ ĐẦU TRANG KHÓA (HIỂN THỊ NGAY TRÊN IPHONE)
    c_hdr_l, c_hdr_r = st.columns([6, 4])
    with c_hdr_l:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 6px;">
            <span style="background: linear-gradient(135deg, #16a34a, #15803d); color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 11px;">BVN</span>
            <span style="font-size: 12px; font-weight: 700; color: #64748b;">{t("HỆ THỐNG BẢO MẬT NỘI BỘ", "INTERNAL SECURITY SYSTEM")}</span>
        </div>
        """, unsafe_allow_html=True)
    with c_hdr_r:
        b_vi, b_en = st.columns(2)
        with b_vi:
            if st.button("🇻🇳 Tiếng Việt", type="primary" if curr_l == 'vi' else "secondary", use_container_width=True, key="lock_lang_btn_vi"):
                if curr_l != 'vi':
                    apply_language_change('vi')
                    st.rerun()
        with b_en:
            if st.button("🇬🇧 English", type="primary" if curr_l == 'en' else "secondary", use_container_width=True, key="lock_lang_btn_en"):
                if curr_l != 'en':
                    apply_language_change('en')
                    st.rerun()

    lock_title = t("HỆ THỐNG BÁO CÁO NỘI BỘ ĐÃ KHÓA BẢO MẬT", "INTERNAL REPORTING SYSTEM IS SECURED")
    lock_sub = t(
        "Hệ thống Báo cáo Sản xuất Nhà máy BVN Quảng Bình hiện đang ở chế độ bảo mật nội bộ.",
        "BVN Quang Binh Wood Pellet Production Report is in private internal mode."
    )
    auth_label = t("Cấp quyền xem báo cáo cho:", "Authorized viewer access for:")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 2px solid #38bdf8; border-radius: 16px; padding: 24px 20px; max-width: 720px; margin: 15px auto 20px auto; text-align: center; box-shadow: 0 12px 36px rgba(0,0,0,0.5);">
        <div style="font-size: 46px; margin-bottom: 8px;">🔒</div>
        <div style="font-size: 21px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; text-transform: uppercase;">
            {lock_title}
        </div>
        <div style="font-size: 13.5px; color: #94a3b8; margin-top: 8px; line-height: 1.7;">
            {lock_sub}<br>
            <b>{auth_label}</b><br>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-top: 8px;">
                <span style="background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🎖️ Giám Đốc (GĐ)</span>
                <span style="background: rgba(234, 179, 8, 0.18); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">👑 PGĐ (Admin)</span>
                <span style="background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">⭐ Quản Đốc (QĐ)</span>
                <span style="background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🟢 Ca A</span>
                <span style="background: rgba(249, 115, 22, 0.18); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🟠 Ca B</span>
                <span style="background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🔵 Ca C</span>
                <span style="background: rgba(168, 85, 247, 0.18); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🪵 Chipper (Tổ Băm)</span>
                <span style="background: rgba(20, 184, 166, 0.18); color: #2dd4bf; border: 1px solid rgba(20, 184, 166, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🔬 QC (Kim Dung)</span>
                <span style="background: rgba(14, 165, 233, 0.18); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">🔧 Bảo Trì (Phan Nhớ)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_box1, c_box2, c_box3 = st.columns([1, 2, 1])
    with c_box2:
        users = load_user_pins()

        st.markdown(f"##### {t('🔑 Mở Khóa Xem Hệ Thống Báo Cáo', '🔑 Unlock Reporting System')}")
        st.caption(t(
            "Nhập mã PIN bảo mật được cấp để mở quyền xem toàn bộ hệ thống báo cáo sản xuất.",
            "Enter your confidential PIN to view all production reports."
        ))
        
        with st.form("form_unlock_all_pin", clear_on_submit=False):
            u_opts = {
                t("⚡ Tự Động Nhận Diện Theo Mã PIN (Nhanh Nhất)", "⚡ Auto-Detect by PIN (Fastest)"): "auto",
                f"🎖️ {t('Giám Đốc (GĐ - Vũ Quang Sáng)', 'Plant Director (GD - Vu Quang Sang)')}": "director",
                f"👑 {t('Phó Giám Đốc (PGĐ - Đỗ Công Thịnh - Admin)', 'Deputy Director (PGD - Do Cong Thinh - Admin)')}": "pgd",
                f"⭐ {t('Quản Đốc (QĐ - Nguyễn Đăng Thành)', 'Factory Manager (QD - Nguyen Dang Thanh)')}": "manager",
                f"🟢 {t('Ca Trưởng Lê Chiến Sắc (Ca A)', 'Shift Leader Le Chien Sac (Shift A)')}": "sac",
                f"🟠 {t('Ca Trưởng Hoàng Phúc Tài (Ca B)', 'Shift Leader Hoang Phuc Tai (Shift B)')}": "tai",
                f"🔵 {t('Ca Trưởng Nguyễn Long (Ca C)', 'Shift Leader Nguyen Long (Shift C)')}": "long",
                f"🪵 {t('QL Tổ Băm (Phạm Văn Cường - Chipper)', 'Chipper Manager (Pham Van Cuong)')}": "ql_tobam",
                f"🪓 {t('Tổ Băm 1 (Trần Văn Quảng - Chipper)', 'Chipper Team 1 (Tran Van Quang)')}": "tobam1",
                f"🪓 {t('Tổ Băm 2 (Trần Mạnh Hà - Chipper)', 'Chipper Team 2 (Tran Manh Ha)')}": "tobam2",
                f"🔬 {t('KCS / QC (Kim Dung)', 'Quality Control QC (Kim Dung)')}": "kcs",
                f"🔧 {t('Tổ Trưởng Cơ Khí (Phan Nhớ - Bảo Trì)', 'Mechanical Lead Phan Nho (Maintenance)')}": "baotri",
            }
            
            sel_identity_label = st.selectbox(
                t("Chọn danh tính (hoặc để Tự Động):", "Select identity (or keep Auto-Detect):"),
                list(u_opts.keys()),
                index=0,
                key="lock_sel_identity"
            )
            sel_uid = u_opts[sel_identity_label]

            in_pin = st.text_input(
                t("🔑 Nhập Mã PIN (4 số):", "🔑 Enter PIN (4 digits):"), 
                type="password", 
                placeholder=t("Nhập mã PIN bí mật của bạn...", "Enter your secret PIN..."), 
                key="lock_in_all_pin", 
                max_chars=8
            )
            
            c_ab1, c_ab2 = st.columns([1, 1])
            with c_ab1:
                submit_view = st.form_submit_button(
                    t("🔓 MỞ XEM BÁO CÁO (Enter ↵)", "🔓 VIEW REPORTS (Enter ↵)"), 
                    type="primary", 
                    use_container_width=True
                )
            with c_ab2:
                submit_entry = st.form_submit_button(
                    t("🏭 VÀO NHẬP SỐ LIỆU", "🏭 DATA ENTRY"), 
                    type="secondary", 
                    use_container_width=True
                )

        if submit_view or submit_entry:
            pin_clean = str(in_pin).strip()
            matched_user = None

            if not pin_clean:
                st.error(t("⚠️ Vui lòng nhập mã PIN!", "⚠️ Please enter a PIN!"))
            elif sel_uid == "auto":
                # Tự động nhận diện người dùng qua mã PIN
                if pin_clean in ["9999", "admin"]:
                    matched_user = users.get("pgd", {"pin": "9999", "full_name": "Phó Giám Đốc (PGĐ - Đỗ Công Thịnh - Admin)", "icon": "👑"})
                elif pin_clean in ["7777"]:
                    matched_user = users.get("manager", {"pin": "7777", "full_name": "Quản Đốc (QĐ - Nguyễn Đăng Thành)", "icon": "⭐"})
                elif pin_clean in ["6868", DEFAULT_VIEWER_KEY, "sang2026"]:
                    matched_user = users.get("director", {"pin": "6868", "full_name": "Giám Đốc (GĐ - Vũ Quang Sáng)", "icon": "🎖️"})
                else:
                    for uid, u in users.items():
                        if pin_clean == str(u.get("pin", "")).strip():
                            matched_user = u
                            break
            else:
                target_u = users.get(sel_uid)
                if target_u and (
                    pin_clean == str(target_u.get("pin", "")).strip() 
                    or (sel_uid == "pgd" and pin_clean in ["9999", "admin"])
                    or (sel_uid == "manager" and pin_clean in ["7777", "9999", "admin"])
                    or (sel_uid == "director" and pin_clean in ["6868", "9999", DEFAULT_VIEWER_KEY, "sang2026"])
                ):
                    matched_user = target_u

            if matched_user:
                st.session_state["authenticated_user"] = matched_user
                st.session_state["viewer_authorized_email"] = matched_user.get("id", "authorized")
                if submit_entry:
                    st.session_state["active_task"] = t("📝 14. Nhập Số Liệu", "📝 14. Data Entry")
                else:
                    st.session_state["active_task"] = get_op_tasks(get_lang())[0]
                u_name = matched_user.get("full_name", matched_user.get("name", "Người dùng"))
                st.success(t(f"✅ Xác thực thành công: {u_name}! Đang mở hệ thống...", f"✅ Successfully verified: {u_name}! Opening system..."))
                st.rerun()
            elif pin_clean:
                st.error(t(
                    "❌ Mã PIN không chính xác! Vui lòng kiểm tra lại hoặc liên hệ Quản lý / Quản trị viên để được cấp mã PIN.",
                    "❌ Incorrect PIN! Please check again or contact Administrator for your PIN."
                ))

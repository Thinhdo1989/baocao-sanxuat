"""
Mô-đun Quản Lý Nhập Liệu Báo Cáo Sản Xuất & KCS
Hỗ trợ:
1. Phân quyền và xác thực bằng Mã PIN theo Ca Trưởng (Long, Sắc, Tài), KCS và Ban Quản Đốc.
2. Form nhập số liệu ca sản xuất (Sản lượng, điện năng, giờ máy chạy 8 máy ép, nghiền, sấy, dăm đốt).
3. Form nhập kết quả đo kiểm chất lượng KCS (Độ ẩm dăm, sau sấy, ẩm viên, tỷ trọng, độ tro).
4. Tính toán thời gian thực các chỉ số KPI: Suất điện (kWh/tấn), Năng suất ép (tấn/h), cảnh báo định mức.
5. Ghi tự động vào Google Sheets 'Product' & 'KCS' và đồng bộ bộ đệm cache cục bộ.
"""

import os
import json
from datetime import datetime, date, time
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

# File lưu trữ mã PIN tùy chỉnh (nếu có)
PIN_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "assets", "user_pins.json")

# Danh sách người dùng mặc định và mã PIN khởi tạo
DEFAULT_USERS = {
    "long": {
        "id": "long",
        "name": "Long",
        "full_name": "Ca Trưởng Long",
        "role": "shift_leader",
        "pin": "1111",
        "icon": "🔵"
    },
    "sac": {
        "id": "sac",
        "name": "Sắc",
        "full_name": "Ca Trưởng Sắc",
        "role": "shift_leader",
        "pin": "2222",
        "icon": "🟢"
    },
    "tai": {
        "id": "tai",
        "name": "Tài",
        "full_name": "Ca Trưởng Tài",
        "role": "shift_leader",
        "pin": "3333",
        "icon": "🟠"
    },
    "kcs": {
        "id": "kcs",
        "name": "KCS",
        "full_name": "Kỹ Thuật Viên KCS / QA-QC",
        "role": "qc",
        "pin": "8888",
        "icon": "🔬"
    },
    "manager": {
        "id": "manager",
        "name": "Quản Đốc",
        "full_name": "Quản Đốc Phân Xưởng / Giám Đốc",
        "role": "manager",
        "pin": "9999",
        "icon": "👑"
    }
}


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
    """Đăng xuất khỏi hệ thống"""
    if "authenticated_user" in st.session_state:
        del st.session_state["authenticated_user"]
    st.rerun()


def render_login_box():
    """Hiển thị hộp đăng nhập mã PIN cho Ca Trưởng / KCS"""
    users = load_user_pins()
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 24px; max-width: 580px; margin: 20px auto; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
        <div style="text-align: center; margin-bottom: 16px;">
            <div style="font-size: 36px; margin-bottom: 8px;">🔐</div>
            <div style="font-size: 20px; font-weight: 800; color: #f8fafc;">XÁC THỰC QUYỀN NHẬP BÁO CÁO CA</div>
            <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
                Chế độ xem công khai (Public) chỉ cho phép tra cứu. Vui lòng đăng nhập mã PIN để nhập số liệu sản xuất và kết quả KCS.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_box1, c_box2, c_box3 = st.columns([1, 2, 1])
    with c_box2:
        user_options = {u["full_name"]: uid for uid, u in users.items()}
        selected_name = st.selectbox("👤 Chọn Danh Tính Của Bạn:", list(user_options.keys()))
        selected_uid = user_options[selected_name]

        input_pin = st.text_input("🔑 Nhập Mã PIN (4 số):", type="password", max_chars=6, placeholder="••••")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔓 ĐĂNG NHẬP", type="primary", use_container_width=True):
                target_user = users[selected_uid]
                if input_pin == target_user["pin"]:
                    st.session_state["authenticated_user"] = target_user
                    st.success(f"✅ Đăng nhập thành công! Xin chào {target_user['full_name']}.")
                    st.rerun()
                else:
                    st.error("❌ Mã PIN không chính xác! Vui lòng thử lại.")

        with col_btn2:
            with st.popover("ℹ️ Gợi ý PIN mặc định"):
                st.markdown("""
                **Mã PIN ban đầu:**
                - Ca Trưởng Long: `1111`
                - Ca Trưởng Sắc: `2222`
                - Ca Trưởng Tài: `3333`
                - KTV KCS: `8888`
                - Quản Đốc: `9999`
                *(Có thể tự đổi PIN sau khi đăng nhập)*
                """)


def render_data_entry_module(dl):
    """
    Hàm chính điều hướng giao diện Nhập Liệu Báo Cáo Sản Xuất & KCS
    """
    current_user = get_current_user()

    # Nếu chưa đăng nhập, hiển thị form xác thực PIN
    if current_user is None:
        render_login_box()
        return

    # Thanh thông tin người dùng đang đăng nhập
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
                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Quyền hạn: {user_role.upper()} • Dữ liệu nhập sẽ tự động gán tên và lưu vào Google Sheets</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_hdr2:
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            logout_user()

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    # Chọn tab theo vai trò
    if user_role == "qc":
        tab_list = ["🔬 Báo Cáo Kiểm Định KCS & Đo Ẩm", "🏭 Báo Cáo Sản Xuất Ca", "⚙️ Đổi Mã PIN"]
    else:
        tab_list = ["🏭 Báo Cáo Sản Xuất Ca", "🔬 Báo Cáo Kiểm Định KCS & Đo Ẩm", "⚙️ Đổi Mã PIN"]

    active_entry_tab = st.tabs(tab_list)

    # 1. TAB BÁO CÁO SẢN XUẤT CA
    idx_prod = tab_list.index("🏭 Báo Cáo Sản Xuất Ca")
    with active_entry_tab[idx_prod]:
        render_shift_production_form(dl, current_user)

    # 2. TAB BÁO CÁO KIỂM ĐỊNH KCS
    idx_kcs = tab_list.index("🔬 Báo Cáo Kiểm Định KCS & Đo Ẩm")
    with active_entry_tab[idx_kcs]:
        render_kcs_entry_form(dl, current_user)

    # 3. TAB ĐỔI MÃ PIN
    idx_pin = tab_list.index("⚙️ Đổi Mã PIN")
    with active_entry_tab[idx_pin]:
        render_change_pin_form(current_user)


def render_shift_production_form(dl, current_user: Dict[str, Any]):
    """Form nhập báo cáo sản xuất ca dành cho Ca Trưởng & Quản Đốc"""
    st.markdown("#### 📝 NHẬP BÁO CÁO KẾT QUẢ SẢN XUẤT CA")
    st.caption("Số liệu nhập tại đây sẽ được tự động đồng bộ lên Google Sheets (Sheet `Product`) và làm mới Dashboard tức thì.")

    with st.form("form_shift_entry", clear_on_submit=False):
        # 1. Thông tin chung
        st.markdown("##### 1️⃣ Thông Tin Thời Gian & Phân Ca")
        c_i1, c_i2, c_i3 = st.columns(3)
        with c_i1:
            report_date = st.date_input("📅 Ngày sản xuất:", value=date.today())
        with c_i2:
            shift_choice = st.selectbox("⏰ Ca làm việc:", ["Ca 1 (06h - 14h)", "Ca 2 (14h - 22h)", "Ca 3 (22h - 06h)"])
        with c_i3:
            # Nếu là Ca trưởng thì mặc định cố định tên, nếu là Quản đốc thì cho chọn
            if current_user.get("role") == "manager":
                shift_leader_input = st.selectbox("👤 Ca Trưởng:", ["Long", "Sắc", "Tài", "Bảo trì-VS", "Nghĩ"])
            else:
                shift_leader_input = current_user.get("name", "Long")
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
        if san_luong_val <= 0 and "Nghĩ" not in shift_leader_input and "Bảo trì" not in shift_leader_input:
            st.error("⚠️ Vui lòng kiểm tra lại: Sản lượng ca đang bằng 0!")
            return

        record_data = {
            'date': report_date,
            'shift_leader': shift_leader_input,
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
            st.success(f"🎉 **{message}**")
            if san_luong_val >= chi_tieu_val and suat_dien_calc <= 175:
                st.balloons()
            st.info("💡 Bạn có thể chuyển sang Mục 1 hoặc Mục 2 trên thanh menu để xem số liệu vừa nhập đã được phản ánh ngay trên các biểu đồ.")
        else:
            st.error(f"❌ {message}")


def render_kcs_entry_form(dl, current_user: Dict[str, Any]):
    """Form nhập kết quả kiểm nghiệm KCS chất lượng độ ẩm & tỷ trọng"""
    st.markdown("#### 🔬 NHẬP KẾT QUẢ ĐO KIỂM CHẤT LƯỢNG KCS")
    st.caption("Dữ liệu đo độ ẩm nguyên liệu, sau sấy và viên nén thành phẩm sẽ được ghi vào sheet `KCS`.")

    with st.form("form_kcs_entry", clear_on_submit=False):
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        with c_k1:
            kcs_date = st.date_input("📅 Ngày kiểm nghiệm:", value=date.today(), key="kcs_in_date")
        with c_k2:
            time_sample = st.selectbox("⏰ Giờ lấy mẫu:", ["02h", "04h", "06h", "08h", "10h", "12h", "14h", "16h", "18h", "20h", "22h", "24h"])
        with c_k3:
            shift_leader_kcs = st.selectbox("👤 Ca Trưởng trực:", ["Long", "Sắc", "Tài"])
        with c_k4:
            tester_name = st.text_input("🧪 KTV kiểm tra:", value=current_user.get("name", "KCS"))

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
        kcs_record = {
            'date': kcs_date,
            'time_sample': time_sample,
            'shift_leader': shift_leader_kcs,
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
            st.success(f"🎉 **{msg_k}**")
        else:
            st.error(f"❌ {msg_k}")


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

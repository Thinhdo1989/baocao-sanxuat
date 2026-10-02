@echo off
chcp 65001 >nul
title Khoi Phuc / Cai Dat Moi Truong Chay Bao Cao San Xuat
cd /d "%~dp0"

echo =====================================================================
echo    KHOI PHUC VA CAI DAT MOI TRUONG PYTHON CHO HE THONG BAO CAO
echo =====================================================================
echo.
echo Dang kiem tra cong cu UV va Python tren may tinh...

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [+] Da tim thay cong cu toc do cao UV!
    echo [*] Dang tao / cap nhat moi truong ao .venv tai thu muc hien tai...
    uv venv .venv --python 3.11
    echo [*] Dang cai dat cac goi thu vien tu requirements.txt...
    uv pip install -r requirements.txt
) else (
    echo [-] Khong tim thay UV, su dung trinh quan ly Python he thong...
    where python >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [LOI] May tinh chua cai dat Python hoac UV!
        echo Vui long cai dat Python 3.11 hoac UV roi thu lai.
        pause
        exit /b 1
    )
    echo [*] Dang khoi tao moi truong ao .venv...
    python -m venv .venv
    echo [*] Dang cai dat cac thu vien can thiet...
    ".venv\Scripts\pip.exe" install -r requirements.txt
)

echo.
if exist ".venv\Scripts\streamlit.exe" (
    echo =====================================================================
    echo [THANH CONG] Moi truong Python .venv da san sang 100%!
    echo Ban co the chay he thong bang cach nhap dup vao Chay_Ung_Dung.bat
    echo =====================================================================
) else (
    echo =====================================================================
    echo [CANH BAO] Khong the tao streamlit.exe. Vui long kiem tra lai ket noi mang!
    echo =====================================================================
)
echo.
pause

@echo off
chcp 65001 >nul
title Khoi Dong He Thong Bao Cao San Xuat - Nha May Vien Nen Go
cd /d "%~dp0"

echo =====================================================================
echo    HE THONG BAO CAO SAN XUAT TU DONG - NHA MAY VIEN NEN GO
echo =====================================================================
echo.
echo [1] MAY TINH NAY (LOCAL):
echo     http://localhost:8501
echo.
echo [2] DIEN THOAI / TABLET (CUNG MANG WI-FI):
echo     http://192.168.1.7:8501
echo.
echo     * Luu y: Dien thoai / tablet can ket noi vao cung mang Wi-Fi!
echo =====================================================================
echo.
echo Dang khoi dong may chu Dashboard Streamlit...
echo Trinh duyet web se tu dong mo khi ung dung san sang!
echo (Vui long giu nguyen cua so nay trong qua trinh su dung)
echo.

if not exist ".venv\Scripts\streamlit.exe" (
    echo [LOI] Khong tim thay moi truong ao .venv!
    echo Vui long lien he ho tro ky thuat.
    pause
    exit /b 1
)

:: Khoi chay Streamlit ho tro ket noi mang noi bo 0.0.0.0
".venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless false

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co van de xay ra khi chay ung dung!
    pause
)

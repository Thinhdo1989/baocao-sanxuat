@echo off
chcp 65001 >nul
title Dong Bo & Cap Nhat Bao Cao San Xuat Len Web Streamlit Cloud
cd /d "%~dp0"

echo =====================================================================
echo    DONG BO & CAP NHAT HE THONG BAO CAO LEN WEB STREAMLIT CLOUD
echo =====================================================================
echo.
echo [1/3] Kiem tra va dong bo file moi nhat vao deploy_files...
xcopy /Y /Q *.py deploy_files\ >nul 2>&1

echo [2/3] Luu cac thay doi vao Git...
git add -A
git commit -m "Auto sync: Cap nhat he thong bao cao" >nul 2>&1

echo [3/3] Dang day du lieu len GitHub (Thinhdo1989/baocao-sanxuat)...
echo (Neu cua so trinh duyet GitHub mo ra, vui long bam "Authorize" / "Sign in")
echo.
git push origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo =====================================================================
    echo [THANH CONG] Da day toan bo ma nguon moi nhat len GitHub thanh cong!
    echo.
    echo Streamlit Cloud se tu dong cap nhat trong khoang 30 - 60 giay.
    echo Link web cua ban: https://baocao-sanxua-pr32vanq35zuxh6zngmmly.streamlit.app/
    echo =====================================================================
) else (
    echo =====================================================================
    echo [CHU Y] Neu GitHub yeu cau xac thuc:
    echo     Vui long lam theo huong dan tren man hinh hoac trinh duyet.
    echo =====================================================================
)
echo.
pause

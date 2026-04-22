@echo off
echo ===================================
echo  Packaging Finance Board v2.0.0
echo ===================================

pip install pyinstaller

pyinstaller --name "FinanceBoard" ^
            --windowed ^
            --icon="assets/icon.ico" ^
            --add-data="assets;assets" ^
            --clean ^
            --noconfirm ^
            main.py

echo.
echo ===================================
echo  Packaging Complete!
echo  Check the 'dist/FinanceBoard' folder.
echo ===================================
pause

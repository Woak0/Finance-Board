@echo off
echo ===================================
echo  Packaging Finance Board...
echo ===================================

REM 
pip install pyinstaller

REM 
pyinstaller --name "FinanceBoard" ^
            --windowed ^
            --icon="assets/icon.ico" ^
            --clean ^
            --noconfirm ^
            main.py

echo.
echo ===================================
echo  Packaging Complete!
echo  Check the 'dist/FinanceBoard' folder.
echo ===================================
pause
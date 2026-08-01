@echo off
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name DuplicateFinder --collect-all tkinter run.py
pause

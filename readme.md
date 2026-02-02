# ⚡ EasyFix Seagate - Pro Edition
**Developed by Aguinaldo Liesack Baptistini (Hawk Informática)**

EasyFix Seagate is a professional firmware repair tool for Seagate F3 hard drives (like the 7200.12 family). It automates the terminal commands needed to fix the "Busy" (BSY) state and translator issues via USB-TTL.

## ✨ Features
- **Automatic Repair Workflow**: Step-by-step guides for motor spin-down/up.
- **Defect List Management**: Quick G-List and SMART reset.
- **Professional PDF Reports**: Generate service reports for your customers.
- **Built-in Manual**: Instant PDF guide for hardware connection.
- **Live Terminal**: Integrated serial monitor at 38400 baud.

## 🛠 Setup
1. Install dependencies: `pip install customtkinter pyserial fpdf Pillow`
2. Connect your USB-TTL adapter (38400, 8, N, 1).
3. Run: `python repair_hdd.py`

## ⚠️ Disclaimer
This tool is for professional use. Incorrect commands can lead to permanent data loss. Always verify the drive model before executing the 'm' command.
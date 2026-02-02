Seagate F3 Firmware Repair Tool (Pro Edition)
A professional-grade Python utility featuring a modern graphical interface designed to recover Seagate F3 Architecture hard drives suffering from the "Busy" (BSY) state, 0MB capacity detection, or SMART failure locks.

🚀 Overview
This tool provides a bridge between your computer and the Seagate drive's internal terminal (F3 T> prompt). It automates high-risk diagnostic commands and provides visual guidance for physical hardware manipulation (motor isolation).

🛠 Features
Modern UI: Built with CustomTkinter for a sleek, dark-themed professional look.

Automated Repair Steps: One-click buttons for critical commands like Translator Regeneration and SMART Reset.

Real-time Terminal: Integrated serial terminal to send manual commands and monitor drive feedback.

Visual Safety Alerts: Built-in alerts telling you exactly when to remove the PCB insulator.

Automatic Logging: Every session is saved to a .txt file with timestamps for forensic analysis and debugging.

📋 Requirements
Hardware
USB to TTL Adapter: (CP2102, FTDI, or PL2303) set to 3.3V.

Jumper Wires: To connect TX, RX, and GND.

Insulator: A small piece of cardstock or plastic to isolate motor contacts.

Software
Python 3.8+

Required Libraries:

Bash
pip install pyserial customtkinter
📖 How to Use
1. Hardware Preparation
Loosen the screws of the PCB.

Place a small piece of paper (insulator) between the PCB and the motor contacts.

Connect the USB-TTL adapter: TX to RX, RX to TX, and GND to GND.

2. Software Execution
Run the script: python repair_tool.py.

Select the correct COM Port from the dropdown.

Click CONNECT.

3. The Repair Sequence
Step 1 (Ctrl+Z): Wake the drive. You should see F3 T>.

Step 2 (Spin Down): Send the /2 and Z commands. The motor will stop.

The "Magic" Moment: When the program flashes RED, remove the paper insulator and tighten the PCB screws.

Step 3 (Spin Up): Send the U command. The motor should spin up without errors.

Steps 4-6: Clear the G-List and Regenerate the Translator to fix the 0MB issue.

🔍 Troubleshooting: The LED:000000CC Error
The LED:000000CC (F-Level T-Card Lock) is the most common firmware panic. It happens when the drive encounters corrupted SMART logs or G-List entries during boot and "panics," entering a busy state.

How to fix it with this tool:
Isolate the motor (Step 2 logic) so the drive cannot read the corrupted firmware area.

Once in F3 T>, navigate to Level 1 (/1).

Use the Reset SMART or Clear G-List buttons.

Format the Layers (Translator) using the Regenerate button.

Power cycle the drive.

⚠️ Disclaimer
Use this tool at your own risk. Firmware repair involves low-level commands that can permanently erase data or brick the drive if performed incorrectly. Always ensure you have a stable power supply and correct voltage levels on your serial adapter.

🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
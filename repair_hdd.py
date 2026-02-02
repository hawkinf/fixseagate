import tkinter as tk
import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
from tkinter import messagebox
from datetime import datetime

# Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SeagateRepairTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Seagate F3 Firmware Repair - Pro Edition")
        self.geometry("1100x700")
        self.ser = None
        self.log_file = f"repair_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # Main Layout
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel: Connection & About ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SERIAL CONNECTION", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.port_menu = ctk.CTkOptionMenu(self.sidebar, values=self.get_ports())
        self.port_menu.pack(padx=10, pady=5)

        self.connect_btn = ctk.CTkButton(self.sidebar, text="CONNECT", fg_color="green", command=self.toggle_connection)
        self.connect_btn.pack(padx=10, pady=10)

        # --- Seção About (Nova) ---
        self.about_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.about_frame.pack(side="bottom", fill="x", pady=20)
        
        self.about_btn = ctk.CTkButton(self.about_frame, text="About Tool", height=20, 
                                      fg_color="#333333", command=self.show_about)
        self.about_btn.pack(padx=10, pady=5)

        self.log_info = ctk.CTkLabel(self.sidebar, text=f"Log File Active", font=ctk.CTkFont(size=10))
        self.log_info.pack(side="bottom", pady=5)

        # --- Center Panel: Repair Steps ---
        self.step_frame = ctk.CTkFrame(self, width=280, fg_color="#2b2b2b")
        self.step_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        
        ctk.CTkLabel(self.step_frame, text="REPAIR SEQUENCE", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        self.add_step_btn("1. Wake Terminal (Ctrl+Z)", self.send_ctrl_z, "Wait for F3 T> prompt")
        self.add_step_btn("2. Spin Down (Z Command)", lambda: self.auto_command("/2\r\nZ"), "Motor stops. PCB Isolation step.")
        
        self.alert_box = ctk.CTkFrame(self.step_frame, fg_color="#444400", border_width=2, border_color="yellow")
        self.alert_box.pack(padx=10, pady=15, fill="x")
        self.alert_label = ctk.CTkLabel(self.alert_box, text="IDLE", wraplength=200, text_color="yellow")
        self.alert_label.pack(pady=10)

        self.add_step_btn("3. Spin Up (U Command)", lambda: self.auto_command("U"), "Remove insulator before clicking")
        self.add_step_btn("4. Enter Level 1 (/1)", lambda: self.auto_command("/1"), "Access maintenance level")
        self.add_step_btn("5. Clear G-List (N1)", lambda: self.auto_command("N1"), "Safe on most F3 models")
        
        btn_reg = ctk.CTkButton(self.step_frame, text="6. Regenerate (m0,2,2...)", anchor="w", 
                               fg_color="#A83232", hover_color="#7A2424", command=self.confirm_regenerate)
        btn_reg.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text="└ WARNING: Data Destructive", font=ctk.CTkFont(size=10), text_color="#FF6666").pack(padx=10, pady=(0, 5), anchor="w")

        self.add_step_btn("7. Reset SMART", lambda: self.auto_command("/1\r\nN1"), "Recommended for BSY/Health fix")

        # --- Right Panel: Terminal ---
        self.terminal_frame = ctk.CTkFrame(self, corner_radius=0)
        self.terminal_frame.grid(row=0, column=2, sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal_output = ctk.CTkTextbox(self.terminal_frame, font=("Courier New", 12), text_color="#00FF00")
        self.terminal_output.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.command_entry = ctk.CTkEntry(self.terminal_frame, placeholder_text="Manual command...")
        self.command_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.command_entry.bind("<Return>", lambda e: self.send_manual())

    def show_about(self):
        about_text = (
            "Seagate F3 Firmware Repair - Pro Edition\n"
            "Version 1.0.0\n\n"
            "Developed by: Aguinaldo Liesack Baptistini\n"
            "Contact: hawkinf@gmail.com\n\n"
            "Specialized tool for Seagate HDD terminal diagnostics."
        )
        messagebox.showinfo("About This Tool", about_text)

    # ... (restante das funções de conexão, toggle_connection, etc. permanecem iguais)
    
    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports] if ports else ["No Ports"]

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connect_btn.configure(text="CONNECT", fg_color="green")
            self.write_to_log("[SYSTEM] Disconnected.")
        else:
            try:
                self.ser = serial.Serial(self.port_menu.get(), 38400, timeout=0.1)
                self.connect_btn.configure(text="DISCONNECT", fg_color="red")
                self.write_to_log(f"[SYSTEM] Connected to {self.ser.port}")
                threading.Thread(target=self.read_serial, daemon=True).start()
            except Exception as e:
                self.write_to_log(f"[ERROR] {e}")

    def write_to_log(self, text):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_entry = f"{timestamp} {text}\n"
        self.terminal_output.insert(tk.END, log_entry)
        self.terminal_output.see(tk.END)
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def send_ctrl_z(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b'\x1a')
            self.write_to_log("[TX] Sent: Ctrl+Z")

    def auto_command(self, cmd_val):
        if self.ser and self.ser.is_open:
            if "Z" in cmd_val:
                self.alert_box.configure(fg_color="#880000")
                self.alert_label.configure(text="!!! REMOVE INSULATOR NOW !!!", text_color="white")
            elif "U" in cmd_val:
                self.alert_box.configure(fg_color="#004400")
                self.alert_label.configure(text="Motor Spinning...", text_color="white")
            
            self.ser.write((cmd_val + "\r\n").encode())
            self.write_to_log(f"[TX] Sent: {cmd_val}")

    def send_manual(self):
        cmd = self.command_entry.get()
        if cmd:
            self.auto_command(cmd)
            self.command_entry.delete(0, tk.END)

    def read_serial(self):
        while self.ser and self.ser.is_open:
            if self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    if data:
                        self.terminal_output.insert(tk.END, data)
                        self.terminal_output.see(tk.END)
                        with open(self.log_file, "a") as f:
                            f.write(data)
                except:
                    pass

    def confirm_regenerate(self):
        msg = ("WARNING: The 'm' command (Regenerate Translator) is DATA DESTRUCTIVE on modern F3 drives (Rosewood, DM series).\n\n"
               "It may cause a 'Translator Shift', making original data unrecoverable.\n\n"
               "Do you want to proceed anyway?")
        if messagebox.askyesno("Critical Security Warning", msg):
            self.auto_command("m0,2,2,0,0,0,0,22")

    def add_step_btn(self, text, command, hint):
        btn = ctk.CTkButton(self.step_frame, text=text, anchor="w", command=command)
        btn.pack(padx=10, pady=2, fill="x")
        lbl = ctk.CTkLabel(self.step_frame, text=f"└ {hint}", font=ctk.CTkFont(size=10), text_color="gray")
        lbl.pack(padx=10, pady=(0, 5), anchor="w")

if __name__ == "__main__":
    app = SeagateRepairTool()
    app.mainloop()
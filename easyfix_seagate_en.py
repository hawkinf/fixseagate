import os
import sys
import tkinter as tk
import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import base64
from tkinter import messagebox, filedialog
from datetime import datetime
from fpdf import FPDF
from PIL import Image

# --- PyInstaller Resource Path Helper ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Obfuscated Developer Data (Base64) ---
def get_dev_info():
    # Decodes "Aguinaldo Liesack Baptistini" and "hawkinf@gmail.com"
    name_b64 = "QWd1aW5hbGRvIExpZXNhY2sgQmFwdGlzdGluaQ=="
    mail_b64 = "aGF3a2luZkBnbWFpbC5jb20="
    name = base64.b64decode(name_b64).decode('utf-8')
    mail = base64.b64decode(mail_b64).decode('utf-8')
    return f"Developed by {name}\n{mail}"

# Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class EasyFixSeagate(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EasyFix Seagate - Professional Edition")
        self.geometry("1150x900")
        self.ser = None
        
        # Main Layout
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar: Branding & Connection ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo Integration
        try:
            logo_path = resource_path("logo.png")
            logo_img = ctk.CTkImage(light_image=Image.open(logo_path),
                                   dark_image=Image.open(logo_path),
                                   size=(160, 160))
            self.logo_label = ctk.CTkLabel(self.sidebar, image=logo_img, text="")
            self.logo_label.pack(pady=(20, 10))
        except:
            ctk.CTkLabel(self.sidebar, text="EASYFIX SEAGATE", 
                         font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(self.sidebar, text="SERIAL PORT", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.port_menu = ctk.CTkOptionMenu(self.sidebar, values=self.get_ports())
        self.port_menu.pack(padx=10, pady=5)

        self.connect_btn = ctk.CTkButton(self.sidebar, text="CONNECT", fg_color="green", command=self.toggle_connection)
        self.connect_btn.pack(padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="HDD SERIAL NUMBER (S/N)", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.sn_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Enter S/N...")
        self.sn_entry.pack(padx=10, pady=5)

        self.save_btn = ctk.CTkButton(self.sidebar, text="SAVE LOG (.TXT)", fg_color="#4A4A4A", command=self.save_log_to_file)
        self.save_btn.pack(padx=10, pady=5)

        self.pdf_btn = ctk.CTkButton(self.sidebar, text="GENERATE PDF REPORT", fg_color="#A83232", command=self.generate_pdf_report)
        self.pdf_btn.pack(padx=10, pady=5)
        
        self.manual_btn = ctk.CTkButton(self.sidebar, text="HELP / MANUAL", fg_color="#2E5A88", command=self.generate_manual_pdf)
        self.manual_btn.pack(padx=10, pady=5)

        # Obfuscated Footer
        self.about_label = ctk.CTkLabel(self.sidebar, text=get_dev_info(), 
                                        font=ctk.CTkFont(size=10), text_color="gray")
        self.about_label.pack(side="bottom", pady=20)

        # --- Center: Repair Workflow ---
        self.step_frame = ctk.CTkFrame(self, width=300, fg_color="#2b2b2b")
        self.step_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        
        ctk.CTkLabel(self.step_frame, text="REPAIR WORKFLOW", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.add_step_btn("1. Wake Terminal (Ctrl+Z)", self.send_ctrl_z, "Initialize F3 T> prompt")
        
        self.alert_box = ctk.CTkFrame(self.step_frame, fg_color="#444400", border_width=2, border_color="yellow")
        self.alert_box.pack(padx=10, pady=10, fill="x")
        self.alert_label = ctk.CTkLabel(self.alert_box, text="STATUS: READY", wraplength=200, text_color="yellow")
        self.alert_label.pack(pady=10)

        self.add_step_btn("A. Stop Motor (/2 then Z)", lambda: self.auto_command("/2\r\nZ"), "Insert paper insulator now")
        self.add_step_btn("B1. Clear G-List (i4,1,22)", lambda: self.auto_command("/4\r\ni4,1,22"), "Clear bad sector lists")
        self.add_step_btn("B2. Reset SMART (/1 then N1)", lambda: self.auto_command("/1\r\nN1"), "Clear SMART error logs")

        btn_reg = ctk.CTkButton(self.step_frame, text="C. Reconstruct (m0,2,2,,,,,22)", 
                               anchor="w", fg_color="#A83232", hover_color="#7A2424", command=self.confirm_reconstruct)
        btn_reg.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text="└ CRITICAL: Rebuilds translator", font=ctk.CTkFont(size=10), text_color="#FF6666").pack(padx=10, pady=(0, 5), anchor="w")

        self.add_step_btn("D. Spin Up Motor (U)", lambda: self.auto_command("/2\r\nU"), "Remove paper before clicking")

        # --- Right: Live Terminal ---
        self.terminal_frame = ctk.CTkFrame(self, corner_radius=0)
        self.terminal_frame.grid(row=0, column=2, sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal_output = ctk.CTkTextbox(self.terminal_frame, font=("Courier New", 12), text_color="#00FF00")
        self.terminal_output.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.command_entry = ctk.CTkEntry(self.terminal_frame, placeholder_text="Manual command (e.g., /T)...")
        self.command_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.command_entry.bind("<Return>", lambda e: self.send_manual())

        self.clear_btn = ctk.CTkButton(self.terminal_frame, text="CLEAR SCREEN", fg_color="#333333", command=self.clear_terminal)
        self.clear_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="e")

    # --- PDF & File Generation ---
    def generate_manual_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="EasyFix_Quick_Manual.pdf")
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(200, 15, "EasyFix Seagate Connection Guide", ln=True, align='C')
            pdf.ln(10)
            steps = ["1. Connect USB-TTL adapter to PC", 
                     "2. Connect GND-GND, TX-RX, RX-TX between adapter and HDD", 
                     "3. Power HDD using SATA power cable", 
                     "4. If LED:000000CC error occurs, use paper insulator in Step A", 
                     "5. Set Baud Rate: 38400 (Software Default)"]
            pdf.set_font("Arial", size=12)
            for s in steps: pdf.multi_cell(0, 10, s)
            pdf.output(path)
            messagebox.showinfo("Success", "Technical Manual generated successfully!")

    def generate_pdf_report(self):
        sn = self.sn_entry.get().strip() or "UNKNOWN"
        content = self.terminal_output.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"HDD_Report_{sn}.pdf")
        if path:
            pdf = FPDF()
            pdf.add_page()
            try: pdf.image(resource_path("logo.png"), 10, 8, 30)
            except: pass
            pdf.set_font("Arial", 'B', 16); pdf.cell(200, 10, "Hardware Recovery Technical Report", ln=True, align='C')
            pdf.ln(15); pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"HDD S/N: {sn} | Date: {datetime.now().strftime('%m/%d/%Y %H:%M')}", ln=True)
            pdf.ln(5); pdf.set_font("Courier", size=7); pdf.multi_cell(0, 4, content)
            pdf.output(path)
            messagebox.showinfo("Success", "PDF Service Report generated!")

    # --- Serial Control ---
    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close(); self.connect_btn.configure(text="CONNECT", fg_color="green")
        else:
            try:
                self.ser = serial.Serial(self.port_menu.get(), 38400, timeout=0.1)
                self.connect_btn.configure(text="DISCONNECT", fg_color="red")
                threading.Thread(target=self.read_serial, daemon=True).start()
            except: messagebox.showerror("Error", "Failed to open serial port.")

    def read_serial(self):
        while self.ser and self.ser.is_open:
            if self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    self.terminal_output.insert(tk.END, data); self.terminal_output.see(tk.END)
                except: pass

    def auto_command(self, cmd_val):
        if self.ser and self.ser.is_open:
            if "Z" in cmd_val: self.alert_label.configure(text="!!! INSERT INSULATOR NOW !!!")
            elif "U" in cmd_val: self.alert_label.configure(text="MOTOR SPINNING UP...")
            self.ser.write((cmd_val + "\r\n").encode())
        else: messagebox.showwarning("Error", "Please connect the adapter first.")

    def send_ctrl_z(self):
        if self.ser and self.ser.is_open: self.ser.write(b'\x1a')

    def send_manual(self):
        cmd = self.command_entry.get()
        if cmd: self.auto_command(cmd); self.command_entry.delete(0, tk.END)

    def clear_terminal(self): self.terminal_output.delete("1.0", tk.END)

    def save_log_to_file(self):
        sn = self.sn_entry.get().strip() or "LOG"
        content = self.terminal_output.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"EasyFix_Log_{sn}.txt")
        if path:
            with open(path, "w") as f: f.write(content)

    def confirm_reconstruct(self):
        if messagebox.askyesno("Security Alert", "Execute m0,2,2,,,,,22?\nWarning: This may overwrite data if the model is incompatible."):
            self.auto_command("/T\r\nm0,2,2,,,,,22")

    def add_step_btn(self, text, command, hint):
        btn = ctk.CTkButton(self.step_frame, text=text, anchor="w", command=command)
        btn.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text=f"└ {hint}", font=ctk.CTkFont(size=10), text_color="gray").pack(padx=10, pady=(0, 5), anchor="w")

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports] if ports else ["No Ports Found"]

if __name__ == "__main__":
    app = EasyFixSeagate()
    app.mainloop()
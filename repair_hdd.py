import tkinter as tk
import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
from tkinter import messagebox, filedialog
from datetime import datetime
from fpdf import FPDF

# Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class EasyFixSeagate(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EasyFix Seagate - Pro Edition")
        self.geometry("1150x850")
        self.ser = None
        
        # Main Layout
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar: Branding & Connection ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="EASYFIX SEAGATE", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(self.sidebar, text="SERIAL PORT", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.port_menu = ctk.CTkOptionMenu(self.sidebar, values=self.get_ports())
        self.port_menu.pack(padx=10, pady=5)

        self.connect_btn = ctk.CTkButton(self.sidebar, text="CONNECT", fg_color="green", command=self.toggle_connection)
        self.connect_btn.pack(padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="HDD SERIAL NUMBER", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.sn_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Enter S/N...")
        self.sn_entry.pack(padx=10, pady=5)

        self.save_btn = ctk.CTkButton(self.sidebar, text="SAVE TXT LOG", fg_color="#4A4A4A", command=self.save_log_to_file)
        self.save_btn.pack(padx=10, pady=5)

        self.pdf_btn = ctk.CTkButton(self.sidebar, text="EXPORT PDF REPORT", fg_color="#A83232", command=self.generate_pdf_report)
        self.pdf_btn.pack(padx=10, pady=5)
        
        self.manual_btn = ctk.CTkButton(self.sidebar, text="HELP / MANUAL", fg_color="#2E5A88", command=self.generate_manual_pdf)
        self.manual_btn.pack(padx=10, pady=5)

        self.about_label = ctk.CTkLabel(self.sidebar, text="Developed by Aguinaldo Liesack\nhawkinf@gmail.com", 
                                        font=ctk.CTkFont(size=10), text_color="gray")
        self.about_label.pack(side="bottom", pady=20)

        # --- Center: Workflow ---
        self.step_frame = ctk.CTkFrame(self, width=300, fg_color="#2b2b2b")
        self.step_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        
        ctk.CTkLabel(self.step_frame, text="REPAIR WORKFLOW", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.add_step_btn("1. Wake Terminal (Ctrl+Z)", self.send_ctrl_z, "Wake up F3 T> prompt")
        
        self.alert_box = ctk.CTkFrame(self.step_frame, fg_color="#444400", border_width=2, border_color="yellow")
        self.alert_box.pack(padx=10, pady=10, fill="x")
        self.alert_label = ctk.CTkLabel(self.alert_box, text="STATUS: READY", wraplength=200, text_color="yellow")
        self.alert_label.pack(pady=10)

        self.add_step_btn("A. Stop Motor (/2 then Z)", lambda: self.auto_command("/2\r\nZ"), "Use motor insulator now")
        self.add_step_btn("B1. Clear G-List (i4,1,22)", lambda: self.auto_command("/4\r\ni4,1,22"), "Nível 4 - Defect list clear")
        self.add_step_btn("B2. Reset SMART (/1 then N1)", lambda: self.auto_command("/1\r\nN1"), "Clear SMART errors")

        btn_reg = ctk.CTkButton(self.step_frame, text="C. Reconstruct (m0,2,2,,,,,22)", 
                               anchor="w", fg_color="#A83232", hover_color="#7A2424", command=self.confirm_reconstruct)
        btn_reg.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text="└ CRITICAL: Rebuilds translator", font=ctk.CTkFont(size=10), text_color="#FF6666").pack(padx=10, pady=(0, 5), anchor="w")

        self.add_step_btn("D. Spin Up (U)", lambda: self.auto_command("/2\r\nU"), "Restart motor after insulator removal")

        # --- Right: Live Terminal ---
        self.terminal_frame = ctk.CTkFrame(self, corner_radius=0)
        self.terminal_frame.grid(row=0, column=2, sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal_output = ctk.CTkTextbox(self.terminal_frame, font=("Courier New", 12), text_color="#00FF00")
        self.terminal_output.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.command_entry = ctk.CTkEntry(self.terminal_frame, placeholder_text="Manual command entry...")
        self.command_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.command_entry.bind("<Return>", lambda e: self.send_manual())

        self.clear_btn = ctk.CTkButton(self.terminal_frame, text="CLEAR SCREEN", fg_color="#333333", command=self.clear_terminal)
        self.clear_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="e")

    # --- Manual PDF Generation ---
    def generate_manual_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="EasyFix_Seagate_QuickManual.pdf")
        if file_path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(200, 15, "EasyFix Seagate - Quick Setup Guide", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(200, 10, "WARNING: Only proceed if you have experience with electronics!", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            
            steps = [
                "1. Connect the USB-TTL adapter to the PC.",
                "2. Connect GND of the cable to GND of the HDD Diagnostic Pins.",
                "3. Connect RX of the cable to TX of the HDD.",
                "4. Connect TX of the cable to RX of the HDD.",
                "5. Power the HDD using a standard SATA power cable.",
                "6. Open EasyFix Seagate and select the correct COM port.",
                "7. Use Baud Rate: 38400 (Locked in software)."
            ]
            for step in steps:
                pdf.multi_cell(0, 10, step)
            
            pdf.ln(10)
            pdf.set_font("Arial", 'I', 10)
            pdf.multi_cell(0, 10, "Note: If 'LED:000000CC' appears, you MUST use a motor insulator (piece of paper) between the PCB and the motor contacts during Step A.")
            pdf.output(file_path)
            messagebox.showinfo("Success", "Quick Manual PDF generated!")

    # ... (Restante da lógica idêntica à versão anterior)
    def generate_pdf_report(self):
        sn = self.sn_entry.get().strip() or "UNKNOWN_SN"
        content = self.terminal_output.get("1.0", tk.END)
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"EasyFix_Report_{sn}.pdf")
        if file_path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "EasyFix Seagate - Technical Report", ln=True, align='C')
            pdf.set_font("Arial", size=10); pdf.ln(10)
            pdf.cell(200, 10, f"Customer Hardware S/N: {sn}", ln=True)
            pdf.cell(200, 10, f"Repair Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.ln(5); pdf.set_font("Courier", size=7)
            pdf.multi_cell(0, 4, content); pdf.output(file_path)
            messagebox.showinfo("Success", "Professional PDF report created!")

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connect_btn.configure(text="CONNECT", fg_color="green")
        else:
            try:
                self.ser = serial.Serial(self.port_menu.get(), 38400, timeout=0.1)
                self.connect_btn.configure(text="DISCONNECT", fg_color="red")
                threading.Thread(target=self.read_serial, daemon=True).start()
            except: messagebox.showerror("Error", "Check USB-TTL Connection")

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
            elif "U" in cmd_val: self.alert_label.configure(text="MOTOR SPINNING UP")
            self.ser.write((cmd_val + "\r\n").encode())
        else: messagebox.showwarning("Error", "Please connect first.")

    def send_ctrl_z(self):
        if self.ser and self.ser.is_open: self.ser.write(b'\x1a')

    def send_manual(self):
        cmd = self.command_entry.get()
        if cmd: self.auto_command(cmd); self.command_entry.delete(0, tk.END)

    def clear_terminal(self): self.terminal_output.delete("1.0", tk.END)

    def save_log_to_file(self):
        sn = self.sn_entry.get().strip() or "UNKNOWN_SN"
        content = self.terminal_output.get("1.0", tk.END)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"EasyFix_Log_{sn}.txt")
        if file_path:
            with open(file_path, "w") as f: f.write(content)

    def confirm_reconstruct(self):
        if messagebox.askyesno("Security Alert", "Proceed with m0,2,2,,,,,22?"):
            self.auto_command("/T\r\nm0,2,2,,,,,22")

    def add_step_btn(self, text, command, hint):
        btn = ctk.CTkButton(self.step_frame, text=text, anchor="w", command=command)
        btn.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text=f"└ {hint}", font=ctk.CTkFont(size=10), text_color="gray").pack(padx=10, pady=(0, 5), anchor="w")

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports] if ports else ["No Ports"]

if __name__ == "__main__":
    app = EasyFixSeagate()
    app.mainloop()
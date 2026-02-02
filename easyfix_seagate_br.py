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

# --- Helper de Caminhos para o PyInstaller ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Ofuscação de Dados (Base64) ---
# Seus dados estão codificados aqui para não ficarem em texto plano no .exe
def get_dev_info():
    # "Aguinaldo Liesack Baptistini" e "hawkinf@gmail.com"
    name_b64 = "QWd1aW5hbGRvIExpZXNhY2sgQmFwdGlzdGluaQ=="
    mail_b64 = "aGF3a2luZkBnbWFpbC5jb20="
    name = base64.b64decode(name_b64).decode('utf-8')
    mail = base64.b64decode(mail_b64).decode('utf-8')
    return f"Desenvolvido por {name}\n{mail}"

# Configurações de Aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class EasyFixSeagate(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EasyFix Seagate - Edição Profissional")
        self.geometry("1150x900")
        self.ser = None
        
        # Layout Principal
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar: Marca e Conexão ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Integração da Logo
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
        
        ctk.CTkLabel(self.sidebar, text="PORTA SERIAL", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.port_menu = ctk.CTkOptionMenu(self.sidebar, values=self.get_ports())
        self.port_menu.pack(padx=10, pady=5)

        self.connect_btn = ctk.CTkButton(self.sidebar, text="CONECTAR", fg_color="green", command=self.toggle_connection)
        self.connect_btn.pack(padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="SERIAL DO HD (S/N)", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.sn_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Digite o S/N...")
        self.sn_entry.pack(padx=10, pady=5)

        self.save_btn = ctk.CTkButton(self.sidebar, text="SALVAR LOG (.TXT)", fg_color="#4A4A4A", command=self.save_log_to_file)
        self.save_btn.pack(padx=10, pady=5)

        self.pdf_btn = ctk.CTkButton(self.sidebar, text="GERAR RELATÓRIO PDF", fg_color="#A83232", command=self.generate_pdf_report)
        self.pdf_btn.pack(padx=10, pady=5)
        
        self.manual_btn = ctk.CTkButton(self.sidebar, text="AJUDA / MANUAL", fg_color="#2E5A88", command=self.generate_manual_pdf)
        self.manual_btn.pack(padx=10, pady=5)

        # Informações Ofuscadas no Rodapé
        self.about_label = ctk.CTkLabel(self.sidebar, text=get_dev_info(), 
                                        font=ctk.CTkFont(size=10), text_color="gray")
        self.about_label.pack(side="bottom", pady=20)

        # --- Centro: Fluxo de Reparo ---
        self.step_frame = ctk.CTkFrame(self, width=300, fg_color="#2b2b2b")
        self.step_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        
        ctk.CTkLabel(self.step_frame, text="FLUXO DE REPARO", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.add_step_btn("1. Acordar Terminal (Ctrl+Z)", self.send_ctrl_z, "Inicia o prompt F3 T>")
        
        self.alert_box = ctk.CTkFrame(self.step_frame, fg_color="#444400", border_width=2, border_color="yellow")
        self.alert_box.pack(padx=10, pady=10, fill="x")
        self.alert_label = ctk.CTkLabel(self.alert_box, text="STATUS: PRONTO", wraplength=200, text_color="yellow")
        self.alert_label.pack(pady=10)

        self.add_step_btn("A. Parar Motor (/2 then Z)", lambda: self.auto_command("/2\r\nZ"), "Insira o isolante de papel agora")
        self.add_step_btn("B1. Limpar G-List (i4,1,22)", lambda: self.auto_command("/4\r\ni4,1,22"), "Limpa lista de setores ruins")
        self.add_step_btn("B2. Resetar SMART (/1 then N1)", lambda: self.auto_command("/1\r\nN1"), "Limpa logs de erro SMART")

        btn_reg = ctk.CTkButton(self.step_frame, text="C. Reconstruir (m0,2,2,,,,,22)", 
                               anchor="w", fg_color="#A83232", hover_color="#7A2424", command=self.confirm_reconstruct)
        btn_reg.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text="└ CRÍTICO: Reconstrói o tradutor", font=ctk.CTkFont(size=10), text_color="#FF6666").pack(padx=10, pady=(0, 5), anchor="w")

        self.add_step_btn("D. Ligar Motor (U)", lambda: self.auto_command("/2\r\nU"), "Remova o papel antes de clicar")

        # --- Direita: Terminal ao Vivo ---
        self.terminal_frame = ctk.CTkFrame(self, corner_radius=0)
        self.terminal_frame.grid(row=0, column=2, sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_row = 0
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal_output = ctk.CTkTextbox(self.terminal_frame, font=("Courier New", 12), text_color="#00FF00")
        self.terminal_output.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.command_entry = ctk.CTkEntry(self.terminal_frame, placeholder_text="Comando manual (ex: /T)...")
        self.command_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.command_entry.bind("<Return>", lambda e: self.send_manual())

        self.clear_btn = ctk.CTkButton(self.terminal_frame, text="LIMPAR TELA", fg_color="#333333", command=self.clear_terminal)
        self.clear_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="e")

    # --- Métodos de PDF e Arquivos ---
    def generate_manual_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="EasyFix_Manual_Rapido.pdf")
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(200, 15, "Guia de Conexao EasyFix Seagate", ln=True, align='C')
            pdf.ln(10)
            steps = ["1. Conecte o cabo USB-TTL ao Computador", 
                     "2. Conecte GND-GND, TX-RX, RX-TX entre cabo e HD", 
                     "3. Alimente o HD com cabo SATA de energia", 
                     "4. Se aparecer LED:000000CC, use isolante de motor no Passo A", 
                     "5. Utilize Baud Rate: 38400"]
            pdf.set_font("Arial", size=12)
            for s in steps: pdf.multi_cell(0, 10, s)
            pdf.output(path)
            messagebox.showinfo("Sucesso", "Manual gerado com sucesso!")

    def generate_pdf_report(self):
        sn = self.sn_entry.get().strip() or "DESCONHECIDO"
        content = self.terminal_output.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Relatorio_HD_{sn}.pdf")
        if path:
            pdf = FPDF()
            pdf.add_page()
            try: pdf.image(resource_path("logo.png"), 10, 8, 30)
            except: pass
            pdf.set_font("Arial", 'B', 16); pdf.cell(200, 10, "Relatorio de Recuperacao de Hardware", ln=True, align='C')
            pdf.ln(15); pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"S/N do HD: {sn} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.ln(5); pdf.set_font("Courier", size=7); pdf.multi_cell(0, 4, content)
            pdf.output(path)
            messagebox.showinfo("Sucesso", "Relatório PDF gerado!")

    # --- Lógica Serial ---
    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close(); self.connect_btn.configure(text="CONECTAR", fg_color="green")
        else:
            try:
                self.ser = serial.Serial(self.port_menu.get(), 38400, timeout=0.1)
                self.connect_btn.configure(text="DESCONECTAR", fg_color="red")
                threading.Thread(target=self.read_serial, daemon=True).start()
            except: messagebox.showerror("Erro", "Falha ao abrir porta serial.")

    def read_serial(self):
        while self.ser and self.ser.is_open:
            if self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    self.terminal_output.insert(tk.END, data); self.terminal_output.see(tk.END)
                except: pass

    def auto_command(self, cmd_val):
        if self.ser and self.ser.is_open:
            if "Z" in cmd_val: self.alert_label.configure(text="!!! INSIRA O ISOLANTE AGORA !!!")
            elif "U" in cmd_val: self.alert_label.configure(text="MOTOR EM ACELERAÇÃO (SPIN UP)")
            self.ser.write((cmd_val + "\r\n").encode())
        else: messagebox.showwarning("Erro", "Conecte o adaptador primeiro.")

    def send_ctrl_z(self):
        if self.ser and self.ser.is_open: self.ser.write(b'\x1a')

    def send_manual(self):
        cmd = self.command_entry.get()
        if cmd: self.auto_command(cmd); self.command_entry.delete(0, tk.END)

    def clear_terminal(self): self.terminal_output.delete("1.0", tk.END)

    def save_log_to_file(self):
        sn = self.sn_entry.get().strip() or "LOG"
        content = self.terminal_output.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"Log_EasyFix_{sn}.txt")
        if path:
            with open(path, "w") as f: f.write(content)

    def confirm_reconstruct(self):
        if messagebox.askyesno("Alerta de Segurança", "Deseja executar m0,2,2,,,,,22?\nIsso pode apagar dados se o modelo for incompatível."):
            self.auto_command("/T\r\nm0,2,2,,,,,22")

    def add_step_btn(self, text, command, hint):
        btn = ctk.CTkButton(self.step_frame, text=text, anchor="w", command=command)
        btn.pack(padx=10, pady=2, fill="x")
        ctk.CTkLabel(self.step_frame, text=f"└ {hint}", font=ctk.CTkFont(size=10), text_color="gray").pack(padx=10, pady=(0, 5), anchor="w")

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports] if ports else ["Sem Portas"]

if __name__ == "__main__":
    app = EasyFixSeagate()
    app.mainloop()
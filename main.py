import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import re
import multiprocessing
import os
import webbrowser
import socket
from datetime import datetime
import ipaddress
from concurrent.futures import ThreadPoolExecutor

# Kendi yazdığımız modüller
import network_utils
from config_manager import ConfigManager

class UltraNetworkMonitorV5:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Monitor Pro v5 - Premium Edition")
        self.root.geometry("1200x950")

        self.config_mgr = ConfigManager()
        self.dark_mode = True

        # Premium Modern Renk Paleti (Refined Material/Fluent)
        self.colors = {
            "dark": {
                "bg": "#121212",
                "top_bar": "#1e1e1e",
                "fg": "#e0e0e0",
                "row": "#1e1e1e",
                "entry_bg": "#2c2c2c",
                "border": "#333333",
                "menu_bg": "#252525",
                "menu_fg": "#ffffff",
                "accent": "#00e5ff",
                "success": "#00e676",
                "error": "#ff5252",
                "hover": "#2a2d2e"
            },
            "light": {
                "bg": "#f0f2f5",
                "top_bar": "#ffffff",
                "fg": "#1c1e21",
                "row": "#ffffff",
                "entry_bg": "#f0f2f5",
                "border": "#dddfe2",
                "menu_bg": "#ffffff",
                "menu_fg": "#050505",
                "accent": "#1877f2",
                "success": "#42b72a",
                "error": "#fa3e3e",
                "hover": "#f2f3f5"
            }
        }

        self.ip_data = []
        self.active_theme = self.colors["dark"]
        self.max_items = 60

        self.setup_styles()
        self.setup_ui()
        self.update_combo_list()
        self.reset_screen()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Modern Scrollbar
        self.style.configure("Vertical.TScrollbar", gripcount=0,
                        background=self.active_theme["border"], darkcolor=self.active_theme["bg"],
                        lightcolor=self.active_theme["bg"], bordercolor=self.active_theme["bg"],
                        troughcolor=self.active_theme["bg"], arrowsize=1)

        # Modern Combobox
        self.style.configure("TCombobox", fieldbackground=self.active_theme["entry_bg"],
                        background=self.active_theme["entry_bg"], foreground=self.active_theme["fg"],
                        arrowcolor=self.active_theme["accent"], bordercolor=self.active_theme["border"])

    def create_modern_btn(self, parent, text, cmd, bg_color):
        btn = tk.Button(parent, text=text, command=cmd, bg=bg_color, fg="white",
                        font=("Segoe UI", 9, "bold"), bd=0, padx=18, pady=7, cursor="hand2",
                        activebackground=bg_color, relief="flat")

        def on_enter(e):
            btn.config(bg=self.adjust_color(bg_color, 25))
        def on_leave(e):
            btn.config(bg=bg_color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def setup_ui(self):
        self.root.configure(bg=self.active_theme["bg"])

        # Üst Araç Çubuğu
        self.top_bar = tk.Frame(self.root, bg=self.active_theme["top_bar"], pady=15, padx=15,
                                highlightthickness=1, highlightbackground=self.active_theme["border"])
        self.top_bar.pack(fill="x")

        self.create_modern_btn(self.top_bar, "+ Toplu IP", self.bulk_add_ips, "#2ecc71").pack(side="left", padx=5)
        self.create_modern_btn(self.top_bar, "🔍 Ağ Keşfi (Scanner)", self.open_scanner_window, "#3498db").pack(side="left", padx=5)
        self.create_modern_btn(self.top_bar, "💾 Yeni Kaydet", self.save_package, "#5765f2").pack(side="left", padx=5)

        self.package_var = tk.StringVar()
        self.package_combo = ttk.Combobox(self.top_bar, textvariable=self.package_var, state="readonly", width=22)
        self.package_combo.pack(side="left", padx=10)

        self.create_modern_btn(self.top_bar, "Yükle", self.load_selected_package, "#9b59b6").pack(side="left", padx=2)
        self.create_modern_btn(self.top_bar, "Sil", self.delete_selected_package, "#e74c3c").pack(side="left", padx=2)

        self.update_btn = tk.Button(self.top_bar, text="⚠️ Değişiklikleri Kaydet",
                                    command=self.quick_update_package, bg="#e67e22", fg="white",
                                    font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=7, cursor="hand2")

        self.theme_btn = self.create_modern_btn(self.top_bar, "🌓 Mod", self.toggle_theme, "#f39c12")
        self.theme_btn.pack(side="right", padx=10)

        self.create_modern_btn(self.top_bar, "🗑️ Temizle", self.reset_screen, "#c0392b").pack(side="right", padx=5)

        # Akıllı Arama Çubuğu
        search_frame = tk.Frame(self.root, bg=self.active_theme["bg"])
        search_frame.pack(fill="x", padx=20, pady=(15, 5))

        self.search_var = tk.StringVar()
        self.search_ent = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10),
                                   bg=self.active_theme["entry_bg"], fg=self.active_theme["fg"],
                                   insertbackground=self.active_theme["fg"], bd=0, highlightthickness=1,
                                   highlightbackground=self.active_theme["border"])
        self.search_ent.pack(fill="x", ipady=4)

        self.search_ent.insert(0, "IP veya Etiket Ara...")
        self.search_ent.bind("<FocusIn>", self.clear_placeholder)
        self.search_ent.bind("<FocusOut>", self.add_placeholder)
        self.search_var.trace_add("write", lambda *args: self.filter_rows())

        # Ana Gövde
        self.container = tk.Frame(self.root, bg=self.active_theme["bg"])
        self.container.pack(fill="both", expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(self.container, bg=self.active_theme["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.active_theme["bg"])

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Global Mousewheel Binding
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def adjust_color(self, hex_color, amount):
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = max(0, min(255, r + amount))
            g = max(0, min(255, g + amount))
            b = max(0, min(255, b + amount))
            return f'#{r:02x}{g:02x}{b:02x}'
        except: return hex_color

    def clear_placeholder(self, event):
        if self.search_ent.get() == "IP veya Etiket Ara...":
            self.search_ent.delete(0, tk.END)
            self.search_ent.config(highlightbackground=self.active_theme["accent"], highlightcolor=self.active_theme["accent"])

    def add_placeholder(self, event):
        if not self.search_ent.get():
            self.search_ent.insert(0, "IP veya Etiket Ara...")
            self.search_ent.config(highlightbackground=self.active_theme["border"])

    def filter_rows(self):
        query = self.search_var.get().lower()
        if query == "ip veya etiket ara...": query = ""
        visible_data = []
        for d in self.ip_data:
            ip = d["entry"].get().lower()
            tag = d["tag_lbl"].cget("text").lower()
            if query in ip or query in tag:
                visible_data.append(d)
                d["frame"].grid()
            else:
                d["frame"].grid_forget()
        for i, data in enumerate(visible_data):
            row_num, col_num = divmod(i, 2)
            data["frame"].grid(row=row_num, column=col_num, padx=10, pady=6, sticky="nsew")

    def add_ip_row(self, initial_ip="", initial_tag=""):
        if len(self.ip_data) >= self.max_items: return
        row_data = {"active": True, "uptime": 0, "last_status": None, "event_log": []}

        f = tk.Frame(self.scrollable_frame, bg=self.active_theme["row"], pady=10, padx=15,
                     highlightbackground=self.active_theme["border"], highlightthickness=1)

        # Hover Effect
        def on_hover(event):
            f.config(bg=self.active_theme["hover"])
            for w in [mid_frame, tag_lbl, cv, lt, ut]: w.config(bg=self.active_theme["hover"])

        def off_hover(event):
            f.config(bg=self.active_theme["row"])
            for w in [mid_frame, tag_lbl, cv, lt, ut]: w.config(bg=self.active_theme["row"])

        f.bind("<Enter>", on_hover)
        f.bind("<Leave>", off_hover)

        tk.Button(f, text="×", command=lambda: self.fully_delete_row(row_data),
                  bg="#ff7675", fg="white", font=("Arial", 10, "bold"), bd=0, width=3).pack(side="left", padx=(0, 15))

        mid_frame = tk.Frame(f, bg=self.active_theme["row"], width=240, height=54)
        mid_frame.pack(side="left", padx=2, pady=2)
        mid_frame.pack_propagate(False)

        ent = tk.Entry(mid_frame, width=25, font=("Consolas", 11), bg=self.active_theme["entry_bg"],
                       fg=self.active_theme["fg"], insertbackground=self.active_theme["fg"], bd=0,
                       highlightthickness=1, highlightbackground=self.active_theme["border"])
        ent.pack(side="top", fill="x", anchor="nw", pady=(2, 0))
        if initial_ip: ent.insert(0, initial_ip)

        ent.bind("<FocusIn>", lambda e: ent.config(highlightbackground=self.active_theme["accent"], highlightcolor=self.active_theme["accent"]))
        ent.bind("<FocusOut>", lambda e: ent.config(highlightbackground=self.active_theme["border"]))

        tag_lbl = tk.Label(mid_frame, text=initial_tag, font=("Segoe UI", 8, "bold italic"),
                          bg=self.active_theme["row"], fg="#0fbcf9")
        if initial_tag: tag_lbl.pack(side="top", anchor="nw")
        else: tag_lbl.pack_forget()

        for w in [mid_frame, tag_lbl]:
            w.bind("<Enter>", on_hover)
            w.bind("<Leave>", off_hover)

        ent.bind("<KeyRelease>", lambda e: self.check_and_expand())
        ent.bind("<Button-3>", lambda e: self.show_context_menu(e, row_data))
        f.bind("<Button-3>", lambda e: self.show_context_menu(e, row_data))

        cv = tk.Canvas(f, width=14, height=14, bg=self.active_theme["row"], highlightthickness=0)
        li = cv.create_oval(2, 2, 13, 13, fill="gray")
        cv.pack(side="left", padx=12)

        lt = tk.Label(f, text="--ms", fg=self.active_theme["accent"], bg=self.active_theme["row"], width=8, font=("Segoe UI", 9, "bold"))
        lt.pack(side="left")

        ut = tk.Label(f, text="0s", fg=self.active_theme["success"], bg=self.active_theme["row"], width=10, font=("Segoe UI", 9, "bold"))
        ut.pack(side="left")

        for w in [cv, lt, ut]:
            w.bind("<Enter>", on_hover)
            w.bind("<Leave>", off_hover)

        row_data.update({"frame": f, "entry": ent, "tag_lbl": tag_lbl, "light": li, "canvas": cv, "lat_lbl": lt, "up_lbl": ut, "labels": [lt, ut, tag_lbl], "mid_frame": mid_frame})
        self.ip_data.append(row_data)
        self.refresh_grid()
        threading.Thread(target=self.ping_loop, args=(row_data,), daemon=True).start()

    def show_context_menu(self, event, row_data):
        ip = row_data["entry"].get().strip()
        if not ip: return
        current_tag = row_data["tag_lbl"].cget("text")
        menu = tk.Menu(self.root, tearoff=0, bg=self.active_theme["menu_bg"], fg=self.active_theme["menu_fg"], font=("Segoe UI", 10), activebackground=self.active_theme["accent"])

        menu.add_command(label="📌 Etiket Ekle / Düzenle", command=lambda: self.manage_tag(row_data, "add"))
        if current_tag:
            menu.add_command(label="❌ Etiketi Kaldır", command=lambda: self.manage_tag(row_data, "remove"))

        menu.add_separator()
        menu.add_command(label="🕒 Kesinti Geçmişi", command=lambda: self.show_event_log(row_data))
        menu.add_command(label="💻 Bilgisayar Adını Bul (Hostname)", command=lambda: self.find_hostname(row_data))
        menu.add_command(label="🔍 Üretici Bilgisini Bul", command=lambda: self.find_manufacturer(row_data))
        menu.add_command(label="🌐 Web Arayüzünü Aç", command=lambda: self.open_web_interface(ip))

        menu.add_separator()
        menu.add_command(label="⚡ Hızlı Port Tara", command=lambda: self.start_port_scan(ip))
        menu.add_command(label="🚀 TraceRoute Başlat", command=lambda: self.start_traceroute(ip))
        menu.add_command(label="📋 IP Kopyala", command=lambda: self.copy_to_clipboard(ip))
        menu.add_separator()
        menu.add_command(label="🔒 SSH Bağlantısı", command=lambda: network_utils.start_ssh(ip))
        menu.add_command(label="💻 RDP (Uzak Masaüstü)", command=lambda: network_utils.start_rdp(ip))
        menu.tk_popup(event.x_root, event.y_root)

    def manage_tag(self, row_data, action):
        if action == "add":
            new_tag = simpledialog.askstring("Etiket", "IP Açıklaması:", parent=self.root)
            if new_tag:
                row_data["tag_lbl"].config(text=new_tag)
                row_data["tag_lbl"].pack(side="top", anchor="nw")
                self.show_update_warning()
        else:
            row_data["tag_lbl"].config(text="")
            row_data["tag_lbl"].pack_forget()
            self.show_update_warning()

    def find_hostname(self, row_data):
        ip = row_data["entry"].get().strip()
        def resolve():
            hostname = network_utils.resolve_hostname(ip)
            if hostname:
                def update_ui():
                    current_tag = row_data["tag_lbl"].cget("text")
                    current_tag = re.sub(r"\s*\[.*?\]", "", current_tag) # Remove old hostname
                    new_tag = f"{current_tag} [{hostname}]" if current_tag else f"[{hostname}]"
                    row_data["tag_lbl"].config(text=new_tag)
                    row_data["tag_lbl"].pack(side="top", anchor="nw")
                    self.show_update_warning()
                self.root.after(0, update_ui)
        threading.Thread(target=resolve, daemon=True).start()

    def show_event_log(self, row_data):
        ip = row_data["entry"].get().strip()
        tw = tk.Toplevel(self.root)
        tw.title(f"Olay Günlüğü: {ip}")
        tw.geometry("450x400")
        tw.configure(bg=self.active_theme["bg"])
        tk.Label(tw, text=f"Cihaz: {ip}", bg=self.active_theme["bg"], fg=self.active_theme["accent"], font=("Segoe UI", 11, "bold"), pady=15).pack()
        txt = tk.Text(tw, bg=self.active_theme["entry_bg"], fg=self.active_theme["fg"], font=("Consolas", 10), bd=0, padx=10, pady=10)
        txt.pack(fill="both", expand=True, padx=20, pady=10)
        for log in row_data["event_log"]:
            tag = "error" if "❌" in log else "success" if "✅" in log else None
            txt.insert(tk.END, log + "\n", tag)
        txt.tag_config("error", foreground=self.active_theme["error"])
        txt.tag_config("success", foreground=self.active_theme["success"])
        txt.config(state="disabled")

    def find_manufacturer(self, row_data):
        ip = row_data["entry"].get().strip()
        manufacturer = network_utils.get_manufacturer_from_arp(ip)
        if manufacturer:
            current_tag = row_data["tag_lbl"].cget("text")
            current_tag = re.sub(r"\s*\(.*?\)", "", current_tag) # Remove old manufacturer
            new_tag = f"{current_tag} ({manufacturer})" if current_tag else f"({manufacturer})"
            row_data["tag_lbl"].config(text=new_tag)
            row_data["tag_lbl"].pack(side="top", anchor="nw")
            self.show_update_warning()
        else:
            messagebox.showwarning("Uyarı", "Üretici bilgisi bulunamadı (ARP kaydı yok).")

    def open_web_interface(self, ip):
        is_443, is_80 = network_utils.check_web_ports(ip)
        if is_443: webbrowser.open(f"https://{ip}")
        elif is_80: webbrowser.open(f"http://{ip}")
        else: messagebox.showwarning("Hata", f"{ip} için web arayüzü (80/443) kapalı.")

    def open_scanner_window(self):
        sw = tk.Toplevel(self.root)
        sw.title("Gelişmiş Ağ Keşfi")
        sw.geometry("500x320")
        sw.configure(bg=self.active_theme["bg"])

        tk.Label(sw, text="IP Aralığı Belirleyin", bg=self.active_theme["bg"], fg="white", font=("Segoe UI", 12, "bold"), pady=20).pack()

        in_f = tk.Frame(sw, bg=self.active_theme["bg"])
        in_f.pack(pady=10)

        tk.Label(in_f, text="Başlangıç:", bg=self.active_theme["bg"], fg=self.active_theme["fg"]).grid(row=0, column=0, padx=5)
        start_ent = tk.Entry(in_f, bg=self.active_theme["entry_bg"], fg="white", bd=0, highlightthickness=1, highlightbackground=self.active_theme["border"])
        start_ent.grid(row=0, column=1, padx=10, ipady=3)
        start_ent.insert(0, "192.168.1.1")

        tk.Label(in_f, text="Bitiş:", bg=self.active_theme["bg"], fg=self.active_theme["fg"]).grid(row=1, column=0, pady=12)
        end_ent = tk.Entry(in_f, bg=self.active_theme["entry_bg"], fg="white", bd=0, highlightthickness=1, highlightbackground=self.active_theme["border"])
        end_ent.grid(row=1, column=1, padx=10, ipady=3)
        end_ent.insert(0, "192.168.1.254")

        prog_lbl = tk.Label(sw, text="", bg=self.active_theme["bg"], fg=self.active_theme["accent"])
        prog_lbl.pack()

        def start_scan():
            try:
                start_ip = ipaddress.IPv4Address(start_ent.get().strip())
                end_ip = ipaddress.IPv4Address(end_ent.get().strip())
                ips = [str(ipaddress.IPv4Address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
            except:
                messagebox.showerror("Hata", "Geçersiz IP formatı!")
                return

            btn_scan.config(state="disabled", text="Taranıyor...")

            def scan_thread():
                live_ips = []
                total = len(ips)
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = {executor.submit(network_utils.fast_ping, ip): ip for ip in ips}
                    for i, future in enumerate(futures):
                        ip = futures[future]
                        if future.result(): live_ips.append(ip)
                        self.root.after(0, lambda val=i+1: prog_lbl.config(text=f"İlerleme: {val}/{total}"))

                def finalize():
                    sw.destroy()
                    if live_ips:
                        for item in list(self.ip_data):
                            item["active"] = False
                            item["frame"].destroy()
                        self.ip_data = []
                        for ip in live_ips: self.add_ip_row(initial_ip=ip)
                        self.add_ip_row()
                        messagebox.showinfo("Tarama Tamamlandı", f"{len(live_ips)} canlı cihaz bulundu.")
                    else:
                        messagebox.showinfo("Bilgi", "Canlı cihaz bulunamadı.")
                self.root.after(0, finalize)

            threading.Thread(target=scan_thread, daemon=True).start()

        btn_scan = self.create_modern_btn(sw, "Taramayı Başlat", start_scan, "#2ecc71")
        btn_scan.pack(pady=15)

    def start_port_scan(self, ip):
        tw = tk.Toplevel(self.root)
        tw.title(f"Port Tarama: {ip}")
        tw.geometry("400x550")
        tw.configure(bg=self.active_theme["bg"])
        tk.Label(tw, text=f"Hedef: {ip}", bg=self.active_theme["bg"], fg=self.active_theme["accent"], font=("Segoe UI", 11, "bold"), pady=15).pack()
        txt_frame = tk.Frame(tw, bg=self.active_theme["bg"])
        txt_frame.pack(fill="both", expand=True, padx=20, pady=5)
        txt = tk.Text(txt_frame, bg=self.active_theme["entry_bg"], fg=self.active_theme["fg"], font=("Consolas", 10), bd=0, padx=10, pady=10)
        txt.pack(side="left", fill="both", expand=True)
        def run_scan():
            self.root.after(0, lambda: txt.insert(tk.END, "Tarama başlatıldı...\n" + "-"*30 + "\n"))
            results = network_utils.scan_ports(ip)
            def update_results():
                for port, status in results:
                    stat_str = "[AÇIK]" if status else "[KAPALI]"
                    txt.insert(tk.END, f"Port {port}: ")
                    txt.insert(tk.END, stat_str + "\n")
                txt.insert(tk.END, "-"*30 + "\nTarama tamamlandı.")
                txt.config(state="disabled")
            self.root.after(0, update_results)
        threading.Thread(target=run_scan, daemon=True).start()

    def ping_loop(self, row_data):
        while row_data["active"]:
            try:
                if not row_data["active"] or not row_data["entry"].winfo_exists(): break
                ip = row_data["entry"].get().strip()
                if ip:
                    success, latency = network_utils.ping_ip(ip)
                    if not row_data["active"] or not row_data["entry"].winfo_exists(): break
                    ts = datetime.now().strftime("%H:%M:%S")
                    def update_ui(success=success, latency=latency, ts=ts):
                        if success:
                            if row_data["last_status"] is False:
                                row_data["event_log"].append(f"[{ts}] ✅ CİHAZ AKTİF!")
                            row_data["canvas"].itemconfig(row_data["light"], fill=self.active_theme["success"])
                            row_data["lat_lbl"].config(text=f"{latency}ms")
                            row_data["uptime"] += 2
                            row_data["up_lbl"].config(text=f"{row_data['uptime']}s")
                            row_data["last_status"] = True
                        else:
                            if row_data["last_status"] is True:
                                row_data["event_log"].append(f"[{ts}] ❌ BAĞLANTI KOPTU!")
                            row_data["canvas"].itemconfig(row_data["light"], fill=self.active_theme["error"])
                            row_data["lat_lbl"].config(text="Hata")
                            row_data["last_status"] = False
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: row_data["canvas"].itemconfig(row_data["light"], fill="gray"))
                    self.root.after(0, lambda: row_data["lat_lbl"].config(text="--ms"))
            except: break
            time.sleep(2)

    def show_update_warning(self):
        if self.package_var.get(): self.update_btn.pack(side="right", padx=10)

    def quick_update_package(self):
        name = self.package_var.get()
        if name:
            package_data = [{"ip": d["entry"].get().strip(), "tag": d["tag_lbl"].cget("text")}
                            for d in self.ip_data if d["entry"].get().strip()]
            self.config_mgr.save_package(name, package_data)
            self.update_btn.pack_forget()
            messagebox.showinfo("Bilgi", f"'{name}' başarıyla güncellendi.")

    def reset_screen(self):
        for item in list(self.ip_data):
            item["active"] = False
            item["frame"].destroy()
        self.ip_data = []
        for _ in range(12): self.add_ip_row()
        if hasattr(self, 'update_btn'): self.update_btn.pack_forget()

    def refresh_grid(self):
        for i, data in enumerate(self.ip_data):
            row_num, col_num = divmod(i, 2)
            data["frame"].grid(row=row_num, column=col_num, padx=10, pady=6, sticky="nsew")

    def fully_delete_row(self, row_data):
        row_data["active"] = False
        try: row_data["frame"].destroy()
        except: pass
        if row_data in self.ip_data: self.ip_data.remove(row_data)
        self.refresh_grid()
        self.show_update_warning()

    def check_and_expand(self):
        if self.ip_data and self.ip_data[-1]["entry"].get().strip() != "" and len(self.ip_data) < self.max_items:
            self.add_ip_row()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.active_theme = self.colors["dark"] if self.dark_mode else self.colors["light"]
        self.root.configure(bg=self.active_theme["bg"])
        self.top_bar.configure(bg=self.active_theme["top_bar"], highlightbackground=self.active_theme["border"])
        self.canvas.configure(bg=self.active_theme["bg"])
        self.scrollable_frame.configure(bg=self.active_theme["bg"])
        self.search_ent.configure(bg=self.active_theme["entry_bg"], fg=self.active_theme["fg"],
                                  insertbackground=self.active_theme["fg"], highlightbackground=self.active_theme["border"])

        self.setup_styles() # Update ttk styles

        for d in self.ip_data:
            d["frame"].configure(bg=self.active_theme["row"], highlightbackground=self.active_theme["border"])
            d["mid_frame"].configure(bg=self.active_theme["row"])
            d["entry"].configure(bg=self.active_theme["entry_bg"], fg=self.active_theme["fg"],
                                 insertbackground=self.active_theme["fg"], highlightbackground=self.active_theme["border"])
            d["canvas"].configure(bg=self.active_theme["row"])
            d["tag_lbl"].configure(bg=self.active_theme["row"])
            d["lat_lbl"].configure(bg=self.active_theme["row"], fg=self.active_theme["accent"])
            d["up_lbl"].configure(bg=self.active_theme["row"], fg=self.active_theme["success"])

    def bulk_add_ips(self):
        ips = simpledialog.askstring("Toplu IP", "IP'leri yapıştırın:")
        if not ips: return
        for item in list(self.ip_data):
            item["active"] = False
            item["frame"].destroy()
        self.ip_data = []
        ip_list = [ip for ip in re.split(r'[,\s\n]+', ips.strip()) if ip]
        for ip in ip_list:
            if len(self.ip_data) >= self.max_items: break
            self.add_ip_row(initial_ip=ip)
        self.add_ip_row()
        self.show_update_warning()

    def save_package(self):
        name = simpledialog.askstring("Kaydet", "Paket adı:")
        if name:
            package_data = [{"ip": d["entry"].get().strip(), "tag": d["tag_lbl"].cget("text")}
                            for d in self.ip_data if d["entry"].get().strip()]
            self.config_mgr.save_package(name, package_data)
            self.update_combo_list()

    def update_combo_list(self):
        packages = self.config_mgr.load_all_packages()
        self.package_combo['values'] = list(packages.keys())

    def load_selected_package(self):
        name = self.package_var.get()
        if not name: return
        for item in list(self.ip_data):
            item["active"] = False
            item["frame"].destroy()
        self.ip_data = []
        packages = self.config_mgr.load_all_packages()
        package_content = packages.get(name, [])
        for item in package_content:
            if isinstance(item, str): self.add_ip_row(initial_ip=item)
            else: self.add_ip_row(initial_ip=item.get("ip"), initial_tag=item.get("tag"))
        self.add_ip_row()
        self.update_btn.pack_forget()

    def delete_selected_package(self):
        name = self.package_var.get()
        if name and messagebox.askyesno("Soru", f"{name} silinsin mi?"):
            if self.config_mgr.delete_package(name):
                self.package_var.set("")
                self.update_combo_list()

    def copy_to_clipboard(self, ip):
        self.root.clipboard_clear()
        self.root.clipboard_append(ip)
        messagebox.showinfo("Kopyalandı", f"{ip} panoya kopyalandı!")

    def start_traceroute(self, ip):
        tw = tk.Toplevel(self.root)
        tw.title(f"Rota İzleniyor: {ip}")
        tw.geometry("700x500")
        tw.configure(bg="#2d3436")
        info_lbl = tk.Label(tw, text=f"Hedef: {ip}", bg="#2d3436", fg="#f1c40f", font=("Segoe UI", 10, "bold"), pady=10)
        info_lbl.pack()
        txt_frame = tk.Frame(tw, bg="#2d3436")
        txt_frame.pack(fill="both", expand=True, padx=10, pady=10)
        txt = tk.Text(txt_frame, bg="#1e272e", fg="#00dcff", font=("Consolas", 10), padx=10, pady=10, bd=0)
        scroll = ttk.Scrollbar(txt_frame, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        txt.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        def run_trace():
            import subprocess
            proc = subprocess.Popen(["tracert", "-d", ip], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, creationflags=0x08000000)
            try:
                for line in proc.stdout:
                    if not tw.winfo_exists(): break
                    txt.insert(tk.END, line); txt.see(tk.END)
                if tw.winfo_exists(): txt.insert(tk.END, "\n--- Tamamlandı ---")
            except: pass
        threading.Thread(target=run_trace, daemon=True).start()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = UltraNetworkMonitorV5(root)
    root.mainloop()

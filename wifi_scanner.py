import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import re
from datetime import datetime
import ctypes

# Windows HD-DPI ayarı / HD-DPI setting for sharp text
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# netsh çıktısı sistem diline göre değişir (İngilizce / Türkçe)
KEYS_SIGNAL = ("signal", "sinyal")
KEYS_CHANNEL = ("channel", "kanal")
KEYS_BAND = ("band", "bant")

# Sinyal renkleri
COL_STRONG = "#38A169"
COL_GOOD = "#ECC94B"
COL_WEAK = "#ED8936"
COL_CRIT = "#E53E3E"

# ----------------------------------------------------------------------
# DİL / LANGUAGE TABLOSU
# ----------------------------------------------------------------------
TEXTS = {
    "tr": {
        "title": "Canlı Wi-Fi Ağ Analizörü & HD Sinyal Spektrumu",
        "btn_stop": "Durdur",
        "btn_start": "Başlat",
        "btn_log": "Log Kaydet (.txt)",
        "st_live": "Canlı Takip Aktif",
        "st_scanning": "Ağlar taranıyor...",
        "st_paused": "Tarama Durduruldu (Ekran Sabit)",
        "count": "Bulunan Ağ: {n}",
        "col_ssid": "Ağ Adı (SSID)",
        "col_signal": "Sinyal Gücü",
        "col_channel": "Kanal",
        "col_band": "Frekans Bandı",
        "col_bssid": "BSSID (MAC Adresi)",
        "panel": " Canlı Yakınlık & Sinyal Spektrumu — Tüm Ağlar ",
        "waiting": "Tarama verisi bekleniyor...",
        "focused": "Odaklanılan Ağ: {ssid} ({band})",
        "chan_mac": "Kanal: {ch}  |  MAC: {mac}",
        "dist_label": "Mesafe Durumu: {txt}",
        "dist1": "Cihaz Modeme Çok Yakın (Mükemmel Sinyal)",
        "dist2": "Orta Mesafede (İyi Sinyal)",
        "dist3": "Modemden Uzakta (Zayıf Sinyal)",
        "dist4": "Çok Uzakta / Duvar Arkasında (Kritik Sinyal)",
        "leg1": "Güçlü (%75+)",
        "leg2": "İyi (%50-74)",
        "leg3": "Zayıf (%30-49)",
        "leg4": "Kritik (%0-29)",
        "row_info": "Kanal {ch} · {band}",
        "hidden": "Gizli Ağ",
        "warn_title": "Uyarı",
        "warn_nodata": "Kaydedilecek herhangi bir tarama verisi bulunamadı.",
        "save_title": "Wi-Fi Log Dosyasını Kaydet",
        "ft_text": "Metin Dosyası",
        "ft_all": "Tüm Dosyalar",
        "log_head": "--- Wi-Fi TARAMA LOG RAPORU ---",
        "log_date": "Tarih/Saat",
        "log_total": "Toplam Ağ Sayısı",
        "log_ssid": "Ağ Adı (SSID)",
        "log_signal": "Sinyal",
        "log_channel": "Kanal",
        "log_band": "Bant",
        "ok_title": "Başarılı",
        "ok_saved": "Log başarıyla kaydedildi:\n{path}",
        "err_title": "Hata",
        "err_saved": "Dosya kaydedilirken bir hata oluştu:\n{err}",
    },
    "en": {
        "title": "Live Wi-Fi Network Analyzer & HD Signal Spectrum",
        "btn_stop": "Stop",
        "btn_start": "Start",
        "btn_log": "Save Log (.txt)",
        "st_live": "Live Tracking Active",
        "st_scanning": "Scanning networks...",
        "st_paused": "Scan Paused (Display Frozen)",
        "count": "Networks Found: {n}",
        "col_ssid": "Network Name (SSID)",
        "col_signal": "Signal Strength",
        "col_channel": "Channel",
        "col_band": "Frequency Band",
        "col_bssid": "BSSID (MAC Address)",
        "panel": " Live Proximity & Signal Spectrum — All Networks ",
        "waiting": "Waiting for scan data...",
        "focused": "Selected Network: {ssid} ({band})",
        "chan_mac": "Channel: {ch}  |  MAC: {mac}",
        "dist_label": "Proximity: {txt}",
        "dist1": "Very Close to the Router (Excellent Signal)",
        "dist2": "Medium Distance (Good Signal)",
        "dist3": "Far from the Router (Weak Signal)",
        "dist4": "Very Far / Behind Walls (Critical Signal)",
        "leg1": "Strong (75%+)",
        "leg2": "Good (50-74%)",
        "leg3": "Weak (30-49%)",
        "leg4": "Critical (0-29%)",
        "row_info": "Channel {ch} · {band}",
        "hidden": "Hidden Network",
        "warn_title": "Warning",
        "warn_nodata": "There is no scan data to save.",
        "save_title": "Save Wi-Fi Log File",
        "ft_text": "Text File",
        "ft_all": "All Files",
        "log_head": "--- Wi-Fi SCAN LOG REPORT ---",
        "log_date": "Date/Time",
        "log_total": "Total Networks",
        "log_ssid": "Network Name (SSID)",
        "log_signal": "Signal",
        "log_channel": "Channel",
        "log_band": "Band",
        "ok_title": "Success",
        "ok_saved": "Log saved successfully:\n{path}",
        "err_title": "Error",
        "err_saved": "An error occurred while saving the file:\n{err}",
    },
}


def signal_color(v):
    if v >= 75:
        return COL_STRONG
    if v >= 50:
        return COL_GOOD
    if v >= 30:
        return COL_WEAK
    return COL_CRIT


def signal_to_int(text):
    try:
        return int(str(text).replace("%", "").strip())
    except ValueError:
        return 0


class WifiScannerGUI:
    def __init__(self, root):
        self.root = root
        self.lang = "tr"
        self.status_key = "st_live"
        self.last_networks_data = []
        self.selected_bssid = None
        self.row_bssids = []

        self.root.geometry("1100x860")
        self.root.configure(background="#F5F6F8")

        self.font_title = ("Segoe UI", 11, "bold")
        self.font_normal = ("Segoe UI", 10)
        self.font_small = ("Segoe UI", 9, "italic")
        self.font_row = ("Segoe UI", 10)
        self.font_info = ("Segoe UI", 9)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=28, font=self.font_normal,
                             background="#FFFFFF", fieldbackground="#FFFFFF")
        self.style.configure("Treeview.Heading", font=self.font_title,
                             background="#EAECEF", foreground="#2D3748")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)

        # ---------------- Menü çubuğu / Menu bar ----------------
        self.lang_var = tk.StringVar(value=self.lang)
        self.menubar = tk.Menu(root)
        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self.lang_menu.add_radiobutton(label="Türkçe", value="tr",
                                       variable=self.lang_var, command=self.change_language)
        self.lang_menu.add_radiobutton(label="English", value="en",
                                       variable=self.lang_var, command=self.change_language)
        self.menubar.add_cascade(label="Dil / Language", menu=self.lang_menu)
        root.config(menu=self.menubar)

        # ---------------- Üst kontrol paneli ----------------
        self.top_frame = tk.Frame(root, bg="#F5F6F8", padx=15, pady=10)
        self.top_frame.pack(fill=tk.X)

        self.is_scanning = True
        self.btn_toggle = ttk.Button(self.top_frame, command=self.toggle_scan)
        self.btn_toggle.pack(side=tk.LEFT, padx=5)

        self.btn_log = ttk.Button(self.top_frame, command=self.save_log)
        self.btn_log.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.top_frame, font=self.font_small,
                                     bg="#F5F6F8", fg="#4A5568")
        self.status_label.pack(side=tk.LEFT, padx=20)

        self.count_label = tk.Label(self.top_frame, font=self.font_title,
                                    bg="#F5F6F8", fg="#2D3748")
        self.count_label.pack(side=tk.RIGHT)

        # ---------------- Üst/alt bölme (sürüklenebilir) ----------------
        self.paned = tk.PanedWindow(root, orient=tk.VERTICAL, sashwidth=8,
                                    sashrelief=tk.FLAT, bg="#F5F6F8", bd=0)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        # ÜST: Tablo
        self.table_frame = tk.Frame(self.paned, bg="#FFFFFF", bd=1, relief=tk.SOLID)

        columns = ("ssid", "signal", "channel", "band", "bssid")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=6)

        self.tree.column("ssid", width=280, anchor=tk.W)
        self.tree.column("signal", width=110, anchor=tk.CENTER)
        self.tree.column("channel", width=90, anchor=tk.CENTER)
        self.tree.column("band", width=120, anchor=tk.CENTER)
        self.tree.column("bssid", width=180, anchor=tk.CENTER)

        self.scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("excellent", background="#E6F4EA", foreground="#137333")
        self.tree.tag_configure("good", background="#FEF7E0", foreground="#B06000")
        self.tree.tag_configure("fair", background="#FCE8E6", foreground="#C5221F")
        self.tree.tag_configure("poor", background="#F5F5F5", foreground="#5F6368")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_network)

        self.paned.add(self.table_frame, minsize=150, stretch="always")

        # ALT: Spektrum paneli
        self.visual_frame = tk.LabelFrame(
            self.paned, font=self.font_title, bg="#FFFFFF", fg="#1A73E8",
            bd=1, relief=tk.SOLID, padx=12, pady=10)

        self.detail_canvas = tk.Canvas(self.visual_frame, height=125, bg="#1E1E24",
                                       highlightthickness=0)
        self.detail_canvas.pack(fill=tk.X)

        self.row_h = 28
        list_wrap = tk.Frame(self.visual_frame, bg="#1E1E24")
        list_wrap.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.list_canvas = tk.Canvas(list_wrap, bg="#1E1E24", highlightthickness=0,
                                     yscrollincrement=self.row_h)
        self.list_scroll = ttk.Scrollbar(list_wrap, orient=tk.VERTICAL,
                                         command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=self.list_scroll.set)
        self.list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.list_canvas.bind("<Button-1>", self.on_list_click)
        self.list_canvas.bind("<Enter>", lambda e: self.list_canvas.bind_all("<MouseWheel>", self.on_mousewheel))
        self.list_canvas.bind("<Leave>", lambda e: self.list_canvas.unbind_all("<MouseWheel>"))
        self.list_canvas.bind("<Configure>", lambda e: self.draw_spectrum(self.last_networks_data))
        self.detail_canvas.bind("<Configure>", lambda e: self.draw_spectrum(self.last_networks_data))

        self.paned.add(self.visual_frame, minsize=300, stretch="always")
        self.root.after(200, lambda: self.paned.sash_place(0, 0, 230))

        # Tüm yazıları seçili dile göre ayarla
        self.apply_language()

        # Thread
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.scan_thread = threading.Thread(target=self.live_scan_loop, daemon=True)
        self.scan_thread.start()

    # ------------------------------------------------------------------
    # DİL İŞLEMLERİ / LANGUAGE HANDLING
    # ------------------------------------------------------------------
    def t(self, key, **kw):
        text = TEXTS[self.lang][key]
        return text.format(**kw) if kw else text

    def ssid_text(self, ssid):
        return ssid if ssid else self.t("hidden")

    def change_language(self):
        self.lang = self.lang_var.get()
        self.apply_language()
        # Tablo ve grafikleri yeni dille yeniden çiz
        self.update_ui(self.last_networks_data)

    def apply_language(self):
        self.root.title(self.t("title"))
        self.btn_toggle.config(text=self.t("btn_stop") if self.is_scanning else self.t("btn_start"))
        self.btn_log.config(text=self.t("btn_log"))
        self.status_label.config(text=self.t(self.status_key))
        self.count_label.config(text=self.t("count", n=len(self.last_networks_data)))
        self.visual_frame.config(text=self.t("panel"))

        self.tree.heading("ssid", text=self.t("col_ssid"))
        self.tree.heading("signal", text=self.t("col_signal"))
        self.tree.heading("channel", text=self.t("col_channel"))
        self.tree.heading("band", text=self.t("col_band"))
        self.tree.heading("bssid", text=self.t("col_bssid"))

        self.draw_spectrum(self.last_networks_data)

    # ------------------------------------------------------------------
    def run_netsh(self):
        """netsh çıktısını UTF-8 olarak al (Türkçe karakterler bozulmasın)."""
        creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            raw = subprocess.check_output(
                "chcp 65001 >nul & netsh wlan show networks mode=bssid",
                shell=True, creationflags=creation)
            return raw.decode("utf-8", errors="replace")
        except Exception:
            pass
        try:
            raw = subprocess.check_output(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                creationflags=creation)
            return raw.decode("cp857", errors="replace")
        except Exception:
            return ""

    def parse_wifi_data(self):
        sonuc = self.run_netsh()
        if not sonuc:
            return []

        parsed_networks = []
        current_ssid = ""          # boş = gizli ağ (gösterirken dile göre çevrilir)
        current_bssid = None
        current_signal = "N/A"
        current_channel = "N/A"
        current_band = "N/A"

        def flush():
            if current_bssid:
                parsed_networks.append(
                    (current_ssid, current_signal, current_channel, current_band, current_bssid))

        for line in sonuc.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            key_l = key.lower()

            if re.match(r"^ssid\s+\d+$", key_l):
                flush()
                current_bssid = None
                current_ssid = value
                current_signal = current_channel = current_band = "N/A"
            elif key_l.startswith("bssid"):
                flush()
                current_bssid = value
                current_signal = current_channel = current_band = "N/A"
            elif key_l in KEYS_SIGNAL:
                current_signal = value
            elif key_l in KEYS_CHANNEL:
                current_channel = value.split("(")[0].strip()
            elif key_l in KEYS_BAND:
                current_band = value

        flush()
        parsed_networks.sort(key=lambda item: signal_to_int(item[1]), reverse=True)
        return parsed_networks

    # ------------------------------------------------------------------
    def set_status(self, key):
        self.status_key = key
        self.root.after(0, lambda: self.status_label.config(text=self.t(self.status_key)))

    def live_scan_loop(self):
        while self.running:
            if self.is_scanning:
                self.set_status("st_scanning")
                networks = self.parse_wifi_data()
                self.last_networks_data = networks
                if self.running:
                    self.root.after(0, self.update_ui, networks)
                self.set_status("st_live")
            else:
                self.set_status("st_paused")
            time.sleep(1.5)

    def update_ui(self, networks):
        for item in self.tree.get_children():
            self.tree.delete(item)

        reselect = None
        for net in networks:
            ssid, signal, channel, band, bssid = net
            sig_val = signal_to_int(signal)
            if sig_val >= 75:
                color_tag = "excellent"
            elif sig_val >= 50:
                color_tag = "good"
            elif sig_val >= 30:
                color_tag = "fair"
            else:
                color_tag = "poor"

            iid = self.tree.insert("", tk.END,
                                   values=(self.ssid_text(ssid), signal, channel, band, bssid),
                                   tags=(color_tag,))
            if bssid == self.selected_bssid:
                reselect = iid

        if reselect:
            self.tree.selection_set(reselect)

        self.count_label.config(text=self.t("count", n=len(networks)))
        self.draw_spectrum(networks)

    def on_select_network(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item[0], "values")
            if values:
                self.selected_bssid = str(values[4])
                self.draw_spectrum(self.last_networks_data)

    # ------------------------------------------------------------------
    def get_target(self, networks):
        if self.selected_bssid:
            for net in networks:
                if net[4] == self.selected_bssid:
                    return net
        return networks[0] if networks else None

    def draw_spectrum(self, networks):
        target = self.get_target(networks)
        self.draw_details(target)
        self.draw_list(networks, target)

    def draw_details(self, target):
        c = self.detail_canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 100:
            w = 1000

        if not target:
            c.create_text(w / 2, 60, text=self.t("waiting"),
                          fill="#FFFFFF", font=self.font_title)
            return

        ssid, signal, channel, band, bssid = target
        sig_val = signal_to_int(signal)

        c.create_text(20, 22, anchor=tk.W,
                      text=self.t("focused", ssid=self.ssid_text(ssid), band=band),
                      fill="#1A73E8", font=("Segoe UI", 12, "bold"))
        c.create_text(20, 46, anchor=tk.W,
                      text=self.t("chan_mac", ch=channel, mac=bssid),
                      fill="#A0AEC0", font=self.font_normal)

        if sig_val >= 75:
            mesafe = self.t("dist1")
        elif sig_val >= 50:
            mesafe = self.t("dist2")
        elif sig_val >= 30:
            mesafe = self.t("dist3")
        else:
            mesafe = self.t("dist4")

        col = signal_color(sig_val)
        c.create_oval(20, 66, 32, 78, fill=col, outline="")
        c.create_text(42, 72, anchor=tk.W, text=self.t("dist_label", txt=mesafe),
                      fill="#FFFFFF", font=self.font_normal)

        lx = 20
        legend = [(COL_STRONG, "leg1"), (COL_GOOD, "leg2"),
                  (COL_WEAK, "leg3"), (COL_CRIT, "leg4")]
        for lc, lk in legend:
            c.create_rectangle(lx, 98, lx + 12, 110, fill=lc, outline="")
            c.create_text(lx + 18, 104, anchor=tk.W, text=self.t(lk),
                          fill="#A0AEC0", font=self.font_info)
            lx += 150

        c.create_text(w - 25, 55, anchor=tk.E, text=f"%{sig_val}", fill=col,
                      font=("Segoe UI", 36, "bold"))

    def draw_list(self, networks, target):
        c = self.list_canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 100:
            w = 1000

        self.row_bssids = []
        if not networks:
            return

        name_x = 15
        info_x = 270
        bar_x = 430
        pct_w = 60
        bar_end = max(bar_x + 60, w - pct_w - 15)
        bar_w = bar_end - bar_x
        rh = self.row_h

        for i, net in enumerate(networks):
            ssid, signal, channel, band, bssid = net
            sig_val = signal_to_int(signal)
            col = signal_color(sig_val)
            y = i * rh
            cy = y + rh / 2
            self.row_bssids.append(bssid)

            is_sel = target is not None and bssid == target[4]
            if is_sel:
                c.create_rectangle(3, y + 1, w - 3, y + rh - 1, fill="#2A3350",
                                   outline="#1A73E8", width=1)

            shown = self.ssid_text(ssid)
            name = shown if len(shown) <= 30 else shown[:29] + "…"
            c.create_text(name_x, cy, anchor=tk.W, text=name, fill="#FFFFFF",
                          font=("Segoe UI", 10, "bold") if is_sel else self.font_row)
            c.create_text(info_x, cy, anchor=tk.W,
                          text=self.t("row_info", ch=channel, band=band),
                          fill="#A0AEC0", font=self.font_info)

            c.create_rectangle(bar_x, y + 8, bar_end, y + rh - 8, fill="#2D3748", outline="")
            fill_w = bar_w * sig_val / 100
            if fill_w > 0:
                c.create_rectangle(bar_x, y + 8, bar_x + fill_w, y + rh - 8, fill=col, outline="")

            c.create_text(w - 15, cy, anchor=tk.E, text=f"%{sig_val}", fill=col,
                          font=("Segoe UI", 10, "bold"))

        c.configure(scrollregion=(0, 0, w, len(networks) * rh + 4))

    def on_list_click(self, event):
        y = self.list_canvas.canvasy(event.y)
        idx = int(y // self.row_h)
        if 0 <= idx < len(self.row_bssids):
            bssid = self.row_bssids[idx]
            self.selected_bssid = bssid
            for iid in self.tree.get_children():
                vals = self.tree.item(iid, "values")
                if vals and str(vals[4]) == bssid:
                    self.tree.selection_set(iid)
                    self.tree.see(iid)
                    break
            self.draw_spectrum(self.last_networks_data)

    def on_mousewheel(self, event):
        self.list_canvas.yview_scroll(int(-event.delta / 120), "units")

    # ------------------------------------------------------------------
    def toggle_scan(self):
        if self.is_scanning:
            self.is_scanning = False
            self.btn_toggle.config(text=self.t("btn_start"))
        else:
            self.is_scanning = True
            self.btn_toggle.config(text=self.t("btn_stop"))

    def save_log(self):
        if not self.last_networks_data:
            messagebox.showwarning(self.t("warn_title"), self.t("warn_nodata"))
            return

        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        varsayilan_ad = f"wifi_log_{zaman_damgasi}.txt"

        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[(self.t("ft_text"), "*.txt"), (self.t("ft_all"), "*.*")],
            initialfile=varsayilan_ad,
            title=self.t("save_title"))

        if dosya_yolu:
            try:
                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(self.t("log_head") + "\n")
                    f.write(f"{self.t('log_date')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{self.t('log_total')}: {len(self.last_networks_data)}\n")
                    f.write("-" * 85 + "\n")
                    f.write(f"{self.t('log_ssid'):<30} | {self.t('log_signal'):<8} | "
                            f"{self.t('log_channel'):<8} | {self.t('log_band'):<8} | BSSID\n")
                    f.write("-" * 85 + "\n")
                    for net in self.last_networks_data:
                        f.write(f"{self.ssid_text(net[0]):<30} | {net[1]:<8} | "
                                f"{net[2]:<8} | {net[3]:<8} | {net[4]}\n")
                messagebox.showinfo(self.t("ok_title"), self.t("ok_saved", path=dosya_yolu))
            except Exception as e:
                messagebox.showerror(self.t("err_title"), self.t("err_saved", err=e))

    def on_closing(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WifiScannerGUI(root)
    root.mainloop()

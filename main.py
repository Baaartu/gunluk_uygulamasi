import hashlib
import json
import os
import datetime
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext, font

# --- Configuration & Theme ---
CONFIG_FILE = "config.json"
JOURNAL_FILE = "journal.txt"

class Theme:
    BG_COLOR = "#2C3E50"        # Dark Blue/Gray
    SIDEBAR_BG = "#34495E"      # Sidebar Color
    FG_COLOR = "#ECF0F1"        # Off-white
    ACCENT_COLOR = "#3498DB"    # Bright Blue
    SUCCESS_COLOR = "#27AE60"   # Green
    WARNING_COLOR = "#F39C12"   # Orange (Edit Mode)
    ERROR_COLOR = "#E74C3C"     # Red
    INPUT_BG = "#FBFCFC"        # Light Gray/White
    INPUT_FG = "#2C3E50"        # Dark Text
    LIST_SELECT_BG = "#3498DB"  # Selection Color
    FONT_FAMILY = "Segoe UI"    # Modern Windows Font
    
# --- Utils ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class EntryParser:
    """Parses and handles journal file operations."""
    SEPARATOR_PATTERN = r"--- (\d{2,4}-\d{1,2}-\d{1,2}) ---"

    @staticmethod
    def get_entries():
        if not os.path.exists(JOURNAL_FILE):
            return []
        
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        parts = re.split(EntryParser.SEPARATOR_PATTERN, content)
        entries = []
        start_idx = 1 if len(parts) > 1 and parts[0].strip() == "" else 1
        
        for i in range(start_idx, len(parts), 2):
            if i + 1 < len(parts):
                date_str = parts[i]
                entry_content = parts[i+1].strip()
                entries.append({"date": date_str, "content": entry_content})
        
        # Return newest first
        return entries[::-1]

    @staticmethod
    def save_all_entries(entries):
        """Rewrites the entire journal file with the provided entries."""
        # Entries are newest first in memory, but we want to write oldest first 
        # (or newest first, but consistent). Let's stick to appending style structure.
        # Original file was likely appended: Entry 1, Entry 2...
        # So we should write them in reverse order of our list (which is New->Old)
        # to keep chronological order in file if desired, OR just write them as is.
        # To match the parser logic (which expects separators), we just write them.
        
        try:
            with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
                # Write in chronological order (Oldest -> Newest) so new appends make sense
                for entry in reversed(entries):
                    f.write(f"\n\n--- {entry['date']} ---\n")
                    f.write(entry['content'])
            return True
        except OSError:
            return False

class JournalApp:
    def __init__(self, root):
        self.root = root
        self.current_entry_index = None # Track which entry is being edited
        self.setup_window()
        self.check_status()

    def setup_window(self):
        self.root.title("Kişisel Günlük Profesyonel")
        self.root.configure(bg=Theme.BG_COLOR)
        
        width, height = 900, 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 500)

        self.main_container = tk.Frame(self.root, bg=Theme.BG_COLOR)
        self.main_container.pack(expand=True, fill="both")

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def check_status(self):
        if not os.path.exists(CONFIG_FILE):
            self.show_setup_screen()
        else:
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    json.load(f)
                self.show_login_screen()
            except (json.JSONDecodeError, OSError):
                messagebox.showerror("Kritik Hata", "Yapılandırma dosyası bozuk.")
                try:
                    os.remove(CONFIG_FILE)
                    self.show_setup_screen()
                except: pass

    # --- UI Helpers ---
    def create_button(self, parent, text, command, bg_color=Theme.ACCENT_COLOR):
        btn = tk.Button(parent, text=text, command=command,
                        bg=bg_color, fg="white", font=(Theme.FONT_FAMILY, 10, "bold"),
                        activebackground=Theme.FG_COLOR, activeforeground=Theme.BG_COLOR,
                        relief="flat", borderwidth=0, padx=15, pady=8, cursor="hand2")
        return btn

    def create_entry_input(self, parent, show=None):
        return tk.Entry(parent, show=show, font=(Theme.FONT_FAMILY, 12),
                        bg=Theme.SIDEBAR_BG, fg=Theme.FG_COLOR,
                        insertbackground="white", relief="flat", borderwidth=5)

    # --- Screens ---
    def show_setup_screen(self):
        self.clear_container()
        frame = tk.Frame(self.main_container, bg=Theme.BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Hoşgeldiniz", font=(Theme.FONT_FAMILY, 24, "bold"), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=10)
        
        # Şifre Alanı
        tk.Label(frame, text="Yeni bir şifre belirleyin:", font=(Theme.FONT_FAMILY, 12), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=5)
        self.pwd_entry = self.create_entry_input(frame, show="*")
        self.pwd_entry.pack(pady=5, fill="x")
        
        # Güvenlik Sorusu Alanı
        tk.Label(frame, text="Güvenlik Sorusu (Şifre kurtarmak için):", font=(Theme.FONT_FAMILY, 12), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=(15, 5))
        self.security_q_entry = self.create_entry_input(frame)
        self.security_q_entry.pack(pady=5, fill="x")
        self.security_q_entry.insert(0, "İlk evcil hayvanınızın adı?") # Varsayılan soru örneği

        # Güvenlik Cevabı Alanı
        tk.Label(frame, text="Cevabınız:", font=(Theme.FONT_FAMILY, 12), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=5)
        self.security_a_entry = self.create_entry_input(frame)
        self.security_a_entry.pack(pady=5, fill="x")

        self.pwd_entry.focus()
        
        self.create_button(frame, "Kurulumu Tamamla", self.save_setup, Theme.SUCCESS_COLOR).pack(pady=20, fill="x")

    def show_login_screen(self):
        self.clear_container()
        frame = tk.Frame(self.main_container, bg=Theme.BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Giriş Yap", font=(Theme.FONT_FAMILY, 24, "bold"), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=20)
        
        self.login_entry = self.create_entry_input(frame, show="*")
        self.login_entry.pack(pady=10, fill="x")
        self.login_entry.bind('<Return>', lambda event: self.verify_login())
        self.login_entry.focus()
        
        self.create_button(frame, "Giriş", self.verify_login).pack(pady=10, fill="x")

        # Şifremi Unuttum Butonu
        tk.Button(frame, text="Şifremi Unuttum", command=self.recover_password,
                  bg=Theme.BG_COLOR, fg=Theme.ACCENT_COLOR, bd=0, cursor="hand2",
                  font=(Theme.FONT_FAMILY, 10, "underline")).pack(pady=5)

    def show_journal_screen(self):
        self.clear_container()
        
        # Sidebar
        sidebar = tk.Frame(self.main_container, bg=Theme.SIDEBAR_BG, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="GEÇMİŞ NOTLAR", bg=Theme.SIDEBAR_BG, fg="#95a5a6", 
                 font=(Theme.FONT_FAMILY, 10, "bold"), anchor="w").pack(fill="x", padx=15, pady=(20, 10))

        self.history_listbox = tk.Listbox(sidebar, bg=Theme.SIDEBAR_BG, fg=Theme.FG_COLOR,
                                          font=(Theme.FONT_FAMILY, 11), bd=0, highlightthickness=0,
                                          selectbackground=Theme.LIST_SELECT_BG, activestyle="none")
        self.history_listbox.pack(expand=True, fill="both", padx=10)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_entry_select)

        self.create_button(sidebar, "+ Yeni Not", self.prepare_new_entry, Theme.SUCCESS_COLOR).pack(fill="x", padx=10, pady=20)

        # Content Area
        content_area = tk.Frame(self.main_container, bg=Theme.BG_COLOR)
        content_area.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # Footer Actions (Pack First to ensure visibility at bottom)
        self.action_frame = tk.Frame(content_area, bg=Theme.BG_COLOR)
        self.action_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Header (Pack Second at top)
        self.header_frame = tk.Frame(content_area, bg=Theme.BG_COLOR)
        self.header_frame.pack(side="top", fill="x", pady=(0, 10))
        
        self.title_label = tk.Label(self.header_frame, text="Yeni Giriş", font=(Theme.FONT_FAMILY, 18, "bold"), 
                                    bg=Theme.BG_COLOR, fg=Theme.FG_COLOR)
        self.title_label.pack(side="left")

        # Header Actions
        self.header_btn_frame = tk.Frame(self.header_frame, bg=Theme.BG_COLOR)
        self.header_btn_frame.pack(side="right")

        tk.Button(self.header_btn_frame, text="Hakkında", command=self.show_about_dialog,
                  bg=Theme.BG_COLOR, fg=Theme.FG_COLOR, bd=0, cursor="hand2",
                  font=(Theme.FONT_FAMILY, 9)).pack(side="left", padx=5)

        tk.Button(self.header_btn_frame, text="Şifre Değiştir", command=self.show_change_password_dialog,
                  bg=Theme.BG_COLOR, fg=Theme.FG_COLOR, bd=0, cursor="hand2",
                  font=(Theme.FONT_FAMILY, 9)).pack(side="left", padx=5)

        tk.Button(self.header_btn_frame, text="Çıkış Yap", command=self.show_login_screen,
                  bg=Theme.BG_COLOR, fg=Theme.ERROR_COLOR, bd=0, cursor="hand2",
                  font=(Theme.FONT_FAMILY, 10, "bold")).pack(side="left", padx=5)

        # Text Editor (Pack Last to fill remaining space)
        self.journal_text = scrolledtext.ScrolledText(content_area, 
                                                    font=(Theme.FONT_FAMILY, 12),
                                                    bg=Theme.INPUT_BG, fg=Theme.INPUT_FG,
                                                    insertbackground="black", relief="flat", padx=15, pady=15)
        self.journal_text.pack(side="top", expand=True, fill="both")

        self.status_label = tk.Label(self.action_frame, text="Hazır", bg=Theme.BG_COLOR, fg="#95a5a6", font=(Theme.FONT_FAMILY, 9))
        self.status_label.pack(side="left")

        # Action Buttons
        self.btn_frame = tk.Frame(self.action_frame, bg=Theme.BG_COLOR)
        self.btn_frame.pack(side="right")

        self.edit_btn = self.create_button(self.btn_frame, "✏️ Düzenle", self.enable_edit_mode, Theme.WARNING_COLOR)
        self.delete_btn = self.create_button(self.btn_frame, "🗑️ Sil", self.delete_entry, Theme.ERROR_COLOR)
        self.save_btn = self.create_button(self.btn_frame, "💾 Kaydet", self.save_entry, Theme.ACCENT_COLOR)
        self.update_btn = self.create_button(self.btn_frame, "💾 Güncelle", self.update_entry, Theme.SUCCESS_COLOR)

        # Initial Load
        self.refresh_history()
        self.prepare_new_entry()

    # --- Actions ---
    def save_setup(self):
        pwd = self.pwd_entry.get()
        sq = self.security_q_entry.get()
        sa = self.security_a_entry.get()

        if not pwd.strip() or not sq.strip() or not sa.strip():
            messagebox.showwarning("Uyarı", "Tüm alanları doldurun!", parent=self.root)
            return

        try:
            config_data = {
                "password_hash": hash_password(pwd),
                "security_question": sq,
                "security_answer_hash": hash_password(sa.lower().strip()) # Cevapları küçük harf ve boşluksuz kaydedelim
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f)
            self.show_login_screen()
        except OSError as e:
            messagebox.showerror("Hata", f"Hata: {e}", parent=self.root)

    def verify_login(self):
        pwd = self.login_entry.get()
        if not pwd: return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            stored_hash = data.get("password_hash")
            
            if stored_hash == hash_password(pwd):
                self.show_journal_screen()
            else:
                messagebox.showerror("Hata", "Yanlış şifre!", parent=self.root)
                self.login_entry.delete(0, tk.END)
        except Exception:
            pass

    def recover_password(self):
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Hata", "Yapılandırma dosyası bulunamadı.", parent=self.root)
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            question = data.get("security_question")
            if not question:
                messagebox.showwarning("Bilgi", "Bu hesap için güvenlik sorusu ayarlanmamış.", parent=self.root)
                return
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Şifre Kurtarma")
            dialog.geometry("400x250")
            dialog.configure(bg=Theme.BG_COLOR)
            
            # Ortala
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 250) // 2
            dialog.geometry(f"+{x}+{y}")
            
            tk.Label(dialog, text="Güvenlik Sorusu:", font=(Theme.FONT_FAMILY, 10, "bold"), bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=(20, 5))
            tk.Label(dialog, text=question, font=(Theme.FONT_FAMILY, 11), bg=Theme.BG_COLOR, fg=Theme.ACCENT_COLOR, wraplength=350).pack(pady=5)
            
            tk.Label(dialog, text="Cevabınız:", bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=5)
            answer_entry = tk.Entry(dialog, font=(Theme.FONT_FAMILY, 11))
            answer_entry.pack(pady=5)
            answer_entry.focus()
            
            def check_answer():
                ans = answer_entry.get().lower().strip()
                if hash_password(ans) == data.get("security_answer_hash"):
                    dialog.destroy()
                    self.show_reset_password_dialog(data) # Mevcut datayı geçirelim ki diğer veriler kaybolmasın (eğer varsa)
                else:
                    messagebox.showerror("Hata", "Yanlış cevap!", parent=dialog)

            tk.Button(dialog, text="Doğrula", command=check_answer, bg=Theme.SUCCESS_COLOR, fg="white").pack(pady=20)

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okuma hatası: {e}", parent=self.root)

    def show_reset_password_dialog(self, current_data):
        dialog = tk.Toplevel(self.root)
        dialog.title("Yeni Şifre Belirle")
        dialog.geometry("300x250")
        dialog.configure(bg=Theme.BG_COLOR)
        
        # Ortala
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 250) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Yeni Şifre:", bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=(20, 5))
        new_pwd = tk.Entry(dialog, show="*", font=(Theme.FONT_FAMILY, 11))
        new_pwd.pack(pady=5)
        new_pwd.focus()
        
        tk.Label(dialog, text="Yeni Şifre (Tekrar):", bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=5)
        confirm_pwd = tk.Entry(dialog, show="*", font=(Theme.FONT_FAMILY, 11))
        confirm_pwd.pack(pady=5)
        
        def save_new_reset():
            p1 = new_pwd.get()
            p2 = confirm_pwd.get()
            
            if not p1 or not p2:
                messagebox.showwarning("Hata", "Alanlar boş bırakılamaz.", parent=dialog)
                return
            
            if p1 != p2:
                messagebox.showwarning("Hata", "Şifreler eşleşmiyor.", parent=dialog)
                return
                
            try:
                # Sadece şifreyi güncelle, soru ve cevabı koru
                current_data["password_hash"] = hash_password(p1)
                
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(current_data, f)
                
                messagebox.showinfo("Başarılı", "Şifreniz sıfırlandı. Yeni şifrenizle giriş yapabilirsiniz.", parent=dialog)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", f"Kaydedilemedi: {e}", parent=dialog)
        
        tk.Button(dialog, text="Şifreyi Güncelle", command=save_new_reset, bg=Theme.SUCCESS_COLOR, fg="white").pack(pady=20)

    def refresh_history(self):
        self.history_listbox.delete(0, tk.END)
        self.entries = EntryParser.get_entries()
        for entry in self.entries:
            self.history_listbox.insert(tk.END, f"📅 {entry['date']}")

    def on_entry_select(self, event):
        selection = self.history_listbox.curselection()
        if not selection: return
        
        self.current_entry_index = selection[0]
        entry = self.entries[self.current_entry_index]
        
        # View Mode State
        self.title_label.config(text=f"Kayıt: {entry['date']}")
        self.journal_text.config(state="normal")
        self.journal_text.delete("1.0", tk.END)
        self.journal_text.insert("1.0", entry['content'])
        self.journal_text.config(state="disabled", bg=Theme.INPUT_BG)
        
        # Button State: Show Edit/Delete, Hide Save/Update
        self.save_btn.pack_forget()
        self.update_btn.pack_forget()
        self.delete_btn.pack(side="right", padx=(0, 10))
        self.edit_btn.pack(side="right")
        
        self.status_label.config(text="Geçmiş görüntüleniyor (Düzenlemek için butona basın)", fg="#F39C12")

    def enable_edit_mode(self):
        self.journal_text.config(state="normal", bg="#FFF8DC") # Slightly different color for edit
        self.edit_btn.pack_forget()
        self.delete_btn.pack_forget() # Hide delete while editing
        self.update_btn.pack(side="right")
        self.status_label.config(text="✏️ Düzenleme modu aktif", fg=Theme.WARNING_COLOR)

    def prepare_new_entry(self):
        # Refresh entries to ensure we have the latest data
        self.entries = EntryParser.get_entries() # Ensure self.entries is up to date if not already
        
        today_storage = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if entry already exists for today
        found_index = None
        for i, entry in enumerate(self.entries):
            if entry['date'] == today_storage:
                found_index = i
                break
        
        if found_index is not None:
            # Entry exists - Open it instead of new
            self.current_entry_index = found_index
            
            # Select in listbox
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(found_index)
            self.history_listbox.see(found_index)
            
            # Simulate selection event to trigger View Mode
            self.on_entry_select(None)
            
            self.status_label.config(text="Bugünün kaydı mevcut. Düzenlemek için 'Düzenle'ye basın.", fg=Theme.WARNING_COLOR)
            return

        # No entry exists, proceed with new
        self.current_entry_index = None
        today_display = datetime.datetime.now().strftime("%d-%m-%Y")
        self.title_label.config(text=f"Yeni Giriş ({today_display})")
        
        self.journal_text.config(state="normal", bg=Theme.INPUT_BG)
        self.journal_text.delete("1.0", tk.END)
        self.history_listbox.selection_clear(0, tk.END)
        
        # Button State: Show Save, Hide Edit/Update/Delete
        self.edit_btn.pack_forget()
        self.update_btn.pack_forget()
        self.delete_btn.pack_forget()
        if not self.save_btn.winfo_ismapped():
            self.save_btn.pack(side="right")
        
        self.status_label.config(text="Yazmaya başlayın...", fg="#95a5a6")

    def save_entry(self):
        content = self.journal_text.get("1.0", tk.END).strip()
        if not content:
            self.status_label.config(text="⚠️ Boş içerik kaydedilmedi", fg=Theme.ERROR_COLOR)
            return

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Double check duplication guard
        for entry in self.entries:
            if entry['date'] == current_date:
                messagebox.showwarning("Uyarı", "Bugün için zaten bir kayıt var. Lütfen listeden seçip düzenleyin.")
                self.prepare_new_entry() # Redirect to existing
                return

        try:
            with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n\n--- {current_date} ---\n")
                f.write(content)
            
            messagebox.showinfo("Başarılı", "Not kaydedildi.", parent=self.root)
            self.refresh_history()
            self.prepare_new_entry()
        except OSError as e:
            messagebox.showerror("Hata", f"Yazma hatası: {e}")

    def update_entry(self):
        if self.current_entry_index is None: return
        
        content = self.journal_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Uyarı", "İçerik boş olamaz.")
            return

        # Update data in memory
        self.entries[self.current_entry_index]['content'] = content
        
        # Rewrite file
        if EntryParser.save_all_entries(self.entries):
            messagebox.showinfo("Başarılı", "Not güncellendi.", parent=self.root)
            self.refresh_history()
            # Reselect the updated entry to stay in view mode or reset
            self.prepare_new_entry()
            self.status_label.config(text="✅ Güncelleme başarılı", fg=Theme.SUCCESS_COLOR)
        else:
            messagebox.showerror("Hata", "Dosya güncellenemedi.", parent=self.root)

    def delete_entry(self):
        if self.current_entry_index is None: return

        entry = self.entries[self.current_entry_index]
        confirm = messagebox.askyesno("Kayıt Sil", f"{entry['date']} tarihli kaydı silmek istediğinize emin misiniz?", parent=self.root)
        
        if confirm:
            # Remove from list
            del self.entries[self.current_entry_index]
            
            # Rewrite file
            if EntryParser.save_all_entries(self.entries):
                messagebox.showinfo("Başarılı", "Kayıt silindi.", parent=self.root)
                self.refresh_history()
                self.prepare_new_entry()
                self.status_label.config(text="🗑️ Kayıt silindi", fg=Theme.ERROR_COLOR)
            else:
                messagebox.showerror("Hata", "Dosya güncellenemedi (Silme başarısız).", parent=self.root)

    def show_about_dialog(self):
        about_text = (
            "Kişisel Günlük Uygulaması v1.0\n\n"
            "Geliştirici: Bartu Öz\n"
            "E-posta: bartuoz222@gmail.com\n\n"
            "Tüm Hakları Saklıdır © 2026\n"
            "Bu yazılımın izinsiz kopyalanması, dağıtılması ve ticari amaçla kullanılması yasaktır."
        )
        messagebox.showinfo("Hakkında", about_text, parent=self.root)

    def show_change_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Şifre Değiştir")
        dialog.geometry("300x250")
        dialog.configure(bg=Theme.BG_COLOR)
        
        tk.Label(dialog, text="Yeni Şifre:", bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=(20, 5))
        new_pwd = tk.Entry(dialog, show="*", font=(Theme.FONT_FAMILY, 11))
        new_pwd.pack(pady=5)
        
        tk.Label(dialog, text="Yeni Şifre (Tekrar):", bg=Theme.BG_COLOR, fg=Theme.FG_COLOR).pack(pady=5)
        confirm_pwd = tk.Entry(dialog, show="*", font=(Theme.FONT_FAMILY, 11))
        confirm_pwd.pack(pady=5)
        
        def save_new():
            p1 = new_pwd.get()
            p2 = confirm_pwd.get()
            
            if not p1 or not p2:
                messagebox.showwarning("Hata", "Alanlar boş bırakılamaz.", parent=dialog)
                return
            
            if p1 != p2:
                messagebox.showwarning("Hata", "Şifreler eşleşmiyor.", parent=dialog)
                return
                
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump({"password_hash": hash_password(p1)}, f)
                messagebox.showinfo("Başarılı", "Şifre güncellendi.", parent=dialog)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", f"Kaydedilemedi: {e}", parent=dialog)
        
        tk.Button(dialog, text="Kaydet", command=save_new, bg=Theme.SUCCESS_COLOR, fg="white").pack(pady=20)

def main():
    try:
        root = tk.Tk()
        app = JournalApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Başlatma hatası: {e}")

if __name__ == "__main__":
    main()

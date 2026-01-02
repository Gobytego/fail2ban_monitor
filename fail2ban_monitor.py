import customtkinter as ctk
import paramiko
import threading
import os
import json
from pathlib import Path
from tkinter import filedialog, messagebox

# --- DYNAMIC CONFIGURATION PATH ---
CONFIG_DIR = Path.home() / ".config" / "gobytego" / "fail2ban_monitor"
CONFIG_FILE = CONFIG_DIR / "servers.json"

def ensure_config_exists():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_FILE

def load_config():
    path = ensure_config_exists()
    if path.exists():
        with open(path, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_config(servers):
    path = ensure_config_exists()
    with open(path, "w") as f:
        json.dump(servers, f, indent=4)

class Fail2BanMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gobytego Fail2Ban Monitor")
        self.geometry("1200x850")
        ctk.set_appearance_mode("dark")
        
        self.servers = load_config()
        self.textboxes = {}
        
        # Main Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        # 1. Create Server Tabs (First)
        for server in self.servers:
            self.add_server_tab(server)
            
        # 2. Create Settings Tab (Last)
        self.setup_settings_tab()
        
        # 3. Focus logic
        if self.servers:
            self.tabview.set(self.servers[0]["name"])
        else:
            self.tabview.set("Settings")

    def setup_settings_tab(self):
        tab = self.tabview.add("Settings")
        self.edit_mode = False
        self.edit_index = None

        ctk.CTkLabel(tab, text="Manage Servers", font=("Arial", 22, "bold")).pack(pady=10)
        ctk.CTkLabel(tab, text=f"Config: {CONFIG_FILE}", font=("Arial", 10), text_color="gray").pack()
        
        self.name_entry = ctk.CTkEntry(tab, placeholder_text="Display Name", width=400)
        self.name_entry.pack(pady=5)
        self.host_entry = ctk.CTkEntry(tab, placeholder_text="Hostname/IP", width=400)
        self.host_entry.pack(pady=5)
        self.user_entry = ctk.CTkEntry(tab, placeholder_text="User", width=400)
        self.user_entry.insert(0, "adam")
        self.user_entry.pack(pady=5)
        self.path_entry = ctk.CTkEntry(tab, placeholder_text="Log Path", width=400)
        self.path_entry.insert(0, "/var/log/fail2ban.log")
        self.path_entry.pack(pady=5)
        self.key_entry = ctk.CTkEntry(tab, placeholder_text="Key Path", width=400)
        self.key_entry.insert(0, os.path.expanduser("~/.ssh/id_rsa"))
        self.key_entry.pack(pady=5)
        
        self.submit_btn = ctk.CTkButton(tab, text="Save Server", command=self.save_server_data)
        self.submit_btn.pack(pady=15)

        self.server_list_frame = ctk.CTkScrollableFrame(tab, width=600, height=200)
        self.server_list_frame.pack(pady=10)
        self.refresh_server_list()

    def add_server_tab(self, server):
        tab = self.tabview.add(server["name"])
        
        # Action Bar with Save Button
        action_bar = ctk.CTkFrame(tab)
        action_bar.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(action_bar, text="Save Log to .txt", width=120,
                     command=lambda s=server["name"]: self.save_log_dialog(s)).pack(side="left", padx=5)

        log_box = ctk.CTkTextbox(tab, font=("Courier", 13), wrap="word")
        log_box.pack(padx=10, pady=10, fill="both", expand=True)
        log_box.tag_config("ban_alert", foreground="#FF4B4B")
        self.textboxes[server["name"]] = log_box

        threading.Thread(target=self.ssh_tail_thread, args=(server, log_box), daemon=True).start()

    def save_log_dialog(self, server_name):
        content = self.textboxes[server_name].get("1.0", "end-1c")
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"fail2ban_{server_name}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Choose Save Location"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Log saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def ssh_tail_thread(self, server, textbox):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            key_path = server.get("key", os.path.expanduser("~/.ssh/id_rsa"))
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
            client.connect(server["host"], username=server["user"], pkey=private_key)
            
            log_path = server.get("path", "/var/log/fail2ban.log")
            cmd = f"stdbuf -oL tail -n 500 -f {log_path}"
            stdin, stdout, stderr = client.exec_command(cmd)

            for line in iter(stdout.readline, ""):
                if "Ban" in line: textbox.insert("end", line, "ban_alert")
                else: textbox.insert("end", line)
                textbox.see("end")
        except Exception as e:
            textbox.insert("end", f"\n[!] ERROR: {str(e)}\n", "ban_alert")

    def refresh_server_list(self):
        for widget in self.server_list_frame.winfo_children(): widget.destroy()
        for i, server in enumerate(self.servers):
            frame = ctk.CTkFrame(self.server_list_frame)
            frame.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(frame, text=f"{server['name']} ({server['host']})", width=300, anchor="w").pack(side="left", padx=10)
            ctk.CTkButton(frame, text="Edit", width=60, fg_color="gray", command=lambda idx=i: self.load_server_for_edit(idx)).pack(side="left", padx=2)
            ctk.CTkButton(frame, text="Delete", width=60, fg_color="#922b21", command=lambda idx=i: self.delete_server(idx)).pack(side="left", padx=2)

    def load_server_for_edit(self, index):
        s = self.servers[index]; self.edit_mode = True; self.edit_index = index
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, s["name"])
        self.host_entry.delete(0, "end"); self.host_entry.insert(0, s["host"])
        self.user_entry.delete(0, "end"); self.user_entry.insert(0, s.get("user", "adam"))
        self.path_entry.delete(0, "end"); self.path_entry.insert(0, s.get("path", "/var/log/fail2ban.log"))
        self.key_entry.delete(0, "end");  self.key_entry.insert(0, s.get("key", ""))
        self.submit_btn.configure(text="Update Server (Restart Required)")

    def delete_server(self, index):
        if messagebox.askyesno("Confirm", f"Delete {self.servers[index]['name']}?"):
            self.servers.pop(index); save_config(self.servers); self.refresh_server_list()

    def save_server_data(self):
        data = {"name": self.name_entry.get(), "host": self.host_entry.get(), "user": self.user_entry.get(), "path": self.path_entry.get(), "key": self.key_entry.get()}
        if self.edit_mode: self.servers[self.edit_index] = data
        else: self.servers.append(data)
        save_config(self.servers); messagebox.showinfo("Success", "Saved. Restart App."); self.refresh_server_list()

if __name__ == "__main__":
    app = Fail2BanMonitor()
    app.mainloop()

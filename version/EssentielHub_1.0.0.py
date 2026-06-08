import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests

CATALOGUE_URL = "https://raw.githubusercontent.com/Cloclo44400/EssentielHub/refs/heads/main/catalogue.json"
HUB_FOLDER = os.path.join(os.path.expanduser("~"), "EssentielHub")

class HubFactoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EssentielHub - Sélecteur de Version")
        self.root.geometry("650x480")
        self.root.minsize(500, 400)
        self.root.configure(bg="#f0f0f0")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=10)
        self.style.configure("TCombobox", font=("Segoe UI", 11))
        self.style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background="#f0f0f0")
        self.style.configure("Status.TLabel", font=("Segoe UI", 10, "italic"), background="#f0f0f0", foreground="#555555")
        self.style.configure("Green.Horizontal.TProgressbar", troughcolor="#e0e0e0", background="#27ae60")

        self.apps_dict = {}
        self.current_config = {}
        self.shortcut_var = tk.BooleanVar(value=True)

        self.create_widgets()
        threading.Thread(target=self.load_catalogue, daemon=True).start()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=30)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="🐍 EssentielHub", style="Title.TLabel").pack(anchor="center", pady=(0, 20))

        app_frame = ttk.Frame(main_frame)
        app_frame.pack(fill="x", pady=5)
        ttk.Label(app_frame, text="Application :").pack(side="left", padx=(0, 10))
        self.app_combobox = ttk.Combobox(app_frame, state="disabled", width=35)
        self.app_combobox.pack(side="left", fill="x", expand=True)
        self.app_combobox.set("Chargement du catalogue...")
        self.app_combobox.bind("<<ComboboxSelected>>", self.on_app_selected)

        ver_frame = ttk.Frame(main_frame)
        ver_frame.pack(fill="x", pady=5)
        ttk.Label(ver_frame, text="Version :").pack(side="left", padx=(0, 10))
        self.version_combobox = ttk.Combobox(ver_frame, state="disabled", width=20)
        self.version_combobox.pack(side="left")
        self.version_combobox.set("Choisissez d'abord une app")

        self.shortcut_check = ttk.Checkbutton(main_frame, text="Créer un raccourci sur le bureau",
                                              variable=self.shortcut_var)
        self.shortcut_check.pack(pady=5, anchor="w")

        self.btn_launch = ttk.Button(main_frame, text="🚀 Compiler / Installer",
                                     command=self.start_build_process, state="disabled")
        self.btn_launch.pack(pady=10)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=5)

        self.status_label = ttk.Label(progress_frame, text="Prêt", style="Status.TLabel")
        self.status_label.pack(anchor="w", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                            length=400, mode="determinate",
                                            style="Green.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=5)

        self.percent_label = ttk.Label(progress_frame, text="0 %", font=("Segoe UI", 10), background="#f0f0f0")
        self.percent_label.pack(anchor="e")

    def update_progress(self, value, message):
        self.root.after(0, self._update_progress_impl, value, message)

    def _update_progress_impl(self, value, message):
        self.progress_bar["value"] = value
        self.percent_label.config(text=f"{int(value)} %")
        self.status_label.config(text=message)

    def set_ui_state(self, app_state=None, version_state=None, btn_state=None, progress_enabled=True):
        self.root.after(0, self._set_ui_state_impl, app_state, version_state, btn_state, progress_enabled)

    def _set_ui_state_impl(self, app_state, version_state, btn_state, progress_enabled):
        if app_state is not None:
            self.app_combobox.config(state=app_state)
        if version_state is not None:
            self.version_combobox.config(state=version_state)
        if btn_state is not None:
            self.btn_launch.config(state=btn_state)
        if not progress_enabled:
            self.progress_bar["value"] = 0
            self.percent_label.config(text="0 %")
            self.status_label.config(text="Prêt")

    def show_messagebox(self, msg_type, title, message):
        self.root.after(0, lambda: self._show_messagebox_impl(msg_type, title, message))

    def _show_messagebox_impl(self, msg_type, title, message):
        if msg_type == "info":
            messagebox.showinfo(title, message)
        elif msg_type == "error":
            messagebox.showerror(title, message)

    def load_catalogue(self):
        try:
            response = requests.get(CATALOGUE_URL, timeout=10)
            if response.status_code == 200:
                catalogue = response.json()
                if not isinstance(catalogue, list):
                    self.update_progress(0, "Format du catalogue invalide")
                    return

                self.apps_dict.clear()
                for app in catalogue:
                    name = app.get("name") or app.get("app_name")
                    url = app.get("url") or app.get("config_url")
                    if name and url:
                        self.apps_dict[name] = url

                apps_list = list(self.apps_dict.keys())
                def update():
                    self.app_combobox['values'] = apps_list
                    if apps_list:
                        self.app_combobox.config(state="readonly")
                        self.app_combobox.current(0)
                        self.on_app_selected(None)
                    else:
                        self.app_combobox.set("Catalogue vide")
                    self.update_progress(0, "Catalogue chargé")
                self.root.after(0, update)
            else:
                self.update_progress(0, f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.update_progress(0, f"Erreur de connexion : {e}")

    def on_app_selected(self, event):
        selected_app = self.app_combobox.get()
        json_url = self.apps_dict.get(selected_app)
        if json_url:
            self.version_combobox.config(state="disabled")
            self.version_combobox.set("Chargement...")
            self.btn_launch.config(state="disabled")
            threading.Thread(target=self.load_app_versions, args=(json_url,), daemon=True).start()

    def load_app_versions(self, json_url):
        try:
            response = requests.get(json_url, timeout=10)
            if response.status_code == 200:
                self.current_config = response.json()
                versions_list = []
                if "versions" in self.current_config:
                    versions_list = list(self.current_config["versions"].keys())
                elif "version" in self.current_config:
                    versions_list = [self.current_config["version"]]

                def update():
                    if versions_list:
                        self.version_combobox['values'] = versions_list
                        self.version_combobox.config(state="readonly")
                        self.version_combobox.current(0)
                        self.btn_launch.config(state="normal")
                        self.update_progress(0, "Versions chargées")
                    else:
                        self.version_combobox.set("Aucune version trouvée")
                self.root.after(0, update)
            else:
                self.version_combobox.set("Erreur de chargement")
        except Exception as e:
            self.version_combobox.set("Erreur de connexion")

    def start_build_process(self):
        selected_version = self.version_combobox.get()
        if not selected_version:
            return
        self.set_ui_state(app_state="disabled", version_state="disabled", btn_state="disabled", progress_enabled=True)
        self.update_progress(0, "Initialisation...")
        threading.Thread(target=self.build_worker, args=(selected_version,), daemon=True).start()

    def build_worker(self, selected_version):
        script_temp = "temp_main.py"
        try:
            app_name = self.current_config.get("app_name", "AppSansNom")
            if "versions" in self.current_config and selected_version in self.current_config["versions"]:
                ver_data = self.current_config["versions"][selected_version]
                main_script_url = ver_data.get("main_script_url")
                dependencies = ver_data.get("dependencies", [])
            else:
                main_script_url = self.current_config.get("main_script_url")
                dependencies = self.current_config.get("dependencies", [])

            if not main_script_url:
                self.update_progress(0, "Erreur : URL du script manquante")
                self.show_messagebox("error", "Erreur", "URL du script introuvable.")
                return

            # 1. Téléchargement (0 → 30 %)
            self.update_progress(10, "Téléchargement du code source...")
            code_response = requests.get(main_script_url, timeout=10)
            if code_response.status_code != 200:
                self.update_progress(0, "Échec du téléchargement")
                self.show_messagebox("error", "Erreur", "Impossible de télécharger le script.")
                return
            with open(script_temp, "w", encoding="utf-8") as f:
                f.write(code_response.text)
            self.update_progress(30, "Code source téléchargé")

            # Vérification PyInstaller
            try:
                subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.update_progress(0, "PyInstaller manquant")
                self.show_messagebox("error", "Erreur", "PyInstaller n'est pas installé.\nLancez 'pip install pyinstaller'.")
                return
            self.update_progress(40, "PyInstaller détecté")

            # 2. Dépendances (40 → 60 %)
            if dependencies:
                self.update_progress(40, f"Installation de {len(dependencies)} dépendance(s)...")
                for idx, lib in enumerate(dependencies):
                    self.update_progress(40 + int((idx + 1) / len(dependencies) * 20),
                                         f"Installation de {lib}...")
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", lib, "--user"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                        )
                    except subprocess.CalledProcessError:
                        self.update_progress(60, f"Avertissement : échec de {lib}")
            else:
                self.update_progress(60, "Aucune dépendance")

            # 3. Création du dossier EssentielHub
            os.makedirs(HUB_FOLDER, exist_ok=True)

            # 4. Compilation avec --noconsole (→ pas de fenêtre noire)
            final_exe_name = f"{app_name}_{selected_version.replace('.', '_')}"
            self.update_progress(65, "Compilation en cours (mode GUI)...")
            commande = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--noconsole",      # ← AJOUTÉ ICI : supprime la console
                f"--name={final_exe_name}",
                "--clean",
                f"--distpath={HUB_FOLDER}",
                script_temp
            ]
            process = subprocess.Popen(commande, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, errors="ignore")
            line_count = 0
            for line in process.stdout:
                line_count += 1
                if line_count % 10 == 0:
                    current = min(90, 65 + line_count // 2)
                    self.update_progress(current, "Compilation en cours...")
            process.wait()

            if process.returncode != 0:
                self.update_progress(0, "Échec de la compilation")
                self.show_messagebox("error", "Échec", "La compilation a échoué.")
                return

            exe_path = os.path.join(HUB_FOLDER, f"{final_exe_name}.exe")
            self.update_progress(95, "Compilation réussie !")

            # 5. Raccourci bureau
            if self.shortcut_var.get():
                self.update_progress(97, "Création du raccourci...")
                try:
                    self.create_desktop_shortcut(exe_path, final_exe_name)
                    self.update_progress(100, "Raccourci créé sur le bureau")
                except Exception as e:
                    self.update_progress(100, "Raccourci non créé (voir détails)")
                    self.show_messagebox("error", "Raccourci", f"Impossible de créer le raccourci : {e}")
            else:
                self.update_progress(100, "Terminé")

            msg = f"{final_exe_name}.exe a été placé dans :\n{HUB_FOLDER}"
            if self.shortcut_var.get():
                msg += "\nUn raccourci a été créé sur le bureau."
            self.show_messagebox("info", "Succès", msg)

        except Exception as e:
            self.update_progress(0, f"Erreur : {e}")
            self.show_messagebox("error", "Erreur", str(e))
        finally:
            if os.path.exists(script_temp):
                try: os.remove(script_temp)
                except: pass
            self.set_ui_state(app_state="readonly", version_state="readonly", btn_state="normal", progress_enabled=False)

    def create_desktop_shortcut(self, target_path, shortcut_name):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut_path = os.path.join(desktop, f"{shortcut_name}.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.IconLocation = target_path
            shortcut.save()
        except ImportError:
            url_path = os.path.join(desktop, f"{shortcut_name}.url")
            with open(url_path, "w") as f:
                f.write("[InternetShortcut]\n")
                f.write(f"URL=file:///{target_path.replace(os.sep, '/')}\n")
                f.write("IconIndex=0\n")
        except Exception as e:
            raise e

if __name__ == "__main__":
    root = tk.Tk()
    app = HubFactoryGUI(root)
    root.mainloop()
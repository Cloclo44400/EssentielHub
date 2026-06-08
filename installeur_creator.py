import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class VersionFrame(ttk.LabelFrame):
    """Composant graphique représentant une version individuelle avec flèches de déplacement."""

    def __init__(self, parent, app, ver="", url="", deps=None):
        super().__init__(parent, text=" Configuration de Version ")
        self.app = app
        self.dependencies = deps if deps is not None else []

        # Ligne d'en-tête avec boutons de déplacement et suppression
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", padx=5, pady=2)

        # Groupe de boutons à droite
        self.controls_frame = ttk.Frame(self.header_frame)
        self.controls_frame.pack(side="right")

        self.btn_up = ttk.Button(
            self.controls_frame, text="🔼", width=3, command=self.move_up
        )
        self.btn_up.pack(side="left", padx=2)

        self.btn_down = ttk.Button(
            self.controls_frame, text="🔽", width=3, command=self.move_down
        )
        self.btn_down.pack(side="left", padx=2)

        self.btn_delete = ttk.Button(
            self.controls_frame, text="❌ Supprimer", command=self.destroy_self
        )
        self.btn_delete.pack(side="left", padx=2)

        # Grille pour les champs principaux
        self.fields_frame = ttk.Frame(self)
        self.fields_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.fields_frame, text="Numéro de version :").grid(
            row=0, column=0, sticky="w", padx=2, pady=5
        )
        self.ent_ver = ttk.Entry(self.fields_frame, width=20)
        self.ent_ver.insert(0, ver)
        self.ent_ver.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(self.fields_frame, text="URL du script principal :").grid(
            row=1, column=0, sticky="w", padx=2, pady=5
        )
        self.ent_url = ttk.Entry(self.fields_frame)
        self.ent_url.insert(0, url)
        self.ent_url.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.fields_frame.columnconfigure(1, weight=1)

        # Section des dépendances
        self.deps_frame = ttk.Frame(self)
        self.deps_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(
            self.deps_frame, text="Dépendances :", font=("Helvetica", 9, "bold")
        ).pack(side="top", anchor="w", pady=(0, 2))

        self.deps_input_row = ttk.Frame(self.deps_frame)
        self.deps_input_row.pack(fill="x", pady=2)

        self.ent_dep = ttk.Entry(self.deps_input_row, width=25)
        self.ent_dep.pack(side="left", padx=(0, 5))
        self.ent_dep.bind("<Return>", lambda e: self.add_dependency())

        self.btn_add_dep = ttk.Button(
            self.deps_input_row, text=" Ajouter", command=self.add_dependency
        )
        self.btn_add_dep.pack(side="left")

        self.deps_list_frame = ttk.Frame(self.deps_frame)
        self.deps_list_frame.pack(fill="x", pady=5)

        self.listbox_deps = tk.Listbox(
            self.deps_list_frame, height=3, selectmode=tk.SINGLE
        )
        self.listbox_deps.pack(side="left", fill="x", expand=True)

        self.btn_rem_dep = ttk.Button(
            self.deps_list_frame, text="Retirer", command=self.remove_dependency
        )
        self.btn_rem_dep.pack(side="right", padx=(5, 0), anchor="n")

        for dep in self.dependencies:
            self.listbox_deps.insert(tk.END, dep)

    def add_dependency(self):
        dep = self.ent_dep.get().strip()
        if dep:
            if dep not in self.listbox_deps.get(0, tk.END):
                self.listbox_deps.insert(tk.END, dep)
                self.ent_dep.delete(0, tk.END)
            else:
                messagebox.showwarning(
                    "Attention", "Cette dépendance est déjà présente."
                )

    def remove_dependency(self):
        selected = self.listbox_deps.curselection()
        if selected:
            self.listbox_deps.delete(selected[0])

    def move_up(self):
        self.app.move_version_up(self)

    def move_down(self):
        self.app.move_version_down(self)

    def get_data(self):
        return {
            "version": self.ent_ver.get().strip(),
            "main_script_url": self.ent_url.get().strip(),
            "dependencies": list(self.listbox_deps.get(0, tk.END)),
        }

    def destroy_self(self):
        self.app.remove_version(self)


class JSONEditorApp(tk.Tk):
    """Fenêtre principale gérant l'ordonnancement des blocs."""

    def __init__(self):
        super().__init__()
        self.title("Éditeur de fichier installeur.json")
        self.geometry("700x800")
        self.minimum_size = (600, 500)

        self.version_frames = []

        style = ttk.Style()
        style.theme_use("clam")

        # ---- Nom de l'application et Import ----
        top_frame = ttk.Frame(self, padding=15)
        top_frame.pack(fill="x")

        ttk.Label(
            top_frame, text="Nom de l'application :", font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=(0, 5))
        self.ent_app_name = ttk.Entry(top_frame, font=("Helvetica", 10))
        self.ent_app_name.insert(0, "FasterHomework")
        self.ent_app_name.pack(side="left", fill="x", expand=True, padx=5)

        btn_import = ttk.Button(
            top_frame, text="📥 Importer un .json", command=self.import_json
        )
        btn_import.pack(side="right", padx=(5, 0))

        # ---- Header Versions ----
        mid_header = ttk.Frame(self, padding=(15, 5))
        mid_header.pack(fill="x")
        ttk.Label(
            mid_header, text="Versions", font=("Helvetica", 12, "bold")
        ).pack(side="left")

        btn_add_ver = ttk.Button(
            mid_header, text="➕ Ajouter une version", command=self.add_version
        )
        btn_add_ver.pack(side="right")

        # ---- Zone dynamique Scrollable ----
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ---- Actions de fin et Output ----
        bottom_frame = ttk.Frame(self, padding=15)
        bottom_frame.pack(fill="x", side="bottom")

        actions_frame = ttk.Frame(bottom_frame)
        actions_frame.pack(fill="x", pady=(0, 5))

        btn_generate = ttk.Button(
            actions_frame, text="⚙️ Générer le JSON", command=self.generate_json
        )
        btn_generate.pack(side="left", padx=(0, 5))

        btn_copy = ttk.Button(
            actions_frame, text="📋 Copier le JSON", command=self.copy_json
        )
        btn_copy.pack(side="left", padx=5)

        ttk.Label(bottom_frame, text="JSON généré :").pack(anchor="w", pady=(5, 2))
        self.txt_output = tk.Text(bottom_frame, height=12, font=("Consolas", 10))
        self.txt_output.pack(fill="x", pady=5)

        self.load_defaults()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_version(self, ver="", url="", deps=None):
        frame = VersionFrame(self.scrollable_frame, self, ver, url, deps)
        # Par défaut, on insère la nouvelle version tout en haut du tableau de bord
        self.version_frames.insert(0, frame)
        self.repack_all_frames()

    def remove_version(self, frame):
        if frame in self.version_frames:
            self.version_frames.remove(frame)
            frame.destroy()
            self.repack_all_frames()

    def move_version_up(self, frame):
        """Monte le bloc vers le haut de l'écran (index inférieur)."""
        idx = self.version_frames.index(frame)
        if idx > 0:
            # Échange de place dans la liste
            self.version_frames[idx], self.version_frames[idx - 1] = (
                self.version_frames[idx - 1],
                self.version_frames[idx],
            )
            self.repack_all_frames()

    def move_version_down(self, frame):
        """Descend le bloc vers le bas de l'écran (index supérieur)."""
        idx = self.version_frames.index(frame)
        if idx < len(self.version_frames) - 1:
            # Échange de place dans la liste
            self.version_frames[idx], self.version_frames[idx + 1] = (
                self.version_frames[idx + 1],
                self.version_frames[idx],
            )
            self.repack_all_frames()

    def repack_all_frames(self):
        """Force la réorganisation visuelle complète selon l'ordre de la liste."""
        for frame in self.version_frames:
            frame.pack_forget()
        for frame in self.version_frames:
            frame.pack(fill="x", expand=True, padx=5, pady=5)

    def build_json_data(self):
        app_name = self.ent_app_name.get().strip() or "MyApp"
        versions = {}
        # On lit de haut en bas pour respecter l'ordre visuel choisi par l'utilisateur
        for frame in self.version_frames:
            data = frame.get_data()
            if data["version"]:
                versions[data["version"]] = {
                    "main_script_url": data["main_script_url"],
                    "dependencies": data["dependencies"],
                }
        return {"app_name": app_name, "versions": versions}

    def generate_json(self):
        data = self.build_json_data()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert("1.0", json_str)

    def copy_json(self):
        self.generate_json()
        json_str = self.txt_output.get("1.0", tk.END).strip()
        if json_str:
            self.clipboard_clear()
            self.clipboard_append(json_str)
            messagebox.showinfo(
                "Succès", "Le JSON a été copié dans le presse-papier !"
            )

    def import_json(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "app_name" not in data or "versions" not in data:
                raise ValueError()

            self.ent_app_name.delete(0, tk.END)
            self.ent_app_name.insert(0, data["app_name"])

            for frame in self.version_frames[:]:
                frame.destroy()
            self.version_frames.clear()

            # On importe les versions dans l'ordre du fichier JSON
            for ver, info in data["versions"].items():
                # On utilise append pour préserver l'ordre du fichier au lieu d'insérer en haut
                frame = VersionFrame(
                    self.scrollable_frame,
                    self,
                    ver,
                    info.get("main_script_url", ""),
                    info.get("dependencies", []),
                )
                self.version_frames.append(frame)

            self.repack_all_frames()

        except Exception:
            messagebox.showerror(
                "Fichier invalide",
                "Fichier invalide — vérifie que c'est bien un installeur.json correct.",
            )

    def load_defaults(self):
        # On charge pour que 2.1.0 apparaisse au-dessus de 2.0.0
        self.add_version(
            "2.0.0",
            "https://raw.githubusercontent.com/Cloclo44400/faster-homework/refs/heads/main/version/faster_homework_v2.0.py",
            ["requests"],
        )
        self.add_version(
            "2.1.0",
            "https://raw.githubusercontent.com/Cloclo44400/faster-homework/refs/heads/main/version/faster_homework_v2.1.0.py",
            ["requests"],
        )


if __name__ == "__main__":
    app = JSONEditorApp()
    app.mainloop()
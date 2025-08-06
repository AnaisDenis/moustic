# --- IMPORTS ---
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from multiprocessing import Pool
from pathlib import Path
import shutil
import subprocess
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.lines import Line2D
import multiprocessing

matplotlib.use('Agg')

# --- CHEMIN FFMPEG ---
#ffmpeg_bin = "C:/Users/2025ad007/Documents/ffmpeg-7.1.1-essentials_build/bin"
#os.environ["PATH"] += os.pathsep + ffmpeg_bin
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ffmpeg_bin = os.path.join(project_root, "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_bin
try:
    subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ FFmpeg est prêt.")
except Exception:
    print("❌ FFmpeg est introuvable. Merci de le placer dans le dossier 'bin/' ou de l'ajouter au PATH.")

def ajuster_temps(df):
    df["time"] = (np.ceil(df["time"] / 0.02) * 0.02).round(4)
    return df


def render_frame(args):
    (i, object_data_dict, selected_objs, time_values, color_dict,
     trace_enabled, trace_data, output_dir, display_modes,
     x_min_user, x_max_user, y_min_user, y_max_user, z_min_user, z_max_user) = args

    current_time = time_values[i]

    rows, cols = 2, 2
    fig = plt.figure(figsize=(cols * 5 + 2, rows * 4.5))  # Taille ajustée

    for idx, mode in enumerate(display_modes):
        row, col = divmod(idx, 2)
        subplot_idx = row * 2 + col + 1

        if mode == "3D":
            ax = fig.add_subplot(rows, cols, subplot_idx, projection='3d')
            ax.set_xlim(x_min_user, x_max_user)
            ax.set_ylim(y_min_user, y_max_user)
            ax.set_zlim(z_min_user, z_max_user)

            x0, x1 = 1.25, 1.65
            y0, y1 = -0.52, -0.12
            z = z_min_user  # "sol" du cube graphique

            lines = [
                [(x0, y0, z), (x1, y0, z)],
                [(x1, y0, z), (x1, y1, z)],
                [(x1, y1, z), (x0, y1, z)],
                [(x0, y1, z), (x0, y0, z)]
            ]

            ax.add_collection3d(Line3DCollection(lines, colors='black', linewidths=1))
            ax.set_xlabel("X (m)")
            ax.set_ylabel("Y (m)")
            ax.set_zlabel("Z (m)")

        else:
            ax = fig.add_subplot(rows, cols, subplot_idx)
            if mode == "XY":
                rect_x = 1.25
                rect_y = -0.52
                rect_width = 1.65 - 1.25
                rect_height = -0.12 - (-0.52)
                ax.add_patch(Rectangle((rect_x, rect_y), rect_width, rect_height,
                                       linewidth=1, edgecolor='black', facecolor='none'))
                ax.set_xlim(x_min_user, x_max_user)
                ax.set_ylim(y_min_user, y_max_user)
                ax.set_xlabel("X (m)")
                ax.set_ylabel("Y (m)")
            elif mode == "XZ":
                ax.plot([1.25, 1.65], [z_min_user, z_min_user], color='black', linewidth=3)
                ax.set_xlim(x_min_user, x_max_user)
                ax.set_ylim(z_min_user, z_max_user)
                ax.set_xlabel("X (m)")
                ax.set_ylabel("Z (m)")
            elif mode == "YZ":
                ax.plot([-0.52, -0.12], [z_min_user, z_min_user], color='black', linewidth=3)
                ax.set_xlim(y_min_user, y_max_user)
                ax.set_ylim(z_min_user, z_max_user)
                ax.set_xlabel("Y (m)")
                ax.set_ylabel("Z (m)")

        shown_labels = set()
        for obj in selected_objs:
            obj_data = object_data_dict.get(obj, {})
            if current_time in obj_data:
                data = obj_data[current_time]
                label = str(obj) if obj not in shown_labels else None
                shown_labels.add(obj)

                if mode == "3D":
                    x, y = data["XY"]
                    _, z = data["XZ"]
                    ax.scatter(x, y, z, s=8, c=[color_dict[obj]], label=label)
                elif mode == "XY":
                    point = data["XY"]
                    ax.scatter(*point, s=8, c=[color_dict[obj]], label=label)
                elif mode == "XZ":
                    point = data["XZ"]
                    ax.scatter(*point, s=8, c=[color_dict[obj]], label=label)
                elif mode == "YZ":
                    _, y = data["XY"]
                    _, z = data["XZ"]
                    ax.scatter(y, z, s=8, c=[color_dict[obj]], label=label)

                if trace_enabled:
                    for xy_t, xz_t, alpha in trace_data.get(obj, {}).get(current_time, []):
                        if mode == "3D":
                            ax.scatter(*xy_t, xz_t[1], s=4, c=[color_dict[obj]], alpha=alpha)
                        elif mode == "XY":
                            ax.scatter(*xy_t, s=4, c=[color_dict[obj]], alpha=alpha)
                        elif mode == "XZ":
                            ax.scatter(*xz_t, s=4, c=[color_dict[obj]], alpha=alpha)
                        elif mode == "YZ":
                            _, y = xy_t
                            _, z = xz_t
                            ax.scatter(y, z, s=4, c=[color_dict[obj]], alpha=alpha)

        ax.set_title(f"Mode {mode}")

    fig.suptitle(f"Temps : {current_time:.2f} s")

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=str(obj),
               markerfacecolor=color_dict[obj], markersize=8)
        for obj in selected_objs
    ]
    fig.subplots_adjust(right=0.75)
    fig.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(0.88, 0.5), fontsize='small', frameon=True)

    fname = os.path.join(output_dir, f"frame_{i:04d}.png")
    fig.savefig(fname)
    plt.close(fig)
    return i


class VideoRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enregistrement vidéo")

        # Bouton pour choisir un fichier CSV
        self.btn_open = tk.Button(root, text="📂 Choisir fichier CSV", command=self.open_file)
        self.btn_open.pack(pady=10)

        self.status_label = tk.Label(root, text="Aucun fichier chargé", fg="red")
        self.status_label.pack(pady=5)

        self.listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, height=10)
        self.listbox.pack(padx=10, pady=10)
        self.listbox.config(state=tk.DISABLED)  # Désactivé tant que pas de fichier

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.btn_record = tk.Button(btn_frame, text="🎥 Enregistrer vidéo", command=self.save_video)
        self.btn_record.pack(side=tk.LEFT, padx=5)
        self.btn_record.config(state=tk.DISABLED)

        self.btn_deselect = tk.Button(btn_frame, text="🩹 Tout décocher", command=self.deselect_all)
        self.btn_deselect.pack(side=tk.LEFT, padx=5)
        self.btn_deselect.config(state=tk.DISABLED)

        self.trace_var = tk.BooleanVar()
        self.trace_checkbox = tk.Checkbutton(root, text="🌠 Effet étoile filante (trace 1s)", variable=self.trace_var)
        self.trace_checkbox.pack(pady=5)
        self.trace_checkbox.config(state=tk.DISABLED)

        trace_duration_frame = tk.Frame(root)
        trace_duration_frame.pack(pady=2)
        tk.Label(trace_duration_frame, text="Durée trace (s) :").pack(side=tk.LEFT)
        self.trace_duration_entry = tk.Entry(trace_duration_frame, width=5)
        self.trace_duration_entry.pack(side=tk.LEFT, padx=2)
        self.trace_duration_entry.insert(0, "1.0")
        self.trace_duration_entry.config(state=tk.DISABLED)

        self.interval_var = tk.BooleanVar()
        self.interval_checkbox = tk.Checkbutton(root, text="🕒 Intervalle sélectionné", variable=self.interval_var,
                                                command=self.toggle_interval_entries)
        self.interval_checkbox.pack()
        self.interval_checkbox.config(state=tk.DISABLED)

        interval_frame = tk.Frame(root)
        interval_frame.pack(pady=5)

        tk.Label(interval_frame, text="De (s) :").pack(side=tk.LEFT)
        self.start_entry = tk.Entry(interval_frame, width=5)
        self.start_entry.pack(side=tk.LEFT, padx=2)
        self.start_entry.configure(state=tk.DISABLED)

        tk.Label(interval_frame, text="à (s) :").pack(side=tk.LEFT)
        self.end_entry = tk.Entry(interval_frame, width=5)
        self.end_entry.pack(side=tk.LEFT, padx=2)
        self.end_entry.configure(state=tk.DISABLED)

        mode_frame = tk.LabelFrame(root, text="🎛️ Modes d'affichage à inclure")
        mode_frame.pack(pady=5, padx=10, fill="x")

        self.mode_xy_var = tk.BooleanVar(value=True)
        self.mode_xz_var = tk.BooleanVar(value=False)
        self.mode_yz_var = tk.BooleanVar(value=False)
        self.mode_3d_var = tk.BooleanVar(value=False)

        tk.Checkbutton(mode_frame, text="XY", variable=self.mode_xy_var).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(mode_frame, text="XZ", variable=self.mode_xz_var).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(mode_frame, text="YZ", variable=self.mode_yz_var).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(mode_frame, text="3D", variable=self.mode_3d_var).pack(side=tk.LEFT, padx=5)

        coords_frame = tk.LabelFrame(root, text="🗺️ Limites de l'espace (optionnel)")
        coords_frame.pack(pady=5, padx=10, fill="x")

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        self.progress['value'] = 0

        def add_coord_entry(label_text, var_name):
            tk.Label(coords_frame, text=label_text).pack(side=tk.LEFT, padx=2)
            entry = tk.Entry(coords_frame, width=6)
            entry.pack(side=tk.LEFT, padx=2)
            setattr(self, var_name, entry)

        add_coord_entry("Xmin :", "xmin_entry")
        add_coord_entry("Xmax :", "xmax_entry")
        add_coord_entry("Ymin :", "ymin_entry")
        add_coord_entry("Ymax :", "ymax_entry")
        add_coord_entry("Zmin :", "zmin_entry")
        add_coord_entry("Zmax :", "zmax_entry")

        # Variables pour données et limites (remplies après chargement fichier)
        self.df = None
        self.all_objects = None
        self.x_min = self.x_max = None
        self.y_min = self.y_max = None
        self.z_min = self.z_max = None

    def open_file(self):
        print("Tentative de chargement du fichier...")  # DEBUG
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Sélectionner un fichier CSV", filetypes=filetypes)
        if not filename:
            print("Aucun fichier sélectionné.")  # DEBUG
            return

        print(f"Fichier sélectionné : {filename}")  # DEBUG

        try:
            df = pd.read_csv(filename, sep=";")
            print("Fichier chargé avec succès")  # DEBUG
            print("Colonnes du fichier :", df.columns.tolist())  # DEBUG
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier:\n{e}")
            print(f"Erreur lecture fichier : {e}")  # DEBUG
            return

        if "object" not in df.columns or "time" not in df.columns:
            messagebox.showerror("Erreur", "Le fichier doit contenir les colonnes 'object' et 'time'.")
            print("Colonnes manquantes !")  # DEBUG
            return

        self.df = ajuster_temps(df)



        self.all_objects = sorted(self.df["object"].unique())
        self.listbox.config(state=tk.NORMAL)
        self.listbox.delete(0, tk.END)
        for obj in self.all_objects:
            self.listbox.insert(tk.END, str(obj))

        self.status_label.config(text=f"Fichier chargé: {os.path.basename(filename)}", fg="green")
        self.btn_record.config(state=tk.NORMAL)
        self.btn_deselect.config(state=tk.NORMAL)
        self.trace_checkbox.config(state=tk.NORMAL)
        self.trace_duration_entry.config(state=tk.NORMAL)
        self.interval_checkbox.config(state=tk.NORMAL)
        self.start_entry.config(state=tk.DISABLED)
        self.end_entry.config(state=tk.DISABLED)

        # Calcul des limites par défaut
        self.x_min = self.df["XSplined"].min()
        self.x_max = self.df["XSplined"].max()
        self.y_min = self.df["YSplined"].min()
        self.y_max = self.df["YSplined"].max()
        self.z_min = self.df["ZSplined"].min()
        self.z_max = self.df["ZSplined"].max()

        # Initialisation des champs limites avec valeurs par défaut
        self.xmin_entry.delete(0, tk.END)
        self.xmin_entry.insert(0, str(round(self.x_min, 2)))
        self.xmax_entry.delete(0, tk.END)
        self.xmax_entry.insert(0, str(round(self.x_max, 2)))
        self.ymin_entry.delete(0, tk.END)
        self.ymin_entry.insert(0, str(round(self.y_min, 2)))
        self.ymax_entry.delete(0, tk.END)
        self.ymax_entry.insert(0, str(round(self.y_max, 2)))
        self.zmin_entry.delete(0, tk.END)
        self.zmin_entry.insert(0, str(round(self.z_min, 2)))
        self.zmax_entry.delete(0, tk.END)
        self.zmax_entry.insert(0, str(round(self.z_max, 2)))

    def deselect_all(self):
        self.listbox.selection_clear(0, tk.END)

    def toggle_interval_entries(self):
        if self.interval_var.get():
            self.start_entry.config(state=tk.NORMAL)
            self.end_entry.config(state=tk.NORMAL)
        else:
            self.start_entry.config(state=tk.DISABLED)
            self.end_entry.config(state=tk.DISABLED)

    def save_video(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Attention", "Veuillez sélectionner au moins un objet.")
            return

        selected_objs = [self.all_objects[i] for i in selected_indices]

        try:
            x_min_user = float(self.xmin_entry.get())
            x_max_user = float(self.xmax_entry.get())
            y_min_user = float(self.ymin_entry.get())
            y_max_user = float(self.ymax_entry.get())
            z_min_user = float(self.zmin_entry.get())
            z_max_user = float(self.zmax_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Les limites doivent être des nombres valides.")
            return

        trace_enabled = self.trace_var.get()
        try:
            trace_duration = float(self.trace_duration_entry.get())
            if trace_duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Durée trace doit être un nombre positif.")
            return

        df = self.df

        time_values = sorted(df["time"].unique())

        if self.interval_var.get():
            try:
                t_start = float(self.start_entry.get())
                t_end = float(self.end_entry.get())
                if t_start >= t_end:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erreur", "Intervalle temps invalide.")
                return
            # Limiter time_values à l’intervalle
            time_values = [t for t in time_values if t_start <= t <= t_end]

        if not time_values:
            messagebox.showerror("Erreur", "Aucune donnée dans l'intervalle spécifié.")
            return

        object_data_dict = {}
        for obj in selected_objs:
            subset = df[df["object"] == obj]
            obj_dict = {}
            for t in time_values:
                sub_t = subset[subset["time"] == t]
                if sub_t.empty:
                    continue
                x = sub_t["XSplined"].values[0]
                y = sub_t["YSplined"].values[0]
                z = sub_t["ZSplined"].values[0]
                obj_dict[t] = {
                    "XY": (x, y),
                    "XZ": (x, z)
                }
            object_data_dict[obj] = obj_dict

        # Création des données trace
        trace_data = {}
        n_trace_frames = int(trace_duration / 0.02)

        for obj in selected_objs:
            trace_data[obj] = {}
            obj_times = sorted(object_data_dict[obj].keys())
            for idx, t in enumerate(time_values):
                trace_points = []
                for dt in range(1, n_trace_frames + 1):
                    trace_idx = idx - dt
                    if trace_idx < 0:
                        break
                    t_trace = time_values[trace_idx]
                    if t_trace in object_data_dict[obj]:
                        alpha = max(0, 1 - dt / n_trace_frames)
                        trace_points.append(
                            (object_data_dict[obj][t_trace]["XY"],
                             object_data_dict[obj][t_trace]["XZ"], alpha)
                        )
                trace_data[obj][t] = trace_points

        color_map = matplotlib.colormaps['tab20']
        color_dict = {}
        for i, obj in enumerate(selected_objs):
            color_dict[obj] = color_map(i % 20)

        # Modes sélectionnés
        display_modes = []
        if self.mode_xy_var.get():
            display_modes.append("XY")
        if self.mode_xz_var.get():
            display_modes.append("XZ")
        if self.mode_yz_var.get():
            display_modes.append("YZ")
        if self.mode_3d_var.get():
            display_modes.append("3D")

        if not display_modes:
            messagebox.showwarning("Attention", "Veuillez sélectionner au moins un mode d'affichage.")
            return

        output_dir = "frames_temp"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # Création des arguments pour multiprocessing
        args_list = []
        for i in range(len(time_values)):
            args_list.append((i, object_data_dict, selected_objs, time_values, color_dict,
                              trace_enabled, trace_data, output_dir, display_modes,
                              x_min_user, x_max_user, y_min_user, y_max_user, z_min_user, z_max_user))

        total_frames = len(time_values)
        self.progress['maximum'] = total_frames
        self.progress['value'] = 0
        self.root.update_idletasks()

        pool = Pool(processes=max(1, multiprocessing.cpu_count() - 1))

        for i, _ in enumerate(pool.imap_unordered(render_frame, args_list), 1):
            self.progress['value'] = i
            self.root.update_idletasks()  # Rafraîchit la GUI pour montrer la progression

        pool.close()
        pool.join()

        # Génération vidéo avec ffmpeg
        # Récupérer le nom de fichier CSV (sans chemin ni extension)
        input_filename = os.path.basename(self.status_label.cget("text").replace("Fichier chargé: ", ""))
        input_name_no_ext = os.path.splitext(input_filename)[0]

        # Construire le chemin vers Detect_couple_v1 (dossier parent de src)
        # self.root.winfo_pathname('') n'est pas disponible, on utilise __file__ (chemin script) et os.path
        script_dir = os.path.dirname(os.path.abspath(__file__))  # dossier src
        parent_dir = os.path.dirname(script_dir)  # dossier parent (Detect_couple_v1 supposé)
        output_dir_final = os.path.join(parent_dir, f"enregistrement_{input_name_no_ext}.mp4")

        video_name = output_dir_final

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-r", "50", "-i",
            os.path.join(output_dir, "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", video_name
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True)
            messagebox.showinfo("Succès", f"Vidéo enregistrée : {video_name}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création de la vidéo:\n{e}")

        # Nettoyer dossier temporaire
        shutil.rmtree(output_dir)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoRecorderApp(root)
    root.mainloop()

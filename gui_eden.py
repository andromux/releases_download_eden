#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Releases GUI
Implementa la lógica de la versión CLI con una interfaz gráfica moderna.
"""

import os
import json
import threading
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import customtkinter as ctk
from tkinter import messagebox

# ------------------ Cliente de GitHub ------------------
# Mantiene la lógica de la versión CLI
class GitHubClient:
    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubReleasesGUI/1.2"
        }
        if token:
            headers["Authorization"] = f"token {token}"
        self.session.headers.update(headers)

    def get_releases(self, repo: str):
        """Devuelve la lista completa de releases."""
        url = f"https://api.github.com/repos/{repo}/releases"
        r = self.session.get(url, timeout=20)
        r.raise_for_status()
        return r.json()

    def download_asset(self, url: str, dest: Path, progress_cb=None):
        """Descarga un asset con barra de progreso."""
        r = self.session.get(url, stream=True, timeout=60)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                done += len(chunk)
                if total and progress_cb:
                    progress_cb(done / total)

# ------------------ Interfaz principal ------------------
class GitHubReleasesGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GitHub Releases GUI")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Fuentes grandes
        base = 40
        self.FONT_NORMAL = ctk.CTkFont(size=base)
        self.FONT_TITLE = ctk.CTkFont(size=int(base * 1.3), weight="bold")

        self.client = GitHubClient()
        self.fav_file = Path.home() / ".github_releases_favs.json"
        self.favorites = self._load_favs()

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        # Frame superior para la barra de búsqueda y botones
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(top_frame, text="Repositorio:", font=self.FONT_NORMAL).pack(side="left", padx=8)
        self.repo_entry = ctk.CTkEntry(top_frame, width=400, font=self.FONT_NORMAL)
        self.repo_entry.pack(side="left", padx=5)

        ctk.CTkButton(top_frame, text="Buscar Releases", command=self.search_releases,
                      font=self.FONT_NORMAL).pack(side="left", padx=5)

        ctk.CTkButton(top_frame, text="⭐ Favoritos", command=self.select_fav,
                      font=self.FONT_NORMAL).pack(side="left", padx=5)

        # Frame principal para el contenido (releases o assets)
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Muestra el mensaje de inicio
        self._show_initial_message()

    def _show_initial_message(self):
        """Limpia el main_frame y muestra el mensaje de inicio."""
        for w in self.main_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.main_frame,
                     text="Introduce un repositorio o elige un favorito",
                     font=self.FONT_TITLE).pack(expand=True)

    # ---------- Funciones de búsqueda y visualización ----------
    def search_releases(self):
        repo = self.repo_entry.get().strip()
        if not repo:
            messagebox.showerror("Error", "Debes introducir un repositorio (usuario/repositorio)")
            return
        if repo not in self.favorites:
            if messagebox.askyesno("Favoritos", f"¿Guardar {repo} en favoritos?"):
                self.favorites.append(repo)
                self._save_favs()

        # Inicia la búsqueda en un hilo separado para no congelar la GUI
        threading.Thread(target=self._fetch_releases, args=(repo,), daemon=True).start()

    def _fetch_releases(self, repo):
        try:
            releases = self.client.get_releases(repo)
            # Usa `after` para actualizar la GUI desde el hilo principal
            self.after(0, lambda: self.show_releases(repo, releases))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"No se pudo obtener releases:\n{e}"))
    
    def show_releases(self, repo, releases):
        """Muestra una lista de releases con scroll."""
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        # Usamos CTkScrollableFrame para la lista de releases
        releases_list_frame = ctk.CTkScrollableFrame(self.main_frame)
        releases_list_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(releases_list_frame, text=f"Releases de {repo}", font=self.FONT_TITLE).pack(pady=5)
        
        if not releases:
            ctk.CTkLabel(releases_list_frame, text="No hay releases en este repositorio", font=self.FONT_NORMAL).pack(pady=10)
            return

        for rel in releases:
            date = rel.get("published_at", "")
            try:
                date = datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%Y-%m-%d")
            except Exception:
                pass
            assets_count = len(rel.get("assets", []))
            info = f"{rel.get('name') or '(sin nombre)'}\nTag: {rel.get('tag_name','-')} | {date} | {assets_count} archivos"
            ctk.CTkButton(releases_list_frame, text=info,
                          font=self.FONT_NORMAL, anchor="w",
                          command=lambda r=rel: self.show_assets(repo, r)).pack(fill="x", pady=6, padx=6)
                          
    def show_assets(self, repo, release):
        """Muestra una lista de assets (archivos) de una release con scroll."""
        for w in self.main_frame.winfo_children():
            w.destroy()

        # Frame superior para el título de la release y botón de retorno
        assets_title_frame = ctk.CTkFrame(self.main_frame)
        assets_title_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkButton(assets_title_frame, text="< Volver", command=self._show_initial_message, font=self.FONT_NORMAL).pack(side="left", padx=5)
        title_text = release.get('name') or release.get('tag_name') or "Release sin nombre"
        ctk.CTkLabel(assets_title_frame, text=f"Archivos de: {title_text}", font=self.FONT_TITLE).pack(side="left", expand=True, padx=5)

        # Usamos CTkScrollableFrame para la lista de archivos
        assets_list_frame = ctk.CTkScrollableFrame(self.main_frame)
        assets_list_frame.pack(fill="both", expand=True)

        assets = release.get("assets", [])
        if not assets:
            ctk.CTkLabel(assets_list_frame, text="No hay archivos en esta release", font=self.FONT_NORMAL).pack(pady=10)
            return

        # Botón para descargar todos los archivos
        ctk.CTkButton(assets_list_frame, text="⬇️ Descargar todos",
                      font=self.FONT_NORMAL,
                      command=lambda: self.download_all(repo, assets)).pack(pady=10)
        
        # Iterar sobre cada asset y crear un botón
        for asset in assets:
            size = self._size(asset.get("size", 0))
            downloads = asset.get("download_count", 0)
            text = f"{asset.get('name')}\n| Tamaño: {size} | Descargas: {downloads}"
            
            btn = ctk.CTkButton(assets_list_frame, text=text,
                                font=self.FONT_NORMAL,
                                command=lambda a=asset: self.download_one(repo, a),
                                anchor="w")
            btn.pack(fill="x", pady=4, padx=6)

    # ---------- Funciones de descarga ----------
    def download_one(self, repo, asset):
        self._start_download(repo, asset)

    def download_all(self, repo, assets):
        for asset in assets:
            self._start_download(repo, asset)

    def _start_download(self, repo, asset):
        dest = (Path.home() / "Descargas" / "GitHubReleases"
                / repo.replace("/", "_") / asset["name"])
        
        win = ctk.CTkToplevel(self)
        win.title(f"Descargando {asset['name']}")
        win.geometry("500x120")
        
        label = ctk.CTkLabel(win, text=f"Descargando {asset['name']}", font=self.FONT_NORMAL)
        label.pack(pady=10)
        bar = ctk.CTkProgressBar(win)
        bar.pack(fill="x", padx=15, pady=10)
        bar.set(0)

        def worker():
            try:
                self.client.download_asset(asset["browser_download_url"], dest,
                                           progress_cb=lambda p: self.after(0, lambda: bar.set(p)))
                self.after(0, lambda: messagebox.showinfo("Descarga", f"Archivo guardado en:\n{dest}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, win.destroy)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Utilidades (funciones de la CLI) ----------
    def _size(self, b: int) -> str:
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"

    def _load_favs(self):
        if self.fav_file.exists():
            try:
                return json.load(open(self.fav_file))
            except Exception:
                return []
        return []

    def _save_favs(self):
        json.dump(self.favorites, open(self.fav_file, "w"), indent=2)

    def select_fav(self):
        if not self.favorites:
            messagebox.showinfo("Favoritos", "No hay favoritos guardados.")
            return
        win = ctk.CTkToplevel(self)
        win.title("Favoritos")
        win.geometry("300x400")
        lst = ctk.CTkScrollableFrame(win)
        lst.pack(fill="both", expand=True, padx=10, pady=10)
        for repo in self.favorites:
            ctk.CTkButton(lst, text=repo, font=self.FONT_NORMAL,
                          command=lambda r=repo: self._use_fav(win, r)).pack(fill="x", pady=5)

    def _use_fav(self, win, repo):
        self.repo_entry.delete(0, "end")
        self.repo_entry.insert(0, repo)
        win.destroy()
        self.search_releases()

# ------------------ MAIN ------------------
if __name__ == "__main__":
    app = GitHubReleasesGUI()
    app.mainloop()
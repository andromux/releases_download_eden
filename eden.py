#!/usr/bin/env python3
"""
GitHub Releases Downloader CLI mejorado
Descarga releases completas o archivos individuales con detalles y progreso.
"""

import os, sys, json, argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn,
        TaskProgressColumn, TimeRemainingColumn,
        DownloadColumn, TransferSpeedColumn
    )
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None

class GitHubReleasesDownloader:
    def __init__(self, repo: str):
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.session = requests.Session()
        self.token = None
        self._load_token()
        self._setup_session()

    # ------------------ Utilidades de impresión ------------------
    def _info(self, msg):   console.print(msg, style="blue") if RICH else print(msg)
    def _ok(self, msg):     console.print(msg, style="green") if RICH else print(msg)
    def _warn(self, msg):   console.print(msg, style="yellow") if RICH else print(msg)
    def _err(self, msg):    console.print(msg, style="red") if RICH else print(msg)

    # ------------------ Token ------------------
    def _load_token(self):
        tf = Path(".secret_token.json")
        if tf.exists():
            try:
                self.token = json.load(tf.open()).get("github_token")
                self._ok("Token cargado") if self.token else self._warn("Archivo de token vacío")
            except Exception as e:
                self._warn(f"No se pudo leer token: {e}")

    def _setup_session(self):
        headers = {"Accept": "application/vnd.github.v3+json",
                   "User-Agent": "GitHubReleasesDownloader/1.1"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        self.session.headers.update(headers)

    # ------------------ API ------------------
    def get_releases(self, limit=20) -> List[Dict]:
        try:
            url = f"{self.base_url}/releases"
            resp = self.session.get(url, params={"per_page": limit}, timeout=30)
            resp.raise_for_status()
            rels = resp.json()
            self._ok(f"Encontradas {len(rels)} releases")
            return rels
        except Exception as e:
            self._err(f"Error al obtener releases: {e}")
            return []

    # ------------------ Presentación ------------------
    def display_releases(self, releases: List[Dict]):
        if not releases:
            self._warn("No hay releases")
            return
        if RICH:
            t = Table(title="📦 Releases")
            t.add_column("#", style="cyan")
            t.add_column("Nombre", style="magenta")
            t.add_column("Tag", style="green")
            t.add_column("Fecha", style="blue")
            t.add_column("Assets", justify="right")
            for i, r in enumerate(releases, 1):
                dt = r.get("published_at") or ""
                date = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d") if dt else "?"
                t.add_row(str(i), r.get("name") or "(sin nombre)",
                          r.get("tag_name","-"), date,
                          str(len(r.get("assets",[]))))
            console.print(t)
        else:
            for i,r in enumerate(releases,1):
                print(f"{i}. {r.get('name','(sin nombre)')} [{len(r.get('assets',[]))} archivos]")

    def display_assets(self, assets: List[Dict]):
        if not assets:
            self._warn("No hay archivos en esta release")
            return
        if RICH:
            t = Table(title="📁 Archivos")
            t.add_column("#", style="cyan")
            t.add_column("Nombre", style="magenta")
            t.add_column("Tamaño", justify="right", style="green")
            t.add_column("Descargas", justify="right", style="blue")
            for i,a in enumerate(assets,1):
                t.add_row(str(i), a.get("name","?"),
                          self._size(a.get("size",0)),
                          str(a.get("download_count",0)))
            console.print(t)
        else:
            for i,a in enumerate(assets,1):
                print(f"{i}. {a.get('name')} ({self._size(a.get('size',0))})")

    def show_file_details(self, asset: Dict):
        name = asset.get("name","?")
        size = self._size(asset.get("size",0))
        url  = asset.get("browser_download_url","")
        mime = asset.get("content_type","?")
        if RICH:
            console.print(Panel(
                f"[bold]Nombre:[/bold] {name}\n"
                f"[bold]Tamaño:[/bold] {size}\n"
                f"[bold]MIME:[/bold] {mime}\n"
                f"[bold]URL:[/bold] {url}",
                title="Detalles del archivo"
            ))
        else:
            print(f"{name}\n Tamaño:{size}\n MIME:{mime}\n URL:{url}")

    # ------------------ Descarga ------------------
    def _size(self, b:int) -> str:
        for u in ['B','KB','MB','GB']:
            if b<1024: return f"{b:.1f} {u}"
            b/=1024
        return f"{b:.1f} TB"

    def download_file(self, asset: Dict, folder="downloads") -> bool:
        Path(folder).mkdir(exist_ok=True)
        path = Path(folder)/asset.get("name","file")
        url  = asset.get("browser_download_url")
        if not url:
            self._err("URL no disponible")
            return False
        try:
            r = self.session.get(url, stream=True, timeout=(5,120))
            r.raise_for_status()
            total = int(r.headers.get("content-length",0))
            if RICH and total>0:
                with Progress(SpinnerColumn(),TextColumn("[progress.description]{task.description}"),
                              BarColumn(),TaskProgressColumn(),
                              DownloadColumn(),TransferSpeedColumn(),TimeRemainingColumn()) as p:
                    task = p.add_task(f"[green]{path.name}", total=total)
                    with open(path,"wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                            p.update(task, advance=len(chunk))
            else:
                print(f"Descargando {path.name}...")
                with open(path,"wb") as f:
                    for c in r.iter_content(8192): f.write(c)
            self._ok(f"Descargado: {path}")
            return True
        except Exception as e:
            self._err(f"Error en {path.name}: {e}")
            return False

    def download_multiple(self, assets: List[Dict], folder="downloads"):
        ok = sum(self.download_file(a, folder) for a in assets)
        self._ok(f"{ok}/{len(assets)} archivos descargados")

    # ------------------ Menús ------------------
    def interactive(self):
        while True:
            if RICH:
                console.print(Panel(f"[blue]Repositorio:[/blue] {self.repo}", title="GitHub Downloader"))
            print("\n1. Ver releases\n2. Descargar última release completa\n3. Descarga detallada\n4. Salir")
            op = input("Opción: ").strip()
            if op=="1":
                rel = self.get_releases()
                self.display_releases(rel)
            elif op=="2":
                rel = self.get_releases(1)
                if rel: self.download_multiple(rel[0].get("assets",[]))
            elif op=="3":
                self.detailed_menu()
            elif op=="4":
                break
            else: print("Opción inválida")

    def detailed_menu(self):
        releases = self.get_releases()
        if not releases: return
        self.display_releases(releases)
        idx = input("Número de release: ").strip()
        if not idx.isdigit(): return
        r = releases[int(idx)-1]
        assets = r.get("assets",[])
        if not assets:
            self._warn("Sin archivos en esta release")
            return
        self.display_assets(assets)
        while True:
            c = input("Número de archivo, 'all' o 'back': ").strip().lower()
            if c == "back": break
            if c == "all":
                self.download_multiple(assets)
                break
            if c.isdigit():
                i = int(c)-1
                if 0<=i<len(assets):
                    a = assets[i]
                    self.show_file_details(a)
                    if input("Descargar? (s/N): ").lower()=="s":
                        self.download_file(a)
            else:
                print("Opción inválida")

def main():
    p = argparse.ArgumentParser(description="Descarga releases de GitHub")
    p.add_argument("--repo", required=True, help="usuario/repositorio")
    args = p.parse_args()
    d = GitHubReleasesDownloader(args.repo)
    d.interactive()

if __name__ == "__main__":
    main()

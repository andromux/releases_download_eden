#!/usr/bin/env python3
"""
GitHub Releases Downloader CLI
Una herramienta profesional para descargar releases de repositorios GitHub

Autor: Andromux ORG
Versión: 1.0.0
"""

import os
import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import argparse

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import (
        Progress, 
        SpinnerColumn, 
        TextColumn, 
        BarColumn, 
        TaskProgressColumn,
        TimeRemainingColumn,
        DownloadColumn,
        TransferSpeedColumn
    )
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Para una mejor experiencia, instala 'rich': pip install rich")

class GitHubReleasesDownloader:
    """
    Clase principal para gestionar la descarga de releases de GitHub
    """
    
    def __init__(self, repo: str = "eden-emulator/Releases"):
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.session = requests.Session()
        self.token = None
        self.console = Console() if RICH_AVAILABLE else None
        
        # Cargar token de autenticación si existe
        self._load_token()
        
        # Configurar headers de la sesión
        self._setup_session()
    
    def _load_token(self) -> None:
        """
        Carga el token de autenticación desde el archivo .secret_token.json
        """
        token_file = Path(".secret_token.json")
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('github_token')
                if self.token:
                    self._print_success("✅ Token de autenticación cargado correctamente")
                else:
                    self._print_warning("⚠️  Archivo de token encontrado pero vacío")
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                self._print_error(f"❌ Error al cargar el token: {e}")
        else:
            self._print_info("ℹ️  No se encontró token de autenticación. Usando límites de API públicos.")
    
    def _setup_session(self) -> None:
        """
        Configura la sesión HTTP con headers apropiados
        """
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Releases-Downloader/1.0'
        }
        
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        self.session.headers.update(headers)
    
    def _print_success(self, message: str) -> None:
        """Imprime mensaje de éxito"""
        if RICH_AVAILABLE:
            self.console.print(message, style="bold green")
        else:
            print(message)
    
    def _print_error(self, message: str) -> None:
        """Imprime mensaje de error"""
        if RICH_AVAILABLE:
            self.console.print(message, style="bold red")
        else:
            print(message)
    
    def _print_warning(self, message: str) -> None:
        """Imprime mensaje de advertencia"""
        if RICH_AVAILABLE:
            self.console.print(message, style="bold yellow")
        else:
            print(message)
    
    def _print_info(self, message: str) -> None:
        """Imprime mensaje informativo"""
        if RICH_AVAILABLE:
            self.console.print(message, style="bold blue")
        else:
            print(message)
    
    def configure_token(self) -> bool:
        """
        Configura el token de autenticación de GitHub
        """
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold blue]Configuración del Token de GitHub[/bold blue]\n\n"
                "Para aumentar el límite de solicitudes a la API, puedes configurar "
                "un Personal Access Token (PAT) de GitHub.\n\n"
                "Pasos para crear un token:\n"
                "1. Ve a GitHub → Settings → Developer settings → Personal access tokens\n"
                "2. Genera un nuevo token con permisos 'public_repo'\n"
                "3. Copia el token generado\n\n"
                "[bold yellow]⚠️  El token se guardará en .secret_token.json[/bold yellow]",
                title="🔑 Configuración de Token"
            ))
            
            token = Prompt.ask("Ingresa tu token de GitHub (deja vacío para omitir)")
        else:
            print("\n🔑 Configuración del Token de GitHub")
            print("=" * 50)
            print("Para aumentar el límite de solicitudes, configura un Personal Access Token")
            token = input("Ingresa tu token de GitHub (Enter para omitir): ").strip()
        
        if not token:
            self._print_info("Token omitido. Continuando sin autenticación.")
            return False
        
        # Validar token
        test_session = requests.Session()
        test_session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        
        try:
            response = test_session.get("https://api.github.com/user")
            if response.status_code == 200:
                # Guardar token
                token_data = {'github_token': token}
                with open('.secret_token.json', 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                self.token = token
                self._setup_session()
                self._print_success("✅ Token configurado y validado correctamente")
                return True
            else:
                self._print_error("❌ Token inválido")
                return False
        
        except requests.RequestException as e:
            self._print_error(f"❌ Error al validar token: {e}")
            return False
    
    def get_releases(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene la lista de releases del repositorio
        
        Args:
            limit: Número máximo de releases a obtener
            
        Returns:
            Lista de releases
        """
        url = f"{self.base_url}/releases"
        
        try:
            if RICH_AVAILABLE:
                with self.console.status("[bold blue]Obteniendo releases...", spinner="dots"):
                    response = self.session.get(url, params={'per_page': limit})
            else:
                print("📡 Obteniendo releases...")
                response = self.session.get(url, params={'per_page': limit})
            
            response.raise_for_status()
            releases = response.json()
            
            self._print_success(f"✅ Se encontraron {len(releases)} releases")
            return releases
            
        except requests.RequestException as e:
            self._print_error(f"❌ Error al obtener releases: {e}")
            return []
    
    def display_releases(self, releases: List[Dict]) -> None:
        """
        Muestra las releases en formato tabla
        """
        if not releases:
            self._print_warning("⚠️  No hay releases disponibles")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="📦 Releases Disponibles")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Nombre", style="magenta", min_width=20)
            table.add_column("Tag", style="green")
            table.add_column("Fecha", style="blue")
            table.add_column("Assets", justify="center")
            table.add_column("Tamaño", justify="right")
            
            for i, release in enumerate(releases, 1):
                # Formatear fecha
                published_date = datetime.strptime(
                    release['published_at'], 
                    "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%Y-%m-%d")
                
                # Calcular tamaño total de assets
                total_size = sum(asset['size'] for asset in release['assets'])
                size_str = self._format_size(total_size) if total_size > 0 else "N/A"
                
                table.add_row(
                    str(i),
                    release['name'] or "Sin nombre",
                    release['tag_name'],
                    published_date,
                    str(len(release['assets'])),
                    size_str
                )
            
            self.console.print(table)
        else:
            # Fallback para cuando rich no esté disponible
            print("\n📦 RELEASES DISPONIBLES")
            print("=" * 80)
            for i, release in enumerate(releases, 1):
                published_date = datetime.strptime(
                    release['published_at'], 
                    "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%Y-%m-%d")
                
                total_size = sum(asset['size'] for asset in release['assets'])
                size_str = self._format_size(total_size) if total_size > 0 else "N/A"
                
                print(f"{i:2}. {release['name'] or 'Sin nombre'}")
                print(f"    Tag: {release['tag_name']}")
                print(f"    Fecha: {published_date}")
                print(f"    Assets: {len(release['assets'])} archivos ({size_str})")
                print()
    
    def display_assets(self, assets: List[Dict]) -> None:
        """
        Muestra los assets de una release
        """
        if not assets:
            self._print_warning("⚠️  Esta release no tiene archivos para descargar")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="📁 Archivos Disponibles")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Nombre", style="magenta", min_width=30)
            table.add_column("Tamaño", justify="right", style="green")
            table.add_column("Descargas", justify="center", style="blue")
            
            for i, asset in enumerate(assets, 1):
                table.add_row(
                    str(i),
                    asset['name'],
                    self._format_size(asset['size']),
                    str(asset['download_count'])
                )
            
            self.console.print(table)
        else:
            print("\n📁 ARCHIVOS DISPONIBLES")
            print("=" * 60)
            for i, asset in enumerate(assets, 1):
                print(f"{i:2}. {asset['name']}")
                print(f"    Tamaño: {self._format_size(asset['size'])}")
                print(f"    Descargas: {asset['download_count']}")
                print()
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Convierte bytes a formato legible
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def download_file(self, asset: Dict, download_path: str = "./downloads") -> bool:
        """
        Descarga un archivo específico
        """
        # Crear directorio de descarga si no existe
        Path(download_path).mkdir(parents=True, exist_ok=True)
        
        file_path = Path(download_path) / asset['name']
        url = asset['browser_download_url']
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Descargando[/bold blue]"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    DownloadColumn(),
                    "•",
                    TransferSpeedColumn(),
                    "•",
                    TimeRemainingColumn(),
                ) as progress:
                    
                    task = progress.add_task(
                        f"[green]{asset['name']}", 
                        total=total_size
                    )
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
            else:
                print(f"📥 Descargando {asset['name']}...")
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            self._print_success(f"✅ Descargado: {asset['name']}")
            return True
            
        except Exception as e:
            self._print_error(f"❌ Error al descargar {asset['name']}: {e}")
            return False
    
    def download_multiple_files(self, assets: List[Dict], download_path: str = "./downloads") -> int:
        """
        Descarga múltiples archivos
        
        Returns:
            Número de archivos descargados exitosamente
        """
        successful_downloads = 0
        
        for asset in assets:
            if self.download_file(asset, download_path):
                successful_downloads += 1
        
        return successful_downloads
    
    def interactive_menu(self) -> None:
        """
        Menú interactivo principal
        """
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold magenta]GitHub Releases Downloader[/bold magenta]\n"
                f"[blue]Repositorio: {self.repo}[/blue]\n"
                f"[green]Token configurado: {'Sí' if self.token else 'No'}[/green]",
                title="🚀 Bienvenido"
            ))
        else:
            print("\n🚀 GITHUB RELEASES DOWNLOADER")
            print("=" * 50)
            print(f"Repositorio: {self.repo}")
            print(f"Token configurado: {'Sí' if self.token else 'No'}")
            print()
        
        while True:
            if RICH_AVAILABLE:
                self.console.print("\n[bold cyan]¿Qué deseas hacer?[/bold cyan]")
                print("1. 📋 Ver releases disponibles")
                print("2. ⚡ Descarga rápida (última release completa)")
                print("3. 🎯 Descarga selectiva")
                print("4. 🔑 Configurar token de GitHub")
                print("5. 🚪 Salir")
                
                choice = Prompt.ask("Selecciona una opción", choices=["1", "2", "3", "4", "5"])
            else:
                print("\n¿Qué deseas hacer?")
                print("1. 📋 Ver releases disponibles")
                print("2. ⚡ Descarga rápida (última release completa)")
                print("3. 🎯 Descarga selectiva")
                print("4. 🔑 Configurar token de GitHub")
                print("5. 🚪 Salir")
                choice = input("Selecciona una opción (1-5): ").strip()
            
            if choice == "1":
                self._show_releases()
            elif choice == "2":
                self._quick_download()
            elif choice == "3":
                self._selective_download()
            elif choice == "4":
                self.configure_token()
            elif choice == "5":
                self._print_success("👋 ¡Hasta luego!")
                break
            else:
                self._print_error("❌ Opción no válida")
    
    def _show_releases(self) -> None:
        """Muestra las releases disponibles"""
        releases = self.get_releases()
        if releases:
            self.display_releases(releases)
    
    def _quick_download(self) -> None:
        """Descarga rápida de la última release completa"""
        releases = self.get_releases(1)
        if not releases:
            return
        
        latest_release = releases[0]
        assets = latest_release['assets']
        
        if not assets:
            self._print_warning("⚠️  La última release no tiene archivos para descargar")
            return
        
        self._print_info(f"📦 Descargando todos los archivos de: {latest_release['name']}")
        self.display_assets(assets)
        
        if RICH_AVAILABLE:
            if not Confirm.ask("\n¿Continuar con la descarga?"):
                return
        else:
            confirm = input("\n¿Continuar con la descarga? (s/N): ").lower()
            if confirm != 's':
                return
        
        successful = self.download_multiple_files(assets)
        self._print_success(f"✅ Descarga completada: {successful}/{len(assets)} archivos")
    
    def _selective_download(self) -> None:
        """Descarga selectiva de archivos"""
        releases = self.get_releases()
        if not releases:
            return
        
        self.display_releases(releases)
        
        # Seleccionar release
        if RICH_AVAILABLE:
            release_choice = Prompt.ask(
                "Selecciona el número de la release",
                default="1"
            )
        else:
            release_choice = input("Selecciona el número de la release (1): ").strip() or "1"
        
        try:
            release_index = int(release_choice) - 1
            if release_index < 0 or release_index >= len(releases):
                self._print_error("❌ Número de release inválido")
                return
        except ValueError:
            self._print_error("❌ Por favor ingresa un número válido")
            return
        
        selected_release = releases[release_index]
        assets = selected_release['assets']
        
        if not assets:
            self._print_warning("⚠️  Esta release no tiene archivos para descargar")
            return
        
        self._print_info(f"📦 Release seleccionada: {selected_release['name']}")
        self.display_assets(assets)
        
        # Seleccionar archivos
        if RICH_AVAILABLE:
            file_choices = Prompt.ask(
                "Selecciona los números de archivo (ej: 1,3,5 o 'all' para todos)",
                default="all"
            )
        else:
            file_choices = input("Selecciona archivos (ej: 1,3,5 o 'all'): ").strip() or "all"
        
        if file_choices.lower() == 'all':
            selected_assets = assets
        else:
            try:
                indices = [int(x.strip()) - 1 for x in file_choices.split(',')]
                selected_assets = [assets[i] for i in indices if 0 <= i < len(assets)]
            except (ValueError, IndexError):
                self._print_error("❌ Selección de archivos inválida")
                return
        
        if not selected_assets:
            self._print_warning("⚠️  No se seleccionaron archivos válidos")
            return
        
        # Confirmar y descargar
        self._print_info(f"📥 Se descargarán {len(selected_assets)} archivo(s)")
        
        if RICH_AVAILABLE:
            if not Confirm.ask("¿Continuar?"):
                return
        else:
            confirm = input("¿Continuar? (s/N): ").lower()
            if confirm != 's':
                return
        
    def display_assets(self, assets: List[Dict]) -> None:
        """
        Muestra los assets de una release (versión básica)
        """
        if not assets:
            self._print_warning("⚠️  Esta release no tiene archivos para descargar")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="📁 Archivos Disponibles")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Nombre", style="magenta", min_width=30)
            table.add_column("Tamaño", justify="right", style="green")
            table.add_column("Descargas", justify="center", style="blue")
            
            for i, asset in enumerate(assets, 1):
                table.add_row(
                    str(i),
                    asset['name'],
                    self._format_size(asset['size']),
                    str(asset['download_count'])
                )
            
            self.console.print(table)
        else:
            print("\n📁 ARCHIVOS DISPONIBLES")
            print("=" * 60)
            for i, asset in enumerate(assets, 1):
                print(f"{i:2}. {asset['name']}")
                print(f"    Tamaño: {self._format_size(asset['size'])}")
                print(f"    Descargas: {asset['download_count']}")
                print()
    
    def _detailed_download(self) -> None:
        """
        Descarga detallada con selección individual de archivos
        """
        releases = self.get_releases()
        if not releases:
            return
        
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold cyan]🔍 Descarga Detallada[/bold cyan]\n\n"
                "Esta opción te permite:\n"
                "• Ver información detallada de cada archivo\n"
                "• Seleccionar archivos individuales\n"
                "• Obtener estimaciones de tiempo de descarga\n"
                "• Ver estadísticas completas de cada release",
                title="💡 Información"
            ))
        else:
            print("\n🔍 DESCARGA DETALLADA")
            print("=" * 50)
            print("Esta opción te permite ver información detallada y seleccionar archivos individuales")
            print()
        
        self.display_releases(releases)
        
        # Seleccionar release
        if RICH_AVAILABLE:
            release_choice = Prompt.ask(
                "Selecciona el número de la release",
                default="1"
            )
        else:
            release_choice = input("Selecciona el número de la release (1): ").strip() or "1"
        
        try:
            release_index = int(release_choice) - 1
            if release_index < 0 or release_index >= len(releases):
                self._print_error("❌ Número de release inválido")
                return
        except ValueError:
            self._print_error("❌ Por favor ingresa un número válido")
            return
        
        selected_release = releases[release_index]
        assets = selected_release['assets']
        
        if not assets:
            self._print_warning("⚠️  Esta release no tiene archivos para descargar")
            return
        
        # Mostrar archivos con información detallada
        while True:
            self.display_assets_detailed(assets, selected_release['name'])
            
            if RICH_AVAILABLE:
                self.console.print("\n[bold cyan]Opciones disponibles:[/bold cyan]")
                print("• Número del archivo: Ver detalles y descargar")
                print("• 'all': Descargar todos los archivos")
                print("• 'back': Volver al menú anterior")
                print("• 'menu': Volver al menú principal")
                
                choice = Prompt.ask("Selecciona una opción").strip().lower()
            else:
                print("\nOpciones disponibles:")
                print("• Número del archivo: Ver detalles y descargar")
                print("• 'all': Descargar todos los archivos")
                print("• 'back': Volver al menú anterior")
                print("• 'menu': Volver al menú principal")
                choice = input("Selecciona una opción: ").strip().lower()
            
            if choice == 'back':
                break
            elif choice == 'menu':
                return
            elif choice == 'all':
                self._download_all_from_detailed(assets, selected_release['name'])
                break
            else:
                # Intentar parsear como número de archivo
                try:
                    file_index = int(choice) - 1
                    if 0 <= file_index < len(assets):
                        selected_asset = assets[file_index]
                        self._handle_individual_file(selected_asset)
                    else:
                        self._print_error("❌ Número de archivo inválido")
                except ValueError:
                    self._print_error("❌ Opción no válida")
    
    def _handle_individual_file(self, asset: Dict) -> None:
        """
        Maneja la selección de un archivo individual
        """
        while True:
            self._show_file_details(asset)
            
            if RICH_AVAILABLE:
                self.console.print("\n[bold cyan]¿Qué deseas hacer con este archivo?[/bold cyan]")
                print("1. 📥 Descargar este archivo")
                print("2. 📋 Copiar URL de descarga")
                print("3. 🔙 Volver a la lista de archivos")
                
                action = Prompt.ask("Selecciona una opción", choices=["1", "2", "3"])
            else:
                print("¿Qué deseas hacer con este archivo?")
                print("1. 📥 Descargar este archivo")
                print("2. 📋 Copiar URL de descarga")
                print("3. 🔙 Volver a la lista de archivos")
                action = input("Selecciona una opción (1-3): ").strip()
            
            if action == "1":
                # Confirmar descarga
                if RICH_AVAILABLE:
                    if Confirm.ask(f"¿Descargar '{asset['name']}'?"):
                        if self.download_file(asset):
                            self._print_success("✅ ¡Descarga completada exitosamente!")
                        else:
                            self._print_error("❌ Error durante la descarga")
                        
                        if not Confirm.ask("¿Descargar otro archivo?"):
                            return
                        else:
                            break
                else:
                    confirm = input(f"¿Descargar '{asset['name']}'? (s/N): ").lower()
                    if confirm == 's':
                        if self.download_file(asset):
                            print("✅ ¡Descarga completada exitosamente!")
                        else:
                            print("❌ Error durante la descarga")
                        
                        another = input("¿Descargar otro archivo? (s/N): ").lower()
                        if another != 's':
                            return
                        else:
                            break
            
            elif action == "2":
                # Mostrar URL de descarga
                download_url = asset['browser_download_url']
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold blue]URL de descarga:[/bold blue]\n{download_url}\n\n"
                        "[bold yellow]💡 Consejo:[/bold yellow] Puedes usar esta URL con wget, curl o tu gestor de descargas favorito",
                        title="🔗 URL de Descarga"
                    ))
                    input("Presiona Enter para continuar...")
                else:
                    print(f"\n🔗 URL de descarga:")
                    print(download_url)
                    print("\n💡 Consejo: Puedes usar esta URL con wget, curl o tu gestor de descargas favorito")
                    input("Presiona Enter para continuar...")
            
            elif action == "3":
                break
            else:
                self._print_error("❌ Opción no válida")
    
    def _download_all_from_detailed(self, assets: List[Dict], release_name: str) -> None:
        """
        Descarga todos los archivos desde la vista detallada
        """
        total_size = sum(asset['size'] for asset in assets)
        
        if RICH_AVAILABLE:
            self.console.print(Panel(
                f"[bold blue]Release:[/bold blue] {release_name}\n"
                f"[bold green]Total archivos:[/bold green] {len(assets)}\n"
                f"[bold yellow]Tamaño total:[/bold yellow] {self._format_size(total_size)}\n"
                f"[bold cyan]Tiempo estimado:[/bold cyan] {self._estimate_download_time(total_size)}",
                title="📦 Confirmación de Descarga Masiva"
            ))
            
            if not Confirm.ask("¿Proceder con la descarga de todos los archivos?"):
                return
        else:
            print(f"\n📦 CONFIRMACIÓN DE DESCARGA MASIVA")
            print("=" * 50)
            print(f"Release: {release_name}")
            print(f"Total archivos: {len(assets)}")
            print(f"Tamaño total: {self._format_size(total_size)}")
            print(f"Tiempo estimado: {self._estimate_download_time(total_size)}")
            
            confirm = input("¿Proceder con la descarga? (s/N): ").lower()
            if confirm != 's':
                return
        
        successful = self.download_multiple_files(assets)
        
        if RICH_AVAILABLE:
            if successful == len(assets):
                self.console.print(Panel(
                    f"[bold green]✅ ¡Descarga completada![/bold green]\n\n"
                    f"Archivos descargados: {successful}/{len(assets)}\n"
                    f"Ubicación: ./downloads/\n"
                    f"Tamaño total: {self._format_size(total_size)}",
                    title="🎉 Descarga Exitosa"
                ))
            else:
                self.console.print(Panel(
                    f"[bold yellow]⚠️  Descarga parcialmente completada[/bold yellow]\n\n"
                    f"Archivos descargados: {successful}/{len(assets)}\n"
                    f"Archivos fallidos: {len(assets) - successful}\n"
                    f"Ubicación: ./downloads/",
                    title="📊 Resultado de Descarga"
                ))
        else:
            print(f"\n✅ Descarga completada: {successful}/{len(assets)} archivos")
            if successful < len(assets):
                print(f"⚠️  {len(assets) - successful} archivos no se pudieron descargar")


def main():
    """
    Función principal del programa
    """
    parser = argparse.ArgumentParser(
        description="GitHub Releases Downloader - Descarga releases de GitHub de forma profesional"
    )
    parser.add_argument(
        "--repo", 
        default="eden-emulator/Releases",
        help="Repositorio de GitHub (formato: usuario/repo)"
    )
    parser.add_argument(
        "--configure-token",
        action="store_true",
        help="Configurar token de GitHub al inicio"
    )
    
    args = parser.parse_args()
    
    # Verificar dependencias opcionales
    if not RICH_AVAILABLE:
        print("💡 Consejo: Instala 'rich' para una mejor experiencia visual:")
        print("   pip install rich")
        print()
    
    try:
        downloader = GitHubReleasesDownloader(args.repo)
        
        if args.configure_token:
            downloader.configure_token()
        
        downloader.interactive_menu()
        
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

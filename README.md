# **GitHub Releases Downloader CLI**

---

### Descripción

Esta es una **herramienta de línea de comandos (CLI)**, potente y fácil de usar, diseñada para simplificar el proceso de descarga de *releases* (versiones) desde cualquier repositorio de GitHub. Con solo unos pocos comandos, podrás listar las versiones disponibles y descargar archivos específicos o todos los *assets* de una *release* completa.

### Características Principales

* **Listado Inteligente**: Muestra de forma clara y organizada las últimas *releases* de un repositorio, incluyendo el nombre, la etiqueta (*tag*) y la fecha de publicación.
* **Descarga Flexible**: Elige entre descargar un solo archivo de una *release* o descargar todos los *assets* de la última versión disponible.
* **Autenticación Opcional**: Funciona sin necesidad de autenticación, pero si proporcionas un **token de GitHub**, la herramienta utilizará la API con un límite de tasa más alto para descargas más rápidas y fiables.
* **Interfaz Moderna**: Utiliza una interfaz de usuario limpia, interactiva y con colores para una mejor experiencia en la terminal.

Ideal para desarrolladores, usuarios de *software* de código abierto y cualquier persona que necesite automatizar la descarga de versiones de proyectos de GitHub.

🚀 Bienvenido
┌────────────────────────────────────────┐
│    GitHub Releases Downloader          │
│    Repositorio: eden-emulator/Releases │# GitHub Releases Downloader CLI

Una herramienta de línea de comandos profesional para descargar releases de repositorios de GitHub de manera fácil y eficiente.

## 🌟 Características

- **Interfaz Intuitiva**: Menú interactivo con colores y formato profesional
- **Autenticación Opcional**: Soporte para tokens de GitHub para mayor límite de API
- **Descarga Flexible**: 
  - Descarga rápida de la última release completa
  - Selección individual de archivos específicos
  - Descarga masiva de múltiples archivos
- **Visualización Clara**: Tablas formateadas con información detallada de releases
- **Manejo Robusto de Errores**: Validación y manejo adecuado de errores de red
- **Progreso Visual**: Barras de progreso durante las descargas

## 📋 Requisitos

- Python 3.7 o superior
- Conexión a internet

## 🚀 Instalación

### Opción 1: Instalación básica
```bash
# Clonar o descargar el script
wget https://raw.githubusercontent.com/andromux/releases_download_eden/refs/heads/main/download_eden.py

# GitHub Releases Downloader - Dependencias
# Autor: Andromux ORG
# Versión: 1.0.0

# Dependencias principales (obligatorias)
requests>=2.31.0

# Dependencias para interfaz mejorada (opcionales pero recomendadas)
rich>=13.0.0

# Dependencias del sistema (ya incluidas en Python 3.x)
# pathlib - incluida desde Python 3.4+
# json - incluida en biblioteca estándar
# os - incluida en biblioteca estándar  
# sys - incluida en biblioteca estándar
# datetime - incluida en biblioteca estándar
# argparse - incluida desde Python 3.2+
# typing - incluida desde Python 3.5+
```

### Opción 2: Instalación completa (recomendada)
```bash
# Instalar todas las dependencias para mejor experiencia
pip install requests rich

# O usando el archivo requirements.txt
pip install -r requirements.txt
```

## 💡 Uso

### Uso Básico
```bash
# Ejecutar con repositorio por defecto (eden-emulator/Releases)
python download_eden.py

# Especificar un repositorio diferente
python download_eden.py --repo usuario/nombre-repo
```

### Configuración del Token de GitHub (Opcional)

Para aumentar el límite de solicitudes de la API de GitHub, puedes configurar un Personal Access Token:

1. **Crear token en GitHub**:
   - Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Genera un nuevo token con permisos `public_repo`
   - Copia el token generado

2. **Configurar en la aplicación**:
   ```bash
   # Configurar token al inicio
   python download_eden.py --configure-token
   
   # O configúralo desde el menú interactivo (opción 4)
   ```

El token se guardará automáticamente en `.secret_token.json` para uso futuro.

## 🎯 Funcionalidades

### 1. Ver Releases Disponibles
- Lista todas las releases del repositorio
- Muestra información detallada: nombre, tag, fecha, número de archivos, tamaño total
- Formato de tabla clara y legible

### 2. Descarga Rápida
- Descarga automáticamente todos los archivos de la última release
- Confirmación antes de iniciar la descarga
- Progreso visual en tiempo real

### 3. Descarga Selectiva
- Selecciona una release específica
- Elige archivos individuales o múltiples
- Soporte para selección por números (ej: 1,3,5)

### 4. Configuración de Token
- Validación automática del token
- Almacenamiento seguro en archivo local
- Funcionamiento sin token con límites públicos de API

## 📁 Estructura de Archivos

```
./
├── download_eden.py  # Script principal
├── requirements.txt               # Dependencias
├── .secret_token.json            # Token de GitHub (se crea automáticamente)
└── downloads/                    # Carpeta de descargas (se crea automáticamente)
    ├── archivo1.zip
    ├── archivo2.exe
    └── ...
```

## 🔧 Opciones de Línea de Comandos

```bash
python download_eden.py [opciones]

Opciones:
  --repo REPO           Repositorio GitHub (formato: usuario/repo)
                       Por defecto: eden-emulator/Releases
  --configure-token     Configurar token de GitHub al inicio
  -h, --help           Mostrar ayuda y salir
```

## 📸 Screenshots

### Menú Principal
<img width="2560" height="1074" alt="pythonimage" src="https://github.com/user-attachments/assets/7ae65ff5-3c4e-4ed0-bba6-70c7dbb61e20" />


### Lista de Releases

<img width="2560" height="1105" alt="list" src="https://github.com/user-attachments/assets/5cebb9df-9d2d-4bb8-b4e6-23feb8c623a9" />


## ⚠️ Limitaciones de la API de GitHub

- **Sin token**: 60 solicitudes por hora
- **Con token**: 5,000 solicitudes por hora

Para uso intensivo, se recomienda configurar un token de GitHub.

## 🐛 Solución de Problemas

### Error: "Module 'rich' not found"
```bash
pip install rich
```

### Error: "Token inválido"
- Verifica que el token tenga permisos `public_repo`
- Regenera el token en GitHub si es necesario

### Error de conexión
- Verifica tu conexión a internet
- Comprueba que el repositorio exista y sea público

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Puedes usarlo libremente para proyectos personales y comerciales.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork del repositorio
2. Crea una rama para tu feature
3. Commit con mensajes descriptivos
4. Push y crea un Pull Request

## 📞 Soporte

Si encuentras algún problema o tienes sugerencias:
- Abre un issue en GitHub
- Describe

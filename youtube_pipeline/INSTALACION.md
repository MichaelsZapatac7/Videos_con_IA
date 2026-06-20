# Guía de Instalación Paso a Paso — Windows y Mac

Esta guía te lleva de cero a tu primer video generado. Sigue los pasos en orden.
No necesitas saber programar — solo copiar y pegar comandos.

---

# 🪟 WINDOWS — Paso a Paso

## Paso 1: Instalar Python

1. Ve a https://www.python.org/downloads/
2. Haz clic en el botón amarillo **"Download Python 3.12"**
3. Abre el archivo descargado
4. ⚠️ **MUY IMPORTANTE:** marca la casilla **"Add Python to PATH"** abajo antes de instalar
5. Haz clic en **"Install Now"**
6. Espera a que termine y cierra

**Verificar:** Abre el menú inicio → escribe `cmd` → Enter. En la ventana negra escribe:
```cmd
python --version
```
Debe mostrar algo como `Python 3.12.x`. Si dice "no se reconoce", reinstala marcando "Add to PATH".

## Paso 2: Instalar FFmpeg (el motor de edición)

**Opción fácil (recomendada):** En la ventana `cmd` escribe:
```cmd
winget install ffmpeg
```
Espera a que termine. Cierra y vuelve a abrir `cmd`.

**Verificar:**
```cmd
ffmpeg -version
```
Debe mostrar información de FFmpeg. Si falla, reinicia el PC y prueba de nuevo.

## Paso 3: Descargar el proyecto

En `cmd`:
```cmd
cd %USERPROFILE%\Desktop
git clone https://github.com/MichaelsZapatac7/IA.git
cd IA
```

> Si no tienes `git`, instálalo con: `winget install Git.Git` (cierra y reabre cmd después).

## Paso 4: Instalar las dependencias del proyecto

```cmd
pip install -r youtube_pipeline\requirements.txt
```

## Paso 5: Configurar tus API keys

```cmd
copy youtube_pipeline\.env.example youtube_pipeline\.env
notepad youtube_pipeline\.env
```
Se abre el Bloc de notas. Pega tus API keys (ver la guía `GUIA_API_KEYS.md`).
Guarda con `Ctrl + S` y cierra.

## Paso 6: ¡Generar tu primer video!

```cmd
python -m youtube_pipeline.main --topic "Los 5 modelos de IA mas importantes de 2026"
```

El video final aparece en la carpeta `output\`.

---

# 🍎 MAC — Paso a Paso

## Paso 1: Instalar Homebrew (gestor de programas)

1. Abre **Terminal** (Cmd + Espacio → escribe "Terminal" → Enter)
2. Pega esto y dale Enter:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
3. Te pedirá tu contraseña de Mac (no se ve mientras escribes, es normal). Enter.
4. Al terminar, si te dice que agregues algo al PATH, copia y pega esos 2 comandos que aparecen.

## Paso 2: Instalar Python y FFmpeg

```bash
brew install python ffmpeg git
```

**Verificar:**
```bash
python3 --version
ffmpeg -version
```
Ambos deben mostrar información de versión.

## Paso 3: Descargar el proyecto

```bash
cd ~/Desktop
git clone https://github.com/MichaelsZapatac7/IA.git
cd IA
```

## Paso 4: Instalar las dependencias

```bash
pip3 install -r youtube_pipeline/requirements.txt
```

> Si da un error de "externally-managed-environment", usa:
> `pip3 install --user -r youtube_pipeline/requirements.txt`

## Paso 5: Configurar tus API keys

```bash
cp youtube_pipeline/.env.example youtube_pipeline/.env
open -e youtube_pipeline/.env
```
Se abre TextEdit. Pega tus API keys (ver `GUIA_API_KEYS.md`).
Guarda con `Cmd + S` y cierra.

## Paso 6: ¡Generar tu primer video!

```bash
python3 -m youtube_pipeline.main --topic "Los 5 modelos de IA mas importantes de 2026"
```

El video final aparece en la carpeta `output/`.

---

# 🎬 Comandos útiles (Windows y Mac)

> En Windows usa `python`, en Mac usa `python3`.

**Video largo normal:**
```bash
python3 -m youtube_pipeline.main --topic "Tu tema aquí"
```

**YouTube Short (vertical, menos de 60s):**
```bash
python3 -m youtube_pipeline.main --topic "Tu tema aquí" --shorts
```

**Video en inglés:**
```bash
python3 -m youtube_pipeline.main --topic "Your topic" --lang en
```

**Video largo + 3 Shorts automáticos del mismo tema:**
```bash
python3 -m youtube_pipeline.main --topic "Tu tema" --also-shorts
```

**Con música de fondo y logo:**
```bash
python3 -m youtube_pipeline.main --topic "Tu tema" --music musica.mp3 --logo logo.png
```

---

# ❓ Problemas comunes

| Error | Solución |
|-------|----------|
| `python no se reconoce` (Windows) | Reinstala Python marcando "Add to PATH" |
| `ffmpeg not found` | Reinstala FFmpeg y reinicia la terminal |
| `Missing environment variables` | Revisa que tu archivo `.env` tenga las keys correctas |
| `401 Unauthorized` | Una API key está mal copiada o vencida |
| `ModuleNotFoundError` | Corre de nuevo el `pip install -r ...` |
| Subtítulos no aparecen | Es opcional, el video se genera igual |

---

# 🔧 Activar el MCP (para que Claude edite por ti)

Una vez que el pipeline básico funcione, sigue `mcp_setup/README.md` para conectar
el servidor MCP de edición a Claude Desktop. Después podrás pedirle a Claude
directamente: *"recorta este video"*, *"agrega subtítulos"*, *"únelos con fundidos"*.

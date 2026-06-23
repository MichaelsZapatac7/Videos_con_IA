# 🎬 MZSHARD — Pipeline de videos animados (IA + Datos)

De una idea a un **video completo (16:9)** + un **Short (9:16)** animados con
**Remotion**, narrados con **tu voz** y con música y logo del canal. Un comando.

```powershell
.\produce.ps1 "Los 5 errores que arruinan un Data Lake" -voz f5
```

Las entregas quedan en **`entregas\`**.

---

## ⚡ Comando rápido (lo que usarás siempre)

Abre PowerShell en la carpeta del proyecto y:

```powershell
# Un video, con tu voz clonada (gratis):
.\produce.ps1 "BigQuery vs Snowflake: cuál elegir en 2026" -voz f5

# Con indicaciones para el guion, y en ElevenLabs:
.\produce.ps1 "Data Governance para principiantes" -voz elevenlabs -detalles "tono directo, ejemplos reales"

# Desde un guion ya escrito (no gasta API de Claude):
.\produce.ps1 "Entrevista Data Architect" -planfile youtube_pipeline\examples\plans\p11_entrevista_data_architect.json -voz f5

# VARIOS videos de golpe (una idea por línea en el .txt):
.\produce.ps1 -lote mis_ideas.txt -voz elevenlabs
```

Parámetros: `-voz f5|elevenlabs` · `-detalles "..."` · `-planfile <ruta>` ·
`-lote <archivo>` · `-musica <nombre_pista>` · `-velocidad 0.9` (F5 más lenta) ·
`-noshort` (no generar el Short).

**Formato del archivo de lote** (`mis_ideas.txt`): una idea por línea; opcional
`tema | detalles`:

```
Los 7 conceptos de SQL que todo Data Engineer debe dominar | enfoque práctico
Delta Lake vs Iceberg en 2026
Cómo diseñar un Lakehouse desde cero | para alguien que viene de Excel
```

---

## 🎙️ Las dos voces

| Voz | Cómo | Cuándo usarla |
|-----|------|---------------|
| **`f5`** | Tu voz clonada local (F5-TTS), **gratis** | Contenido general. Ver [PENDIENTES_VOZ_F5.md](PENDIENTES_VOZ_F5.md) |
| **`elevenlabs`** | Tu voz en ElevenLabs (API de pago) | **Términos técnicos en inglés** (más clara) hasta pulir F5 |

> Por ahora, para videos muy técnicos conviene `elevenlabs`; F5 tiene 2 ajustes
> pendientes (velocidad y una muletilla). Detalle en `PENDIENTES_VOZ_F5.md`.

---

## 🧩 Cómo funciona (resumen)

`youtube_pipeline/producir.py` (corre dentro de `.venv-voz`) hace todo:

1. **Guion** → Claude (API) a partir del tema + detalles, o un `--plan-file` JSON.
2. **Voz** → F5 (local, torch) o ElevenLabs (API), un audio por segmento.
3. **Imágenes** → Pexels (verticales para el Short, horizontales para el completo).
4. **Animación** → manifests + render con **Remotion** (`remotion/`), con música
   (`media/music/`) en bucle al 20% y voz al 100%, y logo (`media/logo/`).
5. **Entrega** → comprime a `entregas/<Título>_COMPLETO_ANIMADO.mp4` y `_SHORT_ANIMADO.mp4`.

Todo se llama por HTTP (`requests`), sin SDKs pesados ni el stack viejo de ffmpeg.

---

## 🛠️ Puesta a punto (solo la primera vez / tras clonar)

1. **Entorno de voz F5** (Python 3.11 + torch cu128 + F5): sigue
   [SETUP_VOZ_LOCAL.md](SETUP_VOZ_LOCAL.md). Crea `.venv-voz/`.
2. **Remotion**: `cd remotion; npm install` (node_modules está gitignored).
3. **Claves**: crea `youtube_pipeline/.env` (no se versiona) con:
   ```
   ANTHROPIC_API_KEY=...     # guion con Claude
   PEXELS_API_KEY=...        # imágenes (gratis)
   ELEVENLABS_API_KEY=...    # solo si usas -voz elevenlabs
   ELEVENLABS_VOICE_ID=94zOad0g7T7K4oa7zhDq
   ```
4. **Música y logo**: ya están en `media/music/` y `media/logo/`.

---

## 📂 Estructura

```
produce.ps1                      # comando rápido (wrapper)
entregas/                        # videos finales (gitignored)
media/                           # logo + música del canal
remotion/                        # proyecto Remotion (animaciones)
youtube_pipeline/
  producir.py                    # ⭐ pipeline unificado (úsalo)
  examples/plans/*.json          # guiones (formato de plan); p11 = entrevista
  generators/voiceover_f5.py     # motor F5
  generators/voiceover_elevenlabs.py
  .env                           # claves (no se versiona)
SETUP_VOZ_LOCAL.md               # instalar la voz F5
PENDIENTES_VOZ_F5.md             # ajustes pendientes de F5
```

> `youtube_pipeline/main.py` y el render por ffmpeg son el camino **anterior**
> (legacy). El camino actual y recomendado es **`producir.py`** + Remotion.

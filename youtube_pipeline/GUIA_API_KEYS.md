# Guía Paso a Paso — Cómo Conseguir Cada API Key

El pipeline necesita 3 keys obligatorias y 1 opcional. Aquí está el proceso
exacto para cada una. Al final pegas todas en tu archivo `.env`.

> ⚠️ **Nunca compartas tus API keys ni las subas a GitHub.** El archivo `.env`
> ya está protegido para que no se suba por accidente.

---

## 1️⃣ ANTHROPIC_API_KEY (genera los guiones con Claude) — OBLIGATORIA

**Costo:** ~$0.003 USD por guión (centavos). Te dan crédito gratis al registrarte.

1. Ve a https://console.anthropic.com
2. Regístrate con tu correo (michaels.zapatac@gmail.com) o con Google
3. Verifica tu correo
4. En el menú izquierdo haz clic en **"API Keys"**
   (o ve directo a https://console.anthropic.com/settings/keys)
5. Haz clic en **"Create Key"**
6. Ponle un nombre, por ejemplo: `youtube-pipeline`
7. Haz clic en **"Add"** / **"Create"**
8. ⚠️ **Copia la key COMPLETA inmediatamente** (empieza con `sk-ant-...`).
   Solo se muestra una vez. Si la pierdes, creas otra.
9. Para usarla necesitas crédito: ve a **"Billing"** → **"Add credits"** y
   carga $5 USD (alcanza para cientos de guiones).

**En tu `.env`:**
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
```

---

## 2️⃣ ELEVENLABS_API_KEY (genera las voces) — OBLIGATORIA

**Costo:** Plan gratis incluye ~10 min de audio/mes. Plan Starter $5/mes = 30 min.

1. Ve a https://elevenlabs.io
2. Haz clic en **"Sign Up"** y regístrate (correo o Google)
3. Verifica tu correo
4. Una vez dentro, haz clic en tu **foto de perfil** (esquina inferior izquierda)
5. Selecciona **"API Keys"**
   (o ve directo a https://elevenlabs.io/app/settings/api-keys)
6. Haz clic en **"Create API Key"**
7. Ponle nombre `youtube-pipeline` y dale **"Create"**
8. **Copia la key** (empieza con `sk_...`)

**Elegir la voz (opcional pero recomendado):**
1. Ve a https://elevenlabs.io/app/voice-library
2. Escucha voces en español que te gusten
3. Cuando elijas una, haz clic en los **3 puntos → "Copy Voice ID"**
4. Pega ese ID en `ELEVENLABS_VOICE_ID` de tu `.env`
   (Si no lo cambias, usa "Rachel" por defecto, que habla multilingüe.)

**En tu `.env`:**
```
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

---

## 3️⃣ PEXELS_API_KEY (descarga clips de video gratis) — OBLIGATORIA

**Costo:** 100% GRATIS. 200 descargas/hora, 20.000/mes.

1. Ve a https://www.pexels.com/api/
2. Haz clic en **"Get Started"** / **"Obtén una clave de API"**
3. Regístrate (correo o Google)
4. Te preguntará para qué la usas — responde algo como:
   *"Generar contenido de video para mi canal de YouTube"*
5. Tu API key aparece **inmediatamente** en la pantalla
   (o en https://www.pexels.com/api/new/)
6. Cópiala (es una cadena larga de letras y números)

**En tu `.env`:**
```
PEXELS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 4️⃣ HIGGSFIELD_API_KEY (genera clips con IA) — OPCIONAL

**Costo:** Starter $15/mes (200 créditos). Solo si quieres clips generados por IA
en vez de stock footage. **El pipeline funciona perfecto sin esto.**

1. Ve a https://higgsfield.ai
2. Regístrate y elige un plan de pago (la API requiere plan pago)
3. Ve a la sección **"API"** o **"Developers"** en tu cuenta
4. Genera tu API key y cópiala

**En tu `.env`:**
```
HIGGSFIELD_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

> Si dejas esta vacía, el pipeline usa solo Pexels (stock footage gratis). Recomiendo
> empezar SIN Higgsfield y agregarlo después si quieres más estilo cinematográfico.

---

## ✅ Tu archivo `.env` final debe verse así

```env
# Obligatorias
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxx
PEXELS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Opcional (déjala vacía si no la usas)
HIGGSFIELD_API_KEY=

# Tu canal
CHANNEL_NAME=@mzcshard
PRIMARY_COLOR=#FF6B35
SECONDARY_COLOR=#1A1A2E
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

---

## 💰 Resumen de costos mensuales

| Servicio | Costo mínimo | Para qué |
|----------|-------------|----------|
| Anthropic (Claude) | ~$5 (dura meses) | Guiones |
| ElevenLabs | $0 gratis / $5 starter | Voces |
| Pexels | **$0 gratis** | Footage |
| Higgsfield | $0 (opcional) / $15 | Clips IA |
| **TOTAL para empezar** | **~$5-10/mes** | Canal completo |

Con esto produces decenas de videos al mes. Un solo video monetizado puede
recuperar la inversión de varios meses.

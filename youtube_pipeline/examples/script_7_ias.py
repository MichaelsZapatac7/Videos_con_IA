"""
Guión de ejemplo: "Las 7 IA más poderosas actualmente"
Escrito directamente (sin llamar a la API) para el video demo del canal @mzcshard.

Empieza con Fable 5 y su limitante actual de uso, y recorre otras 6 IAs clave de 2026.
Este mismo objeto VideoScript es el que produce el pipeline normal con Claude,
así que sirve como plantilla de la estructura esperada.
"""

from youtube_pipeline.generators.script_gen import VideoScript


SCRIPT = VideoScript(
    title="Las 7 IA MÁS PODEROSAS Ahora Mismo (2026)",
    description=(
        "Ranking de las 7 inteligencias artificiales más potentes de 2026: desde Fable 5 "
        "y su limitante de uso, hasta los modelos de video, voz e imagen que están cambiando "
        "todo. ¿Cuál deberías usar tú? #IA #InteligenciaArtificial #Fable5"
    ),
    tags=[
        "inteligencia artificial", "IA 2026", "fable 5", "claude", "gpt-5",
        "gemini", "mejores IA", "herramientas IA", "IA video", "elevenlabs",
        "higgsfield", "tecnologia", "ranking IA", "modelos de IA",
    ],
    hook=(
        "Hay una inteligencia artificial tan poderosa que tienen que limitar cuánto "
        "la puedes usar. Y no es la que estás pensando. Estas son las 7 IA más "
        "poderosas ahora mismo, y la número uno te va a sorprender."
    ),
    segments=[
        {
            "text": (
                "Hay una inteligencia artificial tan poderosa que tienen que limitar "
                "cuánto la puedes usar. Y no es la que estás pensando. Estas son las "
                "siete inteligencias artificiales más poderosas ahora mismo."
            ),
            "visual_cue": "abstract glowing AI neural network blue particles, futuristic",
            "label": "LAS 7 IA MÁS PODEROSAS",
            "duration_seconds": 12,
        },
        {
            "text": (
                "Número uno: Fable 5. Es el modelo más avanzado del momento, capaz de "
                "razonar, escribir y crear a un nivel que hace meses parecía ciencia "
                "ficción. Pero tiene un detalle importante: su limitante de uso. Al ser "
                "tan potente y costoso de ejecutar, el acceso viene con topes de uso. "
                "En los planes normales tienes un número limitado de mensajes por ventana "
                "de tiempo, y por API es de los modelos más caros. La buena noticia: para "
                "tareas críticas, no existe nada mejor."
            ),
            "visual_cue": "powerful supercomputer data center servers glowing, premium technology",
            "label": "1. FABLE 5",
            "duration_seconds": 26,
        },
        {
            "text": (
                "Número dos: Claude Opus 4.8. El hermano de Fable, especializado en "
                "programación y agentes autónomos. Es el favorito de los desarrolladores "
                "porque puede mantener tareas largas y complejas sin perderse. Si quieres "
                "que una IA escriba código de verdad o automatice procesos enteros, este "
                "es tu modelo."
            ),
            "visual_cue": "programmer coding on screen, lines of code, software development dark theme",
            "label": "2. CLAUDE OPUS 4.8",
            "duration_seconds": 20,
        },
        {
            "text": (
                "Número tres: GPT-5 de OpenAI. El todoterreno más conocido del planeta. "
                "Brilla en conversación, razonamiento general y creatividad, y está "
                "integrado en miles de aplicaciones. Es probablemente la IA con la que "
                "más gente interactúa cada día sin siquiera saberlo."
            ),
            "visual_cue": "person chatting with AI assistant on phone, friendly interface",
            "label": "3. GPT-5",
            "duration_seconds": 18,
        },
        {
            "text": (
                "Número cuatro: Gemini de Google. Su superpoder es el contexto gigante "
                "y lo multimodal: puede leer libros enteros, ver imágenes, escuchar audio "
                "y analizar video, todo a la vez. Conectado al ecosistema de Google, es "
                "una bestia para investigación y productividad."
            ),
            "visual_cue": "multiple data types images text video flowing together, multimodal abstract",
            "label": "4. GEMINI",
            "duration_seconds": 18,
        },
        {
            "text": (
                "Número cinco: los modelos de video como Veo y Sora. Escribes una frase "
                "y generan escenas de video realistas en segundos. Están transformando "
                "el cine, la publicidad y, por supuesto, YouTube. Lo que antes costaba "
                "miles de dólares, hoy lo creas desde tu casa."
            ),
            "visual_cue": "cinematic film production camera, movie scene being created, dramatic lighting",
            "label": "5. VIDEO IA: VEO & SORA",
            "duration_seconds": 18,
        },
        {
            "text": (
                "Número seis: Higgsfield. No solo genera video, sino que actúa como un "
                "director de cine con IA: eliges cámara, lente y movimiento para lograr "
                "tomas cinematográficas. Es la herramienta secreta de muchos creadores "
                "para que sus videos se vean profesionales."
            ),
            "visual_cue": "professional film director with camera equipment, cinematic shot setup",
            "label": "6. HIGGSFIELD",
            "duration_seconds": 18,
        },
        {
            "text": (
                "Y número siete: ElevenLabs. La IA de voz más realista que existe. "
                "Convierte texto en narración con emoción real, en decenas de idiomas. "
                "De hecho, canales enteros de YouTube funcionan con su voz. Quién sabe, "
                "quizás la voz que escuchas ahora mismo."
            ),
            "visual_cue": "sound waves audio waveform glowing, microphone studio recording",
            "label": "7. ELEVENLABS",
            "duration_seconds": 18,
        },
        {
            "text": (
                "Esas son las siete IA más poderosas del momento. La pregunta es: ¿cuál "
                "vas a empezar a usar tú? Si este video te sirvió, suscríbete al canal "
                "para no perderte el próximo, donde te muestro cómo combino varias de "
                "estas para crear contenido casi sin esfuerzo. Nos vemos en el próximo."
            ),
            "visual_cue": "subscribe button youtube, call to action, bright engaging",
            "label": "SUSCRÍBETE",
            "duration_seconds": 16,
        },
    ],
    call_to_action=(
        "Suscríbete para ver cómo combino estas IAs para crear contenido. "
        "Dale like y comenta cuál es tu favorita."
    ),
    thumbnail_text="LAS 7 IA MÁS PODEROSAS",
    total_estimated_seconds=164,
    is_shorts=False,
)

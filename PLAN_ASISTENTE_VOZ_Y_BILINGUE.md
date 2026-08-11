# 🎙️🌐 PLAN — Asistente de Voz (2 tiers) + App Bilingüe (ES/EN)

Documento de planificación. Se trabaja **de lo más sencillo a lo más complejo, por partes**.

## 🧭 Principios rectores (no negociables)
1. **Offline nativo en TODOS los planes.** La reproducción descargada y el asistente básico de voz funcionan **sin conexión**. No es un extra de pago.
2. **Free tier — Asistente por comandos on-device:** reconocimiento de voz del propio teléfono + gramática de comandos nuestra. **$0 de API, offline.**
3. **Plus tier — Lenguaje natural (BYOK):** el usuario usa **su propia API key de OpenRouter** (ya existe el campo en el chat). Paga/controla su propio uso; nosotros no ponemos costo de API. El Plus desbloquea entender frases libres y búsqueda de capítulos.
4. **Bilingüe ES/EN** en interfaz, comandos de voz y narración. Objetivo: buena aceptación en Norteamérica y países de habla inglesa.

---

## 🗣️ TAREA A — Asistente de voz

### Fase A0 — Control por sistema (Nivel 0) · **✅ HECHO (v1.0.8)**
- Incrementos de seek configurados en el `ExoPlayer` (retroceder 15s / adelantar 30s) para "retrocede/adelanta" por Assistant, notificación y botones Bluetooth.
- **Refactor a playlist completa**: `playBook`/`setVoice` cargan todas las partes en ExoPlayer y `nextPart`/`previousPart` usan navegación nativa (`seekToNext/PreviousMediaItem`). Así el control por sistema (Assistant "pausa/siguiente/anterior", Android Auto, Bluetooth del volante, botón manos-libres) avanza/retrocede de parte de forma nativa, y `onMediaItemTransition` sincroniza texto/karaoke/progreso en cualquier salto.
- Se preserva el fondo/offline (ExoPlayer prebufferiza la siguiente ventana) y queda listo `goToPart(n)` para "ir al capítulo N" de A1.
- **Pendiente de A1+:** que Assistant abra un libro por nombre ("reproduce X en Libris") requiere App Actions / media browse tree — se hará más adelante. A0 cubre el control de transporte de la sesión activa.

### Fase A1 — Comandos de voz on-device (Nivel 1, **Free**) · **✅ HECHO (v1.0.18)**
`VoiceCommandParser` (gramática bilingüe ES/EN) + `VoiceCommandManager` (SpeechRecognizer on-device, `EXTRA_PREFER_OFFLINE`) + `PlayerViewModel.handleVoiceCommand` + botón 🎤 en el reproductor con overlay de escucha y permiso `RECORD_AUDIO`. Comandos: pausa/reanuda, siguiente/anterior parte, retrocede/adelanta N seg, ir al capítulo N, más rápido/lento, marcapáginas, dónde estoy, detener. También **B11 ✅**: filtro Todos/Español/English en el selector de voces.

_Referencia de diseño original:_
- **A1.1** Permiso `RECORD_AUDIO` + botón de micrófono grande en **Modo Auto** (y opcional en el reproductor).
- **A1.2** `VoiceCommandManager`: wrapper de `SpeechRecognizer` on-device (`createOnDeviceSpeechRecognizer` en API 33+, fallback con `EXTRA_PREFER_OFFLINE`). Estados: escuchando / procesando / resultado.
- **A1.3** Motor de intención por **gramática bilingüe (ES/EN)**:
  - Intents: `PLAY`, `PAUSE`, `TOGGLE`, `NEXT_PART`, `PREV_PART`, `REWIND(seg)`, `FORWARD(seg)`, `GOTO_PART(n)`, `SPEED_UP/DOWN/SET`, `ADD_BOOKMARK`, `WHERE_AM_I`, `STOP`.
  - Parser: normaliza texto, mapea sinónimos y números ("capítulo cinco" / "chapter five"), extrae cantidades ("retrocede treinta segundos" / "rewind thirty seconds").
- **A1.4** Ejecuta la acción → `PlayerViewModel`. Confirmación corta (beep + háptico; opcional TTS "Listo/Done").
- **A1.5** UI de feedback: overlay de escucha + texto reconocido + toast de la acción.
- **Entregable:** parar/seguir/retroceder/adelantar/ir al capítulo N/velocidad/marcapáginas — **offline y gratis**.

### Fase A2 — Lenguaje natural (Nivel 4) · **✅ HECHO (v1.0.19)**
Backend `/api/voice-command` (cascada OpenRouter, misma que el chat, con la key del usuario o la compartida gratis) interpreta la frase → JSON de acción. En el app, `PlayerViewModel.onVoice()` hace la **cascada**: primero la gramática local A1 (gratis/offline); si no entiende, cae al LLM (overlay "Pensando…"). Requiere **redeploy del backend**. Búsqueda semántica de capítulos por texto = refinamiento futuro.

_Referencia de diseño original:_
- **A2.1** Gate: Plus activo **+** API key de OpenRouter del usuario (reusar el almacén de key del chat).
- **A2.2** Cascada inteligente: primero intenta la **gramática local** (gratis/offline); si no hay match **y** hay conexión **y** es Plus → manda el transcript al **LLM**.
- **A2.3** Esquema de intención (function-calling / JSON): mismo set de acciones **+** `SEARCH_CHAPTER(query)` con búsqueda sobre el texto de las partes ("llévame a donde empieza la batalla").
- **A2.4** Confirmación por voz + manejo de latencia ("buscando…").
- **Entregable:** frases naturales + búsqueda semántica de capítulos; el costo lo pone el usuario con su key.

### Fase A3 — Manos libres / wake-word (Nivel 2) · **FUTURO / premium**
- "Hey Libris" siempre-activo con Porcupine/Vosk (offline). Documentado, **no se construye ahora**. Notas: batería, privacidad del micro, política de Play Store para micro en segundo plano.

---

## 🌐 TAREA B — App bilingüe (ES/EN)

### Fase B0 — Infraestructura i18n · **✅ HECHO (v1.0.9)**
- `res/values/strings.xml` (ES) + `res/values-en/strings.xml` (EN) con la semilla de claves.
- `LocaleHelper` + `attachBaseContext` en MainActivity → cambio de idioma por-app en TODAS las versiones (minSdk 24), sin AppCompatActivity ni GMS.
- Selector **Automático / Español / English** en Ajustes (persistido, `recreate()` al cambiar).
- Ajustes migrado como demostración (título, subtítulo y títulos de sección usan `stringResource`).
- **Pendiente B1:** migrar el resto de pantallas (Login, Biblioteca, Reproductor, diálogos…) a `strings`.

### Fase A0.1 — Botones de retroceder/adelantar 30s en la notificación · **✅ HECHO (v1.0.9)**
- `CommandButton` (⏪30s / ⏩30s) en el custom layout del `MediaSession` → resuelve "no escuché bien" con un toque en la notificación/pantalla de bloqueo, sin voz. Incrementos de seek a 30s.

### Fase B1 — Migración de UI por pantallas · **EN PROGRESO** (por tandas)
- **✅ Tanda 1 (v1.0.11):** barra de navegación inferior, **Biblioteca** (tabs, búsqueda, continuar escuchando, categorías Todas/Favoritos, estados vacíos), **Historial** (título, vacío, progreso, reanudar) y subtítulo de Ajustes. Las claves de filtro internas se conservan; solo se traduce la etiqueta visible.
- **✅ Tanda 2 (v1.0.12):** **Reproductor** (barra superior, modos Clásico/Libro/Leer, fila de acciones, "Parte X de Y", controles play/pausa/anterior/siguiente, modo inmersivo) y **Modo Auto** (título, parte, siguiente parte).
- **✅ Tanda 3a (v1.0.13):** diálogos de **Voz**, **Temporizador de sueño** (incluye opciones del enum), **Estadísticas** y **Marcapáginas**.
- **✅ Tanda 3b (v1.0.14):** diálogos de **Chat IA** (saludo, preguntas rápidas, panel de API key, escudo, tip de cuota, errores), **Música de fondo**, **Perfil** y **Logros** (9 insignias con nombre+descripción vía `ctx.getString`).
- **✅ Tanda 4 (v1.0.15):** **Login** (tabs, campos, botones, Google, privacidad), **Subir PDF** (selector, campos, estados, validaciones, errores, éxito) e **InfoCard de Ajustes**.
- **✅ B1 COMPLETO.** Toda la UI de la app cambia entre Español e Inglés. (~169 claves ES / 167 EN; las 2 de diferencia son técnicas no visibles.)

### Fase B2 — Contenido dinámico bilingüe · esfuerzo **medio**
- Comandos de voz bilingües (se conecta con la Tarea A1.3).
- **Voces de narración EN**: añadir voces `en-US` de Edge TTS al catálogo; elegir voz según el **idioma del libro** (requiere metadato de idioma en el catálogo).
- Nombres de géneros/categorías localizados; respuestas del asistente/chat en el idioma de la app.

### Fase B3 — Landing + tienda bilingüe · esfuerzo **medio**
- Landing i18n ES/EN (ya hay expectativa en `DIRECTIVA_LANDINGS_PREMIUM`: políticas bilingües). Ficha de Play Store en inglés.

### Fase B4 — QA bilingüe · esfuerzo **bajo**
- Revisar textos cortados, formato de números/tiempo, cambio de idioma en caliente, ambos idiomas completos.

---

## 🪜 Orden de ejecución sugerido (simple → complejo)
1. **A0** — control por sistema (rápido, gran valor al volante).
2. **B0** — infra i18n (desbloquea comandos EN y todo lo bilingüe).
3. **A1** — comandos de voz on-device (Free, $0) — el asistente estrella.
4. **B1** — migración de UI por pantallas (en tandas).
5. **A2** — Plus, lenguaje natural (BYOK).
6. **B2 / B3** — voces EN, géneros, landing (apertura al mercado inglés).
7. **A3** — wake-word (futuro).

---

## ⚠️ Dependencias y decisiones abiertas
- **Entitlement Plus:** hoy no hay sistema formal de suscripción. Proxy temporal para A2: "tiene API key de OpenRouter" o un flag. A futuro, entitlement real.
- **Idioma de la narración por libro:** hace falta un metadato de idioma en el catálogo (Appwrite `global_books`).
- **Directiva global:** formalizar `DIRECTIVA_APP_BILINGUE.md` en la base de contextos (hoy solo se menciona bilingüe en la de Landings). Recomendado para que aplique a todos los proyectos.
- **Seguridad al volante:** mantener confirmaciones cortas; el asistente debe ser "glanceable" y no exigir mirar la pantalla.

# Plan Futuro — Versión Windows (Compose Multiplatform)

> **ESTADO: FUTURO / BLOQUEADO.** No se inicia hasta que la versión **Android esté 100% terminada, probada y funcional.** Una vez cumplido eso, se dedica todo el esfuerzo a llevarla a Windows sobre base firme.

**Decisión tomada (agosto 2026):** un solo código Kotlin/Compose para Android + Windows usando **Compose Multiplatform**. Se descarta app nativa de Windows (C#/.NET) por duplicar esfuerzo sin beneficio, y se descarta depender de la PWA para escritorio para no mantener dos frontends divergentes a largo plazo.

---

## 0. Precondición: Android 100% listo antes de empezar

No se toca este plan hasta cerrar y **probar en dispositivo real**:

- [ ] Karaoke sincronizado funcionando (tras redeploy del backend).
- [ ] Descarga offline + inventario (gancho premium #1).
- [ ] Música por género / por escena (detección local sin tokens).
- [ ] Marcapáginas persistentes (hoy son solo en memoria).
- [ ] Chat IA con historial (memoria entre preguntas).
- [ ] Limpieza legal del catálogo (ver nota de copyright abajo).
- [ ] Perfil, temas animados, marcos, modo inmersivo verificados.

Migrar sobre algo sin verificar es la receta para romper lo que funciona. Primero base firme.

---

## 1. Qué NO cambia (ya es multiplataforma)

El 80% del trabajo pesado es compartido y no se toca:

- **Backend** — FastAPI en Cloud Run.
- **Autenticación** — Appwrite.
- **Almacenamiento** — Cloudflare R2 (MP3, texto, portadas, tiempos de karaoke).
- **Voz** — Edge TTS.

Solo cambia **la capa de interfaz (UI) y las APIs propias del sistema operativo**.

---

## 2. Arquitectura objetivo (módulos Kotlin Multiplatform)

- **`commonMain`** — casi toda la UI Compose reutilizable tal cual: temas, marcos por género, diálogos, pantallas, karaoke, perfil, lógica de ViewModels.
- **`androidMain`** — específico de Android: Media3/ExoPlayer, Foreground Service, notificaciones de reproducción.
- **`desktopMain`** — específico de Windows: reproductor de audio de escritorio, ventana, empaquetado.

Meta: que el grueso de las pantallas viva en `commonMain` y solo lo dependiente del SO se implemente por plataforma.

---

## 3. Las 4 piezas a desacoplar (patrón `expect`/`actual`)

1. **Reproductor de audio** *(el más delicado)* — Media3 es solo Android. En Windows se usa **VLCJ** o **JavaFX Media**. Se crea una interfaz común `AudioEngine` con dos implementaciones (Android = ExoPlayer, Desktop = VLCJ/JavaFX).
2. **Almacenamiento de preferencias** — `SharedPreferences` (Android) → librería **`multiplatform-settings`** (misma idea, ambas plataformas). Afecta: progreso, posición, tema, voz, perfil, marcapáginas.
3. **Red** — Retrofit funciona en JVM de escritorio; a futuro lo más limpio es **Ktor** (multiplataforma). Se puede empezar manteniendo Retrofit y migrar después.
4. **Carga de imágenes** — Coil tiene versión multiplataforma (portadas); cambio menor.

---

## 4. Empaquetado de Windows

Compose Desktop genera instaladores nativos **`.exe` / `.msi`** vía jpackage (`packageReleaseDistributionForCurrentOS`). También se puede publicar en la **Microsoft Store**. No requiere reescritura: es una tarea de configuración de Gradle.

---

## 5. Plan por fases (seguro, en rama aparte)

Trabajar en una rama **`multiplatform`**, nunca en `main`, para que la app Android de producción quede intacta durante la migración.

- **Fase 1 — Reestructurar a KMP sin romper Android.** Crear módulos `commonMain`/`androidMain`, mover UI compartida a `commonMain`, verificar que Android sigue compilando y funcionando idéntico.
- **Fase 2 — Desacoplar plataformas.** Interfaces `expect`/`actual` para audio, storage, (opcional) red e imágenes.
- **Fase 3 — Target de escritorio.** Añadir `desktopMain`, implementar el reproductor de audio de Windows y el `main()` con ventana Compose Desktop.
- **Fase 4 — Empaquetado.** Generar `.exe`/`.msi`, probar en Windows, pulir integración (ventana, atajos, tamaño).

---

## 6. Riesgos y consideraciones

- **Validación por compilación:** la migración se valida compilando y probando iterativamente. Conviene tener un flujo donde se pueda construir localmente o CI rápido; hacerla "a ciegas" de un solo golpe es arriesgado.
- **Reproductor de audio de escritorio:** es el punto de mayor incertidumbre (elegir y afinar VLCJ vs JavaFX Media, gapless, velocidad de reproducción, posición).
- **Paridad de funciones:** el objetivo es que Windows quede **igual** que Android; se migra sobre la versión Android ya terminada, no sobre una en construcción.
- **CI:** hoy el CI solo construye el APK. Habrá que añadir un job para el build de escritorio.

---

## 7. Recordatorio legal (aplica a ambas plataformas)

Antes de comercializar en cualquier plataforma, **limpiar el catálogo de obras con copyright vigente** (autores contemporáneos, autores fallecidos hace menos de 70–80 años, y **traducciones modernas** de clásicos). Usar textos verificados de **Project Gutenberg** para garantizar dominio público (texto y traducción). Ver `INVESTIGACION_MERCADO_MONETIZACION.md`.

---

*Este documento queda como referencia. Se retoma únicamente cuando la casilla de "Android 100% listo" esté completa.*

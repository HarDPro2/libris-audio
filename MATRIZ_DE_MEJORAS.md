# MATRIZ DE MEJORAS — LIBRIS AUDIO
**Última actualización:** 2026-08-05 | Commit: `pendiente push`

---

## SESIONES PRE-AGOSTO 2026

| # | Fecha | Mejora | Archivos clave | Estado |
|:--|:------|:-------|:---------------|:-------|
| 1 | Abr'26 | PWA inicial: React + Supabase + audio JIT | `main.py`, `PlayerContext.tsx`, `LibraryPage.tsx` | ✅ |
| 2 | Jun'26 | Permisos de dueño: DELETE/PATCH por JWT Supabase | `main.py`, `BookCard.tsx`, `EditBookModal.tsx` | ✅ |
| 3 | Jun'26 | Fix: saltos de reproducción (isTransitioningRef numérico React 18) | `PlayerContext.tsx` | ✅ |
| 4 | Jun'26 | Fix: libro fantasma tras borrar (callback onDeleted) | `BookCard.tsx`, `LibraryPage.tsx` | ✅ |
| 5 | Jun'26 | Fix: sync cross-device (visibilitychange listener) | `LibraryPage.tsx` | ✅ |
| 6 | Jul'26 | Fix: audio cortado (edge-tts segmentado por frases ≤1200 chars) | `main.py` | ✅ |
| 7 | Jul'26 | Fix: audio con pantalla apagada (AudioContext + fetch Blob prefetch) | `PlayerContext.tsx` | ✅ |
| 8 | Jul'26 | Migración a Capacitor → App Android (WebView) | `capacitor.config.ts`, `android/` | ✅ |
| 9 | Jul'26 | CI/CD GitHub Actions → APK automático en Releases | `.github/workflows/build-android-apk.yml` | ✅ |
| 10 | Jul'26 | Landing Page con botón descarga Android | `LandingPage.tsx` | ✅ |
| 11 | Ago'26 | Migración backend Render → Google Cloud Run | `main.py`, Cloud Run config | ✅ |
| 12 | Ago'26 | Migración DB Supabase → Appwrite Cloud | `main.py`, Appwrite collections | ✅ |
| 13 | Ago'26 | App nativa Kotlin pura (sin Capacitor/WebView) | Todo `android/` | ✅ |
| 14 | Ago'26 | MediaSession API (controles pantalla de bloqueo) | `AudioService.kt` | ✅ |
| 15 | Ago'26 | Temas visuales dinámicos — 6+ temas (Cyberpunk, Ocean, Ember…) | `AppThemePreset.kt`, todas las pantallas | ✅ |
| 16 | Ago'26 | Modo Conducción (CarModeScreen) | `CarModeScreen.kt` | ✅ |
| 17 | Ago'26 | Música de fondo ambiental (BackgroundMusicCatalog) | `BackgroundMusicCatalog.kt`, `PlayerScreen.kt` | ✅ |
| 18 | Ago'26 | Control de velocidad de reproducción (0.5x → 2.0x) | `PlayerScreen.kt`, `PlayerViewModel.kt` | ✅ |
| 19 | Ago'26 | Navegación entre partes del libro (nextPart/previousPart) | `PlayerViewModel.kt` | ✅ |
| 20 | Ago'26 | BottomPlayerBar persistente en Scaffold | `MainActivity.kt`, `BottomPlayerBar.kt` | ✅ |

---

## SESIÓN 2026-08-05 — PARIDAD COMPLETA CON LA PWA

| # | Mejora | Descripción detallada | Archivos afectados | Estado |
|:--|:-------|:----------------------|:-------------------|:-------|
| 21 | **Auth Appwrite completa** | AuthViewModel con StateFlow, AppwriteAuthClient Retrofit, session persistence en SharedPreferences | `AuthViewModel.kt`, `AppwriteAuthClient.kt`, `AuthModels.kt` | ✅ |
| 22 | **LoginScreen** | UI glassmorphism, toggle login↔registro, validación en tiempo real, mensajes error reales | `LoginScreen.kt` | ✅ |
| 23 | **Google OAuth2** | Chrome Custom Tab → Appwrite OAuth → deep link `librisaudio://oauth/*` → session | `MainActivity.kt`, `LoginScreen.kt` | ✅ |
| 24 | **Fix pantalla blanca** | `buildUi()` no se llamaba en `onCreate()` — bug crítico | `MainActivity.kt` | ✅ |
| 25 | **Fix "correo incorrecto"** | UUID aleatorio como userId; parsing correcto de HttpException de Appwrite | `AuthViewModel.kt` | ✅ |
| 26 | **LibraryScreen reescrita** | Tabs Explorar/Mi Biblioteca, pills de categorías dinámicas, búsqueda en tiempo real, grid 2 col | `LibraryScreen.kt` | ✅ |
| 27 | **BookCard — nuevo componente** | Portada Coil (AsyncImage), badge categoría, barra progreso, menú ⋮ solo para propietario | `BookCard.kt` | ✅ |
| 28 | **HistoryScreen reescrita** | Solo libros con progress>0, miniatura portada, barra progreso, parte actual, botón Reanudar | `HistoryScreen.kt` | ✅ |
| 29 | **UploadScreen reescrita** | Título obligatorio, categoría obligatoria (16 cats PWA), validación visual roja, upload con addedBy | `UploadScreen.kt` | ✅ |
| 30 | **SettingsScreen completa** | Avatar inicial, nombre+email real, temas con círculos, "Cerrar Sesión" con confirmación | `SettingsScreen.kt` | ✅ |
| 31 | **Backend: audio sin Supabase** | `/api/audio` elimina guard de Supabase — solo necesita R2 | `backend/main.py` | ✅ |
| 32 | **Backend: upload con title/category/added_by** | `/api/upload-pdf` acepta campos de formulario explícitos; usa el título que manda la app | `backend/main.py` | ✅ |
| 33 | **Backend: DELETE Appwrite-aware** | Verifica propiedad en Appwrite `global_books.added_by` (sin Supabase), borra de R2 y Appwrite | `backend/main.py` | ✅ |
| 34 | **Backend: PATCH Appwrite-aware** | Edita título/categoría verificando propiedad en Appwrite (sin Supabase) | `backend/main.py` | ✅ |
| 35 | **PlayerViewModel: deleteBook** | Llama DELETE con token Bearer, quita libro del estado local inmediato | `PlayerViewModel.kt` | ✅ |
| 36 | **PlayerViewModel: editBook** | Llama PATCH con token Bearer, actualiza estado local con nuevos valores | `PlayerViewModel.kt` | ✅ |
| 37 | **BookCategories.kt** | 16 categorías (mismas que la PWA): Clásicos, Ficción, Ciencia… | `BookCategories.kt` | ✅ |
| 38 | **LibrisApi.kt actualizado** | Endpoints DELETE/PATCH/upload multipart con Retrofit; eliminado Supabase | `LibrisApi.kt` | ✅ |
| 39 | **Book.kt — addedBy** | Campo `addedBy: String` en modelo Book; nullable en GlobalBookDto para compatibilidad | `Book.kt` | ✅ |
| 40 | **APPWRITE_PROJECT_ID en backend** | Constante añadida al entorno del backend para autenticar cookies de sesión Appwrite | `backend/main.py` | ✅ |

---

## SESIÓN 2026-08-05 CONTINUACIÓN — FASES 0-4 (BUG FIXES + LOGIN FIX)

| # | Fase | Mejora | Descripción detallada | Archivos afectados | Estado |
|:--|:-----|:-------|:----------------------|:-------------------|:-------|
| 41 | 0 | **Eliminar Supabase del backend** | `supabase==2.4.1` removido de `requirements.txt`; todos los imports, cliente, helpers y handlers duplicados eliminados de `main.py` | `backend/requirements.txt`, `backend/main.py` | ✅ |
| 42 | 0 | **Eliminar Render del backend** | Todas las referencias a Render en comentarios y docstrings reemplazadas por Cloud Run | `backend/main.py` | ✅ |
| 43 | 1 | **Fix handlers duplicados DELETE/PATCH** | Los handlers de Supabase (registrados primero) bloqueaban los de Appwrite — FastAPI solo ejecuta el primero. Eliminados completamente | `backend/main.py` | ✅ |
| 44 | 1 | **Fix PATCH body FastAPI** | `body: dict = None` → `body: dict = Body(default={})` para que FastAPI deserialice JSON correctamente | `backend/main.py` | ✅ |
| 45 | 1 | **Fix session verify async** | `requests.get()` bloqueante dentro de `async def` reemplazado por `httpx.AsyncClient` en `_verify_appwrite_session()` | `backend/main.py` | ✅ |
| 46 | 1 | **Fix: upload_pdf no guardaba en Appwrite** | Endpoint procesaba PDF y subía a R2 pero nunca llamaba a `appwrite_db.create_document()` — libros subidos desde la app no aparecían en el catálogo | `backend/main.py` | ✅ |
| 47 | 1 | **APPWRITE_API_KEY sin hardcoding** | Removido el default hardcodeado del `os.environ.get()` (violaba DIRECTIVA_CERO_HARDCODING); añadido WARNING si no está configurado | `backend/main.py` | ✅ |
| 48 | 2 | **Fix: addedBy siempre vacío en loadBooks()** | `addedBy` no se mapeaba desde el DTO → `isOwner` siempre `false` → menú ⋮ nunca visible | `PlayerViewModel.kt` | ✅ |
| 49 | 3 | **network_security_config.xml** | Nuevo archivo: configura trust para Appwrite, Cloud Run, R2, Cloudflare, OpenRouter, Unsplash. Previene bloqueos de conexión en Android 9+ | `res/xml/network_security_config.xml`, `AndroidManifest.xml` | ✅ |
| 50 | 3 | **Logging detallado en AuthViewModel** | `Log.d/e` en cada paso de login/registro; mensajes de error distinguen SSL, DNS, timeout, HTTP codes | `AuthViewModel.kt` | ✅ |
| 51 | 3 | **OAuth deep link parser robusto** | Maneja múltiples variantes de nombre de parámetro Appwrite (`userId`/`$id`/`uid`, `secret`/`sessionId`/`token`); loguea todos los params recibidos si falta alguno | `MainActivity.kt` | ✅ |
| 52 | 3 | **Verificación URL Retrofit Appwrite** | Confirmado: base URL termina en `/`, paths de `@POST` no empiezan con `/` — Retrofit construye URLs correctas | `AppwriteAuthClient.kt` | ✅ |
| 53 | 4 | **Progreso persistido en SharedPreferences** | `PlayerViewModel` migrado a `AndroidViewModel`; `loadBooks()` restaura `currentPartIndex` y `progressPercent` desde `libris_progress` prefs; `playBook()` guarda en cada cambio de parte | `PlayerViewModel.kt` | ✅ |
| 54 | 4 | **HistoryScreen deja de estar vacía** | Al persistir progreso en SharedPreferences, `progressPercent > 0` funciona entre sesiones | `PlayerViewModel.kt` | ✅ |
| 55 | 4 | **Música de fondo conectada a AudioService** | `PlayerViewModel.setBackgroundTrack(MusicTrack?)` y `setBackgroundVolume(Float)` envían Media3 Custom Commands (`SET_BACKGROUND_TRACK`, `STOP_BACKGROUND_TRACK`, `SET_BACKGROUND_VOLUME`) al `AudioService` | `PlayerViewModel.kt`, `AudioService.kt` | ✅ |
| 56 | 4 | **AudioService: Custom Commands declarados** | `LibraryCallback.onConnect()` añade los 3 comandos personalizados al set permitido; `onCustomCommand()` los maneja llamando a `playBackgroundTrack()`, `stopBackgroundTrack()`, `setBackgroundVolume()` | `AudioService.kt` | ✅ |
| 57 | 4 | **MainActivity: callbacks de música → ViewModel** | `onSelectMusicTrack` y `onBackgroundVolumeChange` en `PlayerScreen` ahora llaman a `playerViewModel.setBackgroundTrack()` y `playerViewModel.setBackgroundVolume()` | `MainActivity.kt` | ✅ |

---

## SESIÓN 2026-08-05 CONTINUACIÓN — FASES A-F (POLISHING + UI FIXES)

| # | Fase | Mejora | Descripción detallada | Archivos afectados | Estado |
|:--|:-----|:-------|:----------------------|:-------------------|:-------|
| 58 | A | **Corregir mojibake en UI** | 9 archivos tenían caracteres corruptos (Latin-1 leído como UTF-8): á→?, é→?, ñ→?, ü→?, emojis→??. Re-guardados como UTF-8 correcto. | `BackgroundMusicCatalog.kt`, `BookmarkDialog.kt`, `MusicSelectorDialog.kt`, `SleepTimerDialog.kt`, `StatsDialog.kt`, `VirtualBookFrame.kt`, `PlayerScreen.kt`, `Theme.kt`, `ChatWithBookDialog.kt` | ✅ |
| 59 | B | **Eliminar URLs duplicadas de música ambiental** | Las 4 pistas "Ambiente" (n1-n4) apuntaban a URLs de Chopin/Satie. Catálogo reescrito con URLs de Cloudflare R2 propias: `music/piano/`, `music/cuerdas/`, `music/barroco/`, `music/orquesta/`, `music/ambiente/`. Fuente a usar: **Musopen.org** (dominio público). | `BackgroundMusicCatalog.kt` | ✅ |
| 60 | — | **Expandir temas visuales de 4 a 8** | CYBERPUNK, OCEAN (Océano Profundo), EMERALD, EMBER (Ember Otoñal), SUNSET, FOREST (Bosque Oscuro), COSMIC, MIDNIGHT. SettingsScreen ya los muestra dinámicamente via `AppThemePreset.values()`. | `Theme.kt` | ✅ |
| 61 | C | **Sleep Timer funcional** | `LaunchedEffect(sleepTimerSeconds, isPlaying)` hace countdown 1s/tick. Al llegar a 0 llama `onTogglePlay()` y resetea. Opción `END_OF_PART` marcada con `-1L` (sin countdown propio). | `PlayerScreen.kt` | ✅ |
| 62 | D | **Persistir tema seleccionado** | `currentTheme` migrado de `var local` en `MainActivity` a `PlayerViewModel.selectedTheme: StateFlow<AppThemePreset>` + `setTheme()`. Se guarda en SharedPreferences `libris_progress` con clave `"theme"`. | `PlayerViewModel.kt`, `MainActivity.kt` | ✅ |
| 63 | E | **Fix thread safety en ChatWithBookDialog** | `OkHttpClient().newCall(request).execute()` (blocking) movido dentro de `withContext(Dispatchers.IO)`. Previene bloqueo del hilo main. | `ChatWithBookDialog.kt` | ✅ |
| 64 | F | **StatsDialog con datos reales** | `PlayerViewModel` acumula minutos de escucha reales en SharedPreferences (1 min cada 60 ticks de 0.5s = 30s de reproducción). Racha diaria por fecha. `PlayerScreen` expone `isStatsVisible` + botón `QueryStats` en top bar. Tres parámetros: `todayMinutes`, `streakDays`, `totalHours`. | `PlayerViewModel.kt`, `PlayerScreen.kt`, `MainActivity.kt` | ✅ |

---

## SESIÓN 2026-08-07 — RECUPERACIÓN DE CATÁLOGO + OAuth + DISEÑO + VOZ

| # | Mejora | Descripción detallada | Archivos afectados | Estado |
|:--|:-------|:----------------------|:-------------------|:-------|
| 65 | **Fix OAuth Google (flujo token)** | El login usaba `sessions/oauth2` (cookie de navegador, no sirve en apps nativas). Cambiado a `tokens/oauth2` + intercambio `sessions/token`. Scheme correcto `appwrite-callback-{projectId}://`. CookieJar en OkHttp para persistir sesión. | `AppwriteAuthClient.kt`, `AuthViewModel.kt`, `MainActivity.kt`, `AndroidManifest.xml`, `build.gradle` | ✅ |
| 66 | **Fix registro email (Retrofit)** | Parámetros con default en interfaz Retrofit no funcionan → header `X-Appwrite-Project` movido a interceptor OkHttp. | `AppwriteAuthClient.kt`, `AuthViewModel.kt` | ✅ |
| 67 | **Recuperación de 97 libros huérfanos** | Los archivos (texto+portadas) migraron de Supabase a R2, pero el índice quedó en Supabase (pausado por egress). Catálogo re-importado a Appwrite `global_books` vía script REST. | `migrar_catalogo_appwrite.py`, `respaldo_libros_supabase.json` | ✅ |
| 68 | **Fix credenciales R2 en Cloud Run** | `SignatureDoesNotMatch` al subir/generar audio: variables R2 actualizadas en Cloud Run con las credenciales correctas. | Cloud Run env vars | ✅ |
| 69 | **Fix backend: leer Appwrite vía REST** | SDK nuevo devuelve objeto `DocumentList` (no dict) → `res.get()` fallaba → siempre fallback a 2 mocks. Reescrito con helper `_appwrite_list_documents()` (httpx REST, queries en JSON). | `backend/main.py` | ✅ |
| 70 | **Categorías dinámicas + sin mocks** | `LibraryScreen` genera pills desde las categorías reales de los libros. Eliminado `getDefaultCatalog()` (2 mocks). `BookCategories` ampliado a las categorías reales. | `LibraryScreen.kt`, `PlayerViewModel.kt`, `BookCategories.kt` | ✅ |
| 71 | **Música de fondo: solo pistas reales** | Catálogo recortado de 24 (19 rotas) a las 5 pistas que existen en R2. | `BackgroundMusicCatalog.kt` | ✅ |
| 72 | **Chat IA: timeout 10s→60s** | Modelos gratuitos de OpenRouter tardan; OkHttp default cortaba a 10s. | `ChatWithBookDialog.kt` | ✅ |
| 73 | **12 temas animados** | Cada tema con su animación Canvas: Red Neuronal, Campo Cuántico, Matrix, Retro Wave, Aurora, Biblioteca Cósmica, Tinta y Pergamino, Brasa + mesh. Selector con tarjetas de degradado. | `Theme.kt`, `AnimatedBackground.kt`, `SettingsScreen.kt` | ✅ |
| 74 | **12 marcos por género** | Modo Libro 3D: Clásico, Medieval, Espiritual, Guerra, Romance, Paranormal, Científico, Comedia, Fantasía, Poesía, Noir, Cósmico — degradados, emblemas, ornamentos, borde con brillo. | `VirtualBookFrame.kt` | ✅ |
| 75 | **Selección de voz del narrador** | 12 voces neurales (Elvira, Álvaro, Dalia, Jorge, Elena, Tomás, Salomé, Paola, Aria, Guy, Francisca, Denise). Persistida; se aplica al instante recargando la parte con la posición conservada. | `VoiceCatalog.kt`, `VoiceSelectorDialog.kt`, `PlayerViewModel.kt`, `PlayerScreen.kt`, `MainActivity.kt` | ✅ |

---

## BACKLOG — PRÓXIMAS MEJORAS (planeadas)

| # | Mejora | Descripción | Prioridad |
|:--|:-------|:------------|:----------|
| B1 | **Descarga offline + inventario** | Descargar partes de un libro a almacenamiento local para escuchar sin conexión. Registro de lo descargado (libro + nº de partes). Sección de gestión donde el usuario ve qué está descargado, elige qué conservar y puede borrar todo para liberar espacio. Reproducción con fallback a archivo local. **Su propio push dedicado** (feature grande). | Alta |
| B2 | **Música por género tipo emisoras** | Carpetas de música en R2 por ambiente: relajante, guerra, romance, misterio, etc. El usuario (o el sistema) ajusta la emisora al género del libro que escucha/lee. Programable como estaciones. | Media |
| B3 | **Animación de fondo en el reproductor** | Extender `AnimatedBackground` al PlayerScreen (hoy solo Biblioteca y Ajustes). | Baja |
| B4 | **Versionado + auto-actualizador** | Hoy cada build es "1.0.0" (sin versión real). Introducir versionado incremental (desde `package.json` o build number), renombrar el APK a nombre **sin versión** (`libris-audio.apk`) en el CI y la landing para que el enlace nunca se rompa, y luego el auto-actualizador in-app (chequea GitHub Releases, descarga e instala vía FileProvider). Los tres dependen de tener versionado decente. | Media |
| B5 | **Sincronización en la nube (progreso + preferencias)** | Colección `user_state` en Appwrite (un doc por usuario con JSON), endpoints backend GET/PUT, y en la app restaurar al login + guardar al cambiar. Para continuar donde quedó en cualquier dispositivo/reinstalación. **← EN CONSTRUCCIÓN** | Alta |

---

## BACKLOG — PENDIENTE

| # | Mejora | Prioridad | Notas |
|:--|:-------|:----------|:------|
| B1 | **Progreso sincronizado en Appwrite** | Media | Actualmente persiste localmente en SharedPreferences. Para sync cross-device crear colección `user_books` en Appwrite y guardar allí |
| B2 | **Mi Biblioteca desde Appwrite** | Media | Actualmente filtra local por `progressPercent>0`. Con `user_books` en Appwrite, sincronizar con la nube |
| B3 | **Subir música a R2 desde Musopen** | Alta | `BackgroundMusicCatalog.kt` tiene URLs placeholder. Descargar de Musopen.org y subir a `r2.dev/music/{categoria}/{archivo}.mp3`. Actualizar `R2` const con URL pública real del bucket. |
| B4 | **Racha diaria robusta (stats)** | Baja | La racha actual suma +1 por día que se reproduce sin verificar días consecutivos. Mejorar comparando fecha de `stats_last_day` con el día anterior. |
| B5 | **Modo END_OF_PART del sleep timer** | Baja | Actualmente marcado con `-1L` pero no hay lógica real. Escuchar `Player.STATE_ENDED` en `PlayerViewModel` y pausar si está activo este modo. |
| B3 | **Prefetch de siguiente parte** | Media | Descargar la siguiente parte en background antes de que termine la actual (como la PWA) |
| B4 | **Firma de release APK** | Media | Keystore → `ANDROID_KEYSTORE_BASE64` en GitHub Secrets → APK firmado para Play Store |
| B5 | **Modo offline** | Media | Caché local de partes ya escuchadas |
| B6 | **Chat IA sobre libro** | Baja | Integrar `/api/chat-book` en PlayerScreen |
| B7 | **Notificaciones push** | Baja | Notificar cuando un libro nuevo está disponible |

---

## RESTRICCIONES ACTIVAS

| Restricción | Hasta | Descripción |
|:------------|:------|:------------|
| 🗑️ Supabase eliminado | permanente | Completamente removido del código. No restaurar. |
| 🗑️ Render eliminado | permanente | Backend 100% en Google Cloud Run. No restaurar. |
| ⚠️ AutoMirrored icons | indefinido | El runner de GitHub Actions no compila con `Icons.AutoMirrored.*` — usar `Icons.Default.*` |
| ⚠️ Appwrite `user_books` | indefinido | Colección no creada aún — progreso persiste en SharedPreferences (local) |
| ⚠️ DIRECTIVA_CERO_HARDCODING | permanente | Todas las credenciales SOLO desde variables de entorno, sin defaults hardcodeados |

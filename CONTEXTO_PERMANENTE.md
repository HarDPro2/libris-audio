# CONTEXTO PERMANENTE — LIBRIS AUDIO
**Última actualización:** 2026-08-05 | **Versión:** 5.0**  
**Commit actual:** `pendiente push` | **Rama:** `main`

---

## 🏗️ ARQUITECTURA GENERAL

### Stack Completo
| Capa | Tecnología | Estado |
|:---|:---|:---|
| **App Android nativa** | Kotlin + Jetpack Compose + Media3 | ✅ Producción |
| **PWA Web** | React + TypeScript + Vite | ✅ Producción (Vercel) |
| **Backend API** | FastAPI (Python) en Google Cloud Run | ✅ Producción |
| **Autenticación** | Appwrite Cloud (`nyc.cloud.appwrite.io`) | ✅ Activo |
| **Base de datos** | Appwrite DB (`global_books` collection) | ✅ Activo |
| **Almacenamiento audio/texto** | Cloudflare R2 | ✅ Activo |
| **TTS (Text-to-Speech)** | Edge TTS — voz `es-MX-JorgeNeural` | ✅ Activo |
| **CI/CD** | GitHub Actions → APK → GitHub Releases | ✅ Activo |
| **IA / Chat** | OpenRouter (cascada multi-modelo gratuita) | ✅ Activo |
| **Supabase** | ❌ ELIMINADO del código | 🗑️ Removido |
| **Render** | ❌ ELIMINADO del código | 🗑️ Removido |

---

## 📱 APP ANDROID NATIVA (Kotlin/Compose)

### Autenticación — Appwrite REST API
- **Email/Contraseña:** registro y login vía `AppwriteAuthClient` (Retrofit)
- **Google OAuth2:** Chrome Custom Tab → Appwrite OAuth → deep link `librisaudio://oauth/success`
- **Session persistence:** `SharedPreferences` guarda `sessionId` y `userId`
- **Cookie auth:** `a_session_<projectId>=<token>` para llamadas autenticadas
- **AuthViewModel:** `StateFlow<AuthState>` — `Idle` → `Unauthenticated` → `Authenticated` | `Error`
- **Project ID Appwrite:** `6a72f5d6002eeff78bc2`
- **Appwrite Region:** `nyc.cloud.appwrite.io`

### Pantallas implementadas

#### 🔐 LoginScreen
- UI glassmorphism con tema dinámico
- Toggle Login ↔ Registro
- Validación de email y contraseña en tiempo real
- Botón **"Continuar con Google"** (Chrome Custom Tab)
- Mensajes de error de Appwrite (HttpException parsing)
- UUID aleatorio como `userId` en registro

#### 📚 LibraryScreen ✅ NUEVA (v4.0)
- **Tab "Explorar"** → catálogo global desde `GET /api/books` (backend)
- **Tab "Mi Biblioteca"** → libros con `progressPercent > 0`
- **Filtro por categorías** → pills horizontales scrolleables, dinámicas desde los libros disponibles
- **Búsqueda en tiempo real** por título, autor y categoría
- **Grid 2 columnas** de `BookCard`
- **Estado vacío** con mensaje según contexto (sin libros / sin resultados / cargando)

#### 🃏 BookCard ✅ NUEVO (v4.0)
- Portada real desde URL con **Coil** (AsyncImage)
- Badge de **categoría** superpuesto en esquina superior izquierda
- **Barra de progreso** en la base de la imagen (si `progressPercent > 0`)
- Menú ⋮ **solo visible para el propietario** (`addedBy == currentUserId`):
  - **Editar nombre y categoría** → diálogo con campo de texto + dropdown de categorías
  - **Eliminar libro** → confirmación antes de borrar
- Conteo de partes en texto

#### 🕐 HistoryScreen ✅ REESCRITA (v4.0)
- Solo muestra libros con `progressPercent > 0`
- Miniatura de portada (52×68dp) con Coil
- Barra de progreso visual + porcentaje
- Texto: `X% completado • Parte Y/Z`
- Botón **"▶ Reanudar"** que redirige a la biblioteca
- Estado vacío con instrucción

#### ⬆️ UploadScreen ✅ REESCRITA (v4.0)
- Selector de PDF con auto-fill del nombre desde el archivo
- **Título del libro** — campo obligatorio (borde rojo si vacío)
- **Categoría** — selector obligatorio (dropdown con 16 categorías)
- Validación visual: el botón queda deshabilitado si faltan campos
- Upload multipart a `POST /api/upload-pdf` con: `file`, `title`, `category`, `added_by`
- Feedback de éxito / error inline
- Al subir: recarga catálogo y va a LibraryScreen

#### ⚙️ SettingsScreen ✅ REESCRITA (v4.0)
- **Avatar** con inicial del nombre/email
- Nombre de usuario y email del usuario logueado
- Selector de **tema visual** con círculos de color
- Tarjeta de info del sistema (TTS, storage, DB, backend, auth)
- Botón **"Cerrar Sesión"** con diálogo de confirmación

#### 🎵 PlayerScreen (existente)
- Reproductor de audio completo
- Control de velocidad (0.5x → 2.0x)
- Navegación entre partes
- Seek con slider de tiempo
- Fondo de música ambiental (24 pistas: Piano, Cuerdas, Barroco, Orquesta, Ambiente)
- `BackgroundMusicCatalog.kt` — URLs apuntan a Cloudflare R2 (`music/piano/`, `music/ambiente/`, etc.)
- Música a obtener de **Musopen.org** (dominio público, 0 restricciones comerciales) y subir a R2
- URLs placeholder: `https://pub-XXXXXXXX.r2.dev/music/{categoria}/{archivo}.mp3`
- Modo conducción (CarModeScreen)

#### 🚗 CarModeScreen (existente)
- UI minimalista para conducción
- Botones grandes: play/pause, +15s/-15s, siguiente parte
- Botón cerrar modo conducción

### Componentes
- `AnimatedBackground` — mesh gradient animado según tema
- `BottomPlayerBar` — mini reproductor en barra inferior
- `BookCard` — tarjeta de libro con acciones de propietario (v4.0)
- `VirtualBookFrame` — frame decorativo de libro 3D
- `AppThemePreset` — **8 temas:** Cyberpunk, Océano Profundo, Esmeralda, Ember Otoñal, Sunset Aurora, Bosque Oscuro, Espacio Cósmico, Medianoche
- Tema seleccionado **persiste** entre sesiones via SharedPreferences (`prefs.putString("theme", ...)`)
- `PlayerViewModel.setTheme(preset)` y `PlayerViewModel.selectedTheme: StateFlow<AppThemePreset>`

### Arquitectura de navegación
```
MainActivity
├── LoginScreen (no auth)
└── Scaffold con NavigationBar (auth)
    ├── LibraryScreen (LIBRARY tab)
    ├── HistoryScreen (HISTORY tab)
    ├── UploadScreen (UPLOAD tab)
    ├── SettingsScreen (SETTINGS tab)
    ├── PlayerScreen (overlay full screen)
    └── CarModeScreen (overlay full screen)
```

### ViewModels
- **AuthViewModel:** estado de sesión, login, registro, logout, Google OAuth
- **PlayerViewModel (`AndroidViewModel`):** lista de libros, playback, seekTo, speed, deleteBook, editBook, persistencia de progreso en SharedPreferences (`libris_progress`), control de música de fondo via Media3 Custom Commands (`SET_BACKGROUND_TRACK`, `STOP_BACKGROUND_TRACK`, `SET_BACKGROUND_VOLUME`)

### Modelos de datos
```kotlin
data class Book(
    val id: String,
    val bookId: String,       // hex usado en R2 y backend
    val title: String,
    val author: String,
    val category: String,
    val coverUrl: String?,
    val partsCount: Int,
    val currentPartIndex: Int,
    val currentTimeSec: Double,
    val progressPercent: Int,
    val addedBy: String        // userId de Appwrite del que subió
)
```

### CI/CD — GitHub Actions
- **Trigger:** push a `main`
- **Build:** `./gradlew assembleDebug`
- **Release:** automático en GitHub Releases
- **URL permanente:** `https://github.com/HarDPro2/libris-audio/releases/latest/download/libris-audio-debug.apk`

---

## 🌐 BACKEND — FastAPI (Google Cloud Run)

**URL:** `https://libris-audio-backend-856706599879.us-west1.run.app`

### Endpoints activos

| Método | Ruta | Descripción | Auth |
|:---|:---|:---|:---|
| `GET` | `/api/health` | Keep-alive ping | No |
| `GET` | `/api/books` | Catálogo global desde Appwrite `global_books` | No |
| `POST` | `/api/upload-pdf` | Sube PDF, extrae texto, genera portada, guarda en R2 + Appwrite | No (addedBy en form) |
| `GET` | `/api/audio/{book_id}/{part_index}` | JIT: genera MP3 con edge-tts y lo sirve desde R2 | No |
| `DELETE` | `/api/books/{book_id}` | Elimina libro de R2 + Appwrite (solo propietario) | Bearer Appwrite session |
| `PATCH` | `/api/books/{book_id}` | Edita título/categoría (solo propietario) | Bearer Appwrite session |
| `GET` | `/api/tts-sample` | Sample de voz para preview | No |
| `POST` | `/api/chat-book` | Chat IA sobre el libro (OpenRouter) | No |

### Eliminación completa de Supabase y Render
- ✅ Supabase **completamente eliminado** del backend (`supabase==2.4.1` removido de `requirements.txt`, todos los imports y helpers removidos de `main.py`)
- ✅ Render **completamente eliminado** — toda referencia en comentarios/docstrings reemplazada por Cloud Run
- ✅ Solo quedan: Appwrite (auth + DB), R2 (storage), Cloud Run (backend)
- ✅ DELETE/PATCH verifican propiedad en Appwrite `global_books.added_by`
- ✅ `upload_pdf` registra el documento en Appwrite DB (antes faltaba esta llamada crítica)
- ✅ Session verification es **async** (usa `httpx.AsyncClient`, no `requests` bloqueante)

### Flujo JIT de audio
```
App solicita → /api/audio/{book_id}/{part_index}
  ↓
¿Existe MP3 en R2? → SÍ → Streamea desde R2
  ↓ NO
Descarga text/part_N.txt de R2
  ↓
edge-tts genera MP3 (segmentado por frases ≤1200 chars)
  ↓
Sube MP3 a R2 para cache permanente
  ↓
Streamea al cliente
```

### Flujo de upload de libro
```
App → POST /api/upload-pdf (file, title, category, added_by)
  ↓
Extrae texto del PDF (PyMuPDF / pdfplumber)
  ↓
Divide en chunks ≤3800 chars → sube como text/part_N.txt a R2
  ↓
Extrae primera página como portada → sube como cover.png a R2
  ↓
Registra en Appwrite global_books {book_id, title, category, added_by, ...}
  ↓
Retorna {title, bookId, partsCount, coverUrl}
```

---

## 🗄️ APPWRITE — Base de Datos

**Proyecto:** `6a72f5d6002eeff78bc2`  
**Región:** `nyc.cloud.appwrite.io`

### Colección `global_books`
| Campo | Tipo | Descripción |
|:---|:---|:---|
| `book_id` | String | ID hex del libro (usado en R2) |
| `title` | String | Título del libro |
| `author` | String | Autor (opcional) |
| `category` | String | Categoría seleccionada al subir |
| `cover_url` | String | URL pública de la portada en R2 |
| `parts_count` | Int | Número de partes de texto |
| `file_hash` | String | Hash del archivo (anti-duplicado) |
| `added_by` | String | `userId` Appwrite del uploader |

---

## ☁️ CLOUDFLARE R2 — Estructura de archivos

```
libris-audio-bucket/
├── {book_id}/
│   ├── cover.png              ← portada extraída del PDF
│   ├── text/
│   │   ├── part_0.txt
│   │   ├── part_1.txt
│   │   └── ...
│   └── audio/
│       ├── part_0_es-MX-JorgeNeural.mp3   ← generado JIT, cacheado
│       ├── part_1_es-MX-JorgeNeural.mp3
│       └── ...
```

---

## 🎨 CATEGORÍAS DE LIBROS (16 categorías)
Clásicos · Ficción · Ciencia · Historia · Filosofía · Aventura · Romance · Misterio · Biografía · Autoayuda · Infantil · Terror · Política · Economía · Arte · General

---

## 🤖 IA — OpenRouter Cascada Gratuita

### Estrategia MONO-API SINGLE-KEY CASCADE
- Una sola API Key de OpenRouter para todos los modelos
- Usuarios pueden traer su propia key (BYOK)
- Escudo `:free` — solo modelos 100% gratuitos

### Cascada de modelos (orden de fallback)
1. `openrouter/auto` (enrutador dinámico)
2. `deepseek/deepseek-r1:free`
3. `meta-llama/llama-3.3-70b-instruct:free`
4. `qwen/qwen-2.5-coder-32b-instruct:free`
5. `google/gemma-2-9b-it:free`

### Tratamiento de 429
Si un modelo supera 20 RPM → salto instantáneo al siguiente en la cascada.

---

## 📊 MATRIZ DE MEJORAS IMPLEMENTADAS

Ver `MATRIZ_DE_MEJORAS.md` para el historial completo. Resumen de la sesión 2026-08-05:

**FASE 0** — Supabase y Render eliminados completamente del backend y del código Android  
**FASE 1** — Cirugía backend: handlers duplicados eliminados, PATCH body corregido, session verify async  
**FASE 2** — `addedBy` mapeado en `loadBooks()` (el menú propietario nunca aparecía)  
**FASE 3** — Login Android: `network_security_config.xml`, logging mejorado en Auth, OAuth deep link robusto  
**FASE 4** — Progreso persistido en SharedPreferences; música de fondo conectada a AudioService via Custom Commands

---

## 🗂️ ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
libris-audio-main/
├── android/                              ← App Android nativa (Kotlin/Compose)
│   └── app/src/main/java/com/librisaudio/app/
│       ├── MainActivity.kt               ← Routing principal, auth state, deep links
│       ├── data/
│       │   ├── api/
│       │   │   ├── AppwriteAuthClient.kt ← Retrofit Appwrite REST
│       │   │   └── LibrisApi.kt          ← Backend API (books, upload, delete, patch)
│       │   └── model/
│       │       ├── AuthModels.kt         ← Session, AuthState
│       │       ├── Book.kt               ← GlobalBookDto, Book domain model
│       │       ├── BookCategories.kt     ← 16 categorías estándar
│       │       └── BackgroundMusicCatalog.kt
│       ├── ui/
│       │   ├── components/
│       │   │   ├── AnimatedBackground.kt
│       │   │   ├── BookCard.kt           ← Tarjeta con acciones de propietario
│       │   │   ├── BottomPlayerBar.kt
│       │   │   └── VirtualBookFrame.kt
│       │   ├── screens/
│       │   │   ├── LoginScreen.kt        ← Login + Registro + Google OAuth
│       │   │   ├── LibraryScreen.kt      ← Explorar/Mi Biblioteca + categorías + búsqueda
│       │   │   ├── HistoryScreen.kt      ← Historial con progreso
│       │   │   ├── UploadScreen.kt       ← PDF + título + categoría obligatorios
│       │   │   ├── SettingsScreen.kt     ← Perfil + temas + logout
│       │   │   ├── PlayerScreen.kt       ← Reproductor completo
│       │   │   └── CarModeScreen.kt      ← Modo conducción
│       │   └── theme/
│       │       ├── AppTheme.kt
│       │       └── AppThemePreset.kt
│       ├── viewmodel/
│       │   ├── AuthViewModel.kt          ← Session, login, registro, logout
│       │   └── PlayerViewModel.kt        ← Books, playback, deleteBook, editBook
│       └── service/
│           └── AudioService.kt           ← Media3 background service
├── backend/
│   └── main.py                           ← FastAPI: books, audio JIT, upload, delete, patch
├── src/                                  ← PWA React (activa en Vercel)
│   ├── pages/
│   │   ├── LibraryPage.tsx
│   │   ├── HistoryPage.tsx
│   │   ├── UploadPage.tsx
│   │   └── SettingsPage.tsx
│   ├── context/
│   │   ├── AuthContext.tsx               ← Supabase auth (pausado)
│   │   └── PlayerContext.tsx             ← Motor de audio PWA
│   └── hooks/
│       └── useBooks.ts                   ← CRUD libros (Supabase + backend)
└── .github/
    └── workflows/
        └── build-android-apk.yml         ← CI/CD APK automático
```

---

## ⚙️ VARIABLES DE ENTORNO REQUERIDAS (Cloud Run)

| Variable | Valor / Descripción |
|:---|:---|
| `APPWRITE_ENDPOINT` | `https://nyc.cloud.appwrite.io/v1` |
| `APPWRITE_PROJECT_ID` | `6a72f5d6002eeff78bc2` |
| `APPWRITE_API_KEY` | API Key del servidor Appwrite |
| `APPWRITE_DB_ID` | ID de la base de datos en Appwrite |
| `R2_ENDPOINT_URL` | URL endpoint de Cloudflare R2 |
| `R2_ACCESS_KEY_ID` | Access key de R2 |
| `R2_SECRET_ACCESS_KEY` | Secret key de R2 |
| `R2_BUCKET` | Nombre del bucket R2 |
| `R2_PUBLIC_URL` | URL pública del bucket R2 |
| `OPENROUTER_API_KEY` | Key para chat IA (opcional) |

---

## ⚠️ RESTRICCIONES ACTIVAS

1. **Supabase eliminado** — completamente removido del código. No restaurar.
2. **Render eliminado** — backend 100% en Google Cloud Run. No restaurar.
3. **AutoMirrored icons** no compatibles con el runner de GitHub Actions — usar `Icons.Default.*`
4. **Google OAuth** requiere que el dominio de callback esté configurado en Google Cloud Console
5. **Appwrite `global_books`** necesita tener los atributos `title`, `category`, `added_by`, `book_id`, `cover_url`, `parts_count` creados como atributos de la colección
6. **DIRECTIVA_CERO_HARDCODING** — `APPWRITE_API_KEY` y todas las credenciales SOLO desde variables de entorno, sin valores por defecto hardcodeados

---

## 📌 COMMITS IMPORTANTES

| Commit | Descripción |
|:---|:---|
| `82b99f8` | fix(critical): add missing buildUi() call in onCreate — blank white screen |
| `5f4c994` | fix(auth): fix email registration + Google OAuth Chrome Custom Tab |
| `a992df7` | fix(backend): remove Supabase dependency from /api/audio and /api/upload-pdf |
| `2b771d9` | feat: full PWA parity — LibraryScreen tabs+categories+search, BookCard owner actions, HistoryScreen, UploadScreen mandatory fields, SettingsScreen profile+logout, backend Appwrite-auth |
| `pendiente` | fix: remove Supabase+Render; fix login (network_security_config, async session verify, OAuth parser); persist progress SharedPreferences; background music Custom Commands |

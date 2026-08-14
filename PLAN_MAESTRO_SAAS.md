# Libris Audio — Plan maestro hacia el modelo SaaS

> Plan de ejecución paso a paso. Cada meta tiene tareas concretas y **criterio de
> aceptación** (cómo saber que está terminada).
>
> Basado en una auditoría real del código (`backend/main.py`, 1109 líneas, y la
> app Kotlin), no en supuestos.

---

## 0. Estado actual — lo que encontré en el código

### Lo que ya funciona a tu favor

- **El motor de ingesta es correcto.** `extract_text_from_pdf` → `clean_text_for_tts`
  → `chunk_text(3800)` → texto plano en R2 → TTS bajo demanda → audio cacheado en R2.
  Guardar **texto plano** y generar audio solo cuando se pide es exactamente la
  arquitectura que hay que tener. No hay que rehacer nada aquí.
- **`clean_text_for_tts` ya es un filtro de ruido embrionario**: descarta líneas que
  son solo un número y las de tipo "página 12". Es la semilla del filtro académico
  de Speechify.
- **PyMuPDF abre mucho más que PDF.** Verificado con archivos de prueba reales:
  EPUB ✅, FB2 ✅, CBZ ✅, TXT ✅. MuPDF además declara MOBI, XPS y SVG.
  **Sin dependencias nuevas.**
- Ya existe borrado con verificación de propietario (`DELETE /api/books/{id}`) y
  estado por usuario (`/api/user-state/{user_id}`).

### Los tres hallazgos críticos

**🔴 1. Todo lo que sube un usuario va a un catálogo global.**
`POST /api/upload-pdf` escribe en la colección `global_books`, y `GET /api/books`
devuelve **todos** los documentos de esa colección a **cualquiera** que llame al
endpoint. Es decir: hoy, si un usuario sube un PDF con derechos de autor, ese libro
queda disponible para todos los usuarios de la app. **Esto es distribución, no
copia privada.** Es el bloqueante número uno del nuevo modelo.

**🔴 2. El contenido se sirve por URL pública.**
`r2_public_url()` devuelve `{R2_PUBLIC_URL}/{key}`, una URL abierta y permanente.
Aunque dejes de listar los libros de usuario, **el audio y el texto siguen siendo
accesibles por quien tenga o adivine la URL**. Ocultar de la lista no basta: hay
que servir el contenido de usuario con URLs firmadas y caducas.

**🟠 3. "Mi Biblioteca" se llena sola y no se puede limpiar.**
El código pone `progressPercent` a un mínimo de 1% en cuanto abres un libro
("Un libro empezado siempre muestra ≥1% para aparecer en Mi Biblioteca"), y la
sección filtra por `progressPercent > 0`. Abrir un libro por curiosidad lo deja
ahí para siempre y **no hay ninguna forma de quitarlo**. Exactamente el problema
que describes.

---

## Arquitectura objetivo

### Modelo de datos — separar catálogo de contenido privado

```
catalog_books     ← dominio público / CC. Visible para TODOS. Solo lo llena el admin.
user_books        ← subidas privadas. owner_id OBLIGATORIO. NUNCA se lista en público.
user_library      ← estantería/historial por usuario (soft-hide)
user_state        ← progreso y preferencias (ya existe)
```

`GET /api/books` pasa a devolver: **`catalog_books` completo + `user_books` cuyo
`owner_id` sea el del usuario autenticado**. Sin token, solo catálogo.

### Pipeline de ingesta universal

```
archivo (cualquier formato)
   ↓ detector de formato + detector de DRM
   ↓ extractor por formato  ─────────┐
   ↓ ¿el texto es suficiente?  ─ no ─┴→ OCR
   ↓ normalizador  →  {capitulos[], bloques[]}
   ↓ filtro de ruido académico
   ↓ texto plano + índice  →  R2 (privado)
   ↓ TTS bajo demanda      →  audio cacheado en R2
```

La clave es que **todo desemboca en la misma estructura interna**. El TTS, el
karaoke, el índice de capítulos y el copiloto de IA no saben ni les importa de qué
formato venía el archivo.

---

## META 0 — Aislamiento y control de la biblioteca 🔴 BLOQUEANTE

*Nada de lo demás debe lanzarse antes que esto. Es lo que sostiene el modelo legal.*

| # | Tarea |
|---|---|
| 0.1 | Crear `user_books` en Appwrite con `owner_id` obligatorio e índice por `owner_id` |
| 0.2 | Migrar los libros existentes de `global_books`: los de dominio público → `catalog_books`; los subidos por usuarios → `user_books` con su `owner_id` |
| 0.3 | `POST /api/upload` exige autenticación y escribe **siempre** en `user_books` con el `owner_id` de la sesión |
| 0.4 | `GET /api/books` devuelve catálogo + solo los propios; sin token, solo catálogo |
| 0.5 | Servir texto y audio de `user_books` con **URL firmada y caducidad corta** (10-15 min), no con URL pública |
| 0.6 | Los endpoints `/api/audio`, `/api/timing` y `/api/text` verifican propiedad antes de responder |

### Los dos modos de borrado

| Modo | Qué hace | Aplica a |
|---|---|---|
| **Quitar de mi biblioteca** | Borra la entrada del historial/estantería. El libro sigue existiendo. Reversible: se vuelve a añadir si lo abres otra vez | **Todos** los libros, también los del catálogo |
| **Eliminar definitivamente** | Borra el documento de `user_books`, el texto de R2, **todos** los audios generados y las entradas de historial de ese libro | **Solo** los que subió ese usuario |

| # | Tarea |
|---|---|
| 0.7 | `DELETE /api/library/{book_id}` — quita del historial. Cualquier libro |
| 0.8 | `DELETE /api/books/{book_id}?purge=true` — borrado total. Solo el propietario. Debe barrer también `audio/{book_id}/*` y `text/{book_id}/*` en R2 (ya tienes `r2_list_prefix` y `r2_delete`) |
| 0.9 | UI: deslizar para quitar de la biblioteca + opción "Eliminar definitivamente" con confirmación explícita en los propios |
| 0.10 | Dejar de forzar `progressPercent = 1%` al abrir. Un libro entra en la biblioteca cuando se escucha de verdad (p. ej. >30 s o >2% del contenido) |

**Criterio de aceptación:** con dos cuentas distintas, la cuenta B no ve ni puede
descargar por URL directa nada subido por la cuenta A. Y la cuenta A puede vaciar
su biblioteca y borrar sus documentos por completo.

### Blindaje legal que acompaña a esta meta

| # | Tarea |
|---|---|
| 0.11 | Términos de servicio: el usuario declara tener derecho sobre lo que sube |
| 0.12 | Procedimiento de retirada por aviso + contacto visible |
| 0.13 | Sin compartir, sin enlaces públicos, sin recomendaciones cruzadas de contenido subido |
| 0.14 | **Revisión de un abogado antes de abrir la subida al público** |

---

## META 1 — Formatos universales

Reordené tu lista para poner primero lo que da más valor por hora de trabajo.

| # | Tarea | Notas |
|---|---|---|
| 1.1 | Aceptar **EPUB, FB2, CBZ, TXT, MOBI** | Ya funciona con PyMuPDF. Es cambiar el filtro `.endswith(".pdf")` por una lista y probar |
| 1.2 | **Índice de capítulos desde el TOC** | `doc.get_toc()` te da el índice real en EPUB/MOBI/FB2. En PDF hay que seguir con heurística de tamaño de fuente, que ya tienes |
| 1.3 | **Detección de DRM** | Si el archivo está protegido: mensaje claro *"Este archivo está protegido por DRM. Reprodúcelo en la aplicación donde lo compraste."* Nunca romperlo |
| 1.4 | **DOCX** | `python-docx` |
| 1.5 | **HTML / MHTML / Markdown** | Trivial, abre el mercado de documentación técnica y apuntes |
| 1.6 | **RTF / ODT / DjVu** | Solo si aparece demanda. Vía Pandoc o Calibre. ⚠️ Calibre es GPLv3: invocarlo como proceso aparte suele estar bien, confirmar antes de empaquetar |

**Criterio de aceptación:** un EPUB con capítulos se sube, se lee, y el índice de
capítulos aparece navegable en la app.

---

## META 2 — OCR: el formato que de verdad falta

Hoy, un PDF escaneado devuelve `422 "El PDF no contiene texto extraíble"`. El
usuario no entiende por qué y se va. Y muchísimo libro universitario en español
circula escaneado.

| # | Tarea |
|---|---|
| 2.1 | Detectar "PDF sin capa de texto": si los caracteres extraídos por página están por debajo de un umbral, es un escaneo |
| 2.2 | OCR de PDF escaneado (Tesseract con `spa`+`eng`, o un OCR en la nube si el coste compensa) |
| 2.3 | **OCR de fotos (JPG/PNG)**: el alumno fotografía las páginas del libro de la biblioteca. Es el caso de uso más natural que existe y ninguno de tus competidores lo hace bien |
| 2.4 | CBZ/CBR con OCR (sin él son solo imágenes, no hay nada que leer) |
| 2.5 | Barra de progreso: el OCR es lento, el usuario tiene que ver que algo pasa |

**Criterio de aceptación:** un PDF escaneado y una foto de una página producen
texto legible y audio correcto.

---

## META 3 — Ponerse al nivel de los mejores

### De Speechify

| # | Tarea |
|---|---|
| 3.1 | **Filtro de ruido académico.** Ampliar `clean_text_for_tts`: saltar citas entre paréntesis tipo `(Freud, 1915, p. 43)`, URLs, DOIs, notas al pie, encabezados repetidos entre páginas, y numeración de listas huérfana. **Debe ser configurable** — un investigador puede querer oír las citas |
| 3.2 | **Velocidad hasta 4x** sin distorsión de tono. Hoy tu tope es 2.0x |

### De ElevenReader

| # | Tarea |
|---|---|
| 3.3 | **Sincronización multidispositivo al segundo.** Ya tienes `/api/user-state`; falta guardar posición exacta y resolver conflictos por marca de tiempo |
| 3.4 | **Voces expresivas.** Depende del proveedor TTS; evaluar coste frente a edge-tts actual antes de comprometerse |

### De NaturalReader

| # | Tarea |
|---|---|
| 3.5 | **Modo dislexia**: OpenDyslexic + interlineado y espaciado configurables. Encaja con tu sistema de fuentes por género, que ya está montado |
| 3.6 | **Exportar a MP3** el libro completo |

### Lo que ellos NO tienen y tú sí

| # | Tarea |
|---|---|
| 3.7 | **Música ambiental ligada al marco/género** (B3 del backlog: subir el catálogo real a R2). Es tu diferenciador real |
| 3.8 | **Marcos como premium**: 2 gratis, los 12 en Premium |
| 3.9 | **Karaoke para aprender idiomas** (shadowing): PDF en inglés, voz nativa, palabra resaltada. Aprovecha que la app ya es bilingüe |

---

## META 5 (APLAZADA) — Monetización

> **No entra ahora.** Antes hay que terminar esta app y construir entera la
> versión de Windows. Se retoma cuando ambas plataformas estén en pie.

| # | Tarea |
|---|---|
| 4.1 | Planes y créditos: topes por caracteres procesados y por preguntas de IA |
| 4.2 | Copiloto de IA sobre el documento: resumen por capítulo, cuestionarios, explicaciones |
| 4.3 | Pasarela de pago multi-país (Stripe no cubre bien toda LatAm: mirar Mercado Pago / dLocal) |
| 4.4 | **Métricas de coste por usuario** — sin esto no puedes fijar precio |

---

## META 4 — Deuda pendiente y pulido

| # | Tarea |
|---|---|
| 5.1 | `updateDismissed` por versión en `SharedPreferences`, no en `remember` |
| 5.2 | Actualizar `MARCOS_ILUSTRADOS_SPEC.md` (ahora son WebP en `drawable-nodpi` con sufijo `_wide`) |
| 5.3 | Retoques de marcos: rayos de Espiritual, borde ancho de Comedia 16:9 |
| 5.4 | Arreglar la numeración duplicada del backlog en `MATRIZ_DE_MEJORAS.md` (hay dos B3, dos B4 y dos B5) |
| 5.5 | Variante `drawable-sw600dp-nodpi` de los marcos para tablets, si se ven blandos |

---

## Orden de ejecución recomendado

```
META 0  ─────────────────────────────►  bloqueante, antes de abrir subidas
   │
   ├── META 1 (formatos)  ──┐
   │                        ├──►  META 3 (paridad)  ──►  META 4 (deuda)
   └── META 2 (OCR)  ───────┘
                                          ⋮
                              versión Windows completa
                                          ⋮
                                    META 5 (cobrar)
```

**META 1 y META 2 van en paralelo** — tocan partes distintas del pipeline. Para no
trabajar doble, el punto de encuentro es el **normalizador**: META 1 aporta los
extractores por formato y META 2 el extractor por OCR, pero **ambos escriben en la
misma estructura** `{capitulos[], bloques[]}`. Conviene escribir primero esa
interfaz y que cada extractor sea un módulo que la cumpla; así añadir un formato
nuevo no toca nada más.

## Riesgos vivos

| Riesgo | Mitigación |
|---|---|
| Abrir subidas antes de META 0 | No lanzar. Es el riesgo legal más serio del proyecto |
| Coste de tokens de IA sin techo | Créditos desde el día uno, nunca "ilimitado" |
| OCR caro o lento | Medir antes de ofrecerlo en el plan gratuito |
| Regenerar audio ya generado | Cachear en R2 y no reprocesar jamás |
| Calibre GPLv3 | Confirmar la licencia antes de empaquetar |

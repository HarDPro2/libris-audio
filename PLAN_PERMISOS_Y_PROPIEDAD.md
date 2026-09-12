# Plan — permisos, propiedad y el motor en la versión comercial

> Libris Audio · 2026-09-12 · escrito después de revisar el código de cada punto,
> no de memoria. Cada apartado dice **qué hay hoy** antes de decir qué hacer.

---

## ⏱️ PARA EMPEZAR LA PRÓXIMA SESIÓN

Lee esto primero y arranca por aquí, en este orden.

### Lo que quedó a medias y se retoma de una

**1. Terminar la migración de la biblioteca.** Van 5 de 83 libros resubidos.
El resto es un solo comando que tarda unos 20 minutos, y si se corta continúa
donde iba porque lleva registro en `migracion_biblioteca.json`:

```powershell
cd "E:\PROYECTO LIBRIS AUDIO\libris-audio-main\backend"
$env:APPWRITE_API_KEY = "standard_..."   # sale del describe de Cloud Run
python subir_biblioteca.py --carpeta "E:\PROYECTO LIBRIS AUDIO\LIBROS" --subir --email alberto.javier.gonzalez@gmail.com
```

Ojo con La Divina Comedia (7,2 MB), La Odisea (6,3) y Guerra y Paz (6,0), que
son los únicos que podrían acercarse al límite de 600 s.

**2. Verificar el modo comunidad.** Que el hermano suba un libro desde su cuenta
y que aparezca en el catálogo del otro. Según el código ya funciona, pero eso
son dos comprobaciones de escritorio y falta la de verdad.

**3. `asignar_propietario.py`.** Falta escribirlo. Pone `added_by` en los 13
libros que siguen con `"biblioteca"` y que no se pueden resubir porque no hay
PDF. Sin eso, nadie puede borrarlos ni editarlos desde la app.

### Estado de la biblioteca al cerrar la sesión del 12-09-2026

| | |
|:---|:---|
| Libros en el catálogo | 97 |
| Resubidos con el motor nuevo | 5 (Analectas, 1984, El Extranjero, Un mundo feliz, El libro de los espíritus) |
| Pendientes de resubir | 78 |
| Sin PDF, no se pueden resubir | 13 |
| Reparados en sitio (no se resuben) | Zaratustra, Los Mediums |
| Con pegotes de la versión vieja del script | Ana Karenina, Analectas (ya resubido), Schopenhauer |

Ana Karenina y Schopenhauer se arreglan solos al resubirse, de modo que no hay
que despegarlos a mano.

### Lo verificado, para no repetir trabajo

- Los dos Kardec quedaron limpios y **verificados contra su propio respaldo** con
  `comparar.py`: 960 cambios, 0 que alarguen el texto, 0 sospechosos.
- *El libro de los espíritus* se reemplazó por una edición mejor, de 282 partes,
  que entró limpia de una sola pasada.
- El motor tarda **1,85 s por libro** en producción.
- La voz por defecto de Libris sigue siendo Jorge (es-MX). Se probó cambiarla a
  Sebastián (es-VE) y se revirtió.

---

## 1 · Guardar el MP3 y escuchar sin conexión

### Lo que ya existe y NO está bloqueado

La escucha sin conexión **funciona y es gratis**. `data/OfflineManager.kt` descarga
audio, texto y tiempos de karaoke a `filesDir/offline/{bookId}/`, el botón está en
`PlayerScreen.kt`, y hay pantalla de gestión con el total de bytes ocupados.

El único candado `Premium` de toda la app son **los marcos 3D**: `Premium.MARCOS_GRATIS`
deja gratis CLASSIC y MEDIEVAL, y el resto pide premium. Nada más está restringido —
ni la descarga, ni las voces, ni la velocidad, ni el karaoke.

### Lo que falta de verdad

**El endpoint `/api/export-mp3/{book_id}` existe en el backend y tiene CERO
referencias en Android.** Une las partes ya generadas en un solo MP3 y lo devuelve.
Nadie puede llamarlo desde la app.

Y ojo con un detalle suyo: solo une **audio ya cacheado**, no genera nada. En un libro
recién subido no hay MP3 todavía, así que el export saldría vacío o incompleto.

### Qué hacer

1. Botón *Exportar MP3* en `PlayerScreen`, junto al de descarga.
2. Antes de llamar, comprobar cuántas partes tienen audio. Si faltan, avisar:
   *"Este libro tiene 40 de 231 partes generadas. Escúchalo entero o descárgalo
   primero para poder exportarlo completo."*
3. Guardar en `Downloads/` por `MediaStore`, no en el almacenamiento interno, para que
   el archivo se pueda pasar a otro sitio. Eso es lo que pide "guardar el MP3".
4. **Decisión pendiente para Libris:** como es la versión personal, lo coherente es
   dejar `MARCOS_GRATIS` con los doce géneros y que el candado premium viva solo en
   Quantum Text Codex. Es una línea en `Premium.kt`.

---

## 2 · Que los libros de una cuenta los vean todos

### Lo que ya existe

`backend/ajustes.py` tiene el **modo comunidad encendido por defecto**:

- `visible_para()` devuelve `True` para todos cuando `MODO_COMUNIDAD` está activo.
- Cada libro nuevo entra con `visibility: "catalog"`.
- `_assert_can_read` no filtra nada en modo comunidad.

En las variables de Cloud Run **no aparece `MODO_COMUNIDAD`**, así que corre con el
valor por defecto: encendido. En principio ya funciona.

### Qué hacer — verificarlo de verdad, no suponerlo

Que tu hermano suba un libro desde su cuenta y que tú lo veas en tu catálogo. Es la
única prueba que vale; las otras dos cuentas de comprobación (leer el código, mirar la
variable) ya están hechas y dicen que sí.

Si no apareciera, el orden de sospecha es: la variable puesta a `0` en algún sitio, o
el campo `visibility` mal escrito en el documento de Appwrite del libro nuevo.

---

## 3 · Que quien sube un libro pueda borrarlo y editarlo

### Lo que ya existe

El backend **ya hace exactamente eso**:

| Acción | Endpoint | Quién puede |
|---|---|---|
| Borrar | `DELETE /api/books/{id}` | solo si `added_by == tu user_id` |
| Editar título y categoría | `PATCH /api/books/{id}` | igual |

Y la subida **ignora a propósito** el campo `added_by` del formulario y toma el
propietario del token de sesión, para que nadie pueda atribuirse un libro ajeno.

### El problema real, y es de datos, no de código

Los 97 libros del catálogo entraron con `added_by: "biblioteca"`, que no es el id de
nadie. Por eso a ti nunca te apareció el botón de borrar: el backend responde 403
porque `"biblioteca" != tu id`.

**La migración lo está arreglando para 83**, que quedan a tu nombre al resubirse.

Quedan **14 sin arreglo**, los que no tienen PDF en disco — entre ellos *El libro de
los espíritus*, que es el que acabamos de limpiar. Esos siguen sin dueño.

### Qué hacer

1. Un script corto, `asignar_propietario.py`, que ponga `added_by` en el documento de
   Appwrite de un libro concreto o de todos los que tengan `"biblioteca"`.
   Simula por defecto, como todos los demás.
2. Verificar en la app que los botones **Editar** y **Borrar** de `BookCard` aparecen
   según propiedad y no siempre. Si hoy se muestran a todo el mundo y el backend
   responde 403, el usuario ve un error en vez de no ver el botón.
3. Decidir quién será el dueño de los 14 huérfanos: tú, por ser quien administra.

---

## 4 · El motor de calidad en la versión comercial

### La premisa a corregir

El diccionario **no tiene licencia de uso personal**. `es_ES.aff` y `es_ES.dic` son
**triple licencia — MPL-2.0 / LGPL-3 / GPL-3+ —** a elección de quien los use, y se
incluyen bajo **MPL-2.0**, que es copyleft *por archivo*: permite distribuirlos dentro
de un producto comercial y cerrado siempre que (a) no se modifiquen, (b) se conserve el
aviso y (c) la fuente siga disponible en el proyecto de origen. Las tres se cumplen.
Está documentado en `backend/diccionarios/LICENCIA.md`.

### Qué se puede llevar a Quantum Text Codex, y bajo qué licencia

| Pieza | Origen | Licencia | ¿Comercial? |
|---|---|---|---|
| `guiones.py` | nuestro | nuestra | sí |
| `basura.py` | nuestro | nuestra | sí |
| `calidad.py` | nuestro | nuestra | sí |
| `calidad_ia.py` | nuestro | nuestra | sí |
| `revision.py` | nuestro | nuestra | sí |
| `es_ES.aff` / `.dic` | RLA-ES / LibreOffice | MPL-2.0 | **sí**, sin modificar |
| `spylls` | Zverik | MIT | sí |

**El motor entero es portable tal cual.** No hace falta variante ni sustituto.

### Lo que sí bloquea la versión comercial (y ya lo sabíamos)

Nada de esto tiene que ver con el diccionario:

- **PyMuPDF — AGPL-3.0.** Es el extractor de PDF. Con cláusula de red: usarlo en un
  servicio obliga a publicar el código. Artifex litiga esto (*Artifex v. Hancom*).
  Sustituto ya elegido: **pypdfium2** (BSD/Apache).
- **edge-tts — GPL + "meant for personal use".** Es la voz. Sustituto ya elegido:
  **Kokoro** (Apache-2.0), verificado en español en el Bloque 1.

### La única regla que hay que respetar para siempre

**Nunca modificar `es_ES.dic` ni `es_ES.aff`.** Si el motor necesita palabras propias
—nombres de personajes, términos de un dominio— van en un archivo aparte que
consultemos además del diccionario. Modificar esos dos archivos activaría la
obligación de la MPL de publicar el archivo modificado.

Merece un comentario en `calidad.py`, donde se cargan, para que nadie lo olvide dentro
de seis meses.

---

## Orden propuesto

1. **Verificar la comunidad** (punto 2) — cuesta una subida de tu hermano y cierra la duda.
2. **`asignar_propietario.py`** (punto 3) — deja los 14 huérfanos con dueño y completa
   lo que la migración no puede.
3. **Botones de la app** (puntos 1 y 3) — exportar MP3, y que Editar/Borrar aparezcan
   según propiedad. Esto sí necesita versión nueva del APK.
4. **Quantum Text Codex** (punto 4) — copiar el motor cuando toque, sin cambios.

---

## Lo que NO hay que hacer

- **No hace falta un diccionario alternativo.** Era la premisa de partida y es falsa.
- **No hace falta "devolver" el permiso de escuchar sin conexión**: nunca se quitó.
  Lo único bloqueado en toda la app son diez marcos 3D.

---

## 5 · La web / PWA — DESCARTADA a propósito (2026-09-12)

**No intentes arreglarla.** Decisión tomada: se sustituye por la versión de
Windows, así que invertir en ella es trabajo tirado.

### Qué le pasa, para que no haya que diagnosticarlo otra vez

El frontend se quedó **a medias** en la migración de Supabase a Appwrite. De
Appwrite no tiene ni una referencia; de Supabase, tres archivos:

| Archivo | Qué hace | Estado |
|---|---|---|
| `src/lib/supabase.ts` | cliente | apunta a un proyecto que ya NO existe |
| `src/context/AuthContext.tsx` | todo el login | `ERR_NAME_NOT_RESOLVED` al entrar |
| `src/hooks/useBooks.ts` | lee las tablas `global_books` y `user_books` | no ve los libros del backend |

Y aunque el login funcionara, mandaría el token de Supabase como `Bearer` a un
backend que valida sesiones de **Appwrite**: las rechazaría todas.

El Android no tiene ninguno de estos problemas porque sí está en Appwrite.

### Lo que sí sirve para la versión de Windows

El backend **ya tiene todos los endpoints** que un cliente necesita, y no hay
que tocar nada del servidor:

```
GET    /api/books            GET /api/audio/{id}/{n}     GET /api/index/{id}
POST   /api/upload-pdf       GET /api/timing/{id}/{n}    GET /api/export-mp3/{id}
DELETE /api/books/{id}       GET /api/text/{id}/{n}      POST /api/chat-book
PATCH  /api/books/{id}       DELETE /api/library/{id}     GET/PUT /api/user-state/{id}
```

Autenticación: sesión de Appwrite, y el token va como
`Authorization: Bearer <secreto de sesión>`. El backend lo valida contra
`/account` de Appwrite usando la cookie `a_session_<project>`.

Cuando llegue el cliente de Windows, eso es todo el contrato que necesita.

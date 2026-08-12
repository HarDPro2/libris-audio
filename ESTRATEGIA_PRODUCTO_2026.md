# Libris Audio — Estrategia de producto y negocio (agosto 2026)

> Documento de trabajo. Consolida la investigación de mercado en cuatro bloques:
> **modelo de negocio**, **tareas**, **mejoras posibles** y **problemas a evitar**.
>
> **Aviso sobre las cifras.** Marco cada dato con su nivel de confianza:
> ✅ verificado en fuente pública · ⚠️ sin verificar, tratar como hipótesis.
> Las cifras ⚠️ vienen de una conversación con un asistente de IA y **no deben
> usarse para decidir precios ni firmar nada** sin comprobarlas.

---

## 1. El giro estratégico

**De:** "app de audiolibros en español" → competías contra Audible y Storytel, con
catálogo de dominio público y sin forma de crecer sin pagar licencias.

**A:** **motor de lectura inmersiva con IA** → vendes la tecnología (TTS + karaoke
sincronizado + música por género + copiloto de estudio), no el contenido.

Por qué el giro importa, en una frase: **el contenido pasa a costar cero y el
usuario aporta el suyo**, así que el margen deja de depender de negociar con
editoriales y pasa a depender de tus costes de cómputo, que sí controlas.

### El embudo nuevo

```
Catálogo libre (clásicos + manuales + tutoriales + documentales)
        ↓  el usuario prueba la tecnología sin registrarse
El usuario sube su propio PDF / EPUB (espacio privado)
        ↓
TTS + karaoke + música ambiental + copiloto IA sobre ese documento
        ↓
Descarga offline (audio ya generado, cacheado)
```

El caso de uso que lo justifica todo, en palabras del propio usuario objetivo:
*"estoy estudiando psicología; en vez de ojear libro por libro, subo el PDF a la
app, me muevo por capítulos, lo descargo para escucharlo offline y uso la IA para
resolver tareas."*

---

## 2. Modelo de negocio

### 2.1 Por qué NO licenciar libros comerciales (todavía)

Los tres esquemas del mercado, y por qué ninguno cuadra con una app independiente:

| Modelo | Quién lo usa | Cómo paga | Por qué te mata |
|---|---|---|---|
| **Pago por escucha** | Audible | % del precio de lista por reproducción (⚠️ 25–50%) | ⚠️ Con lista de $20, pagas $5–10 **por reproducción**. Dos libros al mes y una suscripción de $15 ya va en pérdidas |
| **Fondo común** | Storytel | Bolsa mensual repartida por cuota de horas escuchadas | Pagas céntimos por hora, pero necesitas escala para que la editorial te acepte |
| **Consumo acotado** | Spotify Audiobooks | Tarifa por minuto real, con tope (15 h/mes incluidas) | Requiere poder negociar tarifas por minuto |

Además, una app pequeña no negocia editorial por editorial: entra por un
distribuidor (Bookwire, Zebralution), que ⚠️ se queda un 15–20% de las regalías, y
las editoriales grandes suelen exigir un **anticipo garantizado** que pierdes si no
lo consumes.

**Decisión:** no licenciar ahora. Si algún día quieres bestsellers, hazlo como
**tienda a la carta** — el usuario paga ese libro concreto y le trasladas el coste
de la licencia. Nunca dentro de la suscripción plana.

### 2.2 Estructura de planes propuesta

**Plan Gratuito — adquisición**

- Catálogo libre completo (clásicos, manuales, tutoriales, documentales de dominio público o CC)
- 1–2 voces neurales estándar
- Subida privada: 1–2 PDF al mes, máx. ~30 páginas
- Copiloto IA: ~5 preguntas al mes
- Sin descarga offline · anuncios sutiles
- **2 marcos 3D** desbloqueados

**Plan Premium — $4.99–$7.99/mes**

- Subida de 15–20 documentos grandes al mes (con tope de caracteres, no de archivos)
- Navegación por capítulos indexada (texto y audio sincronizados)
- Copiloto IA por créditos: resúmenes, cuestionarios, explicaciones
- Descarga offline del audio ya generado
- Las 12 voces + karaoke + música ambiental por género
- **Los 9 marcos 3D** y los que vengan

### 2.3 Los marcos como palanca de monetización

Esto es un activo real que ningún competidor tiene. Úsalo en tres direcciones:

1. **Como gancho de conversión.** 2 marcos gratis, el resto en Premium.
2. **Como recompensa.** Desbloquear marcos por rachas de lectura o por horas escuchadas.
3. **Ligado al audio.** Si el marco es Guerra, música orquestal de percusión de fondo;
   si es Romance, acústica suave. El marco deja de ser decoración y pasa a ser el
   selector de atmósfera completa. Ahí no te alcanza nadie.

### 2.4 Estructura de costes a vigilar

```
PDF subido → almacenamiento (céntimos)
           → procesamiento TTS (moderado, una sola vez)
           → tokens del copiloto IA (por pregunta, el más volátil)
```

Regla de oro: **generar el audio una sola vez y cachearlo en R2**. La segunda
descarga del mismo usuario no debe costarte nada de cómputo.

---

## 3. Mapa competitivo

| | **Speechify** | **ElevenReader** | **NaturalReader** | **Libris Audio** |
|---|---|---|---|---|
| Precio | ✅ **$29/mes** o **$139/año** ($11.58/mes) | ⚠️ ~$11/mes · $99/año | ⚠️ $9.92–$19.99/mes | **$4.99–$7.99** (objetivo) |
| Gratis | ✅ 10 voces, tope 1.5x | Funcional | Limitado | Catálogo libre completo |
| Público | Profesionales EE. UU./Europa | Consumidor general | Escuelas / accesibilidad | **Universitarios hispanos + bilingües** |
| Chat con el PDF | Sí, avanzado | **No** | Limitado | Sí, orientado a estudio |
| Voces | ✅ 30+ HD, hasta 4.5x | Excelentes, expresivas, 32 idiomas | Media/alta | 63 voces (42 ES + 21 EN) |
| Inmersión | **Ninguna** | **Ninguna** | **Ninguna** | **Música + marcos + tipografía por género** |
| Karaoke | Resaltado básico | Básico | Sí | Sí, fluido |

**Lectura del mapa:** el hueco está en la intersección de *herramienta de estudio*
× *experiencia inmersiva* × *precio LatAm*. Speechify tiene lo primero y cobra
$29. ElevenLabs tiene las mejores voces y ninguna herramienta de estudio.
Nadie tiene lo segundo. Y **ninguno de los tres apunta al hispanohablante**.

---

## 4. Qué aprender de cada competidor (mejoras a implementar)

### De Speechify

- **Filtro de ruido académico.** Detecta y salta citas entre paréntesis
  ("...según Freud (1915, p. 43)..."), URLs, números de página y encabezados
  repetidos. Sin esto, escuchar un PDF universitario es insufrible. **Es la
  función más importante de toda esta lista.**
- **Velocidad hasta 4.5x sin distorsión de tono.** Hoy tu tope es 2.0x. Los
  estudiantes en época de exámenes lo piden explícitamente.

### De ElevenReader

- **Voces expresivas por contexto** — que la voz susurre o cambie de tono según lo
  que lee. Depende del proveedor TTS, pero conviene tenerlo en el radar.
- **Sincronización multidispositivo al segundo exacto.** Pausas en el móvil y
  continúas en la web en el mismo punto. Tú ya tienes progreso local en
  `SharedPreferences`; esto es exactamente lo que resolvería la colección
  `user_books` de Appwrite que llevas pendiente en el backlog.

### De NaturalReader

- **Modo dislexia**: fuente OpenDyslexic e interlineado configurable. Encaja
  perfecto con tu sistema de fuentes por género, que ya está montado.
- **Exportar a MP3** descargable.

---

## 5. Problemas a evitar

### 5.1 Legales — el punto más delicado

El argumento de "copia privada" (el usuario sube su archivo, la responsabilidad es
suya) **es razonable pero no es un escudo automático**, y depende de la
jurisdicción. Para sostenerlo necesitas, como mínimo:

- Almacenamiento **estrictamente por usuario**, sin ninguna vía de compartir
  archivos entre cuentas. En el momento en que un PDF subido por A sea accesible
  para B, dejas de ser una herramienta y pasas a ser un distribuidor.
- **Procedimiento de retirada por aviso** (notice & takedown) documentado y con
  un contacto visible.
- Términos de servicio que declaren que el usuario garantiza tener derecho sobre
  lo que sube.
- **No indexar, no recomendar y no mostrar públicamente** el contenido subido.

⚠️ **Esto hay que consultarlo con un abogado antes de lanzar la subida de
archivos.** No es una formalidad: es la diferencia entre el modelo y una demanda.

### 5.2 De negocio

- **No meter libros licenciados en la tarifa plana.** Un solo usuario maratónico
  te deja en pérdidas.
- **No copiar el precio de Speechify.** Tu ventaja es geográfica; si cobras
  $29 pierdes la única ventaja estructural que tienes.
- **No cobrar por almacenamiento sino por caracteres procesados.** El coste real
  es el TTS y los tokens, no los megabytes.

### 5.3 Técnicos

- **Tokens de IA sin tope = factura sin tope.** Créditos mensuales desde el día uno,
  no "ilimitado" con letra pequeña.
- **Regenerar audio ya generado.** Cachear en R2 y no volver a procesar jamás.
- **Consumo de datos móviles** (el error de ElevenReader): si generas la voz en la
  nube en tiempo real sin caché, te comes el plan de datos del usuario.

---

## 6. Tareas

### P0 — habilitan el modelo de negocio

| # | Tarea | Notas |
|---|---|---|
| 1 | **Subida de PDF/EPUB por usuario**, almacenamiento privado aislado | Es la función que convierte la app en SaaS |
| 2 | **Filtro de ruido académico** antes del TTS | Citas, URLs, números de página, encabezados |
| 3 | **Indexado por capítulos** con salto en texto y audio | |
| 4 | **Caché de audio generado en R2** | Protege el margen |
| 5 | **Sistema de planes y créditos** (gratis / premium) | Topes por caracteres y por preguntas de IA |
| 6 | **Pasarela de pago multi-país** | Stripe cubre LatAm de forma desigual: verificar país por país |
| 7 | **Términos de servicio + takedown + revisión legal** | Bloqueante antes de abrir la subida |

### P1 — diferenciación

| # | Tarea |
|---|---|
| 8 | **Copiloto IA sobre el documento**: resumen por capítulo, cuestionarios, explicación de conceptos |
| 9 | **Música ambiental ligada al marco/género** (el B3 del backlog: subir catálogo real a R2) |
| 10 | **Marcos como recompensa/premium**: 2 gratis, resto de pago |
| 11 | **Velocidad hasta 4x** sin distorsión |
| 12 | **Sincronización multidispositivo** (colección `user_books` en Appwrite) |

### P2 — accesibilidad y alcance

| # | Tarea |
|---|---|
| 13 | **Modo dislexia**: OpenDyslexic + interlineado |
| 14 | **Exportar a MP3** |
| 15 | **Karaoke para aprender idiomas** (shadowing): PDF en inglés, voz nativa, karaoke visual. Aprovecha que la app ya es bilingüe |
| 16 | Ampliar catálogo libre: manuales, tutoriales, documentales (dominio público / CC) |

### Ya en marcha (no perder de vista)

- 9 géneros × 2 orientaciones de marcos 3D — faltan **Poesía, Noir y Cósmico**
- Auto-actualizador arreglado (`ON_RESUME` + botón manual)
- Barra plegable Temas/Efectos

---

## 7. Métricas a instrumentar desde el principio

Sin estas cifras no puedes fijar el precio ni saber si el plan gratuito te está
desangrando:

- **Coste por usuario/mes**: caracteres TTS + tokens de IA + almacenamiento
- **Conversión gratis → premium**
- **Horas escuchadas por usuario** (te dirá si el tope del plan gratis está bien puesto)
- **% de usuarios que suben documento propio** — es *la* métrica del nuevo modelo:
  mide si el giro funcionó
- **Retención a 7 y 30 días**, segmentada por si usan marcos o no. Si los marcos
  suben la retención, tienes la justificación para monetizarlos

---

## 8. Preguntas abiertas

1. ¿Qué proveedor de LLM para el copiloto? Afecta directamente al coste variable.
2. ¿Pasarela de pago? Stripe no opera igual en todos los países de LatAm; hay que
   mirar Mercado Pago o dLocal según mercado.
3. ¿Precio final: $4.99 o $7.99? Depende de la métrica de coste por usuario, que
   todavía no tienes. **No fijes precio antes de tener el punto 7.**
4. ⚠️ Verificar de primera mano los precios de ElevenReader y NaturalReader, y los
   porcentajes de regalías y de Bookwire, si alguna vez se retoma la vía de licencias.

---

*Fuentes verificadas: precios de Speechify (texttolab.com, mayo 2026).
El resto de cifras marcadas ⚠️ proceden de la investigación previa y están
pendientes de confirmación en fuente primaria.*

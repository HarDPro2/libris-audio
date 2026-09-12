# Motor de calidad de texto — diseño

> Libris Audio · 2026-09-12 · Medido sobre *Historia de las Indias de Nueva España*,
> 20 páginas escaneadas pasadas por OCR real.

---

## Lo que ya corre al subir

El arreglo de los guiones **ya está cableado en las tres rutas de extracción**
(PDF con texto, OCR, texto plano). Cualquier libro nuevo sale con las palabras
enteras. `reparar_libros.py` es solo para los 154 que ya estaban.

Lo que falta es la capa de encima: los errores de OCR.

---

## Por qué no sirve un corrector ortográfico normal

Primera medición, con un diccionario de español corriente:

| | |
|---|---|
| Palabras distintas | 439 |
| "Desconocidas" | **235 (53,5%)** |
| Con "corrección" propuesta | 183 |

Y las correcciones eran así:

```
años     → año        adoraban → adorable
aguas    → agua       anunció  → anuncio
algunos  → alguno     antiguas → antigua
```

**Habría destrozado el texto.** `adoraban → adorable` cambia el sentido de una
frase entera. El problema: ese diccionario no tiene plurales ni conjugaciones,
así que casi todo el español normal le parece desconocido.

---

## Los tres filtros que sí funcionan

Un error de OCR tiene tres marcas a la vez. Exigirlas todas es lo que separa
la señal del ruido.

**1 · Es raro en el libro** (≤2 apariciones)
Un error de escaneo aparece una o dos veces; una palabra de verdad se repite.

**2 · Está a una letra de una palabra frecuente del MISMO libro**
`tiera` a una letra de `tierra`, que sale 13 veces. El libro es su propio
diccionario — el mismo truco que resolvió los guiones, y el que permite
acertar con *Motecuhzoma* o *Chalchiuhcihuall*, que no están en ningún lado.

**3 · No es una palabra española válida**
Aquí importa el diccionario: con **hunspell** (que sí tiene morfología),
`años`, `adoraban`, `fiestas`, `qué`, `eran`, `hacía`, `nombres` se reconocen
como válidas y ni se plantean.

### El efecto de encadenarlos

| Etapa | Candidatas |
|---|---|
| Palabras distintas en 20 páginas | 874 |
| Solo filtro 1+2 (frecuencia) | 55 |
| \+ filtro 3 con diccionario pobre | 39 · *2 falsos por cada acierto* |
| **\+ filtro 3 con hunspell** | **16** |

**De 874 a 16. Un 98% de reducción, y 14 de las 16 son aciertos reales:**

```
mos       → los          aor   → por         tiera → tierra
cémo      → cómo         daa   → día         ela   → era
mexico    → méxico       aio   → año         clección → elección
carpírulo → carírulo     molecuhzoma → motecuhzoma
```

---

## Y aquí es donde la IA gana su sitio

De las 16, dos cosas que lo mecánico **no puede** resolver:

### 1. Elige mal el destino

```
dias  (2x)  →  dios (10x)
```

Debería ser **días**, no *dios*. La frecuencia no distingue; el contexto sí.
Una IA leyendo *"los dias de fiesta"* acierta sin dudar.

### 2. No ve los errores sistemáticos

Esto es lo más revelador de toda la medición:

```
carpírulo → carírulo   <- el destino TAMPOCO es español válido
caríruro  → carírulo
caríruno  → carírulo
caprulo   → capírulo
carfruto  → caríruto
```

**`carírulo` aparece 80 veces y es, él mismo, un error de OCR de "capítulo".**
El método mecánico jamás lo detecta, porque confía en la frecuencia y esa
palabra es frecuentísima. Una IA lo ve a la primera.

Ochenta ocurrencias mal en 20 páginas. En el libro entero, más de mil.

---

## La arquitectura

```
SUBIDA (rápida, no bloquea)
   extraer texto  ->  unir guiones  ->  guardar  ->  responder al usuario
                                                        |
REVISIÓN (en segundo plano)                             v
   1. tres filtros mecánicos     874 palabras  ->  16 candidatas   [gratis]
   2. IA decide con contexto     16 decisiones                     [barato]
   3. errores sistemáticos       "carírulo" x80 -> una decisión     [el premio]
   4. aplicar + invalidar audio  (ya construido en reparar_libros.py)
```

**Coste real:** ~240 decisiones por libro de 300 páginas, en lotes de 20 = unas
12 llamadas por libro. La cascada gratuita de OpenRouter que ya tienes lo cubre.

**Dónde corre:** después de la subida, no durante. El usuario no espera.

---

## Las barandillas, que aquí son lo importante

Una IA suelta sobre el texto de un libro **lo reescribe**. Con Kardec eso es
inaceptable. Por eso:

1. **La IA nunca devuelve prosa.** Solo responde sí/no sobre palabras que ya
   marcaron los filtros mecánicos, y cuál es la corrección.
2. **Solo se acepta a distancia ≤2** de la palabra original. Si propone algo
   más lejos, se descarta sin discusión.
3. **Nunca toca palabras que no pasaron los tres filtros.** El 99,4% del texto
   es intocable por construcción.
4. **Todo queda en un informe** con la lista de cambios, para poder revisarlo
   y revertirlo.
5. **Los nombres propios raros se respetan.** *Huitzilopochtli* aparece poco y
   no está en el diccionario, pero no se parece a ninguna palabra frecuente
   del libro, así que ni entra en la lista.

---

## Lo que NO va a arreglar

Honestidad por delante:

- **`benevoloen- cia`** sigue saliendo *benevoloencia*. La palabra está rota en
  el original y no se parece lo bastante a nada frecuente.
- **Errores que produjeron una palabra válida.** Si el OCR convirtió *casa* en
  *caso*, no hay forma mecánica de saberlo, y la IA solo lo vería si el
  contexto la delata.
- **La calidad del escaneo manda.** Un PDF malo da texto malo; esto recorta el
  daño, no lo borra.

---

## Decisión que te toca a ti

**¿Los cambios se aplican solos o pasan por ti?**

- **Automático** — el libro queda listo sin que hagas nada. Riesgo: un cambio
  malo entra sin que nadie lo vea.
- **Con revisión** — el motor deja el informe y tú apruebas. Más seguro, pero
  son 154 libros y no vas a revisar mil decisiones.
- **Mixto** — se aplica solo lo que la IA marca con alta confianza y los
  errores sistemáticos (que son los que más rinden); el resto queda en el
  informe. *Es lo que yo haría.*

---

## Cableado al subir — hecho (2026-09-12)

`backend/revision.py` es el único punto de entrada. `main.py` lo llama en
`/api/upload-pdf`, después de extraer el texto y **antes de trocearlo**, porque
lo que se guarda en R2 es lo que el TTS leerá durante años.

Orden y coste, medido sobre un libro sintético de **873 KB / 90.000 palabras**:

| Paso | Red | Coste |
|---|---|---|
| 1 · Unir palabras cortadas por guion | no | incluido abajo |
| 2 · Detectar sospechosas (los tres filtros) | no | **0,45 s los dos juntos** |
| 3 · IA sobre las candidatas (lotes de 15) | sí | ~5 s por lote |
| 4 · Aplicar en modo Mixto | no | milisegundos |

Resultado de esa medición: *299 guiones unidos · 35 sospechosas · 0,45 s*.

### Lo que había que arreglar para que esto fuese viable

La primera versión tardaba **26,9 s** en ese mismo libro. El perfilado dejó claro
dónde: 25,6 s de los 27 se iban en sacar frases de ejemplo, con una expresión
regular por candidata sobre el libro entero. Ahora `calidad.contextos_de()`
recorre el texto **una sola vez** e indexa por palabra: **0,21 s**, las mismas 35
candidatas con el mismo contexto.

### El presupuesto de tiempo

Cloud Run corta la petición a los 300 s y un PDF escaneado ya gasta ~134 s solo
en OCR. Por eso `revisar()` recibe los segundos que le quedan:

```
presupuesto = LIMITE_PETICION_S - lo_que_ya_tardó - MARGEN_SUBIDA_S (60 s)
```

Si no llegan a 25 s, **se salta la IA** y lo escribe en el informe. Los pasos 1
y 2 no se saltan nunca: no dependen de la red y cuestan medio segundo.

Para darle aire a la IA en libros escaneados hay que subir el límite del
servicio, sin tocar código:

```bash
gcloud run deploy libris-audio-backend --timeout=600 \
  --set-env-vars LIMITE_PETICION_S=600
```

Interruptor de emergencia: `REVISION_AL_SUBIR=0` desactiva el motor entero.

### El diccionario ya no se instala, viaja dentro

`backend/diccionarios/es_ES.{aff,dic}` — 850 KB, triple licencia
MPL-2.0 / LGPL-3 / GPL-3+, sin modificar, leídos con **spylls** (MIT, Python
puro, no enlaza con hunspell). Ver `backend/diccionarios/LICENCIA.md`.

Con esto el motor funciona igual en Cloud Run, en Windows y en cualquier
portátil, y `hunspell-es` desaparece del `Dockerfile`. Carga: **0,5 s**, una vez
por proceso (`revision.diccionario()` lo cachea).

### Qué queda junto al libro

`{book_id}/revision.json` — guiones unidos, sospechosas encontradas, qué
corrigió la IA y **qué dejó pendiente de que lo mire una persona** (modo Mixto).

### Pruebas

`backend/test_revision.py` — 20 comprobaciones, sin red y sin el backend entero.
Cubre los dos formatos de guion (con salto de línea y ya aplanado), el
presupuesto agotado, la IA caída, la falta de diccionario y que el informe sea
JSON puro.

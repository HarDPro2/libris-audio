# 🎨 Marcos ilustrados PREMIUM por género — Dirección de arte

Complementa a `MARCOS_ILUSTRADOS_SPEC.md` (parte técnica/drop-in). Aquí se fija el
**estilo visual y los motivos por género** de la **2ª tanda de marcos = tier PREMIUM**.
Los marcos animados actuales quedan como gratuitos/fallback; estos ilustrados son de pago.

Basado en 5 referencias reales aprobadas por el usuario (Romance, Fantasía, Paranormal,
Medieval + un mockup en-app de Fantasía).

---

## ✅ Estado actual (v1.0.22)
- **Montados y funcionando 4 marcos**: `frame_love`, `frame_fantasy`, `frame_paranormal`,
  `frame_medieval` (procesados con `android/tools/procesar_marcos.py`: verde→transparente,
  fondo exterior→transparente, recorte, 1600px).
- **Sección nueva "Marcos 3D (Premium)"** en Ajustes = toggle opt-in. **Apagado por
  defecto** → se ven los marcos animados de siempre. Encendido → en el modo *Libro* se usa
  el marco ilustrado del género (si existe PNG); los géneros sin PNG siguen animados.
- Los animados **no se tocaron**: quedan como la opción gratuita/base.

## 🎯 Recomendación de formato para los PRÓXIMOS (importante)
Las 4 referencias vienen **apaisadas (~16:9) y con la ventana descentrada** (p.ej. en
Romance las rosas ocupan la izquierda y el hueco queda a la derecha), y Paranormal/Medieval
vienen **inclinados**. El recuadro del reproductor es **vertical**, así que al montarlos se
**estiran** un poco. Para que los siguientes encajen perfectos, generarlos así:
1. **Ventana centrada** (el hueco transparente en el centro, no a un lado).
2. **Orientación recta/de frente** (sin perspectiva ni inclinación).
3. **Proporción vertical** parecida al panel de lectura (aprox. **4:5 o 3:4**), consistente
   entre todos.
4. Adornos que **desbordan las esquinas** (eso sí se mantiene), pero repartidos para no
   dejar un lado vacío.
> Con eso, el mismo pipeline los deja listos y calzan sin estirar. Los 4 actuales sirven ya
> para validar en el dispositivo; si se ven muy estirados, se regeneran con este formato.

---

## 🟢 Regla de producción crítica: centro verde → transparente
Las referencias vienen con el **centro en verde chroma** para separarlo fácil. El PNG
final que entra en la app **debe llevar ese verde recortado a transparencia** (alfa), NO
verde. Por ese hueco se ve el texto del libro / karaoke.
- Recortar el verde (chroma key) → exportar **PNG-24 con canal alfa**.
- Sin halo/franja verde residual alrededor de la decoración.
- Marco y adornos opacos; solo el centro transparente.

## ✨ Rasgo clave: los adornos DESBORDAN el marco
En las 4 referencias los elementos temáticos **se salen del borde** (no quedan dentro del
rectángulo): cristales que rebasan la esquina superior-izquierda, hiedra/hojas/chispas que
caen por la inferior-derecha, humo que sale por un lado, espada cruzando una esquina. Ese
"romper el marco" es lo que da la sensación 3D/premium. Al exportar hay que **incluir ese
margen extra** alrededor (no recortar los adornos que sobresalen) y dejar zona transparente
suficiente para que respiren.

## 📐 Consistencia para uso en la app
- **Orientación recta (de frente).** Las referencias de Paranormal y Medieval están en
  perspectiva/inclinadas; para el reproductor conviene una versión **plana y centrada** que
  escale limpio (si no, se ve torcido sobre el texto).
- **Proporción común** entre géneros (recomendado ~16:9 o el aspecto del panel de lectura)
  y grosor de marco parecido, para intercambiarlos sin descuadres.
- Márgenes de seguridad interiores: la ornamentación no invade la zona central de texto.
- ~1500–2000px de ancho, PNG-24 con alfa.

## 🖼️ Cómo se ve montado (mockup en-app, referencia Fantasía)
El quinto ejemplo muestra el resultado final: fondo temático **difuminado** detrás, el
**marco con adornos desbordando** las esquinas (cristales arriba-izq, estela de chispas
abajo-der), y en el centro el **texto karaoke** con la **línea actual resaltada** (glow +
color de acento). El marco PNG se superpone; el texto y el resaltado los pinta la app.

---

## Motivos por género
Confirmados por referencia = ✅. El resto se extrapola en el mismo lenguaje visual
(placa ilustrada + adornos que desbordan una/dos esquinas + glow sutil).

| Género (BookBindingStyle) | Archivo | Marco / materiales | Adornos que desbordan |
|---|---|---|---|
| ✅ LOVE · Romance | `frame_love` | Oro rosa/cobre repujado, filigrana | Ramo de **rosas rojas** (sup-izq), **lazo de seda + sello de lacre** (inf-der), pétalos sueltos |
| ✅ FANTASY · Fantasía | `frame_fantasy` | **Mármol blanco + oro con runas** brillantes | **Cristales turquesa** (sup-izq), **hojas mágicas + chispas** (inf-der) |
| ✅ PARANORMAL | `frame_paranormal` | **Piedra tallada gris** oscura, gárgolas, calaveras, murciélagos, telarañas | **Humo morado** (sup-izq), **manos esqueléticas** agarrando (inf-der) |
| ✅ MEDIEVAL | `frame_medieval` | **Cuero marrón + hierro remachado**, nudos celtas | **Espada** cruzando la esquina (sup-izq), **hiedra/musgo** (inf-der) |
| CLASSIC · Clásico | `frame_classic` | Madera noble + filete dorado, sobrio | Voluta/laurel discreto en esquina, marcapáginas de cinta |
| SPIRITUAL · Espiritual | `frame_spiritual` | Mármol claro + oro, halo cálido | Rayos de luz, laurel/olivo, paloma |
| WAR · Bélico | `frame_war` | Metal gastado, remaches, tono militar | Bayoneta/casco, alambre de púas, humo gris |
| SCIENTIFIC · Ciencia | `frame_scientific` | Cromo/vidrio + circuito, azul neón | Órbitas/moléculas, líneas de circuito con glow |
| COMEDY · Comedia | `frame_comedy` | Colores vivos, trazo caricaturesco | Estrellas/confeti, máscaras de teatro |
| POETRY · Poesía | `frame_poetry` | Pergamino, tinta, oro viejo | Pluma de escribir, enredadera floral, caligrafía |
| NOIR | `frame_noir` | Negro/gris art déco, humo | Humo de cigarro, sombras, líneas déco doradas |
| COSMIC · Cósmico | `frame_cosmic` | Azul profundo + nebulosa, estrellado | Planetas/lunas, constelaciones, polvo estelar |

> Nombres de archivo **exactos** (tabla en `MARCOS_ILUSTRADOS_SPEC.md`). Solo minúsculas.

## Checklist de aprobación por marco
1. Centro **transparente** (verde recortado, sin halo).
2. Adornos temáticos correctos y **desbordando** la(s) esquina(s).
3. Orientación **recta**, proporción y grosor coherentes con el resto.
4. Los adornos NO tapan la zona central de texto.
5. ~1500–2000px, PNG-24 con alfa, estilo detallado (no plástico liso).
6. Nombre exacto → `res/drawable/` → recompilar.

## Flujo de producción
Generar referencia (centro verde, adornos desbordando) → recortar verde a alfa (conservando
el margen de los adornos) → aplanar/enderezar si viene en perspectiva → validar checklist →
renombrar `frame_<genero>.png` → `res/drawable/` → build. La app lo toma sola; los géneros
sin PNG siguen con el marco animado (fallback gratuito).

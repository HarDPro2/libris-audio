# 🖼️ Marcos ilustrados por género — Especificación de assets (2ª tanda)

Sistema **drop-in** ya cableado en `VirtualBookFrame.kt`. La app busca automáticamente
un PNG por género en `res/drawable/`. **Si existe → lo superpone. Si no → se queda el
marco animado actual** (sin romper nada). Los marcos animados quedan como opción/fallback.

## Cómo funciona (ya implementado)
- Helper `genreFrameImage(ctx, style)` resuelve por nombre con `resources.getIdentifier(...)`.
- Si devuelve un id válido, se dibuja `Image(painterResource, matchParentSize, FillBounds)`
  sobre el texto (por eso el **centro debe ser transparente**).
- Gate: solo se muestra si los efectos visuales (`fxOn`) están activos.
- **No hace falta tocar código para añadir marcos**: basta con soltar los PNG con el nombre
  exacto en `android/app/src/main/res/drawable/` y recompilar.

## Nombres de archivo requeridos (uno por género)
Colocar en `android/app/src/main/res/drawable/`:

| Género (BookBindingStyle) | Archivo            |
|---------------------------|--------------------|
| CLASSIC                   | `frame_classic.png`    |
| MEDIEVAL                  | `frame_medieval.png`   |
| SPIRITUAL                 | `frame_spiritual.png`  |
| WAR                       | `frame_war.png`        |
| LOVE                      | `frame_love.png`       |
| PARANORMAL                | `frame_paranormal.png` |
| SCIENTIFIC                | `frame_scientific.png` |
| COMEDY                    | `frame_comedy.png`     |
| FANTASY                   | `frame_fantasy.png`    |
| POETRY                    | `frame_poetry.png`     |
| NOIR                      | `frame_noir.png`       |
| COSMIC                    | `frame_cosmic.png`     |

> Nombres solo en minúsculas, sin espacios ni guiones (regla de recursos Android).

## Requisitos de cada PNG
1. **Centro transparente (hueco).** La decoración vive en el **borde y las esquinas**;
   el centro debe dejar ver el texto del libro. Nada de fondo verde ni relleno opaco.
2. **Forma de marco** (no una imagen de fondo). Solo el perímetro decorado.
3. **Relación de aspecto fija y consistente** entre todos los géneros para que escalen
   igual (`FillBounds` estira; si todos comparten proporción, no se deforman).
4. **Márgenes de seguridad** interiores: que la ornamentación no invada la zona de lectura.
5. **Resolución ~1500–2000 px de ancho** con transparencia (PNG-24 con alfa).
6. **Estilo coherente** en los 12: mismo tratamiento de trazo/textura. Buscamos algo
   **tosco/detallado (ilustrado), no liso ni metálico ni 3D-render**.
7. **Acentos en esquinas** (espadas/escudo/corona en medieval, telarañas/árbol seco/
   manos esqueléticas en paranormal, cristales/rosas en fantasy, etc.). Pueden ir dentro
   del mismo PNG o como capas separadas que "desborden" el borde en una futura iteración.

## Flujo para la próxima sesión
1. Generar/producir los 12 PNG según esta spec.
2. Soltarlos en `res/drawable/` con los nombres exactos de la tabla.
3. Recompilar. Cada libro toma el marco de su género automáticamente.
4. Los géneros sin PNG siguen mostrando el marco animado (transición gradual posible).

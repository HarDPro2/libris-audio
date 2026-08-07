package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.nativeCanvas
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.ThemeAnimation
import kotlin.math.*
import kotlin.random.Random

/**
 * Fondo animado que cambia por completo según el estilo del tema.
 * La firma se mantiene: AnimatedBackground(preset, modifier).
 */
@Composable
fun AnimatedBackground(
    preset: AppThemePreset,
    modifier: Modifier = Modifier
) {
    val transition = rememberInfiniteTransition(label = "bg")

    // Tiempo lento continuo 0..1 (para deriva, lluvia, brasas — con módulo es fluido)
    val t by transition.animateFloat(
        initialValue = 0f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(24000, easing = LinearEasing), RepeatMode.Restart),
        label = "t"
    )
    // Tiempo rápido 0..1 (para parpadeos)
    val tFast by transition.animateFloat(
        initialValue = 0f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(6000, easing = LinearEasing), RepeatMode.Restart),
        label = "tFast"
    )

    val p = preset.primary
    val s = preset.secondary
    val bg = preset.background

    Canvas(modifier = modifier.fillMaxSize()) {
        drawRect(color = bg)
        when (preset.animation) {
            ThemeAnimation.MESH      -> drawMesh(t, p, s)
            ThemeAnimation.NEURAL    -> drawNeural(t, tFast, p, s)
            ThemeAnimation.QUANTUM   -> drawQuantum(t, p, s)
            ThemeAnimation.MATRIX    -> drawMatrix(t, p, s, bg)
            ThemeAnimation.RETRO     -> drawRetro(t, p, s, bg)
            ThemeAnimation.AURORA    -> drawAurora(t, p, s)
            ThemeAnimation.STARFIELD -> drawStarfield(t, tFast, p, s)
            ThemeAnimation.INK       -> drawInk(t, tFast, p, s)
            ThemeAnimation.EMBERS    -> drawEmbers(t, p, s)
        }
    }
}

// ── MESH: dos orbes de gradiente flotando ──────────────────────────────────
private fun DrawScope.drawMesh(t: Float, p: Color, s: Color) {
    val a = t * 2f * PI.toFloat()
    val o1 = Offset(size.width * 0.3f + cos(a) * size.width * 0.25f,
                    size.height * 0.3f + sin(a) * size.height * 0.2f)
    val o2 = Offset(size.width * 0.7f + sin(a) * size.width * 0.3f,
                    size.height * 0.7f + cos(a) * size.height * 0.25f)
    drawCircle(Brush.radialGradient(listOf(p.copy(alpha = 0.35f), Color.Transparent), o1, size.width * 0.7f),
        size.width * 0.7f, o1)
    drawCircle(Brush.radialGradient(listOf(s.copy(alpha = 0.25f), Color.Transparent), o2, size.width * 0.8f),
        size.width * 0.8f, o2)
}

// ── NEURAL: nodos + conexiones que pulsan ──────────────────────────────────
private fun DrawScope.drawNeural(t: Float, tFast: Float, p: Color, s: Color) {
    val rnd = Random(7)
    val n = 26
    val xs = FloatArray(n); val ys = FloatArray(n); val ph = FloatArray(n)
    for (i in 0 until n) {
        val bx = rnd.nextFloat() * size.width
        val by = rnd.nextFloat() * size.height
        ph[i] = rnd.nextFloat() * 6.28f
        val drift = 18f
        xs[i] = bx + cos(t * 2f * PI.toFloat() + ph[i]) * drift
        ys[i] = by + sin(t * 2f * PI.toFloat() * 0.8f + ph[i]) * drift
    }
    val maxDist = size.width * 0.28f
    for (i in 0 until n) {
        for (j in i + 1 until n) {
            val dx = xs[i] - xs[j]; val dy = ys[i] - ys[j]
            val d = sqrt(dx * dx + dy * dy)
            if (d < maxDist) {
                val base = 1f - d / maxDist
                val pulse = 0.5f + 0.5f * sin(tFast * 6.28f + ph[i] + ph[j])
                drawLine(
                    color = p.copy(alpha = base * 0.30f * pulse),
                    start = Offset(xs[i], ys[i]), end = Offset(xs[j], ys[j]),
                    strokeWidth = 1.4f
                )
            }
        }
    }
    for (i in 0 until n) {
        val glow = 0.6f + 0.4f * sin(tFast * 6.28f + ph[i])
        drawCircle(Brush.radialGradient(listOf(s.copy(alpha = 0.9f * glow), Color.Transparent),
            Offset(xs[i], ys[i]), 22f), 22f, Offset(xs[i], ys[i]))
        drawCircle(p, 2.6f, Offset(xs[i], ys[i]))
    }
}

// ── QUANTUM: partículas orbitando + ondas expansivas ───────────────────────
private fun DrawScope.drawQuantum(t: Float, p: Color, s: Color) {
    val c = Offset(size.width * 0.5f, size.height * 0.42f)
    // Ondas expansivas
    for (k in 0 until 3) {
        val prog = (t + k / 3f) % 1f
        val r = prog * size.width * 0.75f
        drawCircle(color = p.copy(alpha = (1f - prog) * 0.25f), radius = r, center = c,
            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2f))
    }
    // Glow central
    drawCircle(Brush.radialGradient(listOf(s.copy(alpha = 0.20f), Color.Transparent), c, size.width * 0.4f),
        size.width * 0.4f, c)
    // Partículas orbitando
    val rnd = Random(11)
    val n = 34
    for (i in 0 until n) {
        val radius = (0.12f + rnd.nextFloat() * 0.42f) * size.width
        val speed = 0.5f + rnd.nextFloat() * 1.4f
        val dir = if (rnd.nextBoolean()) 1f else -1f
        val base = rnd.nextFloat() * 6.28f
        val ang = base + dir * t * 2f * PI.toFloat() * speed
        val ecc = 0.6f + rnd.nextFloat() * 0.4f
        val pos = Offset(c.x + cos(ang) * radius, c.y + sin(ang) * radius * ecc)
        val col = if (i % 2 == 0) p else s
        drawCircle(col.copy(alpha = 0.9f), 2.2f, pos)
        drawCircle(col.copy(alpha = 0.18f), 6f, pos)
    }
}

// ── MATRIX: lluvia de código ───────────────────────────────────────────────
private fun DrawScope.drawMatrix(t: Float, p: Color, s: Color, bg: Color) {
    val paint = android.graphics.Paint().apply {
        isAntiAlias = true
        textSize = 30f
        typeface = android.graphics.Typeface.MONOSPACE
    }
    val step = 34f
    val cols = (size.width / step).toInt().coerceAtLeast(1)
    val glyphs = "01ｱｶﾐﾂﾈﾎﾘ ﾊﾍﾏ01"
    val rnd = Random(3)
    val trail = 11
    for (ci in 0 until cols) {
        val x = ci * step + 6f
        val speed = 0.5f + rnd.nextFloat() * 1.7f
        val offset = rnd.nextFloat()
        val headNorm = (t * speed + offset) % 1.2f
        val headY = headNorm * (size.height + 300f) - 150f
        for (k in 0 until trail) {
            val y = headY - k * step
            if (y < -step || y > size.height + step) continue
            val alpha = (1f - k / trail.toFloat())
            val col = if (k == 0) Color.White else p.copy(alpha = alpha * 0.85f)
            paint.color = android.graphics.Color.argb(
                (col.alpha * 255).toInt().coerceIn(0, 255),
                (col.red * 255).toInt(), (col.green * 255).toInt(), (col.blue * 255).toInt()
            )
            val gi = ((ci * 31 + k * 7 + (t * 6).toInt()) % glyphs.length).absoluteValue
            drawContext.canvas.nativeCanvas.drawText(glyphs[gi].toString(), x, y, paint)
        }
    }
}

// ── RETRO: rejilla en perspectiva + sol synthwave ──────────────────────────
private fun DrawScope.drawRetro(t: Float, p: Color, s: Color, bg: Color) {
    val horizon = size.height * 0.52f
    // Cielo degradado
    drawRect(Brush.verticalGradient(listOf(bg, p.copy(alpha = 0.12f), bg),
        startY = 0f, endY = horizon), size = Size(size.width, horizon))
    // Sol con bandas
    val sunC = Offset(size.width * 0.5f, horizon - 40f)
    val sunR = size.width * 0.16f
    drawCircle(Brush.verticalGradient(listOf(p, s), sunC.y - sunR, sunC.y + sunR), sunR, sunC)
    for (b in 0 until 6) {
        val by = sunC.y + (b * 8f)
        drawRect(bg, topLeft = Offset(sunC.x - sunR, by), size = Size(sunR * 2, 4f + b))
    }
    // Rejilla suelo (líneas horizontales que se acercan)
    val gridColor = s.copy(alpha = 0.5f)
    for (i in 0 until 16) {
        val prog = ((i / 16f) + t) % 1f
        val y = horizon + prog * prog * (size.height - horizon)
        drawLine(gridColor.copy(alpha = (1f - prog) * 0.6f), Offset(0f, y), Offset(size.width, y), 1.5f)
    }
    // Líneas verticales convergiendo al punto de fuga
    val vp = Offset(size.width * 0.5f, horizon)
    for (i in -8..8) {
        val bx = size.width * 0.5f + i * size.width * 0.14f
        drawLine(gridColor.copy(alpha = 0.4f), vp, Offset(bx, size.height), 1.5f)
    }
}

// ── AURORA: cortinas boreales ──────────────────────────────────────────────
private fun DrawScope.drawAurora(t: Float, p: Color, s: Color) {
    val bands = 4
    for (b in 0 until bands) {
        val col = if (b % 2 == 0) p else s
        val path = Path()
        val yBase = size.height * (0.25f + b * 0.13f)
        val amp = size.height * 0.10f
        val phase = t * 2f * PI.toFloat() + b
        path.moveTo(0f, yBase)
        var x = 0f
        while (x <= size.width) {
            val y = yBase + sin(x / size.width * 3.5f * PI.toFloat() + phase) * amp
            path.lineTo(x, y); x += 24f
        }
        path.lineTo(size.width, size.height)
        path.lineTo(0f, size.height)
        path.close()
        drawPath(path, Brush.verticalGradient(
            listOf(col.copy(alpha = 0.22f), Color.Transparent),
            startY = yBase - amp, endY = yBase + size.height * 0.25f))
    }
}

// ── STARFIELD: estrellas titilando + libros flotando ───────────────────────
private fun DrawScope.drawStarfield(t: Float, tFast: Float, p: Color, s: Color) {
    val rnd = Random(19)
    // Estrellas
    for (i in 0 until 90) {
        val x = rnd.nextFloat() * size.width
        val y = rnd.nextFloat() * size.height
        val ph = rnd.nextFloat() * 6.28f
        val tw = 0.3f + 0.7f * (0.5f + 0.5f * sin(tFast * 6.28f + ph))
        val r = 0.6f + rnd.nextFloat() * 1.8f
        val col = if (i % 5 == 0) s else Color.White
        drawCircle(col.copy(alpha = tw * 0.9f), r, Offset(x, y))
    }
    // Nebulosa suave
    val c = Offset(size.width * 0.7f, size.height * 0.3f)
    drawCircle(Brush.radialGradient(listOf(p.copy(alpha = 0.18f), Color.Transparent), c, size.width * 0.6f),
        size.width * 0.6f, c)
    // Libros flotando (rectángulos inclinados que ascienden)
    val rb = Random(23)
    for (i in 0 until 7) {
        val bx = rb.nextFloat() * size.width
        val speed = 0.4f + rb.nextFloat() * 0.6f
        val yNorm = (1f - (t * speed + rb.nextFloat()) % 1f)
        val by = yNorm * size.height
        val sz = 10f + rb.nextFloat() * 10f
        val col = if (i % 2 == 0) p else s
        drawRect(col.copy(alpha = 0.5f), topLeft = Offset(bx, by), size = Size(sz * 0.75f, sz))
        drawRect(col.copy(alpha = 0.9f), topLeft = Offset(bx, by), size = Size(2f, sz))
    }
}

// ── INK: tinta ascendente + letras flotando ────────────────────────────────
private fun DrawScope.drawInk(t: Float, tFast: Float, p: Color, s: Color) {
    // Manchas de tinta ascendentes
    val rnd = Random(29)
    for (i in 0 until 16) {
        val bx = rnd.nextFloat() * size.width
        val speed = 0.3f + rnd.nextFloat() * 0.7f
        val yNorm = (1f - (t * speed + rnd.nextFloat()) % 1f)
        val by = yNorm * size.height
        val r = (14f + rnd.nextFloat() * 30f) * (0.4f + yNorm * 0.6f)
        drawCircle(Brush.radialGradient(listOf(p.copy(alpha = 0.10f), Color.Transparent),
            Offset(bx, by), r), r, Offset(bx, by))
    }
    // Letras flotando
    val paint = android.graphics.Paint().apply {
        isAntiAlias = true
        textSize = 40f
        typeface = android.graphics.Typeface.SERIF
    }
    val letters = "AaÆ¶&ZñQ"
    val rl = Random(31)
    for (i in 0 until 8) {
        val bx = rl.nextFloat() * size.width
        val speed = 0.25f + rl.nextFloat() * 0.5f
        val yNorm = (1f - (t * speed + rl.nextFloat()) % 1f)
        val by = yNorm * size.height
        val alpha = (sin(yNorm * PI.toFloat())).coerceIn(0f, 1f) * 0.5f
        val col = s.copy(alpha = alpha)
        paint.color = android.graphics.Color.argb(
            (col.alpha * 255).toInt().coerceIn(0, 255),
            (col.red * 255).toInt(), (col.green * 255).toInt(), (col.blue * 255).toInt())
        paint.textSize = 28f + rl.nextFloat() * 26f
        drawContext.canvas.nativeCanvas.drawText(letters[i % letters.length].toString(), bx, by, paint)
    }
}

// ── EMBERS: brasas / chispas ascendentes ───────────────────────────────────
private fun DrawScope.drawEmbers(t: Float, p: Color, s: Color) {
    // Resplandor inferior
    drawRect(Brush.verticalGradient(listOf(Color.Transparent, p.copy(alpha = 0.12f)),
        startY = size.height * 0.6f, endY = size.height))
    val rnd = Random(37)
    for (i in 0 until 55) {
        val bx = rnd.nextFloat() * size.width
        val speed = 0.4f + rnd.nextFloat() * 1.2f
        val yNorm = (1f - (t * speed + rnd.nextFloat()) % 1f)
        val by = yNorm * size.height
        val sway = sin(t * 6.28f * 2f + i) * 12f
        val x = bx + sway * (1f - yNorm)
        val flick = 0.5f + 0.5f * sin(t * 6.28f * 3f + i)
        val r = (1f + rnd.nextFloat() * 2.2f) * (0.4f + yNorm * 0.6f)
        val col = if (i % 3 == 0) s else p
        val alpha = sin(yNorm * PI.toFloat()).coerceIn(0f, 1f) * flick
        drawCircle(col.copy(alpha = alpha * 0.9f), r, Offset(x, by))
        drawCircle(col.copy(alpha = alpha * 0.25f), r * 2.5f, Offset(x, by))
    }
}

package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.LocalDensity
import kotlin.math.PI
import kotlin.math.floor
import kotlin.math.sin
import kotlin.random.Random

/**
 * Capa animada ambiental por género (subtema visual sobre el marco del libro).
 * Cada estilo tiene su "clima": polvo dorado, brasas, pétalos, luciérnagas,
 * lluvia noir, estrellas cósmicas… Partículas ligeras en un solo Canvas.
 * Se dibuja detrás del texto con alpha baja para no estorbar la lectura.
 */
private enum class FxShape { DUST, EMBER, PETAL, WISP, NODE, CONFETTI, FIREFLY, INK, RAIN, STAR }

private data class GenreFx(
    val shape: FxShape,
    val colors: List<Color>,
    val count: Int,
    val direction: Int,   // -1 sube, +1 baja
    val baseAlpha: Float,
    val sizeMin: Float,
    val sizeMax: Float,
    val sway: Float,      // vaivén horizontal (fracción del ancho)
    val periodMs: Int
)

private fun fxFor(style: BookBindingStyle): GenreFx = when (style) {
    BookBindingStyle.CLASSIC ->
        GenreFx(FxShape.DUST, listOf(Color(0xFFB45309), Color(0xFFEAC086)), 22, -1, 0.22f, 1.4f, 3.2f, 0.04f, 14000)
    BookBindingStyle.MEDIEVAL ->
        GenreFx(FxShape.EMBER, listOf(Color(0xFFF59E0B), Color(0xFFDC2626)), 26, -1, 0.55f, 1.4f, 3.2f, 0.05f, 6000)
    BookBindingStyle.SPIRITUAL ->
        GenreFx(FxShape.WISP, listOf(Color(0xFFC4B5FD), Color(0xFFFFFFFF)), 14, -1, 0.28f, 3.5f, 8f, 0.06f, 12000)
    BookBindingStyle.WAR ->  // ceniza cayendo
        GenreFx(FxShape.DUST, listOf(Color(0xFF9CA3AF), Color(0xFF6B7280)), 22, 1, 0.18f, 1.8f, 4.5f, 0.05f, 15000)
    BookBindingStyle.LOVE ->
        GenreFx(FxShape.PETAL, listOf(Color(0xFFF9A8D4), Color(0xFFEC4899)), 18, 1, 0.55f, 4.5f, 9f, 0.09f, 9000)
    BookBindingStyle.PARANORMAL ->
        GenreFx(FxShape.WISP, listOf(Color(0xFF8B5CF6), Color(0xFFA78BFA)), 12, -1, 0.30f, 5f, 11f, 0.09f, 10000)
    BookBindingStyle.SCIENTIFIC ->
        GenreFx(FxShape.NODE, listOf(Color(0xFF06B6D4), Color(0xFF67E8F9)), 20, -1, 0.35f, 2f, 4f, 0.05f, 11000)
    BookBindingStyle.COMEDY ->
        GenreFx(FxShape.CONFETTI, listOf(Color(0xFFF97316), Color(0xFF22C55E), Color(0xFF3B82F6), Color(0xFFEC4899)), 24, 1, 0.70f, 2.6f, 5.5f, 0.08f, 8000)
    BookBindingStyle.FANTASY ->
        GenreFx(FxShape.FIREFLY, listOf(Color(0xFF34D399), Color(0xFF6EE7B7)), 22, -1, 0.70f, 1.4f, 3.2f, 0.07f, 9000)
    BookBindingStyle.POETRY ->
        GenreFx(FxShape.INK, listOf(Color(0xFFA78BFA), Color(0xFF7C3AED)), 16, 1, 0.35f, 2f, 4.5f, 0.05f, 12000)
    BookBindingStyle.NOIR ->  // lluvia
        GenreFx(FxShape.RAIN, listOf(Color(0xFF9CA3AF), Color(0xFFF59E0B)), 40, 1, 0.25f, 1f, 1.4f, 0f, 2200)
    BookBindingStyle.COSMIC ->
        GenreFx(FxShape.STAR, listOf(Color(0xFF22D3EE), Color(0xFFFFFFFF), Color(0xFFA5B4FC)), 34, -1, 0.85f, 1f, 2.4f, 0.02f, 16000)
}

private data class FxParticle(
    val baseX: Float,
    val phase: Float,
    val sizeT: Float,
    val speedT: Float,
    val colorIdx: Int,
    val blinkPhase: Float
)

private const val TWO_PI = (2.0 * PI).toFloat()
private fun frac(x: Float): Float = x - floor(x)

@Composable
fun GenreFrameOverlay(style: BookBindingStyle, modifier: Modifier = Modifier) {
    val fx = remember(style) { fxFor(style) }
    val density = LocalDensity.current.density
    val particles = remember(style) {
        List(fx.count) {
            FxParticle(
                baseX = Random.nextFloat(),
                phase = Random.nextFloat(),
                sizeT = Random.nextFloat(),
                speedT = 0.7f + Random.nextFloat() * 0.6f,
                colorIdx = Random.nextInt(fx.colors.size),
                blinkPhase = Random.nextFloat()
            )
        }
    }
    val transition = rememberInfiniteTransition(label = "genreFx")
    val t by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(fx.periodMs, easing = LinearEasing), RepeatMode.Restart),
        label = "genreFxT"
    )
    Canvas(modifier = modifier) {
        drawGenreParticles(fx, particles, t, density)
    }
}

private fun DrawScope.drawGenreParticles(
    fx: GenreFx,
    particles: List<FxParticle>,
    t: Float,
    density: Float
) {
    val w = size.width
    val h = size.height
    if (w <= 0f || h <= 0f) return

    particles.forEach { pt ->
        val p = frac(t * pt.speedT + pt.phase)
        val y = if (fx.direction < 0) h * (1f - p) else h * p
        val x = pt.baseX * w + sin((p + pt.phase) * TWO_PI) * fx.sway * w
        val env = sin(p.toDouble() * PI).toFloat().coerceIn(0f, 1f)  // fundido en extremos
        val color = fx.colors[pt.colorIdx % fx.colors.size]
        val sz = (fx.sizeMin + (fx.sizeMax - fx.sizeMin) * pt.sizeT) * density
        val center = Offset(x, y)

        when (fx.shape) {
            FxShape.DUST, FxShape.EMBER, FxShape.NODE -> {
                drawCircle(color.copy(alpha = fx.baseAlpha * env), radius = sz, center = center)
            }
            FxShape.FIREFLY, FxShape.STAR -> {
                val tw = 0.35f + 0.65f * (0.5f + 0.5f * sin((t * pt.speedT + pt.blinkPhase) * TWO_PI * 3f))
                val a = fx.baseAlpha * env * tw
                drawCircle(color.copy(alpha = a * 0.35f), radius = sz * 2.4f, center = center)  // halo
                drawCircle(color.copy(alpha = a), radius = sz, center = center)
            }
            FxShape.WISP, FxShape.INK -> {
                drawOval(
                    color = color.copy(alpha = fx.baseAlpha * env),
                    topLeft = Offset(x - sz, y - sz * 2.2f),
                    size = Size(sz * 2f, sz * 4.4f)
                )
            }
            FxShape.PETAL -> {
                val rot = (p + pt.phase) * 360f
                rotate(rot, pivot = center) {
                    drawOval(
                        color = color.copy(alpha = fx.baseAlpha * env),
                        topLeft = Offset(x - sz, y - sz * 0.6f),
                        size = Size(sz * 2f, sz * 1.2f)
                    )
                }
            }
            FxShape.CONFETTI -> {
                val rot = (p * 4f + pt.phase) * 360f
                rotate(rot, pivot = center) {
                    drawRect(
                        color = color.copy(alpha = fx.baseAlpha * env),
                        topLeft = Offset(x - sz, y - sz * 0.5f),
                        size = Size(sz * 2f, sz)
                    )
                }
            }
            FxShape.RAIN -> {
                val len = sz * 12f
                drawLine(
                    color = color.copy(alpha = fx.baseAlpha),
                    start = center,
                    end = Offset(x + sz * 1.5f, y + len),
                    strokeWidth = maxOf(1f, sz * 0.5f)
                )
            }
        }
    }
}

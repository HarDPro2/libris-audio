package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.NavigateBefore
import androidx.compose.material.icons.filled.NavigateNext
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.data.model.WordTiming
import com.librisaudio.app.util.PageTurnSound

/**
 * Estilos de encuadernación por género. Cada uno con degradado de tapa,
 * emblema, paleta de papel y acento propios.
 */
enum class BookBindingStyle(
    val title: String,
    val emblem: String,
    val coverStart: Color,
    val coverEnd: Color,
    val paperTop: Color,
    val paperBottom: Color,
    val textColor: Color,
    val accentColor: Color
) {
    CLASSIC(
        "Clásico", "📖",
        Color(0xFF5B3A1A), Color(0xFF2A1A08),
        Color(0xFFFDF6E3), Color(0xFFF3E4C2),
        Color(0xFF1E1003), Color(0xFFB45309)
    ),
    MEDIEVAL(
        "Medieval", "⚔️",
        Color(0xFF7F1D1D), Color(0xFF3B0A0A),
        Color(0xFFF5E6C8), Color(0xFFE7D2A0),
        Color(0xFF3B1A06), Color(0xFFB8860B)
    ),
    SPIRITUAL(
        "Espiritual", "🕊️",
        Color(0xFF7C6BB0), Color(0xFF3B2E63),
        Color(0xFFFBF7FF), Color(0xFFEDE4FB),
        Color(0xFF2E2352), Color(0xFF9F7AEA)
    ),
    WAR(
        "Guerra", "🎖️",
        Color(0xFF3F4A2E), Color(0xFF1C2113),
        Color(0xFFECEBDD), Color(0xFFCFCDB5),
        Color(0xFF20250F), Color(0xFF7C8A3E)
    ),
    LOVE(
        "Romance", "🌹",
        Color(0xFF9D174D), Color(0xFF500724),
        Color(0xFFFFF1F5), Color(0xFFFBD9E6),
        Color(0xFF4A0620), Color(0xFFEC4899)
    ),
    PARANORMAL(
        "Paranormal", "👻",
        Color(0xFF3B2E63), Color(0xFF0A0A14),
        Color(0xFF14121F), Color(0xFF0B0A12),
        Color(0xFFD7CDEB), Color(0xFF8B5CF6)
    ),
    SCIENTIFIC(
        "Científico", "🔬",
        Color(0xFF0E7490), Color(0xFF083344),
        Color(0xFFF0F9FF), Color(0xFFD6EEF9),
        Color(0xFF082F3D), Color(0xFF06B6D4)
    ),
    COMEDY(
        "Comedia", "🎭",
        Color(0xFFF59E0B), Color(0xFFB45309),
        Color(0xFFFFFDF2), Color(0xFFFDF1C7),
        Color(0xFF3B2A05), Color(0xFFF97316)
    ),
    FANTASY(
        "Fantasía", "🐉",
        Color(0xFF0F766E), Color(0xFF4C1D95),
        Color(0xFFF0FDFA), Color(0xFFDDEFE9),
        Color(0xFF10251F), Color(0xFF14B8A6)
    ),
    POETRY(
        "Poesía", "🖋️",
        Color(0xFF6D28D9), Color(0xFF3B0764),
        Color(0xFFFBF8FF), Color(0xFFEDE7F9),
        Color(0xFF2E1065), Color(0xFFA78BFA)
    ),
    NOIR(
        "Noir", "🔎",
        Color(0xFF1F2937), Color(0xFF030712),
        Color(0xFF12141A), Color(0xFF090A0F),
        Color(0xFFE5E7EB), Color(0xFFF59E0B)
    ),
    COSMIC(
        "Cósmico", "🚀",
        Color(0xFF4338CA), Color(0xFF0B1026),
        Color(0xFF0B1026), Color(0xFF070A1A),
        Color(0xFFDDE3FF), Color(0xFF22D3EE)
    )
}

@Composable
fun VirtualBookFrame(
    book: Book,
    textPart: String,
    currentPartIndex: Int,
    isPlaying: Boolean,
    isTextLoading: Boolean = false,
    currentPositionMs: Long = 0L,
    wordTimings: List<WordTiming> = emptyList(),
    onSeekTo: (Long) -> Unit = {},
    onNextPart: () -> Unit,
    onPreviousPart: () -> Unit,
    frames3dEnabled: Boolean = false,
    onToggleFrames3d: (Boolean) -> Unit = {},
    showControls: Boolean = true,
    modifier: Modifier = Modifier
) {
    val ctx = LocalContext.current
    var selectedStyle by remember { mutableStateOf(BookBindingStyle.CLASSIC) }
    var fontSizeSp by remember { mutableStateOf(16) }
    var fontMode by remember { mutableStateOf(0) }   // 0 = Género, 1 = Serif, 2 = Sans
    var highlightOn by remember { mutableStateOf(true) }
    var fxOn by remember { mutableStateOf(true) }    // capa animada ambiental por género
    // Marcos 3D ilustrados por género. El estado vive en PlayerViewModel (misma
    // preferencia "frames_3d" que usa Ajustes), así el botón del reproductor y
    // el interruptor de Ajustes nunca se desincronizan.
    val frames3dOn = frames3dEnabled
    var temasOpen by remember { mutableStateOf(false) }
    var efectosOpen by remember { mutableStateOf(false) }

    val activeFont = remember(fontMode, selectedStyle) {
        when (fontMode) {
            1 -> FontFamily.Serif
            2 -> FontFamily.Default
            else -> resolveGenreFont(ctx, selectedStyle)
        }
    }
    val fontLabel = when (fontMode) { 1 -> "Serif"; 2 -> "Sans"; else -> "Género" }

    var flipAngle by remember { mutableStateOf(0f) }
    val animatedAngle by animateFloatAsState(
        targetValue = flipAngle,
        animationSpec = spring(stiffness = Spring.StiffnessLow),
        label = "PageFlip"
    )
    // Brillo sutil que recorre el borde de la tapa
    val shimmer = rememberInfiniteTransition(label = "shimmer")
    val shimmerT by shimmer.animateFloat(
        0f, 1f, infiniteRepeatable(tween(4000, easing = LinearEasing), RepeatMode.Reverse),
        label = "shimmerT"
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(12.dp)
    ) {
        // Toolbar: estilos (scroll horizontal) + fuente. En pantalla completa se
        // oculta entera: el libro se queda solo, con el botón de salir del modo
        // inmersivo que ya dibuja PlayerScreen por encima.
        // Barra compacta: dos desplegables (Temas / Efectos) + tamaño y fuente.
        // Antes eran dos filas siempre visibles que le robaban alto al libro y
        // acababan tapadas por la decoración del marco 3D.
        if (showControls) Column(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                ToolChip("🎨 Temas", temasOpen, selectedStyle.accentColor) {
                    temasOpen = !temasOpen
                    if (temasOpen) efectosOpen = false
                }
                Spacer(Modifier.width(6.dp))
                ToolChip("🎇 Efectos", efectosOpen, selectedStyle.accentColor) {
                    efectosOpen = !efectosOpen
                    if (efectosOpen) temasOpen = false
                }
                Spacer(Modifier.weight(1f))
                IconButton(onClick = { if (fontSizeSp > 12) fontSizeSp -= 2 }) {
                    Text("A-", fontSize = 12.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { if (fontSizeSp < 26) fontSizeSp += 2 }) {
                    Text("A+", fontSize = 14.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { fontMode = (fontMode + 1) % 3 }) {
                    Text(fontLabel, fontSize = 10.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
            }

            // Panel de temas
            if (temasOpen) {
                Spacer(Modifier.height(6.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    BookBindingStyle.values().forEach { style ->
                        val selected = selectedStyle == style
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(10.dp))
                                .background(
                                    if (selected)
                                        Brush.horizontalGradient(listOf(style.coverStart, style.coverEnd))
                                    else Brush.horizontalGradient(listOf(Color(0x331E293B), Color(0x331E293B)))
                                )
                                .clickable { selectedStyle = style }
                                .padding(horizontal = 10.dp, vertical = 5.dp)
                        ) {
                            Text(
                                text = "${style.emblem} ${style.title}",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (selected) Color.White else Color(0xFF94A3B8)
                            )
                        }
                    }
                }
            }

            // Panel de efectos
            if (efectosOpen) {
                Spacer(Modifier.height(6.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    ToolChip("✨ Sync", highlightOn, selectedStyle.accentColor) { highlightOn = !highlightOn }
                    ToolChip("🎇 FX", fxOn, selectedStyle.accentColor) { fxOn = !fxOn }
                    ToolChip("🖼️ 3D", frames3dOn, selectedStyle.accentColor) { onToggleFrames3d(!frames3dOn) }
                }
            }
        }

        // Contenedor sin recorte: el marco base va dentro y el marco 3D se dibuja
        // encima, más grande, para que su hueco coincida con el borde exterior
        // del marco base y la decoración quede por fuera.
        val bookPadding = when {
            !frames3dOn   -> PaddingValues(0.dp)
            showControls  -> PaddingValues(start = 8.dp, end = 8.dp, top = 2.dp, bottom = 26.dp)
            else          -> PaddingValues(horizontal = 30.dp, vertical = 38.dp)
        }
        Box(modifier = Modifier.weight(1f).fillMaxWidth().padding(bookPadding)) {

        // Marco 3D del libro
        Box(
            modifier = Modifier
                .fillMaxSize()
                .shadow(20.dp, RoundedCornerShape(18.dp))
                .clip(RoundedCornerShape(18.dp))
                .background(Brush.verticalGradient(listOf(selectedStyle.paperTop, selectedStyle.paperBottom)))
                .border(
                    BorderStroke(
                        6.dp,
                        Brush.linearGradient(
                            colors = listOf(
                                selectedStyle.coverStart,
                                selectedStyle.accentColor,
                                selectedStyle.coverEnd
                            ),
                            start = Offset0(shimmerT),
                            end = Offset1(shimmerT)
                        )
                    ),
                    RoundedCornerShape(18.dp)
                )
        ) {
            // Sombra del lomo
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .width(18.dp)
                    .align(Alignment.CenterStart)
                    .background(Brush.horizontalGradient(listOf(Color(0x40000000), Color.Transparent)))
            )

            // Capa animada ambiental por género (detrás del texto, subtema visual)
            if (fxOn) {
                GenreFrameOverlay(
                    style = selectedStyle,
                    modifier = Modifier.matchParentSize()
                )
            }

            // Emblemas ornamentales en las esquinas (tenue)
            Text(selectedStyle.emblem, fontSize = 22.sp,
                modifier = Modifier.align(Alignment.TopEnd).padding(10.dp).graphicsLayer { alpha = 0.18f })
            Text(selectedStyle.emblem, fontSize = 22.sp,
                modifier = Modifier.align(Alignment.BottomStart).padding(10.dp).graphicsLayer { alpha = 0.18f })

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(22.dp)
                    .graphicsLayer {
                        rotationY = animatedAngle
                        cameraDistance = 12 * density
                    }
            ) {
                // Placa ornamental con emblema + género
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(selectedStyle.accentColor.copy(alpha = 0.16f))
                        .border(1.dp, selectedStyle.accentColor.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                        .padding(vertical = 8.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${selectedStyle.emblem}  ${selectedStyle.title.uppercase()}  ${selectedStyle.emblem}",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = selectedStyle.accentColor,
                        letterSpacing = 2.sp
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Título + parte
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = book.title.uppercase(),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = selectedStyle.accentColor,
                        maxLines = 1,
                        modifier = Modifier.weight(1f, fill = false)
                    )
                    Text(
                        text = "Parte ${currentPartIndex + 1} / ${book.partsCount}",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = selectedStyle.accentColor
                    )
                }

                // Filete decorativo
                Spacer(modifier = Modifier.height(8.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(2.dp)
                        .background(Brush.horizontalGradient(
                            listOf(Color.Transparent, selectedStyle.accentColor, Color.Transparent)))
                )
                Spacer(modifier = Modifier.height(16.dp))

                val bookPadding = when {
            !frames3dOn   -> PaddingValues(0.dp)
            showControls  -> PaddingValues(start = 8.dp, end = 8.dp, top = 2.dp, bottom = 26.dp)
            else          -> PaddingValues(horizontal = 30.dp, vertical = 38.dp)
        }
        Box(modifier = Modifier.weight(1f).fillMaxWidth().padding(bookPadding)) {
                    if (isTextLoading) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                CircularProgressIndicator(color = selectedStyle.accentColor, modifier = Modifier.size(32.dp))
                                Spacer(Modifier.height(12.dp))
                                Text("Cargando texto...", fontSize = 13.sp,
                                    color = selectedStyle.textColor.copy(alpha = 0.6f), textAlign = TextAlign.Center)
                            }
                        }
                    } else {
                        ReadingText(
                            text = textPart,
                            timings = wordTimings,
                            currentPositionMs = currentPositionMs,
                            highlightOn = highlightOn,
                            accent = selectedStyle.accentColor,
                            textColor = selectedStyle.textColor,
                            fontSizeSp = fontSizeSp,
                            fontFamily = activeFont,
                            onSeekTo = onSeekTo
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))
                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    Text("❧ ${currentPartIndex + 1} ❧", fontSize = 12.sp,
                        color = selectedStyle.accentColor, fontWeight = FontWeight.Bold)
                }
            }

            // Marco ILUSTRADO por género (drop-in): si existe res/drawable/frame_<genero>
            // se superpone (PNG con centro transparente, sobre el texto); si no existe,
            // se mantiene el marco animado actual. Los PNG son la "segunda tanda".

            // Navegación
            IconButton(
                onClick = { PageTurnSound.play(ctx); flipAngle = -30f; onPreviousPart(); flipAngle = 0f },
                modifier = Modifier.align(Alignment.CenterStart).padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateBefore, contentDescription = "Página anterior", tint = selectedStyle.textColor)
            }
            IconButton(
                onClick = { PageTurnSound.play(ctx); flipAngle = 30f; onNextPart(); flipAngle = 0f },
                modifier = Modifier.align(Alignment.CenterEnd).padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateNext, contentDescription = "Siguiente página", tint = selectedStyle.textColor)
            }
        }   // fin del marco base

            // Marco ILUSTRADO por género, por ENCIMA del marco base y sin
            // recortar: se escala para que su hueco transparente coincida
            // exactamente con el borde exterior del marco base, así la
            // decoración (espada, hiedra, lupa…) queda por fuera.
            if (frames3dOn) {
                GenreFrame3d(style = selectedStyle)
            }
        }   // fin del contenedor sin recorte
    }
}

/** Proporciones del hueco transparente de cada marco, medidas sobre el PNG. */
private data class FrameWindow(val x: Float, val y: Float, val w: Float, val h: Float)
private data class FrameKey(val style: BookBindingStyle, val wide: Boolean)

private val FRAME_WINDOWS: Map<FrameKey, FrameWindow> = mapOf(
    FrameKey(BookBindingStyle.CLASSIC, false)    to FrameWindow(0.1641f, 0.1372f, 0.6713f, 0.7176f),
    FrameKey(BookBindingStyle.CLASSIC, true)     to FrameWindow(0.1498f, 0.1901f, 0.7004f, 0.6204f),
    FrameKey(BookBindingStyle.MEDIEVAL, false)   to FrameWindow(0.1512f, 0.1427f, 0.6970f, 0.7197f),
    FrameKey(BookBindingStyle.MEDIEVAL, true)    to FrameWindow(0.1945f, 0.1914f, 0.6117f, 0.6172f),
    FrameKey(BookBindingStyle.SPIRITUAL, false)  to FrameWindow(0.2584f, 0.2167f, 0.4821f, 0.5661f),
    FrameKey(BookBindingStyle.SPIRITUAL, true)   to FrameWindow(0.1747f, 0.2174f, 0.6590f, 0.5651f),
    FrameKey(BookBindingStyle.WAR, false)        to FrameWindow(0.1518f, 0.1364f, 0.6964f, 0.6741f),
    FrameKey(BookBindingStyle.WAR, true)         to FrameWindow(0.1509f, 0.1895f, 0.6985f, 0.6211f),
    FrameKey(BookBindingStyle.LOVE, false)       to FrameWindow(0.1886f, 0.1598f, 0.6217f, 0.6791f),
    FrameKey(BookBindingStyle.LOVE, true)        to FrameWindow(0.1656f, 0.2005f, 0.6769f, 0.6100f),
    FrameKey(BookBindingStyle.PARANORMAL, false) to FrameWindow(0.1914f, 0.1431f, 0.6177f, 0.6925f),
    FrameKey(BookBindingStyle.PARANORMAL, true)  to FrameWindow(0.1927f, 0.2298f, 0.6300f, 0.5462f),
    FrameKey(BookBindingStyle.SCIENTIFIC, false) to FrameWindow(0.1953f, 0.1858f, 0.6088f, 0.6279f),
    FrameKey(BookBindingStyle.SCIENTIFIC, true)  to FrameWindow(0.1509f, 0.1901f, 0.6989f, 0.6204f),
    FrameKey(BookBindingStyle.COMEDY, false)     to FrameWindow(0.2065f, 0.1674f, 0.5865f, 0.6690f),
    FrameKey(BookBindingStyle.COMEDY, true)      to FrameWindow(0.2385f, 0.2461f, 0.5315f, 0.5078f),
    FrameKey(BookBindingStyle.FANTASY, false)    to FrameWindow(0.2567f, 0.2167f, 0.4877f, 0.5669f),
    FrameKey(BookBindingStyle.FANTASY, true)     to FrameWindow(0.1897f, 0.2279f, 0.6168f, 0.5449f)
)

/**
 * Dibuja el marco ilustrado del género escalado de modo que su hueco
 * transparente cubra EXACTAMENTE el área del contenedor (el marco base).
 * El resto de la imagen —la decoración— se sale por fuera, sin recorte.
 * Es proporcional, así que se adapta solo a móvil, tablet y pantalla completa.
 */
@Composable
private fun BoxScope.GenreFrame3d(style: BookBindingStyle) {
    val ctx = LocalContext.current
    BoxWithConstraints(modifier = Modifier.matchParentSize()) {
        val wide = maxWidth > maxHeight
        val res = remember(style, wide) { genreFrameImage(ctx, style, wide) }
        val win = FRAME_WINDOWS[FrameKey(style, wide)]
        if (res != 0 && win != null) {
            // La imagen se dibuja del tamaño del contenedor y luego se ESCALA
            // desde un punto fijo elegido para que el hueco caiga exactamente
            // sobre el contenedor. Escala = 1/tamañoDelHueco; el origen que deja
            // el hueco centrado es  x / (1 - ancho)  (misma fórmula en vertical).
            Image(
                painter = painterResource(res),
                contentDescription = null,
                contentScale = ContentScale.FillBounds,
                modifier = Modifier
                    .matchParentSize()
                    .graphicsLayer {
                        scaleX = 1f / win.w
                        scaleY = 1f / win.h
                        transformOrigin = TransformOrigin(
                            pivotFractionX = win.x / (1f - win.w),
                            pivotFractionY = win.y / (1f - win.h)
                        )
                        clip = false
                    }
            )
        }
    }
}

// ── Texto de lectura con resaltado sincronizado (karaoke) ──────────────────
private data class WordSpan(val start: Int, val end: Int, val timeStart: Long)

private fun buildWordSpans(text: String, timings: List<WordTiming>): List<WordSpan> {
    val out = ArrayList<WordSpan>(timings.size)
    var cursor = 0
    for (t in timings) {
        val w = t.w
        if (w.isBlank()) continue
        val idx = text.indexOf(w, cursor)
        if (idx >= 0) {
            out.add(WordSpan(idx, idx + w.length, t.s))
            cursor = idx + w.length
        }
    }
    return out
}

private fun currentSpanIndex(spans: List<WordSpan>, posMs: Long): Int {
    if (spans.isEmpty()) return -1
    var lo = 0; var hi = spans.size - 1; var ans = -1
    while (lo <= hi) {
        val m = (lo + hi) / 2
        if (spans[m].timeStart <= posMs) { ans = m; lo = m + 1 } else hi = m - 1
    }
    return ans
}

@Composable
private fun ReadingText(
    text: String,
    timings: List<WordTiming>,
    currentPositionMs: Long,
    highlightOn: Boolean,
    accent: Color,
    textColor: Color,
    fontSizeSp: Int,
    fontFamily: FontFamily,
    onSeekTo: (Long) -> Unit
) {
    if (text.isEmpty()) {
        Text(
            "Selecciona un libro y pulsa reproducir para ver el texto aquí.",
            fontSize = fontSizeSp.sp,
            fontFamily = fontFamily,
            color = textColor.copy(alpha = 0.7f)
        )
        return
    }

    // Sin karaoke (sin tiempos o desactivado): texto plano scrolleable
    if (timings.isEmpty() || !highlightOn) {
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            Text(
                text = text,
                fontSize = fontSizeSp.sp,
                fontFamily = fontFamily,
                lineHeight = (fontSizeSp * 1.6).sp,
                color = textColor,
                modifier = Modifier.fillMaxWidth()
            )
        }
        return
    }

    val spans = remember(text, timings) { buildWordSpans(text, timings) }
    val currentIndex = remember(spans, currentPositionMs) { currentSpanIndex(spans, currentPositionMs) }
    var layout by remember { mutableStateOf<TextLayoutResult?>(null) }
    val scroll = rememberScrollState()

    val annotated = remember(text, spans, currentIndex, accent, textColor) {
        buildAnnotatedString {
            append(text)
            if (currentIndex in spans.indices) {
                val sp = spans[currentIndex]
                addStyle(
                    SpanStyle(
                        background = accent.copy(alpha = 0.30f),
                        color = textColor,
                        fontWeight = FontWeight.Bold
                    ),
                    sp.start.coerceIn(0, text.length),
                    sp.end.coerceIn(0, text.length)
                )
            }
        }
    }

    // Auto-scroll: mantener la palabra actual visible
    LaunchedEffect(currentIndex) {
        val l = layout ?: return@LaunchedEffect
        if (currentIndex in spans.indices) {
            val cs = spans[currentIndex].start.coerceIn(0, (text.length - 1).coerceAtLeast(0))
            val line = l.getLineForOffset(cs)
            val top = l.getLineTop(line).toInt()
            scroll.animateScrollTo((top - 160).coerceAtLeast(0))
        }
    }

    Box(Modifier.fillMaxSize().verticalScroll(scroll)) {
        Text(
            text = annotated,
            fontSize = fontSizeSp.sp,
            fontFamily = fontFamily,
            lineHeight = (fontSizeSp * 1.6).sp,
            color = textColor,
            onTextLayout = { layout = it },
            modifier = Modifier
                .fillMaxWidth()
                .pointerInput(spans) {
                    detectTapGestures { pos ->
                        val l = layout ?: return@detectTapGestures
                        val off = l.getOffsetForPosition(pos)
                        val sp = spans.firstOrNull { off >= it.start && off < it.end }
                            ?: spans.lastOrNull { it.start <= off }
                        if (sp != null) onSeekTo(sp.timeStart)
                    }
                }
        )
    }
}

/**
 * Fuente por género. Las 12 .ttf artísticas ya están incluidas en res/font/
 * (Google Fonts vía Fontsource): EB Garamond, MedievalSharp, Cormorant, Oswald,
 * Dancing Script, Creepster, JetBrains Mono, Comic Neue, Uncial Antiqua,
 * Playfair Display, Special Elite, Orbitron. Si por alguna razón faltara alguna,
 * cae con elegancia a una familia integrada de Android.
 */
private fun resolveGenreFont(ctx: android.content.Context, style: BookBindingStyle): FontFamily {
    val (name, fallback) = when (style) {
        BookBindingStyle.CLASSIC    -> "eb_garamond"    to FontFamily.Serif
        BookBindingStyle.MEDIEVAL   -> "medievalsharp"  to FontFamily.Serif
        BookBindingStyle.SPIRITUAL  -> "cormorant"      to FontFamily.Serif
        BookBindingStyle.WAR        -> "oswald"         to FontFamily.SansSerif
        BookBindingStyle.LOVE       -> "dancing_script" to FontFamily.Cursive
        BookBindingStyle.PARANORMAL -> "creepster"      to FontFamily.Serif
        BookBindingStyle.SCIENTIFIC -> "jetbrains_mono" to FontFamily.Monospace
        BookBindingStyle.COMEDY     -> "comic_neue"     to FontFamily.SansSerif
        BookBindingStyle.FANTASY    -> "uncial_antiqua" to FontFamily.Serif
        BookBindingStyle.POETRY     -> "playfair"       to FontFamily.Serif
        BookBindingStyle.NOIR       -> "special_elite"  to FontFamily.Monospace
        BookBindingStyle.COSMIC     -> "orbitron"       to FontFamily.SansSerif
    }
    // Resolver universal alineado con DIRECTIVA_FUENTES_ARTISTICAS_EMBEBIDAS
    return com.librisaudio.app.util.ArtisticFonts.resolve(ctx, name, fallback)
}

/**
 * Marco ILUSTRADO por género (drop-in, "2ª tanda"). Resuelve un PNG opcional en
 * res/drawable/frame_<genero> con centro transparente. Si existe, se superpone al
 * marco; si no, devuelve 0 y se mantiene el marco animado actual (fallback).
 * Ver MARCOS_ILUSTRADOS_SPEC.md. Añadir marcos = soltar los PNG, sin tocar código.
 */
private fun genreFrameImage(
    ctx: android.content.Context,
    style: BookBindingStyle,
    wide: Boolean = false
): Int {
    val name = when (style) {
        BookBindingStyle.CLASSIC    -> "frame_classic"
        BookBindingStyle.MEDIEVAL   -> "frame_medieval"
        BookBindingStyle.SPIRITUAL  -> "frame_spiritual"
        BookBindingStyle.WAR        -> "frame_war"
        BookBindingStyle.LOVE       -> "frame_love"
        BookBindingStyle.PARANORMAL -> "frame_paranormal"
        BookBindingStyle.SCIENTIFIC -> "frame_scientific"
        BookBindingStyle.COMEDY     -> "frame_comedy"
        BookBindingStyle.FANTASY    -> "frame_fantasy"
        BookBindingStyle.POETRY     -> "frame_poetry"
        BookBindingStyle.NOIR       -> "frame_noir"
        BookBindingStyle.COSMIC     -> "frame_cosmic"
    }
    if (wide) {
        val landscape = ctx.resources.getIdentifier(name + "_wide", "drawable", ctx.packageName)
        if (landscape != 0) return landscape
    }
    return ctx.resources.getIdentifier(name, "drawable", ctx.packageName)
}

// Helpers para el degradado del borde que se desplaza (shimmer)
private fun Offset0(t: Float) = androidx.compose.ui.geometry.Offset(t * 300f, 0f)
private fun Offset1(t: Float) = androidx.compose.ui.geometry.Offset(300f + t * 300f, 600f)

/** Chip de la barra de herramientas del lector. */
@Composable
private fun ToolChip(label: String, active: Boolean, accent: Color, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (active) accent else Color(0x33FFFFFF))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 6.dp)
    ) {
        Text(label, fontSize = 10.sp, fontWeight = FontWeight.Bold,
            color = if (active) Color.White else Color(0xFF94A3B8))
    }
}

package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
    modifier: Modifier = Modifier
) {
    var selectedStyle by remember { mutableStateOf(BookBindingStyle.CLASSIC) }
    var fontSizeSp by remember { mutableStateOf(16) }
    var isSerifFont by remember { mutableStateOf(true) }
    var highlightOn by remember { mutableStateOf(true) }

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
        // Toolbar: estilos (scroll horizontal) + fuente
        Column(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
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
            Spacer(Modifier.height(6.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Resaltado sincronizado (karaoke) on/off
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(if (highlightOn) selectedStyle.accentColor else Color(0x33FFFFFF))
                        .clickable { highlightOn = !highlightOn }
                        .padding(horizontal = 8.dp, vertical = 5.dp)
                ) {
                    Text("✨ Sync", fontSize = 10.sp, fontWeight = FontWeight.Bold,
                        color = if (highlightOn) Color.White else Color(0xFF94A3B8))
                }
                Spacer(Modifier.width(6.dp))
                IconButton(onClick = { if (fontSizeSp > 12) fontSizeSp -= 2 }) {
                    Text("A-", fontSize = 12.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { if (fontSizeSp < 26) fontSizeSp += 2 }) {
                    Text("A+", fontSize = 14.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { isSerifFont = !isSerifFont }) {
                    Text(if (isSerifFont) "Serif" else "Sans", fontSize = 11.sp, color = Color.White)
                }
            }
        }

        // Marco 3D del libro
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
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

                Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
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
                            isSerif = isSerifFont,
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

            // Navegación
            IconButton(
                onClick = { flipAngle = -30f; onPreviousPart(); flipAngle = 0f },
                modifier = Modifier.align(Alignment.CenterStart).padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateBefore, contentDescription = "Página anterior", tint = selectedStyle.textColor)
            }
            IconButton(
                onClick = { flipAngle = 30f; onNextPart(); flipAngle = 0f },
                modifier = Modifier.align(Alignment.CenterEnd).padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateNext, contentDescription = "Siguiente página", tint = selectedStyle.textColor)
            }
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
    isSerif: Boolean,
    onSeekTo: (Long) -> Unit
) {
    if (text.isEmpty()) {
        Text(
            "Selecciona un libro y pulsa reproducir para ver el texto aquí.",
            fontSize = fontSizeSp.sp,
            fontFamily = if (isSerif) FontFamily.Serif else FontFamily.Default,
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
                fontFamily = if (isSerif) FontFamily.Serif else FontFamily.Default,
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
            fontFamily = if (isSerif) FontFamily.Serif else FontFamily.Default,
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

// Helpers para el degradado del borde que se desplaza (shimmer)
private fun Offset0(t: Float) = androidx.compose.ui.geometry.Offset(t * 300f, 0f)
private fun Offset1(t: Float) = androidx.compose.ui.geometry.Offset(300f + t * 300f, 600f)

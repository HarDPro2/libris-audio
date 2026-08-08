package com.librisaudio.app.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.runtime.LaunchedEffect
import kotlinx.coroutines.delay
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Bedtime
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Fullscreen
import androidx.compose.material.icons.filled.FullscreenExit
import androidx.compose.material.icons.filled.Headphones
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material.icons.filled.StopCircle
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.QueryStats
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.SkipPrevious
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.data.model.MusicTrack
import com.librisaudio.app.data.model.WordTiming
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.components.AudioVisualizer
import com.librisaudio.app.ui.components.BookmarkDialog
import com.librisaudio.app.ui.components.BookmarkItem
import com.librisaudio.app.ui.components.ChatWithBookDialog
import com.librisaudio.app.ui.components.MusicSelectorDialog
import com.librisaudio.app.ui.components.SleepTimerDialog
import com.librisaudio.app.ui.components.StatsDialog
import com.librisaudio.app.ui.components.SleepTimerOption
import com.librisaudio.app.ui.components.VirtualBookFrame
import com.librisaudio.app.ui.components.VoiceSelectorDialog
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted

enum class PlayerViewMode {
    CLASSIC_PLAYER,   // solo audio
    VIRTUAL_BOOK_3D,  // audio + texto con karaoke
    READ_ONLY         // solo lectura, sin voz
}

@Composable
fun PlayerScreen(
    book: Book,
    isPlaying: Boolean,
    currentPartIndex: Int,
    playbackSpeed: Float,
    currentPositionMs: Long,
    durationMs: Long,
    currentTheme: AppThemePreset,
    selectedMusicTrack: MusicTrack?,
    backgroundVolume: Float,
    currentPartText: String = "",
    isTextLoading: Boolean = false,
    onSelectMusicTrack: (MusicTrack?) -> Unit,
    onBackgroundVolumeChange: (Float) -> Unit,
    onTogglePlay: () -> Unit,
    onNextPart: () -> Unit,
    onPreviousPart: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSelectSpeed: (Float) -> Unit,
    onOpenCarMode: () -> Unit,
    onClose: () -> Unit,
    todayMinutes: Int = 0,
    streakDays: Int = 0,
    totalHours: Double = 0.0,
    selectedVoice: String = "es-MX-JorgeNeural",
    onSelectVoice: (String) -> Unit = {},
    wordTimings: List<WordTiming> = emptyList(),
    onStopPlayback: () -> Unit = {},
    onReadNextPart: () -> Unit = {},
    onReadPreviousPart: () -> Unit = {},
    onPauseVoice: () -> Unit = {},
    bookmarks: List<BookmarkItem> = emptyList(),
    onAddBookmark: (String, Int, Long, String) -> Unit = { _, _, _, _ -> },
    modifier: Modifier = Modifier
) {
    var viewMode by remember { mutableStateOf(PlayerViewMode.CLASSIC_PLAYER) }
    var isImmersive by remember { mutableStateOf(false) }
    var isMusicDialogVisible by remember { mutableStateOf(false) }
    var isSleepTimerVisible by remember { mutableStateOf(false) }
    var isBookmarkVisible by remember { mutableStateOf(false) }
    var isAiChatVisible by remember { mutableStateOf(false) }
    var isStatsVisible by remember { mutableStateOf(false) }
    var isVoiceDialogVisible by remember { mutableStateOf(false) }

    var selectedSleepTimer by remember { mutableStateOf(SleepTimerOption.OFF) }
    var sleepTimerSeconds by remember { mutableStateOf(0L) }

    // ── Sleep Timer countdown ──────────────────────────────────────────────
    LaunchedEffect(sleepTimerSeconds, isPlaying) {
        if (sleepTimerSeconds > 0 && isPlaying) {
            delay(1000L)
            sleepTimerSeconds -= 1
            if (sleepTimerSeconds == 0L) {
                onTogglePlay() // pause audio when timer reaches zero
                selectedSleepTimer = SleepTimerOption.OFF
            }
        } else if (selectedSleepTimer == SleepTimerOption.END_OF_PART) {
            // END_OF_PART: handled via onPartEnded — no countdown needed here
        }
    }

    val speeds = listOf(1.0f, 1.25f, 1.5f, 1.75f, 2.0f)

    val infiniteTransition = rememberInfiniteTransition(label = "AuraPulse")
    val auraGlow by infiniteTransition.animateFloat(
        initialValue = 2.dp.value,
        targetValue = if (isPlaying) 8.dp.value else 2.dp.value,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "Aura"
    )

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Top Navigation Bar (dos filas: controles+modos arriba, acciones abajo)
            if (!isImmersive) Column(modifier = Modifier.fillMaxWidth()) {
              Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
              ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onClose) {
                        Icon(Icons.Default.Home, contentDescription = "Inicio", tint = Color.White)
                    }
                    IconButton(onClick = onStopPlayback) {
                        Icon(Icons.Default.StopCircle, contentDescription = "Detener reproducción", tint = Color.White)
                    }
                }

                // View Mode Switcher Pills (Cl�sico vs Libro 3D)
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(16.dp))
                        .background(CardSurface)
                        .padding(4.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (viewMode == PlayerViewMode.CLASSIC_PLAYER) currentTheme.primary else Color.Transparent)
                            .clickable { viewMode = PlayerViewMode.CLASSIC_PLAYER }
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Headphones, contentDescription = null, tint = Color.White, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Clásico", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }

                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (viewMode == PlayerViewMode.VIRTUAL_BOOK_3D) currentTheme.primary else Color.Transparent)
                            .clickable { viewMode = PlayerViewMode.VIRTUAL_BOOK_3D }
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Book, contentDescription = null, tint = Color.White, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Libro", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }

                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (viewMode == PlayerViewMode.READ_ONLY) currentTheme.primary else Color.Transparent)
                            .clickable { viewMode = PlayerViewMode.READ_ONLY; onPauseVoice() }
                            .padding(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.MenuBook, contentDescription = null, tint = Color.White, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Leer", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }

                // Pantalla completa (cierra la fila superior)
                IconButton(onClick = { isImmersive = true }) {
                    Icon(Icons.Default.Fullscreen, contentDescription = "Pantalla completa", tint = CyanAccent)
                }
              }

              Spacer(modifier = Modifier.height(4.dp))

              // Segunda fila: TODAS las acciones visibles, sin scroll
              Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
              ) {
                    IconButton(onClick = { isVoiceDialogVisible = true }) {
                        Icon(Icons.Default.RecordVoiceOver, contentDescription = "Voz del narrador", tint = Color.White)
                    }
                    IconButton(onClick = { isStatsVisible = true }) {
                        Icon(Icons.Default.QueryStats, contentDescription = "Estadísticas", tint = Color.White)
                    }
                    IconButton(onClick = { isAiChatVisible = true }) {
                        Icon(Icons.Default.AutoAwesome, contentDescription = "Preguntale a la IA", tint = CyanAccent)
                    }
                    IconButton(onClick = onOpenCarMode) {
                        Icon(Icons.Default.DirectionsCar, contentDescription = "Modo Auto", tint = Color.White)
                    }
                    IconButton(onClick = { isSleepTimerVisible = true }) {
                        Icon(Icons.Default.Bedtime, contentDescription = "Sleep Timer", tint = if (selectedSleepTimer != SleepTimerOption.OFF) CyanAccent else Color.White)
                    }
                    IconButton(onClick = { isBookmarkVisible = true }) {
                        Icon(Icons.Default.Bookmark, contentDescription = "Marcapáginas", tint = Color.White)
                    }
                    IconButton(onClick = { isMusicDialogVisible = true }) {
                        Icon(Icons.Default.MusicNote, contentDescription = "Música de Fondo", tint = if (selectedMusicTrack != null) CyanAccent else Color.White)
                    }
              }
            }

            Spacer(modifier = Modifier.height(8.dp))

            if (viewMode != PlayerViewMode.CLASSIC_PLAYER) {
                // Modo lectura: Libro (con audio+karaoke) o Solo Lectura (sin voz)
                val readOnly = viewMode == PlayerViewMode.READ_ONLY
                VirtualBookFrame(
                    book = book,
                    textPart = currentPartText,
                    isTextLoading = isTextLoading,
                    currentPartIndex = currentPartIndex,
                    isPlaying = isPlaying,
                    currentPositionMs = currentPositionMs,
                    wordTimings = if (readOnly) emptyList() else wordTimings,
                    onSeekTo = onSeekTo,
                    onNextPart = if (readOnly) onReadNextPart else onNextPart,
                    onPreviousPart = if (readOnly) onReadPreviousPart else onPreviousPart,
                    modifier = Modifier.weight(1f)
                )
            } else {
                // Classic Player Mode
                Column(
                    modifier = Modifier.weight(1f),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        modifier = Modifier
                            .size(200.dp)
                            .clip(RoundedCornerShape(24.dp))
                            .border(
                                width = auraGlow.dp,
                                brush = Brush.linearGradient(
                                    colors = listOf(currentTheme.primary, currentTheme.secondary)
                                ),
                                shape = RoundedCornerShape(24.dp)
                            )
                            .background(Color(0xFF334155))
                    ) {
                        if (!book.coverUrl.isNullOrEmpty()) {
                            AsyncImage(
                                model = book.coverUrl,
                                contentDescription = book.title,
                                contentScale = ContentScale.Crop,
                                modifier = Modifier.fillMaxSize()
                            )
                        } else {
                            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                Text("??", fontSize = 60.sp)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    AudioVisualizer(
                        isPlaying = isPlaying,
                        primaryColor = currentTheme.primary,
                        secondaryColor = currentTheme.secondary,
                        modifier = Modifier.padding(horizontal = 24.dp)
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = book.title,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "Parte ${currentPartIndex + 1} de ${book.partsCount}",
                        fontSize = 13.sp,
                        color = currentTheme.secondary,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Bottom Audio Control Panel (oculto en Solo Lectura — no hay voz)
            if (!isImmersive && viewMode != PlayerViewMode.READ_ONLY) Column(modifier = Modifier.fillMaxWidth()) {
                val posSec = currentPositionMs / 1000
                val durSec = durationMs / 1000
                val sliderValue = if (durationMs > 0) currentPositionMs.toFloat() / durationMs else 0f

                Slider(
                    value = sliderValue.coerceIn(0f, 1f),
                    onValueChange = { fraction ->
                        if (durationMs > 0) {
                            onSeekTo((fraction * durationMs).toLong())
                        }
                    },
                    colors = SliderDefaults.colors(
                        thumbColor = currentTheme.primary,
                        activeTrackColor = currentTheme.primary,
                        inactiveTrackColor = Color(0x44FFFFFF)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(formatTime(posSec), fontSize = 12.sp, color = TextMuted)
                    Text(formatTime(durSec), fontSize = 12.sp, color = TextMuted)
                }

                Spacer(modifier = Modifier.height(6.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    IconButton(onClick = onPreviousPart, modifier = Modifier.size(44.dp)) {
                        Icon(Icons.Default.SkipPrevious, contentDescription = "Parte Anterior", tint = Color.White, modifier = Modifier.size(32.dp))
                    }

                    Spacer(modifier = Modifier.width(20.dp))

                    IconButton(
                        onClick = onTogglePlay,
                        modifier = Modifier
                            .size(60.dp)
                            .clip(RoundedCornerShape(30.dp))
                            .background(
                                Brush.linearGradient(
                                    colors = listOf(currentTheme.primary, currentTheme.secondary)
                                )
                            )
                    ) {
                        Icon(
                            imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                            contentDescription = if (isPlaying) "Pausar" else "Reproducir",
                            tint = Color.White,
                            modifier = Modifier.size(36.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(20.dp))

                    IconButton(onClick = onNextPart, modifier = Modifier.size(44.dp)) {
                        Icon(Icons.Default.SkipNext, contentDescription = "Siguiente Parte", tint = Color.White, modifier = Modifier.size(32.dp))
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    speeds.forEach { speed ->
                        val isSelected = playbackSpeed == speed
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(10.dp))
                                .background(if (isSelected) currentTheme.primary else Color(0x331E293B))
                                .clickable { onSelectSpeed(speed) }
                                .padding(vertical = 6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "${speed}x",
                                fontSize = 11.sp,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                color = if (isSelected) Color.White else TextMuted
                            )
                        }
                    }
                }
            }
        }

        // Controles flotantes en modo inmersivo (pantalla completa)
        if (isImmersive) {
            IconButton(
                onClick = { isImmersive = false },
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(12.dp)
                    .clip(RoundedCornerShape(20.dp))
                    .background(Color(0x66000000))
            ) {
                Icon(Icons.Default.FullscreenExit, contentDescription = "Salir de pantalla completa", tint = Color.White)
            }
            IconButton(
                onClick = { isMusicDialogVisible = true },
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(12.dp)
                    .clip(RoundedCornerShape(20.dp))
                    .background(Color(0x66000000))
            ) {
                Icon(Icons.Default.MusicNote, contentDescription = "Música de fondo",
                    tint = if (selectedMusicTrack != null) CyanAccent else Color.White)
            }
            Row(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(18.dp)
            ) {
                IconButton(onClick = onPreviousPart) {
                    Icon(Icons.Default.SkipPrevious, contentDescription = "Anterior", tint = Color.White, modifier = Modifier.size(30.dp))
                }
                IconButton(
                    onClick = onTogglePlay,
                    modifier = Modifier
                        .size(56.dp)
                        .clip(RoundedCornerShape(28.dp))
                        .background(Brush.linearGradient(listOf(currentTheme.primary, currentTheme.secondary)))
                ) {
                    Icon(
                        imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = if (isPlaying) "Pausar" else "Reproducir",
                        tint = Color.White, modifier = Modifier.size(32.dp)
                    )
                }
                IconButton(onClick = onNextPart) {
                    Icon(Icons.Default.SkipNext, contentDescription = "Siguiente", tint = Color.White, modifier = Modifier.size(30.dp))
                }
            }
        }

        // Dialogs
        if (isVoiceDialogVisible) {
            VoiceSelectorDialog(
                selectedVoiceId = selectedVoice,
                onSelectVoice = onSelectVoice,
                onDismiss = { isVoiceDialogVisible = false }
            )
        }

        if (isStatsVisible) {
            StatsDialog(
                todayMinutes = todayMinutes,
                streakDays = streakDays,
                totalHours = totalHours,
                onDismiss = { isStatsVisible = false }
            )
        }

        if (isAiChatVisible) {
            ChatWithBookDialog(
                bookId = book.bookId,
                currentPartIndex = currentPartIndex,
                onDismiss = { isAiChatVisible = false }
            )
        }

        if (isMusicDialogVisible) {
            MusicSelectorDialog(
                selectedTrack = selectedMusicTrack,
                backgroundVolume = backgroundVolume,
                onSelectTrack = { track -> onSelectMusicTrack(track) },
                onVolumeChange = onBackgroundVolumeChange,
                onDismiss = { isMusicDialogVisible = false }
            )
        }

        if (isSleepTimerVisible) {
            SleepTimerDialog(
                selectedOption = selectedSleepTimer,
                remainingSeconds = sleepTimerSeconds,
                onSelectOption = { option ->
                    selectedSleepTimer = option
                    sleepTimerSeconds = when {
                        option == SleepTimerOption.OFF          -> 0L
                        option == SleepTimerOption.END_OF_PART  -> -1L // special marker
                        option.minutes > 0                       -> option.minutes * 60L
                        else                                     -> 0L
                    }
                    isSleepTimerVisible = false
                },
                onDismiss = { isSleepTimerVisible = false }
            )
        }

        if (isBookmarkVisible) {
            BookmarkDialog(
                bookTitle = book.title,
                currentPartIndex = currentPartIndex,
                currentPositionMs = currentPositionMs,
                bookmarks = bookmarks,
                onAddBookmark = { note ->
                    onAddBookmark(book.bookId, currentPartIndex, currentPositionMs, note)
                },
                onJumpToBookmark = { item ->
                    onSeekTo(item.positionMs)
                    isBookmarkVisible = false
                },
                onDismiss = { isBookmarkVisible = false }
            )
        }
    }
}

private fun formatTime(seconds: Long): String {
    val m = seconds / 60
    val s = seconds % 60
    return String.format("%02d:%02d", m, s)
}

package com.librisaudio.app.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Headphones
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
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
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.components.AudioVisualizer
import com.librisaudio.app.ui.components.MusicSelectorDialog
import com.librisaudio.app.ui.components.VirtualBookFrame
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted

enum class PlayerViewMode {
    CLASSIC_PLAYER,
    VIRTUAL_BOOK_3D
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
    onSelectMusicTrack: (MusicTrack?) -> Unit,
    onBackgroundVolumeChange: (Float) -> Unit,
    onTogglePlay: () -> Unit,
    onNextPart: () -> Unit,
    onPreviousPart: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSelectSpeed: (Float) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    var viewMode by remember { mutableStateOf(PlayerViewMode.CLASSIC_PLAYER) }
    var isMusicDialogVisible by remember { mutableStateOf(false) }
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
            // Top Navigation Bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onClose) {
                    Icon(Icons.Default.Close, contentDescription = "Cerrar", tint = Color.White)
                }

                // View Mode Switcher Pills (Clásico vs Libro 3D)
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
                            Text("Libro 3D", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }

                // Background Music Button
                IconButton(onClick = { isMusicDialogVisible = true }) {
                    Icon(
                        imageVector = Icons.Default.MusicNote,
                        contentDescription = "Música de Fondo",
                        tint = if (selectedMusicTrack != null) CyanAccent else Color.White
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (viewMode == PlayerViewMode.VIRTUAL_BOOK_3D) {
                // 3D Virtual Book Frame Mode
                VirtualBookFrame(
                    book = book,
                    textPart = "", // Text part content loaded natively
                    currentPartIndex = currentPartIndex,
                    isPlaying = isPlaying,
                    onNextPart = onNextPart,
                    onPreviousPart = onPreviousPart,
                    modifier = Modifier.weight(1f)
                )
            } else {
                // Classic Player Mode
                Column(
                    modifier = Modifier.weight(1f),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    // Large Cover Image with Glowing Neon Pulse Aura
                    Box(
                        modifier = Modifier
                            .size(220.dp)
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
                                Text("??", fontSize = 64.sp)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Audio Visualizer Spectrum Bar Graph
                    AudioVisualizer(
                        isPlaying = isPlaying,
                        primaryColor = currentTheme.primary,
                        secondaryColor = currentTheme.secondary,
                        modifier = Modifier.padding(horizontal = 24.dp)
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = book.title,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Parte ${currentPartIndex + 1} de ${book.partsCount}",
                        fontSize = 13.sp,
                        color = currentTheme.secondary,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Bottom Audio Control Panel (Shared across views)
            Column(modifier = Modifier.fillMaxWidth()) {
                // Progress Slider & Timers
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

                Spacer(modifier = Modifier.height(8.dp))

                // Main Playback Buttons
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
                            .size(64.dp)
                            .clip(RoundedCornerShape(32.dp))
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

                Spacer(modifier = Modifier.height(12.dp))

                // Speed Selector Pills
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

        // Classical Background Music Selector Dialog
        if (isMusicDialogVisible) {
            MusicSelectorDialog(
                selectedTrack = selectedMusicTrack,
                backgroundVolume = backgroundVolume,
                onSelectTrack = { track -> onSelectMusicTrack(track) },
                onVolumeChange = onBackgroundVolumeChange,
                onDismiss = { isMusicDialogVisible = false }
            )
        }
    }
}

private fun formatTime(seconds: Long): String {
    val m = seconds / 60
    val s = seconds % 60
    return String.format("%02d:%02d", m, s)
}

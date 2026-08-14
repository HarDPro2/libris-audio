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
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.DownloadDone
import androidx.compose.material.icons.filled.Fullscreen
import androidx.compose.material.icons.filled.FullscreenExit
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.Headphones
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material.icons.filled.StopCircle
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.QueryStats
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.SkipPrevious
import androidx.compose.material3.*
import androidx.compose.ui.res.stringResource
import com.librisaudio.app.R
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
    musicaAleatoria: Boolean = false,
    onToggleMusicaAleatoria: (Boolean) -> Unit = {},
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
    frames3dEnabled: Boolean = false,
    onToggleFrames3d: (Boolean) -> Unit = {},
    onPauseVoice: () -> Unit = {},
    bookmarks: List<BookmarkItem> = emptyList(),
    onAddBookmark: (String, Int, Long, String) -> Unit = { _, _, _, _ -> },
    isDownloaded: Boolean = false,
    isDownloading: Boolean = false,
    downloadProgress: Int = 0,
    onDownload: () -> Unit = {},
    onVoice: (String) -> Unit = {},
    onVoiceHandsFree: (String) -> Unit = {},
    voiceProcessing: Boolean = false,
    voiceMessage: String? = null,
    onClearVoiceMessage: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    var viewMode by remember { mutableStateOf(PlayerViewMode.CLASSIC_PLAYER) }
    var isImmersive by remember { mutableStateOf(false) }

    // Mantener la pantalla encendida (para leer/karaoke sin tocarla). Persistido.
    val screenCtx = androidx.compose.ui.platform.LocalContext.current
    val currentView = androidx.compose.ui.platform.LocalView.current
    val keepPrefs = remember { screenCtx.getSharedPreferences("libris_prefs", android.content.Context.MODE_PRIVATE) }
    var keepScreenOn by remember { mutableStateOf(keepPrefs.getBoolean("keep_screen_on", false)) }
    androidx.compose.runtime.DisposableEffect(keepScreenOn) {
        currentView.keepScreenOn = keepScreenOn
        onDispose { currentView.keepScreenOn = false }
    }

    // ── Asistente de voz A1 (comandos on-device, gratis) ──
    val voiceMgr = remember { com.librisaudio.app.util.VoiceCommandManager(screenCtx) }
    var isListening by remember { mutableStateOf(false) }
    val voiceLang = remember { java.util.Locale.getDefault().language.ifBlank { "es" } }
    androidx.compose.runtime.DisposableEffect(Unit) { onDispose { voiceMgr.stop() } }

    fun runVoice() {
        if (!voiceMgr.isAvailable()) {
            android.widget.Toast.makeText(screenCtx, screenCtx.getString(R.string.voice_unavailable), android.widget.Toast.LENGTH_SHORT).show()
            return
        }
        isListening = true
        voiceMgr.listen(
            langTag = voiceLang,
            onResult = { text ->
                isListening = false
                onVoice(text)   // ejecuta A1 local o cae a A2 (LLM) en el ViewModel
            },
            onError = { isListening = false }
        )
    }

    val micPermLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) runVoice()
        else android.widget.Toast.makeText(screenCtx, screenCtx.getString(R.string.voice_perm_needed), android.widget.Toast.LENGTH_SHORT).show()
    }

    fun onMicClick() {
        val granted = androidx.core.content.ContextCompat.checkSelfPermission(
            screenCtx, android.Manifest.permission.RECORD_AUDIO
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        if (granted) runVoice() else micPermLauncher.launch(android.Manifest.permission.RECORD_AUDIO)
    }

    // Muestra el resultado del comando de voz (toast) y lo limpia
    LaunchedEffect(voiceMessage) {
        voiceMessage?.let {
            android.widget.Toast.makeText(screenCtx, it, android.widget.Toast.LENGTH_SHORT).show()
            onClearVoiceMessage()
        }
    }

    // ── A3: modo manos libres (escucha continua, solo gramática local) ──
    var handsFree by remember { mutableStateOf(false) }
    LaunchedEffect(handsFree) {
        while (handsFree) {
            val text = voiceMgr.listenOnce(voiceLang)
            if (!handsFree) break
            if (text.isNotBlank()) onVoiceHandsFree(text)
            kotlinx.coroutines.delay(600)
        }
    }
    fun onHandsFreeClick() {
        if (handsFree) {
            handsFree = false
            android.widget.Toast.makeText(screenCtx, screenCtx.getString(R.string.voice_handsfree_off), android.widget.Toast.LENGTH_SHORT).show()
            return
        }
        val granted = androidx.core.content.ContextCompat.checkSelfPermission(
            screenCtx, android.Manifest.permission.RECORD_AUDIO
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        if (granted) {
            handsFree = true
            android.widget.Toast.makeText(screenCtx, screenCtx.getString(R.string.voice_handsfree_on), android.widget.Toast.LENGTH_LONG).show()
        } else micPermLauncher.launch(android.Manifest.permission.RECORD_AUDIO)
    }

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

    // META 3.2 — hasta 4x. Media3 usa Sonic para el estiramiento temporal, que
    // conserva el tono, así que la voz no se agudiza al acelerar. Muy pedido
    // por estudiantes en época de exámenes.
    val speeds = listOf(1.0f, 1.25f, 1.5f, 1.75f, 2.0f, 2.5f, 3.0f, 4.0f)

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
                    TooltipIconButton(stringResource(R.string.player_home), onClick = onClose) {
                        Icon(Icons.Default.Home, contentDescription = stringResource(R.string.player_home), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_stop), onClick = onStopPlayback) {
                        Icon(Icons.Default.StopCircle, contentDescription = stringResource(R.string.player_stop), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.voice_cmd), onClick = { onMicClick() }) {
                        Icon(Icons.Default.Mic, contentDescription = stringResource(R.string.voice_cmd),
                            tint = if (isListening) CyanAccent else Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.voice_handsfree), onClick = { onHandsFreeClick() }) {
                        Icon(Icons.Default.GraphicEq, contentDescription = stringResource(R.string.voice_handsfree),
                            tint = if (handsFree) CyanAccent else Color.White)
                    }
                }

                // Pantalla completa (cierra la fila superior)
                TooltipIconButton(stringResource(R.string.player_fullscreen), onClick = { isImmersive = true }) {
                    Icon(Icons.Default.Fullscreen, contentDescription = stringResource(R.string.player_fullscreen), tint = CyanAccent)
                }
              }

              Spacer(modifier = Modifier.height(6.dp))

              // Selector de modo de vista — fila propia y centrada (evita el descuadre/overflow)
              Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
              ) {
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
                            Text(stringResource(R.string.player_mode_classic), fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White, maxLines = 1, softWrap = false)
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
                            Text(stringResource(R.string.player_mode_book), fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White, maxLines = 1, softWrap = false)
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
                            Text(stringResource(R.string.player_mode_read), fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White, maxLines = 1, softWrap = false)
                        }
                    }
                }
              }

              Spacer(modifier = Modifier.height(4.dp))

              // Segunda fila de acciones. Son 9 iconos y en pantallas estrechas
              // el ultimo (descargar) quedaba fuera: se hace desplazable.
              Row(
                modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
              ) {
                    TooltipIconButton(stringResource(R.string.player_voice), onClick = { isVoiceDialogVisible = true }) {
                        Icon(Icons.Default.RecordVoiceOver, contentDescription = stringResource(R.string.player_voice), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_stats), onClick = { isStatsVisible = true }) {
                        Icon(Icons.Default.QueryStats, contentDescription = stringResource(R.string.player_stats), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_ask_ai), onClick = { isAiChatVisible = true }) {
                        Icon(Icons.Default.AutoAwesome, contentDescription = stringResource(R.string.player_ask_ai), tint = CyanAccent)
                    }
                    TooltipIconButton(stringResource(R.string.player_car_mode), onClick = onOpenCarMode) {
                        Icon(Icons.Default.DirectionsCar, contentDescription = stringResource(R.string.player_car_mode), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_sleep_timer), onClick = { isSleepTimerVisible = true }) {
                        Icon(Icons.Default.Bedtime, contentDescription = stringResource(R.string.player_sleep_timer), tint = if (selectedSleepTimer != SleepTimerOption.OFF) CyanAccent else Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_bookmarks), onClick = { isBookmarkVisible = true }) {
                        Icon(Icons.Default.Bookmark, contentDescription = stringResource(R.string.player_bookmarks), tint = Color.White)
                    }
                    TooltipIconButton(stringResource(R.string.player_bg_music), onClick = { isMusicDialogVisible = true }) {
                        Icon(Icons.Default.MusicNote, contentDescription = stringResource(R.string.player_bg_music), tint = if (selectedMusicTrack != null || musicaAleatoria) CyanAccent else Color.White)
                    }
                    TooltipIconButton(
                        stringResource(R.string.player_keep_awake),
                        onClick = {
                            keepScreenOn = !keepScreenOn
                            keepPrefs.edit().putBoolean("keep_screen_on", keepScreenOn).apply()
                        }
                    ) {
                        Icon(Icons.Default.LightMode, contentDescription = stringResource(R.string.player_keep_awake),
                            tint = if (keepScreenOn) CyanAccent else Color.White)
                    }
                    TooltipIconButton(
                        label = stringResource(if (isDownloaded) R.string.player_downloaded else R.string.player_download),
                        onClick = { if (!isDownloading && !isDownloaded) onDownload() },
                        enabled = !isDownloading
                    ) {
                        when {
                            isDownloading -> CircularProgressIndicator(
                                progress = (downloadProgress / 100f).coerceIn(0f, 1f),
                                modifier = Modifier.size(22.dp),
                                strokeWidth = 2.dp,
                                color = CyanAccent
                            )
                            isDownloaded -> Icon(Icons.Default.DownloadDone, contentDescription = stringResource(R.string.player_downloaded), tint = CyanAccent)
                            else -> Icon(Icons.Default.Download, contentDescription = stringResource(R.string.player_download), tint = Color.White)
                        }
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
                    frames3dEnabled = frames3dEnabled,
                    onToggleFrames3d = onToggleFrames3d,
                    showControls = !isImmersive,
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
                        text = stringResource(R.string.player_part_of, currentPartIndex + 1, book.partsCount),
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
                        Icon(Icons.Default.SkipPrevious, contentDescription = stringResource(R.string.player_prev_part), tint = Color.White, modifier = Modifier.size(32.dp))
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
                            contentDescription = if (isPlaying) stringResource(R.string.player_pause) else stringResource(R.string.player_play),
                            tint = Color.White,
                            modifier = Modifier.size(36.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(20.dp))

                    IconButton(onClick = onNextPart, modifier = Modifier.size(44.dp)) {
                        Icon(Icons.Default.SkipNext, contentDescription = stringResource(R.string.player_next_part), tint = Color.White, modifier = Modifier.size(32.dp))
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Con 8 velocidades ya no caben repartiendo el ancho: la fila
                // se desplaza y cada chip ocupa lo que necesita. (weight(1f)
                // además es incompatible con una fila con scroll horizontal.)
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    speeds.forEach { speed ->
                        val isSelected = playbackSpeed == speed
                        Box(
                            modifier = Modifier
                                .widthIn(min = 52.dp)
                                .clip(RoundedCornerShape(10.dp))
                                .background(if (isSelected) currentTheme.primary else Color(0x331E293B))
                                .clickable { onSelectSpeed(speed) }
                                .padding(horizontal = 10.dp, vertical = 6.dp),
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
                Icon(Icons.Default.FullscreenExit, contentDescription = stringResource(R.string.player_exit_fullscreen), tint = Color.White)
            }
            IconButton(
                onClick = { isMusicDialogVisible = true },
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(12.dp)
                    .clip(RoundedCornerShape(20.dp))
                    .background(Color(0x66000000))
            ) {
                Icon(Icons.Default.MusicNote, contentDescription = stringResource(R.string.player_bg_music),
                    tint = if (selectedMusicTrack != null || musicaAleatoria) CyanAccent else Color.White)
            }
            Row(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(18.dp)
            ) {
                IconButton(onClick = onPreviousPart) {
                    Icon(Icons.Default.SkipPrevious, contentDescription = stringResource(R.string.player_previous), tint = Color.White, modifier = Modifier.size(30.dp))
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
                        contentDescription = if (isPlaying) stringResource(R.string.player_pause) else stringResource(R.string.player_play),
                        tint = Color.White, modifier = Modifier.size(32.dp)
                    )
                }
                IconButton(onClick = onNextPart) {
                    Icon(Icons.Default.SkipNext, contentDescription = stringResource(R.string.player_next), tint = Color.White, modifier = Modifier.size(30.dp))
                }
            }
        }

        // Overlay del asistente de voz (escuchando o pensando)
        if (isListening || voiceProcessing) {
            Box(
                modifier = Modifier.fillMaxSize().background(Color(0xCC000000)),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    if (voiceProcessing) {
                        CircularProgressIndicator(color = CyanAccent, modifier = Modifier.size(48.dp))
                    } else {
                        Icon(Icons.Default.Mic, contentDescription = null, tint = CyanAccent, modifier = Modifier.size(56.dp))
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        stringResource(if (voiceProcessing) R.string.voice_thinking else R.string.voice_listening),
                        color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold
                    )
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
                // META 3.7 — el selector se ordena segun el marco del libro abierto
                estiloGenero = com.librisaudio.app.data.model.GenreMusic.estiloPara(book),
                aleatorio = musicaAleatoria,
                onToggleAleatorio = onToggleMusicaAleatoria,
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

/** IconButton con nombre en tooltip al mantener pulsado (Material3). */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TooltipIconButton(
    label: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    content: @Composable () -> Unit
) {
    TooltipBox(
        positionProvider = TooltipDefaults.rememberPlainTooltipPositionProvider(),
        tooltip = { PlainTooltip { Text(label) } },
        state = rememberTooltipState()
    ) {
        IconButton(onClick = onClick, enabled = enabled) { content() }
    }
}

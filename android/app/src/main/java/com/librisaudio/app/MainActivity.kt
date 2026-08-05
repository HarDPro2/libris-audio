package com.librisaudio.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.activity.compose.setContent
import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.font.FontWeight
import com.librisaudio.app.data.model.MusicTrack
import com.librisaudio.app.ui.components.BottomPlayerBar
import com.librisaudio.app.ui.screens.*
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.LibrisAudioTheme
import com.librisaudio.app.viewmodel.AuthState
import com.librisaudio.app.viewmodel.AuthViewModel
import com.librisaudio.app.viewmodel.PlayerViewModel

enum class MainTab {
    LIBRARY, HISTORY, UPLOAD, SETTINGS
}

class MainActivity : ComponentActivity() {

    private val playerViewModel: PlayerViewModel by viewModels()
    private val authViewModel: AuthViewModel by viewModels()

    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        playerViewModel.initMediaController(this)
        authViewModel.init(this)

        setContent {
            var currentTheme by remember { mutableStateOf(AppThemePreset.CYBERPUNK) }

            LibrisAudioTheme(preset = currentTheme) {
                val authState by authViewModel.authState.collectAsState()

                // Show loading spinner while restoring session
                if (authState is AuthState.Idle) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = currentTheme.primary)
                    }
                    return@LibrisAudioTheme
                }

                // Show Login screen if not authenticated
                if (authState is AuthState.Unauthenticated || authState is AuthState.Error) {
                    LoginScreen(
                        authViewModel   = authViewModel,
                        authState       = authState,
                        currentTheme    = currentTheme
                    )
                    return@LibrisAudioTheme
                }

                // ── Authenticated App ──────────────────────────────────────
                val session = (authState as? AuthState.Authenticated)?.session

                var selectedTab by remember { mutableStateOf(MainTab.LIBRARY) }
                var selectedMusicTrack by remember { mutableStateOf<MusicTrack?>(null) }
                var backgroundVolume by remember { mutableStateOf(0.25f) }
                var isCarModeOpen by remember { mutableStateOf(false) }

                val books by playerViewModel.books.collectAsState()
                val currentBook by playerViewModel.currentBook.collectAsState()
                val isPlaying by playerViewModel.isPlaying.collectAsState()
                val currentPartIndex by playerViewModel.currentPartIndex.collectAsState()
                val playbackSpeed by playerViewModel.playbackSpeed.collectAsState()
                val currentPositionMs by playerViewModel.currentPositionMs.collectAsState()
                val durationMs by playerViewModel.durationMs.collectAsState()

                var isFullPlayerOpen by remember { mutableStateOf(false) }

                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    topBar = {
                        if (!isFullPlayerOpen && !isCarModeOpen) {
                            TopAppBar(
                                title = {
                                    Column {
                                        Text(
                                            text = "Libris Audio",
                                            fontSize = 18.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = Color.White
                                        )
                                        if (session != null) {
                                            Text(
                                                text = session.email,
                                                fontSize = 11.sp,
                                                color = Color(0xFF8FA3BF)
                                            )
                                        }
                                    }
                                },
                                navigationIcon = {
                                    Icon(
                                        Icons.Default.AutoStories,
                                        contentDescription = "Logo",
                                        tint = currentTheme.primary,
                                        modifier = Modifier.padding(start = 12.dp).size(28.dp)
                                    )
                                },
                                actions = {
                                    IconButton(onClick = { authViewModel.logout() }) {
                                        Icon(
                                            Logout,
                                            contentDescription = "Cerrar sesión",
                                            tint = Color(0xFF8FA3BF)
                                        )
                                    }
                                },
                                colors = TopAppBarDefaults.topAppBarColors(
                                    containerColor = Color(0xEE0A0F1E)
                                )
                            )
                        }
                    },
                    bottomBar = {
                        if (!isFullPlayerOpen && !isCarModeOpen) {
                            Column {
                                if (currentBook != null) {
                                    BottomPlayerBar(
                                        book = currentBook!!,
                                        isPlaying = isPlaying,
                                        currentPartIndex = currentPartIndex,
                                        onTogglePlay = { playerViewModel.togglePlayPause() },
                                        onNextPart = { playerViewModel.nextPart() },
                                        onOpenFullPlayer = { isFullPlayerOpen = true }
                                    )
                                }

                                NavigationBar(
                                    containerColor = Color(0xEE0F172A),
                                    contentColor = Color.White
                                ) {
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.LIBRARY,
                                        onClick = { selectedTab = MainTab.LIBRARY },
                                        icon = { Icon(Icons.Default.Book, contentDescription = "Biblioteca") },
                                        label = { Text("Biblioteca") },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.HISTORY,
                                        onClick = { selectedTab = MainTab.HISTORY },
                                        icon = { Icon(Icons.Default.History, contentDescription = "Historial") },
                                        label = { Text("Historial") },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.UPLOAD,
                                        onClick = { selectedTab = MainTab.UPLOAD },
                                        icon = { Icon(Icons.Default.CloudUpload, contentDescription = "Subir PDF") },
                                        label = { Text("Subir PDF") },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.SETTINGS,
                                        onClick = { selectedTab = MainTab.SETTINGS },
                                        icon = { Icon(Icons.Default.Settings, contentDescription = "Ajustes") },
                                        label = { Text("Ajustes") },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                }
                            }
                        }
                    }
                ) { innerPadding ->
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding)
                    ) {
                        when (selectedTab) {
                            MainTab.LIBRARY -> LibraryScreen(
                                books = books,
                                currentTheme = currentTheme,
                                onSelectTheme = { newTheme -> currentTheme = newTheme },
                                onBookSelect = { selectedBook -> playerViewModel.playBook(selectedBook) }
                            )
                            MainTab.HISTORY -> HistoryScreen(
                                books = books,
                                currentTheme = currentTheme,
                                onBookSelect = { selectedBook -> playerViewModel.playBook(selectedBook) }
                            )
                            MainTab.UPLOAD -> UploadScreen(
                                currentTheme = currentTheme,
                                onUploadSuccess = {
                                    playerViewModel.loadBooks()
                                    selectedTab = MainTab.LIBRARY
                                }
                            )
                            MainTab.SETTINGS -> SettingsScreen(
                                currentTheme = currentTheme,
                                onSelectTheme = { newTheme -> currentTheme = newTheme },
                                userName = session?.name ?: "",
                                userEmail = session?.email ?: "",
                                onLogout = { authViewModel.logout() }
                            )
                        }

                        if (currentBook != null && isFullPlayerOpen && !isCarModeOpen) {
                            PlayerScreen(
                                book = currentBook!!,
                                isPlaying = isPlaying,
                                currentPartIndex = currentPartIndex,
                                playbackSpeed = playbackSpeed,
                                currentPositionMs = currentPositionMs,
                                durationMs = durationMs,
                                currentTheme = currentTheme,
                                selectedMusicTrack = selectedMusicTrack,
                                backgroundVolume = backgroundVolume,
                                onSelectMusicTrack = { track -> selectedMusicTrack = track },
                                onBackgroundVolumeChange = { vol -> backgroundVolume = vol },
                                onTogglePlay = { playerViewModel.togglePlayPause() },
                                onNextPart = { playerViewModel.nextPart() },
                                onPreviousPart = { playerViewModel.previousPart() },
                                onSeekTo = { posMs -> playerViewModel.seekTo(posMs) },
                                onSelectSpeed = { speed -> playerViewModel.setSpeed(speed) },
                                onOpenCarMode = { isCarModeOpen = true },
                                onClose = { isFullPlayerOpen = false }
                            )
                        }

                        if (currentBook != null && isCarModeOpen) {
                            CarModeScreen(
                                book = currentBook!!,
                                isPlaying = isPlaying,
                                currentPartIndex = currentPartIndex,
                                onTogglePlay = { playerViewModel.togglePlayPause() },
                                onRewind15 = { playerViewModel.seekTo((currentPositionMs - 15000).coerceAtLeast(0)) },
                                onForward15 = { playerViewModel.seekTo(currentPositionMs + 15000) },
                                onNextPart = { playerViewModel.nextPart() },
                                onCloseCarMode = { isCarModeOpen = false }
                            )
                        }
                    }
                }
            }
        }
    }
}

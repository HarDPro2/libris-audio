package com.librisaudio.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.librisaudio.app.data.model.MusicTrack
import com.librisaudio.app.ui.components.BottomPlayerBar
import com.librisaudio.app.ui.screens.*
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.LibrisAudioTheme
import com.librisaudio.app.viewmodel.PlayerViewModel

enum class MainTab {
    LIBRARY, HISTORY, UPLOAD, SETTINGS
}

class MainActivity : ComponentActivity() {

    private val playerViewModel: PlayerViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        playerViewModel.initMediaController(this)

        setContent {
            var currentTheme by remember { mutableStateOf(AppThemePreset.CYBERPUNK) }
            var selectedTab by remember { mutableStateOf(MainTab.LIBRARY) }
            var selectedMusicTrack by remember { mutableStateOf<MusicTrack?>(null) }
            var backgroundVolume by remember { mutableStateOf(0.25f) }
            var isCarModeOpen by remember { mutableStateOf(false) }

            LibrisAudioTheme(preset = currentTheme) {
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
                                        colors = NavigationBarItemDefaults.colors(
                                            indicatorColor = currentTheme.primary
                                        )
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.HISTORY,
                                        onClick = { selectedTab = MainTab.HISTORY },
                                        icon = { Icon(Icons.Default.History, contentDescription = "Historial") },
                                        label = { Text("Historial") },
                                        colors = NavigationBarItemDefaults.colors(
                                            indicatorColor = currentTheme.primary
                                        )
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.UPLOAD,
                                        onClick = { selectedTab = MainTab.UPLOAD },
                                        icon = { Icon(Icons.Default.CloudUpload, contentDescription = "Subir PDF") },
                                        label = { Text("Subir PDF") },
                                        colors = NavigationBarItemDefaults.colors(
                                            indicatorColor = currentTheme.primary
                                        )
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.SETTINGS,
                                        onClick = { selectedTab = MainTab.SETTINGS },
                                        icon = { Icon(Icons.Default.Settings, contentDescription = "Ajustes") },
                                        label = { Text("Ajustes") },
                                        colors = NavigationBarItemDefaults.colors(
                                            indicatorColor = currentTheme.primary
                                        )
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
                                onSelectTheme = { newTheme -> currentTheme = newTheme }
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

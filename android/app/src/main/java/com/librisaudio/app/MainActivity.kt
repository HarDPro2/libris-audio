package com.librisaudio.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.librisaudio.app.data.model.MusicTrack
import com.librisaudio.app.ui.components.BottomPlayerBar
import com.librisaudio.app.ui.screens.LibraryScreen
import com.librisaudio.app.ui.screens.PlayerScreen
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.LibrisAudioTheme
import com.librisaudio.app.viewmodel.PlayerViewModel

class MainActivity : ComponentActivity() {

    private val playerViewModel: PlayerViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate()
        playerViewModel.initMediaController(this)

        setContent {
            var currentTheme by remember { mutableStateOf(AppThemePreset.CYBERPUNK) }
            var selectedMusicTrack by remember { mutableStateOf<MusicTrack?>(null) }
            var backgroundVolume by remember { mutableStateOf(0.25f) }

            LibrisAudioTheme(preset = currentTheme) {
                val books by playerViewModel.books.collectAsState()
                val currentBook by playerViewModel.currentBook.collectAsState()
                val isPlaying by playerViewModel.isPlaying.collectAsState()
                val currentPartIndex by playerViewModel.currentPartIndex.collectAsState()
                val playbackSpeed by playerViewModel.playbackSpeed.collectAsState()
                val currentPositionMs by playerViewModel.currentPositionMs.collectAsState()
                val durationMs by playerViewModel.durationMs.collectAsState()

                var isFullPlayerOpen by remember { mutableStateOf(false) }

                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding)
                    ) {
                        LibraryScreen(
                            books = books,
                            currentTheme = currentTheme,
                            onSelectTheme = { newTheme -> currentTheme = newTheme },
                            onBookSelect = { selectedBook ->
                                playerViewModel.playBook(selectedBook)
                            }
                        )

                        if (currentBook != null && !isFullPlayerOpen) {
                            BottomPlayerBar(
                                book = currentBook!!,
                                isPlaying = isPlaying,
                                currentPartIndex = currentPartIndex,
                                onTogglePlay = { playerViewModel.togglePlayPause() },
                                onNextPart = { playerViewModel.nextPart() },
                                onOpenFullPlayer = { isFullPlayerOpen = true },
                                modifier = Modifier.align(Alignment.BottomCenter)
                            )
                        }

                        if (currentBook != null && isFullPlayerOpen) {
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
                                onClose = { isFullPlayerOpen = false }
                            )
                        }
                    }
                }
            }
        }
    }
}

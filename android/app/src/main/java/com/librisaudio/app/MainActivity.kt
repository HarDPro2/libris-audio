package com.librisaudio.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.activity.compose.setContent
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.font.FontWeight
import com.librisaudio.app.data.api.AppwriteAuthClient
import com.librisaudio.app.data.api.AppwriteSdkClient
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
        AppwriteSdkClient.init(this)   // must be before handleAuthDeepLink
        // Handle deep link if app was launched via OAuth redirect
        handleAuthDeepLink(intent)
        // Render the UI
        buildUi()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleAuthDeepLink(intent)
    }

    private fun handleAuthDeepLink(intent: Intent?) {
        val data = intent?.data ?: return
        Log.d("MainActivity", "Deep link recibido: $data scheme=${data.scheme}")

        // Appwrite SDK scheme: appwrite-callback-{projectId}
        val expectedScheme = "appwrite-callback-${AppwriteAuthClient.APPWRITE_PROJECT_ID}"
        if (data.scheme != expectedScheme) return

        // Delegate full URI to AuthViewModel — it extracts params and fetches the account
        authViewModel.handleOAuthCallback(data)
    }

    private fun openGoogleOAuth() {
        // Appwrite SDK format: success URL must be appwrite-callback-{projectId}://
        // (no host, no path). Appwrite appends ?userId=X&secret=Y&expire=Z to it.
        val successUri = "appwrite-callback-${AppwriteAuthClient.APPWRITE_PROJECT_ID}://"
        val failureUri = "appwrite-callback-${AppwriteAuthClient.APPWRITE_PROJECT_ID}://"
        val url = "${AppwriteAuthClient.APPWRITE_ENDPOINT}v1/account/sessions/oauth2/google" +
                  "?project=${AppwriteAuthClient.APPWRITE_PROJECT_ID}" +
                  "&success=${Uri.encode(successUri)}" +
                  "&failure=${Uri.encode(failureUri)}"
        Log.d("MainActivity", "Opening OAuth URL: $url")
        // Use regular browser instead of Custom Tab — BlueStacks/some devices
        // don't forward query params correctly from Custom Tabs deep links
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }

    @OptIn(ExperimentalMaterial3Api::class)
    private fun buildUi() {
        setContent {
            val currentTheme by playerViewModel.selectedTheme.collectAsState()

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
                        currentTheme    = currentTheme,
                        onGoogleSignIn  = { openGoogleOAuth() }
                    )
                    return@LibrisAudioTheme
                }

                // ── Authenticated App ──────────────────────────────────────
                val session = (authState as? AuthState.Authenticated)?.session

                var selectedTab by remember { mutableStateOf(MainTab.LIBRARY) }
                var isCarModeOpen by remember { mutableStateOf(false) }

                // Background music state — tracked in PlayerViewModel so AudioService receives commands
                val selectedMusicTrack by playerViewModel.selectedMusicTrack.collectAsState()
                val backgroundVolume   by playerViewModel.backgroundVolume.collectAsState()

                // Libro 3D text state
                val currentPartText by playerViewModel.currentPartText.collectAsState()
                val isTextLoading   by playerViewModel.isTextLoading.collectAsState()

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
                                            Icons.Default.Logout,
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
                                personalBooks = books.filter { it.progressPercent > 0 },
                                currentTheme = currentTheme,
                                currentUserId = session?.userId ?: "",
                                onBookSelect = { selectedBook -> playerViewModel.playBook(selectedBook) },
                                onDeleteBook = { book -> playerViewModel.deleteBook(book, session?.sessionId ?: "") },
                                onEditBook  = { book, newTitle, newCat -> playerViewModel.editBook(book, newTitle, newCat, session?.sessionId ?: "") }
                            )
                            MainTab.HISTORY -> HistoryScreen(
                                books = books,
                                currentTheme = currentTheme,
                                onBookSelect = { selectedBook ->
                                    playerViewModel.playBook(selectedBook)
                                    selectedTab = MainTab.LIBRARY
                                }
                            )
                            MainTab.UPLOAD -> UploadScreen(
                                currentTheme = currentTheme,
                                currentUserId = session?.userId ?: "",
                                onUploadSuccess = {
                                    playerViewModel.loadBooks()
                                    selectedTab = MainTab.LIBRARY
                                }
                            )
                            MainTab.SETTINGS -> SettingsScreen(
                                currentTheme = currentTheme,
                                onSelectTheme = { newTheme -> playerViewModel.setTheme(newTheme) },
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
                                currentPartText = currentPartText,
                                isTextLoading = isTextLoading,
                                todayMinutes = playerViewModel.todayMinutes,
                                streakDays = playerViewModel.streakDays,
                                totalHours = playerViewModel.totalHours,
                                onSelectMusicTrack = { track -> playerViewModel.setBackgroundTrack(track) },
                                onBackgroundVolumeChange = { vol -> playerViewModel.setBackgroundVolume(vol) },
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

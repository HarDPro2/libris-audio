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
import androidx.compose.foundation.clickable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import com.librisaudio.app.data.api.AppwriteAuthClient
import com.librisaudio.app.data.api.AppwriteSdkClient
import com.librisaudio.app.data.model.ProfileManager
import com.librisaudio.app.data.model.UserProfile
import com.librisaudio.app.ui.components.BottomPlayerBar
import com.librisaudio.app.ui.components.ProfileAvatar
import com.librisaudio.app.ui.components.ProfileDialog
import com.librisaudio.app.ui.screens.*
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.LibrisAudioTheme
import com.librisaudio.app.util.UpdateManager
import com.librisaudio.app.viewmodel.AuthState
import com.librisaudio.app.viewmodel.AuthViewModel
import com.librisaudio.app.viewmodel.PlayerViewModel
import kotlinx.coroutines.launch

enum class MainTab {
    LIBRARY, HISTORY, UPLOAD, DOWNLOADS, SETTINGS
}

class MainActivity : ComponentActivity() {

    private val playerViewModel: PlayerViewModel by viewModels()
    private val authViewModel: AuthViewModel by viewModels()

    @OptIn(ExperimentalMaterial3Api::class)
    override fun attachBaseContext(newBase: android.content.Context) {
        // Aplica el idioma elegido por el usuario (i18n por-app)
        super.attachBaseContext(com.librisaudio.app.util.LocaleHelper.wrap(newBase))
    }

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
        // Use the TOKEN flow (not session) — returns userId+secret in the redirect
        // URL, which works for native apps. The session flow uses browser cookies.
        val url = "${AppwriteAuthClient.APPWRITE_ENDPOINT}v1/account/tokens/oauth2/google" +
                  "?project=${AppwriteAuthClient.APPWRITE_PROJECT_ID}" +
                  "&success=${Uri.encode(successUri)}" +
                  "&failure=${Uri.encode(failureUri)}"
        Log.d("MainActivity", "Opening OAuth URL: $url")
        // Use regular browser instead of Custom Tab — BlueStacks/some devices
        // don't forward query params correctly from Custom Tabs deep links
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }

    /** ¿La app está exenta de la optimización de batería? Si NO, los fabricantes
     *  agresivos (Samsung, Xiaomi/MIUI, Huawei, Oppo…) pueden cortar la reproducción
     *  con la pantalla apagada. */
    fun isIgnoringBatteryOptimizations(): Boolean {
        val pm = getSystemService(POWER_SERVICE) as android.os.PowerManager
        return pm.isIgnoringBatteryOptimizations(packageName)
    }

    /** Abre el diálogo del sistema para poner la app en "Sin restricciones". */
    fun requestIgnoreBatteryOptimizations() {
        try {
            startActivity(
                Intent(
                    android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                    Uri.parse("package:$packageName")
                )
            )
        } catch (_: Exception) {
            // Fallback: abre la lista de optimización de batería
            try {
                startActivity(Intent(android.provider.Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
            } catch (_: Exception) { /* algunos ROMs no exponen ninguno */ }
        }
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

                val userProfile by playerViewModel.userProfile.collectAsState()
                var showProfileDialog by remember { mutableStateOf(false) }

                // Al iniciar sesión: restaura progreso + preferencias desde la nube
                LaunchedEffect(session?.userId) {
                    session?.userId?.let { playerViewModel.enableCloudSync(it) }
                }

                // ── Aviso de batería: pedir "Sin restricciones" una vez ──────
                // Sin esto, muchos teléfonos cortan el audio con la pantalla apagada.
                var showBatteryDialog by remember { mutableStateOf(false) }
                LaunchedEffect(Unit) {
                    val prefs = getSharedPreferences("libris_prefs", MODE_PRIVATE)
                    val alreadyAsked = prefs.getBoolean("asked_battery_opt", false)
                    if (!isIgnoringBatteryOptimizations() && !alreadyAsked) {
                        showBatteryDialog = true
                    }
                }
                if (showBatteryDialog) {
                    AlertDialog(
                        onDismissRequest = { showBatteryDialog = false },
                        icon = { Icon(Icons.Filled.BatteryChargingFull, contentDescription = null, tint = currentTheme.primary) },
                        title = { Text("Reproducción con pantalla apagada") },
                        text = {
                            Text(
                                "Para que el audio no se corte al apagar la pantalla, permite que " +
                                "Libris funcione sin restricciones de batería. Algunos teléfonos " +
                                "(Samsung, Xiaomi, Huawei…) detienen las apps en segundo plano por defecto.\n\n" +
                                "En la siguiente pantalla elige \"Permitir\" o \"Sin restricciones\"."
                            )
                        },
                        confirmButton = {
                            TextButton(onClick = {
                                getSharedPreferences("libris_prefs", MODE_PRIVATE)
                                    .edit().putBoolean("asked_battery_opt", true).apply()
                                showBatteryDialog = false
                                requestIgnoreBatteryOptimizations()
                            }) { Text("Permitir") }
                        },
                        dismissButton = {
                            TextButton(onClick = {
                                getSharedPreferences("libris_prefs", MODE_PRIVATE)
                                    .edit().putBoolean("asked_battery_opt", true).apply()
                                showBatteryDialog = false
                            }) { Text("Ahora no") }
                        }
                    )
                }

                // ── Auto-actualizador: avisar si hay versión nueva en GitHub ──
                var updateInfo by remember { mutableStateOf<UpdateManager.UpdateInfo?>(null) }
                var updateDismissed by remember { mutableStateOf(false) }
                var downloading by remember { mutableStateOf(false) }
                var downloadProgress by remember { mutableStateOf(0) }
                val updateScope = rememberCoroutineScope()
                LaunchedEffect(Unit) {
                    updateInfo = UpdateManager.checkForUpdate(BuildConfig.VERSION_NAME)
                }
                val info = updateInfo
                if (info != null && !updateDismissed) {
                    AlertDialog(
                        onDismissRequest = { if (!downloading) updateDismissed = true },
                        icon = { Icon(Icons.Filled.SystemUpdate, contentDescription = null, tint = currentTheme.primary) },
                        title = { Text("Nueva versión disponible") },
                        text = {
                            Column {
                                Text("La versión ${info.versionName} está lista para instalar.")
                                if (info.notes.isNotBlank()) {
                                    Spacer(Modifier.height(8.dp))
                                    Text(
                                        info.notes,
                                        fontSize = 12.sp,
                                        color = Color(0xFF8FA3BF),
                                        maxLines = 6
                                    )
                                }
                                if (downloading) {
                                    Spacer(Modifier.height(12.dp))
                                    if (downloadProgress >= 0) {
                                        LinearProgressIndicator(
                                            progress = downloadProgress / 100f,
                                            modifier = Modifier.fillMaxWidth(),
                                            color = currentTheme.primary
                                        )
                                        Text("Descargando… $downloadProgress%", fontSize = 12.sp, color = Color(0xFF8FA3BF))
                                    } else {
                                        LinearProgressIndicator(
                                            modifier = Modifier.fillMaxWidth(),
                                            color = currentTheme.primary
                                        )
                                        Text("Descargando…", fontSize = 12.sp, color = Color(0xFF8FA3BF))
                                    }
                                }
                            }
                        },
                        confirmButton = {
                            TextButton(
                                enabled = !downloading,
                                onClick = {
                                    downloading = true
                                    downloadProgress = 0
                                    updateScope.launch {
                                        val apk = UpdateManager.downloadApk(this@MainActivity) { p ->
                                            downloadProgress = p
                                        }
                                        downloading = false
                                        if (apk != null) {
                                            UpdateManager.installApk(this@MainActivity, apk)
                                        } else {
                                            updateDismissed = true
                                        }
                                    }
                                }
                            ) { Text(if (downloading) "Descargando…" else "Actualizar") }
                        },
                        dismissButton = {
                            TextButton(
                                enabled = !downloading,
                                onClick = { updateDismissed = true }
                            ) { Text("Ahora no") }
                        }
                    )
                }

                var selectedTab by remember { mutableStateOf(MainTab.LIBRARY) }
                var isCarModeOpen by remember { mutableStateOf(false) }

                // Background music state — tracked in PlayerViewModel so AudioService receives commands
                val selectedMusicTrack by playerViewModel.selectedMusicTrack.collectAsState()
                val backgroundVolume   by playerViewModel.backgroundVolume.collectAsState()

                // Libro 3D text state
                val currentPartText by playerViewModel.currentPartText.collectAsState()
                val isTextLoading   by playerViewModel.isTextLoading.collectAsState()
                val wordTimings     by playerViewModel.wordTimings.collectAsState()

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
                                    Column(modifier = Modifier.clickable { showProfileDialog = true }) {
                                        Text(
                                            text = userProfile.displayName.ifBlank { "Tu perfil" },
                                            fontSize = 16.sp,
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
                                    Box(modifier = Modifier
                                        .padding(start = 10.dp)
                                        .clickable { showProfileDialog = true }
                                    ) {
                                        ProfileAvatar(userProfile, 34.dp)
                                    }
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
                                        icon = { Icon(Icons.Default.Book, contentDescription = stringResource(R.string.nav_library)) },
                                        label = { Text(stringResource(R.string.nav_library)) },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.HISTORY,
                                        onClick = { selectedTab = MainTab.HISTORY },
                                        icon = { Icon(Icons.Default.History, contentDescription = stringResource(R.string.nav_history)) },
                                        label = { Text(stringResource(R.string.nav_history)) },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.UPLOAD,
                                        onClick = { selectedTab = MainTab.UPLOAD },
                                        icon = { Icon(Icons.Default.CloudUpload, contentDescription = stringResource(R.string.nav_upload)) },
                                        label = { Text(stringResource(R.string.nav_upload)) },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.DOWNLOADS,
                                        onClick = { selectedTab = MainTab.DOWNLOADS },
                                        icon = { Icon(Icons.Default.Download, contentDescription = stringResource(R.string.nav_downloads)) },
                                        label = { Text(stringResource(R.string.nav_downloads)) },
                                        colors = NavigationBarItemDefaults.colors(indicatorColor = currentTheme.primary)
                                    )
                                    NavigationBarItem(
                                        selected = selectedTab == MainTab.SETTINGS,
                                        onClick = { selectedTab = MainTab.SETTINGS },
                                        icon = { Icon(Icons.Default.Settings, contentDescription = stringResource(R.string.nav_settings)) },
                                        label = { Text(stringResource(R.string.nav_settings)) },
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
                                currentUserEmail = session?.email ?: "",
                                onBookSelect = { selectedBook -> playerViewModel.resumeBook(selectedBook) },
                                onDeleteBook = { book -> playerViewModel.deleteBook(book, session?.sessionId ?: "") },
                                onEditBook  = { book, newTitle, newCat -> playerViewModel.editBook(book, newTitle, newCat, session?.sessionId ?: "") },
                                lastBookId = playerViewModel.lastBookId.collectAsState().value,
                                onContinue = { book -> playerViewModel.resumeBook(book) },
                                favorites = playerViewModel.favorites.collectAsState().value,
                                onToggleFavorite = { book -> playerViewModel.toggleFavorite(book.bookId) }
                            )
                            MainTab.HISTORY -> HistoryScreen(
                                books = books,
                                currentTheme = currentTheme,
                                onBookSelect = { selectedBook ->
                                    playerViewModel.resumeBook(selectedBook)
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
                            MainTab.DOWNLOADS -> DownloadsScreen(
                                currentTheme = currentTheme,
                                books = playerViewModel.offlineBooks.collectAsState().value,
                                totalBytes = playerViewModel.offlineTotalBytes.collectAsState().value,
                                onPlay = { bookId ->
                                    books.firstOrNull { it.bookId == bookId }?.let { playerViewModel.resumeBook(it) }
                                },
                                onDelete = { bookId -> playerViewModel.deleteOffline(bookId) },
                                onDeleteAll = { playerViewModel.deleteAllOffline() }
                            )
                            MainTab.SETTINGS -> SettingsScreen(
                                currentTheme = currentTheme,
                                onSelectTheme = { newTheme -> playerViewModel.setTheme(newTheme) },
                                userName = userProfile.displayName.ifBlank { session?.name ?: "" },
                                userEmail = session?.email ?: "",
                                onLogout = { authViewModel.logout() },
                                currentLang = com.librisaudio.app.util.LocaleHelper.getLang(this@MainActivity),
                                onSelectLanguage = { tag ->
                                    com.librisaudio.app.util.LocaleHelper.setLang(this@MainActivity, tag)
                                    recreate()   // re-aplica el idioma vía attachBaseContext
                                }
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
                                selectedVoice = playerViewModel.selectedVoice.collectAsState().value,
                                onSelectVoice = { voiceId -> playerViewModel.setVoice(voiceId) },
                                wordTimings = wordTimings,
                                onSelectMusicTrack = { track -> playerViewModel.setBackgroundTrack(track) },
                                onBackgroundVolumeChange = { vol -> playerViewModel.setBackgroundVolume(vol) },
                                onTogglePlay = { playerViewModel.togglePlayPause() },
                                onNextPart = { playerViewModel.nextPart() },
                                onPreviousPart = { playerViewModel.previousPart() },
                                onSeekTo = { posMs -> playerViewModel.seekTo(posMs) },
                                onSelectSpeed = { speed -> playerViewModel.setSpeed(speed) },
                                onOpenCarMode = { isCarModeOpen = true },
                                onStopPlayback = { playerViewModel.stopPlayback(); isFullPlayerOpen = false },
                                onReadNextPart = { playerViewModel.readNextPart() },
                                onReadPreviousPart = { playerViewModel.readPreviousPart() },
                                onPauseVoice = { playerViewModel.pauseVoice() },
                                bookmarks = playerViewModel.bookmarks.collectAsState().value,
                                onAddBookmark = { bid, pi, pos, note -> playerViewModel.addBookmark(bid, pi, pos, note) },
                                isDownloaded = playerViewModel.downloadedIds.collectAsState().value.contains(currentBook!!.bookId),
                                isDownloading = playerViewModel.downloadingBookId.collectAsState().value == currentBook!!.bookId,
                                downloadProgress = playerViewModel.downloadProgress.collectAsState().value,
                                onDownload = { playerViewModel.downloadBook(currentBook!!) },
                                onVoice = { text -> playerViewModel.onVoice(text) },
                                onVoiceHandsFree = { text -> playerViewModel.onVoiceHandsFree(text) },
                                voiceProcessing = playerViewModel.voiceProcessing.collectAsState().value,
                                voiceMessage = playerViewModel.voiceMessage.collectAsState().value,
                                onClearVoiceMessage = { playerViewModel.clearVoiceMessage() },
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

                        if (showProfileDialog) {
                            ProfileDialog(
                                initial = userProfile,
                                email = session?.email ?: "",
                                primary = currentTheme.primary,
                                onSave = { p -> playerViewModel.updateProfile(p) },
                                onDismiss = { showProfileDialog = false }
                            )
                        }
                    }
                }
            }
        }
    }
}

package com.librisaudio.app.viewmodel

import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.SharedPreferences
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.Player
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.MoreExecutors
import com.librisaudio.app.data.api.ApiClient
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.service.AudioService
import com.librisaudio.app.ui.theme.AppThemePreset
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class PlayerViewModel(application: Application) : AndroidViewModel(application) {

    private val prefs: SharedPreferences =
        application.getSharedPreferences("libris_progress", Context.MODE_PRIVATE)

    private val _books = MutableStateFlow<List<Book>>(emptyList())
    val books: StateFlow<List<Book>> = _books.asStateFlow()

    private val _currentBook = MutableStateFlow<Book?>(null)
    val currentBook: StateFlow<Book?> = _currentBook.asStateFlow()

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _currentPartIndex = MutableStateFlow(0)
    val currentPartIndex: StateFlow<Int> = _currentPartIndex.asStateFlow()

    private val _playbackSpeed = MutableStateFlow(1.0f)
    val playbackSpeed: StateFlow<Float> = _playbackSpeed.asStateFlow()

    private val _currentPositionMs = MutableStateFlow(0L)
    val currentPositionMs: StateFlow<Long> = _currentPositionMs.asStateFlow()

    private val _durationMs = MutableStateFlow(0L)
    val durationMs: StateFlow<Long> = _durationMs.asStateFlow()

    private var mediaController: MediaController? = null

    // ── Part text (for VirtualBookFrame / Libro 3D mode) ──────────────────
    private val _currentPartText = MutableStateFlow("")
    val currentPartText: StateFlow<String> = _currentPartText.asStateFlow()

    private val _isTextLoading = MutableStateFlow(false)
    val isTextLoading: StateFlow<Boolean> = _isTextLoading.asStateFlow()

    // ── Listening stats ───────────────────────────────────────────────────
    /** Today's listening minutes (persisted by calendar date). */
    val todayMinutes: Int
        get() {
            val today = java.text.SimpleDateFormat("yyyyMMdd", java.util.Locale.US)
                .format(java.util.Date())
            return prefs.getInt("stats_today_min_$today", 0)
        }

    /** Total accumulated listening hours (all time). */
    val totalHours: Double
        get() = prefs.getInt("stats_total_min", 0) / 60.0

    /** Consecutive days listened (naive: incremented once per day a book plays). */
    val streakDays: Int
        get() = prefs.getInt("stats_streak", 0)

    private fun addListeningMinutes(minutes: Int) {
        if (minutes <= 0) return
        val today = java.text.SimpleDateFormat("yyyyMMdd", java.util.Locale.US)
            .format(java.util.Date())
        val lastDay = prefs.getString("stats_last_day", "") ?: ""
        val todaySoFar = prefs.getInt("stats_today_min_$today", 0)
        val totalSoFar = prefs.getInt("stats_total_min", 0)
        val streak = prefs.getInt("stats_streak", 0)

        prefs.edit()
            .putInt("stats_today_min_$today", todaySoFar + minutes)
            .putInt("stats_total_min", totalSoFar + minutes)
            .putInt("stats_streak", if (lastDay != today) streak + 1 else streak)
            .putString("stats_last_day", today)
            .apply()
    }

    // ── Theme persistence ─────────────────────────────────────────────────
    private val _selectedTheme = MutableStateFlow(
        runCatching {
            AppThemePreset.valueOf(prefs.getString("theme", AppThemePreset.CYBERPUNK.name)!!)
        }.getOrDefault(AppThemePreset.CYBERPUNK)
    )
    val selectedTheme: StateFlow<AppThemePreset> = _selectedTheme.asStateFlow()

    fun setTheme(preset: AppThemePreset) {
        _selectedTheme.value = preset
        prefs.edit().putString("theme", preset.name).apply()
    }

    // ── Background music state ─────────────────────────────────────────────
    private val _selectedMusicTrack = MutableStateFlow<com.librisaudio.app.data.model.MusicTrack?>(null)
    val selectedMusicTrack: StateFlow<com.librisaudio.app.data.model.MusicTrack?> = _selectedMusicTrack.asStateFlow()

    private val _backgroundVolume = MutableStateFlow(0.25f)
    val backgroundVolume: StateFlow<Float> = _backgroundVolume.asStateFlow()

    // ── Voz del narrador (Edge TTS) ────────────────────────────────────────
    private val _selectedVoice = MutableStateFlow(
        prefs.getString("voice", com.librisaudio.app.data.model.VoiceCatalog.DEFAULT)
            ?: com.librisaudio.app.data.model.VoiceCatalog.DEFAULT
    )
    val selectedVoice: StateFlow<String> = _selectedVoice.asStateFlow()

    fun setVoice(voiceId: String) {
        if (voiceId == _selectedVoice.value) return
        _selectedVoice.value = voiceId
        prefs.edit().putString("voice", voiceId).apply()
        // Recargar la parte actual con la nueva voz, conservando la posición
        val book = _currentBook.value ?: return
        val player = mediaController ?: return
        val pos = player.currentPosition.coerceAtLeast(0L)
        val wasPlaying = player.isPlaying
        val mediaItem = MediaItem.Builder()
            .setUri(book.getAudioUrl(_currentPartIndex.value, voiceId))
            .setMediaMetadata(
                MediaMetadata.Builder()
                    .setTitle("${book.title} (Parte ${_currentPartIndex.value + 1})")
                    .setArtist(book.category)
                    .build()
            )
            .build()
        player.setMediaItem(mediaItem)
        player.prepare()
        player.seekTo(pos)
        if (wasPlaying) player.play()
    }

    init {
        loadBooks()
        startPositionTracker()
    }

    fun initMediaController(context: Context) {
        if (mediaController != null) return
        val sessionToken = SessionToken(context, ComponentName(context, AudioService::class.java))
        val controllerFuture = MediaController.Builder(context, sessionToken).buildAsync()
        controllerFuture.addListener({
            try {
                mediaController = controllerFuture.get()
                setupPlayerListener()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }, MoreExecutors.directExecutor())
    }

    private fun setupPlayerListener() {
        val player = mediaController ?: return
        player.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(playing: Boolean) {
                _isPlaying.value = playing
            }

            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) {
                    onPartEnded()
                }
            }

            override fun onPositionDiscontinuity(
                oldPosition: Player.PositionInfo,
                newPosition: Player.PositionInfo,
                reason: Int
            ) {
                _currentPositionMs.value = newPosition.positionMs
            }
        })
    }

    fun loadBooks() {
        viewModelScope.launch {
            try {
                val dtos = ApiClient.backendService.getBooksFromBackend()
                val mapped = dtos.map { dto ->
                    val bookId = dto.bookId ?: dto.id ?: "1"
                    // Restore persisted progress from SharedPreferences
                    val savedPartIndex    = prefs.getInt("part_$bookId", 0)
                    val savedProgressPct  = prefs.getInt("pct_$bookId", 0)
                    Book(
                        id              = dto.id ?: bookId,
                        bookId          = bookId,
                        title           = dto.title ?: "Sin título",
                        author          = dto.author ?: "Libris Audio",
                        category        = dto.category ?: "General",
                        coverUrl        = if (!dto.coverUrl.isNullOrEmpty()) dto.coverUrl
                                          else "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop",
                        partsCount      = dto.partsCount ?: 1,
                        currentPartIndex = savedPartIndex,
                        progressPercent  = savedProgressPct,
                        addedBy         = dto.addedBy ?: ""
                    )
                }
                _books.value = mapped
            } catch (e: Exception) {
                e.printStackTrace()
                _books.value = emptyList()
            }
        }
    }

    /** Fetches the plain text of a book part from the backend (for Libro 3D mode). */
    fun loadPartText(bookId: String, partIndex: Int) {
        viewModelScope.launch {
            _isTextLoading.value = true
            _currentPartText.value = ""
            try {
                val body = ApiClient.backendService.getBookText(bookId, partIndex)
                _currentPartText.value = body.string()
            } catch (e: Exception) {
                _currentPartText.value = "No se pudo cargar el texto de esta parte."
            } finally {
                _isTextLoading.value = false
            }
        }
    }

    /** Persist part index and progress percentage for a book to SharedPreferences. */
    private fun saveProgress(bookId: String, partIndex: Int, progressPct: Int) {
        prefs.edit()
            .putInt("part_$bookId", partIndex)
            .putInt("pct_$bookId", progressPct)
            .apply()
    }

    fun playBook(book: Book, partIndex: Int = 0) {
        _currentBook.value = book
        _currentPartIndex.value = partIndex

        // Persist which part we're on so HistoryScreen can show progress
        val progressPct = if (book.partsCount > 0)
            ((partIndex.toFloat() / book.partsCount) * 100).toInt()
        else 0
        saveProgress(book.bookId, partIndex, progressPct)

        // Update progress in the in-memory list so HistoryScreen updates immediately
        _books.value = _books.value.map {
            if (it.bookId == book.bookId) it.copy(currentPartIndex = partIndex, progressPercent = progressPct)
            else it
        }

        // Load text for Libro 3D mode (non-blocking, runs in background)
        loadPartText(book.bookId, partIndex)

        val audioUrl = book.getAudioUrl(partIndex, _selectedVoice.value)
        val mediaItem = MediaItem.Builder()
            .setUri(audioUrl)
            .setMediaMetadata(
                MediaMetadata.Builder()
                    .setTitle("${book.title} (Parte ${partIndex + 1})")
                    .setArtist(book.category)
                    .build()
            )
            .build()

        mediaController?.let { player ->
            player.setMediaItem(mediaItem)
            player.prepare()
            player.play()
            _isPlaying.value = true
        }
    }

    fun togglePlayPause() {
        val player = mediaController ?: return
        if (player.isPlaying) {
            player.pause()
            _isPlaying.value = false
        } else {
            player.play()
            _isPlaying.value = true
        }
    }

    fun nextPart() {
        val book = _currentBook.value ?: return
        val nextIdx = _currentPartIndex.value + 1
        if (nextIdx < book.partsCount) {
            playBook(book, nextIdx)
        }
    }

    fun previousPart() {
        val book = _currentBook.value ?: return
        val prevIdx = _currentPartIndex.value - 1
        if (prevIdx >= 0) {
            playBook(book, prevIdx)
        }
    }

    fun seekTo(positionMs: Long) {
        mediaController?.seekTo(positionMs)
        _currentPositionMs.value = positionMs
    }

    fun setSpeed(speed: Float) {
        _playbackSpeed.value = speed
        mediaController?.setPlaybackSpeed(speed)
    }

    private fun onPartEnded() {
        nextPart()
    }

    private fun startPositionTracker() {
        viewModelScope.launch {
            var ticksPlaying = 0
            while (true) {
                delay(500)
                mediaController?.let { player ->
                    if (player.isPlaying) {
                        _currentPositionMs.value = player.currentPosition
                        _durationMs.value = player.duration.coerceAtLeast(0L)
                        ticksPlaying++
                        // Every 60 ticks = 30 seconds of real playback → add 1 minute to stats
                        if (ticksPlaying % 60 == 0) {
                            addListeningMinutes(1)
                        }
                    }
                }
            }
        }
    }

    // ── Background music controls ──────────────────────────────────────────

    /**
     * Set (or clear) the background ambient track.
     * Sends a Media3 Custom Command to AudioService via the MediaController.
     */
    fun setBackgroundTrack(track: com.librisaudio.app.data.model.MusicTrack?) {
        _selectedMusicTrack.value = track

        val controller = mediaController ?: return
        if (track == null) {
            val cmd = androidx.media3.session.SessionCommand("STOP_BACKGROUND_TRACK", android.os.Bundle.EMPTY)
            controller.sendCustomCommand(cmd, android.os.Bundle.EMPTY)
        } else {
            val extras = android.os.Bundle().apply {
                putString("url", track.streamUrl)
                putFloat("volume", _backgroundVolume.value)
            }
            val cmd = androidx.media3.session.SessionCommand("SET_BACKGROUND_TRACK", android.os.Bundle.EMPTY)
            controller.sendCustomCommand(cmd, extras)
        }
    }

    fun setBackgroundVolume(volume: Float) {
        _backgroundVolume.value = volume.coerceIn(0f, 1f)
        val controller = mediaController ?: return
        val extras = android.os.Bundle().apply { putFloat("volume", volume.coerceIn(0f, 1f)) }
        val cmd = androidx.media3.session.SessionCommand("SET_BACKGROUND_VOLUME", android.os.Bundle.EMPTY)
        controller.sendCustomCommand(cmd, extras)
    }

    /** Owner: delete a book from catalog + R2. sessionId = Appwrite session token. */
    fun deleteBook(book: Book, sessionId: String) {
        viewModelScope.launch {
            try {
                val response = ApiClient.backendService.deleteBook(
                    bookId = book.bookId,
                    authorization = "Bearer $sessionId"
                )
                if (response.isSuccessful || response.code() == 404) {
                    // Remove from local list regardless
                    _books.value = _books.value.filter { it.id != book.id }
                    if (_currentBook.value?.id == book.id) {
                        _currentBook.value = null
                        _isPlaying.value = false
                        mediaController?.stop()
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    /** Owner: edit a book's title and/or category in catalog. */
    fun editBook(book: Book, newTitle: String, newCategory: String, sessionId: String) {
        viewModelScope.launch {
            try {
                val patch = mutableMapOf<String, String>()
                if (newTitle.isNotBlank() && newTitle != book.title) patch["title"] = newTitle
                if (newCategory.isNotBlank() && newCategory != book.category) patch["category"] = newCategory
                if (patch.isEmpty()) return@launch

                val response = ApiClient.backendService.patchBook(
                    bookId = book.bookId,
                    authorization = "Bearer $sessionId",
                    body = patch
                )
                if (response.isSuccessful) {
                    // Update local list immediately
                    _books.value = _books.value.map {
                        if (it.id == book.id) it.copy(title = newTitle, category = newCategory) else it
                    }
                    if (_currentBook.value?.id == book.id) {
                        _currentBook.value = _currentBook.value?.copy(title = newTitle, category = newCategory)
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}

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
import com.librisaudio.app.util.VoiceCommandParser
import com.librisaudio.app.util.VoiceIntent
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

    // ── Tiempos de palabra (karaoke / resaltado sincronizado) ─────────────
    private val _wordTimings = MutableStateFlow<List<com.librisaudio.app.data.model.WordTiming>>(emptyList())
    val wordTimings: StateFlow<List<com.librisaudio.app.data.model.WordTiming>> = _wordTimings.asStateFlow()

    // ── Descargas offline ─────────────────────────────────────────────────
    private val offline = com.librisaudio.app.data.OfflineManager(application)

    private val _downloadingBookId = MutableStateFlow<String?>(null)
    val downloadingBookId: StateFlow<String?> = _downloadingBookId.asStateFlow()

    private val _downloadProgress = MutableStateFlow(0)   // 0..100
    val downloadProgress: StateFlow<Int> = _downloadProgress.asStateFlow()

    private val _downloadedIds = MutableStateFlow<Set<String>>(emptySet())
    val downloadedIds: StateFlow<Set<String>> = _downloadedIds.asStateFlow()

    private val _offlineBooks = MutableStateFlow<List<com.librisaudio.app.data.OfflineBook>>(emptyList())
    val offlineBooks: StateFlow<List<com.librisaudio.app.data.OfflineBook>> = _offlineBooks.asStateFlow()

    private val _offlineTotalBytes = MutableStateFlow(0L)
    val offlineTotalBytes: StateFlow<Long> = _offlineTotalBytes.asStateFlow()

    /** Refresca la lista de libros descargados y el tamaño total. */
    fun refreshOffline() {
        val list = offline.downloadedBooks()
        _offlineBooks.value = list
        _downloadedIds.value = list.map { it.bookId }.toSet()
        _offlineTotalBytes.value = offline.totalSizeBytes()
    }

    /** Descarga el libro completo (audio+texto+timing) para la voz seleccionada. */
    fun downloadBook(book: Book) {
        if (_downloadingBookId.value != null) return   // una descarga a la vez
        viewModelScope.launch {
            _downloadingBookId.value = book.bookId
            _downloadProgress.value = 0
            offline.download(book, voiceEfectiva()) { done, total ->
                _downloadProgress.value = if (total > 0) done * 100 / total else 0
            }
            _downloadingBookId.value = null
            refreshOffline()
        }
    }

    fun deleteOffline(bookId: String) { offline.delete(bookId); refreshOffline() }
    fun deleteAllOffline() { offline.deleteAll(); refreshOffline() }

    /** Carga los tiempos de palabra de una parte para la voz actual. */
    fun loadTiming(bookId: String, partIndex: Int, voice: String) {
        viewModelScope.launch {
            _wordTimings.value = emptyList()
            // Offline primero: si la parte está descargada, usa el timing local
            offline.localTimings(bookId, partIndex, voice)?.let {
                _wordTimings.value = it
                return@launch
            }
            try {
                _wordTimings.value = ApiClient.backendService.getTiming(bookId, partIndex, voice)
            } catch (e: Exception) {
                _wordTimings.value = emptyList()  // sin karaoke si falla — el texto se muestra normal
            }
        }
    }

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
        saveToCloud()
    }

    // ── Marcos 3D ilustrados (premium, opt-in) ─────────────────────────────
    // Cuando está activo, en el modo "Libro" se usa el marco ilustrado del
    // género (res/drawable/frame_<genero>) si existe; si no, o si está apagado,
    // se mantiene el marco animado actual.
    private val _frames3d = MutableStateFlow(prefs.getBoolean("frames_3d", false))
    val frames3d: StateFlow<Boolean> = _frames3d.asStateFlow()

    fun setFrames3d(enabled: Boolean) {
        _frames3d.value = enabled
        prefs.edit().putBoolean("frames_3d", enabled).apply()
    }

    // ── Sincronización en la nube (progreso + preferencias) ────────────────
    private var cloudUserId: String? = null
    private var cloudSaveJob: kotlinx.coroutines.Job? = null

    /** Se llama al hacer login: guarda el userId y restaura su estado del servidor. */
    fun enableCloudSync(userId: String) {
        if (userId.isBlank() || cloudUserId == userId) return
        cloudUserId = userId
        restoreFromCloud()
    }

    /**
     * Vuelve a traer el estado de la nube. Se llama al reabrir la app: sin
     * esto, `restoreFromCloud` solo corría en el login y el progreso hecho en
     * otro dispositivo no aparecía hasta cerrar sesión. Mismo fallo que tenía
     * el auto-actualizador con LaunchedEffect(Unit).
     */
    // ── META 3.9 — voz según el idioma del documento ──────────────────────
    //
    // Un PDF en inglés leído con voz española es inservible para hacer
    // shadowing. Cuando el documento está en otro idioma se usa una voz de ese
    // idioma SOLO para ese libro: la voz preferida del usuario no se toca, así
    // que al volver a un libro en español sigue oyendo la suya.
    private val _idiomaDocumento = MutableStateFlow<String?>(null)
    val idiomaDocumento: StateFlow<String?> = _idiomaDocumento.asStateFlow()

    private var voiceOverride: String? = null

    /** Voz que se usa realmente para reproducir. */
    private fun voiceEfectiva(): String = voiceOverride ?: _selectedVoice.value

    private fun aplicarIdiomaDocumento(bookId: String) {
        viewModelScope.launch {
            val idioma = try {
                ApiClient.backendService.getBookIndex(bookId).language
            } catch (_: Exception) { null }
            _idiomaDocumento.value = idioma
            val preferida = _selectedVoice.value
            voiceOverride = when {
                idioma == "en" && !preferida.startsWith("en-") ->
                    com.librisaudio.app.data.model.VoiceCatalog.DEFAULT_EN
                idioma == "es" && !preferida.startsWith("es-") ->
                    com.librisaudio.app.data.model.VoiceCatalog.DEFAULT
                else -> null
            }
        }
    }

    fun syncNow() {
        if (cloudUserId == null) return
        if (_isPlaying.value) return   // no pisar una escucha en curso
        restoreFromCloud()
    }

    private fun restoreFromCloud() {
        val uid = cloudUserId ?: return
        viewModelScope.launch {
            try {
                val state = ApiClient.backendService.getUserState(uid)
                val editor = prefs.edit()
                state.theme?.let { name ->
                    runCatching { AppThemePreset.valueOf(name) }.getOrNull()?.let { t ->
                        _selectedTheme.value = t
                        editor.putString("theme", t.name)
                    }
                }
                state.voice?.let { v ->
                    _selectedVoice.value = v
                    editor.putString("voice", v)
                }
                // Fusión por libro: solo se acepta lo remoto si es MÁS RECIENTE
                // que lo local. Antes se sobrescribía siempre, así que abrir la
                // app en un móvil desactualizado borraba el avance del otro.
                state.progress?.forEach { (bookId, pp) ->
                    val locales = prefs.getLong("ts_$bookId", 0L)
                    if (pp.updatedAt >= locales) {
                        editor.putInt("part_$bookId", pp.part)
                        editor.putLong("pos_$bookId", pp.pos)
                        if (pp.pct > 0) editor.putInt("pct_$bookId", pp.pct)
                        editor.putLong("ts_$bookId", pp.updatedAt)
                    }
                }
                val started = (state.started ?: emptyList()).toMutableSet()
                state.progress?.keys?.let { started.addAll(it) }
                editor.putStringSet("started_books", started)
                state.stats?.let { s ->
                    editor.putInt("stats_streak", s.streak)
                    editor.putInt("stats_total_min", s.totalMin)
                    editor.putString("stats_last_day", s.lastDay)
                }
                state.favorites?.let {
                    editor.putStringSet("favorites", it.toSet())
                    _favorites.value = it.toSet()
                }
                editor.apply()
                // Perfil (nombre + avatar)
                if (state.displayName != null || state.avatarId != null) {
                    val cur = _userProfile.value
                    val merged = cur.copy(
                        displayName = state.displayName ?: cur.displayName,
                        avatarId = state.avatarId ?: cur.avatarId
                    )
                    _userProfile.value = merged
                    com.librisaudio.app.data.model.ProfileManager.save(getApplication<android.app.Application>(), merged)
                }
                // Marcapáginas
                state.bookmarks?.let {
                    _bookmarks.value = it
                    persistBookmarks()
                }
                loadBooks()   // refleja el progreso restaurado en "Mi Biblioteca"
            } catch (_: Exception) { /* sin conexión → sigue con lo local */ }
        }
    }

    /** Guarda el estado completo en la nube (con antirrebote para no saturar). */
    fun saveToCloud() {
        val uid = cloudUserId ?: return
        cloudSaveJob?.cancel()
        cloudSaveJob = viewModelScope.launch {
            delay(1500)
            try {
                val started = prefs.getStringSet("started_books", emptySet()) ?: emptySet()
                val progress = started.associateWith { bid ->
                    com.librisaudio.app.data.model.PartPos(
                        part = prefs.getInt("part_$bid", 0),
                        pos = prefs.getLong("pos_$bid", 0L),
                        pct = prefs.getInt("pct_$bid", 0),
                        updatedAt = prefs.getLong("ts_$bid", 0L)
                    )
                }
                val dto = com.librisaudio.app.data.model.UserStateDto(
                    theme = _selectedTheme.value.name,
                    voice = voiceEfectiva(),
                    progress = progress,
                    started = started.toList(),
                    favorites = _favorites.value.toList(),
                    displayName = _userProfile.value.displayName,
                    avatarId = _userProfile.value.avatarId,
                    bookmarks = _bookmarks.value,
                    stats = com.librisaudio.app.data.model.StatsDto(
                        streak = prefs.getInt("stats_streak", 0),
                        totalMin = prefs.getInt("stats_total_min", 0),
                        lastDay = prefs.getString("stats_last_day", "") ?: ""
                    )
                )
                ApiClient.backendService.putUserState(uid, dto)
            } catch (_: Exception) { /* reintenta en el próximo cambio */ }
        }
    }

    // ── Background music state ─────────────────────────────────────────────
    private val _selectedMusicTrack = MutableStateFlow<com.librisaudio.app.data.model.MusicTrack?>(null)
    val selectedMusicTrack: StateFlow<com.librisaudio.app.data.model.MusicTrack?> = _selectedMusicTrack.asStateFlow()

    private val _backgroundVolume = MutableStateFlow(0.25f)
    val backgroundVolume: StateFlow<Float> = _backgroundVolume.asStateFlow()

    // META 3.7 — bookId en el que el usuario eligio pista a mano (null = ninguno).
    private var musicaElegidaEnLibro: String? = null

    /**
     * Ajusta la musica de fondo al genero del libro que se abre.
     *
     * Regla deliberada: NO enciende la musica por su cuenta. Si esta apagada
     * sigue apagada; solo cambia QUE suena cuando ya hay musica puesta. Quien
     * no quiere musica de fondo no debe encontrarsela sonando en cada libro.
     * Tampoco pisa una eleccion manual hecha en este mismo libro.
     */
    fun aplicarMusicaDeGenero(book: Book) {
        if (_selectedMusicTrack.value == null) return          // apagada: se respeta
        if (musicaElegidaEnLibro == book.bookId) return        // el usuario ya eligio aqui
        val sugerida = com.librisaudio.app.data.model.GenreMusic.pistaSugerida(book) ?: return
        if (sugerida.id == _selectedMusicTrack.value?.id) return
        setBackgroundTrack(sugerida, manual = false)
    }

    // ── Voz del narrador (Edge TTS) ────────────────────────────────────────
    private val _selectedVoice = MutableStateFlow(
        prefs.getString("voice", com.librisaudio.app.data.model.VoiceCatalog.DEFAULT)
            ?: com.librisaudio.app.data.model.VoiceCatalog.DEFAULT
    )
    val selectedVoice: StateFlow<String> = _selectedVoice.asStateFlow()

    // ── Último libro reproducido (para "Continuar escuchando") ─────────────
    private val _lastBookId = MutableStateFlow(prefs.getString("last_book_id", "") ?: "")
    val lastBookId: StateFlow<String> = _lastBookId.asStateFlow()

    private fun markLastBook(bookId: String) {
        _lastBookId.value = bookId
        prefs.edit().putString("last_book_id", bookId).apply()
    }

    // ── Favoritos ──────────────────────────────────────────────────────────
    private val _favorites = MutableStateFlow(
        prefs.getStringSet("favorites", emptySet())?.toSet() ?: emptySet()
    )
    val favorites: StateFlow<Set<String>> = _favorites.asStateFlow()

    fun toggleFavorite(bookId: String) {
        val set = _favorites.value.toMutableSet()
        if (!set.add(bookId)) set.remove(bookId)
        _favorites.value = set
        prefs.edit().putStringSet("favorites", set).apply()
        saveToCloud()
    }

    // ── Marcapáginas (persistidos + sincronizados) ─────────────────────────
    private val _bookmarks = MutableStateFlow(loadBookmarks())
    val bookmarks: StateFlow<List<com.librisaudio.app.ui.components.BookmarkItem>> = _bookmarks.asStateFlow()

    private fun loadBookmarks(): List<com.librisaudio.app.ui.components.BookmarkItem> {
        val json = prefs.getString("bookmarks_json", null) ?: return emptyList()
        return try {
            val type = object : com.google.gson.reflect.TypeToken<List<com.librisaudio.app.ui.components.BookmarkItem>>() {}.type
            com.google.gson.Gson().fromJson<List<com.librisaudio.app.ui.components.BookmarkItem>>(json, type) ?: emptyList()
        } catch (_: Exception) { emptyList() }
    }

    private fun persistBookmarks() {
        prefs.edit().putString("bookmarks_json", com.google.gson.Gson().toJson(_bookmarks.value)).apply()
    }

    fun addBookmark(bookId: String, partIndex: Int, positionMs: Long, note: String) {
        val item = com.librisaudio.app.ui.components.BookmarkItem(
            id = System.currentTimeMillis().toString(),
            bookId = bookId, partIndex = partIndex, positionMs = positionMs, note = note
        )
        _bookmarks.value = _bookmarks.value + item
        persistBookmarks()
        saveToCloud()
    }

    fun removeBookmark(id: String) {
        _bookmarks.value = _bookmarks.value.filter { it.id != id }
        persistBookmarks()
        saveToCloud()
    }

    // ── Perfil (nombre + avatar) sincronizable ─────────────────────────────
    private val _userProfile = MutableStateFlow(
        com.librisaudio.app.data.model.ProfileManager.load(getApplication<android.app.Application>())
    )
    val userProfile: StateFlow<com.librisaudio.app.data.model.UserProfile> = _userProfile.asStateFlow()

    fun updateProfile(profile: com.librisaudio.app.data.model.UserProfile) {
        _userProfile.value = profile
        com.librisaudio.app.data.model.ProfileManager.save(getApplication<android.app.Application>(), profile)
        saveToCloud()
    }

    fun setVoice(voiceId: String) {
        if (voiceId == _selectedVoice.value) return
        // Elección manual: gana siempre sobre la detección automática.
        voiceOverride = null
        _selectedVoice.value = voiceId
        prefs.edit().putString("voice", voiceId).apply()
        saveToCloud()
        // Recargar la parte actual con la nueva voz, conservando la posición
        val book = _currentBook.value ?: return
        val player = mediaController ?: return
        val pos = player.currentPosition.coerceAtLeast(0L)
        val wasPlaying = player.isPlaying
        val idx = _currentPartIndex.value
        // Reconstruir la playlist completa con la nueva voz, en la misma parte/posición
        val items = (0 until book.partsCount).map { buildMediaItem(book, it, voiceId) }
        player.setMediaItems(items, idx, pos)
        player.prepare()
        if (wasPlaying) player.play()
        // Los tiempos cambian con la voz — recargar
        loadTiming(book.bookId, idx, voiceId)
    }

    init {
        loadBooks()
        startPositionTracker()
        refreshOffline()
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

            override fun onMediaItemTransition(item: MediaItem?, reason: Int) {
                // Cambió la parte activa, ya sea por avance automático (fin de parte)
                // o por salto manual (UI, notificación, Assistant, Android Auto,
                // Bluetooth). Ignoramos el cambio inicial de playlist y el repeat.
                if (reason == Player.MEDIA_ITEM_TRANSITION_REASON_PLAYLIST_CHANGED ||
                    reason == Player.MEDIA_ITEM_TRANSITION_REASON_REPEAT) return
                val newIdx = item?.mediaId?.toIntOrNull() ?: return
                if (newIdx != _currentPartIndex.value) applyPartChange(newIdx)
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
                val started = prefs.getStringSet("started_books", emptySet()) ?: emptySet()
                val mapped = dtos.map { dto ->
                    val bookId = dto.bookId ?: dto.id ?: "1"
                    // Restore persisted progress from SharedPreferences
                    val savedPartIndex    = prefs.getInt("part_$bookId", 0)
                    val savedProgressPct  = prefs.getInt("pct_$bookId", 0)
                    // Un libro empezado siempre muestra ≥1% para aparecer en "Mi Biblioteca"
                    val effectivePct = if (bookId in started) savedProgressPct.coerceAtLeast(1) else savedProgressPct
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
                        progressPercent  = effectivePct,
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
            // Offline primero: si la parte está descargada, usa el texto local
            offline.localText(bookId, partIndex)?.let {
                _currentPartText.value = it
                _isTextLoading.value = false
                return@launch
            }
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
            .putLong("ts_$bookId", System.currentTimeMillis())
            .apply()
    }

    fun playBook(book: Book, partIndex: Int = 0, seekToMs: Long = 0L) {
        val libroNuevo = _currentBook.value?.bookId != book.bookId
        if (libroNuevo) aplicarIdiomaDocumento(book.bookId)
        _currentBook.value = book
        if (libroNuevo) aplicarMusicaDeGenero(book)
        _currentPartIndex.value = partIndex

        // Persist which part we're on so HistoryScreen can show progress
        val progressPct = if (book.partsCount > 0)
            ((partIndex.toFloat() / book.partsCount) * 100).toInt()
        else 0
        saveProgress(book.bookId, partIndex, progressPct)
        markStarted(book.bookId)
        markLastBook(book.bookId)
        savePosition(book.bookId, seekToMs)
        saveToCloud()

        // El libro aparece en "Mi Biblioteca" al instante (min 1% aunque sea parte 0)
        _books.value = _books.value.map {
            if (it.bookId == book.bookId)
                it.copy(currentPartIndex = partIndex, progressPercent = progressPct.coerceAtLeast(1))
            else it
        }

        // Load text + word timings for Libro 3D / karaoke (non-blocking)
        loadPartText(book.bookId, partIndex)
        loadTiming(book.bookId, partIndex, voiceEfectiva())
        // Predescarga: el backend genera y cachea la SIGUIENTE parte (una sola,
        // para no saturar) → al avanzar no hay espera ni cortes.
        prefetchNextPart(book, partIndex, voiceEfectiva())

        val voice = voiceEfectiva()
        mediaController?.let { player ->
            // Playlist COMPLETA de todas las partes. Ventajas:
            //  • El control por sistema (Assistant, Android Auto, notificación,
            //    Bluetooth del volante) avanza/retrocede de parte de forma NATIVA.
            //  • ExoPlayer prebufferiza la siguiente ventana → sigue sin cortes con
            //    la pantalla apagada / Doze / offline (archivos locales).
            //  • "Ir al capítulo N" se vuelve un simple seekTo(index).
            // ExoPlayer solo bufferiza la ventana actual y la próxima, no descarga
            // todas las partes de golpe.
            val items = (0 until book.partsCount).map { buildMediaItem(book, it, voice) }
            player.setMediaItems(items, partIndex, seekToMs)
            player.prepare()
            player.play()
            _isPlaying.value = true
        }
    }

    /** Construye un MediaItem con el índice de parte codificado en el mediaId,
     *  para poder saber a qué parte avanzó ExoPlayer al reproducir la cola. */
    private fun buildMediaItem(book: Book, partIndex: Int, voice: String): MediaItem {
        // Offline primero: si el MP3 está descargado, reproduce el archivo local
        // (instantáneo y sin red — ideal con pantalla apagada / sin conexión).
        val local = offline.localAudio(book.bookId, partIndex, voice)
        val uri = if (local != null) android.net.Uri.fromFile(local)
                  else android.net.Uri.parse(book.getAudioUrl(partIndex, voice))
        return MediaItem.Builder()
            .setUri(uri)
            .setMediaId(partIndex.toString())
            .setMediaMetadata(
                MediaMetadata.Builder()
                    .setTitle("${book.title} (Parte ${partIndex + 1})")
                    .setArtist(book.category)
                    .build()
            )
            .build()
    }

    /** Sincroniza el estado de la app cuando cambia la parte activa (por avance
     *  automático al terminar, o por salto del usuario/sistema). NO toca la cola
     *  del reproductor — la playlist completa ya está cargada. */
    private fun applyPartChange(newIdx: Int) {
        val book = _currentBook.value ?: return
        _currentPartIndex.value = newIdx
        val progressPct = if (book.partsCount > 0)
            ((newIdx.toFloat() / book.partsCount) * 100).toInt() else 0
        saveProgress(book.bookId, newIdx, progressPct)
        markLastBook(book.bookId)
        savePosition(book.bookId, 0L)
        saveToCloud()
        _books.value = _books.value.map {
            if (it.bookId == book.bookId)
                it.copy(currentPartIndex = newIdx, progressPercent = progressPct.coerceAtLeast(1))
            else it
        }
        loadPartText(book.bookId, newIdx)
        loadTiming(book.bookId, newIdx, voiceEfectiva())
        prefetchNextPart(book, newIdx, voiceEfectiva())
    }

    /** Pausa la voz (para entrar al modo Solo Lectura). */
    fun pauseVoice() {
        mediaController?.pause()
        _isPlaying.value = false
    }

    /** Solo Lectura: carga el texto de una parte SIN reproducir audio ni karaoke. */
    private fun readPart(book: Book, partIndex: Int) {
        _currentPartIndex.value = partIndex
        val progressPct = if (book.partsCount > 0)
            ((partIndex.toFloat() / book.partsCount) * 100).toInt() else 0
        saveProgress(book.bookId, partIndex, progressPct)
        markStarted(book.bookId)
        markLastBook(book.bookId)
        savePosition(book.bookId, 0L)
        saveToCloud()
        _books.value = _books.value.map {
            if (it.bookId == book.bookId)
                it.copy(currentPartIndex = partIndex, progressPercent = progressPct.coerceAtLeast(1))
            else it
        }
        loadPartText(book.bookId, partIndex)
    }

    fun readNextPart() {
        val book = _currentBook.value ?: return
        val next = _currentPartIndex.value + 1
        if (next < book.partsCount) readPart(book, next)
    }

    fun readPreviousPart() {
        val book = _currentBook.value ?: return
        val prev = _currentPartIndex.value - 1
        if (prev >= 0) readPart(book, prev)
    }

    /** Reanuda un libro desde la última parte y posición guardadas (continuar donde quedó). */
    fun resumeBook(book: Book) {
        val part = prefs.getInt("part_${book.bookId}", 0)
        val pos  = prefs.getLong("pos_${book.bookId}", 0L)
        playBook(book, part, pos)
    }

    /** Detiene por completo la reproducción y cierra el libro actual. */
    fun stopPlayback() {
        mediaController?.stop()
        _isPlaying.value = false
        _currentBook.value = null
    }

    /** Warm-up de la siguiente parte en el backend (genera+cachea MP3 y tiempos). */
    private fun prefetchNextPart(book: Book, partIndex: Int, voice: String) {
        val next = partIndex + 1
        if (next >= book.partsCount) return
        viewModelScope.launch {
            try {
                ApiClient.backendService.getTiming(book.bookId, next, voice)
            } catch (_: Exception) { /* silencioso — es solo pre-carga */ }
        }
    }

    // ── Biblioteca del usuario: dos modos de borrado ──────────────────────
    //
    //  1. quitarDeBiblioteca  -> solo historial. Vale para CUALQUIER libro.
    //                            El libro sigue existiendo; si lo reabre, vuelve.
    //  2. eliminarDocumento   -> borrado total. SOLO para los que subió él:
    //                            documento, texto y todos los audios de R2.

    /** Quita el libro del historial local (y del estado en la nube). */
    fun removeFromLibrary(bookId: String, sessionId: String = "") {
        val set = (prefs.getStringSet("started_books", emptySet()) ?: emptySet()).toMutableSet()
        set.remove(bookId)
        val editor = prefs.edit()
            .putStringSet("started_books", set)
            .remove("part_$bookId")
            .remove("pct_$bookId")
            .remove("pos_$bookId")
        if (prefs.getString("last_book_id", null) == bookId) editor.remove("last_book_id")
        editor.apply()

        _books.value = _books.value.map {
            if (it.bookId == bookId) it.copy(progressPercent = 0, currentPartIndex = 0) else it
        }

        if (sessionId.isNotBlank()) {
            viewModelScope.launch {
                try {
                    ApiClient.backendService.removeFromLibrary(bookId, "Bearer $sessionId")
                } catch (_: Exception) { /* el borrado local ya surtió efecto */ }
            }
        }
    }

    private fun markStarted(bookId: String) {
        val set = (prefs.getStringSet("started_books", emptySet()) ?: emptySet()).toMutableSet()
        if (set.add(bookId)) prefs.edit().putStringSet("started_books", set).apply()
    }

    private fun savePosition(bookId: String, positionMs: Long) {
        prefs.edit()
            .putLong("pos_${bookId}", positionMs.coerceAtLeast(0L))
            .putLong("ts_${bookId}", System.currentTimeMillis())
            .apply()
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
        // Navegación nativa sobre la playlist → el estado se sincroniza vía
        // onMediaItemTransition (igual que el control por sistema).
        mediaController?.let { if (it.hasNextMediaItem()) it.seekToNextMediaItem() }
    }

    fun previousPart() {
        mediaController?.let { if (it.hasPreviousMediaItem()) it.seekToPreviousMediaItem() }
    }

    /** Salta directo a una parte (para "ir al capítulo N" del asistente de voz). */
    fun goToPart(index: Int) {
        val book = _currentBook.value ?: return
        val target = index.coerceIn(0, (book.partsCount - 1).coerceAtLeast(0))
        mediaController?.seekTo(target, 0L)
    }

    fun seekTo(positionMs: Long) {
        mediaController?.seekTo(positionMs)
        _currentPositionMs.value = positionMs
    }

    fun setSpeed(speed: Float) {
        _playbackSpeed.value = speed
        mediaController?.setPlaybackSpeed(speed)
    }

    // ── Asistente de voz (A1 local + A2 lenguaje natural) ──
    private val _voiceProcessing = MutableStateFlow(false)
    val voiceProcessing: StateFlow<Boolean> = _voiceProcessing.asStateFlow()
    private val _voiceMessage = MutableStateFlow<String?>(null)
    val voiceMessage: StateFlow<String?> = _voiceMessage.asStateFlow()
    fun clearVoiceMessage() { _voiceMessage.value = null }

    /** Procesa una frase de voz: primero gramática local (A1, gratis/offline);
     *  si no la entiende, cae al LLM vía backend (A2, con la key del usuario). */
    fun onVoice(text: String) {
        if (text.isBlank()) return
        val local = VoiceCommandParser.parse(text)
        if (local != VoiceIntent.Unknown) {
            executeIntent(local)
            _voiceMessage.value = messageFor(local, text)
            return
        }
        // A2: fallback al LLM (lenguaje natural)
        _voiceProcessing.value = true
        viewModelScope.launch {
            val resultIntent = try {
                val key = getApplication<Application>()
                    .getSharedPreferences("LibrisAudioPrefs", Context.MODE_PRIVATE)
                    .getString("OPENROUTER_API_KEY", "")?.trim()
                val resp = ApiClient.backendService.voiceCommand(
                    com.librisaudio.app.data.api.VoiceCommandRequest(
                        transcript = text,
                        current_part = _currentPartIndex.value,
                        parts_count = _currentBook.value?.partsCount ?: 1,
                        user_openrouter_key = key?.ifBlank { null }
                    )
                )
                actionToIntent(resp)
            } catch (e: Exception) {
                VoiceIntent.Unknown
            }
            if (resultIntent != VoiceIntent.Unknown) executeIntent(resultIntent)
            _voiceMessage.value = messageFor(resultIntent, text)
            _voiceProcessing.value = false
        }
    }

    /** Modo MANOS LIBRES (A3): solo gramática local (sin LLM), y silencioso si no
     *  reconoce — así la narración de fondo no dispara acciones ni toasts. */
    fun onVoiceHandsFree(text: String) {
        val intent = VoiceCommandParser.parse(text)
        if (intent != VoiceIntent.Unknown) {
            executeIntent(intent)
            _voiceMessage.value = messageFor(intent, text)
        }
    }

    private fun executeIntent(intent: VoiceIntent) {
        when (intent) {
            VoiceIntent.Play      -> { mediaController?.play(); _isPlaying.value = true }
            VoiceIntent.Pause     -> { mediaController?.pause(); _isPlaying.value = false }
            VoiceIntent.NextPart  -> nextPart()
            VoiceIntent.PrevPart  -> previousPart()
            is VoiceIntent.Rewind -> seekTo((_currentPositionMs.value - intent.seconds * 1000L).coerceAtLeast(0))
            is VoiceIntent.Forward-> seekTo(_currentPositionMs.value + intent.seconds * 1000L)
            is VoiceIntent.GoToPart -> goToPart(intent.part - 1)
            VoiceIntent.SpeedUp   -> setSpeed((_playbackSpeed.value + 0.25f).coerceAtMost(2.0f))
            VoiceIntent.SpeedDown -> setSpeed((_playbackSpeed.value - 0.25f).coerceAtLeast(0.5f))
            VoiceIntent.SpeedNormal -> setSpeed(1.0f)
            VoiceIntent.Bookmark  -> _currentBook.value?.let {
                addBookmark(it.bookId, _currentPartIndex.value, _currentPositionMs.value, "🎤")
            }
            VoiceIntent.WhereAmI  -> { }
            VoiceIntent.Stop      -> stopPlayback()
            VoiceIntent.Unknown   -> { }
        }
    }

    private fun actionToIntent(resp: com.librisaudio.app.data.api.VoiceCommandResponse): VoiceIntent =
        when (resp.action) {
            "play"        -> VoiceIntent.Play
            "pause"       -> VoiceIntent.Pause
            "next"        -> VoiceIntent.NextPart
            "prev"        -> VoiceIntent.PrevPart
            "rewind"      -> VoiceIntent.Rewind(resp.seconds ?: 15)
            "forward"     -> VoiceIntent.Forward(resp.seconds ?: 30)
            "goto"        -> VoiceIntent.GoToPart((resp.part ?: 1).coerceAtLeast(1))
            "speed_up"    -> VoiceIntent.SpeedUp
            "speed_down"  -> VoiceIntent.SpeedDown
            "speed_normal"-> VoiceIntent.SpeedNormal
            "bookmark"    -> VoiceIntent.Bookmark
            "where"       -> VoiceIntent.WhereAmI
            "stop"        -> VoiceIntent.Stop
            else          -> VoiceIntent.Unknown
        }

    private fun messageFor(intent: VoiceIntent, rawText: String): String {
        val app = getApplication<Application>()
        return when (intent) {
            VoiceIntent.WhereAmI -> app.getString(
                com.librisaudio.app.R.string.player_part_of,
                _currentPartIndex.value + 1,
                _currentBook.value?.partsCount ?: 1
            )
            VoiceIntent.Unknown -> app.getString(com.librisaudio.app.R.string.voice_not_understood)
            else -> "🎤 $rawText"
        }
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
                            saveToCloud()   // sincroniza posición/progreso periódicamente
                        }
                        // Cada 10 ticks (~5s) guardar la posición para poder reanudar
                        if (ticksPlaying % 10 == 0) {
                            _currentBook.value?.let { savePosition(it.bookId, player.currentPosition) }
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
    fun setBackgroundTrack(
        track: com.librisaudio.app.data.model.MusicTrack?,
        manual: Boolean = true
    ) {
        // META 3.7 — si la eleccion viene del usuario queda anclada a ESTE libro:
        // mientras siga en el, la autoseleccion por genero no se la pisa.
        if (manual) musicaElegidaEnLibro = _currentBook.value?.bookId
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
                    // Limpiar tambien el historial: si no, quedaban huerfanas
                    // las claves part_/pct_/pos_ y el id en started_books.
                    removeFromLibrary(book.bookId)
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

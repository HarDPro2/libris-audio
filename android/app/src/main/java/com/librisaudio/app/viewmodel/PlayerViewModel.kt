package com.librisaudio.app.viewmodel

import android.content.ComponentName
import android.content.Context
import androidx.lifecycle.ViewModel
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
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class PlayerViewModel : ViewModel() {

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
                    Book(
                        id = dto.id ?: dto.bookId ?: "1",
                        bookId = dto.bookId ?: dto.id ?: "1",
                        title = dto.title ?: "Sin título",
                        category = dto.category ?: "General",
                        coverUrl = if (!dto.coverUrl.isNullOrEmpty()) dto.coverUrl else "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop",
                        partsCount = dto.partsCount ?: 1
                    )
                }
                _books.value = if (mapped.isNotEmpty()) mapped else getDefaultCatalog()
            } catch (e: Exception) {
                e.printStackTrace()
                _books.value = getDefaultCatalog()
            }
        }
    }

    private fun getDefaultCatalog(): List<Book> {
        return listOf(
            Book(
                id = "1",
                bookId = "9780140449136",
                title = "La Odisea",
                category = "Clásicos",
                coverUrl = "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop",
                partsCount = 5
            ),
            Book(
                id = "2",
                bookId = "9788437604947",
                title = "Don Quijote de la Mancha",
                category = "Ficción",
                coverUrl = "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300&h=400&fit=crop",
                partsCount = 8
            )
        )
    }

    fun playBook(book: Book, partIndex: Int = 0) {
        _currentBook.value = book
        _currentPartIndex.value = partIndex

        val audioUrl = book.getAudioUrl(partIndex)
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
            while (true) {
                delay(500)
                mediaController?.let { player ->
                    if (player.isPlaying) {
                        _currentPositionMs.value = player.currentPosition
                        _durationMs.value = player.duration.coerceAtLeast(0L)
                    }
                }
            }
        }
    }
}

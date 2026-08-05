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
                val dtos = ApiClient.supabaseService.getGlobalBooks(ApiClient.SUPABASE_ANON_KEY)
                val mapped = dtos.map { dto ->
                    Book(
                        id = dto.id,
                        bookId = dto.bookId,
                        title = dto.title,
                        category = dto.category ?: "General",
                        coverUrl = dto.coverUrl,
                        partsCount = dto.partsCount ?: 1
                    )
                }
                _books.value = mapped
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun playBook(book: Book, partIndex: Int = 0) {
        _currentBook.value = book
        _currentPartIndex.value = partIndex
        val audioUrl = book.getAudioUrl(partIndex)

        val metadata = MediaMetadata.Builder()
            .setTitle(book.title)
            .setArtist(book.author)
            .build()

        val mediaItem = MediaItem.Builder()
            .setUri(audioUrl)
            .setMediaMetadata(metadata)
            .build()

        mediaController?.let { controller ->
            controller.setMediaItem(mediaItem)
            controller.setPlaybackSpeed(_playbackSpeed.value)
            controller.prepare()
            controller.play()
            _isPlaying.value = true
        }
    }

    fun togglePlayPause() {
        val controller = mediaController ?: return
        if (controller.isPlaying) {
            controller.pause()
            _isPlaying.value = false
        } else {
            controller.play()
            _isPlaying.value = true
        }
    }

    fun setSpeed(speed: Float) {
        _playbackSpeed.value = speed
        mediaController?.setPlaybackSpeed(speed)
    }

    fun seekTo(positionMs: Long) {
        mediaController?.seekTo(positionMs)
        _currentPositionMs.value = positionMs
    }

    fun nextPart() {
        val book = _currentBook.value ?: return
        if (_currentPartIndex.value < book.partsCount - 1) {
            playBook(book, _currentPartIndex.value + 1)
        }
    }

    fun previousPart() {
        val book = _currentBook.value ?: return
        if (_currentPartIndex.value > 0) {
            playBook(book, _currentPartIndex.value - 1)
        }
    }

    private fun onPartEnded() {
        val book = _currentBook.value ?: return
        if (_currentPartIndex.value < book.partsCount - 1) {
            playBook(book, _currentPartIndex.value + 1)
        } else {
            _isPlaying.value = false
        }
    }

    private fun startPositionTracker() {
        viewModelScope.launch {
            while (true) {
                mediaController?.let { controller ->
                    if (controller.isPlaying) {
                        _currentPositionMs.value = controller.currentPosition
                        _durationMs.value = if (controller.duration > 0) controller.duration else 0L
                    }
                }
                delay(1000)
            }
        }
    }
}

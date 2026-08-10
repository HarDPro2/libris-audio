package com.librisaudio.app.service

import android.os.Bundle
import android.os.PowerManager
import androidx.annotation.OptIn
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.CommandButton
import androidx.media3.session.MediaLibraryService
import androidx.media3.session.MediaSession
import androidx.media3.session.SessionCommand
import androidx.media3.session.SessionResult
import com.google.common.collect.ImmutableList
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture
import com.librisaudio.app.R

class AudioService : MediaLibraryService() {

    private var mediaSession: MediaLibrarySession? = null
    private lateinit var voicePlayer: ExoPlayer
    private lateinit var backgroundMusicPlayer: ExoPlayer

    private var wakeLock: PowerManager.WakeLock? = null

    @OptIn(UnstableApi::class)
    override fun onCreate() {
        super.onCreate()

        // 1. Initialize Voice ExoPlayer (Speech Attributes)
        val speechAudioAttributes = AudioAttributes.Builder()
            .setUsage(C.USAGE_MEDIA)
            .setContentType(C.CONTENT_TYPE_SPEECH)
            .build()

        voicePlayer = ExoPlayer.Builder(this)
            .setAudioAttributes(speechAudioAttributes, true)
            .setHandleAudioBecomingNoisy(true)
            .setWakeMode(C.WAKE_MODE_NETWORK)
            // Incrementos para "retrocede/adelanta" (Assistant, Android Auto,
            // notificación, botones Bluetooth del volante).
            .setSeekBackIncrementMs(30_000L)
            .setSeekForwardIncrementMs(30_000L)
            .build()

        // 2. Initialize Background Music ExoPlayer (Music Attributes, Looping)
        val musicAudioAttributes = AudioAttributes.Builder()
            .setUsage(C.USAGE_MEDIA)
            .setContentType(C.CONTENT_TYPE_MUSIC)
            .build()

        backgroundMusicPlayer = ExoPlayer.Builder(this)
            .setAudioAttributes(musicAudioAttributes, false)
            .build()

        backgroundMusicPlayer.repeatMode = Player.REPEAT_MODE_ONE
        backgroundMusicPlayer.volume = 0.25f // Default 25% background volume

        // 3. WakeLock to prevent CPU sleep during playback
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "LibrisAudio::WakeLock")

        // 4. Botones de retroceder/adelantar 30s para la notificación / pantalla
        //    de bloqueo (así "no escuché bien" se resuelve con un toque, sin voz).
        val rewindButton = CommandButton.Builder()
            .setDisplayName("Retroceder 30s")
            .setIconResId(R.drawable.ic_seek_back_30)
            .setPlayerCommand(Player.COMMAND_SEEK_BACK)
            .build()
        val forwardButton = CommandButton.Builder()
            .setDisplayName("Adelantar 30s")
            .setIconResId(R.drawable.ic_seek_forward_30)
            .setPlayerCommand(Player.COMMAND_SEEK_FORWARD)
            .build()

        // 5. Build MediaSession con el layout personalizado
        mediaSession = MediaLibrarySession.Builder(this, voicePlayer, LibraryCallback())
            .setCustomLayout(ImmutableList.of(rewindButton, forwardButton))
            .build()

        // 5. WakeLock ligado a la voz (la música de fondo suena independiente)
        voicePlayer.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                if (isPlaying) {
                    if (wakeLock?.isHeld == false) wakeLock?.acquire(3 * 60 * 60 * 1000L)
                } else {
                    if (wakeLock?.isHeld == true) wakeLock?.release()
                }
            }
        })
    }

    fun playBackgroundTrack(url: String, volume: Float = 0.25f) {
        val item = MediaItem.fromUri(url)
        backgroundMusicPlayer.setMediaItem(item)
        backgroundMusicPlayer.volume = volume
        backgroundMusicPlayer.prepare()
        // Arranca siempre al seleccionar (ambiente independiente de la voz —
        // así también suena en el modo lectura con la voz en pausa).
        backgroundMusicPlayer.playWhenReady = true
        backgroundMusicPlayer.play()
    }

    fun stopBackgroundTrack() {
        backgroundMusicPlayer.stop()
        backgroundMusicPlayer.clearMediaItems()
    }

    fun setBackgroundVolume(volume: Float) {
        backgroundMusicPlayer.volume = volume.coerceIn(0f, 1f)
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaLibrarySession? {
        return mediaSession
    }

    override fun onDestroy() {
        mediaSession?.run {
            voicePlayer.release()
            backgroundMusicPlayer.release()
            release()
            mediaSession = null
        }
        if (wakeLock?.isHeld == true) {
            wakeLock?.release()
        }
        super.onDestroy()
    }

    private inner class LibraryCallback : MediaLibrarySession.Callback {

        // Declare which custom commands this service accepts
        override fun onConnect(
            session: MediaSession,
            controller: MediaSession.ControllerInfo
        ): MediaSession.ConnectionResult {
            val customCommands = setOf(
                SessionCommand("SET_BACKGROUND_TRACK",  Bundle.EMPTY),
                SessionCommand("STOP_BACKGROUND_TRACK", Bundle.EMPTY),
                SessionCommand("SET_BACKGROUND_VOLUME", Bundle.EMPTY)
            )
            val connectionResult = super.onConnect(session, controller)
            return MediaSession.ConnectionResult.accept(
                connectionResult.availableSessionCommands.buildUpon()
                    .addSessionCommands(customCommands)
                    .build(),
                connectionResult.availablePlayerCommands
            )
        }

        @OptIn(UnstableApi::class)
        override fun onCustomCommand(
            session: MediaSession,
            controller: MediaSession.ControllerInfo,
            customCommand: SessionCommand,
            args: Bundle
        ): ListenableFuture<SessionResult> {
            when (customCommand.customAction) {
                "SET_BACKGROUND_TRACK" -> {
                    val url    = args.getString("url") ?: return Futures.immediateFuture(SessionResult(SessionResult.RESULT_ERROR_BAD_VALUE))
                    val volume = args.getFloat("volume", 0.25f)
                    playBackgroundTrack(url, volume)
                }
                "STOP_BACKGROUND_TRACK" -> stopBackgroundTrack()
                "SET_BACKGROUND_VOLUME" -> {
                    val volume = args.getFloat("volume", 0.25f)
                    setBackgroundVolume(volume)
                }
            }
            return Futures.immediateFuture(SessionResult(SessionResult.RESULT_SUCCESS))
        }
    }
}

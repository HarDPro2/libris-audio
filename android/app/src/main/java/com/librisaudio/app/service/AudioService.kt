package com.librisaudio.app.service

import android.content.Intent
import android.os.PowerManager
import androidx.annotation.OptIn
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaLibraryService
import androidx.media3.session.MediaSession

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

        // 4. Build MediaSession
        mediaSession = MediaLibrarySession.Builder(this, voicePlayer, LibraryCallback()).build()

        // 5. Sync background music play/pause with voice playback
        voicePlayer.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                if (isPlaying) {
                    if (wakeLock?.isHeld == false) wakeLock?.acquire(3 * 60 * 60 * 1000L)
                    if (backgroundMusicPlayer.mediaItemCount > 0 && !backgroundMusicPlayer.isPlaying) {
                        backgroundMusicPlayer.play()
                    }
                } else {
                    if (wakeLock?.isHeld == true) wakeLock?.release()
                    if (backgroundMusicPlayer.isPlaying) {
                        backgroundMusicPlayer.pause()
                    }
                }
            }
        })
    }

    fun playBackgroundTrack(url: String, volume: Float = 0.25f) {
        val item = MediaItem.fromUri(url)
        backgroundMusicPlayer.setMediaItem(item)
        backgroundMusicPlayer.volume = volume
        backgroundMusicPlayer.prepare()
        if (voicePlayer.isPlaying) {
            backgroundMusicPlayer.play()
        }
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

    private inner class LibraryCallback : MediaLibrarySession.Callback
}

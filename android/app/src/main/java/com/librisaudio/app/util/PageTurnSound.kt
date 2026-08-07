package com.librisaudio.app.util

import android.content.Context
import android.media.AudioManager
import android.media.MediaPlayer

/**
 * Reproduce un sonido corto al pasar de página, para aumentar la inmersión.
 *
 * - Si existe `res/raw/page_flip.mp3` (o .ogg/.wav), lo usa (sonido real de hoja).
 * - Si no, cae a un clic suave del sistema como respaldo, sin depender de archivos.
 *
 * Para el sonido de hoja real: coloca `page_flip.mp3` en
 *   android/app/src/main/res/raw/page_flip.mp3
 */
object PageTurnSound {
    fun play(context: Context) {
        try {
            val resId = context.resources.getIdentifier("page_flip", "raw", context.packageName)
            if (resId != 0) {
                MediaPlayer.create(context, resId)?.apply {
                    setOnCompletionListener { it.release() }
                    start()
                }
            } else {
                (context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager)
                    ?.playSoundEffect(AudioManager.FX_KEY_CLICK, 0.5f)
            }
        } catch (_: Exception) { /* el sonido es secundario, nunca debe romper la app */ }
    }
}

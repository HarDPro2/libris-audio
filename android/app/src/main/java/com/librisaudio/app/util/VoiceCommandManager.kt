package com.librisaudio.app.util

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Reconocimiento de voz ON-DEVICE (gratis, offline en la mayoría de teléfonos).
 * Escucha un comando corto y devuelve el texto reconocido. Debe usarse en el hilo
 * principal (SpeechRecognizer lo exige).
 */
class VoiceCommandManager(context: Context) {

    private val appCtx = context.applicationContext
    private var recognizer: SpeechRecognizer? = null

    fun isAvailable(): Boolean = SpeechRecognizer.isRecognitionAvailable(appCtx)

    fun listen(
        langTag: String,
        onResult: (String) -> Unit,
        onError: (Int) -> Unit
    ) {
        stop()
        val r = try {
            if (Build.VERSION.SDK_INT >= 33 &&
                SpeechRecognizer.isOnDeviceRecognitionAvailable(appCtx)
            ) SpeechRecognizer.createOnDeviceSpeechRecognizer(appCtx)
            else SpeechRecognizer.createSpeechRecognizer(appCtx)
        } catch (e: Exception) {
            SpeechRecognizer.createSpeechRecognizer(appCtx)
        }
        recognizer = r
        val resultCb = onResult      // capturamos los callbacks para evitar
        val errorCb = onError        // colisión de nombres con los overrides

        r.setRecognitionListener(object : RecognitionListener {
            override fun onResults(results: Bundle) {
                val list = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                resultCb(list?.firstOrNull().orEmpty())
            }
            override fun onError(error: Int) { errorCb(error) }
            override fun onReadyForSpeech(params: Bundle?) {}
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, langTag)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }
        try {
            r.startListening(intent)
        } catch (e: Exception) {
            onError(SpeechRecognizer.ERROR_CLIENT)
        }
    }

    fun stop() {
        try { recognizer?.destroy() } catch (_: Exception) {}
        recognizer = null
    }

    /** Versión suspend para el modo manos libres: escucha una vez y devuelve el
     *  texto (o "" si hubo error/silencio). Cancelable. */
    suspend fun listenOnce(langTag: String): String =
        kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            listen(
                langTag = langTag,
                onResult = { if (cont.isActive) cont.resumeWith(Result.success(it)) },
                onError = { if (cont.isActive) cont.resumeWith(Result.success("")) }
            )
            cont.invokeOnCancellation { stop() }
        }
}

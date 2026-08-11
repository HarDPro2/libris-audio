package com.librisaudio.app.util

import java.text.Normalizer

/** Intención reconocida a partir de un comando de voz. */
sealed class VoiceIntent {
    object Play : VoiceIntent()
    object Pause : VoiceIntent()
    object NextPart : VoiceIntent()
    object PrevPart : VoiceIntent()
    data class Rewind(val seconds: Int) : VoiceIntent()
    data class Forward(val seconds: Int) : VoiceIntent()
    data class GoToPart(val part: Int) : VoiceIntent()   // 1-based
    object SpeedUp : VoiceIntent()
    object SpeedDown : VoiceIntent()
    object SpeedNormal : VoiceIntent()
    object Bookmark : VoiceIntent()
    object WhereAmI : VoiceIntent()
    object Stop : VoiceIntent()
    object Unknown : VoiceIntent()
}

/**
 * Parser de comandos de voz BILINGÜE (ES/EN) por gramática. Sin red, sin costo.
 * Cubre los comandos claros; las frases ambiguas las resuelve A2 (LLM) más adelante.
 */
object VoiceCommandParser {

    fun parse(raw: String): VoiceIntent {
        val t = normalize(raw)
        if (t.isBlank()) return VoiceIntent.Unknown
        val num = extractNumber(t)

        // 1) Velocidad
        if (containsAny(t, "mas rapido", "más rapido", "acelera", "faster", "speed up"))
            return VoiceIntent.SpeedUp
        if (containsAny(t, "mas lento", "más lento", "despacio", "slower", "slow down"))
            return VoiceIntent.SpeedDown
        if (containsAny(t, "velocidad normal", "normal speed", "velocidad uno"))
            return VoiceIntent.SpeedNormal

        // 2) Ir al capítulo/parte N (sin contexto de retroceder/adelantar/siguiente)
        if (num != null && containsAny(t, "capitulo", "chapter", "parte", "part") &&
            !containsAny(t, "siguiente", "next", "anterior", "previous", "atras",
                "back", "adelanta", "avanza", "forward", "retrocede", "rewind", "segundo", "second")
        ) return VoiceIntent.GoToPart(num)

        // 3) Retroceder / adelantar N segundos
        if (containsAny(t, "retrocede", "atras", "rewind", "regresa", "back"))
            return VoiceIntent.Rewind(if (num != null && containsAny(t, "segundo", "second")) num else 15)
        if (containsAny(t, "adelanta", "avanza", "forward", "skip ahead", "salta"))
            return VoiceIntent.Forward(if (num != null && containsAny(t, "segundo", "second")) num else 30)

        // 4) Navegación de parte
        if (containsAny(t, "siguiente", "proxima", "próxima", "next"))
            return VoiceIntent.NextPart
        if (containsAny(t, "anterior", "previous", "regresa parte", "parte anterior"))
            return VoiceIntent.PrevPart

        // 5) Marcapáginas
        if (containsAny(t, "marca", "marcapagina", "bookmark", "guarda esto", "save mark"))
            return VoiceIntent.Bookmark

        // 6) ¿Dónde estoy?
        if (containsAny(t, "donde estoy", "que parte", "which part", "where am i", "what part"))
            return VoiceIntent.WhereAmI

        // 7) Detener por completo / cerrar
        if (containsAny(t, "deten la reproduccion", "detener", "cierra", "cerrar", "salir",
                "stop playback", "close", "exit"))
            return VoiceIntent.Stop

        // 8) Pausar / reanudar
        if (containsAny(t, "pausa", "pause", "detente", "espera", "stop"))
            return VoiceIntent.Pause
        if (containsAny(t, "reanuda", "continua", "continúa", "sigue", "reproduce",
                "play", "resume", "continue"))
            return VoiceIntent.Play

        return VoiceIntent.Unknown
    }

    private fun normalize(s: String): String =
        Normalizer.normalize(s.lowercase().trim(), Normalizer.Form.NFD)
            .replace(Regex("\\p{Mn}"), "")

    private fun containsAny(t: String, vararg words: String): Boolean = words.any { t.contains(it) }

    private fun extractNumber(t: String): Int? {
        Regex("\\d+").find(t)?.value?.toIntOrNull()?.let { return it }
        val words = mapOf(
            "un" to 1, "uno" to 1, "una" to 1, "one" to 1,
            "dos" to 2, "two" to 2, "tres" to 3, "three" to 3,
            "cuatro" to 4, "four" to 4, "cinco" to 5, "five" to 5,
            "seis" to 6, "six" to 6, "siete" to 7, "seven" to 7,
            "ocho" to 8, "eight" to 8, "nueve" to 9, "nine" to 9,
            "diez" to 10, "ten" to 10, "once" to 11, "eleven" to 11,
            "doce" to 12, "twelve" to 12, "trece" to 13, "thirteen" to 13,
            "catorce" to 14, "fourteen" to 14, "quince" to 15, "fifteen" to 15,
            "dieciseis" to 16, "sixteen" to 16, "diecisiete" to 17, "seventeen" to 17,
            "dieciocho" to 18, "eighteen" to 18, "diecinueve" to 19, "nineteen" to 19,
            "veinte" to 20, "twenty" to 20, "treinta" to 30, "thirty" to 30,
            "cuarenta" to 40, "forty" to 40, "cincuenta" to 50, "fifty" to 50,
            "sesenta" to 60, "sixty" to 60, "noventa" to 90, "ninety" to 90,
            "cien" to 100, "hundred" to 100
        )
        for (w in t.split(" ", ",", ".")) words[w.trim()]?.let { return it }
        return null
    }
}

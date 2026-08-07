package com.librisaudio.app.data.model

/** Una voz neural de Edge TTS (Microsoft Azure). */
data class TtsVoice(
    val id: String,       // ID de Edge TTS, p.ej. "es-MX-JorgeNeural"
    val name: String,     // nombre para mostrar
    val country: String,
    val gender: String,   // "Mujer" / "Hombre"
    val flag: String      // emoji de bandera
)

object VoiceCatalog {
    const val DEFAULT = "es-MX-JorgeNeural"

    val voices = listOf(
        TtsVoice("es-ES-ElviraNeural",   "Elvira",    "España",     "Mujer",  "🇪🇸"),
        TtsVoice("es-ES-AlvaroNeural",   "Álvaro",    "España",     "Hombre", "🇪🇸"),
        TtsVoice("es-MX-DaliaNeural",    "Dalia",     "México",     "Mujer",  "🇲🇽"),
        TtsVoice("es-MX-JorgeNeural",    "Jorge",     "México",     "Hombre", "🇲🇽"),
        TtsVoice("es-AR-ElenaNeural",    "Elena",     "Argentina",  "Mujer",  "🇦🇷"),
        TtsVoice("es-AR-TomasNeural",    "Tomás",     "Argentina",  "Hombre", "🇦🇷"),
        TtsVoice("es-CO-SalomeNeural",   "Salomé",    "Colombia",   "Mujer",  "🇨🇴"),
        TtsVoice("es-VE-PaolaNeural",    "Paola",     "Venezuela",  "Mujer",  "🇻🇪"),
        TtsVoice("en-US-AriaNeural",     "Aria",      "USA",        "Mujer",  "🇺🇸"),
        TtsVoice("en-US-GuyNeural",      "Guy",       "USA",        "Hombre", "🇺🇸"),
        TtsVoice("pt-BR-FranciscaNeural","Francisca", "Brasil",     "Mujer",  "🇧🇷"),
        TtsVoice("fr-FR-DeniseNeural",   "Denise",    "Francia",    "Mujer",  "🇫🇷")
    )

    fun byId(id: String): TtsVoice? = voices.firstOrNull { it.id == id }
}

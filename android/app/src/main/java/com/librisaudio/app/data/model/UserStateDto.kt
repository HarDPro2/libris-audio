package com.librisaudio.app.data.model

/**
 * Parte y posición (ms) de un libro en el progreso del usuario.
 *
 * `updatedAt` es lo que permite la sincronización real entre dispositivos: al
 * fusionar, gana el progreso MÁS RECIENTE de cada libro por separado. Sin esta
 * marca, el último dispositivo que guardaba pisaba al otro aunque su progreso
 * fuera más viejo.
 */
data class PartPos(
    val part: Int = 0,
    val pos: Long = 0L,
    val pct: Int = 0,
    val updatedAt: Long = 0L
)

/** Estadísticas de escucha (racha, tiempo) para conservarlas entre dispositivos. */
data class StatsDto(
    val streak: Int = 0,
    val totalMin: Int = 0,
    val lastDay: String = ""
)

/** Estado del usuario sincronizado en la nube: progreso + preferencias + racha. */
data class UserStateDto(
    val theme: String? = null,
    val voice: String? = null,
    val progress: Map<String, PartPos>? = null,
    val started: List<String>? = null,
    val favorites: List<String>? = null,
    val displayName: String? = null,
    val avatarId: Int? = null,
    val bookmarks: List<com.librisaudio.app.ui.components.BookmarkItem>? = null,
    val stats: StatsDto? = null
)

/** Un capítulo del índice del documento. */
data class ChapterDto(
    @com.google.gson.annotations.SerializedName("titulo")   val title: String = "",
    @com.google.gson.annotations.SerializedName("capitulo") val index: Int = 0,
    @com.google.gson.annotations.SerializedName("offset")   val offset: Int = 0
)

/** Índice del documento: capítulos navegables e idioma detectado. */
data class BookIndexDto(
    @com.google.gson.annotations.SerializedName("formato")   val format: String? = null,
    @com.google.gson.annotations.SerializedName("idioma")    val language: String? = null,
    @com.google.gson.annotations.SerializedName("capitulos") val chapters: List<ChapterDto>? = null
)

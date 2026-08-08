package com.librisaudio.app.data.model

/** Parte y posición (ms) de un libro en el progreso del usuario. */
data class PartPos(
    val part: Int = 0,
    val pos: Long = 0L
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

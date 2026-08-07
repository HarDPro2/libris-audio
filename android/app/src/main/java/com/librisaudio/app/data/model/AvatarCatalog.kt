package com.librisaudio.app.data.model

import androidx.compose.ui.graphics.Color

/** Un avatar artístico: emoji + degradado + nombre pegajoso. */
data class Avatar(
    val id: Int,
    val name: String,
    val emoji: String,
    val c1: Color,
    val c2: Color
)

object AvatarCatalog {

    // Paleta de degradados (se ciclan entre los avatares para dar variedad)
    private val gradients = listOf(
        Color(0xFF8B5CF6) to Color(0xFF06B6D4),   // morado-cian (firma)
        Color(0xFF00D4FF) to Color(0xFF3B82F6),   // azul eléctrico
        Color(0xFFEC4899) to Color(0xFFF59E0B),   // rosa-ámbar
        Color(0xFF10B981) to Color(0xFF14B8A6),   // esmeralda
        Color(0xFFF97316) to Color(0xFFEF4444),   // fuego
        Color(0xFF6366F1) to Color(0xFFA855F7),   // índigo-violeta
        Color(0xFF22D3EE) to Color(0xFF34D399),   // aqua
        Color(0xFFF43F5E) to Color(0xFF8B5CF6),   // carmín-morado
        Color(0xFFFACC15) to Color(0xFFF97316),   // dorado
        Color(0xFF0EA5E9) to Color(0xFF6366F1)    // océano-índigo
    )

    private val defs = listOf(
        "El Sabio" to "🦉", "La Exploradora" to "🧭", "Alma Errante" to "🌙", "El Cronista" to "📜",
        "Reina de Tinta" to "👑", "Lobo Lector" to "🐺", "Estrella Fugaz" to "🌠", "El Alquimista" to "⚗️",
        "Musa Nocturna" to "🎭", "Corsario" to "🏴‍☠️", "El Ermitaño" to "🏔️", "Fénix" to "🔥",
        "La Hechicera" to "🔮", "El Caballero" to "🛡️", "Nómada" to "🐫", "La Poeta" to "🖋️",
        "Zorro Astuto" to "🦊", "El Guardián" to "🗝️", "La Soñadora" to "💭", "Trotamundos" to "🌍",
        "El Bardo" to "🎻", "Gata Curiosa" to "🐱", "Vikingo" to "⚔️", "La Vidente" to "👁️",
        "Búho Sabio" to "🦉", "Dragón" to "🐉", "La Corsaria" to "⚓", "Monje Zen" to "🧘",
        "Cometa" to "☄️", "La Bibliotecaria" to "📚", "Halcón" to "🦅", "Bruja Buena" to "🧙",
        "El Filósofo" to "🏛️", "Sirena" to "🧜", "Cazamitos" to "🏹", "La Aventurera" to "🎒",
        "Búfalo" to "🦬", "Estrella Polar" to "⭐", "El Inventor" to "💡", "Mariposa" to "🦋",
        "Samurái" to "🗡️", "La Astrónoma" to "🔭", "Oso Polar" to "🐻‍❄️", "Duende" to "🍀",
        "La Pirata" to "🦜", "Colibrí" to "🐦", "El Místico" to "🕯️", "Loba" to "🐺",
        "Golondrina" to "🕊️", "Viajero del Tiempo" to "⏳"
    )

    val avatars: List<Avatar> = defs.mapIndexed { i, (name, emoji) ->
        val g = gradients[i % gradients.size]
        Avatar(id = i, name = name, emoji = emoji, c1 = g.first, c2 = g.second)
    }

    fun byId(id: Int): Avatar = avatars.firstOrNull { it.id == id } ?: avatars.first()
}

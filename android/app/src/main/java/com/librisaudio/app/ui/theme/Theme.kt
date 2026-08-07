package com.librisaudio.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** Estilo de animación de fondo asociado a cada tema. */
enum class ThemeAnimation {
    MESH,       // orbes de gradiente flotando (suave)
    NEURAL,     // red neuronal: nodos + conexiones que pulsan
    QUANTUM,    // campo cuántico: partículas orbitando + ondas
    MATRIX,     // lluvia de código verde
    RETRO,      // synthwave: rejilla en perspectiva + sol
    AURORA,     // cortinas de aurora boreal
    STARFIELD,  // estrellas titilando + destellos (biblioteca cósmica)
    INK,        // tinta ascendente + letras flotando (pergamino)
    EMBERS      // brasas / chispas ascendentes
}

enum class AppThemePreset(
    val title: String,
    val primary: Color,
    val secondary: Color,
    val background: Color,
    val surface: Color,
    val animation: ThemeAnimation
) {
    // ── Animados destacados ────────────────────────────────────────────────
    NEURAL(
        title = "Red Neuronal",
        primary = Color(0xFF00D4FF),   // azul eléctrico
        secondary = Color(0xFF3B82F6),
        background = Color(0xFF030B14),
        surface = Color(0xFF0A1826),
        animation = ThemeAnimation.NEURAL
    ),
    QUANTUM(
        title = "Campo Cuántico",
        primary = Color(0xFF8B5CF6),   // azul + morado (firma)
        secondary = Color(0xFF22D3EE),
        background = Color(0xFF070A1A),
        surface = Color(0xFF121634),
        animation = ThemeAnimation.QUANTUM
    ),
    MATRIX(
        title = "Matrix",
        primary = Color(0xFF00FF66),
        secondary = Color(0xFF00A844),
        background = Color(0xFF000804),
        surface = Color(0xFF041209),
        animation = ThemeAnimation.MATRIX
    ),
    RETRO(
        title = "Retro Wave",
        primary = Color(0xFFFF2E97),
        secondary = Color(0xFF00E5FF),
        background = Color(0xFF160A2B),
        surface = Color(0xFF241145),
        animation = ThemeAnimation.RETRO
    ),
    AURORA(
        title = "Aurora Literaria",
        primary = Color(0xFF22D3EE),   // azul eléctrico / teal
        secondary = Color(0xFF34D399),
        background = Color(0xFF04121A),
        surface = Color(0xFF0A2233),
        animation = ThemeAnimation.AURORA
    ),
    COSMIC(
        title = "Biblioteca Cósmica",
        primary = Color(0xFF8B5CF6),   // azul + morado (firma)
        secondary = Color(0xFF06B6D4),
        background = Color(0xFF060814),
        surface = Color(0xFF121A2E),
        animation = ThemeAnimation.STARFIELD
    ),
    INK(
        title = "Tinta y Pergamino",
        primary = Color(0xFFD4A574),
        secondary = Color(0xFFE8C89A),
        background = Color(0xFF120C06),
        surface = Color(0xFF201509),
        animation = ThemeAnimation.INK
    ),
    EMBER(
        title = "Brasa Literaria",
        primary = Color(0xFFF97316),
        secondary = Color(0xFFEF4444),
        background = Color(0xFF16070A),
        surface = Color(0xFF2A0E10),
        animation = ThemeAnimation.EMBERS
    ),

    // ── Suaves (mesh de gradiente) ─────────────────────────────────────────
    CYBERPUNK(
        title = "Cyberpunk",
        primary = Color(0xFF8B5CF6),
        secondary = Color(0xFF06B6D4),
        background = Color(0xFF0F172A),
        surface = Color(0xFF1E293B),
        animation = ThemeAnimation.MESH
    ),
    OCEAN(
        title = "Océano Profundo",
        primary = Color(0xFF0EA5E9),
        secondary = Color(0xFF22D3EE),
        background = Color(0xFF0C1A2E),
        surface = Color(0xFF0F2744),
        animation = ThemeAnimation.MESH
    ),
    FOREST(
        title = "Bosque Oscuro",
        primary = Color(0xFF4ADE80),
        secondary = Color(0xFF86EFAC),
        background = Color(0xFF071810),
        surface = Color(0xFF0D2818),
        animation = ThemeAnimation.MESH
    ),
    MIDNIGHT(
        title = "Medianoche",
        primary = Color(0xFFCBD5E1),
        secondary = Color(0xFF64748B),
        background = Color(0xFF000000),
        surface = Color(0xFF0D0D0D),
        animation = ThemeAnimation.STARFIELD
    )
}

val PurpleAccent = Color(0xFF8B5CF6)
val CyanAccent = Color(0xFF06B6D4)
val DarkSlate = Color(0xFF0F172A)
val CardSurface = Color(0xFF1E293B)
val GreenAccent = Color(0xFF10B981)
val TextWhite = Color(0xFFF8FAFC)
val TextMuted = Color(0xFF94A3B8)

@Composable
fun LibrisAudioTheme(
    preset: AppThemePreset = AppThemePreset.CYBERPUNK,
    content: @Composable () -> Unit
) {
    val colorScheme = darkColorScheme(
        primary = preset.primary,
        secondary = preset.secondary,
        background = preset.background,
        surface = preset.surface,
        onPrimary = Color.White,
        onSecondary = Color.White,
        onBackground = TextWhite,
        onSurface = TextWhite
    )

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}

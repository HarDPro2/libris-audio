package com.librisaudio.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

enum class AppThemePreset(
    val title: String,
    val primary: Color,
    val secondary: Color,
    val background: Color,
    val surface: Color
) {
    CYBERPUNK(
        title = "Cyberpunk",
        primary = Color(0xFF8B5CF6),
        secondary = Color(0xFF06B6D4),
        background = Color(0xFF0F172A),
        surface = Color(0xFF1E293B)
    ),
    OCEAN(
        title = "Océano Profundo",
        primary = Color(0xFF0EA5E9),
        secondary = Color(0xFF22D3EE),
        background = Color(0xFF0C1A2E),
        surface = Color(0xFF0F2744)
    ),
    EMERALD(
        title = "Esmeralda",
        primary = Color(0xFF10B981),
        secondary = Color(0xFF14B8A6),
        background = Color(0xFF064E3B),
        surface = Color(0xFF065F46)
    ),
    EMBER(
        title = "Ember Otoñal",
        primary = Color(0xFFF97316),
        secondary = Color(0xFFEF4444),
        background = Color(0xFF1C0A00),
        surface = Color(0xFF2D1200)
    ),
    SUNSET(
        title = "Sunset Aurora",
        primary = Color(0xFFEC4899),
        secondary = Color(0xFFF59E0B),
        background = Color(0xFF31103F),
        surface = Color(0xFF4C1D95)
    ),
    FOREST(
        title = "Bosque Oscuro",
        primary = Color(0xFF4ADE80),
        secondary = Color(0xFF86EFAC),
        background = Color(0xFF071810),
        surface = Color(0xFF0D2818)
    ),
    COSMIC(
        title = "Espacio Cósmico",
        primary = Color(0xFF6366F1),
        secondary = Color(0xFFA855F7),
        background = Color(0xFF090D16),
        surface = Color(0xFF131B2E)
    ),
    MIDNIGHT(
        title = "Medianoche",
        primary = Color(0xFFCBD5E1),
        secondary = Color(0xFF94A3B8),
        background = Color(0xFF000000),
        surface = Color(0xFF0D0D0D)
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

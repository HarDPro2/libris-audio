package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.components.AchievementsDialog
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.ThemeAnimation
import com.librisaudio.app.ui.theme.TextMuted
import androidx.compose.ui.res.stringResource
import com.librisaudio.app.R

/** Emoji representativo de cada estilo de animación de tema. */
private fun animationIcon(preset: AppThemePreset): String = when (preset.animation) {
    ThemeAnimation.NEURAL    -> "🧠"
    ThemeAnimation.QUANTUM   -> "⚛️"
    ThemeAnimation.MATRIX    -> "💊"
    ThemeAnimation.RETRO     -> "🌆"
    ThemeAnimation.AURORA    -> "🌌"
    ThemeAnimation.STARFIELD -> "✨"
    ThemeAnimation.INK       -> "🖋️"
    ThemeAnimation.EMBERS    -> "🔥"
    ThemeAnimation.PETALS    -> "🌹"
    ThemeAnimation.FOG       -> "🌫️"
    ThemeAnimation.FIREFLIES -> "🧚"
    ThemeAnimation.DUST      -> "🕯️"
    ThemeAnimation.MESH      -> "🎨"
}

/** Nombre localizado del tema (los títulos del enum están en español). */
@Composable
private fun themeName(preset: AppThemePreset): String = when (preset) {
    AppThemePreset.NEURAL    -> stringResource(R.string.theme_neural)
    AppThemePreset.QUANTUM   -> stringResource(R.string.theme_quantum)
    AppThemePreset.MATRIX    -> stringResource(R.string.theme_matrix)
    AppThemePreset.RETRO     -> stringResource(R.string.theme_retro)
    AppThemePreset.AURORA    -> stringResource(R.string.theme_aurora)
    AppThemePreset.COSMIC    -> stringResource(R.string.theme_cosmic)
    AppThemePreset.INK       -> stringResource(R.string.theme_ink)
    AppThemePreset.EMBER     -> stringResource(R.string.theme_ember)
    AppThemePreset.ROMANCE   -> stringResource(R.string.theme_romance)
    AppThemePreset.MYSTERY   -> stringResource(R.string.theme_mystery)
    AppThemePreset.ENCHANTED -> stringResource(R.string.theme_enchanted)
    AppThemePreset.LIBRARY   -> stringResource(R.string.theme_library)
    AppThemePreset.CYBERPUNK -> stringResource(R.string.theme_cyberpunk)
    AppThemePreset.OCEAN     -> stringResource(R.string.theme_ocean)
    AppThemePreset.FOREST    -> stringResource(R.string.theme_forest)
    AppThemePreset.MIDNIGHT  -> stringResource(R.string.theme_midnight)
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SettingsScreen(
    currentTheme: AppThemePreset,
    onSelectTheme: (AppThemePreset) -> Unit,
    userName: String = "",
    userEmail: String = "",
    onLogout: (() -> Unit)? = null,
    currentLang: String = "system",
    onSelectLanguage: (String) -> Unit = {},
    frames3dEnabled: Boolean = false,
    onToggleFrames3d: (Boolean) -> Unit = {},
    premiumEnabled: Boolean = false,
    onTogglePremium: (Boolean) -> Unit = {},
    onCheckUpdates: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    var showLogoutConfirm by remember { mutableStateOf(false) }
    var showAchievements by remember { mutableStateOf(false) }
    var showGuide by remember { mutableStateOf(false) }

    if (showAchievements) {
        AchievementsDialog(primary = currentTheme.primary, onDismiss = { showAchievements = false })
    }
    if (showGuide) {
        GuideDialog(currentTheme = currentTheme, onDismiss = { showGuide = false })
    }

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            Spacer(modifier = Modifier.height(8.dp))

            // Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Settings, contentDescription = null, tint = currentTheme.primary, modifier = Modifier.size(26.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(stringResource(R.string.settings_title), fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
            }
            Text(stringResource(R.string.settings_subtitle), fontSize = 12.sp, color = TextMuted)

            Spacer(modifier = Modifier.height(24.dp))

            // ─── User Profile Card ────────────────────────────────────────
            Surface(
                shape = RoundedCornerShape(18.dp),
                color = Color(0x441E293B),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Avatar circle
                    Box(
                        modifier = Modifier
                            .size(52.dp)
                            .clip(CircleShape)
                            .background(currentTheme.primary.copy(alpha = 0.25f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = (userName.firstOrNull()?.uppercaseChar() ?: userEmail.firstOrNull()?.uppercaseChar() ?: '?').toString(),
                            fontSize = 22.sp,
                            fontWeight = FontWeight.Bold,
                            color = currentTheme.primary
                        )
                    }
                    Spacer(modifier = Modifier.width(14.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = userName.ifBlank { "Usuario" },
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            fontSize = 16.sp
                        )
                        Text(
                            text = userEmail.ifBlank { "Sin email" },
                            color = TextMuted,
                            fontSize = 13.sp
                        )
                    }
                    Icon(Icons.Default.Person, contentDescription = null, tint = TextMuted)
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // ─── Idioma / Language ────────────────────────────────────────
            SectionTitle(stringResource(R.string.settings_section_language))
            Spacer(modifier = Modifier.height(10.dp))
            LanguageSelector(currentLang = currentLang, currentTheme = currentTheme, onSelect = onSelectLanguage)
            Spacer(modifier = Modifier.height(24.dp))

            // ─── Ayuda ────────────────────────────────────────────────────
            SectionTitle(stringResource(R.string.settings_section_help))
            Spacer(modifier = Modifier.height(10.dp))
            OutlinedButton(
                onClick = { showGuide = true },
                modifier = Modifier.fillMaxWidth().height(48.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = currentTheme.primary),
                border = androidx.compose.foundation.BorderStroke(1.dp, currentTheme.primary.copy(alpha = 0.5f))
            ) {
                Icon(Icons.Default.HelpOutline, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(stringResource(R.string.guia_open), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
            }
            Spacer(modifier = Modifier.height(24.dp))

            // ─── Theme Section ────────────────────────────────────────────
            SectionTitle(stringResource(R.string.settings_section_theme))
            Text(stringResource(R.string.settings_theme_subtitle), fontSize = 11.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(12.dp))

            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                AppThemePreset.values().forEach { preset ->
                    val isSelected = currentTheme == preset
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .width(112.dp)
                            .clip(RoundedCornerShape(18.dp))
                            .background(
                                androidx.compose.ui.graphics.Brush.verticalGradient(
                                    listOf(preset.primary.copy(alpha = 0.30f), preset.surface.copy(alpha = 0.6f))
                                )
                            )
                            .then(
                                if (isSelected)
                                    Modifier.border(2.dp, preset.primary, RoundedCornerShape(18.dp))
                                else Modifier
                            )
                            .clickable { onSelectTheme(preset) }
                            .padding(vertical = 14.dp, horizontal = 8.dp)
                    ) {
                        // Preview: swatch con gradiente primario→secundario + ícono de animación
                        Box(
                            modifier = Modifier
                                .size(46.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(
                                    androidx.compose.ui.graphics.Brush.linearGradient(
                                        listOf(preset.primary, preset.secondary)
                                    )
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(animationIcon(preset), fontSize = 20.sp)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = themeName(preset),
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                            color = if (isSelected) Color.White else Color(0xFFCBD5E1),
                            maxLines = 2,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                            lineHeight = 13.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // ─── Premium (provisional hasta la META 5) ────────────────────
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(Color(0x22FFFFFF))
                    .clickable { onTogglePremium(!premiumEnabled) }
                    .padding(horizontal = 14.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("Premium", fontSize = 14.sp,
                         fontWeight = FontWeight.Bold, color = Color.White)
                    Text("Desbloquea los 12 marcos 3D. Provisional: se sustituirá " +
                         "por la suscripción real.",
                         fontSize = 11.sp, color = TextMuted)
                }
                Switch(
                    checked = premiumEnabled,
                    onCheckedChange = { onTogglePremium(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Color.White,
                        checkedTrackColor = currentTheme.primary
                    )
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // ─── Marcos 3D (premium, opt-in) ──────────────────────────────
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(Color(0x22FFFFFF))
                    .clickable { onToggleFrames3d(!frames3dEnabled) }
                    .padding(horizontal = 14.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        stringResource(R.string.settings_frames3d_title),
                        fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White
                    )
                    Text(
                        stringResource(R.string.settings_frames3d_subtitle),
                        fontSize = 11.sp, color = TextMuted
                    )
                }
                Switch(
                    checked = frames3dEnabled,
                    onCheckedChange = { onToggleFrames3d(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Color.White,
                        checkedTrackColor = currentTheme.primary
                    )
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // ─── Achievements Section ─────────────────────────────────────
            SectionTitle(stringResource(R.string.settings_section_achievements))
            Spacer(modifier = Modifier.height(10.dp))
            OutlinedButton(
                onClick = { showAchievements = true },
                modifier = Modifier.fillMaxWidth().height(50.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = currentTheme.primary),
                border = androidx.compose.foundation.BorderStroke(1.dp, currentTheme.primary.copy(alpha = 0.4f))
            ) {
                Icon(Icons.Default.EmojiEvents, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(stringResource(R.string.settings_view_achievements), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
            }

            Spacer(modifier = Modifier.height(24.dp))

            // ─── Logout Button ────────────────────────────────────────────
            if (onLogout != null) {
                SectionTitle(stringResource(R.string.settings_section_session))
                Spacer(modifier = Modifier.height(10.dp))

                OutlinedButton(
                    onClick = { showLogoutConfirm = true },
                    modifier = Modifier.fillMaxWidth().height(50.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFEF4444)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x44EF4444))
                ) {
                    Icon(Icons.Default.Logout, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(stringResource(R.string.settings_logout), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            OutlinedButton(
                onClick = onCheckUpdates,
                modifier = Modifier.fillMaxWidth().height(48.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = currentTheme.primary),
                border = androidx.compose.foundation.BorderStroke(1.dp, currentTheme.primary.copy(alpha = 0.5f))
            ) {
                Icon(Icons.Default.SystemUpdate, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(stringResource(R.string.settings_check_updates), fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            }

            Spacer(modifier = Modifier.height(24.dp))
            // Pie discreto con la versión (sin info técnica)
            Text(
                text = "Libris Audio · v${com.librisaudio.app.BuildConfig.VERSION_NAME}",
                fontSize = 11.sp,
                color = TextMuted,
                modifier = Modifier.fillMaxWidth(),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )

            Spacer(modifier = Modifier.height(100.dp))
        }
    }

    // Logout confirmation
    if (showLogoutConfirm) {
        AlertDialog(
            onDismissRequest = { showLogoutConfirm = false },
            title = { Text(stringResource(R.string.settings_logout), color = Color.White, fontWeight = FontWeight.Bold) },
            text = { Text(stringResource(R.string.logout_confirm_msg), color = TextMuted) },
            confirmButton = {
                TextButton(onClick = { showLogoutConfirm = false; onLogout?.invoke() }) {
                    Text(stringResource(R.string.settings_logout), color = Color(0xFFEF4444), fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutConfirm = false }) {
                    Text(stringResource(R.string.action_cancel), color = TextMuted)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 15.sp)
}

@Composable
private fun InfoCard(items: List<Pair<String, String>>, currentTheme: AppThemePreset) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = Color(0x441E293B),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            items.forEachIndexed { index, (label, value) ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(label, color = TextMuted, fontSize = 13.sp)
                    Text(value, color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                }
                if (index < items.lastIndex) {
                    HorizontalDivider(
                        modifier = Modifier.padding(vertical = 8.dp),
                        color = Color(0x22FFFFFF)
                    )
                }
            }
        }
    }
}

@Composable
private fun OfflineDownloadsCard(
    books: List<com.librisaudio.app.data.OfflineBook>,
    totalBytes: Long,
    currentTheme: AppThemePreset,
    onDelete: (String) -> Unit,
    onDeleteAll: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = Color(0x441E293B),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            if (books.isEmpty()) {
                Text(
                    "No tienes libros descargados. Abre un libro y toca el ícono de descarga (↓) para oírlo sin conexión.",
                    color = TextMuted, fontSize = 13.sp
                )
            } else {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "${books.size} libro(s) · ${formatBytes(totalBytes)}",
                        color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Medium
                    )
                    TextButton(onClick = onDeleteAll) {
                        Text("Borrar todo", color = Color(0xFFEF4444), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
                HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp), color = Color(0x22FFFFFF))
                books.forEach { b ->
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(b.title, color = Color.White, fontSize = 13.sp,
                                fontWeight = FontWeight.Medium, maxLines = 1)
                            Text(
                                "${b.partsCount} partes · ${formatBytes(b.sizeBytes)}" +
                                    if (!b.complete) " · incompleto" else "",
                                color = TextMuted, fontSize = 11.sp
                            )
                        }
                        IconButton(onClick = { onDelete(b.bookId) }) {
                            Icon(Icons.Default.Delete, contentDescription = "Borrar descarga", tint = Color(0xFFEF4444))
                        }
                    }
                }
            }
        }
    }
}

private fun formatBytes(bytes: Long): String {
    if (bytes <= 0) return "0 MB"
    val mb = bytes / (1024.0 * 1024.0)
    return if (mb >= 1) String.format("%.1f MB", mb) else String.format("%.0f KB", bytes / 1024.0)
}

@Composable
private fun LanguageSelector(
    currentLang: String,
    currentTheme: AppThemePreset,
    onSelect: (String) -> Unit
) {
    val options = listOf(
        "system" to stringResource(R.string.language_system),
        "es" to stringResource(R.string.language_spanish),
        "en" to stringResource(R.string.language_english)
    )
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        options.forEach { (tag, label) ->
            val selected = tag == currentLang
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (selected) currentTheme.primary else Color(0x33FFFFFF))
                    .clickable { if (!selected) onSelect(tag) }
                    .padding(vertical = 10.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    label,
                    color = if (selected) Color.White else TextMuted,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1
                )
            }
        }
    }
}

@Composable
private fun GuideDialog(currentTheme: AppThemePreset, onDismiss: () -> Unit) {
    androidx.compose.ui.window.Dialog(onDismissRequest = onDismiss) {
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = Color(0xFF0F172A),
            modifier = Modifier.fillMaxWidth(0.95f).fillMaxHeight(0.85f)
        ) {
            // Antes aqui vivia una guia de seis puntos que cubria menos de un
            // tercio de la app. La sustituye el catalogo completo de funciones.
            GuiaScreen(currentTheme = currentTheme, onBack = onDismiss)
        }
    }
}

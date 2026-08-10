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

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SettingsScreen(
    currentTheme: AppThemePreset,
    onSelectTheme: (AppThemePreset) -> Unit,
    userName: String = "",
    userEmail: String = "",
    onLogout: (() -> Unit)? = null,
    offlineBooks: List<com.librisaudio.app.data.OfflineBook> = emptyList(),
    offlineTotalBytes: Long = 0L,
    onDeleteOffline: (String) -> Unit = {},
    onDeleteAllOffline: () -> Unit = {},
    currentLang: String = "system",
    onSelectLanguage: (String) -> Unit = {},
    modifier: Modifier = Modifier
) {
    var showLogoutConfirm by remember { mutableStateOf(false) }
    var showAchievements by remember { mutableStateOf(false) }

    if (showAchievements) {
        AchievementsDialog(primary = currentTheme.primary, onDismiss = { showAchievements = false })
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
                            text = preset.title,
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
                Text("Ver mis logros", fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
            }

            Spacer(modifier = Modifier.height(24.dp))

            // ─── Info Section ─────────────────────────────────────────────
            // ─── Descargas offline ────────────────────────────────────────
            SectionTitle(stringResource(R.string.settings_section_downloads))
            Spacer(modifier = Modifier.height(10.dp))
            OfflineDownloadsCard(
                books = offlineBooks,
                totalBytes = offlineTotalBytes,
                currentTheme = currentTheme,
                onDelete = onDeleteOffline,
                onDeleteAll = onDeleteAllOffline
            )
            Spacer(modifier = Modifier.height(24.dp))

            SectionTitle(stringResource(R.string.settings_section_system))
            Spacer(modifier = Modifier.height(10.dp))

            InfoCard(
                items = listOf(
                    stringResource(R.string.info_version) to com.librisaudio.app.BuildConfig.VERSION_NAME,
                    "🔊 Audio" to "Edge TTS Neural (Microsoft Azure)",
                    stringResource(R.string.info_storage) to "Cloudflare R2",
                    stringResource(R.string.info_database) to "Appwrite Cloud",
                    "⚡ Backend" to "Google Cloud Run",
                    stringResource(R.string.info_auth) to "Appwrite Auth"
                ),
                currentTheme = currentTheme
            )

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
                    Text("Cerrar Sesión", fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                }
            }

            Spacer(modifier = Modifier.height(100.dp))
        }
    }

    // Logout confirmation
    if (showLogoutConfirm) {
        AlertDialog(
            onDismissRequest = { showLogoutConfirm = false },
            title = { Text("Cerrar Sesión", color = Color.White, fontWeight = FontWeight.Bold) },
            text = { Text("¿Seguro que quieres salir de tu cuenta?", color = TextMuted) },
            confirmButton = {
                TextButton(onClick = { showLogoutConfirm = false; onLogout?.invoke() }) {
                    Text("Cerrar sesión", color = Color(0xFFEF4444), fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutConfirm = false }) {
                    Text("Cancelar", color = TextMuted)
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

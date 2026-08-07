package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
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
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.ThemeAnimation
import com.librisaudio.app.ui.theme.TextMuted

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

@Composable
fun SettingsScreen(
    currentTheme: AppThemePreset,
    onSelectTheme: (AppThemePreset) -> Unit,
    userName: String = "",
    userEmail: String = "",
    onLogout: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    var showLogoutConfirm by remember { mutableStateOf(false) }

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
                Text("Ajustes", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
            }
            Text("Personaliza tu experiencia", fontSize = 12.sp, color = TextMuted)

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

            // ─── Theme Section ────────────────────────────────────────────
            SectionTitle("🎨 Tema Visual")
            Text("Cada tema tiene su propia animación de fondo", fontSize = 11.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(12.dp))

            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(AppThemePreset.values()) { preset ->
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

            // ─── Info Section ─────────────────────────────────────────────
            SectionTitle("ℹ️ Información del Sistema")
            Spacer(modifier = Modifier.height(10.dp))

            InfoCard(
                items = listOf(
                    "🔊 Audio" to "Edge TTS Neural (Microsoft Azure)",
                    "☁️ Almacenamiento" to "Cloudflare R2",
                    "🗄️ Base de datos" to "Appwrite Cloud",
                    "⚡ Backend" to "Google Cloud Run",
                    "🔐 Autenticación" to "Appwrite Auth"
                ),
                currentTheme = currentTheme
            )

            Spacer(modifier = Modifier.height(24.dp))

            // ─── Logout Button ────────────────────────────────────────────
            if (onLogout != null) {
                SectionTitle("🚪 Sesión")
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
